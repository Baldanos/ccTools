#!/usr/bin/env python
# -*- coding: utf-8 -*-

import serial
import threading
import time
import sys
from optparse import OptionParser

from ccTalk import *

##
#
# Globals
#
##
data = ""
readLock = threading.Lock()


class serialReader(threading.Thread):

    def __init__(self):
        super(serialReader, self).__init__()
        self.terminated = False
    
    def run(self):
        #print "serialReader running"
        global ser
        global data
        global readLock
        global outFile
        while not self.terminated:
            bytesToRead = ser.inWaiting()
            #print bytesToRead
            if bytesToRead > 0:
                #print "serial waiting for lock"
                readLock.acquire()
                data = data + ser.read(bytesToRead)
                if outFile is not None:
                    outFile.write(data)
                #print "serial released lock"
                readLock.release()
            time.sleep(1)

    def stop(self):
        self.terminated = True

class ccTalkDisplay(threading.Thread):

    def __init__(self):
        super(ccTalkDisplay, self).__init__()
        self.terminated = False

    def run(self):
        #print "display running"
        global readLock
        global data
        while not self.terminated:
            if len(data)>0:
                #print "display waiting for lock"
                readLock.acquire()
                data, messages = parseMessages(data)
                #print "display released lock"
                readLock.release()

                for i in xrange(0,len(messages)):
                    print messages[i]
            time.sleep(1)

    def stop(self):
        self.terminated = True


def enterBitBang():

    # Enter bitbang mode
    for i in xrange(20):
        ser.write("\x00")
        if ser.inWaiting()>4:
            if "BBIO1" in ser.read(5):
                break

    # Enter UART mode
    ser.write("\x03")

    #Baud rate : 9600
    ser.write(chr(0b01100100))

    #Peripherals : power ON / pullup ON
    ser.write(chr(0b01001100))


    # Enable UART RX echo
    ser.write(chr(0b00000010))

    # Cleans input buffer
    ser.flushInput()


def leaveBitBang():

    # Disable UART RX echo
    ser.write(chr(0b00000011))


    # Leave UART mode
    ser.write("\x00")

    # Leave bitbang mode
    ser.write("\x0f")

if __name__ == '__main__':

    parser = OptionParser()
    parser.add_option("-i", "--interface", help="Serial port to use", metavar="DEVICE", dest="serPort")
    parser.add_option("-w", "--write", help="File name to write data", metavar="FILE", dest="outFile")
    parser.add_option("-b", "--bus-pirate", help="Use this switch to tell the serial port is a bus pirate", dest="busPirate", action="store_true", default=False)

    (options, args) = parser.parse_args()

    if options.serPort is None:
        print "Error, no serial port specified"
        sys.exit()
    else:
        try:
            ser=serial.Serial(options.serPort, 115200, timeout=1)
        except serial.SerialException, e:
            print e.message
            sys.exit()

    if options.outFile is not None:
        outFile = open(options.outFile,"wb")
    else:
        outFile = None

    #Inits th bus pirate device if needed
    if options.busPirate:
        enterBitBang()

    display = ccTalkDisplay()
    display.start()
    print "display init done"

    reader = serialReader()
    reader.start()
    print "serial reader init done"


    try:
        while True:
            time.sleep(1)
    except:
        print "Stopping display thread"
        display.stop()
        display.join()
        print "Stopping reader thread"
        reader.stop()
        reader.join()
        if outFile is not None:
            outFile.close()
        if options.busPirate:
            leaveBitBang()
