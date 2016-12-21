from machine import SPI, Pin, I2C
import SI5351
import time

i2c = I2C( scl=Pin(5), sda=Pin(4), freq=400000)
devlist = i2c.scan()
print(devlist)

clockgen = SI5351.SI5351( i2c) 
clockgen.begin()
clockgen.setClockBuilderData()

# INTEGER ONLY MODE --> most accurate output */  
# Setup PLLA to integer only mode @ 900MHz (must be 600..900MHz) */
# Set Multisynth 0 to 112.5MHz using integer only mode (div by 4/6/8) */
# 25MHz * 36 = 900 MHz, then 900 MHz / 8 = 112.5 MHz */
print("Set PLLA to 900MHz")

clockgen.setupPLL(36, 0, 1, pllsource='A')

print("Set Output #0 to {:2.2f}MHz".format(900/8))

clockgen.setupMultisynth( output=0, div=8, num=0, denom=1, pllsource="A")

# FRACTIONAL MODE --> More flexible but introduce clock jitter 
# Setup PLLB to fractional mode @616.66667MHz (XTAL * 24 + 2/3)
# Setup Multisynth 1 to 13.55311MHz (PLLB/45.5) */
mult =  32
pllb = 25e6*mult
print( 'PLLB = {:5.2e} Hz'.format(pllb))
clockgen.setupPLL( mult, 0, 1, "B")
divider = 32
num2 = 2
denom2 =10
m2 = pllb/(divider+num2/denom2)
print( "Set Output #1 to {:5.4E} Hz".format(m2) )
clockgen.setupMultisynth( 1, divider, num2, denom2, pllsource="B")


# Multisynth 2 is not yet used and won't be enabled, but can be */
# Use PLLB @ 616.66667MHz, then divide by 900 -> 685.185 KHz */
# then divide by 64 for 10.706 KHz */
# configured using either PLL in either integer or fractional mode */

print("Set Output #2 to {:5.1e} Hz".format(400e6/200/2.0))
clockgen.setupMultisynth(2, 100, 0, 1, pllsource="B")
clockgen.setupRdiv(2, 4)

# Enable the clocks
clockgen.enableOutputs(True)

