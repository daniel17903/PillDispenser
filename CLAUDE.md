# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Firmware for a battery-powered automatic pill dispenser built on a Seeed Studio XIAO ESP32-S3. The device sleeps in deep sleep almost all the time, wakes up once or twice a day, fetches its configuration from a Home Assistant instance via the REST API, and dispenses a pill by driving a servo at a configured time of day.

This is an Arduino sketch project — there is no build system, package manager, test suite, or linter in the repository. It is built and flashed with the Arduino IDE (or `arduino-cli`) with the ESP32 board support installed.

## Repository layout

- `firmware/pill_dispenser/pill_dispenser.ino` — main sketch: WiFi/NTP setup, deep-sleep scheduling, and the dispense logic. All work happens in `setup()`; `loop()` is empty because the device deep-sleeps instead of looping.
- `firmware/pill_dispenser/HaClient.{h,cpp}` — minimal Home Assistant REST API client (`GET /api/states/<entity_id>` with a Bearer token, TLS without certificate verification). Reads `input_boolean` and `input_datetime` helper entities.
- `firmware/pill_dispenser/Time.{h,cpp}` — small time-of-day class with timezone conversion (Europe/Berlin, DST rules) and `secondsUntilNext()` used for sleep scheduling.
- `firmware/pill_dispenser/config.example.h` — template for `config.h` (WiFi credentials, HA host/port/token). The real `config.h` is git-ignored and must exist for the sketch to compile.
- `hardware/` — STL files (`stl/`, mechanism parts in `stl/mechanism/`), parts list, and `render_exploded_view.py`, which regenerates `docs/images/exploded_view.png`.
- `homeassistant/` — setup of the HA helper entities.
- `docs/` — wiring (`wiring.md`, `images/wiring.svg`), software flow with Mermaid diagrams (`software.md`), power consumption math (`power-consumption.md`).

The sketch folder and the `.ino` file must keep the same name (Arduino requirement).

## Library dependencies

ArduinoJson, NTPClient, Timezone, ESP32Servo (ESP32) / Servo (ESP8266), plus the WiFi/HTTPClient libraries that ship with the board cores. The `#ifdef ESP32` guards keep ESP8266 compatibility, but the deep-sleep calls (`esp_sleep_enable_timer_wakeup`, `esp_deep_sleep_start`) and `RTC_DATA_ATTR` are ESP32-specific.

## Key behavior to preserve when editing

- **State across deep sleep lives in `RTC_DATA_ATTR` variables** (`bootCount`, `dispenseOnWakeUp`, `pillDispenseTime`, `pillDispenseEnabled`). They survive deep-sleep wakeups but reset on a cold boot / reset — that reset is intentional: `dispenseOnWakeUp` initializes to `true` so a power cycle dispenses a pill immediately.
- **Two kinds of wakeups**: dispense wakeups (at `pill_dispense_time`) and configuration-loading wakeups (daily at 06:00, `loadConfigurationTime`). Which one comes next is decided at the end of `setup()` and encoded in `dispenseOnWakeUp` before sleeping.
- **Double-dispense guard**: if a pill was just dispensed and the next scheduled dispense is less than 6 hours away, it is pushed to the next day. Don't remove this — the RTC timer is inaccurate and can wake up early.
- **Failure handling is "keep last known value"**: if WiFi or HA is unreachable, the previous configuration from RTC memory is used; a failed WiFi connection sleeps 1 hour and suppresses dispensing on the retry wakeup.
- **First boot delays 30 s before sleeping** (`bootCount == 1` in `sleepForSeconds`) to leave a window for flashing new firmware — deep sleep makes the USB port unavailable.
- **Power draw matters**: WiFi is switched off before running the servo, and the servo is powered through a MOSFET on pin D2 that is only enabled during dispensing. Keep awake time minimal; battery-life math is in `docs/power-consumption.md`.

## Home Assistant integration

The device reads two helper entities that must exist in HA: `input_boolean.pill_dispense_enabled` and `input_datetime.pill_dispense_time` (the entity IDs are hardcoded in `loadConfigFromHa()`). Configuration changes in HA only take effect at the next wakeup — the device is unreachable while in deep sleep.
