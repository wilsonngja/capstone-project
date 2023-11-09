import crc8
import struct
from PacketStructClass import HelloPacket

PacketWOChecksumFormat = "BBHHHHHHHHB"
PacketFormat = "BBHHHHHHHHBB"

def calculate_crc8(Packet):
    crc = crc8.crc8()
    crc.reset()
    crc.update(Packet)
    
    return (crc.digest())[0]

def pack_data(DataPkt, bullet):
    global PacketWOChecksumFormat
    global PacketFormat
    
    crc = crc8.crc8()
    crc.reset()

    DataPkt.data = bullet
    DataPacketWOChecksum = struct.pack(PacketWOChecksumFormat,
                                    DataPkt.device_id,
                                    DataPkt.packet_id,
                                    DataPkt.data,
                                    DataPkt.padding_1,
                                    DataPkt.padding_2,
                                    DataPkt.padding_3,
                                    DataPkt.padding_4,
                                    DataPkt.padding_5,
                                    DataPkt.padding_6,
                                    DataPkt.padding_7,
                                    DataPkt.padding_8,
                                    )
    
    DataPkt.checksum = calculate_crc8(DataPacketWOChecksum)
    return struct.pack(PacketFormat,
                    DataPkt.device_id,
                    DataPkt.packet_id,
                    DataPkt.data,
                    DataPkt.padding_1,
                    DataPkt.padding_2,
                    DataPkt.padding_3,
                    DataPkt.padding_4,
                    DataPkt.padding_5,
                    DataPkt.padding_6,
                    DataPkt.padding_7,
                    DataPkt.padding_8,
                    DataPkt.checksum)


def pack_data(HelloPacket):
    crc = crc8.crc8()
    crc.reset()

    HelloPacketWOChecksum = struct.pack(PacketWOChecksumFormat,
                                    HelloPacket.device_id,
                                    HelloPacket.packet_id,
                                    HelloPacket.padding_1,
                                    HelloPacket.padding_2,
                                    HelloPacket.padding_3,
                                    HelloPacket.padding_4,
                                    HelloPacket.padding_5,
                                    HelloPacket.padding_6,
                                    HelloPacket.padding_7,
                                    HelloPacket.padding_8,
                                    HelloPacket.padding_9)
    
    HelloPacket.checksum = calculate_crc8(HelloPacketWOChecksum)
    return struct.pack(PacketFormat, 
                    HelloPacket.device_id,
                    HelloPacket.packet_id,
                    HelloPacket.padding_1,
                    HelloPacket.padding_2,
                    HelloPacket.padding_3,
                    HelloPacket.padding_4,
                    HelloPacket.padding_5,
                    HelloPacket.padding_6,
                    HelloPacket.padding_7,
                    HelloPacket.padding_8,
                    HelloPacket.padding_9,
                    HelloPacket.checksum)

def pack_ack_data(Packet):
    crc = crc8.crc8()
    crc.reset()

    AckPacketWOChecksum = struct.pack("BBHHHHHHHHB",
                                Packet.device_id,
                                Packet.packet_id,
                                Packet.padding_1,
                                Packet.padding_2,
                                Packet.padding_3,
                                Packet.padding_4,
                                Packet.padding_5,
                                Packet.padding_6,
                                Packet.padding_7,
                                Packet.padding_8,
                                Packet.padding_9)
    
    Packet.checksum = calculate_crc8(AckPacketWOChecksum)
    
    return struct.pack(PacketFormat, 
                    Packet.device_id,
                    Packet.packet_id,
                    Packet.padding_1,
                    Packet.padding_2,
                    Packet.padding_3,
                    Packet.padding_4,
                    Packet.padding_5,
                    Packet.padding_6,
                    Packet.padding_7,
                    Packet.padding_8,
                    Packet.padding_9,
                    Packet.checksum)


def pack_data_result(DataPacket):
    crc = crc8.crc8()
    crc.reset()
    
    DataPacketWOChecksum = struct.pack(PacketWOChecksumFormat,
                                DataPacket.device_id,
                                DataPacket.packet_id,
                                DataPacket.data,
                                DataPacket.padding_1,
                                DataPacket.padding_2,
                                DataPacket.padding_3,
                                DataPacket.padding_4,
                                DataPacket.padding_5,
                                DataPacket.padding_6,
                                DataPacket.padding_7,
                                DataPacket.padding_8)
    
    DataPacket.checksum = calculate_crc8(DataPacketWOChecksum)
    
    return struct.pack(PacketFormat, 
                    DataPacket.device_id,
                    DataPacket.packet_id,
                    DataPacket.data,
                    DataPacket.padding_1,
                    DataPacket.padding_2,
                    DataPacket.padding_3,
                    DataPacket.padding_4,
                    DataPacket.padding_5,
                    DataPacket.padding_6,
                    DataPacket.padding_7,
                    DataPacket.padding_8,
                    DataPacket.checksum)