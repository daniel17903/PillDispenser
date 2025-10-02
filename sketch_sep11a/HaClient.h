#ifndef HA_CLIENT_H
#define HA_CLIENT_H
#include <ArduinoJson.h>
#include "Time.h"

struct BooleanResult
{
    bool success;
    bool result;
};

struct TimeResult
{
    bool success;
    Time result;
};

/**
Client for the HA Rest API, see https://developers.home-assistant.io/docs/api/rest/
*/
class HaClient {
private:
    String _host;
    int _port;
    String _token;

    bool getEntityState(String entityId, JsonDocument& responseJson);

public:
    HaClient(String host, int port, String token);

    TimeResult getTimeInput(String entityId);
    BooleanResult getBooleanInput(String entityId);

};

#endif