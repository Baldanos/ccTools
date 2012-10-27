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
        global ser

   
    def run(self):
        #print "serialReader running"
        global data
        global readLock
        global outFile
        ser.read(ser.inWaiting())
        while not self.terminated:
            bytesToRead = ser.inWaiting()
            #print bytesToRead
            if bytesToRead > 0:
                #print "serial waiting for lock"
                readLock.acquire()
                read = ser.read(bytesToRead)
                data = data + read 
                if outFile is not None:
                    outFile.write(read)
                #print "serial released lock"
                readLock.release()
            time.sleep(0.1)

    def stop(self):
        self.terminated = True

def enterBitBang():
    """
    Enters binary bitbang mode on the bus pirate
    """
    # Enter bitbang mode
    for i in xrange(20):
        ser.write("\x00")
    if "BBIO1" not in ser.read(5):
        print "Could not get into bbIO mode"
        sys.exit(0)
        
    # Enter UART mode
    ser.write("\x03")
    time.sleep(0.01)
    #if "ART1" not in ser.read(4):
    #    sys.exit(0)
    #Baud rate : 9600
    ser.write(chr(0b01100100))
    ser.read(1)
    #Peripherals : power ON / pullup ON
    ser.write(chr(0b01001100))
    ser.read(1)
    #Start UART bridge
    ser.write(chr(0b00001111))
    ser.read(1)


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
            time.sleep(0.2)

    def stop(self):
        self.terminated = True


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
            if options.busPirate:
                #ser=serial.Serial(options.serPort, 115200, timeout=1)
                ser=serial.Serial(options.serPort, 115200)
                enterBitBang()
            else:
                #ser=serial.Serial(options.serPort, 9600, timeout=1)
                ser=serial.Serial(options.serPort, 9600)
        except serial.SerialException, e:
            print "Error"
            print e.message
            sys.exit()

    if options.outFile is not None:
        outFile = open(options.outFile,"wb")
    else:
        outFile = None


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
