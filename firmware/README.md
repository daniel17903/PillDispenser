# Firmware

Arduino sketch for the Seeed Studio XIAO ESP32-S3. All work happens in `setup()`. The device goes into deep sleep at the end of every run, so `loop()` is never reached.

| File | Purpose |
| ---- | ------- |
| `pill_dispenser/pill_dispenser.ino` | WiFi/NTP setup, deep-sleep scheduling, dispense logic |
| `pill_dispenser/HaClient.{h,cpp}` | Minimal Home Assistant REST API client |
| `pill_dispenser/Time.{h,cpp}` | Time-of-day class with timezone conversion and `secondsUntilNext()` |
| `pill_dispenser/config.example.h` | Template for your `config.h` |

How the wakeup cycle works is described in [docs/software.md](../docs/software.md).

## Requirements

- [Arduino IDE](https://www.arduino.cc/en/software) or [`arduino-cli`](https://arduino.github.io/arduino-cli/)
- ESP32 board support ([espressif/arduino-esp32](https://github.com/espressif/arduino-esp32)), board **XIAO_ESP32S3**
- Libraries (install via the Library Manager):
  - [ArduinoJson](https://arduinojson.org/) (v7)
  - [NTPClient](https://github.com/arduino-libraries/NTPClient)
  - [Timezone](https://github.com/JChristensen/Timezone)
  - [ESP32Servo](https://github.com/madhephaestus/ESP32Servo)

## Configuration (`config.h`)

Copy `pill_dispenser/config.example.h` to `pill_dispenser/config.h` and fill in your values. `config.h` is git-ignored, so your credentials stay out of the repository.

| Constant   | Description |
| ---------- | ----------- |
| `ssid`     | WiFi network name |
| `password` | WiFi password |
| `haToken`  | Home Assistant long-lived access token (used as a Bearer token) |
| `haHost`   | Hostname of the Home Assistant instance (HTTPS, the certificate is not verified) |
| `haPort`   | Port of the Home Assistant instance (usually `8123`) |

The timezone is currently hardcoded to Europe/Berlin (CET/CEST) in `getLocalTime()` in `pill_dispenser.ino`. Change the two `TimeChangeRule`s there if you live elsewhere.

The Home Assistant entities the firmware reads are described in [homeassistant/README.md](../homeassistant/README.md).

## Build and flash

With the Arduino IDE: open `pill_dispenser/pill_dispenser.ino`, select the board *XIAO_ESP32S3* and the port, then upload.

With `arduino-cli`:

```bash
arduino-cli compile --fqbn esp32:esp32:XIAO_ESP32S3 firmware/pill_dispenser
```

```bash
arduino-cli upload --fqbn esp32:esp32:XIAO_ESP32S3 -p /dev/ttyACM0 firmware/pill_dispenser
```

### Flashing a device that is already running

The USB port is not available while the ESP32 is in deep sleep. After a cold boot (switch off and on, or press reset) the firmware waits **30 seconds** before its first deep sleep, so you can upload new firmware in that window.

**Note:** a cold boot always dispenses a pill right away if dispensing is enabled in Home Assistant. Turn `input_boolean.pill_dispense_enabled` off before power-cycling the device just to flash it.

If the board doesn't show up at all, hold the **BOOT** button while plugging in USB to enter the bootloader.

## Debugging

The firmware logs to the serial port at **115200 baud**: boot count, WiFi status, current time, loaded configuration and how long it will sleep.

## Security notes

- TLS certificate verification is disabled (`setInsecure()`), so the connection is encrypted but the server is not authenticated.
- The Home Assistant token is compiled into the firmware. Use a dedicated Home Assistant user for it and don't share the binary.
