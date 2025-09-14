#include "config.h"
#include "Time.h"
#ifdef ESP32
#include <WiFi.h>
#include <HTTPClient.h>
#include <ESP32Servo.h>
#else
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <Servo.h>
#endif
#include <WiFiClientSecure.h>

#include <Timezone.h>
#include <NTPClient.h>
#include <WiFiUdp.h>
#include <ArduinoJson.h>

// factor to convert microseconds to seconds
#define uS_TO_S_FACTOR 1000000ULL 

RTC_DATA_ATTR int bootCount = 0;
RTC_DATA_ATTR bool dispenseOnWakeUp = true;

const Time defaultPillDispenseTime(7, 0, 0);
Servo servo; 

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

Time getPillDispenseTimeConfigurationFromServer(){
  WiFiClientSecure *client = new WiFiClientSecure;
  if(client) {
    client->setInsecure();
    HTTPClient https;

    Serial.print("[HTTPS] begin...\n");
    if (https.begin(*client, "homeserver.ge1ger.de", 8123, "/api/states/input_datetime.pill_dispense_time")) {  // HTTPS
      https.addHeader("Authorization", "Bearer " + haToken);
      Serial.print("[HTTPS] GET...\n");
      int httpCode = https.GET();
      // httpCode will be negative on error
      if (httpCode > 0) {
        // HTTP header has been send and Server response header has been handled
       Serial.printf("[HTTPS] GET... code: %d\n", httpCode);
        // file found at server
        if (httpCode == HTTP_CODE_OK) {
          // print server response payload
          String payload = https.getString();
          JsonDocument doc;
          deserializeJson(doc, payload);
          int hour = doc["attributes"]["hour"];
          int minute = doc["attributes"]["minute"];
          int second = doc["attributes"]["second"];
          
          return Time(hour, minute, second);
        }
      }
      else {
        Serial.printf("[HTTPS] GET... failed, error: %s\n", https.errorToString(httpCode).c_str());
      }
      https.end();
    }
  }
  else {
    Serial.printf("[HTTPS] Unable to connect\n");
  }

  Serial.println("Using default pill dispense time");
  return defaultPillDispenseTime;
}

void sleepForSeconds(int seconds){
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

void dispensePill() {
  Serial.print("Dispensing pill...");
  // turn on Servo via Mosfet
  digitalWrite(D2, HIGH);
  // wait for servo power
  delay(100);
  servo.attach(D1, 600, 2400);
  servo.write(0);              // tell servo to go to position in variable 'pos'
  delay(1000);       
  servo.write(180);              // tell servo to go to position in variable 'pos'
  delay(1000);     
  servo.detach();  
  // turn off Servo via Mosfet
  digitalWrite(D2, LOW);
}

void setup() {
    Serial.begin(115200);
    ++bootCount;
    Serial.println("Boot number: " + String(bootCount));
    pinMode(D2, OUTPUT);

    dispensePill();

    if(!connectToWifi()){
      Serial.println("Failed to connect to wifi, retrying in 1h...");
      sleepForSeconds(60 * 60);
      return;
    }
    
    Time now = getLocalTime();
    Serial.print("Time now: ");
    now.print();

    Time configuredPillDispenseTime = getPillDispenseTimeConfigurationFromServer();
    Serial.print("Loaded configured pill dispense time: ");
    configuredPillDispenseTime.print();

    WiFi.mode(WIFI_OFF);    

    long secondsToSleep = now.secondsUntilNext(configuredPillDispenseTime);
    Serial.print("Seconds to sleep: ");
    Serial.println(secondsToSleep);

    sleepForSeconds(secondsToSleep);
}

void loop()
{
    // Nothing...
}
