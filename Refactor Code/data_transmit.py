# Import Libraries
from bluepy.btle import Peripheral, UUID, DefaultDelegate, BTLEDisconnectError
from PacketStructClass import HelloPacket, AckPacket

import threading
import sys
import time
import CRC8Packet
import struct
import os
import random

from paho.mqtt import client as mqttclient
from queue import Queue

from time import perf_counter

import socket
import json
import asyncio


index  = 1

# YELLOW/WHITE = PLAYER 1
# BLUE = PLAYER 2
NODE_DEVICE_ID = 0

# Device IDs
PLAYER_1_GLOVE_DEVICE_ID = 1
PLAYER_1_GUN_DEVICE_ID = 2
PLAYER_1_VEST_DEVICE_ID = 3

# Packet IDs
HELLO_PACKET_ID = 0
CONN_EST_PACKET_ID = 1
ACK_PACKET_ID = 2
NAK_PACKET_ID = 3
DATA_PACKET_ID = 4

# Colors
YELLOW = "\033[93m"
END = '\033[0m'

# Characteristic Objects
chGlove1 = None
chGun1 = None
chVest1 = None

# Player 1 MAC Addresses
PLAYER_1_GLOVE_MAC_ADDRESS = "D0:39:72:E4:93:9D"
PLAYER_1_GUN_MAC_ADDRESS = "D0:39:72:E4:80:A8"
PLAYER_1_VEST_MAC_ADDRESS = "D0:39:72:E4:86:B8"

# Player 2 MAC Addresses
PLAYER_2_GLOVE_MAC_ADDRESS = "D0:39:72:E4:93:BC"
PLAYER_2_GUN_MAC_ADDRESS = "D0:39:72:E4:8C:05"
PLAYER_2_VEST_MAC_ADDRESS = "D0:39:72:E4:91:AC"

# Player X MAC Address
PLAYER_3_GLOVE_MAC_ADDRESS ="D0:39:72:C8:54:8D"
PLAYER_3_GUN_MAC_ADDRESS = "D0:39:72:C8:56:46"
PLAYER_3_VEST_MAC_ADDRESS = "D0:39:72:C8:57:2E"

DEVICE = {1: "GLOVE", 2: "GUN", 3: "VEST"}

PACKET_FORMAT = "BBHHHHHHHHBB"

# Data Packet Size
DATA_PACKET_SIZE = 20

# Handshaking Acknowledgement
helloPacketReceivedGlove1 = False
helloPacketReceivedGun1 = False
helloPacketReceivedVest1 = False
connPacketReceivedGlove1 = False
connPacketReceivedGun1 = False
connPacketReceivedVest1 = False

# Byte Array for Player 1
byteArrayGlove1 = bytearray()
byteArrayGun1 = bytearray()
byteArrayVest1 = bytearray()

# Error Count (Fragmentation)
errorCountGlove1 = 0
errorCountGun1 = 0
errorCountVest1 = 0

# Tuple Data Player 1
tupleDataGlove1 = None
tupleDataGun1 = None
tupleDataVest1 = None

# Start Time
start_time = time.time()

# Bluno Object
blunoGlove1 = None
blunoGun1 = None
blunoVest1 = None

# Relay 
BROKER = 'broker.emqx.io'
relay_queue = Queue()
mqtt_queue = Queue()

# Notification Timeout Duration
NOTIFICATION_TIMEOUT = 3

# Checksum correct value
CHECKSUM_CORRECT_VALUE = 0

# Maximum Error before assuming fragmentation issue
ERROR_MAX_COUNT = 3

msg = None
hp = None
bullets = None

sensortimer = perf_counter()


class RelayClient:
    def __init__(self, sn):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sn = int(sn)

    async def send_message(self, msg):
        self.sock.sendall(bytes((str(len(msg)) + '_'), encoding="utf-8"))
        self.sock.sendall(bytes(msg, encoding="utf-8"))
    
    async def main(self):
        self.sock.connect(('172.26.190.39', 10000 + self.sn)) 
        print("connected")

        while True:
            if not relay_queue.empty():
                msg = relay_queue.get()
                await self.send_message(msg)
                print("sent:" + msg)

    def run(self):
        try:
            asyncio.run(self.main())
        except KeyboardInterrupt:
            pass

class MQTTClient:

    def __init__(self, sn):
        self.sn = int(sn)

    def connect_mqtt(self):
        # Set Connecting Client ID
        client = mqttclient.Client(f'lasertagb01-vizrelay{self.sn}')
        client.on_connect = self.on_connect
        # client.username_pw_set(username, password)
        client.connect(BROKER, 1883)
        return client
    

    def on_connect(self,client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)


    def on_message(self, client, userdata, message):
        mqtt_queue.put(json.loads(message.payload.decode("utf-8")))

            
    def run(self):
        mqttclient = self.connect_mqtt()
        mqttclient.loop_start()

        mqttclient.subscribe("lasertag/vizgamestate")
        mqttclient.on_message = self.on_message

        

        while True:
            global ch2
            global ch3

            global bullets
            global hp
            if not mqtt_queue.empty():
                msg = mqtt_queue.get()
                if msg['type'] == "UPDATE":
                    if self.sn == 1:
                        hp = msg['ga1me_state']['p1']['hp']
                        bullets = msg['game_state']['p1']['bullets']
                        if isinstance(ch2, bluepy.btle.Characteristics):
                            ch2.write(CRC8Packet.pack_data(DataPkt(DATA_PACKET_ID, bullets)))
                        if isinstance(ch3, bluepy.btle.Characteristics):
                            ch3.write(CRC8Packet.pack_data(DataPkt(DATA_PACKET_ID, hp)))
                    else:
                        hp = msg['game_state']['p2']['hp']
                        bullets = msg['game_state']['p2']['bullets']
                        if isinstance(ch2, bluepy.btle.Characteristics):
                            ch2.write(CRC8Packet.pack_data(DataPkt(DATA_PACKET_ID, bullets)))
                        if isinstance(ch3, bluepy.btle.Characteristics):
                            ch3.write(CRC8Packet.pack_data(DataPkt(DATA_PACKET_ID, hp)))
                        
                
                    print("hp: " + str(hp) + "bullets: " + str(bullets))


def Bluno(deviceMACAddress, deviceID, helloPacketReceived, connPacketReceived):
    helloPacketReceived = False
    connPacketReceived = False
    count = 0

    while True:
        global helloPacketReceivedGlove1
        global helloPacketReceivedGun1
        global helloPacketReceivedVest1
        global connPacketReceivedGlove1
        global connPacketReceivedGun1
        global connPacketReceivedVest1

        global errorCountGlove1
        global errorCountGun1
        global errorCountVest1

        # helloPacketReceived = False
        # connPacketReceived = False

        # Connecting to the Bluno
        print(deviceMACAddress, deviceID, helloPacketReceived, connPacketReceived)
        bluno, ch, receivedHello, receivedConn = connectToBLE(deviceMACAddress, deviceID, helloPacketReceived, connPacketReceived)
        print(DEVICE[deviceID], "connected")

        # Start time is used here to determine the duration whether packet drops
        hello_packet_start_time = time.time()

        # Boolean expression for whether Handshaking process is complete
        helloPacketNotReceived = (helloPacketReceived == False)
        connectionNotReceived = (helloPacketReceived == True) and (connPacketReceived == False) 
        
        
        # Initiate Hello Packet to the Bluno and wait for response
        ch.write(CRC8Packet.pack_data(HelloPacket(HELLO_PACKET_ID)))

        
        while not (helloPacketReceived and connPacketReceived):
            try:
                

                    
                while True:
                    global receivedHelloPacket
                    global receivedConnPacket

                    if (DEVICE[deviceID] == 'GUN'):
                        receivedHelloPacket = helloPacketReceivedGun1
                        receivedConnPacket = connPacketReceivedGun1
                    elif (DEVICE[deviceID] == 'GLOVE'):
                        receivedHelloPacket = helloPacketReceivedGlove1
                        receivedConnPacket = connPacketReceivedGlove1
                    elif (DEVICE[deviceID] == 'VEST'):
                        receivedHelloPacket = helloPacketReceivedVest1
                        receivedConnPacket = connPacketReceivedVest1
                    connectEstablished = receivedHelloPacket and receivedConnPacket
                    # Wait for Notification with a time out of 3 seconds
                    if bluno.waitForNotifications(NOTIFICATION_TIMEOUT):
                        # Check if the hello packet has been received but connection established packet not received
                        if not (receivedHelloPacket):
                            ch.write(CRC8Packet.pack_data(HelloPacket(CONN_EST_PACKET_ID)))
                            receivedHelloPacket = True
                        elif not (receivedConnPacket):
                            # print("SENDING ACK 2")
                            receivedConnPacket = True
                        # If connection has already been established, send a statement that the device is connected
                        # To be shown once only
                        elif (connectEstablished and (count == 0)):
                            print(DEVICE[deviceID] + " connected...")
                            count += 1
                        

                        if (deviceID == 2):
                            global bullets
                            if (bullets != None):
                                print("THERE ARE ", str(bullets), " bullets")
                                ch2.write(CRC8Packet.pack_data_result(DataPacket(DATA_PACKET_ID, int(bullets))))
                                print("Writing to Gun is successful")
                                bullets = None
                        
                        if (deviceID == 3):
                            global hp
                            if (hp != None):
                                print("You have ", str(hp), " hp left.")
                                ch3.write(CRC8Packet.pack_data_result(DataPacket(DATA_PACKET_ID, int(hp))))
                                print("Writing to Vest is successful")
                                hp = None


                    # If after 3 seconds and response has not been received, send a new packet
                    # Hello Packet if the hello packet response is not received
                    # Connection Established Packet if connection established packet is not received

                    elif (time.time() - hello_packet_start_time > NOTIFICATION_TIMEOUT) and not receivedHelloPacket:
                        # print("Rabs kebabs")
                        ch.write(CRC8Packet.pack_data(HelloPacket(HELLO_PACKET_ID)))
                        hello_packet_start_time = time.time()
                    
                    elif (time.time() - hello_packet_start_time > NOTIFICATION_TIMEOUT) and not receivedConnPacket:
                        # print("Rabs kebabs")
                        ch.write(CRC8Packet.pack_data(HelloPacket(CONN_EST_PACKET_ID)))
                        hello_packet_start_time = time.time()
            
            except Exception as e:
                # Show the exception and reset the settings
                print(e)
                print(DEVICE[deviceID], "disconnected from 'Bluno' function...")
                bluno.disconnect()
                receivedHelloPacket = False
                receivedConnPacket = False
                if (DEVICE[deviceID] == 'GUN'):
                    helloPacketReceivedGun1 = False 
                    connPacketReceivedGun1 = False
                elif (DEVICE[deviceID] == 'GLOVE'):
                    helloPacketReceivedGlove1 = False
                    connPacketReceivedGlove1 = False
                elif (DEVICE[deviceID] == 'VEST'):
                    helloPacketReceivedVest1 = False
                    connPacketReceivedVest1 = False
                count = 0
                break

def connectToBLE(deviceMACAddress, deviceID, helloPacketReceived, connPacketReceived):
    try:
        bluno = Peripheral(deviceMACAddress, "public")
        svc = bluno.getServiceByUUID("dfb0")
        ch = svc.getCharacteristics("dfb1")[0]
        sensorDelegate = SensorsDelegate(ch, deviceID, bluno, helloPacketReceived, connPacketReceived)
        bluno.setDelegate(sensorDelegate)

        
        return (bluno, ch, sensorDelegate.helloPacketReceived, sensorDelegate.connPacketReceived)
    except Exception as e:
        print(DEVICE[deviceID], "unable to connect to 'connectToBLE' function...")
        # Bluno(deviceMACAddress, deviceID)
        
                

class SensorsDelegate(DefaultDelegate):
    def __init__(self, ch, deviceID, bluno, helloPacketReceived, connPacketReceived):
        DefaultDelegate.__init__(self)
        self.ch = ch
        self.deviceID = deviceID
        self.bluno = bluno
        self.helloPacketReceived = helloPacketReceived
        self.connPacketReceived = connPacketReceived
    
    def handleNotification(self, cHandle, data=0):
        if (cHandle == 37):
            global byteArrayGlove1
            global byteArrayGun1
            global byteArrayVest1
            global helloPacketReceivedGlove1
            global connPacketReceivedGlove1
            global helloPacketReceivedGun1
            global connPacketReceivedGun1
            global helloPacketReceivedVest1
            global connPacketReceivedVest1
            global relay_queue


            # Check the Device ID
            if (data[0] == PLAYER_1_GLOVE_DEVICE_ID):
                try:
                    global sensortimer
                    global index

                    if perf_counter() > sensortimer + 1.0:
                        index = 1
                    sensortimer = perf_counter()

                    # Push the received data to byteArray
                    byteArrayGlove1.extend(data)
                    global errorCountGlove1

                    # Process the data only when there's 20 or more data
                    # The interpretation is that when there are at least 20 data,
                    # we assume the packet coming in is full.
                    if (len(byteArrayGlove1) >= DATA_PACKET_SIZE):
                        # Take the first 20 data and unpack into a tuple
                        byte_array = byteArrayGlove1[:DATA_PACKET_SIZE]
                        tuple_data = struct.unpack(PACKET_FORMAT, byte_array)
                        byteArrayGlove1 = byteArrayGlove1[DATA_PACKET_SIZE:]
                        
                        # Check for corrupted packet using the CRC8 (Error if checksum != 0)
                        checksum_value = CRC8Packet.calculate_crc8(byte_array)
                        if (checksum_value != CHECKSUM_CORRECT_VALUE):
                            # Packet receieved is corrupted, increasing error count
                            # If there are 3 consecutive error, assume is the result of fragmentation and reset
                            errorCountGlove1 += 1
                            if (errorCountGlove1 == ERROR_MAX_COUNT):
                                byte_array_1 = bytearray()
                                self.helloPacketReceived = False
                                self.connPacketReceived = False
                                errorCountGlove1 = 0
                                self.bluno.disconnect()
                        else:
                            # Checksum is 0 - Data received is correct and not corrupted
                            tuple_data1 = tuple(tuple_data)

                            # Printing out the data and sending over to External Comms
                            # print("GLOVE: ", tuple_data1)
                            Gyroscope_X = tuple_data1[2]
                            Gyroscope_Y = tuple_data1[3]
                            Gyroscope_Z = tuple_data1[4]

                            Accelerometer_X = tuple_data1[5]
                            Accelerometer_Y = tuple_data1[6]
                            Accelerometer_Z = tuple_data1[7]

                            Flex_Sensor_Value = tuple_data1[8]
                            Flex_Sensor_Value2 = tuple_data1[9]
                            sending_data = str(Gyroscope_X) + ", " + str(Gyroscope_Y) + ", " + str(Gyroscope_Z) + ", " + str(Accelerometer_X) + ", " + str(Accelerometer_Y) + ", " + str(Accelerometer_Z) + ", " + str(Flex_Sensor_Value) + ", " + str(Flex_Sensor_Value2)
                            relay_queue.put(sending_data)
                            
                            # Training data portion
                            print(str(index), str(tuple_data1))
                            index += 1
                            if (index == 33):
                                index = 1
                            
                            if (tuple_data1[1] == HELLO_PACKET_ID):
                                if (self.helloPacketReceived == False):
                                    self.helloPacketReceived = True
                                elif (self.connPacketReceived == False):
                                    self.connPacketReceived = True
        
                            errorCountGlove1 = 0
                except Exception as e:
                    print(e)
                    print(DEVICE[self.deviceID], "disconnected from Delegate...")
                    helloPacketReceivedGlove1 = False
                    connPacketReceivedGlove1 = False
                    
                                    
            elif (data[0] == PLAYER_1_GUN_DEVICE_ID):
                try:
                    # Push the data to the byte array
                    byteArrayGun1.extend(data)
                    global errorCountGun1

                    # Compute the data only when at least 20 data is received
                    if (len(byteArrayGun1) >= DATA_PACKET_SIZE):
                        # Take the first 20 to unpack
                        byte_array = byteArrayGun1[:DATA_PACKET_SIZE]
                        tuple_data = struct.unpack(PACKET_FORMAT, byte_array)
                        byteArrayGun1 = byteArrayGun1[DATA_PACKET_SIZE:]

                        # Check for corrupted packet through CRC8
                        checksum_value = CRC8Packet.calculate_crc8(byte_array)

                        # If checksum value is not 0, it means data packet is corrupted
                        if (checksum_value != CHECKSUM_CORRECT_VALUE):
                            # Increment error count. If error count reaches 3, assume that it's
                            # issues caused by fragmentation and reset
                            errorCountGun1 += 1
                            if (errorCountGun1 == ERROR_MAX_COUNT):
                                byteArrayGun1 = bytearray()
                                errorCountGun1 = 0
                                self.helloPacketReceived = False
                                self.connPacketReceived = False
                                self.bluno.disconnect()

                        else:
                            # Data is correct.
                            tuple_data2 = tuple(tuple_data)
                            print("GUN Receiving: ", tuple_data2)
                            # print(tuple_data2)

                            # If the packet ID is hello Packet, change the state
                            if (tuple_data2[1] == HELLO_PACKET_ID):
                                # print("RECEIVED HELLO PACKET")
                                if (self.helloPacketReceived == False):
                                    self.helloPacketReceived = True
                                    global helloPacketReceivedGun1
                                    helloPacketReceivedGun1 = self.helloPacketReceived

                                    
                                elif (self.connPacketReceived == False):
                                    self.connPacketReceived = True
                                    global connPacketReceived
                                    connPacketReceived = self.connPacketReceived
                                    

                            # If it's a data packet, respond with an acknowledgement.
                            # Only Gun and Vest requires acknowledgement
                            elif (tuple_data2[1] == DATA_PACKET_ID):
                                # self.ch.write(CRC8Packet.pack_data(HelloPacket(ACK_PACKET_ID)))
                                relay_queue.put("SHOTS FIRED")
                            
                            # Reset the count since data received is correct
                            errorCountGun1 = 0
                except Exception as e:
                    print(e)
                    print(DEVICE[self.deviceID], "disconnected from Delegate...")
                    self.helloPacketReceived = False
                    self.connPacketReceived = False
                    
            elif (data[0] == PLAYER_1_VEST_DEVICE_ID):
                try:
                    # Push the data into the byte array
                    byteArrayVest1.extend(data)
                    global errorCountVest1

                    # Only process the data when it's at size of at least 20
                    if (len(byteArrayVest1) >= DATA_PACKET_SIZE):
                        
                        # Take the first 20 byte to unpack
                        byte_array = byteArrayVest1[:DATA_PACKET_SIZE]
                        tuple_data = struct.unpack(PACKET_FORMAT, byte_array)
                        byteArrayVest1 = byteArrayVest1[DATA_PACKET_SIZE:]
                    
                        # Calculate for corrupted packet.
                        checksum_value = CRC8Packet.calculate_crc8(byte_array)

                        # If checksum is not 0, assume it's fragmentation and hence increase the error count
                        if (checksum_value != CHECKSUM_CORRECT_VALUE):
                            errorCountVest1 += 1

                            # If there is 3 consecutive counts of error, assume is issues arises from fragmentation
                            # Hence requires a reset
                            if (errorCountVest1 == ERROR_MAX_COUNT):
                                byteArrayVest1 = bytearray()
                                self.helloPacketReceived = False
                                self.connPacketReceived = False
                                errorCountVest1 = 0
                                self.bluno.disconnect()
                                
                        else:
                            # Data received is correct
                            tuple_data3 = tuple(tuple_data)
                            print("VEST: ", tuple_data3)

                            # If data received is a hello packet type, change the boolean state of the handshaking process
                            if (tuple_data3[1] == HELLO_PACKET_ID):
                                if (self.helloPacketReceived == False):
                                    self.helloPacketReceived = True
                                elif (self.connPacketReceived == False):
                                    self.connPacketReceived = True

                            # If it's a data packet, respond with Acknowledgement
                            elif (tuple_data3[1] == DATA_PACKET_ID):
                                self.ch.write(CRC8Packet.pack_data(HelloPacket(ACK_PACKET_ID)))
                                relay_queue.put("KANA SHOT")
                        
                        errorCountVest1 = 0
                except Exception as e:
                    print(e)
                    print(DEVICE[self.deviceID], "disconnected from Delegate...")
                    helloPacketReceivedVest1 = False
                    connPacketReceivedVest1 = False

# Declare Thread
t1 = threading.Thread(target=Bluno, args=(PLAYER_1_GLOVE_MAC_ADDRESS, PLAYER_1_GLOVE_DEVICE_ID, False, False))
t2 = threading.Thread(target=Bluno, args=(PLAYER_1_GUN_MAC_ADDRESS, PLAYER_1_GUN_DEVICE_ID, False, False))

t3 = threading.Thread(target=Bluno, args=(PLAYER_1_VEST_MAC_ADDRESS, PLAYER_1_VEST_DEVICE_ID, False, False))
t4 = threading.Thread(target=Bluno, args=(PLAYER_2_VEST_MAC_ADDRESS, PLAYER_1_GUN_DEVICE_ID, False, False))

# Main Function
if __name__=='__main__':
    sn = input("Enter player number:")

    relay_client = RelayClient(sn)
    relay = threading.Thread(target=relay_client.run)
    
    mqtt_client = MQTTClient(sn)
    mqtt_thread = threading.Thread(target=mqtt_client.run)
    


    # t1.start()
    t2.start()    
    # t3.start()
    # relay.join()
    # relay.start()
    # mqtt_thread.start()

