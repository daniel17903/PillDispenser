# Home Assistant setup

The dispenser reads two helper entities via the [Home Assistant REST API](https://developers.home-assistant.io/docs/api/rest/) (`GET /api/states/<entity_id>`). The entity IDs are hardcoded in `loadConfigFromHa()` in the firmware.

| Entity | Type | Purpose |
| ------ | ---- | ------- |
| `input_boolean.pill_dispense_enabled` | Toggle | Master switch. When `off`, no pill is dispensed |
| `input_datetime.pill_dispense_time` | Date/Time (time only) | Time of day at which a pill is dispensed |

## Creating the helpers

**In the UI:** *Settings → Devices & services → Helpers → Create helper*

- *Toggle* named `Pill dispense enabled`
- *Date and/or time* named `Pill dispense time`, with *Time* only

Check that the generated entity IDs match the table above.

**Or in YAML** (`configuration.yaml`):

```yaml
input_boolean:
  pill_dispense_enabled:
    name: Pill dispense enabled
    icon: mdi:pill

input_datetime:
  pill_dispense_time:
    name: Pill dispense time
    has_date: false
    has_time: true
    initial: "08:30:00"
```

## Access token

Create a long-lived access token under *your profile → Security → Long-lived access tokens* and put it in `haToken` in `firmware/pill_dispenser/config.h`. Ideally create a separate Home Assistant user for the dispenser.

## When changes take effect

The device is unreachable while it's in deep sleep. Changes in Home Assistant are picked up at the **next wakeup**: either the next dispense time or the daily configuration check at 06:00.

Example: the device is set to dispense at 08:30 and sleeps after the 06:00 check. You change the time to 20:00 at 07:00. The device still wakes up at 08:30 (it doesn't know about the change yet), dispenses, reads the new time and sleeps until 20:00, where it dispenses **again**. Changing the time on the same day can therefore cause two pills in one day. The double-dispense guard only prevents a second dispense within 6 hours of the previous one. To be safe, change the time after that day's pill has been dispensed, or turn dispensing off for that day.

If an entity cannot be fetched, the device keeps the last successfully loaded value. The defaults after a cold boot are `enabled = on` and `08:30:00`.
