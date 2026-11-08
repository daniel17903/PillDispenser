#include "Time.h"

Time::Time(uint8_t h, uint8_t m, uint8_t s, time_t epoch) {
    setHour(h);
    setMinute(m);
    setSecond(s);
    setEpochSeconds(epoch);
}

Time Time::fromTimeT(time_t utcTime, Timezone& tz) {
    time_t localTime = tz.toLocal(utcTime); // Convert UTC to local time
    tmElements_t tm;
    breakTime(localTime, tm); // Break down local time into components
    return Time(tm.Hour, tm.Minute, tm.Second, localTime);
}

// Getter implementations
uint8_t Time::getHour() const {
    return hour;
}

uint8_t Time::getMinute() const {
    return minute;
}

uint8_t Time::getSecond() const {
    return second;
}


time_t Time::getEpochSeconds() const {
    return epochSeconds;
}

// Setter implementations with validation
void Time::setHour(uint8_t h) {
    hour = (h <= 23) ? h : 0; // Default to 0 if invalid
}

void Time::setMinute(uint8_t m) {
    minute = (m <= 59) ? m : 0; // Default to 0 if invalid
}

void Time::setSecond(uint8_t s) {
    second = (s <= 59) ? s : 0; // Default to 0 if invalid
}


void Time::setEpochSeconds(time_t epoch) {
    epochSeconds = (epoch >= 0) ? epoch : 0; // Ensure non-negative epoch
}

bool Time::isAfter(const Time& other) const {
    return epochSeconds > other.epochSeconds;
}

bool Time::isAfterIgnoringDate(const Time& other) const {
    if (hour > other.hour) return true;
    if (hour < other.hour) return false;
    
    if (minute > other.minute) return true;
    if (minute < other.minute) return false;
    
    return second > other.second;
}

// Calculate absolute difference in seconds between this and another time
long Time::diffInSeconds(const Time& other) const {
    return abs((long)epochSeconds - (long)other.epochSeconds);
}

// Print time to Serial in HH:MM:SS format
void Time::print() const {
    Serial.print(hour);
    Serial.print(":");
    if (minute < 10) Serial.print("0");
    Serial.print(minute);
    Serial.print(":");
    if (second < 10) Serial.print("0");
    Serial.print(second);
    Serial.println();
}

// Calculate seconds until the next occurrence of the target time (either same day or next day)
long Time::secondsUntilNext(const Time& target) const {
    // Create a tmElements_t for the current time in UTC
    tmElements_t currentTm;
    breakTime(epochSeconds, currentTm); // Break down UTC epoch into components

    // Create a tmElements_t for the target time on the same date
    tmElements_t targetTm = currentTm;
    targetTm.Hour = target.hour;
    targetTm.Minute = target.minute;
    targetTm.Second = target.second;

    // Convert target time to UTC epoch seconds
    time_t targetEpoch = makeTime(targetTm);

    // If target time is today and has passed (or is equal), add 1 day (86400 seconds)
    if (isAfterIgnoringDate(target) || (hour == target.hour && minute == target.minute && second == target.second)) {
        targetEpoch += 86400; // Move to tomorrow
    }

    // Calculate seconds until the target time
    return (long)(targetEpoch - epochSeconds);
}