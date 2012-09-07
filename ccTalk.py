##
#
# ccTalk library
#
##

##
#
# Globals
#
##

# Parses a byte string to process ccTalk messages
def parseMessages(data):
    """
    Parses a byte string to grab messages
    Returns a list containing all ccTalk messages found
    """
    try:
        messages = []
        length = data[1]

        message=data[:ord(length)+5]
        msg = ccTalkMessage(message)
        messages.append(msg)
        data = data[ord(length)+5:]
    except:
        data = data[1:]

    if len(data)>0:
        data, messages2 = parseMessages(data)
        for message in messages2:
            messages.append(message)
    
    return (data,messages)

# Header types definition
headerTypes = {
        255 : 'Factory set:up and test',
        254 : 'Simple poll',
        253 : 'Address poll',
        252 : 'Address clash',
        251 : 'Address change',
        250 : 'Address random',
        249 : 'Request polling priority',
        248 : 'Request status',
        247 : 'Request variable set',
        246 : 'Request manufacturer id',
        245 : 'Request equipment category id',
        244 : 'Request product code',
        243 : 'Request database version',
        242 : 'Request serial number',
        241 : 'Request software revision',
        240 : 'Test solenoids',
        239 : 'Operate motors',
        238 : 'Test output lines',
        237 : 'Read input lines',
        236 : 'Read opto states',
        235 : 'Read last credit or error code',
        234 : 'Issue guard code',
        233 : 'Latch output lines',
        232 : 'Perform self:check',
        231 : 'Modify inhibit status',
        230 : 'Request inhibit status',
        229 : 'Read buffered credit or error codes',
        228 : 'Modify master inhibit status',
        227 : 'Request master inhibit status',
        226 : 'Request insertion counter',
        225 : 'Request accept counter',
        224 : 'Dispense coins',
        223 : 'Dispense change',
        222 : 'Modify sorter override status',
        221 : 'Request sorter override status',
        220 : 'One:shot credit',
        219 : 'Enter new PIN number',
        218 : 'Enter PIN number',
        217 : 'Request payout high / low status',
        216 : 'Request data storage availability',
        215 : 'Read data block',
        214 : 'Write data block',
        213 : 'Request option flags',
        212 : 'Request coin position',
        211 : 'Power management control',
        210 : 'Modify sorter paths',
        209 : 'Request sorter paths',
        208 : 'Modify payout absolute count',
        207 : 'Request payout absolute count',
        206 : 'Empty payout',
        205 : 'Request audit information block',
        204 : 'Meter control',
        203 : 'Display control',
        202 : 'Teach mode control',
        201 : 'Request teach status',
        200 : 'Upload coin data',
        199 : 'Configuration to EEPROM',
        198 : 'Counters to EEPROM',
        197 : 'Calculate ROM checksum',
        196 : 'Request creation date',
        195 : 'Request last modification date',
        194 : 'Request reject counter',
        193 : 'Request fraud counter',
        192 : 'Request build code',
        191 : 'Keypad control',
        190 : 'Request payout status',
        189 : 'Modify default sorter path',
        188 : 'Request default sorter path',
        187 : 'Modify payout capacity',
        186 : 'Request payout capacity',
        185 : 'Modify coin id',
        184 : 'Request coin id',
        183 : 'Upload window data',
        182 : 'Download calibration info',
        181 : 'Modify security setting',
        180 : 'Request security setting',
        179 : 'Modify bank select',
        178 : 'Request bank select',
        177 : 'Handheld function',
        176 : 'Request alarm counter',
        175 : 'Modify payout float',
        174 : 'Request payout float',
        173 : 'Request thermistor reading',
        172 : 'Emergency stop',
        171 : 'Request hopper coin',
        170 : 'Request base year',
        169 : 'Request address mode',
        168 : 'Request hopper dispense count',
        167 : 'Dispense hopper coins',
        166 : 'Request hopper status',
        165 : 'Modify variable set',
        164 : 'Enable hopper',
        163 : 'Test hopper',
        162 : 'Modify inhibit and override registers',
        161 : 'Pump RNG',
        160 : 'Request cipher key',
        159 : 'Read buffered bill events',
        158 : 'Modify bill id',
        157 : 'Request bill id',
        156 : 'Request country scaling factor',
        155 : 'Request bill position',
        154 : 'Route bill',
        153 : 'Modify bill operating mode',
        152 : 'Request bill operating mode',
        151 : 'Test lamps',
        150 : 'Request individual accept counter',
        149 : 'Request individual error counter',
        148 : 'Read opto voltages',
        147 : 'Perform stacker cycle',
        146 : 'Operate bi:directional motors',
        145 : 'Request currency revision',
        144 : 'Upload bill tables',
        143 : 'Begin bill table upgrade',
        142 : 'Finish bill table upgrade',
        141 : 'Request firmware upgrade capability',
        140 : 'Upload firmware',
        139 : 'Begin firmware upgrade',
        138 : 'Finish firmware upgrade',
        137 : 'Switch encryption code',
        136 : 'Store encryption code',
        135 : 'Set accept limit',
        134 : 'Dispense hopper value',
        133 : 'Request hopper polling value',
        132 : 'Emergency stop value',
        131 : 'Request hopper coin value',
        130 : 'Request indexed hopper dispense count',
        129 : 'Read barcode data',
        128 : 'Request money in',
        127 : 'Request money out',
        126 : 'Clear money counters',
        125 : 'Pay money out',
        124 : 'Verify money out',
        123 : 'Request activity register',
        122 : 'Request error status',
        121 : 'Purge hopper',
        120 : 'Modify hopper balance',
        119 : 'Request hopper balance',
        118 : 'Modify cashbox value',
        117 : 'Request cashbox value',
        116 : 'Modify real time clock',
        115 : 'Request real time clock',
        114 : 'Request USB id',
        113 : 'Switch baud rate',
        112 : 'Read encrypted events',
        111 : 'Request encryption support',
        110 : 'Switch encryption key',
        109 : 'Request encrypted hopper status',
        108 : 'Request encrypted monetary id',
        4 : 'Request comms revision',
        3 : 'Clear comms status variables',
        2 : 'Request comms status variables',
        1 : 'Reset device',
        0 : 'Reply'
        }

##
#
# Classes
#
##

##
#
# ccTalkPayload
#
# Used to manage the ccTalk payloads
#
##
class ccTalkPayload():

    def __init__(self, header='0', data=''):
        try:
            self.header = int(header)
        except TypeError, e:
            self.header=0
        self.data = data
        self.decodedHeader=''
        if self.header!='':
            self.headerType = headerTypes[self.header]
        else:
            self.headerType=''

    def parsePayload(self, header=0):
        """
        Processes the ccTalk payload and returns the interpreted data
        The header parameter is used to parse a ccTalk response
        """
        #Analyzing a response
        if self.header==0:
            #TODO: Add handling code for other headers 
            if header==230 or header==231:
                #Process inhibit status
                return self._extractChannelData()
            elif header==229:
                #Process coin event code status
                return self._extractCoinBuffer()
            elif header in [131, 145, 170, 171, 184, 192, 241, 242, 244, 245, 246]:
                #Process functions that return ASCII
                self.decodedHeader = str(self.data)
                return self.decodedHeader
            elif header==227:
                return self._extractEnableState()
            else:
                self.decodedHeader = self.data.encode('hex')
                return self.decodedHeader
        #Anlyzing a request
        else:
            #TODO: Add handling code for other functions
            if self.header==231:
                return self._extractChannelData()
            elif self.header==228:
                return self._extractEnableState()
            elif self.header in [184, 209]:
                return self._extractChannelInfo()
            else:
                self.decodedHeader = self.data.encode('hex')
                return self.decodedHeader

    def __repr__(self):
        """
        Returns a byte string representing the ccTalk payload
        """
        return chr(self.header) + self.data

    ##
    #
    # Private methods used to parse and extract response data
    #
    ##

    def _extractEnableState(self):
        if self.data=='\x01':
            self.decodedHeader = "State enabled"
        else:
            self.decodedHeader = "State disabled"
        return self.decodedHeader
        
    def _extractChannelInfo(self):
        self.decodedHeader = "Channel "+str(ord(self.data))
        return self.decodedHeader

    def _extractCoinBuffer(self):
        """
        Extracts event buffer response from request 229
        """
        data = self.data[1:]
        eventCpt = ord(self.data[0])
        self.decodedHeader = "Event Counter : "+str(eventCpt)+"\n"
        for resultA,resultB in zip(data,data[1:])[::2]:
            self.decodedHeader = self.decodedHeader + "Coin ID "+str(ord(resultA))+" - Error code "+str(ord(resultB))+"\n"
        self.decodedHeader = self.decodedHeader.strip()
        return self.decodedHeader

    def _extractChannelData(self):
        """
        Extract channel data
        Used with Headers 230 and 231 (Modify/Request Inhibit status)
        Gets the two bytes input and sends back an array containing the channel status
        1 - enabled
        0 - disabled
        """
        channels = []
        for byte in self.data:
            for bit in self._extractBits(ord(byte)):
                channels.append(bit)
            ch = 1
            enabledChannels=[]
            disabledChannels = []
            for channel in channels: 
                if channel ==1:
                    enabledChannels.append(ch)
                else:
                    disabledChannels.append(ch)
                ch = ch+1
        self.decodedHeader = "Enabled channels : " + str(enabledChannels) + "\nDisabled channels : " + str(disabledChannels) 
        return self.decodedHeader

    def _extractBits(self,byte):
        for i in xrange(8):
            yield (byte >> i) & 1


##
#
# ccTalkMessage
#
# Represents a ccTalk message
#
##
class ccTalkMessage():
    def __init__(self, data='', source=1, destination=2, header=0, payload=''):
        if data == '':
            #Creates a blank message
            self.destination = destination
            self.length = len(payload)
            self.source = source
            self.payload = ccTalkPayload(header, payload)
            #self.payload = ccTalkPayload()
        elif self._validateChecksum(data):
            #Generates a message using raw data
            self.destination = ord(data[0])
            self.length = ord(data[1])
            self.source = ord(data[2])
            header = ord(data[3])
            data = data[4:-1]
            self.payload = ccTalkPayload(header, data)
        else:
            raise Exception 

    def raw(self):
        """
        Returns a byte string representing the ccTalk message
        """
        return chr(self.destination)+chr(self.length)+chr(self.source)+repr(self.payload)+chr(self._calculateChecksum())

    def __len__(self):
        return len(chr(self.destination)+chr(self.length)+chr(self.source)+repr(self.payload)+chr(self._calculateChecksum()))

    def __repr__(self):
        """
        Returns a byte string representing the ccTalk message
        """
        return repr(chr(self.destination)+chr(self.length)+chr(self.source)+repr(self.payload)+chr(self._calculateChecksum()))

    def __str__(self):
        """
        Returns a user-friendly representation of the message
        """
        if self.payload.data !="":
            return "<cctalk src="+str(self.source)+" dst="+str(self.destination)+" length="+str(self.length)+" header="+str(self.payload.header)+" data="+self.payload.data.encode('hex')+">"
        else:
            return "<cctalk src="+str(self.source)+" dst="+str(self.destination)+" length="+str(self.length)+" header="+str(self.payload.header)+">"
                

    def setPayload(self, header, data=''):
        """
        Creates a new payload for the message
        """
        self.payload = ccTalkPayload(header, data)
        self.length = chr(len(data))

    def getPayload(self):
        return repr(self.payload)

    def _calculateChecksum(self):
        """
        Calculates the checksum for the message
        """
        data = chr(self.destination)+chr(self.length)+chr(self.source)+repr(self.payload)
        total = 0
        for byte in data:
            total = total + ord(byte)
        return 256-(total%256)

    def _validateChecksum(self, data):
        """
        Validates the checksum of a full message
        """
        total = 0
        for byte in data[:-1]:
            total = total + ord(byte)
        return (256-(total%256)==ord(data[-1]))

