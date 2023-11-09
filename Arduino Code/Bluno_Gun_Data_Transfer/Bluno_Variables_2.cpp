#include "Bluno_Variables_2.h"

byte incomingData[20];
int index = 0;

bool hasReceivedHelloPacket = false;
bool hasReceivedConnPacket = false;

bool isReadyToSendData = false;

uint8_t calculateCRC8(void* ack_packet, int packet_length) {
  CRC8 crc(7, 0, 0, false, false);

  crc.reset();
  crc.add((uint8_t*)ack_packet, packet_length);  

  return crc.calc();
}

Ack_Packet computeAckPacketResponse() {
  Ack_Packet ack_packet_response;

  ack_packet_response.Device_ID = BLUNO_2_DEVICE_ID;
  ack_packet_response.Packet_ID = ACK_PACKET_ID;
  ack_packet_response.Padding_1 = 0;
  ack_packet_response.Padding_2 = 0;
  ack_packet_response.Padding_3 = 0;
  ack_packet_response.Padding_4 = 0;
  ack_packet_response.Padding_5 = 0;
  ack_packet_response.Padding_6 = 0;
  ack_packet_response.Padding_7 = 0;
  ack_packet_response.Padding_8 = 0;
  ack_packet_response.Padding_9 = 0;
  ack_packet_response.Checksum = calculateCRC8(&ack_packet_response, 19);
  
  return ack_packet_response;
}

Data_Packet computeDataPacketResponse() {
  Data_Packet data_packet;
  data_packet.Device_ID = BLUNO_2_DEVICE_ID;
  data_packet.Packet_ID = DATA_PACKET_ID;
  
  data_packet.LEDState = 1;
  data_packet.Padding_1 = 0;
  data_packet.Padding_2 = 0;

  data_packet.Padding_3 = 0;
  data_packet.Padding_4 = 0;
  data_packet.Padding_5 = 0;

  data_packet.Padding_6 = 0;
  data_packet.Padding_7 = 0;
  data_packet.Padding_8 = 0;

  data_packet.Checksum = calculateCRC8(&data_packet, 19);

  return data_packet;
}
