#ifndef TIME_H
#define TIME_H
#include <Timezone.h>

class Time {
private:
    uint8_t hour;   // 0-23, 1 byte
    uint8_t minute; // 0-59, 1 byte
    uint8_t second; // 0-59, 1 byte
    time_t epochSeconds;

public:
    // Constructor
    Time(uint8_t h = 0, uint8_t m = 0, uint8_t s = 0, time_t epoch = 0);
    static Time fromTimeT(time_t utcTime, Timezone& tz);

    // Getters
    uint8_t getHour() const;
    uint8_t getMinute() const;
    uint8_t getSecond() const;
    time_t getEpochSeconds() const;

    // Setters
    void setHour(uint8_t h);
    void setMinute(uint8_t m);
    void setSecond(uint8_t s);
    void setEpochSeconds(time_t epoch);

    // Method to check if this time is after another time
    bool isAfter(const Time& other) const;
    // Method to check if this time is after another time (ignoring date)
    bool isAfterIgnoringDate(const Time& other) const;
    void print() const;
    long diffInSeconds(const Time& other) const;

    // Method to calculate seconds until the next occurrence of the given time
    long secondsUntilNext(const Time& target) const;
};

#endif