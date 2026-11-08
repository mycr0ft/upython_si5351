# upython_si5351

This project is a port of the Arduino code for the [Adafruit Si5351 Clock Generator Breakout](https://learn.adafruit.com/adafruit-si5351-clock-generator-breakout/overview "Adafruit Si5351 Clock Generator Breakout") to [Micropython](http://docs.micropython.org/en/latest/esp8266/esp8266/quickref.html "micropython") for the ESP8266. 

The original sources are available [here](https://github.com/adafruit/Adafruit_Si5351_Library). The Adafruit library was written by Limor Fried/Ladyada forJ Adafruit Industries and distributed under a BSD license, all text above must be included in any redistribution.

Support Adafruit as they invest time and resources by providing open source code for their products.

## API

```python
from machine import I2C, Pin
import SI5351

i2c = I2C( scl=Pin(5), sda=Pin(4), freq=400000)
clockgen = SI5351.SI5351( i2c)
clockgen.begin()
clockgen.setClockBuilderData()                        # or configure the PLLs by hand
clockgen.setupPLL( 36, 0, 1, pllsource='A')           # 25MHz * 36 = 900MHz
clockgen.setupMultisynth( 0, 8, 0, 1, pllsource='A')  # 900MHz / 8 = 112.5MHz
clockgen.PLLsoftreset()
clockgen.enableOutputs( True)
```

`setupMultisynth( output, div, num, denom, pllsource='A', phase_delay=0, inverted=0, powerdown=0)`

`phase_delay` is a **fraction of that output's period** (0 to 1), applied through
the CLKx initial phase offset registers (165-170) and relative to the other
outputs running from the same PLL - use it to phase two clocks against each other,
e.g. for a balanced mixer. The hardware quantises it to a quarter of the VCO
period (datasheet rev 0.95 register 165: one LSB is Tvco/4), so a delay of
`phase_delay * Tout` is `phase_delay * 4 * (div + num/denom)` register steps, and
the 7-bit field means the delay must stay under `127 * Tvco/4`. Leaving the argument
out writes 0, so re-configuring an output does not inherit an earlier offset.
The offset is latched when `enableOutputs()` runs, so call `setupMultisynth()` first.

`test_clockgen.py` is the on-hardware demo. `test_phase_offset.py` checks the
phase-offset register encoding against a stand-in I2C bus, so it runs on a desktop:

```bash
python3 test_phase_offset.py
```


