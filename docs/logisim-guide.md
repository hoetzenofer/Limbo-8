# Limbo-8 – Logisim

The circuits are made for Logisim Evolution 5.0.0 (Java 21+).

## Files

- `logisim/limbo.circ` – the computer, one subcircuit per module.
- `logisim/chips.circ` – the 74HC154 and 74HC688 (`ic74hc154`, `ic74hc688`), which Logisim's TTL library lacks. `limbo.circ` loads it as a library by relative path, so keep both files in the same folder.

## Modules

```
computer               clock, reset button, displays
└── cpu
    ├── control_unit   reg_ir, step_counter, cond_mux, microcode, cw_latch, db_decoder
    ├── reg_a, reg_b, reg_t
    ├── alu
    ├── flags
    ├── pc, mar, reg_x, sp
    ├── addr_mux
    ├── memory         ROM, RAM, decoding
    └── io             I/O decoding, debug LEDs
```

`datapath` is the test bench of the data path alone (control word from input pins).

Real chips come from Logisim's TTL library with their datasheet pins. Parts that are only there to model the inside of the ROM and RAM chips are labelled "Model of the … pins (not built, inside the chip)".

## Running/Executing

1. Open `limbo.circ`, select `computer`.
2. Set *Simulate → Auto-Tick Frequency* to 128 Hz and turn on *Simulate → Auto-Tick Enabled* (Ctrl+K). One clock cycle is two ticks, so the CPU runs at 64 Hz.
3. The reset button restarts the program at `$0000`. `HLT` stops the clock.

Right click on a module → *View* shows its inside with the current values. *Simulate → Manual Tick Half Cycle* (Ctrl+T) steps half a clock.

## Loading a program

Right click on the ROM `rom28c256` in `memory` → *Load Image* → a `.bin` from the assembler. The microcode ROMs (`rom_mc0`–`rom_mc2`) are filled by `microcode/microcode.py`.

In the repository the program ROM is empty (all `$FF` = `HLT`), so the CPU halts until a program is loaded.

## Conventions

- Pin names are lower case; active-low signals start with `n` (`noe`, `nload`). Control signals keep their names from the control word (`PC_INC`, `FL_ZN`).
- A module that reads and drives the data bus has two pins, `bus_in` and `bus_out`, connected to the same bus outside.
- Signals inside a module are connected by tunnels.

