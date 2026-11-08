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

## Automatically following the phone's next alarm

[`automation_next_alarm.yaml`](automation_next_alarm.yaml) sets `input_datetime.pill_dispense_time` to **30 minutes after the phone's next alarm**, so the pill is ready shortly after you get up.

1. Install the [Home Assistant Companion app](https://companion.home-assistant.io/) on your phone and enable the **Next alarm** sensor (*Settings → Companion app → Manage sensors*). This sensor is only available on Android.
2. Create a new automation, switch to *Edit in YAML* and paste the file's contents.
3. Replace `sensor.my_phone_next_alarm` with your phone's sensor, e.g. `sensor.pixel_8_next_alarm`.

If no alarm is set, the sensor is `unavailable` and the automation keeps the previous dispense time.

Caveats:

- The dispenser only reads the new time at its next wakeup (see below), so the alarm must be set before 06:00 to take effect the same morning.
- When an alarm rings, the sensor jumps to the following alarm and the automation updates the dispense time right away, possibly before that day's pill has been dispensed. The double-dispense guard prevents a second pill as long as the new time is less than 6 hours after the old one. If the next alarm is much later (e.g. 07:00 on a weekday followed by 14:00), the device dispenses at the old time and **again** at the new time on the same day.

## Access token

Create a long-lived access token under *your profile → Security → Long-lived access tokens* and put it in `haToken` in `firmware/pill_dispenser/config.h`. Ideally create a separate Home Assistant user for the dispenser.

## When changes take effect

The device is unreachable while it's in deep sleep. Changes in Home Assistant are picked up at the **next wakeup**: either the next dispense time or the daily configuration check at 06:00.

Example: the device is set to dispense at 08:30 and sleeps after the 06:00 check. You change the time to 20:00 at 07:00. The device still wakes up at 08:30 (it doesn't know about the change yet), dispenses, reads the new time and sleeps until 20:00, where it dispenses **again**. Changing the time on the same day can therefore cause two pills in one day.

The 6-hour double-dispense guard doesn't fully prevent this. It is only checked on the wakeup right after a dispense, and the firmware doesn't remember when the last pill was dispensed. Example: the device dispenses at 04:00 and you change the time to 08:00 at 05:00. The 06:00 configuration check reads 08:00 and the device dispenses again at 08:00, only 4 hours later. If a second pill would be a problem, turn dispensing off before changing the time and back on after the new time has passed.

If an entity cannot be fetched, the device keeps the last successfully loaded value. The defaults after a cold boot are `enabled = on` and `08:30:00`.
