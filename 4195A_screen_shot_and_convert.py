#!/usr/bin/python
#
# @(#) Address the 4195A, set as spectrum analyzer and read the data as CSV
# 2021 xaos@maximaphysics.com
#
# Quick summary. This is V0.01. Only a test.
#
# The HP 4195A's display data can be copied to a printer or
# HP-GL compatible plotter. When the COPY key is pressed,
# the softkeys shown in the figure below will be displ.ayed.
# To produce a hard copy, the analyzer must be in the TALK
# ONLY mode and the printer or plotter must be in the LISTEN ONLY mode.
#
import signal
import time
from time import sleep
from datetime import datetime
from plx_gpib_ethernet import PrologixGPIBEthernet
import os
from io import StringIO
import requests
import sys
import re
import pandas as pd
import plotly.express as px

pd.set_option("display.precision", 8)

def keyboardInterruptHandler(signal, frame):
    print("\nKeyboardInterrupt (ID: {}) has been caught. Cleaning up...".format(signal))
    gpib.close()
    exit(0)

def filter_non_printable(str):
      return ''.join([c for c in str if ord(c) > 31 or ord(c) == 9])

def float_conv(s):
    """
    Convert a string in engineering unit exponents notation
    to a float.

    Ex:
    "3.3m" -> float(3.3e-3)
    "4.5M" -> float(4.5e6)
    "2.111u" -> float(2.111e-6)

    Supported qualifiers:
    "p" = x 1e-12
    "n" = x 1e-9
    "u" = x 1e-6
    "m" = x 1e-3
    "k" or "K" = x 1e3
    "M" = x 1e6
    no qualifier = x 1e0

    In case of a unsupported qualifier, the float(x) conversion will
    yield a ValueError exception and the program will crash :)
    """
    mult = 1.0

    if s[-1] == 'm':
        mult = 1e-3
        s = s[:-1]
    elif s[-1] == 'M':
        mult = 1e6
        s = s[:-1]
    elif s[-1] == 'u':
        mult = 1e-6
        s = s[:-1]
    elif s[-1] == 'p':
        mult = 1e-12
        s = s[:-1]
    elif s[-1] == 'n':
        mult = 1e-9
        s = s[:-1]
    elif s[-1] == 'K':
        mult = 1e3
        s = s[:-1]
    elif s[-1] == 'k':
        mult = 1e3
        s = s[:-1]

    return float(s) * mult
#
def check_ports():
    #
    sys.stdout.write("Running check\r\n")
    sys.stdout.flush()
    cmd = "netstat -a >netstat_lnp.out 2>&1"
    returned_value = os.system(cmd)  # returns the exit code in unix
    return returned_value
#
def connect_and_open():

    gpibx = PrologixGPIBEthernet('192.168.1.18', 2)
    # open connection to Prologix GPIB-to-Ethernet adapter
    try:
        gpibx.connect()
    except:
        print("[gpib.connect] Error 1")
        exit()

    # select gpib device at address 10
    try:
        gpibx.select(3)
    except:
        print("[gpib.select] Error 2")
        exit()
    return gpibx

def create_header():
gpib.write("RBW?\r\n")            # Read register RBW Resolution Bandwidth
sleep(1.0)
buf = gpib.read()
print "Resolution Bandwidth: " + buf
#
gpib.write("REF?\r\n")            # Read register REF
sleep(1.0)
buf = gpib.read()
print "Reference Top       : " + buf
#
gpib.write("SPAN?\r\n")           # Read register SPAN
sleep(1.0)
buf = gpib.read()
print "Span                : " + buf
#
gpib.write("START?\r\n")          # Read register
sleep(1.0)
buf = gpib.read()
print "Start               : " + buf
#
gpib.write("STOP?\r\n")           # Read register
sleep(1.0)
buf = gpib.read()
print "Stop                : " + buf
#
gpib.write("STEP?\r\n")           # Read register
sleep(1.0)
buf = gpib.read()
print "Step                : " + buf
#
gpib.write("ST?\r\n")           # Read register
sleep(1.0)
buf = gpib.read()
print "Sweep Time          : " + buf
#
# Main
signal.signal(signal.SIGINT, keyboardInterruptHandler)
#
gpib = connect_and_open()
#
gpib.write("++eoi 1\r\n")           # Enable EOI assertion with last character
gpib.write("++eos 0\r\n")           # Append CR+LF to instrument commands
gpib.write("++eot_enable 1\r\n")    # Append user defined character when EOI detected
gpib.write("++eot_char 42\r\n")     # Append * (ASCII 42) when EOI is detected
#
# Specify the string to add to the output scan files
file_pstring="0"
file_path="./"
if sys.argv[1:]:
    file_pstring=sys.argv[1]
if sys.argv[2:]:
    file_path=sys.argv[2]
#
#gpib.write("RQS=8\r\n")          # Bit 3 enables End bit of 4195A.
gpib.write("CPYM2\r\n")
gpib.write("COPY\r\n")
#sleep(2.0)
#gpib.write("++lon 0\r\n")       # Enable "listen only mode"
#
done = False
data = ""
read_count = 0
while not done:      # And not finished
    sleep(0.2)
    try:
        buf = gpib.read()
    except:
        print("[gpib.read] Error 3 - " + str(len(data)) )
        done = True
        gpib.write("CLS\r\n")
        gpib.write("++loc\r\n")
        gpib.close()
        exit(1)

    data = data + buf
    #sys.stdout.write("Read Count: " + str(read_count) + "\r")
    sys.stdout.write(str(data) + "\r")
    sys.stdout.flush()
    read_count = read_count + 1
    #
    # End of operation is marked by star
    if buf.find("*") != -1:
        done = True
        print("[gpib.read] End of Data")

print("")
#gpib.write("CPYM3\r\n")                 # Selects raster graphics dump hard copy mode.
gpib.write("CLS\r\n")                   # Clear the HP-IB Status Byte
gpib.write("++loc\r\n")                 # Set the device to local mode
gpib.close()
sleep(1.0)
#
# Ok, we got data. Let's process it
#
filename = file_path + "/" + "4195_screen_shot_" + file_pstring + ".gpib"
#
if len(data) > 0:
    #
    # Let's start writing to file
    f = open(filename, "w")
    lstart = 0

    # Extract line data
    f.write(data)
    f.close()
exit()
