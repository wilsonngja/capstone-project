#include "Bluno_Variables.h"
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>


byte incomingData[20];
int index = 0;

bool hasReceivedHelloPacket = false;
bool hasReceivedConnPacket = false;

bool isReadyToSendData = true;

//Adafruit_MPU6050 imu;

//float VCC = 5;
//float flexResistor = 10000; //10K Ohms
//
//float flexMinResistance = 40000;
//float flexMaxResistance = 300000;
//float baseFlexValue = 16;
//float flexInterval = 10;

uint8_t calculateCRC8(void* hello_packet, int packet_length) {
  CRC8 crc(7, 0, 0, false, false);

  crc.reset();
  crc.add((uint8_t*)hello_packet, packet_length);  

  return crc.calc();
}

Hello_Packet computeHelloPacketResponse() {
  Hello_Packet hello_packet_response;

  hello_packet_response.Device_ID = BLUNO_1_DEVICE_ID;
  hello_packet_response.Packet_ID = HELLO_PACKET_ID;
  hello_packet_response.Padding_1 = 0;
  hello_packet_response.Padding_2 = 0;
  hello_packet_response.Padding_3 = 0;
  hello_packet_response.Padding_4 = 0;
  hello_packet_response.Padding_5 = 0;
  hello_packet_response.Padding_6 = 0;
  hello_packet_response.Padding_7 = 0;
  hello_packet_response.Padding_8 = 0;
  hello_packet_response.Padding_9 = 0;
  hello_packet_response.Checksum = calculateCRC8(&hello_packet_response, 19);

  return hello_packet_response;
}

Data_Packet computeDataPacketResponse(struct Glove_Data glove_data) {
  Data_Packet data_packet;
  data_packet.Device_ID = BLUNO_1_DEVICE_ID;
  data_packet.Packet_ID = DATA_PACKET_ID;
  
  data_packet.GyroscopeX = glove_data.GyroX;
  data_packet.GyroscopeY = glove_data.GyroY;
  data_packet.GyroscopeZ = glove_data.GyroZ;

  data_packet.AccelerometerX = glove_data.AccX;
  data_packet.AccelerometerY = glove_data.AccY;
  data_packet.AccelerometerZ = glove_data.AccZ;

  data_packet.FlexValue = glove_data.Flex1;
  data_packet.FlexValue2 = glove_data.Flex2;
  data_packet.Padding_1 = 0;

  data_packet.Checksum = calculateCRC8(&data_packet, 19);

  return data_packet;
}

int mapAcc(float accValue) {
  accValue = accValue * 10;
  int map_accValue = map(accValue, -78.4, 78.4, 0, 1023);
  map_accValue = constrain(accValue, 0, 1023); 

  return map_accValue;
}

int mapGyro(float gyroValue) {
  gyroValue = gyroValue * 100;
  int map_gyroValue = map(gyroValue, -500, 500, 0, 1023);
  map_gyroValue = constrain(gyroValue, 0, 1023);

  return map_gyroValue; 
}



//int getFlexSensorValue(const int flexPin) {
//  
//  int ADCRaw = analogRead(flexPin);
//  float ADCVoltage = (ADCRaw * VCC) / 1023;
//
//  float resistance = flexResistor * (VCC / ADCVoltage - 1);
//  int flexValue  = map(resistance, flexMinResistance, flexMaxResistance, 0, 20);
//  flexValue = constrain(flexValue, 0, 20);
//
//  return flexValue;
//}

//void setupImu(Adafruit_MPU6050 imu) {
//  if (!imu.begin()) {
//    while (1) {
//      delay(10);
//    }
//  }
//  
//  // Set accelerometer range to +- 8G (Gravitational Strength)
//  imu.setAccelerometerRange(MPU6050_RANGE_8_G);
//
//  // Set Gyro range to +- 500 deg/s
//  imu.setGyroRange(MPU6050_RANGE_500_DEG);
//
//  // Set Filter bandwidth of digital lowpass filter to 21 Hz. For smoothing of signal & removal of high freq noise
//  imu.setFilterBandwidth(MPU6050_BAND_21_HZ);
//
//  delay(10);
//}
//
//Glove_Data getGloveReadings(Adafruit_MPU6050 imu) {
//  
//  sensors_event_t a,g, temp;
//  imu.getEvent(&a, &g, &temp);
//
//  Glove_Data gloveData;
//  
//  gloveData.GyroX = mapGyro(g.gyro.x);
//  gloveData.GyroY = mapGyro(g.gyro.y);
//  gloveData.GyroZ = mapGyro(g.gyro.z);
//
//  gloveData.AccX = mapAcc(a.acceleration.x);
//  gloveData.AccY = mapAcc(a.acceleration.y);
//  gloveData.AccZ = mapAcc(a.acceleration.z);
//
//  gloveData.Flex1 = getFlexSensorValue(FLEX_PIN1);
//  gloveData.Flex2 = getFlexSensorValue(FLEX_PIN2);
//
//  return gloveData;
//}
