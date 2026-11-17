LEDS = $F003        ; leds

LDSP #$FF           ; stack pointer
LDA  #%00000001     ; load a with starter value

load:
    STA  LEDS       ; store value from a at $F003
    SHL             ; shift left
    INC  A          ; set last bit to 1
    JNC  load       ; again

unload:
    STA  LEDS
    SHR             ; shift right
    JNZ  unload
    JMP  load       ; from the beginning
