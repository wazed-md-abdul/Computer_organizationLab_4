# Lab 4 CPU Datapath and Control

Use Python 3 to observe the exact single-cycle teaching model used in Lecture 4.
This functional model exposes data values, control choices, and the state committed
at a rising edge. It does not model propagation delay, analog waveforms, caches,
pipeline stages, operating systems, or the full RV32I instruction set.

## Start

Extract the student package. Open a terminal in the folder containing
`lab4_cpu.py` and the `scenarios` folder. No additional packages are needed.
On Windows use `python`; on macOS/Linux use `python3` if `python` is unavailable.

```text
python lab4_cpu.py --scenario add
python lab4_cpu.py --scenario sequence --csv sequence_trace.csv
python lab4_cpu.py --scenario not_taken --csv not_taken_trace.csv
python lab4_cpu.py --scenario loop --csv loop_trace.csv
```

The `add` scenario starts with x6=99 so that the difference between a candidate
wire value and a stored register value is visible. `sequence` and `taken` both
run load, add, store, and a taken branch. `not_taken` changes only x11 from 12 to 9.
The loop ends when the PC reaches an address with no supplied instruction.
This is an observation boundary; it is not a RISC-V halt instruction.

## Other scenarios

| Name | Purpose |
|---|---|
| `load` | Independent clean load |
| `store` | Independent clean store |
| `branch` | Independent equal branch |
| `negative_load` | Load with an immediate of -4 |
| `store_checkpoint` | Store with an immediate of -4 |
| `fault_a` | Store experiment A |
| `fault_b` | Load experiment B |
| `fault_c` | Branch experiment C |

Each run reloads fresh state. The named fault scenarios apply their fault
automatically. Diagnose each symptom in the student handout before running it.
After recording your diagnosis, inspect the reported control values and test your
proposed repair with `--fault NAME=BIT`.

```text
python lab4_cpu.py --scenario fault_a
python lab4_cpu.py --scenario load --fault WBsel=0
python lab4_cpu.py --scenario store --fault WBsel=0
python lab4_cpu.py --scenario store --fault WBsel=1
```

For a clean scenario, `--fault NAME=BIT` forces that control during every cycle
you execute. Use independent one-instruction scenarios for controlled comparisons.
Repeat `--fault` only if a task asks for more than one forced control.

## Ripes observation files

The four `.s` files are for Ripes. They include setup instructions outside the
measured interval; do not pass them to this four-instruction Python model.
Choose a 32-bit single-cycle processor and disable the compressed C extension.
Use the actual instruction and data addresses shown by your simulator.

| File | Measured interval |
|---|---|
| `01_load_add_store.s` | Three instructions from trace_start to before lab_done |
| `02_branch.s` | Four instructions from trace_start through the first beq |
| `03_negative_store.s` | One sw instruction from trace_start to before lab_done |
| `04_loop_optional.s` | Five executed instructions from trace_start to before lab_done |

For `02_branch.s`, change the immediate in the `addi x11,x0,12` instruction
under the `INPUT_X11` label to 9 for the second run. The label is an assembly
label, not a directive or a register. Reset after editing. Stop immediately after
the first branch; its target and fall-through addresses are both outside the
measured interval. For the other files, set a breakpoint at `lab_done` and stop
before executing its marker instruction. The marker does not halt a processor.

The Ripes implementation may use different internal signal names, mux encodings,
or circuit arrangements. Compare architectural results there. Use the Python
model for the exact control convention of this lecture.

## Capture results

```text
python lab4_cpu.py --scenario sequence --steps 1
python lab4_cpu.py --scenario sequence --csv trace.csv --json trace.json
python lab4_cpu.py --help
```

`--steps N` limits the number of completed cycles. CSV outputs candidate values
and selected post-edge state. JSON outputs complete before/after snapshots.
Supply output filenames in an existing writable folder. The CSV's hexadecimal
values are 32-bit bit patterns; for example 0xFFFFFFFF represents -1 if interpreted
as a signed integer. An `unused` memory output does not imply an error if no enabled
destination consumes it.

## Edit a scenario

Copy a file from `scenarios`, change the initial registers, memory, or program,
and pass the copied file path to `--scenario`.

```text
python lab4_cpu.py --scenario my_case.json
```

Use x0 through x31 register names. All instruction addresses and active word
accesses must be aligned to four bytes. Memory contains only explicitly initialized
32-bit words. Initialize every memory word your experiment accesses, including a
wrong destination you deliberately test. The program supports only:

```text
add x6, x5, x2
lw x5, 0(x10)
sw x6, 4(x10)
beq x6, x11, 12
```

The branch immediate is a signed byte offset from the current branch PC.
The model assembles these forms into real instruction words and decodes the words
by opcode, funct fields, register fields, and immediate bits. A JSON program row
can instead supply a `word` value, such as `"0xFFC52283"` for `lw x5,-4(x10)`.
Labels, directives, register aliases, pseudoinstructions, and setup instructions
such as `addi` or `la` are not part of this four-instruction model.

## Control conventions

- ALUSrc=0 selects Read2; ALUSrc=1 selects the sign-extended immediate.
- WBsel=0 selects the ALU result; WBsel=1 selects data-memory output.
- RegWrite and MemWrite enable state updates at the ending rising edge.
- A dedicated comparator supplies Eq, and a dedicated adder supplies PC+immediate.
- Normally PCSel=Branch AND Eq. PCSel=0 chooses PC+4; PCSel=1 chooses the target.
- For `sw`, WBsel is a don't-care. For `beq`, ALUSrc and WBsel are don't-cares.
  The model chooses zero by default so outputs are repeatable.
- Instruction and data memory are separate. Register and data-memory reads are
  modeled as combinational. All relevant state writes commit together at the edge.
- x0 stays zero even when its write-enable path is active.

The main ALU always adds in this subset. The branch does not use the main ALU
result. Raw field wires can contain bits with no architectural operand meaning;
for example, lw bits 24:20 are immediate bits, not an rs2 operand. An unused value
on a wire does not authorize a register or memory update.

Use `control_table_blank.csv` and `trace_table_blank.csv` for your predictions.
Complete them before inspecting the simulator output and explain any correction.
