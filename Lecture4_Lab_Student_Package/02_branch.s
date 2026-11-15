# Lab 4 - compare taken and not-taken branch outcomes in Ripes
# Use a 32-bit single-cycle processor with C disabled.
# Stop immediately after the FIRST beq in the trace.
# x2 is scratch here; this program does not use a stack.

.data
source_word: .word 7
destination: .word 0

.text
main:
    # SETUP: do not include setup in the instruction count.
    la   x10, source_word
    addi x2, x0, 5
    addi x5, x0, 0
    addi x6, x0, 0
INPUT_X11:
    # Change the immediate on the next line from 12 to 9 for the second run.
    addi x11, x0, 12

trace_start:
    # Let S be the actual address of trace_start.
    lw   x5, 0(x10)                 # S
    add  x6, x5, x2                 # S + 4
    sw   x6, 4(x10)                 # S + 8
    beq  x6, x11, branch_taken      # S + 12; target is S + 24

branch_not_taken:
    # Sequential-path instruction at S + 16.
    # Stop BEFORE this instruction for the four-instruction experiment.
    add  x0, x0, x0
    beq  x0, x0, lab_done           # S + 20; outside the measured interval

branch_taken:
    # Branch-target instruction at S + 24.
    # Stop BEFORE this instruction for the four-instruction experiment.
    add  x0, x0, x0

lab_done:
    # Optional end marker for execution beyond the measured interval.
    add  x0, x0, x0
