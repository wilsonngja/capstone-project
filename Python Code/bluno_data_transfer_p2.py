# Import Libraries
from bluepy.btle import Peripheral, UUID, DefaultDelegate, BTLEDisconnectError, Characteristic

import threading


import sys
import time
from PacketStructClass import HelloPacket, AckPacket, DataPacket
import CRC8Packet
import struct
import os
from paho.mqtt import client as mqttclient

import socket
import json
import asyncio
from queue import Queue

from time import perf_counter

import random

count = 0


index = 1

BROKER = 'broker.emqx.io'
relay_queue = Queue()
mqtt_queue = Queue()

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

YELLOW = "\033[93m"
END = '\033[0m'

count1 = 0
count2 = 0
count3 = 0

ch1 = None
ch2 = None
ch3 = None

# MAC Address
Bluno1_MAC_Address = "D0:39:72:E4:80:A8"

# Bluno4_MAC_Address = "D0:39:72:E4:93:BC"

BLUNO_VEST_PLAYER_1_MAC_ADDRESS = "D0:39:72:E4:86:B8"
BLUNO_VEST_PLAYER_2_MAC_ADDRESS = "D0:39:72:E4:91:AC"
BLUNO_GLOVE_PLAYER_1_MAC_ADDRESS = "D0:39:72:E4:93:9D"
BLUNO_GLOVE_PLAYER_2_MAC_ADDRESS = "D0:39:72:E4:93:BC"
BLUNO_GUN_PLAYER_1_MAC_ADDRESS = "D0:39:72:E4:80:A8"
# BLUNO_GUN_PLAYER_2_MAC_ADDRESS = "D0:39:72:E4:8C:05"
BLUNO_GUN_PLAYER_2_MAC_ADDRESS = "D0:39:72:C8:56:46"



clear_screen = '\033c'



helloPacketReceived1 = False
helloPacketReceived2 = False
helloPacketReceived3 = False
connPacketReceived1 = False
connPacketReceived2 = False
connPacketReceived3 = False

fragment_packet_count1 = 0
fragment_packet_count2 = 0
fragment_packet_count3 = 0

error_count1 = 0 
error_count2 = 0
error_count3 = 0


dataReceived =[0] * 20
isAcknowledgeMessage = False

byte_array_1 = bytearray()
byte_array_2 = bytearray()
byte_array_3 = bytearray()


tuple_data1 = None
tuple_data2 = None
tuple_data3 = None

Flex_Sensor_Value = YELLOW + "Disconnected" + END
Flex_Sensor_Value2 = YELLOW + "Disconnected" + END
Button_Pressed = YELLOW + "Disconnected" + END
Ir_Sensor = YELLOW + "Disconnected" + END
Accelerometer_X = YELLOW + "Disconnected" + END
Accelerometer_Y = YELLOW + "Disconnected" + END
Accelerometer_Z = YELLOW + "Disconnected" + END
Gyroscope_X = YELLOW + "Disconnected" + END
Gyroscope_Y = YELLOW + "Disconnected" + END
Gyroscope_Z = YELLOW + "Disconnected" + END

start_time = time.time()
num_of_bytes = 0

num_of_bytes1 = 0  
num_of_bytes2 = 0
num_of_bytes3 = 0

size = None

bluno1 = None
bluno2 = None
bluno3 = None

total_packets = 0
total_packets1 = 0
total_packets2 = 0
total_packets3 = 0

packets_failed = 0
packets_failed1 = 0
packets_failed2 = 0
packets_failed3 = 0

success_rate = 0.0
success_rate1 = 0.0
success_rate2 = 0.0
success_rate3 = 0.0

relay_queue = Queue()


msg = None
hp = None
bullets = None

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
                        hp = msg['game_state']['p1']['hp']
                        bullets = msg['game_state']['p1']['bullets']
                        
                        try:
                            # print(type(hp), type(bullets))
                            print("hp: " + str(hp) + "bullets: " + str(bullets))
                            
                        except Exception as e:
                            print(e)
                    else:
                        hp = msg['game_state']['p2']['hp']
                        bullets = msg['game_state']['p2']['bullets']
                        
                    
                        
                

# Function to connect to Bluno 1 and send data.
def BlunoGlove():
    global Gyroscope_X
    global Gyroscope_Y
    global Gyroscope_Z

    global Accelerometer_X
    global Accelerometer_Y
    global Accelerometer_Z

    global Flex_Sensor_Value
    global Flex_Sensor_Value2

    while True:
        global helloPacketReceived1
        global connPacketReceived1

        global ch1
        global count1
        global error_count1
        
        bluno, ch1 = connectToBLEGlove()
        hello_packet_start_time = time.time()
        
        helloPacketNotReceived = (helloPacketReceived1 == False)
        connectionNotReceived = (helloPacketReceived1 == True) and (connPacketReceived1 == False) 

        ch1.write(CRC8Packet.pack_data(HelloPacket(HELLO_PACKET_ID)))
        # print("HELLO ", struct.unpack("BBHHHHHHHHBB", CRC8Packet.pack_data(HelloPacket(HELLO_PACKET_ID))))
        while not (helloPacketReceived1):
            # print("FULL LOOP")
            try:
                while True:
                    if bluno.waitForNotifications(3): # calls handleNotification()
                        if not (helloPacketReceived1):
                            ch1.write(CRC8Packet.pack_data(HelloPacket(CONN_EST_PACKET_ID)))
                            helloPacketReceived1 = True

                        elif ((helloPacketReceived1 == True) and (connPacketReceived1 == False)):
                            connPacketReceived1 = True
                            
                        elif (helloPacketReceived1 and connPacketReceived1 and (count1 == 0)):
                            Gyroscope_X = "Connected"
                            Gyroscope_Y = "Connected"
                            Gyroscope_Z = "Connected"

                            Accelerometer_X = "Connected"
                            Accelerometer_Y = "Connected"
                            Accelerometer_Z = "Connected"

                            count1 += 1

                    
                    elif (time.time() - hello_packet_start_time > 3) and (helloPacketReceived1 == False):
                        ch1.write(CRC8Packet.pack_data(HelloPacket(HELLO_PACKET_ID)))
                        # print("INNER HELLO", struct.unpack("BBHHHHHHHHBB", CRC8Packet.pack_data(HelloPacket(HELLO_PACKET_ID))))
                        hello_packet_start_time = time.time()
          
                    elif (time.time() - hello_packet_start_time > 3) and (connPacketReceived1 == False):
                        ch1.write(CRC8Packet.pack_data(HelloPacket(CONN_EST_PACKET_ID)))
                        # print("INNER HELLO", struct.unpack("BBHHHHHHHHBB", CRC8Packet.pack_data(HelloPacket(CONN_EST_PACKET_ID))))
                        hello_packet_start_time = time.time()
                    

            except Exception as e:
                print("GLOVE DISCONNECTED")
                bluno.disconnect()
                global YELLOW
                global END
                Gyroscope_X = YELLOW + "Disconnected" + END
                Gyroscope_Y = YELLOW + "Disconnected" + END
                Gyroscope_Z = YELLOW + "Disconnected" + END
                Accelerometer_X = YELLOW + "Disconnected" + END
                Accelerometer_Y = YELLOW + "Disconnected" + END
                Accelerometer_Z = YELLOW + "Disconnected" + END
                Flex_Sensor_Value = YELLOW + "Disconnected" + END
                Flex_Sensor_Value2 = YELLOW + "Disconnected" + END
                helloPacketReceived1 = False
                connPacketReceived1 = False
                error_count1 = 0
                break


def connectToBLEGlove():
    # Connect to Bluno1
    global Flex_Sensor_Value 
    global Accelerometer_X 
    global Accelerometer_Y 
    global Accelerometer_Z 
    global Gyroscope_X 
    global Gyroscope_Y 
    global Gyroscope_Z 

    global helloPacketReceived1
    helloPacketReceived1 = False
    global connPacketReceived1
    connPacketReceived1 = False

    global bluno1

    try:
        bluno1 = Peripheral(BLUNO_GLOVE_PLAYER_1_MAC_ADDRESS, "public")
        bluno1.setDelegate(SensorsDelegate1())

        print("GLOVE CONNECTED")
        # Retrieve Service and Characteristics
        svc = bluno1.getServiceByUUID("dfb0")
        ch = svc.getCharacteristics("dfb1")[0]

        return (bluno1, ch)
    except Exception as e:
        helloPacketReceived1 = False
        connPacketReceived1 = False
        # print("Exception occurred in Connect", e)
        # print("Unable to connect to glove")
        print("GLOVE DISCONNECTED")
        Flex_Sensor_Value = YELLOW + "Unable to connect... Trying again" + END
        Flex_Sensor_Value2 = YELLOW + "Unable to connect... Trying again" + END
        Accelerometer_X = YELLOW + "Unable to connect... Trying again" + END
        Accelerometer_Y = YELLOW + "Unable to connect... Trying again" + END
        Accelerometer_Z = YELLOW + "Unable to connect... Trying again" + END
        Gyroscope_X = YELLOW + "Unable to connect... Trying again" + END
        Gyroscope_Y = YELLOW + "Unable to connect... Trying again" + END
        Gyroscope_Z = YELLOW + "Unable to connect... Trying again" + END

        BlunoGlove()
        
        

    # Establish Delegate to handle notification
            
            

# Function to connect to Bluno 2 and send data
def BlunoGun():
    global Button_Pressed

    while True:
        global helloPacketReceived2
        global connPacketReceived2

        global ch2
        global error_count2

        global YELLOW
        global END

        # print("HELLO")
        bluno, ch2 = connectToBLEGun()
        hello_packet_start_time = time.time()

        # print(type(ch2))
        ch2.write(CRC8Packet.pack_data(HelloPacket(HELLO_PACKET_ID)))
        while not (helloPacketReceived2 and connPacketReceived2):
            try:
                global count2
                while True:
                    if bluno.waitForNotifications(3): # calls handleNotification()
                        
                        
                        if ((helloPacketReceived2 == True) and (connPacketReceived2 == False)):
                            ch2.write(CRC8Packet.pack_data(HelloPacket(CONN_EST_PACKET_ID)))
                        
                        elif (helloPacketReceived2 and connPacketReceived2 and (count2 == 0)):
                            print("GUN CONNECTED")
                            Button_Pressed = "Connected"
                            count2 += 1

                    elif (time.time() - hello_packet_start_time > 3) and (helloPacketReceived2 == False):
                        ch2.write(CRC8Packet.pack_data(HelloPacket(HELLO_PACKET_ID)))
                        hello_packet_start_time = time.time()   
                    
                    elif (time.time() - hello_packet_start_time > 3) and (helloPacketReceived2 == True) and (connPacketReceived2 == False):
                        ch2.write(CRC8Packet.pack_data(HelloPacket(CONN_EST_PACKET_ID)))
                        hello_packet_start_time = time.time()
                
                    global bullets
                    if (bullets != None):
                        # print("THERE ARE ", str(bullets), " bullets")
                        ch2.write(CRC8Packet.pack_data_result(DataPacket(DATA_PACKET_ID, int(bullets))))
                        # print("DATA SENT SUCCESSFULLY")
                        bullets = None


                    
            except Exception as e:
                bluno.disconnect()
                print(e)
                print("GUN DISCONNECTED")
                Button_Pressed = YELLOW + "Disconnected" + END
                
                helloPacketReceived2 = False
                connPacketReceived2 = False
                error_count2 = 0
                break
                
def connectToBLEGun():
    global Button_Pressed

    global helloPacketReceived2
    helloPacketReceived2 = False
    global connPacketReceived2
    connPacketReceived2 = False

    # Button_Pressed = "Connecting..."

    global bluno2
    # Establish connection to Bluno2
    try:
        # print("HELLOHELLO")
        bluno2 = Peripheral(BLUNO_GUN_PLAYER_2_MAC_ADDRESS, "public")

        # Establish Delegate to handle notification
        bluno2.setDelegate(SensorsDelegate2())

        
        # Retrieve Service and Characteristics
        svc = bluno2.getServiceByUUID("dfb0")
        ch = svc.getCharacteristics("dfb1")[0]

    
        return (bluno2, ch)
    except Exception as e:
        print("GUN DISCONNECTED")
        helloPacketReceived2 = False
        connPacketReceived2 = False
        # print("Unable to connect to gun")
        Button_Pressed = YELLOW + "Unable to connect, trying again" + END
        BlunoGun()




def BlunoVest():
    global Ir_Sensor

    while True:
        global helloPacketReceived3
        global connPacketReceived3

        global ch3
        global error_count3

        bluno, ch3 = connectToBLEVest()
        hello_packet_start_time = time.time()


        ch3.write(CRC8Packet.pack_data(HelloPacket(HELLO_PACKET_ID)))
        while not (helloPacketReceived3 and connPacketReceived3):
            global count3
            try:
                while True:
                    if bluno.waitForNotifications(3): # calls handleNotification()
                        
                        
                        if ((helloPacketReceived3 == True) and (connPacketReceived3 == False)):
                            ch3.write(CRC8Packet.pack_data(HelloPacket(CONN_EST_PACKET_ID)))
                        
                        elif (helloPacketReceived3 and connPacketReceived3 and (count3 == 0)):
                            print("VEST CONNECTED")
                            Ir_Sensor = "Connected"             
                            count3 += 1

                    elif (time.time() - hello_packet_start_time > 3) and (helloPacketReceived3 == False):
                        ch3.write(CRC8Packet.pack_data(HelloPacket(HELLO_PACKET_ID)))
                        hello_packet_start_time = time.time()   
                    
                    elif (time.time() - hello_packet_start_time > 3) and (helloPacketReceived3 == True) and (connPacketReceived3 == False):
                        ch3.write(CRC8Packet.pack_data(HelloPacket(CONN_EST_PACKET_ID)))
                        hello_packet_start_time = time.time()

                    global hp
                    
                    if (hp != None):
                        print("You have ", str(hp), " hp left.")
                        # tuple_data = struct.unpack("BBHHHHHHHHBB", CRC8Packet.pack_data_result(DataPacket(DATA_PACKET_ID, int(hp))))
                        # print(tuple_data[2])
                        # print(struct.unpack("BBHHHHHHHHBB", DataPacket(DATA_PACKET_ID, int(hp))))
                        ch3.write(CRC8Packet.pack_data_result(DataPacket(DATA_PACKET_ID, int(hp))))
                        print("Writing to vest is successful")
                        hp = None
            
            except Exception as e:
                bluno.disconnect()
                Ir_Sensor= YELLOW + "Disconnected" + END
                helloPacketReceived3 = False
                connPacketReceived3 = False
                error_count3 = 0
                break

def connectToBLEVest():
    global Ir_Sensor

    global helloPacketReceived3
    helloPacketReceived3 = False
    global connPacketReceived3
    connPacketReceived3 = False

    global bluno3
    # Establish connection to Bluno3
    try:
        bluno3 = Peripheral(BLUNO_VEST_PLAYER_2_MAC_ADDRESS, "public")

        # Establish Delegate to handle notification
        bluno3.setDelegate(SensorsDelegate3())
    
        
        # Retrieve Service and Characteristics
        svc = bluno3.getServiceByUUID("dfb0")
        ch = svc.getCharacteristics("dfb1")[0]

    
        return (bluno3, ch)
    except Exception as e:
        helloPacketReceived3 = False
        connPacketReceived3 = False
        # print("Unable to connect to Vest")
        Ir_Sensor = YELLOW + "Unable to connect..." + END
        BlunoVest()


def pushData():
    

    while True:
        
        global helloPacketReceived1
        global helloPacketReceived2
        global helloPacketReceived3
        global connPacketReceived1
        global connPacketReceived2
        global connPacketReceived3

        global tuple_data1
        global tuple_data2
        global tuple_data3

        global Ir_Sensor

        global Flex_Sensor_Value 
        global Flex_Sensor_Value2
        global Button_Pressed 
            
        global Accelerometer_X 
        global Accelerometer_Y 
        global Accelerometer_Z 
        global Gyroscope_X 
        global Gyroscope_Y 
        global Gyroscope_Z
        
        global relay_queue

        
        # print(tuple_data1)
        if (connPacketReceived1) and (isinstance(tuple_data1, tuple)):
            # print("Enter inner loop")
            Gyroscope_X = tuple_data1[2]
            Gyroscope_Y = tuple_data1[3]
            Gyroscope_Z = tuple_data1[4]

            Accelerometer_X = tuple_data1[5]
            Accelerometer_Y = tuple_data1[6]
            Accelerometer_Z = tuple_data1[7]

            Flex_Sensor_Value = tuple_data1[8]
            Flex_Sensor_Value2 = tuple_data1[9]
            sending_data = str(Gyroscope_X) + ", " + str(Gyroscope_Y) + ", " + str(Gyroscope_Z) + ", " + str(Accelerometer_X) + ", " + str(Accelerometer_Y) + ", " + str(Accelerometer_Z) + ", " + str(Flex_Sensor_Value) + ", " + str(Flex_Sensor_Value2) + ", " + str(Button_Pressed)
            # relay_queue.put(sending_data)
            # sleep(0.01)
        # else:
            # relay_queue.put(str(type(tuple_data1)))
        
        
        if (connPacketReceived2) and (isinstance(tuple_data2, tuple)):
            Button_Pressed = tuple_data2[2]
            sending_data = str(tuple_data2)
            relay_queue.put("SHOTS FIRED")
            tuple_data2 = 0
        else:
            Button_Pressed = 0
        
        if ((connPacketReceived3) and (isinstance(tuple_data3, tuple))):
            Ir_Sensor = tuple_data3[2]
        else:
            Ir_Sensor = 0
        
        # sending_data = str(Gyroscope_X) + ", " + str(Gyroscope_Y) + ", " + str(Gyroscope_Z) + ", " + str(Accelerometer_X) + ", " + str(Accelerometer_Y) + ", " + str(Accelerometer_Z) + ", " + str(Flex_Sensor_Value) + ", " + str(Flex_Sensor_Value2) + ", " + str(Button_Pressed)
        # relay_queue.put(sending_data)


def printData():
    global tuple_data1
    global tuple_data2
    global tuple_data3

    global Flex_Sensor_Value 
    global Flex_Sensor_Value2
    global Button_Pressed 
    global Ir_Sensor 
    global Accelerometer_X 
    global Accelerometer_Y 
    global Accelerometer_Z 
    global Gyroscope_X 
    global Gyroscope_Y 
    global Gyroscope_Z 

    global helloPacketReceived1
    global helloPacketReceived2
    global helloPacketReceived3
    global connPacketReceived1
    global connPacketReceived2
    global connPacketReceived3

    global start_time

    global num_of_bytes

    

    global success_rate
    global total_packets
    global packets_failed

    global success_rate1
    global total_packets1
    global packets_failed1

    global success_rate2
    global total_packets2
    global packets_failed2

    global success_rate3
    global total_packets3
    global packets_failed3

    while True:
        GREEN = '\033[32m'
        
        RED = "\033[31m"
        CYAN = '\033[36m'
        
        MAGENTA = '\033[35m'
        ORANGE = '\033[91m'
        BLUE = '\033[96m'

        UNDERLINE = '\033[4m'  
        BOLD = '\033[1m'

        global YELLOW
        global END

        global fragment_packet_count1
        global fragment_packet_count2
        global fragment_packet_count3

        total_packet1_sent = "0"
        success_rate_packet_1 = "0.0"
        success_packet1_sent = "0"

        total_packet2_sent = "0"
        success_rate_packet_2 = "0.0"
        success_packet2_sent = "0"

        total_packet3_sent = "0"
        success_rate_packet_3 = "0.0"
        success_packet3_sent = "0"

        total_packets_sent = "0"
        success_packet_sent = "0"
        success_rate_sent = "0.0"

        total_packets = 0
        success_packet = 0
        success_rate = 0.0
        packets_failed = 0



        if (total_packets1 or total_packets2 or total_packets3):
            total_packets = total_packets1 + total_packets2 + total_packets3
            success_packet = total_packets - packets_failed1 - packets_failed2 - packets_failed3
            packets_failed = packets_failed1 + packets_failed2 + packets_failed3
            success_rate = (success_packet / total_packets) * 100.0

        # BLUNO 1
        if total_packets1 > 1:
            total_packet1_sent = GREEN + str(total_packets1) + END        
        
        if (total_packets1 - packets_failed1) > 70:
            success_packet1_sent = GREEN + str(total_packets1 - packets_failed1) + END
            success_rate_packet_1 = GREEN + str(round(success_rate1, 2))
        elif (total_packets1 - packets_failed1) != 0:
            success_packet1_sent = RED + YELLOW + str(total_packets1 - packets_failed1) + END
            success_rate_packet_1 = RED + YELLOW + str(round(success_rate1, 2)) + "%"+ END


        if (connPacketReceived1) and (isinstance(tuple_data1, tuple)):
            Gyroscope_X = GREEN + str(tuple_data1[2]) + END
            Gyroscope_Y = GREEN+ str(tuple_data1[3]) + END
            Gyroscope_Z = GREEN + str(tuple_data1[4]) + END

            Accelerometer_X = GREEN + str(tuple_data1[5]) + END
            Accelerometer_Y = GREEN + str(tuple_data1[6]) + END
            Accelerometer_Z = GREEN + str(tuple_data1[7]) + END

            Flex_Sensor_Value = GREEN + str(tuple_data1[8]) + END
            Flex_Sensor_Value2 = GREEN + str(tuple_data1[9]) + END

        else:
            Gyroscope_X = YELLOW + "Connecting..."  + END
            Gyroscope_Y = YELLOW + "Connecting..." + END
            Gyroscope_Z = YELLOW + "Connecting..." + END
            Accelerometer_X = YELLOW + "Connecting..." + END
            Accelerometer_Y = YELLOW + "Connecting..." + END
            Accelerometer_Z = YELLOW + "Connecting..." + END
            Flex_Sensor_Value = YELLOW + "Connecting..." + END
            Flex_Sensor_Value2 = YELLOW + "Connecting..." + END



        # BLUNO 2
        if total_packets2 > 1:
            total_packet2_sent = GREEN + str(total_packets2) + END

        if (total_packets2 - packets_failed2) > 70:
            success_packet2_sent = GREEN + str(total_packets2 - packets_failed2) + END
            success_rate_packet_2 = GREEN + str(round(success_rate2, 2))
        elif (total_packets2 - packets_failed2) != 0:
            success_packet2_sent = RED + YELLOW + str(total_packets2 - packets_failed2) + END
            success_rate_packet_2 = RED + YELLOW + str(round(success_rate2, 2)) + END

        if (connPacketReceived2) and (isinstance(tuple_data2, tuple)):
            Button_Pressed = GREEN + str(tuple_data2[2]) + END
        else:
            Button_Pressed = YELLOW + "Connecting..." + END

        # BLUNO 3
        if total_packets3 > 1:
            total_packet3_sent = GREEN + str(total_packets3) + END

        if (total_packets3 - packets_failed3) > 70:
            success_packet3_sent = GREEN + str(total_packets3 - packets_failed3) + END
            success_rate_packet_3 = GREEN + str(round(success_rate3, 2))
        elif (total_packets3 - packets_failed3) != 0:
            success_packet3_sent = RED + YELLOW + str(total_packets3 - packets_failed3) + END
            success_rate_packet_3 = RED + YELLOW + str(round(success_rate3, 2)) + END


        if ((connPacketReceived3) and (isinstance(tuple_data3, tuple))):
            Ir_Sensor = GREEN + str(tuple_data3[2]) + END
        else:
            Ir_Sensor = YELLOW + "Connecting..." + END

        # TOTAL PACKETS
        if total_packets > 1:
            total_packets_sent = GREEN + str(total_packets) + END
        
        if success_rate > 70:
            success_packet_sent = GREEN + str(total_packets - packets_failed) + END
            success_rate_sent = GREEN + str(round(success_rate, 2))
        elif success_rate != 0:
            success_packet_sent = RED + YELLOW + str(total_packets - packets_failed) + END
            success_rate_sent = RED + YELLOW + str(round(success_rate, 2)) + END

        
        throughput = round(num_of_bytes/(time.time() - start_time),2)
        if (throughput > 30):
            throughput_rate = GREEN + str(throughput) + "Bps"+ END
        elif (throughput == 0):
            throughput_rate = RED + str(throughput) + "Bps"+ END
        else:
            throughput_rate = YELLOW + str(throughput) + "Bps"+ END

        if (time.time() - start_time > 3):
            start_time = time.time()
            num_of_bytes = 0

        
        os.system('clear')  # Clear the screen based on the platform
    
        print(f"{BOLD}{CYAN}GyroX:{END} {Gyroscope_X} \n{BOLD}{CYAN}GyroY:{END} {Gyroscope_Y} \n{BOLD}{CYAN}GyroZ:{END} {Gyroscope_Z}")
        print(f"{BOLD}{CYAN}AccX:{END} {Accelerometer_X} \n{BOLD}{CYAN}AccY:{END} {Accelerometer_Y} \n{BOLD}{CYAN}AccZ:{END} {Accelerometer_Z}")
        print(f"{BOLD}{CYAN}Flex Sensor 1:{END} {Flex_Sensor_Value}\n{BOLD}{CYAN}Flex Sensor 2:{END} {Flex_Sensor_Value2}")
        # print(f"{BOLD}{CYAN}Button Pressed:{END} {Button_Pressed}")
        # print(f"{BOLD}{CYAN}IR Sensor{END} {Ir_Sensor}\n")
        
        # print(f"{BOLD}{MAGENTA}Total Packet 1 Sent:{END} {total_packet1_sent}\n{BOLD}{MAGENTA}Packets Sent Successfully:{END} {success_packet1_sent}\n{BOLD}{MAGENTA}Success Rate Bluno 1:{END} {success_rate_packet_1}\033[0m\n{BOLD}{MAGENTA}Fragmented Packets:{END}{fragment_packet_count1}\n")
        # print(f"{BOLD}{MAGENTA}Total Packet 2 Sent:{END} {total_packet2_sent}\n{BOLD}{MAGENTA}Packets Sent Successfully:{END} {success_packet2_sent}\n{BOLD}{MAGENTA}Success Rate Bluno 2:{END} {success_rate_packet_2}%\033[0m\n{BOLD}{MAGENTA}Fragmented Packets:{END}{fragment_packet_count2}\n")
        # print(f"{BOLD}{MAGENTA}Total Packet 3 Sent:{END} {total_packet3_sent}\n{BOLD}{MAGENTA}Packets Sent Successfully:{END} {success_packet3_sent}\n{BOLD}{MAGENTA}Success Rate Bluno 3:{END} {success_rate_packet_3}%\033[0m\n{BOLD}{MAGENTA}Fragmented Packets:{END}{fragment_packet_count3}\n")
        
        
        # print(f"{BOLD}{MAGENTA}Total Packets Sent:{END} {total_packets_sent}\n{BOLD}{MAGENTA}Total Packets Sent Successfully:{END} {success_packet_sent}")
        # print(f"{BOLD}{MAGENTA}Success Rate:{END} {success_rate_sent}%\033[0m\n")
        # print(f"{BOLD}{BLUE}Throughput:{END} {throughput_rate}")
        
        time.sleep(0.2)



def writeData():
    global tuple_data1
    global tuple_data2
    global tuple_data3

    global Flex_Sensor_Value 
    global Flex_Sensor_Value2
    global Button_Pressed 
    global Ir_Sensor 
    global Accelerometer_X 
    global Accelerometer_Y 
    global Accelerometer_Z 
    global Gyroscope_X 
    global Gyroscope_Y 
    global Gyroscope_Z 

    global helloPacketReceived1
    global helloPacketReceived2
    global helloPacketReceived3
    global connPacketReceived1
    global connPacketReceived2
    global connPacketReceived3

    global start_time

    sequence = ['End']
    next_line = "\n"

    f = open("test_file.txt", "a")
    try:
        
        while True:
            if (connPacketReceived1) and (isinstance(tuple_data1, tuple)):

                with open('3-NN-2.txt', 'a') as file:
                    
                    for action in sequence:
                        print("Action: ", action)
                        file.write(action + '\n')
                        for i in range(1,4):
                            print(i)
                            time.sleep(1)
                        

                        for i in range(1, 41):
                            Gyroscope_X = str(tuple_data1[2]) + ", "
                            Gyroscope_Y = str(tuple_data1[3]) + ", "
                            Gyroscope_Z = str(tuple_data1[4]) + ", "

                            Accelerometer_X = str(tuple_data1[5]) + ", "
                            Accelerometer_Y = str(tuple_data1[6]) + ", "
                            Accelerometer_Z = str(tuple_data1[7]) + ", "

                            Flex_Sensor_Value = str(tuple_data1[8]) + ", "
                            Flex_Sensor_Value2 = str(tuple_data1[9]) + ", "


                            final_data = str(i) + ", " +  Gyroscope_X + Gyroscope_Y + Gyroscope_Z + Accelerometer_X + Accelerometer_Y + Accelerometer_Z + Flex_Sensor_Value + Flex_Sensor_Value2 + next_line
                            print("Writing: ", final_data)
                            file.write(final_data)
                            file.flush()
                            time.sleep(0.05)

                        time.sleep(1)
                    # time.sleep(0.1)

            # else:
            #     Gyroscope_X = "0, "
            #     Gyroscope_Y = "0, "
            #     Gyroscope_Z = "0, "
            #     Accelerometer_X = "0, "
            #     Accelerometer_Y = "0, "
            #     Accelerometer_Z = "0, "
            #     Flex_Sensor_Value = "0, "
            #     Flex_Sensor_Value2 = "0, "

            # if (connPacketReceived2) and (isinstance(tuple_data2, tuple)):
            #     Button_Pressed = str(tuple_data2[2]) + ", "
            # else:
            #     Button_Pressed = "0, "
            

            # if ((connPacketReceived3) and (isinstance(tuple_data3, tuple))):
            #     Ir_Sensor = str(tuple_data3[2])
            # else:
            #     Ir_Sensor = "0, "
            
            
    except KeyboardInterrupt:
        print("CTRL + C PRESSED. Exiting...")
        f.close()

def writeIndividualActionData():
    global tuple_data1
    global tuple_data2
    global tuple_data3

    global Flex_Sensor_Value 
    global Flex_Sensor_Value2
    global Button_Pressed 
    global Ir_Sensor 
    global Accelerometer_X 
    global Accelerometer_Y 
    global Accelerometer_Z 
    global Gyroscope_X 
    global Gyroscope_Y 
    global Gyroscope_Z 

    global helloPacketReceived1
    global helloPacketReceived2
    global helloPacketReceived3
    global connPacketReceived1
    global connPacketReceived2
    global connPacketReceived3

    global start_time

    sequence = ['End']
    next_line = "\n"

    f = open("test_file.txt", "a")
    try:
        
        while True:
            if (connPacketReceived1) and (isinstance(tuple_data1, tuple)):

                with open('sample_output.txt', 'a') as file:
                    for i in range(1, 33):
                        Gyroscope_X = str(tuple_data1[2]) + ", "
                        Gyroscope_Y = str(tuple_data1[3]) + ", "
                        Gyroscope_Z = str(tuple_data1[4]) + ", "

                        Accelerometer_X = str(tuple_data1[5]) + ", "
                        Accelerometer_Y = str(tuple_data1[6]) + ", "
                        Accelerometer_Z = str(tuple_data1[7]) + ", "

                        Flex_Sensor_Value = str(tuple_data1[8]) + ", "
                        Flex_Sensor_Value2 = str(tuple_data1[9]) + ", "


                        final_data = Gyroscope_X + Gyroscope_Y + Gyroscope_Z + Accelerometer_X + Accelerometer_Y + Accelerometer_Z + Flex_Sensor_Value + Flex_Sensor_Value2 + next_line
                        print("Writing: ", final_data)
                        file.write(final_data)
                        file.flush()
                    # tuple_data1 = None
                    
            
            
    except KeyboardInterrupt:
        print("CTRL + C PRESSED. Exiting...")
        f.close()


sensortimer = perf_counter()

# Sensor Delegate for Bluno 1
class SensorsDelegate1(DefaultDelegate):
    """
    Deleguate object from bluepy library to manage notifications from the Arduino Bluno through BLE.
    """
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data=0):
        """
        Sorts data transmitted by Arduino Bluno through BLE.
        """ 

        global helloPacketReceived1
        global connPacketReceived1
        global ch1
        global tuple_data1
        global num_of_bytes
        global size
        

        global total_packets1
        global packets_failed1
        global success_rate1

        global YELLOW
        global END

        if (cHandle==37):
            # print(data)
            global byte_array_1
            global error_count1
            global fragment_packet_count1
            global index

            ###
            global sensortimer
            if perf_counter() > sensortimer + 1.0:
                index = 0
            sensortimer = perf_counter()
            ###
            
            try:
                byte_array_1.extend(data)
                
                 
                if (len(byte_array_1) >= 20):
                    
                    byte_array = byte_array_1[:20]
                    tuple_data = struct.unpack("BBHHHHHHHHBB", byte_array)
                    byte_array_1 = byte_array_1[20:]
                    total_packets1 += 1
                    checksum_value = CRC8Packet.calculate_crc8(byte_array)
                    
                    if (checksum_value != 0):
                        # print(tuple_data)

                        error_count1 += 1
                        packets_failed1 += 1
                        if (error_count1 == 3):
                            byte_array_1 = bytearray()
                            global Flex_Sensor_Value
                            global Accelerometer_X
                            global Accelerometer_Y
                            global Accelerometer_Z
                            global Gyroscope_X
                            global Gyroscope_Y
                            global Gyroscope_Z

                            Flex_Sensor_Value = YELLOW + "Connecting..." + END
                            Accelerometer_X = YELLOW + "Connecting..." + END
                            Accelerometer_Y = YELLOW + "Connecting..." + END
                            Accelerometer_Z = YELLOW + "Connecting..." + END
                            Gyroscope_X = YELLOW + "Connecting..." + END
                            Gyroscope_Y = YELLOW + "Connecting..." + END
                            Gyroscope_Z = YELLOW + "Connecting..." + END

                            fragment_packet_count1 += 1
                            error_count1 = 0

                    else:
                        global relay_queue
                        tuple_data1 = tuple(tuple_data)
                        Gyroscope_X = tuple_data1[2]
                        Gyroscope_Y = tuple_data1[3]
                        Gyroscope_Z = tuple_data1[4]

                        Accelerometer_X = tuple_data1[5]
                        Accelerometer_Y = tuple_data1[6]
                        Accelerometer_Z = tuple_data1[7]

                        Flex_Sensor_Value = tuple_data1[8]
                        Flex_Sensor_Value2 = tuple_data1[9]
                        sending_data = str(Gyroscope_X) + ", " + str(Gyroscope_Y) + ", " + str(Gyroscope_Z) + ", " + str(Accelerometer_X) + ", " + str(Accelerometer_Y) + ", " + str(Accelerometer_Z) + ", " + str(Flex_Sensor_Value) + ", " + str(Flex_Sensor_Value2)
                        # print(tuple_data1)
                        # print(index)
                        print(str(index), str(tuple_data1))
                        index += 1
                        relay_queue.put(sending_data)
                        if (index == 33):
                            index = 1
                        
                        if (tuple_data1[1] == 0):
                            if (helloPacketReceived1 == False):
                                helloPacketReceived1 = True
                            elif (connPacketReceived1 == False):
                                connPacketReceived1 = True
                        elif (tuple_data1[1] == 4):
                            # ch1.write(CRC8Packet.pack_data(HelloPacket(ACK_PACKET_ID)))
                            num_of_bytes += 1
                        
                        error_count1 = 0
                    
                    if (tuple_data[1] > 4) or (tuple_data[0] > 3):
                        fragment_packet_count1 += 1

                    success_rate1 = ((total_packets1 - packets_failed1)/total_packets1) * 100.0

            except Exception as e:
                print("GLOVE DISCONNECTED")
                # print("Error in ")
                helloPacketReceived1 = False
                connPacketReceived1 = False
                

# Sensor Delegate for Bluno 2
class SensorsDelegate2(DefaultDelegate):
    """
    Deleguate object from bluepy library to manage notifications from the Arduino Bluno through BLE.
    """
    def __init__(self):
        DefaultDelegate.__init__(self)
        

    def handleNotification(self, cHandle, data=0):
        """
        Sorts data transmitted by Arduino Bluno through BLE.
        """
        global helloPacketReceived2
        global connPacketReceived2
        global ch2
        global tuple_data2
        global num_of_bytes

        global total_packets2
        global packets_failed2
        global success_rate2
        
        if (cHandle==37):
            global byte_array_2

            try:
                byte_array_2.extend(data)

                global error_count2
                global fragment_packet_count2
                

                if (len(byte_array_2) >= 20):

                    byte_array = byte_array_2[:20]
                    tuple_data = struct.unpack("BBHHHHHHHHBB", byte_array)
                    byte_array_2 = byte_array_2[20:]

                    total_packets2 += 1
                    checksum_value = CRC8Packet.calculate_crc8(byte_array)


                    if (checksum_value != 0):
                        # print(tuple_data, "ERROR COUNT", error_count2)
                        packets_failed2 += 1
                        error_count2 += 1


                        if (error_count2 == 3):
                            byte_array_2 = bytearray()
                            global Button_Pressed
                            Button_Pressed = YELLOW + "Connecting..." + END
                            

                    else:
                        tuple_data2 = tuple(tuple_data)
                        print(tuple_data2)
                        if (tuple_data2[1] == 0):
                            if (helloPacketReceived2 == False):
                                helloPacketReceived2 = True
                            elif (connPacketReceived2 == False):
                                connPacketReceived2 = True
                        elif (tuple_data2[1] == 4):
                            ch2.write(CRC8Packet.pack_data(HelloPacket(ACK_PACKET_ID)))
                            relay_queue.put("SHOTS FIRED")
                            num_of_bytes += 1
                        
                        error_count2 = 0
                    
                    if (tuple_data[1] > 4) or (tuple_data[0] > 3):
                        fragment_packet_count2 += 1 
                    success_rate2 = ((total_packets2 - packets_failed2) /total_packets2 ) * 100.0
                   
            except Exception as e:
                print("Gun Disconnected")
                helloPacketReceived2 = False
                connPacketReceived2 = False



# Sensor Delegate for Bluno 3
class SensorsDelegate3(DefaultDelegate):
    """
    Deleguate object from bluepy library to manage notifications from the Arduino Bluno through BLE.
    """
    def __init__(self):
        DefaultDelegate.__init__(self)
        

    def handleNotification(self, cHandle, data=0):
        """
        Sorts data transmitted by Arduino Bluno through BLE.
        """

        global helloPacketReceived3
        global connPacketReceived3
        global ch3
        global tuple_data3
        global num_of_bytes
        global Ir_Sensor

        global total_packets3
        global packets_failed3
        global success_rate3

        global fragment_packet_count3

        if (cHandle==37):
            global byte_array_3

            try:
                byte_array_3.extend(data)

                global error_count3
                
                if (len(byte_array_3) >= 20):
                    total_packets3 += 1
                    
                    byte_array = byte_array_3[:20]
                    tuple_data = struct.unpack("BBHHHHHHHHBB", byte_array)
                    print(tuple_data)
                    byte_array_3 = byte_array_3[20:]
                    
                    checksum_value = CRC8Packet.calculate_crc8(byte_array)
                    if (checksum_value != 0):
                        # print(tuple_data, "ERROR COUNT", error_count3)
                        packets_failed3 += 1
                        error_count3 += 1

                        if (error_count3 == 3):
                            byte_array_3 = bytearray()
                            Ir_Sensor = YELLOW + "Connecting..." + END
                            error_count3 = 0

                    else:
                        tuple_data3 = tuple(tuple_data)
                        # print(tuple_data3)
                        if (tuple_data3[1] == 0):
                            if (helloPacketReceived3 == False):
                                helloPacketReceived3 = True
                            elif (connPacketReceived3 == False):
                                connPacketReceived3 = True
                        elif (tuple_data3[1] == 4):
                            global relay_queue
                            # ch3.write(CRC8Packet.pack_data(HelloPacket(ACK_PACKET_ID)))
                            relay_queue.put("KANA SHOT")
                            num_of_bytes += 1
                        
                        error_count3 = 0
                    
                    if (tuple_data[1] > 4) or (tuple_data[0] > 3):
                        fragment_packet_count3 += 1
                    success_rate3 = ((total_packets3 - packets_failed3)/total_packets3) * 100.0
            
            
            except Exception as e:
                print("Vest disconnected")
                helloPacketReceived3 = False
                connPacketReceived3 = False



# Declare Thread
t1 = threading.Thread(target=BlunoGlove)
t2 = threading.Thread(target=BlunoGun)
t3 = threading.Thread(target=BlunoVest)
t4 = threading.Thread(target=writeIndividualActionData)

# Main Function
if __name__=='__main__':
    sn = input("Enter player number:")

    relay_client = RelayClient(sn)
    relay = threading.Thread(target=relay_client.run)
    
    mqtt_client = MQTTClient(sn)
    mqtt_thread = threading.Thread(target=mqtt_client.run)
    

    # ic.join()
    # relay.join()

    # t1.start()
    # t2.start()    
    t3.start()
    # t4.start()
    relay.start()
    mqtt_thread.start()
