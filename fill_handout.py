import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def set_cell_background(cell, hex_color):
    tcPr = cell._element.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def style_cell(cell, text, bold=False, italic=False, color_rgb=(30, 41, 59), font_size=9.5, align=WD_ALIGN_PARAGRAPH.LEFT, bg_hex=None):
    cell.text = ''
    if bg_hex:
        set_cell_background(cell, bg_hex)
    set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    run = p.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.name = 'Calibri'
    run.font.size = Pt(font_size)
    run.font.color.rgb = RGBColor(*color_rgb)

def format_paragraph(p, text, font_size=10.0, bold=False, italic=False, color_rgb=(30, 41, 59), space_after=5, space_before=2):
    p.text = ''
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(font_size)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = RGBColor(*color_rgb)
    return run

def process_handout(handout_path, output_path):
    doc = docx.Document(handout_path)
    
    # P3: Student info
    format_paragraph(doc.paragraphs[3], 'Name: Student Report                    Student ID: 2026-CO-LAB4                    Date: November 15, 2026', font_size=10.5, bold=True, color_rgb=(15, 23, 42))
    
    # Table 2: After instruction | PC | x5 | x6 | M[B] | M[B+4]
    t2 = doc.tables[2]
    headers_t2 = ['After instruction', 'PC', 'x5', 'x6', 'M[B]', 'M[B+4]']
    for col_idx, h in enumerate(headers_t2):
        style_cell(t2.rows[0].cells[col_idx], h, bold=True, color_rgb=(255, 255, 255), bg_hex='1E293B', font_size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
    t2_data = [
        ('lw x5, 0(x10)', '0x04 (Ripes: 0x18)', '7 (0x07)', '0 (0x00)', '7 (0x07)', '0 (0x00)'),
        ('add x6, x5, x2', '0x08 (Ripes: 0x1C)', '7 (0x07)', '12 (0x0C)', '7 (0x07)', '0 (0x00)'),
        ('sw x6, 4(x10)', '0x0C (Ripes: 0x20)', '7 (0x07)', '12 (0x0C)', '7 (0x07)', '12 (0x0C)')
    ]
    for r_idx, row in enumerate(t2_data, start=1):
        bg = 'F8FAFC' if r_idx % 2 == 1 else 'FFFFFF'
        style_cell(t2.rows[r_idx].cells[0], row[0], bold=True, bg_hex=bg, color_rgb=(15, 23, 42))
        for c_idx in range(1, 6):
            style_cell(t2.rows[r_idx].cells[c_idx], row[c_idx], bg_hex=bg, align=WD_ALIGN_PARAGRAPH.CENTER)
            
    # Table 3: Quantity | Prediction | Observation
    t3 = doc.tables[3]
    headers_t3 = ['Quantity', 'Prediction', 'Observation']
    for col_idx, h in enumerate(headers_t3):
        style_cell(t3.rows[0].cells[col_idx], h, bold=True, color_rgb=(255, 255, 255), bg_hex='1E293B', font_size=10)
    t3_data = [
        ('Load ALU result', '0x00001000 (effective address B)', '0x00001000 (Ripes: 0x10000000)'),
        ('Load memory output and write-back input', '0x00000007 (data word 7)', '0x00000007 (MemReadData = WBData = 7)'),
        ('x5 before the load completion edge', '0x00000000 (unmodified pre-edge state)', '0x00000000 (wire settled, register unlatched)'),
        ('Store effective address', '0x00001004 (address B + 4)', '0x00001004 (Ripes: 0x10000004)'),
        ('Store write-data input', '0x0000000C (value of x6 = 12)', '0x0000000C (Read2 bus carries 12 directly)'),
        ('Registers changed by the store', 'None (RegWrite = 0)', 'None (All integer registers preserved unchanged)')
    ]
    for r_idx, row in enumerate(t3_data, start=1):
        bg = 'F8FAFC' if r_idx % 2 == 1 else 'FFFFFF'
        style_cell(t3.rows[r_idx].cells[0], row[0], bold=True, bg_hex=bg, color_rgb=(15, 23, 42))
        style_cell(t3.rows[r_idx].cells[1], row[1], bg_hex=bg)
        style_cell(t3.rows[r_idx].cells[2], row[2], bg_hex=bg)
        
    # Paragraphs A1, A2, A3
    format_paragraph(doc.paragraphs[36], 'A1 Answer: The processor employs synchronous, edge-triggered state storage. The main ALU computes effective address 0x1000, and Data Memory combinational read outputs 7, placing candidate value 7 on the MemReadData and WBData wires. However, register file entry x5 updates ONLY on the rising clock edge when RegWrite=1 is sampled. Throughout the clock cycle before the edge, wire values are transient candidates and x5 retains its initial stored value 0x00000000.', font_size=10.0)
    format_paragraph(doc.paragraphs[38], 'A2 Answer: "Where to write" (effective address): Generated by the ALU adding base register x10 (0x1000) and sign-extended immediate offset 4 (ALUSrc=1), producing address 0x1004 sent to the Data Memory address port.\n"What to write" (store data): Read directly from register file port 2 (rs2 = x6 = 12 = 0x0000000C) along a dedicated bus to the Data Memory WriteData input, completely bypassing the ALU. RegWrite=0 ensures all architectural registers remain strictly preserved.', font_size=10.0)
    format_paragraph(doc.paragraphs[40], 'A3 Answer: In this single-cycle processor model, each instruction completes its entire execution—fetch, decode, register read, ALU computation, memory access, and writeback—within a single clock cycle. The updated value of x5 commits to the register file at the rising clock edge ending Cycle 1 (the lw). When Cycle 2 (the add) begins immediately after this edge, the register file read port combinationally reads the newly committed value (7) in x5. With no overlapping pipeline stages, data dependencies are resolved sequentially without stalls, bubbles, or forwarding logic.', font_size=10.0)
    
    # Table 4: Control table
    t4 = doc.tables[4]
    headers_t4 = ['Instruction', 'RegWrite', 'ALUSrc', 'MemWrite', 'WBsel', 'Branch', 'PCSel']
    for col_idx, h in enumerate(headers_t4):
        style_cell(t4.rows[0].cells[col_idx], h, bold=True, color_rgb=(255, 255, 255), bg_hex='1E293B', font_size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
    t4_data = [
        ('add', '1', '0', '0', '0', '0', '0'),
        ('lw', '1', '1', '0', '1', '0', '0'),
        ('sw', '0', '1', '1', 'X (0)', '0', '0'),
        ('beq equal', '0', 'X (0)', '0', 'X (0)', '1', '1'),
        ('beq unequal', '0', 'X (0)', '0', 'X (0)', '1', '0')
    ]
    for r_idx, row in enumerate(t4_data, start=1):
        bg = 'F8FAFC' if r_idx % 2 == 1 else 'FFFFFF'
        style_cell(t4.rows[r_idx].cells[0], row[0], bold=True, bg_hex=bg, color_rgb=(15, 23, 42))
        for c_idx in range(1, 7):
            style_cell(t4.rows[r_idx].cells[c_idx], row[c_idx], bg_hex=bg, align=WD_ALIGN_PARAGRAPH.CENTER)
            
    # Table 5: Decode 0x00652223
    t5 = doc.tables[5]
    headers_t5 = ['Field', 'Bit positions', 'Your value']
    for col_idx, h in enumerate(headers_t5):
        style_cell(t5.rows[0].cells[col_idx], h, bold=True, color_rgb=(255, 255, 255), bg_hex='1E293B', font_size=10)
    t5_data = [
        ('opcode', '6:0', '0100011 (0x23, STORE)'),
        ('funct3', '14:12', '010 (0x2, sw / 32-bit word store)'),
        ('rs1', '19:15', '01010 (10, x10 base address)'),
        ('rs2', '24:20', '00110 (6, x6 store data)'),
        ('imm[11:5]', '31:25', '0000000 (0)'),
        ('imm[4:0]', '11:7', '00100 (4)')
    ]
    for r_idx, row in enumerate(t5_data, start=1):
        bg = 'F8FAFC' if r_idx % 2 == 1 else 'FFFFFF'
        style_cell(t5.rows[r_idx].cells[0], row[0], bold=True, bg_hex=bg, color_rgb=(15, 23, 42))
        style_cell(t5.rows[r_idx].cells[1], row[1], bg_hex=bg)
        style_cell(t5.rows[r_idx].cells[2], row[2], bg_hex=bg)
        
    # B1, B2
    format_paragraph(doc.paragraphs[54], 'B1 Answer: In RISC-V, source register specifiers rs1 (bits 19:15) and rs2 (bits 24:20) are fixed across all instruction formats to keep register read decoding simple and uniform. Store instructions write to memory rather than registers and therefore have no destination register (rd). To utilize all 32 bits without extra decode logic, the 5 bits at positions 11:7 (which hold rd in R-type and I-type instructions) are repurposed in S-format to store the lower immediate bits imm[4:0].', font_size=10.0)
    format_paragraph(doc.paragraphs[56], 'B2 Answer: Both add and sub are R-type instructions sharing identical opcode 0110011 (0x33) and identical funct3 = 000. They are uniquely distinguished by the 7-bit funct7 field at bits 31:25: add has funct7 = 0000000 (0x00), while sub has funct7 = 0100000 (0x20, with bit 30 set high).', font_size=10.0)
    
    # Table 6: Branch outcomes
    t6 = doc.tables[6]
    headers_t6 = ['x11', 'Eq', 'PC+4', 'PC+12', 'PCSel', 'PC after edge']
    for col_idx, h in enumerate(headers_t6):
        style_cell(t6.rows[0].cells[col_idx], h, bold=True, color_rgb=(255, 255, 255), bg_hex='1E293B', font_size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
    t6_data = [
        ('12', '1', '0x00000010 (Ripes: 0x28)', '0x00000018 (Ripes: 0x30)', '1', '0x00000018 (Ripes: 0x30)'),
        ('9', '0', '0x00000010 (Ripes: 0x28)', '0x00000018 (Ripes: 0x30)', '0', '0x00000010 (Ripes: 0x28)')
    ]
    for r_idx, row in enumerate(t6_data, start=1):
        bg = 'F8FAFC' if r_idx % 2 == 1 else 'FFFFFF'
        style_cell(t6.rows[r_idx].cells[0], row[0], bold=True, bg_hex=bg, color_rgb=(15, 23, 42), align=WD_ALIGN_PARAGRAPH.CENTER)
        for c_idx in range(1, 6):
            style_cell(t6.rows[r_idx].cells[c_idx], row[c_idx], bg_hex=bg, align=WD_ALIGN_PARAGRAPH.CENTER)
            
    # C1a, C1b
    format_paragraph(doc.paragraphs[66], 'C1a Answer: beq writes NEITHER an integer register nor a memory word (RegWrite = 0, MemWrite = 0). All register file contents (x0–x31) and data memory words remain completely unchanged. The ONLY architectural state component that changes at the clock edge is the Program Counter (PC), which updates to the branch target address if taken, or to PC+4 if not taken.', font_size=10.0)
    format_paragraph(doc.paragraphs[68], 'C1b Answer: In RISC-V, branch immediate offsets are defined relative to the address of the branch instruction itself (PC), not PC+4. The branch target adder computes Target = PC + imm. If the offset (+12 bytes) were added to PC+4, the target would be shifted forward by 4 extra bytes (PC+16), corrupting control flow and jumping to the wrong instruction.', font_size=10.0)
    
    # Table 7: Negative store observation table
    t7 = doc.tables[7]
    headers_t7 = ['Observation', 'Prediction', 'Observed']
    for col_idx, h in enumerate(headers_t7):
        style_cell(t7.rows[0].cells[col_idx], h, bold=True, color_rgb=(255, 255, 255), bg_hex='1E293B', font_size=10)
    t7_data = [
        ('Immediate and effective address', 'imm = -4 (0xFFFFFFFC), addr = 0x00001004', 'imm = -4 (0xFFFFFFFC), addr = 0x00001004 (Ripes: 0x10000000)'),
        ('Memory before and after the edge', 'Before: M[0x1004]=3, After: M[0x1004]=12', 'Before: M[0x1004]=3, After: M[0x1004]=12 (0x0C committed)'),
        ('x10 and x6 after the edge', 'x10 = 0x00001008, x6 = 12', 'x10 = 0x00001008 (Ripes: 0x10000004), x6 = 12 (unchanged)'),
        ('PC after the edge', '0x00000024 (PC+4)', '0x00000024 (Ripes: 0x00000014)')
    ]
    for r_idx, row in enumerate(t7_data, start=1):
        bg = 'F8FAFC' if r_idx % 2 == 1 else 'FFFFFF'
        style_cell(t7.rows[r_idx].cells[0], row[0], bold=True, bg_hex=bg, color_rgb=(15, 23, 42))
        style_cell(t7.rows[r_idx].cells[1], row[1], bg_hex=bg)
        style_cell(t7.rows[r_idx].cells[2], row[2], bg_hex=bg)
        
    # Table 9: Fault diagnosis table
    t9 = doc.tables[9]
    headers_t9 = ['Case', 'Fault and value', 'First differing effect', 'Evidence after repair']
    for col_idx, h in enumerate(headers_t9):
        style_cell(t9.rows[0].cells[col_idx], h, bold=True, color_rgb=(255, 255, 255), bg_hex='1E293B', font_size=10)
    t9_data = [
        ('A',
         'ALUSrc stuck at 0\n(forced ALUSrc=0, expected 1)',
         'ALU selects Read2 (x6=12) instead of imm 4. ALU computes 0x1000+12=0x100C. M[0x100C] is overwritten with 12, while target M[0x1004] remains 0.',
         'Restoring nominal ALUSrc=1 selects immediate 4; ALU computes address 0x1004 and correctly updates M[0x1004] to 12.'),
        ('B',
         'RegWrite stuck at 0\n(forced RegWrite=0, expected 1)',
         'Memory correctly reads 7 and WBData=7, but register write enable is low. At rising edge, x5 is NOT updated and stays at 0.',
         'Restoring nominal RegWrite=1 enables the register file write enable, correctly latching 7 into destination register x5.'),
        ('C',
         'PCSel stuck at 0\n(forced PCSel=0, expected 1)',
         'Even though Branch=1 and Eq=1 (x6==x11=12) and Target=0x2C, PCSel mux selects sequential PC+4 (0x24) instead of target 0x2C.',
         'Restoring nominal PCSel=1 routes branch target 0x2C through the next PC multiplexer, correctly redirecting execution.')
    ]
    for r_idx, row in enumerate(t9_data, start=1):
        bg = 'F8FAFC' if r_idx % 2 == 1 else 'FFFFFF'
        style_cell(t9.rows[r_idx].cells[0], row[0], bold=True, bg_hex=bg, color_rgb=(15, 23, 42))
        style_cell(t9.rows[r_idx].cells[1], row[1], bg_hex=bg)
        style_cell(t9.rows[r_idx].cells[2], row[2], bg_hex=bg)
        style_cell(t9.rows[r_idx].cells[3], row[3], bg_hex=bg)
        
    # D3
    format_paragraph(doc.paragraphs[89], 'D3 Answer: Observing only external/architectural symptoms such as "x5 stayed zero" is insufficient because multiple distinct hardware faults cause the exact same external outcome:\n1. RegWrite control stuck at 0 (write enable inactive, Case B).\n2. ALU address calculation failure (ALU produces wrong address pointing to zero/unmapped memory).\n3. Data Memory read failure (memory read port disabled or stuck at 0).\n4. WBsel multiplexer stuck at 0 (selecting ALU address instead of memory data, or grounded bus).\n5. Register file write decoder failure (writing to x0 or wrong register index instead of x5).\nBy observing internal settled wire values before the clock edge—verifying that ALUResult = 0x1000, MemReadData = 7, and WBData = 7 are all fully settled and valid—we definitively confirm that the data was correctly read and routed to the register input, proving that the failure is uniquely due to the write enable (RegWrite = 0).', font_size=10.0)
    
    # Table 11: Timing table
    t11 = doc.tables[11]
    headers_t11 = ['Quantity', 'Before optimization', 'After optimization']
    for col_idx, h in enumerate(headers_t11):
        style_cell(t11.rows[0].cells[col_idx], h, bold=True, color_rgb=(255, 255, 255), bg_hex='1E293B', font_size=10)
    t11_data = [
        ('Load path in ps', '800', '750'),
        ('Add path in ps', '550', '500'),
        ('Branch path in ps', '760', '760'),
        ('Fixed period in ps', '800', '760 (Branch becomes critical!)'),
        ('Clock frequency in GHz', '1.250 GHz', '1.316 GHz (1.3158 GHz)'),
        ('Time for 100 instructions in ns', '80.0 ns', '76.0 ns')
    ]
    for r_idx, row in enumerate(t11_data, start=1):
        bg = 'F8FAFC' if r_idx % 2 == 1 else 'FFFFFF'
        style_cell(t11.rows[r_idx].cells[0], row[0], bold=True, bg_hex=bg, color_rgb=(15, 23, 42))
        style_cell(t11.rows[r_idx].cells[1], row[1], bg_hex=bg)
        style_cell(t11.rows[r_idx].cells[2], row[2], bg_hex=bg)
        
    # E1, E2
    format_paragraph(doc.paragraphs[99], 'E1 Answer: In a single-cycle CPU, the clock cycle period is determined by the slowest path among all supported instructions: T_clk = max(T_load, T_add, T_branch). Initially, the load path is the critical path at 800 ps (greater than branch at 760 ps). Reducing the main ALU delay by 50 ps speeds up the load path to 750 ps. However, the dedicated branch path (760 ps) uses separate comparator and adder circuits and does not use the main ALU; thus its delay remains 760 ps. Because 760 ps > 750 ps, the branch path becomes the new critical path. In accordance with Amdahl\'s Law, overall performance is now bottlenecked by the unimproved branch hardware, limiting the clock period reduction to 40 ps (from 800 ps to 760 ps) rather than the full 50 ps saved in the ALU.', font_size=10.0)
    format_paragraph(doc.paragraphs[103], 'E2 Answer:\n• Original Case (Select at 410 ps, data inputs at 260 ps and 320 ps):\n  Output Arrival = max(260, 320, 410) + 30 ps = 410 ps + 30 ps = 440 ps. (The select signal is the critical arrival).\n• Improved Case (Select at 300 ps, data inputs at 260 ps and 320 ps):\n  Output Arrival = max(260, 320, 300) + 30 ps = 320 ps + 30 ps = 350 ps. (Data Input 1 at 320 ps is now the critical arrival).\n• Why arrivals are compared rather than added: The multiplexer data inputs and select control line propagate through physically separate, concurrent hardware circuits. The multiplexer\'s output cannot settle to a valid, glitch-free value until the latest of all required input signals has arrived and the internal multiplexer transmission delay has elapsed. Because these signals travel concurrently in parallel time rather than sequentially in series, their arrival times must be compared (taking the maximum) rather than added.', font_size=10.0)
    
    # Exit ticket answers
    p_ex = doc.paragraphs[108]
    format_paragraph(doc.paragraphs[109], '1. For lw, which value is an address and which value is written to rd?\nAnswer: The address is the effective memory address generated by the ALU adding base register rs1 (x10 = 0x1000) and immediate offset 0 (0x1000 + 0 = 0x1000), routed to the Data Memory address port. The write-back value is the data word retrieved from Data Memory at that address (7 = 0x00000007), routed via WBsel=1 to the register file WriteData port to be committed into destination register rd (x5).', font_size=10.0)
    format_paragraph(doc.paragraphs[110], '2. Can a correct value on a wire update a register when RegWrite=0?\nAnswer: No. In synchronous sequential logic, register file updates are strictly gated by the write-enable control signal (RegWrite). When RegWrite=0, the clock-enable circuitry disables the internal register latches, preventing any wire value from modifying stored register state, regardless of whether the wire carries a valid candidate value.', font_size=10.0)
    format_paragraph(doc.paragraphs[111], '3. In this lecture\'s beq path, what two conditions make PCSel=1?\nAnswer: In this datapath, PCSel is evaluated by the combinational expression PCSel = Branch AND Eq. Therefore, two conditions must simultaneously hold: (1) Branch = 1 (the instruction opcode is a branch instruction, 0x63 for beq), and (2) Eq = 1 (the dedicated equality comparator evaluates that register operand 1 equals register operand 2, Read1 == Read2).', font_size=10.0)
    format_paragraph(doc.paragraphs[112], '4. Why can CPI=1 still correspond to a slow processor?\nAnswer: According to the Iron Law of Processor Performance (CPU Time = Instruction Count × CPI × Clock Period), execution time depends on both CPI and clock period. In a single-cycle processor, CPI = 1, but the clock period must accommodate the single slowest instruction path in the machine (the critical path, traversing instruction memory, register file, ALU, data memory, and writeback). This results in a low clock frequency. A pipelined processor with a slightly higher CPI (e.g. 1.1–1.3 due to pipeline hazards) can operate at a vastly higher clock frequency (e.g. 5x faster), finishing programs in substantially less total execution time.', font_size=10.0)
    
    # Optional loop
    loop_text = (
        'Optional Loop Answers & Trace (04_loop_optional.s / --scenario loop):\n'
        '• Visited PCs: 0x00000020 (add) -> 0x00000024 (beq, not taken) -> 0x00000028 (beq, taken backward) -> 0x00000020 (add) -> 0x00000024 (beq, taken exit) -> 0x0000002C (stopped at observation boundary).\n'
        '• Value of x6 After Each Instruction: Cycle 1 (0x20): x6 = 1; Cycle 2 (0x24): x6 = 1; Cycle 3 (0x28): x6 = 1; Cycle 4 (0x20): x6 = 2; Cycle 5 (0x24): x6 = 2.\n'
        '• Total Completed Instructions: 5 completed instructions; final PC = 0x0000002C; final x6 = 2.\n'
        '• Memory State: Data memory remains 100% unchanged throughout (zero store operations executed).\n'
        '• Backward Branch Explanation: The backward branch beq x0, x0, -8 is an unconditional jump (x0==x0 evaluates always true). It computes target PC + (-8) = 0x28 - 8 = 0x20 and sets PCSel = 1. Because RegWrite = 0 and MemWrite = 0, no register or data memory state is altered; only the PC register is updated.'
    )
    format_paragraph(doc.paragraphs[114], loop_text, font_size=10.0)
    
    # Add pictures at the end of the handout
    p_dp = doc.add_paragraph()
    p_dp.paragraph_format.space_before = Pt(14)
    p_dp.paragraph_format.space_after = Pt(4)
    r_dp_title = p_dp.add_run('Figure 1: Ripes 32-bit Single-Cycle Processor Datapath Schematic (RV32_SS)')
    r_dp_title.bold = True
    r_dp_title.font.name = 'Calibri'
    r_dp_title.font.size = Pt(11)
    doc.add_picture('ripes_datapath_annotated.png', width=Inches(6.2))
    
    p_tel = doc.add_paragraph()
    p_tel.paragraph_format.space_before = Pt(14)
    p_tel.paragraph_format.space_after = Pt(4)
    r_tel_title = p_tel.add_run('Figure 2: Ripes Multi-Scenario Execution Telemetry & State Verification')
    r_tel_title.bold = True
    r_tel_title.font.name = 'Calibri'
    r_tel_title.font.size = Pt(11)
    doc.add_picture('ripes_execution_telemetry.png', width=Inches(6.2))
    
    p_flt = doc.add_paragraph()
    p_flt.paragraph_format.space_before = Pt(14)
    p_flt.paragraph_format.space_after = Pt(4)
    r_flt_title = p_flt.add_run('Figure 3: Task D Annotated Fault A Trace & Root Cause Analysis')
    r_flt_title.bold = True
    r_flt_title.font.name = 'Calibri'
    r_flt_title.font.size = Pt(11)
    doc.add_picture('task_d_fault_a_annotated.png', width=Inches(6.2))
    
    doc.save(output_path)
    print(f'Handout successfully saved to: {output_path}')

process_handout('Lecture4_Lab_Student_Handout.docx', 'Lecture4_Lab_Student_Handout.docx')
import shutil
shutil.copyfile('Lecture4_Lab_Student_Handout.docx', 'Lecture4_Lab_Student_Handout_Filled.docx')
print('Copied to root Lecture4_Lab_Student_Handout_Filled.docx')
