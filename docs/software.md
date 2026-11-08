# How the software works

The firmware runs once per wakeup. Everything happens in `setup()` in [`pill_dispenser.ino`](../firmware/pill_dispenser/pill_dispenser.ino), and every run ends in deep sleep. The device is unreachable while it sleeps, so Home Assistant never pushes anything to it. The dispenser always **pulls** its configuration when it wakes up.

## Sequence: a typical day

The phone reports its next alarm to Home Assistant, and an automation sets the dispense time to 30 minutes after that alarm (see [homeassistant/README.md](../homeassistant/README.md)). The dispenser only picks the change up the next time it wakes up.

```mermaid
sequenceDiagram
    actor Phone as Smartphone
    participant HA as Home Assistant
    participant ESP as Pill dispenser

    Phone->>HA: next alarm: 07:00
    HA->>HA: automation sets pill_dispense_time = 07:30

    Note over ESP: deep sleep
    ESP->>HA: 06:00 wakeup: read configuration
    HA-->>ESP: enabled, 07:30
    Note over ESP: deep sleep until 07:30

    ESP->>HA: 07:30 wakeup: read configuration
    HA-->>ESP: enabled, 07:30
    ESP->>ESP: dispense pill
    Note over ESP: deep sleep until 06:00 tomorrow
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
| WiFi not connected after 60 × 500 ms | Sleep 1 h, then try again **without** dispensing. A dispense wakeup that hits a WiFi failure skips that pill |
| Home Assistant unreachable or invalid response | Keep the last known value from RTC memory |
| RTC timer wakes up early | Covered by the 6 h double-dispense guard |
| Dispense time changed in Home Assistant | Not fully covered: the 6 h guard only applies to the wakeup right after a dispense, not to later configuration wakeups. See [when changes take effect](../homeassistant/README.md#when-changes-take-effect) |
