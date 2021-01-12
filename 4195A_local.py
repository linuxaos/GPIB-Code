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


from plx_gpib_ethernet import PrologixGPIBEthernet

gpib = PrologixGPIBEthernet('192.168.1.18')

def keyboardInterruptHandler(signal, frame):
    print("\nKeyboardInterrupt (ID: {}) has been caught. Cleaning up...".format(signal))
    gpib.close()
    exit(0)

signal.signal(signal.SIGINT, keyboardInterruptHandler)

# open connection to Prologix GPIB-to-Ethernet adapter
try:
    gpib.connect()
except:
    print("[gpib.connect] Error 1")
    exit()

# Select gpib device at address 3
gpib.select(3)
gpib.write("++eoi 1")
gpib.write("RST")
sleep(2)
gpib.write("++loc")
gpib.close()
exit()
