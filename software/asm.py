# syntax (similar to 6502 assemblers):
#   label:  MNEMONIC operand   ; comment      labels end with ':', case-sensitive
#   NAME = expression                         constant
#   .org expression                           continue at this address
#   .byte expr, "text", ...                   bytes; .word expr, ... = 16 bit little-endian
#   operands: #expr (immediate), expr (address), [X], [X+], registers as in the table (MOV A,B, PUSH F, ...)
#   expressions: $1F (hex), %1010 (binary), 31, 'A', labels, * (current address), + - ( ), <expr = low byte, >expr = high byte
#   NOT is XOR #$FF (docs/instruction-set.md, section 8). unused ROM bytes are $FF (erased EEPROM = HLT).

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(ROOT / "microcode"))
import instructions

ROM_SIZE = 0x8000
LST_HEX_WIDTH = 13
REGISTER_NAMES = {
    "A",
    "B",
    "X",
    "XL",
    "XH",
    "F",
    "SP",
    "PC"
}

class AsmError(Exception):
    pass

def opcode_table():
    table = {}

    for entries in instructions.SECTIONS.values():
        for e in entries:
            mnemonic, _, pattern = e["name"].partition(" ")
            table.setdefault(mnemonic.upper(), {})[pattern.replace(" ", "").upper()] = e["code"]

    return table

OPCODES = opcode_table()
NAMES = {}
for _entries in instructions.SECTIONS.values():
    for _e in _entries:
        NAMES.setdefault(_e["name"].partition(" ")[0].upper(), []).append(_e["name"])

def evaluate(text, symbols, here, final):
    tokens = re.findall(r"\$[0-9A-Fa-f]+|%[01]+|\d+|'.'|[A-Za-z_][A-Za-z0-9_]*|[-+()<>*]", text)

    if "".join(tokens) != re.sub(r"\s+", "", text):
        raise AsmError(f"cannot read expression '{text}'")
    
    pos = 0

    def peek():
        return tokens[pos] if pos < len(tokens) else None

    def take():
        nonlocal pos
        pos += 1
        return tokens[pos - 1]

    def atom():
        t = take() if peek() is not None else None

        if t is None:
            raise AsmError(f"expression '{text}' ends too early")
        
        if t == "(":
            v = expr()
            if peek() != ")":
                raise AsmError(f"missing ')' in '{text}'")
            take()
            return v
        if t == "-":
            return -atom()
        if t == "<":
            return atom() & 0xFF
        if t == ">":
            return (atom() >> 8) & 0xFF
        if t == "*":
            return here
        if t.startswith("$"):
            return int(t[1:], 16)
        if t.startswith("%"):
            return int(t[1:], 2)
        if t.startswith("'"):
            return ord(t[1])
        if t.isdigit():
            return int(t)
        if t in symbols:
            return symbols[t]
        if final:
            raise AsmError(f"unknown label '{t}'")
        return 0

    def expr():
        v = atom()

        while peek() in ("+", "-"):
            v = v + atom() if take() == "+" else v - atom()

        return v

    value = expr()

    if pos != len(tokens):
        raise AsmError(f"cannot read expression '{text}'")
    
    return value

def split_args(text):
    args, cur, quoted = [], "", False

    for ch in text:
        if ch == '"':
            quoted = not quoted

        if ch == "," and not quoted:
            args.append(cur.strip())
            cur = ""

        else:
            cur += ch

    if cur.strip():
        args.append(cur.strip())

    return args

def parse_operand(mnemonic, operand):
    patterns = OPCODES[mnemonic]
    norm = operand.replace(" ", "").upper()

    if norm in patterns:
        return norm, None
    
    if operand.startswith("#"):
        for p in ("#n", "#nn"):
            if p.upper() in patterns:
                return p.upper(), operand[1:].strip()
            
        raise AsmError(f"{mnemonic} has no immediate form")
    
    looks_like_register = norm in REGISTER_NAMES or norm.startswith("[") or "," in norm

    if operand and "ADDR" in patterns and not looks_like_register:
        return "ADDR", operand
    
    forms = ", ".join(NAMES[mnemonic])

    raise AsmError(f"'{mnemonic} {operand}' does not exist (known: {forms})")

def strip_comment(line):
    out, quoted = "", False

    for ch in line:
        if ch == '"':
            quoted = not quoted

        if ch == ";" and not quoted:
            break

        out += ch

    return out.strip()

def assemble(text):
    lines = text.splitlines()
    symbols = {}

    for final in (False, True):
        here, image, listing = 0, {}, []

        for no, raw in enumerate(lines, 1):
            try:
                line = strip_comment(raw)
                m = re.match(r"([A-Za-z_][A-Za-z0-9_]*):\s*(.*)", line)

                if m:
                    label, line = m.group(1), m.group(2)

                    if label.upper() in REGISTER_NAMES:
                        raise AsmError(f"label '{label}' looks like a register")
                    
                    if not final:
                        if label in symbols:
                            raise AsmError(f"label '{label}' defined twice")
                        
                        symbols[label] = here

                m = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)", line)

                if m:
                    symbols[m.group(1)] = evaluate(m.group(2), symbols, here, final)
                    listing.append(f"{'':{6 + LST_HEX_WIDTH}} {raw}")
                    continue

                start, data = here, []

                if not line:
                    pass

                elif line.lower().startswith(".org"):
                    here = evaluate(line[4:], symbols, here, True)
                    start = here

                elif line.lower().startswith((".byte", ".word")):
                    word = line.lower().startswith(".word")

                    for arg in split_args(line[5:]):
                        if arg.startswith('"'):
                            if word or not arg.endswith('"') or len(arg) < 2:
                                raise AsmError(f"bad string {arg}")
                            
                            data += [ord(ch) for ch in arg[1:-1]]

                        else:
                            v = evaluate(arg, symbols, here + len(data), final)
                            data += [v & 0xFF, (v >> 8) & 0xFF] if word else [v & 0xFF]

                            if final and not (-0x8000 <= v <= 0xFFFF if word else -0x80 <= v <= 0xFF):
                                raise AsmError(f"value {v} too big for {'.word' if word else '.byte'}")
                else:
                    mnemonic, _, operand = line.partition(" ")
                    mnemonic, operand = mnemonic.upper(), operand.strip()

                    if mnemonic == "NOT" and not operand:
                        mnemonic, operand = "XOR", "#$FF"

                    if mnemonic not in OPCODES:
                        raise AsmError(f"unknown instruction '{mnemonic}'")
                    
                    pattern, exp = parse_operand(mnemonic, operand)
                    data = [OPCODES[mnemonic][pattern]]

                    if exp is not None:
                        v = evaluate(exp, symbols, here, final)

                        if pattern == "#N":
                            if final and not -0x80 <= v <= 0xFF:
                                raise AsmError(f"immediate {v} does not fit into 8 bits")
                            
                            data.append(v & 0xFF)

                        else:
                            if final and not 0 <= v <= 0xFFFF:
                                raise AsmError(f"address {v} out of range")
                            
                            data += [v & 0xFF, (v >> 8) & 0xFF]

                for k, b in enumerate(data):
                    if final and here + k in image:
                        raise AsmError(f"address ${here + k:04X} written twice")
                    
                    image[here + k] = b

                here += len(data)
                listing.append(f"{start:04X}  {' '.join(f'{b:02X}' for b in data[:4]):{LST_HEX_WIDTH}} {raw}")

            except AsmError as err:
                raise AsmError(f"line {no}: {err}\n    {raw.strip()}") from None
            
    return image, listing, symbols

def rom_image(image):
    bad = [a for a in image if not 0 <= a < ROM_SIZE]

    if bad:
        raise AsmError(f"code outside the ROM ($0000-$7FFF): ${min(bad):04X}")
    
    rom = bytearray([0xFF] * ROM_SIZE)

    for a, b in image.items():
        rom[a] = b

    return bytes(rom)

def main(argv):
    if not argv or argv[0].startswith("-"):
        raise SystemExit(__doc__)
    
    src = Path(argv[0])
    out = Path(argv[argv.index("-o") + 1]) if "-o" in argv else src.with_suffix(".bin")
    lst = Path(argv[argv.index("-l") + 1]) if "-l" in argv else src.with_suffix(".lst")

    if not src.is_file():
        raise SystemExit(f"{src}: file not found")
    
    try:
        image, listing, _ = assemble(src.read_text(encoding="utf-8"))
        rom = rom_image(image)

    except AsmError as err:
        raise SystemExit(f"{src}: {err}")
    
    out.write_bytes(rom)
    lst.write_text("\n".join(listing) + "\n", encoding="utf-8", newline="\n")
    print(f"{src}: {len(image)} bytes -> {out}, listing {lst}")

if __name__ == "__main__":
    main(sys.argv[1:])
