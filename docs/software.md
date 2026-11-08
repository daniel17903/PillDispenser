# How the software works

The firmware runs once per wakeup. Everything happens in `setup()` in [`pill_dispenser.ino`](../firmware/pill_dispenser/pill_dispenser.ino), and every run ends in deep sleep. The device is unreachable while it sleeps, so Home Assistant never pushes anything to it. The dispenser always **pulls** its configuration when it wakes up.

## Sequence: a typical day

The user changes the configuration on a smartphone at any time. The dispenser only sees the change at its next wakeup.

```mermaid
sequenceDiagram
    autonumber
    actor User as User (smartphone)
    participant HA as Home Assistant
    participant ESP as Pill dispenser (ESP32-S3)
    participant NTP as NTP server

    Note over ESP: deep sleep (~14 µA)

    User->>HA: set pill_dispense_time = 08:30<br/>pill_dispense_enabled = on
    Note over HA: stores helper states<br/>(device is asleep, not notified)

    rect rgb(235, 242, 255)
    Note over ESP: 06:00 wakeup: configuration only<br/>(dispenseOnWakeUp = false)
    ESP->>ESP: connect to WiFi
    ESP->>NTP: get current time
    NTP-->>ESP: epoch time → Europe/Berlin
    ESP->>HA: GET /api/states/input_boolean.pill_dispense_enabled
    HA-->>ESP: "on"
    ESP->>HA: GET /api/states/input_datetime.pill_dispense_time
    HA-->>ESP: 08:30:00
    ESP->>ESP: WiFi off, no dispensing
    ESP->>ESP: next wakeup = min(08:30, 06:00 tomorrow) → 08:30<br/>dispenseOnWakeUp = true
    end

    Note over ESP: deep sleep until 08:30

    rect rgb(235, 255, 240)
    Note over ESP: 08:30 wakeup: dispense<br/>(dispenseOnWakeUp = true)
    ESP->>ESP: connect to WiFi
    ESP->>NTP: get current time
    ESP->>HA: GET both helper states
    HA-->>ESP: on, 08:30:00
    ESP->>ESP: WiFi off
    ESP->>ESP: D2 high (MOSFET → servo power on)<br/>servo 0° → 180°, D2 low
    ESP->>ESP: next dispense in < 6 h? → push to tomorrow<br/>next wakeup = 06:00 tomorrow
    end

    Note over ESP: deep sleep until 06:00

    User->>HA: pill_dispense_enabled = off (going on vacation)
    Note over ESP: 06:00: reads "off" → no more pills<br/>until it is switched on again
```

## Flowchart: one wakeup

```mermaid
flowchart TD
    A([Wake up: timer or cold boot]) --> B[bootCount++]
    B --> C{WiFi connected<br/>within 30 s?}
    C -- no --> C1[dispenseOnWakeUp = false]
    C1 --> C2[sleep 1 h]
    C -- yes --> D[Get time via NTP]
    D --> E[Load enabled + dispense time from HA<br/>keep previous value on failure]
    E --> F[WiFi off]
    F --> G{dispenseOnWakeUp<br/>and enabled?}
    G -- yes --> H[Dispense pill]
    G -- no --> I
    H --> I[Compute seconds until<br/>next dispense time and 06:00]
    I --> J{Dispense wakeup and next<br/>dispense &lt; 6 h away?}
    J -- yes --> K[Push dispense to the next day]
    J -- no --> L
    K --> L{06:00 comes first?}
    L -- yes --> M[dispenseOnWakeUp = false<br/>sleep until 06:00]
    L -- no --> N[dispenseOnWakeUp = true<br/>sleep until dispense time]
    M --> Z{First boot?}
    N --> Z
    C2 --> Z
    Z -- yes --> Z1[wait 30 s<br/>window for flashing]
    Z -- no --> S
    Z1 --> S([esp_deep_sleep_start])
```

## State across deep sleep

Variables marked `RTC_DATA_ATTR` live in RTC memory. They survive deep sleep but are reset on a cold boot (power switch, reset button, flashing):

| Variable | Cold-boot value | Meaning |
| -------- | --------------- | ------- |
| `bootCount` | `0` | Number of wakeups since the last cold boot. `1` triggers the 30 s flash window |
| `dispenseOnWakeUp` | `true` | Whether the current wakeup is a dispense wakeup. `true` on cold boot, so **powering on dispenses a pill immediately** |
| `pillDispenseTime` | `08:30:00` | Last time loaded from Home Assistant |
| `pillDispenseEnabled` | `true` | Last enabled state loaded from Home Assistant |

## Failure handling

| Situation | Behaviour |
| --------- | --------- |
| WiFi not connected after 60 × 500 ms | Sleep 1 h, then try again **without** dispensing |
| Home Assistant unreachable or invalid response | Keep the last known value from RTC memory |
| RTC timer wakes up early | Covered by the 6 h double-dispense guard |
