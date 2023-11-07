//#include "CRC8.h"
#include "CRC8.h"
#include "CRC.h"
#include "Bluno_Variables.h"
#include <Adafruit_MPU6050.h>
#include <Arduino.h>
#include <arduinoFFT.h>
#include <avr/wdt.h>

#define SAMPLES 16
#define TOTAL_SAMPLES 32
#define SAMPLING_FREQUENCY 100
#define THRESHOLD 700
#define TS 50


int count = 0;

arduinoFFT FFT;
long long fft_sum =0;
Glove_Data gloveDatas[TOTAL_SAMPLES]={};


Adafruit_MPU6050 imu;


float flexMinResistance = 40000;
float flexMaxResistance = 300000;
float baseFlexValue = 16;
float flexInterval = 10;
String actions[11] = { "nothing", "doctor", "spider", "punch",  "thor", "nothing", "shield", "spear", "grenade", "reload", "nothing"}; 

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

void read_action (){
   for (int i =0; i < 11; i ++){
     delay (1000); 

     Serial.println(actions[i]); 
     delay(500);
     Serial.print("3"); 
     delay(500); 
     Serial.print("2"); 
     delay(500); 
     Serial.print("1"); 
     delay(500); 
     Serial.println("go"); 
    
    for (int j = 0; j< 50; j ++){
      Serial.print(j); 
      Serial.print(", ");
      senddata();
      delay(50);  //sampling rate
    }
   }
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
void send_remaining_readings(){
  int n = SAMPLES;
  for (int i = SAMPLES; i < TOTAL_SAMPLES; i ++){
    Glove_Data gloveData;
    gloveDatas[i] = getGloveReadings(); 
    delay(TS); 
  }
}

bool start_of_move(){ 
  int n = SAMPLES; 
  double vReal[3][SAMPLES] = {}; 
  double vImag[3][SAMPLES] = {}; 
  
  //collect samples
  for (int i = 0; i < n; i ++){
    Glove_Data gloveData;
    gloveDatas[i] = getGloveReadings(); 

    vReal[0][i] += gloveDatas[i].GyroX;
    vReal[1][i] += gloveDatas[i].GyroY;

    //vReal[0][i] += gloveDatas[i].AccX;
    vReal[2][i] += gloveDatas[i].AccY*5;

    //vReal[2][i] += gloveDatas[i].AccZ;
    //Serial.print(vReal[0][i]); 
    //vReal[1][i] += gloveDatas[i].AccX + gloveDatas[i].AccY + gloveDatas[i].AccZ;
    //Serial.print(vReal[1][i]); 
    //vReal[2][i] += gloveDatas[i].Flex1 + gloveDatas[i].Flex2;

    vImag[0][i] = 0;
    vImag[1][i] = 0;
    vImag[2][i] = 0;

    delay(TS); 
  }

  //fft
  //float weighted_sums[3]= {}; 
  float sums[3] = {0,0,0};

  for (int j = 0; j < 3; j ++){
    int weighted_sum = 0; 

    FFT = arduinoFFT(vReal[j], vImag[j], SAMPLES, SAMPLING_FREQUENCY);
    FFT.Windowing(vReal[j], SAMPLES, FFT_WIN_TYP_HAMMING, FFT_FORWARD);
    FFT.Compute(vReal[j], vImag[j], SAMPLES, FFT_FORWARD);
    FFT.ComplexToMagnitude(vReal[j], vImag[j], SAMPLES);

    float delta_f = SAMPLING_FREQUENCY / SAMPLES;

    //weighted sum of frequency*amplitude
    for (int i = 0; i < SAMPLES / 2; i++) {
      int frequency = round(i * delta_f);
      long amplitude = round(vReal[j][i]);
      int scale = 2;
      if (j ==0){
        scale = 1.2;
      }
      if (j == 1){
        scale = 1;
      }
      sums[j] += (scale*frequency * amplitude)/100;
    }
    //Serial.print(sums[j]);
    //Serial.print(", ");

    if (sums[j]> 400){
      return true;
    }
   // sums[j] += weighted_sum;
    }
  //int sum = weighted_sum;
  //Serial.println();

  if (sums[1] > 250){
    if (sums[0] >200 || sums[3]> 150){
      return true;
    }
  }

  if (sums[0] > 300){
    if (sums[1] > 200 || sums[2] > 200){
      return true;
    }
  }

  return false;
}

void senddata(){
    struct Data_Packet data_packet;

    for (int i = 0; i < TOTAL_SAMPLES; i++){
      data_packet = computeDataPacketResponse(gloveDatas[i]);
      Serial.write((uint8_t*) &data_packet, sizeof(data_packet));
      delay(8);
    }
}

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);

  pinMode(FLEX_PIN1, INPUT);
  pinMode(FLEX_PIN2, INPUT);

  
  //wdt_disable(); //Disable WDT
  //delay(3000);
  //wdt_enable(WDTO_2S); //Enable WDT with a timeout of 2 seconds
  //Serial.println("WDT Enabled");
  setupImu();  
}

void(* resetFunc) (void) = 0;

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
      } 
    }
  }

      
  //Serial.println("start");

  if (start_of_move()){
    //Serial.println("Move Started");
    //sdelay(1000);
    send_remaining_readings();
    senddata();
    //count += 1;
  }

  
  
  //wdt_reset();
  //if (count == 5) {
  //  count = 0;
  //  while(1);
  //}
  // Serial.println("RESETTED");
  // delay(1000);
  // resetFunc();
  // while(1);
  

  
//  Serial.println("RESET");
}
    
    

      
    
      
   
