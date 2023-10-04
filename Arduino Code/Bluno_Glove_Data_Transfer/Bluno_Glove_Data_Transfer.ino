//#include "CRC8.h"
#include "CRC8.h"
#include "CRC.h"
#include "Bluno_Variables.h"
#include <Adafruit_MPU6050.h>

Adafruit_MPU6050 imu;


float flexMinResistance = 40000;
float flexMaxResistance = 300000;
float baseFlexValue = 16;
float flexInterval = 10;



float VCC = 5;
float flexResistor = 10000; //10K Ohms


void setupImu() {
  if (!imu.begin()) {
    while (1) {
      delay(10);
    }
  }
  
  // Set accelerometer range to +- 8G (Gravitational Strength)
  imu.setAccelerometerRange(MPU6050_RANGE_8_G);

  // Set Gyro range to +- 500 deg/s
  imu.setGyroRange(MPU6050_RANGE_500_DEG);

  // Set Filter bandwidth of digital lowpass filter to 21 Hz. For smoothing of signal & removal of high freq noise
  imu.setFilterBandwidth(MPU6050_BAND_21_HZ);

  delay(10);
}

int getFlexSensorValue(const int flexPin) {
  
  int ADCRaw = analogRead(flexPin);
  float ADCVoltage = (ADCRaw * VCC) / 1023;

  float resistance = flexResistor * (VCC / ADCVoltage - 1);
  float flexValue  = map(resistance, flexMinResistance, flexMaxResistance, 0, 20);
  flexValue = constrain(flexValue, 0, 20);

  return flexValue;
}

Glove_Data getGloveReadings() {
  
  sensors_event_t a,g, temp;
  imu.getEvent(&a, &g, &temp);

  Glove_Data gloveData;

//    Serial.print("GyroX: " +  String(g.gyro.x) + " ");
//    Serial.print("GyroY: " +  String(g.gyro.y) + " ");
//    Serial.print("GyroZ: " +  String(g.gyro.z) + " ");
//
//    Serial.print("AccX: " + String(g.acceleration.x) + " ");
//    Serial.print("AccY: " + String(g.acceleration.y) + " ");
//    Serial.print("AccZ: " + String(g.acceleration.z) + " ");
//
//    Serial.print("Flex1: " + String(getFlexSensorValue(FLEX_PIN1)) + " ");
//    Serial.println("Flex2: " + String(getFlexSensorValue(FLEX_PIN2)) + " ");

  gloveData.GyroX = mapGyro(g.gyro.x);
  gloveData.GyroY = mapGyro(g.gyro.y);
  gloveData.GyroZ = mapGyro(g.gyro.z);

  gloveData.AccX = mapAcc(a.acceleration.x);
  gloveData.AccY = mapAcc(a.acceleration.y);
  gloveData.AccZ = mapAcc(a.acceleration.z);

  gloveData.Flex1 = getFlexSensorValue(FLEX_PIN1);
  gloveData.Flex2 = getFlexSensorValue(FLEX_PIN2);

  return gloveData;
}


void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);

  pinMode(FLEX_PIN1, INPUT);
  pinMode(FLEX_PIN2, INPUT);

  
  setupImu();  
}


void loop() {
  struct Hello_Packet hello_packet_response;
  
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
        if (hasReceivedHelloPacket == false) {
          Serial.write((uint8_t*) &hello_packet_response, sizeof(hello_packet_response));  
          hasReceivedHelloPacket = true;  
        } else if (hasReceivedConnPacket == false) {
          Serial.write((uint8_t*) &hello_packet_response, sizeof(hello_packet_response));  
          hasReceivedConnPacket = true;
          isReadyToSendData = true; 
        }
      } 


       
    }
  }
  

  // The part on sending data
  if (isReadyToSendData) {
    struct Data_Packet data_packet;
    struct Glove_Data glove_data;

    glove_data = getGloveReadings();

  //    glove_data.GyroX = random(0, 1023);
  //    glove_data.GyroY = random(0, 1023);
  //    glove_data.GyroZ = random(0, 1023);
  //
  //    glove_data.AccX = random(0, 1023);
  //    glove_data.AccY = random(0, 1023);
  //    glove_data.AccZ = random(0, 1023);
  //
  //    glove_data.Flex1 = random(0, 1023);
  //    glove_data.Flex2 = random(0, 1023);

    Serial.print("GyroX: " +  String(glove_data.GyroX) + " ");
    Serial.print("GyroY: " +  String(glove_data.GyroY) + " ");
    Serial.print("GyroZ: " +  String(glove_data.GyroZ) + " ");

    Serial.print("AccX: " + String(glove_data.AccX) + " ");
    Serial.print("AccY: " + String(glove_data.AccY) + " ");
    Serial.print("AccZ: " + String(glove_data.AccZ) + " ");

    Serial.print("Flex1: " + String(glove_data.Flex1) + " ");
    Serial.println("Flex2: " + String(glove_data.Flex2) + " ");
    data_packet = computeDataPacketResponse(glove_data);
//    Serial.write((uint8_t*) &data_packet, sizeof(data_packet));
  }
  delay(10);
  
  
}
    
    

      
    
      
   
