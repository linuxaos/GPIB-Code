#!/usr/bin/python
#
# @(#) Address the 4195A, set as spectrum analyzer and read the data as CSV
# 2021 xaos@maximaphysics.com
#
# Quick summary. This is V1.01. Only a test.
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
from decimal import *

default_IP="192.168.1.18"
default_GPIB_address=3

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
    gpibx = PrologixGPIBEthernet(default_IP, default_GPIB_address)
    # open connection to Prologix GPIB-to-Ethernet adapter
    try:
        gpibx.connect()
    except:
        print("[gpib.connect] Error 1")
        exit()

    # Select gpib device at address x
    try:
        gpibx.select(default_GPIB_address)
    except:
        print("[gpib.select] Error 2")
        exit()
    return gpibx
#
def read_GPIB_config():
    filename = "prologix_gpib.conf"
    try:
        f = open(filename, "r")
    except:
        print "NOTE: ould not open config file. Using defaults"

    for rline in f:
        li=rline.strip()
        if not li.startswith("#"):
            cfline=li.split()
            tmp_IP=cfline[0]
            tmp_GPIB_ADDR=cfline[1]
            if tmp_GPIB_ADDR != "":
                default_IP=tmp_IP
                default_GPIB_address=tmp_GPIB_ADDR
            break

    print "IP: " + default_IP + " - GPIB: " + default_GPIB_address
    f.close()
#
# Main
signal.signal(signal.SIGINT, keyboardInterruptHandler)
#
# Read from the configuration file
read_GPIB_config()
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
###########################################################################
# Create the top header
#
# ERROR: filter_non_printable should be against buf
#
register_name="Resolution Bandwidth"
gpib.write("RBW?\r\n")            # Read register RBW Resolution Bandwidth
sleep(1.0)
try:
    buf = filter_non_printable(gpib.read())
except:
    print("[gpib.read] Error 1")
    done = True
    gpib.write("CLS\r\n")
    sleep(2.2)
    gpib.write("++loc\r\n")
    gpib.write("++lon 0\r\n")       # Disable "listen only mode"
    gpib.close()
    exit(1)
#
buf = buf.replace("*", "")
ebuf = Decimal(str(buf)).normalize(); bufeng = ebuf.to_eng_string();
print_line = register_name + ": " + bufeng + "Hz"; print print_line
print_HTML_header = "<BR>" + print_line + ",&nbsp;"
#
register_name="Reference Top"
gpib.write("REF?\r\n")            # Read register REF
sleep(1.0)
buf = filter_non_printable(gpib.read())
buf = buf.replace("*", "")
ebuf = Decimal(str(buf)).normalize(); bufeng = ebuf.to_eng_string();
print_line = register_name + ": " + bufeng; print print_line
print_HTML_header = print_HTML_header + print_line + ",&nbsp;"
#
register_name="Span"
gpib.write("SPAN?\r\n")           # Read register SPAN
sleep(1.0)
buf = filter_non_printable(gpib.read())
buf = buf.replace("*", "")
ebuf = Decimal(str(buf)).normalize(); bufeng = ebuf.to_eng_string();
print_line = register_name + ": " + bufeng + "Hz"; print print_line
print_HTML_header = print_HTML_header + print_line + "<BR>\n"
#
register_name="Start"
gpib.write("START?\r\n")          # Read register
sleep(1.0)
buf = filter_non_printable(gpib.read())
buf = buf.replace("*", "")
ebuf = Decimal(str(buf)).normalize(); bufeng = ebuf.to_eng_string();
print_line = register_name + ": " + bufeng + "Hz"; print print_line
print_HTML_header = print_HTML_header + print_line + ",&nbsp;"
#
register_name="Stop"
gpib.write("STOP?\r\n")           # Read register
sleep(1.0)
buf = filter_non_printable(gpib.read())
buf = buf.replace("*", "")
ebuf = Decimal(str(buf)).normalize(); bufeng = ebuf.to_eng_string();
print_line = register_name + ": " + bufeng + "Hz"; print print_line
print_HTML_header = print_HTML_header + print_line + ",&nbsp;"
#
register_name="Step"
gpib.write("STEP?\r\n")           # Read register
sleep(1.0)
buf = filter_non_printable(gpib.read())
buf = buf.replace("*", "")
ebuf = Decimal(str(buf)).normalize(); bufeng = ebuf.to_eng_string();
print_line = register_name + ": " + bufeng + "Hz"; print print_line
print_HTML_header = print_HTML_header + print_line + ",&nbsp;"
#
register_name="Sweep Time"
gpib.write("ST?\r\n")           # Read register
sleep(1.0)
buf = filter_non_printable(gpib.read())
buf = buf.replace("*", "")
ebuf = Decimal(str(buf)).normalize(); bufeng = ebuf.to_eng_string();
print_line = register_name + ": " + bufeng; print print_line
print_HTML_header = print_HTML_header + print_line + "s\n"
###########
filename = file_path + "/" + "4195_screen_shot_MACH_HEADER_" + file_pstring + ".html"
f = open(filename, "w")
f.write(print_HTML_header)
f.close()
###########################################################################
# Main
gpib.write("CPYM2\r\n")
gpib.write("COPY\r\n")
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
        print("[gpib.read] Error 3")
        done = True
        gpib.write("CLS\r\n")
        sleep(2.2)
        gpib.write("++loc\r\n")
        gpib.write("++lon 0\r\n")       # Disable "listen only mode"
        gpib.close()
        exit(1)
    #
    data = data + buf
    sys.stdout.write("Read Count: " + str(read_count) + "\r")
    sys.stdout.flush()
    #
    # End of operation is marked by star
    if buf.find("*") != -1:
        done = True
        print("[gpib.read] End of Data")
    #
    read_count = read_count + 1
#
gpib.write("CLS\r\n")                   # Clear the HP-IB Status Byte
#gpib.write("CPYM3\r\n")                # Selects raster graphics dump hard copy mode.
gpib.write("++loc\r\n")                 # Set the device to local mode
gpib.close()
sleep(1.0)
#
# Ok, we got data. Let's process it
lines = [s.strip() for s in data.strip('\0').strip().replace("*","").replace(chr(27),"").split('\n') if s.strip() != "" and len(s.strip()) > 2]
lines = [s for s in lines if len(s.strip()) > 2]
output = []
#
filename = file_path + "/" + "4195_screen_shot_" + file_pstring + ".csv"
#
line_count=0
FORMAT_4195A=""
FORMAT_HEADING=""
# 0 > SPECTRUM
# 1 > N    FREQUENCY [ Hz ]      MAG  [  dBm  ]     MAG  [       ]
# 
# 0 > NETWORK
# 1 > N    FREQUENCY [ Hz ]      T/R  [  dB   ]    PHASE [  deg  ]
#
# This is the Smith Chart
# 0 > NETWORK
# 1 > N    FREQUENCY [ Hz ]      Re   [       ]     Im   [       ]
#
if len(lines) > 2:
    #
    # Let's start writing to file
    f = open(filename, "w")
    lstart = 0
    #
    # Extract line data
    for xline in lines[lstart:]:
        if line_count < 1:
            heading = filter_non_printable(xline)
            FORMAT_4195A = heading[16:]
            TITLE_4195A = FORMAT_4195A + " Configuration"
            FORMAT_4195A = "-," + FORMAT_4195A + " Configuration" + ",,"
            print(str(line_count) + " > " + str(TITLE_4195A))
            line_count = line_count + 1
            continue
        elif line_count < 2:
            heading = filter_non_printable(xline)
            FORMAT_HEADING = re.sub(r"^N", "N,", heading)
            FORMAT_HEADING = re.sub(r"[[]", "_", FORMAT_HEADING)
            FORMAT_HEADING = re.sub(r"[]]", ",", FORMAT_HEADING)
            FORMAT_HEADING = re.sub(r"\s", "",   FORMAT_HEADING)
            FORMAT_HEADING = re.sub(r"_,", ",",  FORMAT_HEADING)
            FORMAT_HEADING = re.sub(r",$", "",  FORMAT_HEADING)
            str_split=FORMAT_HEADING.split(',')
            COL1_4195A = str_split[1]
            COL2_4195A = str_split[2]
            COL3_4195A = str_split[3]
            #
            # Now we break this up so we can create the chart headings
            print(str(line_count) + " > " + str(FORMAT_HEADING))
            line_count = line_count + 1
            continue
        else:
            line = filter_non_printable(xline)
            line = re.sub(r"\s\s*", " ", line)
            line = re.sub(r"^\s*", "", line)
            #print "[0]>>>>>>>>>>>>Line: \"" + line + "\""
            #
            linen = re.sub("^([0-9]*).*$", r'\1', line)
            #print "[1]>>>>>>>>>>>>Line: \"" + linen + "\""
            #
            n = int(linen)
            linen = re.sub("^[0-9]*\s*([^.]*[.][0-9]*)\s.*$", r'\1', line)
            #print "[2]>>>>>>>>>>>>Line: \"" + linen + "\""
            #
            linen = re.sub(r"\s", "", linen)
            freq = float(linen)
            #
            linen = re.sub("^[0-9]*\s*[^.]*[.][0-9]*\s(.*)$", r'\1', line)
            #print "[3]>>>>>>>>>>>>Line: \"" + linen + "\""
            #
            fields = ["%e" % float_conv(s) for s in linen.split() if s != ""]
            output.append("%d,%f,%s" % (n, freq, ",".join(fields)))

    # Write waveform to file
    csvVAR=FORMAT_HEADING + "\n"
    f.write(FORMAT_4195A + "\n")
    f.write(FORMAT_HEADING + "\n")
    for line in output:
        oline = line + "\n"
        csvVAR = csvVAR + oline         # We need this below so we can create the graphs
        f.write(oline)
    f.close()
#
vdata = unicode(csvVAR)
buffer = StringIO(vdata)
#df = pd.read_csv(filepath_or_buffer = buffer, header = 0, usecols = ["Frequency", "dbm"])
df = pd.read_csv(filepath_or_buffer = buffer, header = 0, usecols = [1, 2])
#
# In case we ever want to re-read from the csv we just created
#df = pd.read_csv(filepath_or_buffer = buffer)
ltitle=TITLE_4195A + " - " + COL1_4195A + " vs " + COL2_4195A
# DEBUG
#print(COL1_4195A + " - " + COL2_4195A + " - " + ltitle + "\n")
fig = px.line(df, x=str(COL1_4195A), y=str(COL2_4195A), title=str(ltitle))
filename = file_path + "/" + "gpib_power_raw_mid_" + file_pstring + ".html"
fig.write_html(filename, full_html=False, default_width='100%', include_plotlyjs=False)
#
filename = file_path + "/" + "gpib_power_raw_" + file_pstring + ".html"
fig.write_html(filename, full_html=False, default_width='100%', include_plotlyjs=False)
#
# DEBUG
# If we uncomment this, a copy of firefox will startup and the plot will be in there.
# fig.show()
buffer = StringIO(vdata)
df = pd.read_csv(filepath_or_buffer = buffer, header = 0, usecols = [1,3])
#
# In case we ever want to re-read from the csv we just created
#df = pd.read_csv(filepath_or_buffer = buffer)
ltitle=TITLE_4195A + " - " + COL1_4195A + " vs " + COL3_4195A
fig = px.line(df, x=str(COL1_4195A), y=str(COL3_4195A), title=str(ltitle))
filename = file_path + "/" + "gpib_phase_raw_mid_" + file_pstring + ".html"
fig.write_html(filename, full_html=False, default_width='100%', include_plotlyjs=False)
filename = file_path + "/" + "gpib_phase_raw_" + file_pstring + ".html"
fig.write_html(filename, full_html=False, default_width='100%', include_plotlyjs=False)

exit()
