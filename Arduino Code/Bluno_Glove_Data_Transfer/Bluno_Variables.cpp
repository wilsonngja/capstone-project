#include "Bluno_Variables.h"

byte incomingData[20];
int index = 0;

bool hasReceivedHelloPacket = false;
bool hasReceivedConnPacket = false;

bool isReadyToSendData = false;

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

Data_Packet computeDataPacketResponse() {
  Data_Packet data_packet;
  data_packet.Device_ID = BLUNO_1_DEVICE_ID;
  data_packet.Packet_ID = DATA_PACKET_ID;
  
  data_packet.GyroscopeX = random(0, 1023);
  data_packet.GyroscopeY = random(0, 1023);
  data_packet.GyroscopeZ = random(0, 1023);

  data_packet.AccelerometerX = random(0, 1023);
  data_packet.AccelerometerY = random(0, 1023);
  data_packet.AccelerometerZ = random(0, 1023);

  data_packet.FlexValue = random(0,1023);
  data_packet.FlexValue2 = random(0,1023);
  data_packet.Padding_1 = 0;

  data_packet.Checksum = calculateCRC8(&data_packet, 19);

  return data_packet;
}
