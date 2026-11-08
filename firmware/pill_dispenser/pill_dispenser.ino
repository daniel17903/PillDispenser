#include "config.h"
#include "Time.h"
#ifdef ESP32
#include <WiFi.h>
#include <ESP32Servo.h>
#else
#include <ESP8266WiFi.h>
#include <Servo.h>
#endif

#include <Timezone.h>
#include <NTPClient.h>
#include <WiFiUdp.h>
#include <ArduinoJson.h>
#include "HaClient.h"

// factor to convert microseconds to seconds
#define uS_TO_S_FACTOR 1000000ULL 

RTC_DATA_ATTR int bootCount = 0;
RTC_DATA_ATTR bool dispenseOnWakeUp = true;

// these will be loaded from ha
RTC_DATA_ATTR Time pillDispenseTime(8, 30, 0);
RTC_DATA_ATTR bool pillDispenseEnabled = true;

const long HOUR_IN_SECONDS = 60 * 60;
const long DAY_IN_SECONDS = 24 * 60 * 60;

// the time to wake up to load configuration from server
const Time loadConfigurationTime(6, 0, 0);

Servo servo;
HaClient haClient(haHost, haPort, haToken); 


boolean connectToWifi(){
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  int retries = 0;
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print("Attempting to connect to SSID: ");
    Serial.println(ssid);
    delay(500);
    retries += 1;
    if(retries > 60) return false;
  }
  Serial.println("connected");
  return true;
}

Time getLocalTime(){
  WiFiUDP ntpUDP;
  NTPClient timeClient(ntpUDP);
  timeClient.begin();
  timeClient.update();
  unsigned long epochTime = timeClient.getEpochTime();
  timeClient.end();
  TimeChangeRule ruleSummer = {"BERSO", Last, Sun, Mar, 2, 120};  //UTC + 2
  TimeChangeRule ruleWinter = {"BERWI", Last, Sun, Oct, 3, 60};  //UTC + 1
  Timezone berlin(ruleSummer, ruleWinter);

  return Time::fromTimeT(timeClient.getEpochTime(), berlin);
}


void sleepForSeconds(unsigned long long seconds){
  Serial.print("Seconds to sleep: ");
  Serial.println(seconds);

  if(bootCount == 1){
    // Give a chance to flash a new program before going into deep sleep
    delay(30000);
    seconds -= 30;
  }

  // see https://wiki.seeedstudio.com/XIAO_ESP32S3_Consumption/
  esp_sleep_enable_timer_wakeup(seconds * uS_TO_S_FACTOR);
  Serial.println("Going to sleep now");
  Serial.flush();
  esp_deep_sleep_start();
}

void loadConfigFromHa(){
  BooleanResult pillDispenseIsEnabledResult = haClient.getBooleanInput("input_boolean.pill_dispense_enabled");
  if(pillDispenseIsEnabledResult.success){
    pillDispenseEnabled = pillDispenseIsEnabledResult.result;
    Serial.print("Loaded enabled state from ha: ");
    Serial.println(pillDispenseEnabled);
  } else {
    Serial.print("Failed to load enabled state from ha, using previous value: ");
    Serial.println(pillDispenseEnabled);
  }

  TimeResult configuredPillDispenseTime = haClient.getTimeInput("input_datetime.pill_dispense_time");
  if(configuredPillDispenseTime.success){
    pillDispenseTime = configuredPillDispenseTime.result;
    Serial.print("Loaded pill dispense time from ha: ");
    pillDispenseTime.print();
  } else {
    Serial.print("Failed to load pill dispense time from ha, using previous value: ");
    pillDispenseTime.print();
  }
}

void dispensePill() {
  pinMode(D2, OUTPUT);
  Serial.print("Dispensing pill...");
  // turn on Servo via Mosfet
  digitalWrite(D2, HIGH);
  // wait for servo power
  delay(100);
  servo.attach(D1, 500, 2400);
  servo.write(0);
  delay(1000);       
  servo.write(180);
  delay(1000);     
  servo.detach();  
  // turn off Servo via Mosfet
  digitalWrite(D2, LOW);
}

void setup() {
    Serial.begin(115200);
    ++bootCount;
    Serial.println("Boot number: " + String(bootCount));

    if(!connectToWifi()){
      dispenseOnWakeUp = false;
      Serial.println("Failed to connect to wifi, retrying in 1h...");
      sleepForSeconds(HOUR_IN_SECONDS);
      return;
    }
    
    Time now = getLocalTime();
    Serial.print("Time now: ");
    now.print();

    loadConfigFromHa();

    WiFi.mode(WIFI_OFF);    

    if(dispenseOnWakeUp && pillDispenseEnabled){
      dispensePill();
    }

    unsigned long long secondsToSleep;
    unsigned long long secondsToSleepUntilPillDispenseTime = now.secondsUntilNext(pillDispenseTime);
    unsigned long long secondsToSleepUntilLoadConfigurationTime = now.secondsUntilNext(loadConfigurationTime);
   
    // if we already dispensed a pill now we don't want to dispense another one within the next 6h
    // this can happen when waking up too early because the RTC in inaccurat
    // or when the device was switched on < 15min before the configured time
    // or when today a pill was dispensed at an earlier time than tomorrow
    if (secondsToSleepUntilPillDispenseTime < 6 * HOUR_IN_SECONDS && dispenseOnWakeUp) {
      secondsToSleepUntilPillDispenseTime += DAY_IN_SECONDS;
    }

    if(secondsToSleepUntilLoadConfigurationTime < secondsToSleepUntilPillDispenseTime){
      dispenseOnWakeUp = false;
      secondsToSleep = secondsToSleepUntilLoadConfigurationTime;
      Serial.print("Sleeping until next configuration loading time: ");
      loadConfigurationTime.print();
    } else {
      dispenseOnWakeUp = true;
      secondsToSleep = secondsToSleepUntilPillDispenseTime;
      Serial.print("Sleeping until next pill dispense time: ");
      pillDispenseTime.print();
    }

    sleepForSeconds(secondsToSleep);
}

void loop()
{
    // Nothing...
}
