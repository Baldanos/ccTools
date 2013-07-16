/*
Copyright (C) 2012 Nicolas Oberli

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
*/

//The devide address
int MYADDRESS = 1;
//Initial state of the event counter
int state = 0;

//Channel value, each channel got its number of credits to add
//Change the values in this table to match between channels and credits
//Here, channel 5 means 1 credit, channel 7 means 2 credits and channel 9 is 5 credits
int channelValue[] = {0,0,0,0,0,1,0,2,0,5,0,0,0,0,0,0,0};

//The credit key to play on the keyboard
char creditKey = KEY_5;


byte buffer[50];
boolean isMessage = false;

HardwareSerial Uart = HardwareSerial();

void disableRx(){
  UCSR1B &= ~(1<<RXEN1); // use UCSR0B and RXEN0 to use with Arduino
}

void enableRx(){
  UCSR1B |= (1<<RXEN1); // use UCSR0B and RXEN0 to use with Arduino
}

void sendSimplePoll(){
  //Sends a simple poll
  //<cctalk src=1 dst=2 length=0 header=254>
  byte buff[] = {0x02,0x00,0x01,0xfe,0xff};
  Uart.write(buff,5);
  Uart.flush();
}

void sendInhibits(){
  //Sends a change inhibit status request to enable all channels
  //<cctalk src=1 dst=2 length=2 header=231 data=ffff>
  byte buff1[] = {0x02,0x02,0x01,0xe7,0xff,0xff,0x16};
  Uart.write(buff1,7);
  Uart.flush();
  delay(500);
  byte buff2[] = {0x02,0x01,0x01,0xe4,0x01,0x17};
  Uart.write(buff2,6);
  Uart.flush();
}

void sendManufID(){
  //Requests manufacturer ID
  //<cctalk src=1 dst=2 length=0 header=246>
  byte buff[] = {0x02,0x00,0x01,0xf6,0x07};
  Uart.write(buff,5);
  Uart.flush();
}

void sendProdCode(){
  //Requests product code
  //<cctalk src=1 dst=2 length=0 header=244>
  byte buff[] = {0x02,0x00,0x01,0xf4,0x09};
  Uart.write(buff,5);
  Uart.flush();
}

void sendCredits(){
  //Requests credit status
  //<cctalk src=1 dst=2 length=0 header=229>
  byte buff[] = {0x02,0x00,0x01,0xe5,0x18};
  Uart.write(buff,5);
}

void sendCreditKey(int number){
  //Sends the credits with the keyboard
  while (number!=0) {
    Keyboard.set_key1(creditKey);
    Keyboard.send_now();
    delay(20);
    Keyboard.set_key1(0);
    Keyboard.send_now();
    delay(50);
    number--;
  }
}

void setup() {
  //Init LED pin
  pinMode(6, OUTPUT);
  
  //Init pullup for the bus
  pinMode(17, INPUT_PULLUP);
  
  //Init Uart and ccTalk device
  Uart.begin(9600);
  
  Serial.begin(9600);
  
  //Init coin acceptor
  disableRx();
  sendSimplePoll();
  delay(500);
  sendInhibits();
  delay(500);
  sendManufID();
  delay(500);
  sendProdCode();
  delay(500);
  enableRx();
  
  while(Uart.available()){
    Uart.read();
  }
  
  digitalWrite(6, LOW);
  
}

 
void loop() {  
  //Request credits
  sendCredits();
  
  //Read responses
  readPacket();
  
  if (isMessage) {
    if (state<buffer[4]) {
      int channel = int(buffer[5]);
      if (channel <= 16) {
        Serial.println(channel, DEC);
        Serial.print("Adding ");
        Serial.print(channelValue[channel]);
        Serial.println(" credits.");
        sendCreditKey(channelValue[channel]);
      }
      if (state == 255) {
        state = 1;
      }else{
        state++;
      }
    }
    isMessage = false;
  }
  delay(500);
}

//
//Handles incoming ccTalk messages
//
void readPacket() {
  
  bool isError = false;
  
  while(Uart.available()>=2){
    
    int dest = Uart.read();
    int length = Uart.read();
  
    //Serial.print("Got packet, waiting for ");
    //Serial.print(length+3);
    //Serial.println(" bytes of data");
    
    //Wait for full message bytes, or end receive loop
    while (Uart.available() < length+3){
      delay(50);
      if (Uart.available() < length+3) {
        isError=true;
        break;
      }
    }
    if(isError) {
      Serial.println("[*]Impossible to fetch packet data, flushing");
      while (Uart.available()) {
        Uart.read();
      }
      break;
    }
    
    
    buffer[0] = dest;
    buffer[1] = length;
    
    for (int i=2;i<length+5;i++) {
      buffer[i] = Uart.read();
    }
    
    int sum = 0;
    for (int i=0;i<length+4;i++){
      sum += (int)buffer[i];
    }

    if (! (buffer[length+4] == 256-(sum%256))) {
      Serial.println("Packet is invalid, flushing");
      delay(50);
      for (int i=0;i<20;i++){
        Serial.print(buffer[i], HEX);
        Serial.print(" ");
      }
      Serial.println(" ");
      while (Uart.available()){
        Uart.read();
      }
    }
    
    if (dest == MYADDRESS) {
      isMessage = true;
      break;
    }
  }
}


