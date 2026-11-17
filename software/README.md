# Software

- `asm.py` - assembler (guide: `docs/assembler.md`), opcodes from `microcode/instructions.py`
- `cpu_test.asm` - cpu test (for testing the cpu), runs instructions while counting up and stops with leds at 01011010
- `running_light.asm` - a simple example: one bit runs back and forth over the debug LEDs ($F003).
- `loading_bar.asm` - another example: a bar fills all 8 leds one by one, then the other way back.
