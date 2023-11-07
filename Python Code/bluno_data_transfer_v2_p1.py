# Import Libraries
from bluepy.btle import Peripheral, UUID, DefaultDelegate, BTLEDisconnectError, Characteristic

# import threading


import sys
import time
from PacketStructClass import HelloPacket, AckPacket, DataPacket
import CRC8Packet
import struct
import os
from paho.mqtt import client as mqttclient
from multiprocessing import Process, Queue

import socket
import json
import asyncio
# from queue import Queue

from time import perf_counter

import random

count = 0


index = 1

TIMEOUT = 0.5 

BROKER = 'broker.emqx.io'
relay_queue = Queue()
mqtt_queue = Queue()
gun_queue = Queue()
vest_queue = Queue()

# Yellow/White 1 
# Blue 2 
NODE_DEVICE_ID = 0
BLUNO_1_DEVICE_ID = 1
BLUNO_2_DEVICE_ID = 2
BLUNO_3_DEVICE_ID = 3

HELLO_PACKET_ID = 0
CONN_EST_PACKET_ID = 1
ACK_PACKET_ID = 2
NAK_PACKET_ID = 3
DATA_PACKET_ID = 4

# MAC Address
Bluno1_MAC_Address = "D0:39:72:E4:80:A8"

# Bluno4_MAC_Address = "D0:39:72:E4:93:BC"

BLUNO_VEST_PLAYER_1_MAC_ADDRESS = "D0:39:72:E4:86:B8"
BLUNO_VEST_PLAYER_2_MAC_ADDRESS = "D0:39:72:E4:91:AC"
BLUNO_GLOVE_PLAYER_1_MAC_ADDRESS = "D0:39:72:E4:93:9D"
BLUNO_GLOVE_PLAYER_2_MAC_ADDRESS = "D0:39:72:E4:93:BC"
BLUNO_GUN_PLAYER_1_MAC_ADDRESS = "D0:39:72:E4:80:A8"
BLUNO_GUN_PLAYER_2_MAC_ADDRESS = "D0:39:72:E4:8C:05"
# BLUNO_GUN_PLAYER_2_MAC_ADDRESS = "D0:39:72:C8:56:46"

dataReceived =[0] * 20
isAcknowledgeMessage = False


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
            msg = mqtt_queue.get()
            print(msg)
            if msg['type'] == "UPDATE":
                if self.sn == 1:
                    hp = msg['game_state']['p1']['hp']
                    bullets = msg['game_state']['p1']['bullets']
                    
                    print("hp: " + str(hp) + "bullets: " + str(bullets))
                    gun_queue.put(bullets)
                    vest_queue.put(hp)
                        
                else:
                    hp = msg['game_state']['p2']['hp']
                    bullets = msg['game_state']['p2']['bullets']

                    print("hp: " + str(hp) + "bullets: " + str(bullets))
                    gun_queue.put(bullets)
                    vest_queue.put(hp)
                        
                    
class BlunoGlove:

    def __init__(self):
        self.helloPacketReceived = False
        self.connPacketReceived = False
        self.connected = False
        self.error_count = 0
        self.svc = None
        self.peripheral = None
        self.ch = None
        


    def connectToBLEGlove(self):
        self.helloPacketReceived = False
        self.connPacketReceived = False

        try:
            self.peripheral = Peripheral(BLUNO_GLOVE_PLAYER_1_MAC_ADDRESS, "public")
            self.peripheral.setDelegate(self.SensorsDelegateGlove(self))

            # print("GLOVE CONNECTED")
            # Retrieve Service and Characteristics
            self.svc = self.peripheral.getServiceByUUID("dfb0")
            self.ch = self.svc.getCharacteristics("dfb1")[0]
        
        except Exception as e:
            print(e)
            self.helloPacketReceived = False
            self.connPacketReceived = False
            self.connected = False
            print("GLOVE DISCONNECTED")
            self.connectToBLEGlove()


    # Function to connect to Bluno 1 and send data.
    def run(self):
        while True:
            self.connectToBLEGlove()
            hello_packet_start_time = perf_counter()

            self.ch.write(CRC8Packet.pack_data(HelloPacket(HELLO_PACKET_ID)))

            while not self.helloPacketReceived:
                try:
                    while True:
                        if self.peripheral.waitForNotifications(TIMEOUT): # calls handleNotification()
                            if not self.helloPacketReceived:
                                self.ch.write(CRC8Packet.pack_data(HelloPacket(CONN_EST_PACKET_ID)))
                                self.helloPacketReceived = True
                                print("hello packet")
                            elif not self.connPacketReceived:
                                self.connPacketReceived = True
                                print("conn packet")
                            elif not self.connected:
                                print("GLOVE CONNECTED")
                                self.connected = True
                        
                        elif perf_counter() - hello_packet_start_time > TIMEOUT and not self.helloPacketReceived:
                            self.ch.write(CRC8Packet.pack_data(HelloPacket(HELLO_PACKET_ID)))
                            hello_packet_start_time = perf_counter()
            
                        elif perf_counter() - hello_packet_start_time > TIMEOUT and not self.connPacketReceived:
                            self.ch.write(CRC8Packet.pack_data(HelloPacket(CONN_EST_PACKET_ID)))
                            hello_packet_start_time = perf_counter()
                        
                except Exception:
                    print("GLOVE DISCONNECTED")
                    self.peripheral.disconnect()
                    self.helloPacketReceived = False
                    self.connPacketReceived = False
                    self.connected = False
                    self.error_count = 0
                    break


    class SensorsDelegateGlove(DefaultDelegate):
        """
        Delegate object from bluepy library to manage notifications from the Arduino Bluno through BLE.
        """
        def __init__(self, parent):
            DefaultDelegate.__init__(self)
            self.byte_array = bytearray()
            self.error_count = 0
            self.index = 0
            self.sensortimer = perf_counter()
            self.parent = parent


        """
        Sorts data transmitted by Arduino Bluno through BLE.
        """ 
        def handleNotification(self, cHandle, data=0):
            if (cHandle==37):
                if perf_counter() > self.sensortimer + 1.0:
                    self.index = 0
                self.sensortimer = perf_counter() 
                self.byte_array.extend(data)
                
                if (len(self.byte_array) >= 20):
                    byte_array = self.byte_array[:20]
                    tuple_data = struct.unpack("BBHHHHHHHHBB", byte_array)
                    self.byte_array = self.byte_array[20:]
                    checksum_value = CRC8Packet.calculate_crc8(byte_array)
                    
                    if (checksum_value != 0):
                        self.error_count += 1
                        if (self.error_count == 3):
                            self.byte_array = bytearray()
                            self.error_count = 0

                    else:
                        tuple_data1 = tuple(tuple_data)
                        sending_data = str(tuple_data1[2])
                        for i in range(3, 10):
                            sending_data += ", "
                            sending_data += str(tuple_data1[i])
                        print(str(self.index), str(tuple_data1))

                        self.index += 1
                        relay_queue.put(sending_data)
                        if (self.index == 33):
                            self.index = 1
                        
                        if (tuple_data1[1] == 0):
                            if (self.parent.helloPacketReceived == False):
                                self.parent.helloPacketReceived = True
                            elif (self.parent.connPacketReceived == False):
                                self.parent.connPacketReceived = True
                        elif (tuple_data1[1] == 4):
                            # ch1.write(CRC8Packet.pack_data(HelloPacket(ACK_PACKET_ID)))
                            pass
                        
                        self.error_count = 0
                    
                
class BlunoGun:

    def __init__(self):
        self.helloPacketReceived = False
        self.connPacketReceived = False
        self.connected = False
        self.error_count = 0
        self.svc = None
        self.peripheral = None
        self.ch = None
        self.commsToBlunoSent = True
        self.commsToBlunoData = None


    # Function to connect to Bluno 2 and send data
    def run(self):
        while True:
            self.connectToBLEGun()
            # hello_packet_start_time = perf_counter()
            

            self.ch.write(CRC8Packet.pack_data(HelloPacket(HELLO_PACKET_ID)))
            while not (self.helloPacketReceived and self.connPacketReceived):
                try:
                    while True:
                        hello_packet_start_time = perf_counter()
                        comms_to_bluno_start_time = perf_counter()

                        if self.peripheral.waitForNotifications(TIMEOUT): # calls handleNotification()

                            if self.helloPacketReceived and not self.connPacketReceived:
                                self.ch.write(CRC8Packet.pack_data(HelloPacket(CONN_EST_PACKET_ID)))
                            
                            elif self.helloPacketReceived and self.connPacketReceived and not self.connected:
                                print("GUN CONNECTED")
                                self.connected = True

                        elif (perf_counter() - hello_packet_start_time > TIMEOUT) and not self.helloPacketReceived:
                            self.ch.write(CRC8Packet.pack_data(HelloPacket(HELLO_PACKET_ID)))
                            hello_packet_start_time = perf_counter() 
                        
                        elif (perf_counter() - hello_packet_start_time > TIMEOUT) and self.helloPacketReceived and not self.connPacketReceived:
                            self.ch.write(CRC8Packet.pack_data(HelloPacket(CONN_EST_PACKET_ID)))
                            hello_packet_start_time = perf_counter()
                    
                        # For Internal Back to Bluno
                        elif (self.helloPacketReceived and self.connPacketReceived and not self.commsToBlunoSent and (perf_counter() - comms_to_bluno_start_time > TIMEOUT)):
                            
                            self.ch.write(CRC8Packet.pack_data_result(DataPacket(DATA_PACKET_ID, self.commsToBlunoData)))
                            print("Re-writing to gun is successful")
                            comms_to_bluno_start_time = perf_counter()


                        if not gun_queue.empty():
                            self.commsToBlunoData = int(gun_queue.get())
                            self.ch.write(CRC8Packet.pack_data_result(DataPacket(DATA_PACKET_ID, self.commsToBlunoData)))
                            print("Writing to gun is successful")
                            self.commsToBlunoSent = False
                            comms_to_bluno_start_time = perf_counter()

                except Exception as e:
                    self.peripheral.disconnect()
                    print(e)
                    print("GUN DISCONNECTED")
                    
                    self.helloPacketReceived = False
                    self.connPacketReceived = False
                    self.connected = False
                    hello_packet_start_time = perf_counter()
                    comms_to_bluno_start_time = perf_counter()
                    break


    def connectToBLEGun(self):
        self.helloPacketReceived = False
        self.connPacketReceived = False

        try:
            self.peripheral = Peripheral(BLUNO_GUN_PLAYER_1_MAC_ADDRESS, "public")
            # Establish Delegate to handle notification
            self.peripheral.setDelegate(self.SensorsDelegateGun(self))

            # Retrieve Service and Characteristics
            self.svc = self.peripheral.getServiceByUUID("dfb0")
            self.ch = self.svc.getCharacteristics("dfb1")[0]

        except Exception as e:
            print("GUN DISCONNECTED")
            self.helloPacketReceived = False
            self.connPacketReceived = False
            self.connected = False
            self.connectToBLEGun()


    # Sensor Delegate for Bluno 2
    class SensorsDelegateGun(DefaultDelegate):
        """
        Deleguate object from bluepy library to manage notifications from the Arduino Bluno through BLE.
        """
        def __init__(self, parent):
            DefaultDelegate.__init__(self)
            self.byte_array = bytearray()
            self.error_count = 0
            self.sensortimer = perf_counter()
            self.parent = parent
            

        """
        Sorts data transmitted by Arduino Bluno through BLE.
        """
        def handleNotification(self, cHandle, data=0):
            if (cHandle==37):
                self.byte_array.extend(data)

                if (len(self.byte_array) >= 20):

                    byte_array = self.byte_array[:20]
                    tuple_data = struct.unpack("BBHHHHHHHHBB", byte_array)
                    self.byte_array = self.byte_array[20:]

                    checksum_value = CRC8Packet.calculate_crc8(byte_array)

                    if (checksum_value != 0):
                        self.error_count += 1
                        if (self.error_count == 3):
                            self.byte_array = bytearray()
                            self.error_count = 0                         

                    else:
                        tuple_data2 = tuple(tuple_data)
                        if (tuple_data2[1] == 0):
                            if (self.parent.helloPacketReceived == False):
                                self.parent.helloPacketReceived = True
                            elif (self.parent.connPacketReceived == False):
                                self.parent.connPacketReceived = True
                            elif (self.parent.helloPacketReceived and self.parent.connPacketReceived):
                                self.parent.commsToBlunoSent = True
                                
                        elif (tuple_data2[1] == 4):
                            self.parent.ch.write(CRC8Packet.pack_data(HelloPacket(ACK_PACKET_ID)))
                            relay_queue.put("SHOTS FIRED")
                        
                        self.error_count = 0
                        

class BlunoVest:

    def __init__(self):
        self.helloPacketReceived = False
        self.connPacketReceived = False
        self.connected = False
        self.error_count = 0
        self.svc = None
        self.peripheral = None
        self.ch = None
        self.commsToBlunoSent = True
        self.commsToBlunoData = None


    def run(self):
        while True:
            self.connectToBLEVest()
            # hello_packet_start_time = time.time()

            self.ch.write(CRC8Packet.pack_data(HelloPacket(HELLO_PACKET_ID)))

            while not (self.helloPacketReceived and self.connPacketReceived):
                try:
                    while True:
                        hello_packet_start_time = perf_counter()
                        comms_to_bluno_start_time = perf_counter()
                        
                        if self.peripheral.waitForNotifications(TIMEOUT): # calls handleNotification()
                            
                            if ((self.helloPacketReceived == True) and (self.connPacketReceived == False)):
                                self.ch.write(CRC8Packet.pack_data(HelloPacket(CONN_EST_PACKET_ID)))
                            
                            elif self.helloPacketReceived and self.connPacketReceived and not self.connected:
                                print("VEST CONNECTED")        
                                self.connected = True

                        elif (perf_counter() - hello_packet_start_time > TIMEOUT) and (self.helloPacketReceived == False):
                            self.ch.write(CRC8Packet.pack_data(HelloPacket(HELLO_PACKET_ID)))
                            print("Vest Hello Packet Sent again")
                            hello_packet_start_time = perf_counter()
                        
                        elif (perf_counter() - hello_packet_start_time > TIMEOUT) and (self.helloPacketReceived == True) and (self.connPacketReceived == False):
                            self.ch.write(CRC8Packet.pack_data(HelloPacket(CONN_EST_PACKET_ID)))
                            print("Vest Conn Packet Sent again")
                            hello_packet_start_time = perf_counter()
                        
                        # For Internal Back to Bluno
                        elif (self.helloPacketReceived and self.connPacketReceived and not self.commsToBlunoSent and (perf_counter() - comms_to_bluno_start_time > TIMEOUT)):
                            
                            self.ch.write(CRC8Packet.pack_data_result(DataPacket(DATA_PACKET_ID, self.commsToBlunoData)))
                            print("Re-writing to vest is successful")
                            comms_to_bluno_start_time = perf_counter()


                        if not vest_queue.empty():
                            self.commsToBlunoData = int(vest_queue.get())
                            self.ch.write(CRC8Packet.pack_data_result(DataPacket(DATA_PACKET_ID, self.commsToBlunoData)))
                            print("Writing to vest is successful")
                            self.commsToBlunoSent = False
                            comms_to_bluno_start_time = perf_counter()
                
                except Exception as e:
                    self.peripheral.disconnect()
                    print(e)
                    print("VEST DISCONNECTED...")
                    self.helloPacketReceived = False
                    self.connPacketReceived = False
                    self.connected = False
                    self.error_count = 0
                    hello_packet_start_time = perf_counter()
                    comms_to_bluno_start_time = perf_counter()
                    break


    def connectToBLEVest(self):
        self.helloPacketReceived = False
        self.connPacketReceived = False

        # Establish connection to Bluno3
        try:
            self.peripheral = Peripheral(BLUNO_VEST_PLAYER_1_MAC_ADDRESS, "public")

            # Establish Delegate to handle notification
            self.peripheral.setDelegate(self.SensorsDelegateVest(self))
        
            # Retrieve Service and Characteristics
            self.svc = self.peripheral.getServiceByUUID("dfb0")
            self.ch = self.svc.getCharacteristics("dfb1")[0]

        except Exception as e:
            print("VEST DISCONNECTED")
            self.helloPacketReceived = False
            self.connPacketReceived = False
            self.connected = False
            self.connectToBLEVest()


    # Sensor Delegate for Bluno 3
    class SensorsDelegateVest(DefaultDelegate):
        """
        Deleguate object from bluepy library to manage notifications from the Arduino Bluno through BLE.
        """
        def __init__(self, parent):
            DefaultDelegate.__init__(self)
            self.byte_array = bytearray()
            self.error_count = 0
            self.index = 0
            self.sensortimer = perf_counter()
            self.parent = parent
            

        def handleNotification(self, cHandle, data=0):
            """
            Sorts data transmitted by Arduino Bluno through BLE.
            """
            if (cHandle==37):
                self.byte_array.extend(data)

                if (len(self.byte_array) >= 20):                    
                    byte_array = self.byte_array[:20]
                    tuple_data = struct.unpack("BBHHHHHHHHBB", byte_array)
                    # print(tuple_data)
                    self.byte_array = self.byte_array[20:]
                    
                    checksum_value = CRC8Packet.calculate_crc8(byte_array)
                    if (checksum_value != 0):
                        self.error_count += 1

                        if (self.error_count == 3):
                            self.byte_array = bytearray()
                            self.error_count = 0

                    else:
                        tuple_data3 = tuple(tuple_data)
                        # print(tuple_data3)
                        if (tuple_data3[1] == 0):
                            if (self.parent.helloPacketReceived == False):
                                self.parent.helloPacketReceived = True
                            elif (self.parent.connPacketReceived == False):
                                self.parent.connPacketReceived = True
                            
                            elif (self.parent.helloPacketReceived and self.parent.connPacketReceived):
                                self.parent.commsToBlunoSent = True
                        elif (tuple_data3[1] == 4):
                            # ch3.write(CRC8Packet.pack_data(HelloPacket(ACK_PACKET_ID)))
                            relay_queue.put("KANA SHOT")
                        
                        self.error_count = 0
        



# Main Function
if __name__=='__main__':
    sn = input("Enter player number:")

    blunoGlove = BlunoGlove()
    blunoGun = BlunoGun()
    blunoVest = BlunoVest()

    # Declare Thread
    t1 = Process(target=blunoGlove.run)
    t2 = Process(target=blunoGun.run)
    t3 = Process(target=blunoVest.run)

    relay_client = RelayClient(sn)
    relay = Process(target=relay_client.run)
    
    mqtt_client = MQTTClient(sn)
    mqtt_thread = Process(target=mqtt_client.run)

    t1.start()
    t2.start()    
    t3.start()

    # relay.start()
    # mqtt_thread.start()
