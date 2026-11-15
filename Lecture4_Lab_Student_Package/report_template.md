# Lecture 4 Lab Report

Name:  
Student ID:  
Date:  
Ripes version and processor model:  
Python version:  
Actual Ripes B (source_word) and S (trace_start):

Write predictions before running and observations afterwards. Use the handout
for complete task instructions. Expand all response areas as needed.

## A Load add store

| Instruction | Predicted PC/x5/x6/memory after edge | Observed state | Explanation |
|---|---|---|---|
| lw | | | |
| add | | | |
| sw | | | |

- Load ALU result and memory output:
- x5 before and after the edge:
- Store address versus store data:
- Registers unchanged by the store:
- Why the add needs no stall in this model:

Attach `task_a.csv`.

## B Control and decoding

| Instruction | RegWrite | ALUSrc | MemWrite | WBsel | Branch | PCSel |
|---|---|---|---|---|---|---|
| add | | | | | | |
| lw | | | | | | |
| sw | | | | | | |
| beq equal | | | | | | |
| beq unequal | | | | | | |

Explain each X entry:

Explain why the store still uses rs2 when ALUSrc=1:

Decode 0x00652223:

| Field | Value |
|---|---|
| opcode | |
| funct3 | |
| rs1 | |
| rs2 | |
| imm[11:5] | |
| imm[4:0] | |
| Signed immediate | |

Explain bits 11:7 in S format and the extra field that distinguishes add from sub:

## C Branch and signed offset

| x11 | Predicted Eq | PC+4 | Target | PCSel | Observed next PC |
|---|---|---|---|---|---|
| 12 | | | | | |
| 9 | | | | | |

- Branch base address and preserved state:
- Negative store immediate in signed decimal and 32-bit hex:
- Effective address and store data:
- Memory before and after the edge:
- Source registers and PC after the edge:

## D Faults

| Case | Predicted control fault and value | First wrong effect | Clean run evidence |
|---|---|---|---|
| A | | | |
| B | | | |
| C | | | |

- D1: MemWrite=0, correct signals and missing update:
- D2: WBsel=0 and 1 for a store, state comparison and explanation:
- D3: Why internal observations are needed to distinguish faults:

Attach one fault trace or annotated screenshot. State its PC and whether it shows
the state before or after the edge.

## E Timing

| Quantity | Before | After ALU improvement |
|---|---|---|
| Load path ps | | |
| Add path ps | | |
| Branch path ps | | |
| Fixed period ps | | |
| Frequency GHz | | |
| Time for 100 instructions ns | | |

- Load delay calculation:
- Speedup calculation:
- Why the critical path changes:
- Mux output arrival with select at 410 ps:
- Mux output arrival with select at 300 ps:
- Why arrivals are compared rather than added:

## Exit ticket

1. Distinguish a load's address and write-back value.
2. Explain the effect of RegWrite=0.
3. State the conditions for PCSel=1.
4. Explain why CPI=1 does not guarantee a fast processor.

## Optional loop

Visited PCs, x6 after each instruction, total completed instructions, and unchanged memory:
