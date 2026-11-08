"""Hardware-free checks for the Si5351 driver's initial phase offset support.

Runs on CPython by standing in for the MicroPython `machine` module and for a
real I2C bus, so the register writes can be inspected without a board:

    python3 test_phase_offset.py

No test framework: the point is that it runs anywhere python3 does.
"""

import sys
import types

# Stand in for MicroPython's machine module before importing the driver.
sys.modules.setdefault("machine", types.SimpleNamespace(I2C=object))

import SI5351

PHOFF_BASE = SI5351.SI5351_REGISTER_165_CLK0_INITIAL_PHASE_OFFSET


class FakeI2C:
    """Records every register write, ignores everything else."""

    def __init__(self):
        self.registers = {}

    def writeto_mem(self, address, register, buffer):
        self.registers[register] = buffer[0]

    def readfrom_mem_into(self, address, register, buffer):
        buffer[0] = self.registers.get(register, 0)


def new_clockgen():
    bus = FakeI2C()
    clockgen = SI5351.SI5351(bus)
    clockgen.begin()
    clockgen.setClockBuilderData()
    return clockgen, bus


def check(name, condition):
    condition = bool(condition)
    print(("PASS " if condition else "FAIL ") + name)
    return condition


def main():
    ok = True

    # Integer mode, div 8 from a 900MHz PLL: Tout = 8 * Tvco, one step = Tvco/4,
    # so a quarter of the output period is 8 steps.
    clockgen, bus = new_clockgen()
    clockgen.setupPLL(36, 0, 1, pllsource="A")
    clockgen.setupMultisynth(0, 8, 0, 1, phase_delay=0.25)
    ok &= check("output 0: quarter output period writes PHOFF=8 to register 165",
                bus.registers[PHOFF_BASE] == 8)

    # Fractional mode, div 32 + 2/10: a half period is 4 * 0.5 * 32.2 = 64.4 -> 64 steps.
    clockgen.setupPLL(32, 2, 10, pllsource="B")
    clockgen.setupMultisynth(1, 32, 2, 10, pllsource="B", phase_delay=0.5)
    ok &= check("output 1: half output period writes PHOFF=64 to register 166",
                bus.registers[PHOFF_BASE + 1] == 64)

    # Each output has its own register; writing one must not disturb the others.
    clockgen.setupMultisynth(2, 4, 0, 1, pllsource="B", phase_delay=0.125)
    ok &= check("output 2: 1/8 period on div 4 writes PHOFF=2 to register 167",
                bus.registers[PHOFF_BASE + 2] == 2)
    ok &= check("neighbouring phase registers keep their values",
                bus.registers[PHOFF_BASE] == 8 and bus.registers[PHOFF_BASE + 1] == 64)

    # No argument means no offset, and it clears an offset set by an earlier call
    # rather than leaving the old value in the register.
    clockgen.setupMultisynth(1, 32, 2, 10, pllsource="B")
    ok &= check("omitting phase_delay clears register 166 back to 0",
                bus.registers[PHOFF_BASE + 1] == 0)

    # The 7-bit field caps the offset; div 100 from PLLB saturates at 127/400 of a period.
    try:
        clockgen.setupMultisynth(2, 100, 0, 1, pllsource="B", phase_delay=0.4)
    except AssertionError as exc:
        ok &= check("a delay the field cannot hold is rejected", "too large" in str(exc))
    else:
        ok &= check("a delay the field cannot hold is rejected", False)

    # Divider mode is chosen by num alone; a phase offset must not flip it.
    clockgen, bus = new_clockgen()
    clockgen.setupPLL(36, 0, 1, pllsource="A")
    clockgen.setupMultisynth(0, 8, 0, 1, phase_delay=0.25)
    ok &= check("integer-mode clock control bit still set with a phase offset",
                bus.registers[SI5351.SI5351_REGISTER_16_CLK0_CONTROL] & (1 << 6))

    # And the control register still carries inversion and powerdown as asked.
    clockgen.setupMultisynth(0, 8, 0, 1, phase_delay=0.25, inverted=1, powerdown=1)
    control = bus.registers[SI5351.SI5351_REGISTER_16_CLK0_CONTROL]
    ok &= check("inverted and powerdown bits survive the phase path",
                control & (1 << 4) and control & (1 << 7))

    try:
        clockgen.setupMultisynth(0, 8, 0, 1, phase_delay=-0.1)
    except AssertionError:
        ok &= check("negative phase_delay is rejected", True)
    else:
        ok &= check("negative phase_delay is rejected", False)

    print("\nall checks passed" if ok else "\nFAILURES ABOVE")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
