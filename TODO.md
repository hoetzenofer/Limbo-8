# TODO

## Assembler (`software/asm.py`)

- [ ] tabs between mnemonic and operand do not work
- [ ] running it without arguments prints nothing and exits with code 0
- [ ] character literals `';'` and `' '` don't work
- [ ] `.byte ','` fails: the comma in the character literal is taken as an argument separator
- [ ] `<expr` and `>expr` only apply to the next atom
- [ ] `-o` or `-l` as the last argument (without a file name) crashes with `IndexError`
- [ ] constants (`NAME = ...`) are not checked against register names and may be defined twice
- [ ] `LDX #-1` says "address -1 out of range", although the operand is an immediate

## Microcode Python Files (`microcode/`)

- [ ] revise `instructions.py`
- [ ] revise `microcode.py`

## Assembly CPU Test (`software/cpu_test.asm`)
- [ ] not easily understandable, revise
