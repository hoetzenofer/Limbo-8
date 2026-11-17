# Limbo-8 – Assembler

`software/asm.py` turns an assembly file into a 32 KB image for the ROM (28C256). The opcodes come from `microcode/instructions.py`.

## Usage

```bash
python software/asm.py prog.asm                         → prog.bin and prog.lst (listing)
python software/asm.py prog.asm -o out.bin -l out.lst
```

To run a program in Logisim: in the circuit `memory`, right click on the ROM → *Load Image* → the `.bin`, then press reset in `computer`.

## Syntax

```asm6502
NAME = expression              ; constant
        .org $0100             ; continue at address $0100
label:  INSTRUCTION operand    ; comment
text:   .byte "Hello", 13, 0   ; bytes and text
ptr:    .word text, $1234      ; 16 bits, low byte first
```

- Labels end with `:` and are case-sensitive. They must not be register names (`A`, `B`, `X`, `XL`, `XH`, `F`, `SP`, `PC`).
- Instructions and registers may be lower case.

| Expression                  | Meaning                            |
| --------------------------- | ---------------------------------- |
| `$1F`, `%1010`, `31`, `'A'` | hex, binary, decimal, ASCII        |
| `*`                         | address of the current instruction |
| `<expr`, `>expr`            | low byte, high byte                |
| `+ - ( )`                   | arithmetic                         |

| Operand   | Example                               |
| --------- | ------------------------------------- |
| immediate | `LDA #$05`, `LDX #buffer`             |
| address   | `LDA $8000`, `JMP loop`               |
| pointer   | `LDA [X]`, `LDA [X+]`                 |
| register  | `MOV A,B`, `ADD B`, `PUSH F`, `JMP X` |

`NOT` = `XOR #$FF`. Unused ROM bytes are `$FF` (`HLT`).

## Example

```asm6502
LEDS = $F003
        LDSP #$FF
        LDA  #0
loop:   STA  LEDS      ; count on the debug LEDs
        INC  A
        JMP  loop
```

Errors name the line, e.g. `line 3: 'LDB [X]' does not exist (known: LDB #n, LDB addr)`.
