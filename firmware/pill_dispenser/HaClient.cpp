#include "HaClient.h"
#include <WiFiClientSecure.h>
#ifdef ESP32
#include <HTTPClient.h>
#else
#include <ESP8266HTTPClient.h>
#endif

HaClient::HaClient(String host, int port, String token) {
    _host = host;
    _port = port;
    _token = token;
}


TimeResult HaClient::getTimeInput(String entityId){
  JsonDocument response;
  bool success = getEntityState(entityId, response);
  if(!success) return { false };

  if(!response["attributes"]["hour"].is<int>() || !response["attributes"]["minute"].is<int>() || !response["attributes"]["second"].is<int>()){
    Serial.print("Received invalid time json: ");
    serializeJson(response, Serial);
    return { false };
  }

  int hour = response["attributes"]["hour"];
  int minute = response["attributes"]["minute"];
  int second = response["attributes"]["second"];
  Time time(hour, minute, second);

  return { true, time };
}


BooleanResult HaClient::getBooleanInput(String entityId){
  JsonDocument response;
  bool success = getEntityState(entityId, response);
  if(!success) return { false };

  if(!response["state"].is<const char*>()){
    Serial.print("Received invalid boolean json: ");
    serializeJson(response, Serial);
    return { false };
  }

  String state = response["state"];

  return { true, state == "on" };
}

bool HaClient::getEntityState(String entityId, JsonDocument& responseJson){
  WiFiClientSecure *client = new WiFiClientSecure;
  if(client) {
    client->setInsecure();
    HTTPClient https;

    Serial.print("[HTTPS] begin...\n");
    if (https.begin(*client, _host, _port, "/api/states/" + entityId)) {
      https.addHeader("Authorization", "Bearer " + _token);
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
          deserializeJson(responseJson, payload);
          return true;
        }
      }
      else {
        Serial.printf("[HTTPS] GET... failed, error: %s\n", https.errorToString(httpCode).c_str());
        https.end();
      }
    }
  }
  else {
    Serial.printf("[HTTPS] Unable to connect\n");
  }
  
  return false;
}