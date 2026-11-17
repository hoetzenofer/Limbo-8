# Limbo-8 – Architecture

## 1. Overview

| Name               | Description                                                                                      |
| ------------------ | ------------------------------------------------------------------------------------------------ |
| Data bus           | 8 bit, one driver at a time (74HC541 tri-state drivers, ROM/RAM via `/OE`), pull-downs           |
| Address bus        | 16 bit = 64 KB, always driven by exactly one of PC, X, SP, MAR                                   |
| Registers          | A (accumulator), B, X (16-bit pointer), SP (8 bit, stack at `$DF00–$DFFF`), PC (16 bit)          |
| Internal registers | IR, T (second ALU operand), MAR (16 bit), flags Z, C, N                                          |
| Control unit       | microcode in 3× 28C256 (24-bit control word), control word latch, up to 16 steps per instruction |
| Memory             | ROM 32 KB (28C256), RAM 24 KB (62256)                                                            |
| Chips              | 73 ICs (CPU, memory, I/O decoding, debug LEDs)                                                   |

## 2. Data bus

The control word holds the source (`DB_SRC`) and the destination (`DB_DST`) as 4-bit numbers. Two 74HC154 decode them, so only one source can drive the bus. Source 0 = nobody drives, the pull-downs give `$00`. Source 14 is a 74HC541 with its inputs on GND.

| No. | Source            | No. | Source                       |
| --- | ----------------- | --- | ---------------------------- |
| 0   | –                 | 8   | SHR (A shifted right by one) |
| 1   | A                 | 9   | XL                           |
| 2   | B                 | 10  | XH                           |
| 3   | memory            | 11  | PCL                          |
| 4   | ALU sum (ADD/SUB) | 12  | PCH                          |
| 5   | ALU AND           | 13  | flags                        |
| 6   | ALU OR            | 14  | constant `$00`               |
| 7   | ALU XOR           | 15  | –                            |

| No. | Destination    | No.   | Destination   |
| --- | -------------- | ----- | ------------- |
| 0   | –              | 6     | ML (MAR low)  |
| 1   | A              | 7     | MH (MAR high) |
| 2   | B              | 8     | XL            |
| 3   | T              | 9     | XH            |
| 4   | IR             | 10    | SP            |
| 5   | memory (write) | 11    | flags         |
|     |                | 12–15 | –             |

## 3. Address bus

`AB_SRC` (2 bits) selects the driver through a 74HC139:

| AB_SRC | Driver | Used for                           |
| ------ | ------ | ---------------------------------- |
| 00     | PC     | fetching instructions and operands |
| 01     | X      | `[X]`, `[X+]`, `JMP X`             |
| 10     | SP     | stack (`$DF00` + SP)               |
| 11     | MAR    | absolute addresses, jump targets   |

## 4. Registers

| Register | Chips                            | Function                                                                                                      |
| -------- | -------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| A        | 74HC377 + 74HC541                | loads from the bus, always feeds the ALU                                                                      |
| B        | 74HC377 + 74HC541                | loads from the bus                                                                                            |
| T        | 74HC377                          | second ALU operand                                                                                            |
| IR       | 74HC377                          | opcode, feeds the microcode address                                                                           |
| PC       | 4× 74HC161 + 4× 74HC541          | counts (`PC_INC`), loads 16 bits from the address bus (`/PC_LD`), PCL/PCH onto the data bus, cleared by reset |
| MAR      | 2× 74HC377 + 2× 74HC541          | loaded byte by byte from the data bus                                                                         |
| X        | 4× 74HC161 + 4× 74HC541          | loaded byte by byte (XL, XH), counts (`X_INC`), XL/XH onto the data bus, cleared by reset                     |
| SP       | 2× 74HC193 + 74HC00 + 2× 74HC541 | counts up/down, loaded from the data bus; a 74HC541 with fixed inputs supplies the high byte `$DF`            |

The 74HC377 loads on the rising clock edge when its `/E` is low. The 74HC161 counters are chained (ENT ← RCO of the lower counter).

## 5. ALU and flags

The ALU always computes with A and T. Every operation is a bus source of its own.

- **ADD/SUB:** 2× 74HC283, T inverted by 2× 74HC86 (`ALU_INV`). Carry-in from `CIN`: 00 = 0, 01 = 1, 10 = C flag (`cin = CIN0 OR (CIN1 AND C)`, 74HC00).
- **AND, OR, XOR:** 2× 74HC08, 2× 74HC32, 2× 74HC86.
- **SHR:** a 74HC541 wired to A shifted by one bit (bit 7 = 0).
- 5× 74HC541 put the results onto the bus (sources 4–8).

| Operation | T       | ALU_INV | CIN |
| --------- | ------- | ------- | --- |
| ADD       | operand | 0       | 0   |
| ADC       | operand | 0       | C   |
| SUB, CMP  | operand | 1       | 1   |
| SBC       | operand | 1       | C   |
| INC       | `$00`   | 0       | 1   |
| DEC       | `$00`   | 1       | 0   |
| SHL       | A       | 0       | 0   |

**Flags** (74HC688, 74HC02, 74HC157, 2× 74HC173, 74HC541):

- Z = data bus is `$00` (74HC688), N = data bus bit 7, C = carry out of the adder.
- `FL_ZN` loads Z and N, `FL_C` loads C. Destination 11 (`POP F`) loads all three from the bus (74HC157 selects).
- Flags byte (source 13, destination 11): bit 0 = C, bit 1 = Z, bit 7 = N, bits 2–6 = 0.

## 6. Control unit

```
IR ──────────┐
step counter ┼─> 3× 28C256 ─> control word latch ─> control signals
cond mux ────┘
```

- **Step counter:** 74HC161, counts on the rising clock edge, `/STEP_RST` loads 0, reset clears it.
- **Condition mux:** 74HC151, IR bits 2–0 select the input: Z, C, N, 1, Z, C, N, 0. The microcode decides whether a jump is taken on 0 or on 1.
- **Control word latch:** 3× 74HC273, take the control word on the falling clock edge (clock inverted by a 74HC04), cleared by reset. The latch holds the control word stable while the EEPROM outputs change.

**Microcode address:**

| Bits   | Contents                                   |
| ------ | ------------------------------------------ |
| A0–A7  | opcode (IR)                                |
| A8–A11 | step                                       |
| A12    | condition (cond mux)                       |
| A13    | 0, reserved for an interrupt request (IRQ) |
| A14    | 0                                          |

**Control word** (active high, except bit 15):

| Bits | Signal                                   | Bits  | Signal    |
| ---- | ---------------------------------------- | ----- | --------- |
| 0–3  | DB_SRC                                   | 14    | SP_DEC    |
| 4–7  | DB_DST                                   | 15    | /STEP_RST |
| 8–9  | AB_SRC                                   | 16    | ALU_INV   |
| 10   | PC_INC                                   | 17–18 | CIN       |
| 11   | PC_LD (inverted to /PC_LD by the 74HC04) | 19    | FL_ZN     |
| 12   | X_INC                                    | 20    | FL_C      |
| 13   | SP_INC                                   | 21    | HLT       |

Bits 22 and 23 are unused. EEPROM 0 holds bits 0–7, EEPROM 1 bits 8–15, EEPROM 2 bits 16–23.

After a reset the latch is 0, so only `/STEP_RST` is active and the step counter stays at 0 until the first fetch word is in the latch. Step 0 is the fetch in all 256 opcodes.

## 7. Clock and timing

A step runs from one falling clock edge to the next:

1. **Clock falls:** the latch takes the new control word. SP counts (`SP_INC`, `SP_DEC`).
2. **Clock rises:** registers, flags, IR and debug LEDs load; PC and X count or load; the step counter counts or goes to 0.
3. **Clock high:** memory writes (`/WE`) and SP loads (`/PL`).

`/WE = NAND(NAND(/MEM_WR, /MEM_WR), CLK)` and `/PL = NAND(NAND(/SP_LD, /SP_LD), CLK)` (74HC00); the SP count inputs are `NAND(SP_INC, CLK)` and `NAND(SP_DEC, CLK)`.

Rules for the microcode:

- In a write step and in an SP load step the address must not change (no `PC_INC` or `X_INC` on the register on the address bus).
- `SP_INC`/`SP_DEC` never in the same step as a memory write through SP.

`HLT` stops the clock; only reset starts the CPU again.

## 8. Memory map

| Range         | Contents                                |
| ------------- | --------------------------------------- |
| `$0000–$7FFF` | ROM (28C256), program starts at `$0000` |
| `$8000–$DFFF` | RAM (62256), stack at `$DF00–$DFFF`     |
| `$E000–$EFFF` | VRAM (graphics, not built yet)          |
| `$F000–$FFFF` | I/O                                     |

Decoding:

- ROM `/CE` = A15, `/OE` = memory read (source 3).
- RAM `/CE` = NAND(A15, NAND(A14, A13)) (74HC00).
- 74HC138 #1: G1 = A15, C B A = A14 A13 A12 → `/Y6` = VRAM, `/Y7` = I/O.
- 74HC138 #2: `/G2B` = I/O, C B A = A2 A1 A0; a 74HC32 combines its outputs with memory read/write. `$F008–$FFFF` mirror `$F000–$F007`.

| Address | Read                            | Write                           |
| ------- | ------------------------------- | ------------------------------- |
| `$F000` | keyboard (not built yet)        | –                               |
| `$F001` | keyboard status (not built yet) | –                               |
| `$F002` | –                               | scroll register (not built yet) |
| `$F003` | –                               | debug LEDs (74HC377)            |
