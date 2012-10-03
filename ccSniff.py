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

    def __init__(self, busPirate=True):
        super(serialReader, self).__init__()
        self.terminated = False
        try:
            if busPirate:
                self.ser=serial.Serial(options.serPort, 115200, timeout=1)
                self.enterBitBang()
            else:
                self.ser=serial.Serial(options.serPort, 9600, timeout=1)
        except serial.SerialException, e:
            print e.message
            sys.exit()

   
    def run(self):
        #print "serialReader running"
        global data
        global readLock
        global outFile
        self.ser.read(self.ser.inWaiting())
        while not self.terminated:
            bytesToRead = self.ser.inWaiting()
            #print bytesToRead
            if bytesToRead > 0:
                #print "serial waiting for lock"
                readLock.acquire()
                data = data + self.ser.read(bytesToRead)
                if outFile is not None:
                    outFile.write(data)
                #print "serial released lock"
                readLock.release()
            time.sleep(1)
        self.leaveBitBang()

    def stop(self):
        self.terminated = True

    def enterBitBang(self):

        # Enter bitbang mode
        for i in xrange(20):
            self.ser.write("\x00")
            while self.ser.inWaiting()>4:
                if "BBIO1" in self.ser.read(5):
                    break

        # Enter UART mode
        self.ser.write("\x03")

        #Baud rate : 9600
        self.ser.write(chr(0b01100100))

        #Peripherals : power ON / pullup ON
        self.ser.write(chr(0b01001100))


        # Enable UART RX echo
        self.ser.write(chr(0b00000010))

        time.sleep(0.1)

        # Cleans input buffer
        self.ser.flushInput()


    def leaveBitBang(self):

        # Disable UART RX echo
        self.ser.write(chr(0b00000011))


        # Leave UART mode
        self.ser.write("\x00")

        # Leave bitbang mode
        self.ser.write("\x0f")


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
        reader=serialReader(options.busPirate)

    if options.outFile is not None:
        outFile = open(options.outFile,"wb")
    else:
        outFile = None


    display = ccTalkDisplay()
    display.start()
    print "display init done"


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
