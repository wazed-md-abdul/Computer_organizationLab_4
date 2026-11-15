# Lab 4 - store with a negative byte offset in Ripes
# Use a 32-bit single-cycle processor with C disabled.

.data
slot: .word 3
next_word: .word 0

.text
main:
    # SETUP: x10 points four bytes beyond slot; x6 contains the store value.
    la   x10, slot
    addi x10, x10, 4
    addi x6, x0, 12

trace_start:
    # Record the actual PC and base register value before this instruction.
    sw   x6, -4(x10)

lab_done:
    # Break here and stop BEFORE this marker.
    # Record the destination memory word and the source registers.
    add  x0, x0, x0
