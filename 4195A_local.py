#!/bin/python
#
#
# @(#) Address the 4195A, set as spectrum analyzer, reset and quit
#
# 2021 xaos@maximaphysics.com
#
# This is V0.01. Only a test.
#
import signal
import time
from time import sleep
from datetime import datetime

default_IP="192.168.1.18"
default_GPIB_address=3

from plx_gpib_ethernet import PrologixGPIBEthernet
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


def keyboardInterruptHandler(signal, frame):
    print("\nKeyboardInterrupt (ID: {}) has been caught. Cleaning up...".format(signal))
    gpib.close()
    exit(0)

signal.signal(signal.SIGINT, keyboardInterruptHandler)
#
# Read from the configuration file
read_GPIB_config()
#
gpib = PrologixGPIBEthernet(default_IP, default_GPIB_address)
#
# open connection to Prologix GPIB-to-Ethernet adapter
try:
    gpib.connect()
except:
    print("[gpib.connect] Error 1")
    exit()

# Select gpib device at address 3
gpib.select(default_GPIB_address)
gpib.write("++eoi 1")
sleep(2)
gpib.write("++loc")
gpib.write("SWM1\r\n")  # Cont sweep
gpib.write("++loc")
gpib.close()
exit()
