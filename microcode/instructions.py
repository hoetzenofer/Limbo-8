# Limbo-8 instruction set: every opcode with its micro steps.
#
# This table is the only source of the microcode. microcode.py makes the EEPROM images, the ROM contents in
# logisim/limbo.circ and the tables in docs/instruction-set.md from it. Run it after every change:
#
#     python microcode/microcode.py
#
# A step is a string of signals separated by spaces (names as in docs/architecture.md):
#
#     AB=PC  AB=X  AB=SP  AB=MAR     address bus source
#     SRC->DST                       data bus transfer, e.g. MEM->A, A->MEM, ADD->A (ADD->- = no destination)
#     CIN=0  CIN=1  CIN=C            carry in of the adder
#     PC_INC PC_LD X_INC SP_INC SP_DEC ALU_INV FL_ZN FL_C HLT
#     (text)                         a note for the docs
#
# microcode.py adds the fetch step T0 in front and STEP_RST to the last step.

FETCH = "AB=PC MEM->IR PC_INC"                            # T0 of every opcode
ADDR = ["AB=PC MEM->ML PC_INC", "AB=PC MEM->MH PC_INC"]   # 16-bit operand into the MAR, low byte first
JMP = ADDR + ["AB=MAR PC_LD"]

def op(code, name, *steps, note=None):
    return {"code": code, "name": name, "steps": list(steps), "note": note}

def jump(code, name, taken_on):
    return {
        "code": code,
        "name": name,
        "steps": JMP,
        "skip": ["PC_INC", "PC_INC"],
        "taken_on": taken_on
    }

LOAD_STORE = [ # 0001 S R mm: S = store, R = register B, mm = #n / addr / [X] / [X+]
    op(0x10, "LDA #n",   "AB=PC MEM->A PC_INC FL_ZN"),
    op(0x11, "LDA addr", *ADDR, "AB=MAR MEM->A FL_ZN"),
    op(0x12, "LDA [X]",  "AB=X MEM->A FL_ZN"),
    op(0x13, "LDA [X+]", "AB=X MEM->A X_INC FL_ZN"),
    op(0x14, "LDB #n",   "AB=PC MEM->B PC_INC FL_ZN"),
    op(0x15, "LDB addr", *ADDR, "AB=MAR MEM->B FL_ZN"),
    op(0x19, "STA addr", *ADDR, "AB=MAR A->MEM"),
    op(0x1A, "STA [X]",  "AB=X A->MEM"),
    op(0x1B, "STA [X+]", "AB=X A->MEM", "X_INC"),
    op(0x1D, "STB addr", *ADDR, "AB=MAR B->MEM"),
]

TRANSFER = [ # MOV target,source; X and SP
    op(0x20, "MOV A,B",  "B->A FL_ZN"),
    op(0x21, "MOV B,A",  "A->B FL_ZN"),
    op(0x22, "MOV A,XL", "XL->A FL_ZN"),
    op(0x23, "MOV A,XH", "XH->A FL_ZN"),
    op(0x24, "MOV XL,A", "A->XL"),
    op(0x25, "MOV XH,A", "A->XH"),
    op(0x30, "LDX #nn",  "AB=PC MEM->XL PC_INC", "AB=PC MEM->XH PC_INC"),
    op(0x31, "INX",      "X_INC"),
    op(0x32, "JMP X",    "AB=X PC_LD"),
    op(0x33, "LDSP #n",  "AB=PC MEM->SP (no PC_INC)", "PC_INC"),
]

JUMPS = [ # 0100 0 p ff: ff = Z / C / N / always (cond mux input), p = 1 jumps on 0
    op(0x43, "JMP addr", *JMP, note="same for A12 = 0 and 1"),
    jump(0x40, "JZ addr",  taken_on=1),
    jump(0x41, "JC addr",  taken_on=1),
    jump(0x42, "JN addr",  taken_on=1),
    jump(0x44, "JNZ addr", taken_on=0),
    jump(0x45, "JNC addr", taken_on=0),
    jump(0x46, "JNN addr", taken_on=0),
    op(0x48, "CALL addr", *ADDR, "AB=SP PCH->MEM", "SP_DEC", "AB=SP PCL->MEM", "AB=MAR PC_LD SP_DEC"),
    op(0x49, "RET", "SP_INC", "AB=SP MEM->ML SP_INC", "AB=SP MEM->MH", "AB=MAR PC_LD"),
]

STACK = [ # 0101 P rrr: P = pop, rrr = A / B / XL / XH / F
    op(0x50, "PUSH A",  "AB=SP A->MEM", "SP_DEC"),
    op(0x51, "PUSH B",  "AB=SP B->MEM", "SP_DEC"),
    op(0x52, "PUSH XL", "AB=SP XL->MEM", "SP_DEC"),
    op(0x53, "PUSH XH", "AB=SP XH->MEM", "SP_DEC"),
    op(0x54, "PUSH F",  "AB=SP Flags->MEM", "SP_DEC"),
    op(0x58, "POP A",   "SP_INC", "AB=SP MEM->A FL_ZN"),
    op(0x59, "POP B",   "SP_INC", "AB=SP MEM->B FL_ZN"),
    op(0x5A, "POP XL",  "SP_INC", "AB=SP MEM->XL"),
    op(0x5B, "POP XH",  "SP_INC", "AB=SP MEM->XH"),
    op(0x5C, "POP F",   "SP_INC", "AB=SP MEM->Flags"),
]

ALU_MODES = [
    ("#n",   ["AB=PC MEM->T PC_INC"]),
    ("addr", ADDR + ["AB=MAR MEM->T"]),
    ("[X]",  ["AB=X MEM->T"]),
    ("B",    ["B->T"]),
]

ALU_OPS = [
    ("ADD", "ADD->A FL_ZN FL_C"),
    ("ADC", "ADD->A CIN=C FL_ZN FL_C"),
    ("SUB", "ADD->A ALU_INV CIN=1 FL_ZN FL_C"),
    ("SBC", "ADD->A ALU_INV CIN=C FL_ZN FL_C"),
    ("AND", "AND->A FL_ZN"),
    ("OR",  "OR->A FL_ZN"),
    ("XOR", "XOR->A FL_ZN"),
    ("CMP", "ADD->- ALU_INV CIN=1 FL_ZN FL_C"),
]

ALU = [
    op(0x80 | o << 2 | m, f"{name} {mode}", *operand, last)
    for o, (name, last) in enumerate(ALU_OPS)
    for m, (mode, operand) in enumerate(ALU_MODES)
]

SINGLE = [ # single instructions on A
    op(0x60, "INC A", "$00->T", "ADD->A CIN=1 FL_ZN"),
    op(0x61, "DEC A", "$00->T", "ADD->A ALU_INV CIN=0 FL_ZN"),
    op(0x62, "SHL",   "A->T", "ADD->A FL_ZN FL_C"),
    op(0x63, "SHR",   "SHR->A FL_ZN"),
]

MISC = [
    op(0x00, "NOP", ""),
    op(0xFF, "HLT", "HLT"),
]

SECTIONS = {
    "load": LOAD_STORE,
    "transfer": TRANSFER,
    "jump": JUMPS,
    "stack": STACK,
    "alu": ALU,
    "single": SINGLE,
    "misc": MISC
}
