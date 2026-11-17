LEDS  = $F003

LDSP #$FF                       ; stack setup
LDA  #%00000001                 ; start with lsb (right side)

left:   STA  LEDS
        SHL                     ; shift left
        JNZ  left               ; rinse n repeat
        LDA  #%01000000

right:  STA  LEDS
        SHR                     ; shift right
        JNZ  right
        LDA  #%00000010
        JMP  left
