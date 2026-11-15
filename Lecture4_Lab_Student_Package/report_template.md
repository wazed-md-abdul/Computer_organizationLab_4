# Lecture 4 Lab Report: CPU Datapath and Control

**Name:** Student Report  
**Student ID:** 2026-CO-LAB4  
**Date:** November 15, 2026  
**Ripes version and processor model:** Ripes v2.2.6, 32-bit Single-Cycle Processor (`RV32_SS`), Extended Layout, C extension disabled  
**Python version:** Python 3.14.7  
**Actual Ripes B (source_word) and S (trace_start):**  
- Ripes: `B = 0x10000000`, `S = 0x00000014` (PC = 0x14 for `01_load_add_store.s`)  
- Course Teaching Model (`lab4_cpu.py`): `B = 0x00001000`, `S = 0x00000000`  

---

## Task A: Load Add Store

### Execution State Trace Table

| Instruction | Predicted PC/x5/x6/memory after edge | Observed state | Explanation |
|---|---|---|---|
| `lw x5, 0(x10)` | PC = 0x04 (Ripes: 0x18)<br>x5 = 7 (0x07), x6 = 0<br>M[B] = 7, M[B+4] = 0 | PC = 0x00000004 (Ripes: 0x18)<br>x5 = 0x00000007, x6 = 0x00000000<br>M[0x1000] = 0x07, M[0x1004] = 0x00 | ALU calculates effective address `x10 + 0 = 0x1000`. Data memory outputs 7. `WBsel=1` routes memory output to write-back data bus. `RegWrite=1` enables register write. At the rising clock edge, x5 latches 7. PC increments by 4. Memory and other registers remain unchanged. |
| `add x6, x5, x2` | PC = 0x08 (Ripes: 0x1C)<br>x5 = 7, x6 = 12 (0x0C)<br>M[B] = 7, M[B+4] = 0 | PC = 0x00000008 (Ripes: 0x1C)<br>x5 = 0x00000007, x6 = 0x0000000C<br>M[0x1000] = 0x07, M[0x1004] = 0x00 | ALU reads x5 (7) and x2 (5); `ALUSrc=0` selects rs2. Main ALU adds `7 + 5 = 12 (0x0C)`. `WBsel=0` routes ALUResult to write-back bus. `RegWrite=1` enables register write. At the rising edge, x6 latches 12. PC increments by 4. Memory remains unchanged. |
| `sw x6, 4(x10)` | PC = 0x0C (Ripes: 0x20)<br>x5 = 7, x6 = 12 (0x0C)<br>M[B] = 7, M[B+4] = 12 (0x0C) | PC = 0x0000000C (Ripes: 0x20)<br>x5 = 0x00000007, x6 = 0x0000000C<br>M[0x1000] = 0x07, M[0x1004] = 0x0C | ALU calculates effective address `x10 + 4 = 0x1004` (`ALUSrc=1` selects immediate 4). StoreData bus routes rs2 (x6=12) directly to Data Memory write-data port. `MemWrite=1` enables memory write; `RegWrite=0` disables register write. At rising edge, M[0x1004] updates from 0 to 12. All integer registers remain unchanged. |

### Analysis Questions

- **Load ALU result and memory output:**  
  The main ALU calculates effective address `0x00001000` (`x10 + 0`). Data Memory combinational read port settles `MemReadData = 0x00000007`, which propagates through the write-back multiplexer (`WBsel=1`) onto the `WBData` bus as candidate value 7.
- **x5 before and after the edge:**  
  The processor uses synchronous, edge-triggered register storage. Throughout Cycle 1 prior to the rising clock edge, wire values are transient combinational candidates; register x5 retains its pre-existing stored value `0x00000000`. Only when the rising clock edge arrives—sampling `RegWrite=1`—does x5 latch the candidate value from `WBData`, committing the transition from 0 to 7.
- **Store address versus store data:**  
  - *Where to write (effective address):* Computed by the main ALU adding base register `rs1` (`x10 = 0x1000`) and the sign-extended 12-bit immediate offset (4), selected via `ALUSrc=1`. The result `0x1004` is connected directly to the Data Memory address port.
  - *What to write (store data):* Read combinationally from register file read port 2 (`rs2 = x6 = 12`) along a dedicated internal bus to the Data Memory `WriteData` port, completely bypassing the ALU.
- **Registers unchanged by the store:**  
  `RegWrite = 0` deasserts the register file write enable. As a result, no integer registers (x0–x31) are modified. Source registers x10 and x6, intermediate register x5, and all others remain strictly preserved.
- **Why the add needs no stall in this model:**  
  In a single-cycle CPU architecture, each instruction executes to full completion within exactly one clock cycle. The value loaded into x5 commits to the register file at the rising clock edge ending Cycle 1 (the `lw`). When Cycle 2 (the `add`) begins immediately after this clock edge, the register file read port combinationally reads the newly committed value (7) in x5. Because instructions execute strictly sequentially without overlapping pipeline stages, there are no pipeline hazards (RAW data hazards) and thus no need for pipeline stalls, bubbles, or forwarding hardware.

*Attachment: `task_a.csv` is generated and attached.*

---

## Task B: Control and Decoding

### Control Signal Table

| Instruction | RegWrite | ALUSrc | MemWrite | WBsel | Branch | PCSel |
|---|---|---|---|---|---|---|
| `add` | 1 | 0 | 0 | 0 | 0 | 0 |
| `lw` | 1 | 1 | 0 | 1 | 0 | 0 |
| `sw` | 0 | 1 | 1 | X (0) | 0 | 0 |
| `beq equal` | 0 | X (0) | 0 | X (0) | 1 | 1 |
| `beq unequal` | 0 | X (0) | 0 | X (0) | 1 | 0 |

### Analysis Questions

- **Explain each X entry:**  
  1. `sw` (`WBsel = X`): `WBsel` chooses whether `ALUResult` (0) or `MemReadData` (1) drives the write-back bus to the register file. For `sw`, `RegWrite = 0` deasserts the register write enable. Because no register latches the write-back bus, the multiplexer selection has zero architectural effect. The course tracer defaults `WBsel` to 0 for deterministic outputs.  
  2. `beq` (`ALUSrc = X`, `WBsel = X`): In this architecture, `beq` evaluates equality using a dedicated comparator (`Read1 == Read2`) and computes the branch target using a dedicated adder (`PC + imm`). The main ALU result and memory output are completely unused. Furthermore, `RegWrite = 0` and `MemWrite = 0` prevent any state changes to registers or memory. Therefore, both `ALUSrc` (ALU input B mux) and `WBsel` are true don't-cares. The tracer defaults both to 0.
- **Explain why the store still uses rs2 when ALUSrc=1:**  
  In `sw`, the ALU must compute the destination memory address (`rs1 + offset`), which requires `ALUSrc = 1` to route the sign-extended immediate instead of `rs2` into the ALU. However, the store instruction must also supply the data word to store. The datapath contains a separate, dedicated wire routing the second register read port (`Read2 / rs2`) directly to the Data Memory `WriteData` input. Thus, `rs2` is actively used for memory data even though `ALUSrc = 1` selects the immediate for the ALU.

### Instruction Decoding: 0x00652223

Binary: `0000 0000 0110 0101 0010 0010 0010 0011`

| Field | Bit Positions | Value | Interpretation |
|---|---|---|---|
| `opcode` | 6:0 | `0100011` (`0x23`) | STORE instruction class |
| `funct3` | 14:12 | `010` (`0x2`) | Word store width (`sw`, 32 bits) |
| `rs1` | 19:15 | `01010` (10) | Base address register `x10` |
| `rs2` | 24:20 | `00110` (6) | Source store data register `x6` |
| `imm[11:5]` | 31:25 | `0000000` (0) | Upper 7 bits of store immediate |
| `imm[4:0]` | 11:7 | `00100` (4) | Lower 5 bits of store immediate |
| **Signed immediate** | Concatenated | **+4** | `imm[11:5] ## imm[4:0] = 000000000100_2 = +4` (`0x00000004`) |

- **Explain bits 11:7 in S format and the extra field that distinguishes add from sub:**  
  - *S-format bits 11:7 (B1):* In RISC-V, source register specifiers `rs1` (bits 19:15) and `rs2` (bits 24:20) remain in identical bit positions across all instruction formats to keep register read decoding simple and uniform. Store instructions write to memory rather than registers and therefore do not have a destination register (`rd`). To utilize all instruction bits without adding decode complexity, the 5 bits at positions 11:7 (which hold `rd` in R-type and I-type instructions) are repurposed to hold the lower 5 bits of the immediate offset (`imm[4:0]`).  
  - *Add vs. Sub distinction (B2):* Both `add` and `sub` are R-type instructions sharing identical opcode `0110011` (`0x33`) and identical `funct3 = 000`. They are uniquely distinguished by the 7-bit `funct7` field at bits 31:25: `add` has `funct7 = 0000000` (`0x00`), whereas `sub` has `funct7 = 0100000` (`0x20`, with bit 30 set high).

---

## Task C: Branch and Signed Offset

### Branch Outcomes Table

| x11 | Predicted Eq | Sequential PC (PC+4) | Target PC (PC+12) | PCSel | Observed next PC |
|---|---|---|---|---|---|
| 12 | 1 | 0x00000010 (Ripes: 0x28) | 0x00000018 (Ripes: 0x30) | 1 | 0x00000018 (Ripes: 0x30) |
| 9 | 0 | 0x00000010 (Ripes: 0x28) | 0x00000018 (Ripes: 0x30) | 0 | 0x00000010 (Ripes: 0x28) |

### Analysis Questions

- **Branch base address and preserved state:**  
  - *C1a (State Preserved vs. Changed):* `beq` writes NEITHER an integer register nor a memory word (`RegWrite = 0`, `MemWrite = 0`). All register file contents (x0–x31) and data memory words remain completely unchanged. The ONLY architectural state component that changes at the clock edge is the Program Counter (PC), updating to the branch target address (`PC+12`) if taken (`x11=12`), or to sequential `PC+4` if not taken (`x11=9`).  
  - *C1b (Branch Base Address):* In RISC-V RV32I, branch offsets are PC-relative, defined with respect to the address of the branch instruction itself (PC), not PC+4. The branch target adder computes `Target = PC + imm`. If the offset (+12 bytes) were added to PC+4, the target would be shifted forward by 4 extra bytes (`Target = PC+16`), corrupting control flow and jumping to the wrong instruction.
- **Negative store immediate in signed decimal and 32-bit hex:**  
  Signed decimal value is `-4`. In 12-bit signed two's complement it is `0xFFC` (binary `1111 1111 1100`), and sign-extended to 32 bits it is `0xFFFFFFFC`.
- **Effective address and store data:**  
  - *Course Model:* Effective address = `x10 + (-4) = 0x00001008 + (-4) = 0x00001004`. Store data = `x6 = 12` (`0x0000000C`).  
  - *Ripes:* Effective address = `x10 + (-4) = 0x10000004 + (-4) = 0x10000000` (`slot`). Store data = `x6 = 12` (`0x0000000C`).
- **Memory before and after the edge:**  
  - *Course Model:* Before edge, `M[0x1004] = 0x00000003`; after rising edge, `M[0x1004] = 0x0000000C` (12).  
  - *Ripes:* Before edge, `M[0x10000000] = 0x00000003`; after rising edge, `M[0x10000000] = 0x0000000C` (12).
- **Source registers and PC after the edge:**  
  Base register `x10` (`0x1008` in Python, `0x10000004` in Ripes) and data register `x6` (12) are completely unchanged (`RegWrite=0`). Next PC advances from `0x20` to `0x24` (`PC+4`) in Python, and from `0x10` to `0x14` in Ripes.  
  *Checkpoint reasoning:* Changing the offset from positive to negative alters only the immediate generator and ALU input B for address calculation. The store data wire is tapped directly from register read port 2 (`Read2`), which is selected exclusively by `rs2` and independent of the address calculation.

---

## Task D: Fault Diagnosis

### Fault Diagnosis Table

| Case | Predicted control fault and value | First wrong effect | Clean run evidence |
|---|---|---|---|
| A | `ALUSrc` stuck at 0<br>(forced `ALUSrc=0`, expected 1) | ALU selects `Read2` (x6=12) instead of imm 4. ALU computes `0x1000 + 12 = 0x100C`. `M[0x100C]` is overwritten with 12, while target `M[0x1004]` remains 0. | In clean store (`--scenario store`), `ALUSrc=1`, ALU computes `0x1004`, and `M[0x1004]` is correctly updated to 12. |
| B | `RegWrite` stuck at 0<br>(forced `RegWrite=0`, expected 1) | Memory correctly reads 7 and `WBData=7`, but register write enable is low. At rising edge, x5 is NOT updated and stays at 0. | In clean load (`--scenario load`), `RegWrite=1`, and x5 updates from 0 to 7 at the rising clock edge. |
| C | `PCSel` stuck at 0<br>(forced `PCSel=0`, expected 1) | Even though `Branch=1` and `Eq=1` (x6==x11=12) and `Target=0x2C`, `PCSel` mux selects sequential `PC+4` (0x24) instead of target 0x2C. | In clean branch (`--scenario branch`), `PCSel=1`, and PC updates to branch target 0x2C at the clock edge. |

### Analysis Questions

- **D1: MemWrite=0, correct signals and missing update:**  
  - *Signals Remaining Correct:* All address calculation and data routing signals are fully correct: `ALU_A = 0x1000`, `ALU_B = 4` (`ALUSrc=1`), `ALUResult = 0x1004`, `StoreData = 12` (`0x0C`), and `RegWrite = 0`.  
  - *Missing Update:* Because `MemWrite = 0`, the write enable port of Data Memory is deasserted. At the rising clock edge, no write occurs; memory word `M[0x1004]` remains `0x00000000`.  
  - *Comparison with Case A:* In Case A, routing was faulty (`ALUSrc=0` routed x6 instead of imm) but write permission was active (`MemWrite=1`), causing an unintended write to the WRONG memory address (`0x100C`). In D1, routing is correct (address is `0x1004`), but write permission is revoked (`MemWrite=0`), resulting in NO write occurring anywhere in memory.
- **D2: WBsel=0 and 1 for a store, state comparison and explanation:**  
  - *Architectural State Comparison:* In both runs (`WBsel=0` and `WBsel=1`), the post-edge architectural state is 100% IDENTICAL: `PC = 0x0000000C`, `M[0x1004] = 0x0000000C`, `x5 = 0`, and `x6 = 12`.  
  - *Explanation:* In a store instruction, `RegWrite = 0`. Because the register file write enable is low, the register file ignores whatever value is present on the write-back bus (`WBData`). Whether `WBsel=0` routes the ALU result (`0x1004`) or `WBsel=1` routes data memory output (`0x0000`) to `WBData`, neither value is ever latched into any register. Thus, an unused wire value cannot alter architectural state, proving `WBsel` is a true don't-care for stores.
- **D3: Why internal observations are needed to distinguish faults:**  
  Observing only external/architectural symptoms such as "x5 stayed zero" is insufficient because multiple distinct hardware faults cause the exact same external outcome:
  1. `RegWrite` control stuck at 0 (write enable inactive, Case B).
  2. ALU address calculation failure (ALU produces wrong address pointing to zero/unmapped memory).
  3. Data Memory read failure (memory read port disabled or stuck at 0).
  4. `WBsel` multiplexer stuck at 0 (selecting ALU address instead of memory data, or grounded bus).
  5. Register file write decoder failure (writing to x0 or wrong register index instead of x5).  
  By observing internal settled wire values before the clock edge—verifying that `ALUResult = 0x1000`, `MemReadData = 7`, and `WBData = 7` are all fully settled and valid—we definitively confirm that the data was correctly read and routed to the register input, proving that the failure is uniquely due to the write enable (`RegWrite = 0`).

*Attachment: Fault A Annotated Trace Diagram is attached below and embedded in the report document.*  
- **PC:** `0x00000008` (Course Model) / `0x0000001C` (Ripes)  
- **Timing:** Shows candidate wires settled **BEFORE** the edge (`ALUResult = 0x100C`, `ALU_B = 0x0C`) and state committed **AFTER** the rising clock edge (`M[0x100C] = 12`, target `M[0x1004] = 0`).

---

## Task E: Timing Calculations

### Timing Budget Comparison Table

| Quantity | Before Optimization | After ALU Improvement |
|---|---|---|
| Load path (ps) | 800 ps | 750 ps |
| Add path (ps) | 550 ps | 500 ps |
| Branch path (ps) | 760 ps | 760 ps |
| **Fixed clock period (ps)** | **800 ps** | **760 ps** *(Branch becomes critical!)* |
| **Clock frequency (GHz)** | **1.250 GHz** | **1.316 GHz** *(1.3158 GHz)* |
| **Time for 100 instructions (ns)** | **80.0 ns** | **76.0 ns** |

### Analysis Questions

- **Load delay calculation:**  
  - *Before:* Launch (30 ps) + Instruction access/decode (200 ps) + Register file access (100 ps) + Main ALU (150 ps) + Data memory read (250 ps) + Write-back selection (30 ps) + Setup/margin (40 ps) = **800 ps**.  
  - *After (ALU reduced from 150 ps to 100 ps):* 30 + 200 + 100 + 100 + 250 + 30 + 40 = **750 ps**.
- **Speedup calculation:**  
  $$\text{Speedup} = \frac{\text{Execution Time}_{\text{before}}}{\text{Execution Time}_{\text{after}}} = \frac{T_{\text{clk, before}}}{T_{\text{clk, after}}} = \frac{800\text{ ps}}{760\text{ ps}} \approx 1.0526 \quad (5.26\%\text{ improvement, or } 1.05\times)$$
- **Why the critical path changes:**  
  In a single-cycle CPU, the clock cycle period is determined by the slowest path among all supported instructions: $T_{\text{clk}} = \max(T_{\text{load}}, T_{\text{add}}, T_{\text{branch}})$. Initially, the load path is the critical path at 800 ps (greater than branch at 760 ps). Reducing the main ALU delay by 50 ps speeds up the load path to 750 ps. However, the dedicated branch path (760 ps) uses separate comparator and adder circuits and does not use the main ALU; thus its delay remains 760 ps. Because 760 ps > 750 ps, the branch path becomes the new critical path. In accordance with Amdahl's Law, overall performance is now bottlenecked by the unimproved branch hardware, limiting the clock period reduction to 40 ps (from 800 ps to 760 ps) rather than the full 50 ps saved in the ALU.
- **Mux output arrival with select at 410 ps:**  
  Data inputs ready at 260 ps and 320 ps; Mux delay = 30 ps.  
  $$\text{Arrival} = \max(260, 320, 410) + 30\text{ ps} = 410\text{ ps} + 30\text{ ps} = \mathbf{440\text{ ps}}$$  
  *(The select signal is the critical arrival).*
- **Mux output arrival with select at 300 ps:**  
  $$\text{Arrival} = \max(260, 320, 300) + 30\text{ ps} = 320\text{ ps} + 30\text{ ps} = \mathbf{350\text{ ps}}$$  
  *(Data Input 1 at 320 ps is now the critical arrival).*
- **Why arrivals are compared rather than added:**  
  The multiplexer data inputs and select control line propagate through physically separate, concurrent hardware circuits. The multiplexer's output cannot settle to a valid, glitch-free value until the latest of all required input signals has arrived and the internal multiplexer transmission delay has elapsed. Because these signals travel concurrently in parallel time rather than sequentially in series, their arrival times must be compared (taking the maximum) rather than added.

---

## Exit Ticket

1. **Distinguish a load's address and write-back value:**  
   The address is the memory location generated by the ALU adding base register `rs1` (`x10 = 0x1000`) and immediate offset 0 (`0x1000 + 0 = 0x1000`), routed to the Data Memory address port. The write-back value is the data word retrieved from Data Memory at that address (7 = `0x00000007`), routed via `WBsel=1` to the register file `WriteData` port to be committed into destination register `rd` (`x5`).
2. **Explain the effect of RegWrite=0:**  
   `RegWrite=0` disables the write-enable control line of the integer register file. At the rising clock edge, no register entry (x0 through x31) is updated, ensuring that instructions which do not produce a register result (such as `sw` and `beq`) preserve all architectural register contents unchanged.
3. **State the conditions for PCSel=1:**  
   In this lecture datapath, `PCSel` is evaluated by the combinational expression `PCSel = Branch AND Eq`. Therefore, two conditions must simultaneously hold: (1) `Branch = 1` (the instruction opcode is a branch instruction, `0x63` for `beq`), and (2) `Eq = 1` (the dedicated equality comparator evaluates that register operand 1 equals register operand 2, `Read1 == Read2`).
4. **Explain why CPI=1 does not guarantee a fast processor:**  
   According to the Iron Law of Processor Performance ($\text{CPU Time} = \text{Instruction Count} \times \text{CPI} \times \text{Clock Period}$), execution time depends on both CPI and clock period. In a single-cycle processor, CPI = 1, but the clock period must accommodate the single slowest instruction path in the machine (the critical path, traversing instruction memory, register file, ALU, data memory, and writeback). This results in a low clock frequency. A pipelined processor with a slightly higher CPI (e.g. 1.1–1.3 due to pipeline hazards) can operate at a vastly higher clock frequency (e.g. 5x faster), finishing programs in substantially less total execution time.

---

## Optional Loop

- **Visited PCs:** `0x00000020` (add) $\to$ `0x00000024` (beq, not taken) $\to$ `0x00000028` (beq, taken backward) $\to$ `0x00000020` (add) $\to$ `0x00000024` (beq, taken exit) $\to$ `0x0000002C` (stopped at observation boundary).
- **Value of x6 after each instruction:**  
  - Cycle 1 (0x20): x6 = 1  
  - Cycle 2 (0x24): x6 = 1  
  - Cycle 3 (0x28): x6 = 1  
  - Cycle 4 (0x20): x6 = 2  
  - Cycle 5 (0x24): x6 = 2  
- **Total completed instructions:** 5 completed instructions; final PC = `0x0000002C`; final x6 = 2.
- **Unchanged memory:** Data memory remains 100% unchanged throughout (zero store operations executed).
- **Why the backward branch needs no register or memory write:**  
  The backward branch `beq x0, x0, -8` is an unconditional jump (`x0 == x0` evaluates always true). It computes target `PC + (-8) = 0x28 - 8 = 0x20` and sets `PCSel = 1`. Because `RegWrite = 0` and `MemWrite = 0`, no register or data memory state is altered; only the PC register is updated.
