# Lab 4 - load, add, and store in Ripes
# Select a 32-bit single-cycle processor and disable the C extension.
# x2 is deliberately a scratch register in this standalone experiment.
# No stack or function calls are used.

.data
source_word: .word 7
destination: .word 0

.text
main:
    # SETUP: exclude these instructions from the measured trace.
    la   x10, source_word
    addi x2, x0, 5
    addi x5, x0, 0
    addi x6, x0, 0

trace_start:
    # Record the actual address of trace_start as S.
    # Record the actual address of source_word as B.
    lw   x5, 0(x10)       # S
    add  x6, x5, x2       # S + 4
    sw   x6, 4(x10)       # S + 8

lab_done:
    # Set a breakpoint here. Stop BEFORE executing this marker.
    # The measured interval contains exactly three instructions.
    add  x0, x0, x0
