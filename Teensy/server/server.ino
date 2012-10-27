int MYADDRESS = 1;
int state = 0;

//Channel value, each channel got its number of credits to add
int channelValue[] = {0,0,0,0,1,0,2,0,5,0,0,0,0,0,0,0};
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
  byte buff[] = {0x02,0x00,0x01,0xfe,0xff};
  Uart.write(buff,5);
  Uart.flush();
}

void sendInhibits(){
  byte buff1[] = {0x02,0x02,0x01,0xe7,0xff,0xff,0x16};
  Uart.write(buff1,7);
  Uart.flush();
  delay(500);
  byte buff2[] = {0x02,0x01,0x01,0xe4,0x01,0x17};
  Uart.write(buff2,6);
  Uart.flush();
}

void sendManufID(){
  byte buff[] = {0x02,0x00,0x01,0xf6,0x07};
  Uart.write(buff,5);
  Uart.flush();
}

void sendProdCode(){
  byte buff[] = {0x02,0x00,0x01,0xf4,0x09};
  Uart.write(buff,5);
  Uart.flush();
}

void sendCredits(){
  byte buff[] = {0x02,0x00,0x01,0xe5,0x18};
  Uart.write(buff,5);
}

void sendCreditKey(int number){
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
      
        sendCreditKey(channelValue[channel-1]);
        Serial.print("Added ");
        Serial.print(channelValue[channel-1]);
        Serial.println(" credits.");
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
  
    Serial.print("Got packet, waiting for ");
    Serial.print(length+3);
    Serial.println(" bytes of data");
    
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


