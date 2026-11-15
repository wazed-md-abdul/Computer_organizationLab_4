# Lab 4 - optional loop trace in Ripes
# Use a 32-bit single-cycle processor with C disabled.
# x2 is deliberately scratch. No stack or function calls are used.

.text
main:
    # SETUP: exclude these three instructions from the measured trace.
    addi x6, x0, 0
    addi x2, x0, 1
    addi x11, x0, 2

trace_start:
loop:
    add  x6, x6, x2
    beq  x6, x11, done
    beq  x0, x0, loop

done:
lab_done:
    # Set a breakpoint here. Stop BEFORE executing this marker.
    # Record the completed instruction count and the final x6 value.
    add  x0, x0, x0
