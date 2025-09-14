# PillDispenser

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
