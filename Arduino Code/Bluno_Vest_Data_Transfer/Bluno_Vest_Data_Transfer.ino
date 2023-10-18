//#include "CRC8.h"
#include "CRC8.h"
#include "CRC.h"
#include "Bluno_Variables_3.h"

// VEST
#define player 1 // Orange (50)
//#define player 2 // BLUE (20)

#include <Adafruit_NeoPixel.h>
#define neoPixelPin A2
#define numPixels 10
Adafruit_NeoPixel NeoPixel(numPixels, neoPixelPin, NEO_GRB + NEO_KHZ800);

int livesNum = 10; // number of HP (1 live, 10 HP, total = 100HP)
//int HP = 100;

#define RECV_PIN A3 // not pin 2
unsigned long triggertime = 0;
unsigned long serialtime = 0;
unsigned long receivetime = 0;
unsigned long pulsebuffer = 0;

int numOfChecks;

int lightuptime = 800;
int hitbywhichplayer = 0; // to send to internal comms
bool receiverstate = 0;
int pulsecheck = 0;

int pulsedelay;

//void health() {
//  HP -= 10;
//}

void playerShot(int livesNum) {
  
  // livesNum--;
  NeoPixel.clear();
  for(int x = 0; x < livesNum; x++) { // neopixel
      if (player ==  1) {
        NeoPixel.setPixelColor(x, NeoPixel.Color(242, 133, 0)); // orange
      } else if (player == 2) {
        NeoPixel.setPixelColor(x, NeoPixel.Color(0, 0, 255)); // blue
      }
    }
    NeoPixel.show(); 
    delay(1100);

  if(livesNum <= 0) {
    NeoPixel.clear();
    NeoPixel.show(); 
    delay(500);
    livesNum = 10;
  }
  
}


void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  NeoPixel.begin(); 
  NeoPixel.setBrightness(50);

   if (player == 1) {
      pulsedelay = 50; // align with player 2 gun
      numOfChecks = 4;
  } else if (player == 2) {
      pulsedelay = 20;   // align with player 1 gun
      numOfChecks = 5;
  }
  
}
///

void loop() {
  struct Hello_Packet hello_packet_response;

  NeoPixel.clear();
  if(livesNum == numPixels) {
     for(int x = 0; x < livesNum; x++) { // neopixel
        if (player ==  1) {
        NeoPixel.setPixelColor(x, NeoPixel.Color(242, 133, 0)); // orange
      } else if (player == 2) {
        NeoPixel.setPixelColor(x, NeoPixel.Color(0, 0, 255)); // blue
      }
    }
    NeoPixel.show(); 
  }
  
  // Check for data available
  while (Serial.available()) {
    if (index != 20) {
      
      byte data = Serial.read();
      incomingData[index] = data;
      index += 1;
    } 
  }

 

  
  if (index == 20) {
    index = 0;

    if (calculateCRC8(incomingData, 20) == 0){
      if (incomingData[PACKET_ID_INDEX] == DATA_PACKET_ID) {
        livesNum = incomingData[2] / 10;
      }
      
      // Sending Hello Packet
      if ((incomingData[PACKET_ID_INDEX] == HELLO_PACKET_ID) || (incomingData[PACKET_ID_INDEX] == CONN_EST_PACKET_ID)){
        // Hello Packet is correctly computed, hence write a response to send back to Relay Node.
        hello_packet_response = computeHelloPacketResponse();


        // If previous connected and Arduino is not powered off, then restart manually
        if ((hasReceivedHelloPacket == true) && (hasReceivedConnPacket)) {
          hasReceivedHelloPacket = false;
          hasReceivedConnPacket = false;
          isReadyToSendData = false;
        }

        // Make sure the 2 handshake start

         // Serial.println(String(hasReceivedHelloPacket) + " " + String(hasReceivedConnPacket));
        if (hasReceivedHelloPacket == false) {
          Serial.write((uint8_t*) &hello_packet_response, sizeof(hello_packet_response));  
          hasReceivedHelloPacket = true;  
          
        } else if (hasReceivedConnPacket == false) {
          Serial.write((uint8_t*) &hello_packet_response, sizeof(hello_packet_response));  
          hasReceivedConnPacket = true;
          isReadyToSendData = true; 
          
        }
      } 
//      else if (incomingData[PACKET_ID_INDEX] == ACK_PACKET_ID) {
//        isReadyToSendData = true;
//      }

      // Added in on October 11
      else if (incomingData[PACKET_ID_INDEX] == DATA_PACKET_ID) {
        livesNum = incomingData[2] / 10;
//        Serial.println(livesNum);/
        for(int x = 0; x < livesNum; x++) { // neopixel
          if (player ==  1) {
            NeoPixel.setPixelColor(x, NeoPixel.Color(242, 133, 0)); // orange
          } else if (player == 2) {
            NeoPixel.setPixelColor(x, NeoPixel.Color(0, 0, 255)); // blue
          }
        }
        NeoPixel.show(); 
      }
    }
  }
  
  
  // The part on sending data
  if (isReadyToSendData) {
    if(millis()>=pulsebuffer+pulsedelay)
    {
      
      pulsebuffer = millis();
      //Serial.println(pulsebuffer);
      if(receiverstate!=digitalRead(RECV_PIN))
      {
        
        // Serial.println(" DataFlipped");
        pulsecheck++;
        if(pulsecheck== numOfChecks)
        {
          
          struct Data_Packet data_packet;
          data_packet = computeDataPacketResponse(1);
          Serial.write((uint8_t*) &data_packet, sizeof(data_packet));
//          isReadyToSendData = f/alse;
          
          hitbywhichplayer = 1; // internal comms
          livesNum--;
          playerShot(livesNum);
          // health();
          receivetime=millis();
          //Serial.println("PulseConfirmed");
        }
      }
      else
      {
        pulsecheck = 0;
      }
      receiverstate = digitalRead(RECV_PIN);    
  
      if(hitbywhichplayer==1)
      {
        if(millis()<receivetime+lightuptime)
        {
          //Serial.println("HitReceived");
        }
        else
        {
          hitbywhichplayer=0;
        }
      }
    }
  
    // int IR_Value = random(0,2);
    //data_packet = computeDataPacketResponse(IR_Value);
    //Serial.write((uint8_t*) &data_packet, sizeof(data_packet));
    //isReadyToSendData = false;
  }
  delay(7);
  
  
  
}
    
    

      
    
      
   
