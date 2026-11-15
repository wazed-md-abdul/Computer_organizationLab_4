#!/usr/bin/env python3
"""Lecture 4 single-cycle teaching model: add, lw, sw, beq only.

This is a functional teaching model, not an RTL simulator or timing simulator.
Each step first evaluates wires from old state, then commits at one rising edge.
No external packages are required. Run: python lab4_cpu.py --help
"""
import argparse
import copy
import csv
import json
import re
from pathlib import Path

MASK = 0xFFFFFFFF
CONTROL_NAMES = ("RegWrite", "ALUSrc", "MemWrite", "WBsel", "Branch", "PCSel")


def integer(value):
    return int(value, 0) if isinstance(value, str) else int(value)


def u32(value):
    return value & MASK


def signed(value, bits=32):
    return (value & ((1 << bits) - 1)) - ((1 << bits) if value & (1 << (bits - 1)) else 0)


def hx(value):
    return "unused" if value is None else f"0x{u32(value):08X}"


def reg_index(token):
    if not re.fullmatch(r"x(?:[0-9]|[12][0-9]|3[01])", token):
        raise ValueError(f"Use register names x0 through x31, not {token!r}")
    return int(token[1:])


def assemble(text):
    """Strict assembler for the four instruction forms used in this lab.

    Branch immediates are signed byte offsets from the branch PC, not labels.
    No pseudoinstructions, directives, or setup instructions are supported.
    """
    fields = text.replace(",", " ").replace("(", " ").replace(")", " ").split()
    if not fields:
        raise ValueError("Empty instruction")
    op = fields[0].lower()
    if len(fields) != 4:
        raise ValueError(f"Bad instruction form: {text!r}")
    if op == "add":
        rd, rs1, rs2 = map(reg_index, fields[1:])
        return rs2 << 20 | rs1 << 15 | rd << 7 | 0x33
    if op in ("lw", "sw"):
        r, imm, rs1 = reg_index(fields[1]), integer(fields[2]), reg_index(fields[3])
        if not -2048 <= imm <= 2047:
            raise ValueError("Load/store immediate must fit signed 12 bits")
        imm &= 0xFFF
        if op == "lw":
            return imm << 20 | rs1 << 15 | 2 << 12 | r << 7 | 0x03
        return (imm >> 5) << 25 | r << 20 | rs1 << 15 | 2 << 12 | (imm & 31) << 7 | 0x23
    if op == "beq":
        rs1, rs2, imm = reg_index(fields[1]), reg_index(fields[2]), integer(fields[3])
        if not -4096 <= imm <= 4094 or imm % 2:
            raise ValueError("Branch immediate must be even and fit signed 13 bits")
        imm &= 0x1FFF
        return ((imm >> 12) & 1) << 31 | ((imm >> 5) & 63) << 25 | rs2 << 20 | rs1 << 15 | ((imm >> 1) & 15) << 8 | ((imm >> 11) & 1) << 7 | 0x63
    raise ValueError(f"Unsupported instruction: {op}; use add, lw, sw, or beq")


def decode(word):
    """Decode real RV32I instruction bits, checking opcode/funct fields."""
    if not isinstance(word, int) or not 0 <= word <= MASK:
        raise ValueError("Instruction word must be an unsigned 32-bit integer")
    opcode, funct3, funct7 = word & 127, (word >> 12) & 7, (word >> 25) & 127
    rd, rs1, rs2 = (word >> 7) & 31, (word >> 15) & 31, (word >> 20) & 31
    if opcode == 0x33 and funct3 == 0 and funct7 == 0:
        op, imm, used = "add", 0, (rd, rs1, rs2)
    elif opcode == 0x03 and funct3 == 2:
        op, imm, used = "lw", signed(word >> 20, 12), (rd, rs1, None)
    elif opcode == 0x23 and funct3 == 2:
        op, imm, used = "sw", signed(((word >> 25) << 5) | rd, 12), (None, rs1, rs2)
    elif opcode == 0x63 and funct3 == 0:
        bimm = ((word >> 31) & 1) << 12 | ((word >> 7) & 1) << 11 | ((word >> 25) & 63) << 5 | ((word >> 8) & 15) << 1
        op, imm, used = "beq", signed(bimm, 13), (None, rs1, rs2)
    else:
        raise ValueError(f"Unsupported encoding {hx(word)}: opcode/funct fields do not match the lab subset")
    return {"op": op, "imm": imm, "rd_bits": rd, "rs1_bits": rs1, "rs2_bits": rs2,
            "rd": used[0], "rs1": used[1], "rs2": used[2],
            "opcode": opcode, "funct3": funct3, "funct7": funct7}


def controls(op):
    # Choose zero for don't-care selectors. The branch has dedicated hardware.
    return {"RegWrite": int(op in ("add", "lw")), "ALUSrc": int(op in ("lw", "sw")),
            "MemWrite": int(op == "sw"), "WBsel": int(op == "lw"), "Branch": int(op == "beq")}


class CPU:
    def __init__(self, scenario):
        self.pc = u32(integer(scenario.get("pc", 0)))
        self.regs = [0] * 32
        for name, value in scenario.get("registers", {}).items():
            idx = reg_index(name)
            if idx == 0 and integer(value) != 0:
                raise ValueError("x0 must be initialized to zero")
            self.regs[idx] = u32(integer(value))
        self.memory = {u32(integer(a)): u32(integer(v)) for a, v in scenario.get("memory", {}).items()}
        if self.pc % 4 or any(a % 4 for a in self.memory):
            raise ValueError("This lab uses 4-byte-aligned instruction and word addresses")
        self.program = {}
        self.source = {}
        for row in scenario["program"]:
            addr = u32(integer(row["pc"]))
            if addr % 4 or addr in self.program:
                raise ValueError("Instruction addresses must be unique and 4-byte aligned")
            word = integer(row["word"]) if "word" in row else assemble(row["asm"])
            decode(word)
            self.program[addr] = word
            self.source[addr] = row.get("asm", hx(word))
        self.edge_count = 0

    def state(self):
        return {"pc": self.pc, "registers": list(self.regs), "memory": dict(self.memory)}

    def evaluate(self, faults=None):
        """Evaluate candidate values without mutating any architectural state."""
        if self.pc not in self.program:
            raise ValueError(f"No instruction supplied at {hx(self.pc)}")
        faults = faults or {}
        if any(k not in CONTROL_NAMES or v not in (0, 1) for k, v in faults.items()):
            raise ValueError("Faults require a known control name and value 0 or 1")
        word = self.program[self.pc]
        d = decode(word)
        nominal = controls(d["op"])
        c = dict(nominal)
        c.update({k: v for k, v in faults.items() if k != "PCSel"})
        # Real shared wiring reads the raw five-bit selectors. For lw, rs2_bits
        # are immediate bits, NOT a second architectural operand.
        read1, read2 = self.regs[d["rs1_bits"]], self.regs[d["rs2_bits"]]
        b = u32(d["imm"]) if c["ALUSrc"] else read2
        alu = u32(read1 + b)
        eq = int(read1 == read2)
        target, sequential = u32(self.pc + d["imm"]), u32(self.pc + 4)
        pcsel = faults.get("PCSel", int(c["Branch"] and eq))
        c["PCSel"] = pcsel
        nextpc = target if pcsel else sequential
        if nextpc % 4:
            raise ValueError("Selected next PC is misaligned for this RV32I-only lab")
        active_memory = d["op"] == "lw" or bool(c["MemWrite"]) or (bool(c["RegWrite"]) and bool(c["WBsel"]))
        if active_memory and (alu % 4 or alu not in self.memory):
            raise ValueError(f"Active word access at {hx(alu)} is misaligned or outside initialized lab memory")
        memdata = self.memory.get(alu) if alu % 4 == 0 else None
        wbdata = memdata if c["WBsel"] else alu
        before = self.state()
        after = copy.deepcopy(before)
        after["pc"] = nextpc
        # Raw rd bits drive the shared write-address port, even for formats
        # without rd. Correct RegWrite=0 prevents accidental writes there.
        reg_update = None
        if c["RegWrite"] and d["rd_bits"] != 0:
            if wbdata is None:
                raise ValueError("Enabled register write has no defined write-back data")
            idx = d["rd_bits"]
            reg_update = {"register": f"x{idx}", "before": self.regs[idx], "after": wbdata}
            after["registers"][idx] = wbdata
        mem_update = None
        if c["MemWrite"]:
            mem_update = {"address": alu, "before": self.memory[alu], "after": read2}
            after["memory"][alu] = read2
        after["registers"][0] = 0
        return {"edge": self.edge_count + 1, "instruction": self.source[self.pc], "word": word,
                "decoded": d, "nominal_controls": nominal, "controls": c, "faults": dict(faults),
                "signals": {"Read1": read1, "Read2": read2, "Imm": d["imm"], "ALU_A": read1,
                            "ALU_B": b, "ALUResult": alu, "MemReadData": memdata,
                            "StoreData": read2, "WBData": wbdata, "Eq": eq,
                            "PCplus4": sequential, "BranchTarget": target, "NextPC": nextpc},
                "before": before, "after": after, "register_update": reg_update, "memory_update": mem_update}

    def commit(self, trace):
        if self.state() != trace["before"] or trace["edge"] != self.edge_count + 1:
            raise ValueError("Stale trace: evaluate again from the current architectural state")
        self.pc = trace["after"]["pc"]
        self.regs = list(trace["after"]["registers"])
        self.memory = dict(trace["after"]["memory"])
        self.edge_count += 1

    def step(self, faults=None):
        trace = self.evaluate(faults)
        self.commit(trace)
        return trace


def format_trace(t):
    s, d, c = t["signals"], t["decoded"], t["controls"]
    lines = [f"Cycle {t['edge']} | PC {hx(t['before']['pc'])} | {t['instruction']} | word {hx(t['word'])}",
             "  BEFORE EDGE: state has NOT changed; all listed wires are candidate values.",
             "  Controls: " + "  ".join(f"{key}={c[key]}" for key in CONTROL_NAMES),
             f"  ALU_A={hx(s['ALU_A'])}  ALU_B={hx(s['ALU_B'])}  ALUResult={hx(s['ALUResult'])}"]
    if d["op"] in ("lw", "sw"):
        lines.append(f"  Immediate={s['Imm']}  EffectiveAddress={hx(s['ALUResult'])}  StoreData={hx(s['StoreData'])}")
    if d["op"] == "lw" or c["WBsel"]:
        lines.append(f"  MemReadData={hx(s['MemReadData'])}  WBData={hx(s['WBData'])}")
    elif d["op"] == "add":
        lines.append(f"  WBData={hx(s['WBData'])}")
    if d["op"] == "beq":
        lines.append(f"  Eq={s['Eq']}  BranchTarget={hx(s['BranchTarget'])}  (dedicated comparator and target adder)")
        lines.append("  Main ALU result is unused by this branch; ALUSrc is a don't-care.")
    lines.append(f"  PCplus4={hx(s['PCplus4'])}  NextPC={hx(s['NextPC'])}")
    if d["rd"] is not None:
        lines.append(f"  Old x{d['rd']} remains {hx(t['before']['registers'][d['rd']])} before the edge.")
    lines.append("  AT RISING EDGE:")
    update = t["register_update"]
    lines.append(f"    {update['register']}: {hx(update['before'])} -> {hx(update['after'])}" if update else "    No writable integer register changes.")
    update = t["memory_update"]
    lines.append(f"    M[{hx(update['address'])}]: {hx(update['before'])} -> {hx(update['after'])}" if update else "    Data memory unchanged.")
    lines.append(f"    PC: {hx(t['before']['pc'])} -> {hx(t['after']['pc'])}")
    return "\n".join(lines)


CSV_FIELDS = ["cycle", "PC_before", "instruction", "machine_word", *CONTROL_NAMES,
              "ALU_A", "ALU_B", "ALUResult", "StoreData", "MemReadData", "WBData", "Eq",
              "BranchTarget", "PC_after", "x5_after", "x6_after", "M_0x1004_after"]


def csv_rows(traces):
    for t in traces:
        yield {"cycle": t["edge"], "PC_before": hx(t["before"]["pc"]), "instruction": t["instruction"],
               "machine_word": hx(t["word"]), **t["controls"],
               **{k: hx(t["signals"][k]) for k in ("ALU_A", "ALU_B", "ALUResult", "StoreData", "MemReadData", "WBData", "BranchTarget")},
               "Eq": t["signals"]["Eq"], "PC_after": hx(t["after"]["pc"]),
               "x5_after": hx(t["after"]["registers"][5]), "x6_after": hx(t["after"]["registers"][6]),
               "M_0x1004_after": hx(t["after"]["memory"].get(0x1004))}


def parse_fault(value):
    try:
        key, bit = value.split("=")
        bit = int(bit)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Use a fault such as ALUSrc=0") from exc
    if key not in CONTROL_NAMES or bit not in (0, 1):
        raise argparse.ArgumentTypeError("Choose a named control and value 0 or 1")
    return key, bit


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", default="sequence", help="Built-in scenario name or a JSON file path")
    parser.add_argument("--fault", action="append", type=parse_fault, default=[], help="Force a control in every executed cycle, e.g. WBsel=0; repeat for several controls")
    parser.add_argument("--steps", type=int, help="Maximum cycles (default comes from the scenario)")
    parser.add_argument("--csv", type=Path, help="Write detailed trace rows to this CSV")
    parser.add_argument("--json", type=Path, help="Write complete pre-edge and post-edge traces to this JSON")
    args = parser.parse_args(argv)
    candidate = Path(args.scenario)
    path = candidate if candidate.is_file() else Path(__file__).parent / "scenarios" / (args.scenario + ".json")
    try:
        scenario = json.loads(path.read_text(encoding="utf-8"))
        cpu = CPU(scenario)
        steps = args.steps if args.steps is not None else scenario.get("steps", len(cpu.program))
        if steps < 1:
            raise ValueError("--steps must be positive")
        faults = dict(scenario.get("faults", {}))
        faults.update(dict(args.fault))
        print(scenario["title"])
        print("Lecture 4 teaching model | WBsel 0=ALU, 1=memory | each cycle ends at one rising edge")
        print("Fresh state loaded for this run. Memory is a sparse map of initialized 32-bit words.")
        if faults:
            print("Forced controls: " + ", ".join(f"{k}={v}" for k, v in faults.items()))
        traces = []
        for _ in range(steps):
            if cpu.pc not in cpu.program:
                print(f"Stopped at {hx(cpu.pc)}: no next instruction supplied; this is the observation boundary, not a halt instruction.")
                break
            trace = cpu.step(faults)
            traces.append(trace)
            print("\n" + format_trace(trace))
        print(f"\nObserved {len(traces)} completed instruction(s). Final PC={hx(cpu.pc)}; x5={hx(cpu.regs[5])}; x6={hx(cpu.regs[6])}; M[0x00001004]={hx(cpu.memory.get(0x1004))}.")
        print("Unused internal outputs do not imply architectural writes; inspect the write enables.")
        if args.csv:
            with args.csv.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
                writer.writeheader()
                writer.writerows(csv_rows(traces))
            print(f"CSV saved: {args.csv}")
        if args.json:
            args.json.write_text(json.dumps(traces, indent=2) + "\n", encoding="utf-8")
            print(f"JSON saved: {args.json}")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
