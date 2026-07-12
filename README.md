# PillDispenser

## Configuration

The dispenser is configured in two places: a local `config.h` file that is compiled into the firmware, and two Home Assistant helper entities that are fetched over the network on every wakeup.

### Local configuration (`config.h`)

Copy `sketch_sep11a/config.dist.h` to `sketch_sep11a/config.h` and fill in your values before flashing:

| Constant   | Description                                                        |
| ---------- | ------------------------------------------------------------------ |
| `ssid`     | WiFi network name                                                  |
| `password` | WiFi password                                                      |
| `haToken`  | Home Assistant long-lived access token (used as a Bearer token)    |
| `haHost`   | Hostname of the Home Assistant instance (HTTPS, certificate is not verified) |
| `haPort`   | Port of the Home Assistant instance (usually `8123`)               |

### Home Assistant entities

On every wakeup the dispenser reads the following helper entities via the [HA REST API](https://developers.home-assistant.io/docs/api/rest/) (`GET /api/states/<entity_id>`). Create them in Home Assistant under *Settings → Devices & services → Helpers*:

| Entity                                | Type      | Purpose                                             |
| ------------------------------------- | --------- | --------------------------------------------------- |
| `input_boolean.pill_dispense_enabled` | Toggle    | Master switch — when `off`, no pill is dispensed    |
| `input_datetime.pill_dispense_time`   | Date/Time (time only) | Time of day at which a pill is dispensed |

If an entity cannot be fetched (e.g. HA is unreachable), the dispenser keeps the last successfully loaded value, which is preserved in RTC memory across deep sleep. The defaults after a cold boot are `enabled = true` and `08:30:00`.

### How the wakeup cycle works

The device spends almost all of its time in deep sleep and only wakes up briefly:

1. On wakeup it connects to WiFi, gets the current time via NTP (timezone Europe/Berlin) and loads the two entities from Home Assistant. If WiFi fails, it retries in one hour without dispensing.
2. If this wakeup was scheduled as a dispense wakeup (or the device was just powered on / reset) **and** `pill_dispense_enabled` is `on`, a pill is dispensed by driving the servo once.
3. It then goes back to deep sleep until whichever comes first: the next `pill_dispense_time` or the daily configuration-loading time (06:00), where it re-reads the entities without dispensing. Configuration changes in Home Assistant therefore take effect at the next wakeup, not immediately.

To avoid double dispensing (e.g. after a reboot shortly before the scheduled time), a dispense scheduled less than 6 hours after a pill was just dispensed is skipped and moved to the next day.

Note that a cold boot (power cycle or reset button) always counts as a dispense wakeup: as long as `pill_dispense_enabled` is `on`, a pill is dispensed immediately after the configuration is loaded.

## Hardware

[Seeed Studio XIAO ESP32-S3](https://www.seeedstudio.com/Seeed-Studio-XIAO-ESP32S3-Pre-Soldered-p-6334.html)

## Power consumption

- during deep sleep: 14μA
- no sleep, no wifi: 32mA
- with wifi receiving: 90mA
- with servo running: 200mA (<3s per pill dispense)

### Power usage:

Per day:

- 10s on with wifi (for connecting to wifi and getting the configuration and current time)
- 3s on with servo
- 86387s in deep sleep

#### Waking up 1 time / day

(10 x 90.000μA + 3 x 200.000μA + 86387 x 14μA) / 86400 = 31,6μA on average

3000mAh / 31,6 x 10 ^ -3 = 94.963,7h (11 years)

-> A 3000mAh battery would last about 94.963,7h (11 years) when waking up 1 time / day

#### Waking up 10 times / day

(100 x 90.000μA + 30 x 200.000μA + 86270 x 14μA) / 86400 = 187,6μA on average

3000mAh / 187,6 x 10 ^ -3 = 15.991,5h (1,8 years)

-> A 3000mAh battery would last about 15.991,5h (1,8 years) when waking up 10 time / day

#### Waking up 1 time / day for 4h

(14400 x 90.000μA + 3 x 200.000μA + 71997 x 14μA) / 86400 = 15mA on average

3000mAh / 15 = 200h (8,3d days)

-> A 3000mAh battery would last about 200h (8,3d days) when waking up 1 time / day and staying on for 4h
