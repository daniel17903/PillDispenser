# Power consumption

Measured on the Seeed Studio XIAO ESP32-S3 (see also [Seeed's consumption notes](https://wiki.seeedstudio.com/XIAO_ESP32S3_Consumption/)):

| State | Current |
| ----- | ------- |
| Deep sleep | 14 µA |
| Awake, WiFi off | 32 mA |
| Awake, WiFi receiving | 90 mA |
| Servo running | 200 mA (< 3 s per dispense) |

## Assumptions per wakeup

- 10 s awake with WiFi (connecting, NTP, loading the configuration from Home Assistant)
- 3 s with the servo running
- the rest of the day in deep sleep

All examples use a 3000 mAh battery and ignore self-discharge and the LiPo's usable capacity. Real-world runtime will be shorter.

## Waking up once a day

(10 s × 90,000 µA + 3 s × 200,000 µA + 86,387 s × 14 µA) / 86,400 s ≈ **31.6 µA** on average

3000 mAh / 0.0316 mA ≈ 94,964 h ≈ **11 years**

## Waking up 10 times a day

(100 s × 90,000 µA + 30 s × 200,000 µA + 86,270 s × 14 µA) / 86,400 s ≈ **187.6 µA** on average

3000 mAh / 0.1876 mA ≈ 15,992 h ≈ **1.8 years**

## Staying awake for 4 hours a day (e.g. a firmware bug that prevents deep sleep)

(14,400 s × 90,000 µA + 3 s × 200,000 µA + 71,997 s × 14 µA) / 86,400 s ≈ **15 mA** on average

3000 mAh / 15 mA = 200 h ≈ **8.3 days**

## In practice

The firmware wakes up at most twice a day (06:00 configuration check and the dispense time), so the average is about 42 µA (~8 years on paper). Battery self-discharge (typically a few percent per month for LiPo) will limit runtime more than the electronics.
