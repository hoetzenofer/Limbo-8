# microcode

Microcode of the Limbo-8 (`docs/architecture.md`, section 6; instruction set in `docs/instruction-set.md`).

| File | Contents |
|---|---|
| `instructions.py` | the instruction table: all opcodes with their micro steps – **the one source** for everything else |
| `microcode.py` | checks the table (timing rules) and generates everything from it |
| `mc0.bin` – `mc2.bin` | EEPROM images for the programmer (28C256, 32 KB each): mc0 = control word bits 0–7, mc1 = 8–15, mc2 = 16–23 |

After every change to `instructions.py` (with `logisim/limbo.circ` not open in Logisim):

```
python microcode/microcode.py           # .bin, ROM contents in logisim/limbo.circ, tables in the docs
python microcode/microcode.py --check   # writes nothing, only reports whether everything is up to date
```
