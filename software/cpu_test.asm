; program that checks if instructions work.
; finished on a crisp tuesday afternoon.
; somehow probably works, will revise later (./TODO.md)

LEDS    = $F003
VAR     = $8000
BUF     = $8100
STACK   = $DF00

        .org $0000
start:  LDSP #$FF
        NOP

; ----- 1: loads set Z and N
        LDA #1
        STA LEDS
        LDA #0
        JNZ fail
        JN  fail
        LDA #$80
        JZ  fail
        JNN fail
        LDB #0
        JNZ fail
        LDB #$FF
        JNN fail

; ----- 2: memory, MOV
        LDA #2
        STA LEDS
        LDA #$5C
        STA VAR
        LDA #0
        LDA VAR
        CMP #$5C
        JNZ fail
        LDB #$3A
        STB VAR+1
        LDB #0
        LDB VAR+1
        MOV A,B
        CMP #$3A
        JNZ fail
        LDA #$77
        MOV B,A
        LDA #0
        MOV A,B
        CMP #$77
        JNZ fail
        LDB VAR
        MOV A,B
        CMP #$5C
        JNZ fail
        LDA table+2
        CMP #$C3
        JNZ fail
        LDA #$FF
        STA $DFFE
        LDA #$01
        STA $8002
        LDA $DFFE
        CMP #$FF
        JNZ fail
        LDA $8002
        CMP #$01
        JNZ fail

; ----- 3: ALU with operand in B (B = $0F, A = $3C)
        LDA #3
        STA LEDS
        LDB #$0F
        LDA #$3C
        ADD B
        JC  fail
        CMP #$4B
        JNZ fail
        LDA #$3C
        CMP #0
        ADC B
        CMP #$4C
        JNZ fail
        LDA #$3C
        SUB B
        JNC fail
        CMP #$2D
        JNZ fail
        LDA #$3C
        ADD #0
        SBC B
        CMP #$2C
        JNZ fail
        LDA #$3C
        AND B
        CMP #$0C
        JNZ fail
        LDA #$3C
        OR  B
        CMP #$3F
        JNZ fail
        LDA #$3C
        XOR B
        CMP #$33
        JNZ fail
        LDA #$3C
        CMP B
        JZ  fail
        JNC fail
        CMP #$3C
        JNZ fail

; ----- 4: ALU with operand in memory (VAR = $0F)
        LDA #4
        STA LEDS
        LDA #$0F
        STA VAR
        LDA #$3C
        ADD VAR
        CMP #$4B
        JNZ fail
        LDA #$3C
        CMP #0
        ADC VAR
        CMP #$4C
        JNZ fail
        LDA #$3C
        SUB VAR
        JNC fail
        CMP #$2D
        JNZ fail
        LDA #$3C
        ADD #0
        SBC VAR
        CMP #$2C
        JNZ fail
        LDA #$3C
        AND VAR
        CMP #$0C
        JNZ fail
        LDA #$3C
        OR  VAR
        CMP #$3F
        JNZ fail
        LDA #$3C
        XOR VAR
        CMP #$33
        JNZ fail
        LDA #$3C
        CMP VAR
        JZ  fail
        JNC fail

; ----- 5: ALU with operand at [X] (X = VAR)
        LDA #5
        STA LEDS
        LDX #VAR
        LDA #$3C
        ADD [X]
        CMP #$4B
        JNZ fail
        LDA #$3C
        CMP #0
        ADC [X]
        CMP #$4C
        JNZ fail
        LDA #$3C
        SUB [X]
        JNC fail
        CMP #$2D
        JNZ fail
        LDA #$3C
        ADD #0
        SBC [X]
        CMP #$2C
        JNZ fail
        LDA #$3C
        AND [X]
        CMP #$0C
        JNZ fail
        LDA #$3C
        OR  [X]
        CMP #$3F
        JNZ fail
        LDA #$3C
        XOR [X]
        CMP #$33
        JNZ fail
        LDA #$3C
        CMP [X]
        JZ  fail
        JNC fail

; ----- 6: ALU with immediate operand, carry and borrow
        LDA #6
        STA LEDS
        LDA #$3C
        ADD #$0F
        CMP #$4B
        JNZ fail
        LDA #$3C
        CMP #0
        ADC #$0F
        CMP #$4C
        JNZ fail
        LDA #$3C
        SUB #$0F
        CMP #$2D
        JNZ fail
        LDA #$3C
        ADD #0
        SBC #$0F
        CMP #$2C
        JNZ fail
        LDA #$3C
        AND #$0F
        CMP #$0C
        JNZ fail
        LDA #$3C
        OR  #$0F
        CMP #$3F
        JNZ fail
        LDA #$3C
        XOR #$0F
        CMP #$33
        JNZ fail
        LDA #$F0
        ADD #$20
        JNC fail
        CMP #$10
        JNZ fail
        LDA #$20
        SUB #$50
        JC  fail
        JNN fail
        CMP #$D0
        JNZ fail
        LDA #$40
        CMP #$41
        JC  fail
        JZ  fail
        CMP #$40
        JNZ fail
        JNC fail
        LDA #$0F
        NOT
        CMP #$F0
        JNZ fail

; ----- 7: INC, DEC, SHL, SHR
        LDA #7
        STA LEDS
        LDA #$FF
        CMP #0
        INC A
        JNZ fail
        JNC fail
        DEC A
        JNN fail
        CMP #$FF
        JNZ fail
        LDA #$81
        SHL
        JNC fail
        CMP #$02
        JNZ fail
        LDA #$40
        SHL
        JC  fail
        JNN fail
        LDA #$81
        ADD #0
        SHR
        JC  fail
        CMP #$40
        JNZ fail
        LDA #$01
        SHR
        JNZ fail

; ----- 8: X register
        LDA #8
        STA LEDS
        LDX #$1234
        MOV A,XL
        CMP #$34
        JNZ fail
        MOV A,XH
        CMP #$12
        JNZ fail
        LDA #$9A
        MOV XL,A
        LDA #$BC
        MOV XH,A
        MOV A,XL
        CMP #$9A
        JNZ fail
        MOV A,XH
        CMP #$BC
        JNZ fail
        LDX #$80FF
        INX
        MOV A,XL
        CMP #$00
        JNZ fail
        MOV A,XH
        CMP #$81
        JNZ fail
        LDX #$FFFF
        INX
        MOV A,XH
        CMP #0
        JNZ fail

; ----- 9: pointers [X], [X+]
        LDA #9
        STA LEDS
        LDX #BUF
        LDA #$11
        STA [X+]
        LDA #$22
        STA [X+]
        LDA #$33
        STA [X]
        LDX #BUF
        LDA [X+]
        CMP #$11
        JNZ fail
        LDA [X+]
        CMP #$22
        JNZ fail
        LDA [X]
        CMP #$33
        JNZ fail
        MOV A,XL
        CMP #<(BUF+2)
        JNZ fail
        LDX #table
        LDA [X+]
        CMP #$A5
        JNZ fail
        LDA [X]
        CMP #$5A
        JNZ fail
        LDX #jx
        JMP X
        JMP fail
jx:     NOP

; ----- 10: conditional jumps, taken and not taken
        LDA #10
        STA LEDS
        LDA #0
        JZ  j1
        JMP fail
j1:     JNZ fail
        JNN j2
        JMP fail
j2:     JN  fail
        CMP #1
        JC  fail
        JNC j3
        JMP fail
j3:     JN  j4
        JMP fail
j4:     JZ  fail
        JNZ j5
        JMP fail
j5:     CMP #0
        JC  j6
        JMP fail
j6:     JNC fail
        LDA #5
        LDB #0
loop:   MOV B,A
        DEC A
        JNZ loop
        MOV A,B
        CMP #1
        JNZ fail

; ----- 11: stack, PUSH/POP of every register, flags on the stack
        LDA #11
        STA LEDS
        LDA #$11
        PUSH A
        LDB #$22
        PUSH B
        LDX #$3344
        PUSH XL
        PUSH XH
        LDA $DFFF
        CMP #$11
        JNZ fail
        LDA #0
        CMP #0
        PUSH F
        LDA #$80
        ADD #0
        POP F
        JNZ fail
        JNC fail
        JN  fail
        LDX #0
        POP XH
        POP XL
        MOV A,XH
        CMP #$33
        JNZ fail
        MOV A,XL
        CMP #$44
        JNZ fail
        POP B
        POP A
        CMP #$11
        JNZ fail
        MOV A,B
        CMP #$22
        JNZ fail
        LDA #$82
        PUSH A
        POP F
        JNN fail
        JNZ fail
        JC  fail
        LDA #$FF
        CMP #$01
        PUSH F
        POP A
        CMP #$81
        JNZ fail
        LDA #0
        ADD #0
        PUSH F
        POP A
        CMP #$02
        JNZ fail
        LDA #$02
        PUSH A
        POP F
        JNZ fail
        JC  fail
        JN  fail
        LDSP #$80
        LDA #$6D
        PUSH A
        LDA STACK+$80
        CMP #$6D
        JNZ fail
        LDSP #$FF

; ----- 12: CALL and RET, nested
        LDA #12
        STA LEDS
        LDA #0
        CALL sub1
ret1:   CMP #3
        JNZ fail
        LDA STACK+$FF
        CMP #>ret1
        JNZ fail
        LDA STACK+$FE
        CMP #<ret1
        JNZ fail

; ----- done
        LDA #$5A
        STA LEDS
done:   HLT

fail:   HLT

sub1:   INC A
        CALL sub2
        INC A
        RET
sub2:   INC A
        RET

table:  .byte $A5, $5A, $C3
