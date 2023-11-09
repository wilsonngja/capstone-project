//#include "CRC8.h"
#include "CRC8.h"
#include "CRC.h"
#include "Bluno_Variables_2.h"

#include <Adafruit_NeoPixel.h>

int lastButtonState = HIGH;
int currentButtonState;

int shotNum = 0;

#define neoPixelPin 2
#define numPixels 6
Adafruit_NeoPixel NeoPixel(numPixels, neoPixelPin, NEO_GRB + NEO_KHZ800);
#define ledPin A0

volatile byte pulse = 0;

#define NPN_SIGNAL_PIN 3
#define NPN_BASE_PIN 4
#define PB_PIN 5

unsigned long triggerTime = 0;
unsigned long serialTime = 0;
unsigned long receiveTime = 0;
unsigned long pulseTime = 0;

bool activatePulse = 0;
bool pulseState = 0;
int bullets = 6;
int prevBullets;
//bool enableLED = 1;

int i = 0;

int player = 2;
int pulseDelay = (player == 1) ?  20 : 50;
int shootTime = 400;
int cooldownTime = 800;

bool shotFired = false;
int reload = 0;

ISR(TIMER2_COMPB_vect) {
  pulse++;
  if (pulse >= 8) {
    pulse = 0;
    TCCR2A ^= _BV(COM2B1);
  }
}

void setIrModOutput() {
  pinMode(NPN_SIGNAL_PIN, OUTPUT);
  TCCR2A = _BV(COM2B1) | _BV(WGM21) | _BV(WGM20); // Just enable output on Pin 3 
  TCCR2B = _BV(WGM22) | _BV(CS22);
  OCR2A = 51; // defines the frequency 51 = 38.4 KHz, 54 = 36.2 KHz, 58 = 34 KHz, 62 = 32 KHz
  OCR2B = 26;  // deines the duty cycle - Half the OCR2A value for 50%
  TCCR2B = TCCR2B & 0b00111000 | 0x2; // select a prescale value of 8:1 of the system clock
}


void setLEDS()
{
    NeoPixel.clear();
    for (int i = 0; i < bullets; i += 1)
    {
        if (player == 1)
        {
            NeoPixel.setPixelColor(i, NeoPixel.Color(25, 21, 0)); // orange
        }
        else if (player == 2)
        {
            NeoPixel.setPixelColor(i, NeoPixel.Color(0, 0, 25)); // blue
        }
    }
    NeoPixel.show();
}


void setup() {
  Serial.begin(115200);
  NeoPixel.begin();
  pinMode(PB_PIN, INPUT_PULLUP);
  pinMode(NPN_BASE_PIN, OUTPUT);
  pinMode(ledPin, OUTPUT);

  setIrModOutput();
  TIMSK2 = _BV(OCIE2B);
  NeoPixel.clear();
  for (int x = 5; x >= 0; x--)
  { // neopixel
      if (player == 1)
      {
          NeoPixel.setPixelColor(x, NeoPixel.Color(25, 21, 0)); // orange
      }
      else if (player == 2)
      {
          NeoPixel.setPixelColor(x, NeoPixel.Color(0, 0, 25)); // blue
      }
  }
  NeoPixel.show(); 
}


void loop() {
  struct Ack_Packet ack_packet_response;
  
  // Check for data available
  if (Serial.available()) {
    byte data = Serial.read();
    if (data == BLUNO_2_DEVICE_ID) {
      index = 0;
    }
    incomingData[index] = data;
    index += 1;
  }

  // When full Data Packet arrive
  if (index == 20) {
    index = 0;

    // If checksum is correct (0)    
    if (calculateCRC8(incomingData, 20) == 0){
      
      // If receiving packet is the Hello Packet for Handshaking
      if (incomingData[PACKET_ID_INDEX] == HELLO_PACKET_ID) {
        isReadyToSendData = false;
        ack_packet_response = computeAckPacketResponse();
        Serial.write((uint8_t*) &ack_packet_response, sizeof(ack_packet_response));
      } else if (incomingData[PACKET_ID_INDEX] == CONN_EST_PACKET_ID) {
        isReadyToSendData = true;
        ack_packet_response = computeAckPacketResponse();
        Serial.write((uint8_t*) &ack_packet_response, sizeof(ack_packet_response));
      } else if (incomingData[PACKET_ID_INDEX] == DATA_PACKET_ID) {
        prevBullets = bullets;
        bullets = incomingData[2];
        if (bullets != prevBullets) {
          setLEDS();
        }
        Serial.write((uint8_t*) &ack_packet_response, sizeof(ack_packet_response)); 
      }
      
      /*
      if ((incomingData[PACKET_ID_INDEX] == HELLO_PACKET_ID) || (incomingData[PACKET_ID_INDEX] == CONN_EST_PACKET_ID)){
        // Hello Packet is correctly computed, hence write a response to send back to Relay Node.
        ack_packet_response = computeAckPacketResponse();


        // If previous connected and Arduino is not powered off, then restart manually


         
        if ((hasReceivedHelloPacket == true) && (hasReceivedConnPacket)) {
          hasReceivedHelloPacket = false;
          hasReceivedConnPacket = false;
          isReadyToSendData = false;
        }

        // Make sure the 2 handshake start
        if (hasReceivedHelloPacket == false) {
          Serial.write((uint8_t*) &ack_packet_response, sizeof(ack_packet_response));  
          hasReceivedHelloPacket = true;  
        } else if (hasReceivedConnPacket == false) {
          Serial.write((uint8_t*) &ack_packet_response, sizeof(ack_packet_response));  
          hasReceivedConnPacket = true;
          isReadyToSendData = true; 
        }
      } 
      */

      /*
      // Added in on October 11
      if (incomingData[PACKET_ID_INDEX] == DATA_PACKET_ID) {
        // minimise calls to LEDs
        prevBullets = bullets;
        bullets = incomingData[2];
        if (bullets != prevBullets) {
          setLEDS();
        }
        Serial.write((uint8_t*) &ack_packet_response, sizeof(ack_packet_response));   
      }
      */

    }
  }

  // The part on sending data
  if (isReadyToSendData) {
    struct Data_Packet data_packet;
  
    currentButtonState = digitalRead(PB_PIN);

    // Gun - Trigger is pressed
    if(lastButtonState == LOW && currentButtonState == HIGH and !shotFired) { // button pressed
      activatePulse = 1;
      triggerTime = millis();
      if (bullets > 0) {
        bullets--;
        setLEDS();
        digitalWrite(ledPin, HIGH); // led
        delay(10);
        digitalWrite(ledPin, LOW);
      } 
      shotFired = true;
      struct Data_Packet data_packet;
    
      data_packet = computeDataPacketResponse();
      Serial.write((uint8_t*) &data_packet, sizeof(data_packet));
    }
    else if(lastButtonState == HIGH && currentButtonState == LOW) {
    }
    // save the last state
    lastButtonState = currentButtonState;
  
    // Gun - Cease shooting after shoot time has passed
    if (millis() >= triggerTime + shootTime) {
      activatePulse = 0;
    }

    if (millis() >= triggerTime + cooldownTime) {
      shotFired = false;
    }

    // Gun - Activate pulse signal with pulseTime delay
    if (activatePulse == 1) {
      if (millis() >= pulseTime + pulseDelay) {
        digitalWrite(NPN_BASE_PIN, pulseState);
        pulseState = !pulseState;
        pulseTime = millis();
      }
    }

    if (activatePulse == 0) {
      digitalWrite(NPN_BASE_PIN, LOW);
    }  
  }
  delay(7);
  
}
