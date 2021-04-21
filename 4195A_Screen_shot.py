#!/bin/python
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
import sys
import re

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
if sys.argv[1:]:
    span_specific=sys.argv[1]
#
#gpib.write("AUTO\r\n")          # Scale the display to the data
gpib.write("CPYM2\r\n")
gpib.write("COPY\r\n")
#gpib.write("++lon 0\r\n")       # Enable "listen only mode"
#
done = False
data = ""
read_count = 0
while not done:      # And not finished
    try:
        sleep(0.2)
        buf = gpib.read()
        data = data + buf
        sys.stdout.write("Read Count: " + str(read_count) + "\r")
        sys.stdout.flush()
        read_count = read_count + 1
        #
        # End of operation is marked by star
        if buf.find("*") <> -1:
            done = True
            print("[gpib.read] End of Data")
    except:
        print("[gpib.read] Error 3")
        done = True
        gpib.write("CPYM3\r\n")
        sleep(2.2)
        gpib.write("++loc\r\n")
        gpib.write("++lon 0\r\n")       # Disable "listen only mode"
        gpib.close()
        exit(1)

print("")
gpib.write("CPYM3\r\n")                 # Selects raster graphics dump hard copy mode.
gpib.write("CLS\r\n")                   # Clear the HP-IB Status Byte
gpib.write("++loc\r\n")                 # Set the device to local mode
gpib.close()
sleep(1.0)
#
# Ok, we got data. Let's process it
lines = [s.strip() for s in data.strip('\0').strip().replace("*","").replace(chr(27),"").split('\n') if s.strip() <> "" and len(s.strip()) > 2]
lines = [s for s in lines if len(s.strip()) > 2]
output = []
#
filename = "4195_screen_shot.csv"
#
if len(lines) > 2:
    #
    # Let's start writing to file
    f = open(filename, "w")
    # Extract heading
    heading = filter_non_printable(lines[1]) + "\n"
    heading = re.sub(r"^N", "N,", heading)
    heading = re.sub(r"[]]", "],", heading)
    sys.stdout.write("Heading[1]:\r\n\t" + heading + "\r\n")
    sys.stdout.flush()
    f.write(heading)
    lstart = 2
#    rxx = re.search("^.*SPECTRUM\s*[0-9]*", heading)
#    if rxx:
#        #
#        #  9              4SPECTRUM
#        now = datetime.now()
#        current_time = now.strftime("%Y/%m/%d %H:%M:%S")
#        if span_specific == "FM":
#            heading = "4195A Spectrum Analyzer " + current_time + ",Commercial Radio FM Band,,"
#        elif span_specific == "FM1":
#            heading = "4195A Spectrum Analyzer " + current_time + ",Commercial Radio FM Band Swept with high RBW,,"
#        else:
#            heading = "4195A Spectrum Analyzer " + current_time + ",0-500MHz Sweep,,"
#        f.write(heading + "\n")            # Let's write this out
#        lstart=3
#        heading = lines[2]
#    else:
#        lstart=2
#
#    #
#    # N   FREQUENCY [ Hz ]    A   B
#    if heading[0] <> 'N':
#        print("Wrong data format (does not start with 'N')\nCancel copy on local machine and reset GPIB adapter")
#        f.write(heading + "\n")            # Let's write this out. We don't care what it says
#        f.close()
#        exit()
#    heading = "N,FREQUENCY [ Hz ],DBm,Phase"
#    f.write(heading + "\n")            # Let's write this out

#    sys.stdout.write("Heading[2]:\r\n\t" + heading + "\r\n")
#    sys.stdout.flush()

    # Extract line data
    for xline in lines[lstart:]:
        line = filter_non_printable(xline)
        n = int(line[0:5].strip())
        freq = float(line[5:22].strip().replace(" ",""))
        fsplit = line[22:].split()

        fields = ["%e" % float_conv(s) for s in line[22:].split() if s <> ""]
        output.append("%d,%f,%s" % (n, freq, ",".join(fields)))
        #output.append(line)

    # Write waveform to file
    for line in output:
        oline = line + "\n"
        f.write(oline)
    f.close()

#for line in output:
#    print(line)

exit()
