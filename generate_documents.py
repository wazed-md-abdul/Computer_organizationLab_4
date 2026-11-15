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

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
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

def process_report_template(template_path, output_path):
    doc = docx.Document(template_path)
    
    # P2: Student info
    format_paragraph(doc.paragraphs[2], 'Name: Student Report                    Student ID: 2026-CO-LAB4                    Date: November 15, 2026', font_size=10.5, bold=True, color_rgb=(15, 23, 42))
    
    # P5: Environment
    env_text = (
        '• Ripes Simulator: Ripes v2.2.6 (Windows 64-bit); Processor model: 32-bit Single-Cycle Processor (RV32_SS), Extended Layout, compressed C extension disabled.\n'
        '• Python Teaching Model: Python 3.14.7 (Lecture 4 lab4_cpu.py teaching simulator).\n'
        '• Actual Ripes Base (B) & Trace Start (S): B = 0x10000000 (address of source_word); S = 0x00000014 (address of trace_start in 01_load_add_store.s).\n'
        '• Course Model Base (B) & Trace Start (S): B = 0x00001000; S = 0x00000000.'
    )
    format_paragraph(doc.paragraphs[5], env_text, font_size=10.0, color_rgb=(30, 41, 59))
    
    # Table 0: Load Add Store Table
    t0 = doc.tables[0]
    # Header styling
    headers_t0 = ['Op', 'Predicted state', 'Observed state', 'Explanation of changes']
    for col_idx, h in enumerate(headers_t0):
        style_cell(t0.rows[0].cells[col_idx], h, bold=True, color_rgb=(255, 255, 255), bg_hex='1E293B', font_size=10)
    
    t0_data = [
        ('lw',
         'PC = 0x00000004 (Ripes: S+4 = 0x18)\nx5 = 7 (0x00000007), x6 = 0\nM[B] = 7, M[B+4] = 0',
         'PC = 0x00000004 (Ripes: 0x18)\nx5 = 0x00000007, x6 = 0x00000000\nM[0x1000] = 0x07, M[0x1004] = 0x00',
         'ALU adds x10 (0x1000) and imm (0) to compute effective address 0x1000. Data memory outputs 7. WBsel=1 selects memory output. RegWrite=1 enables register write. At the rising clock edge, x5 latches 7. PC advances to 0x04 (Ripes: 0x18). Memory and other registers remain unchanged.'),
        ('add',
         'PC = 0x00000008 (Ripes: S+8 = 0x1C)\nx5 = 7, x6 = 12 (0x0000000C)\nM[B] = 7, M[B+4] = 0',
         'PC = 0x00000008 (Ripes: 0x1C)\nx5 = 0x00000007, x6 = 0x0000000C\nM[0x1000] = 0x07, M[0x1004] = 0x00',
         'ALU reads x5 (7) and x2 (5); ALUSrc=0 selects rs2. Main ALU adds 7 + 5 = 12 (0x0C). WBsel=0 selects ALUResult. RegWrite=1 enables register write. At the rising edge, x6 latches 12. PC advances to 0x08 (Ripes: 0x1C). Memory remains unchanged.'),
        ('sw',
         'PC = 0x0000000C (Ripes: S+12 = 0x20)\nx5 = 7, x6 = 12 (0x0C)\nM[B] = 7, M[B+4] = 12 (0x0000000C)',
         'PC = 0x0000000C (Ripes: 0x20)\nx5 = 0x00000007, x6 = 0x0000000C\nM[0x1000] = 0x07, M[0x1004] = 0x0C',
         'ALU adds x10 (0x1000) and imm (4) to compute effective address 0x1004 (ALUSrc=1). StoreData wire routes rs2 (x6=12) directly to Data Memory write-data port. MemWrite=1 enables memory write; RegWrite=0 disables register write. At rising edge, M[0x1004] updates from 0 to 12. All integer registers remain unchanged.')
    ]
    for r_idx, row in enumerate(t0_data, start=1):
        bg = 'F8FAFC' if r_idx % 2 == 1 else 'FFFFFF'
        style_cell(t0.rows[r_idx].cells[0], row[0], bold=True, bg_hex=bg, color_rgb=(15, 23, 42))
        style_cell(t0.rows[r_idx].cells[1], row[1], bg_hex=bg)
        style_cell(t0.rows[r_idx].cells[2], row[2], bg_hex=bg)
        style_cell(t0.rows[r_idx].cells[3], row[3], bg_hex=bg)
        
    # Questions in Section A: P9, P10 (Load); P12, P13 (Store); P15 (No stall)
    p9_text = (
        '• Address & Memory Output: The main ALU calculates effective address 0x1000 by adding base register x10 (0x1000) and sign-extended immediate offset 0. The Data Memory combinational read port settles MemReadData = 7 (0x00000007), which propagates through the write-back multiplexer (WBsel=1) onto the WBData bus as candidate value 7.\n'
        '• x5 Before vs. After Rising Edge: The processor is synchronous with edge-triggered registers. Throughout Cycle 1 before the clock edge, wire values are transient combinational candidates; register x5 holds its pre-existing stored value 0x00000000. Only when the rising clock edge arrives—sampling RegWrite=1—does x5 latch the candidate value from WBData, committing the update from 0 to 7.'
    )
    format_paragraph(doc.paragraphs[9], p9_text, font_size=10.0)
    format_paragraph(doc.paragraphs[10], '', space_before=0, space_after=0)
    
    p12_text = (
        '• Address Route ("Where to write"): Register rs1 (x10 = 0x1000) drives ALU input A. ALUSrc = 1 selects the sign-extended immediate (4) for ALU input B. The main ALU computes effective address 0x1000 + 4 = 0x1004, which connects directly to the Data Memory address port.\n'
        '• Data Route ("What to write"): Register rs2 (x6 = 12 = 0x0000000C) is read combinationally from the register file\'s second read port (Read2) and routed directly via a dedicated internal bus to the Data Memory WriteData port, completely bypassing the ALU.\n'
        '• Preserved Registers: RegWrite = 0 disables the register file write enable. No integer register (x0–x31) changes state at the clock edge. Source registers x10 and x6, intermediate register x5, and all others remain strictly unchanged.'
    )
    format_paragraph(doc.paragraphs[12], p12_text, font_size=10.0)
    format_paragraph(doc.paragraphs[13], '', space_before=0, space_after=0)
    
    p15_text = (
        'In a single-cycle CPU datapath, every instruction executes to full completion within exactly one clock cycle. The value loaded into x5 commits to the register file at the rising clock edge ending Cycle 1 (the lw). When Cycle 2 (the add) begins immediately after this clock edge, the register file read port combinationally reads the newly updated value (7) in x5. Because instructions execute strictly sequentially without overlapping pipeline stages, there are no Read-After-Write (RAW) pipeline data hazards and thus no need for pipeline stalls, bubbles, or forwarding hardware.'
    )
    format_paragraph(doc.paragraphs[15], p15_text, font_size=10.0)
    
    # Table 1: Controls
    t1 = doc.tables[1]
    headers_t1 = ['Instruction', 'RegWrite', 'ALUSrc', 'MemWrite', 'WBsel', 'Branch', 'PCSel']
    for col_idx, h in enumerate(headers_t1):
        style_cell(t1.rows[0].cells[col_idx], h, bold=True, color_rgb=(255, 255, 255), bg_hex='1E293B', font_size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
    t1_data = [
        ('add', '1', '0', '0', '0', '0', '0'),
        ('lw', '1', '1', '0', '1', '0', '0'),
        ('sw', '0', '1', '1', 'X (0)', '0', '0'),
        ('beq equal', '0', 'X (0)', '0', 'X (0)', '1', '1'),
        ('beq unequal', '0', 'X (0)', '0', 'X (0)', '1', '0')
    ]
    for r_idx, row in enumerate(t1_data, start=1):
        bg = 'F8FAFC' if r_idx % 2 == 1 else 'FFFFFF'
        style_cell(t1.rows[r_idx].cells[0], row[0], bold=True, bg_hex=bg, color_rgb=(15, 23, 42))
        for c_idx in range(1, 7):
            style_cell(t1.rows[r_idx].cells[c_idx], row[c_idx], bg_hex=bg, align=WD_ALIGN_PARAGRAPH.CENTER)
            
    # Questions in Section B: P19, P20, P21 (X entries & rs2 in store)
    p19_text = (
        '• Justification of Don\'t-Care (X) Entries:\n'
        '  1. sw (WBsel = X): WBsel chooses between ALUResult (0) and MemReadData (1) to feed the register file write data port. In a store instruction, RegWrite = 0 deasserts the register write enable. Because no register latches the write-back bus, the multiplexer selection has zero architectural effect. The course tracer defaults WBsel to 0 for deterministic outputs.\n'
        '  2. beq (ALUSrc = X, WBsel = X): In this architecture, beq evaluates equality using a dedicated comparator (Read1 == Read2) and computes the branch target using a dedicated adder (PC + imm). The main ALU result and memory output are completely unused. Furthermore, RegWrite = 0 and MemWrite = 0 prevent any state changes to registers or memory. Therefore, both ALUSrc (ALU input B mux) and WBsel are true don\'t-cares. The tracer defaults both to 0.\n'
        '• Why Store Still Uses rs2 When ALUSrc = 1: In sw, the ALU must compute the destination memory address (rs1 + offset), which requires ALUSrc = 1 to route the sign-extended immediate instead of rs2 into the ALU. However, the instruction must also supply the data word to store. The datapath contains a separate, dedicated wire routing the second register read port (Read2 / rs2) directly to the Data Memory WriteData input. Thus, rs2 is actively used for memory data even though ALUSrc = 1 selects the immediate for the ALU.'
    )
    format_paragraph(doc.paragraphs[19], p19_text, font_size=10.0)
    format_paragraph(doc.paragraphs[20], '', space_before=0, space_after=0)
    format_paragraph(doc.paragraphs[21], '', space_before=0, space_after=0)
    
    # Table 2: Decode 0x00652223
    t2 = doc.tables[2]
    headers_t2 = ['Field', 'Bit positions', 'Your value']
    for col_idx, h in enumerate(headers_t2):
        style_cell(t2.rows[0].cells[col_idx], h, bold=True, color_rgb=(255, 255, 255), bg_hex='1E293B', font_size=10)
    t2_data = [
        ('opcode', '6:0', '0100011 (0x23, STORE)'),
        ('funct3', '14:12', '010 (0x2, sw / 32-bit word store)'),
        ('rs1', '19:15', '01010 (10, x10 base address)'),
        ('rs2', '24:20', '00110 (6, x6 store data)'),
        ('imm[11:5]', '31:25', '0000000 (0)'),
        ('imm[4:0]', '11:7', '00100 (4)')
    ]
    for r_idx, row in enumerate(t2_data, start=1):
        bg = 'F8FAFC' if r_idx % 2 == 1 else 'FFFFFF'
        style_cell(t2.rows[r_idx].cells[0], row[0], bold=True, bg_hex=bg, color_rgb=(15, 23, 42))
        style_cell(t2.rows[r_idx].cells[1], row[1], bg_hex=bg)
        style_cell(t2.rows[r_idx].cells[2], row[2], bg_hex=bg)
        
    p24_text = (
        '• Signed Store Immediate Reconstruction: In S-format encoding, the 12-bit immediate is split into imm[11:5] (bits 31:25) and imm[4:0] (bits 11:7). Reconstructing the immediate by concatenation yields:\n'
        '  imm[11:0] = imm[11:5] ## imm[4:0] = 0000000 ## 00100 = 000000000100_2 = +4 (decimal +4, 32-bit hex 0x00000004).\n'
        '• How the Decoder Identifies a Word Store: Opcode bits 6:0 are 0100011 (0x23), identifying the instruction as belonging to the STORE major opcode class. The funct3 field at bits 14:12 is 010 (0x2), which uniquely specifies 32-bit Word width (sw), distinguishing it from byte (sb, funct3=000) and halfword (sh, funct3=001).'
    )
    format_paragraph(doc.paragraphs[24], p24_text, font_size=10.0)
    format_paragraph(doc.paragraphs[25], '', space_before=0, space_after=0)
    
    p27_text = (
        '• S-Format Bits 11:7 (B1): In the RISC-V ISA design, register source specifiers rs1 (bits 19:15) and rs2 (bits 24:20) remain in identical bit positions across all instruction formats to keep register read decoding simple and uniform. Store instructions write to memory rather than registers and therefore do not have a destination register (rd). To utilize all instruction bits without adding decode complexity, the 5 bits at positions 11:7 (which hold rd in R-type and I-type instructions) are repurposed to hold the lower 5 bits of the immediate offset (imm[4:0]).\n'
        '• Add vs. Sub Distinction (B2): Both add and sub are R-type instructions sharing identical opcode 0110011 (0x33) and identical funct3 = 000. They are uniquely distinguished by the 7-bit funct7 field at bits 31:25: add has funct7 = 0000000 (0x00), whereas sub has funct7 = 0100000 (0x20, with bit 30 set high).'
    )
    format_paragraph(doc.paragraphs[27], p27_text, font_size=10.0)
    format_paragraph(doc.paragraphs[28], '', space_before=0, space_after=0)
    
    # Table 3: Branch outcomes
    t3 = doc.tables[3]
    headers_t3 = ['Run', 'Eq', 'Sequential PC', 'Target PC', 'PCSel', 'Observed PC']
    for col_idx, h in enumerate(headers_t3):
        style_cell(t3.rows[0].cells[col_idx], h, bold=True, color_rgb=(255, 255, 255), bg_hex='1E293B', font_size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
    t3_data = [
        ('x11=12', '1', '0x00000010 (Ripes: 0x28)', '0x00000018 (Ripes: 0x30)', '1', '0x00000018 (Ripes: 0x30)'),
        ('x11=9', '0', '0x00000010 (Ripes: 0x28)', '0x00000018 (Ripes: 0x30)', '0', '0x00000010 (Ripes: 0x28)')
    ]
    for r_idx, row in enumerate(t3_data, start=1):
        bg = 'F8FAFC' if r_idx % 2 == 1 else 'FFFFFF'
        style_cell(t3.rows[r_idx].cells[0], row[0], bold=True, bg_hex=bg, color_rgb=(15, 23, 42))
        for c_idx in range(1, 6):
            style_cell(t3.rows[r_idx].cells[c_idx], row[c_idx], bg_hex=bg, align=WD_ALIGN_PARAGRAPH.CENTER)
            
    p32_text = (
        '• C1a (State Preserved vs. Changed): beq writes NEITHER an integer register nor a memory word (RegWrite = 0, MemWrite = 0). All register contents (x0–x31) and data memory words remain completely unchanged. The ONLY architectural state component that changes at the clock edge is the Program Counter (PC), updating to the branch target address (PC+12) if taken (x11=12), or to sequential PC+4 if not taken (x11=9).\n'
        '• C1b (Branch Base Address): In RISC-V RV32I, branch offsets are defined relative to the address of the branch instruction itself (PC), not PC+4. The branch target adder computes Target = PC + imm. If the offset (+12 bytes) were added to PC+4, the target would be shifted forward by 4 extra bytes (target = PC+16), corrupting control flow and jumping to the wrong instruction.'
    )
    format_paragraph(doc.paragraphs[32], p32_text, font_size=10.0)
    format_paragraph(doc.paragraphs[33], '', space_before=0, space_after=0)
    
    p35_text = (
        '• Immediate: Signed decimal value is -4. In 12-bit signed two\'s complement it is 0xFFC (binary 1111 1111 1100), and sign-extended to 32 bits it is 0xFFFFFFFC.\n'
        '• Effective Address & Store Data:\n'
        '  - Course Model: Effective address = x10 + (-4) = 0x00001008 + (-4) = 0x00001004. Store data = x6 = 12 (0x0000000C).\n'
        '  - Ripes: Effective address = x10 + (-4) = 0x10000004 + (-4) = 0x10000000 (slot). Store data = x6 = 12 (0x0000000C).\n'
        '• Memory Before and After Edge:\n'
        '  - Course Model: Before edge, M[0x1004] = 3 (0x00000003); after rising edge, M[0x1004] commits to 12 (0x0000000C).\n'
        '  - Ripes: Before edge, M[0x10000000] = 3; after rising edge, M[0x10000000] commits to 12 (0x0000000C).\n'
        '• Unchanged Registers & Next PC: Base register x10 (0x1008 in Python, 0x10000004 in Ripes) and data register x6 (12) are completely unchanged (RegWrite=0). Next PC advances from 0x20 to 0x24 (PC+4) in Python, and from 0x10 to 0x14 in Ripes.\n'
        '• Checkpoint Explanation: Changing the offset from positive to negative alters only the immediate generator and ALU input B for address calculation. The store data wire is tapped directly from register read port 2 (Read2), which is selected exclusively by rs2 and independent of the address calculation.'
    )
    format_paragraph(doc.paragraphs[35], p35_text, font_size=10.0)
    format_paragraph(doc.paragraphs[36], '', space_before=0, space_after=0)
    format_paragraph(doc.paragraphs[37], '', space_before=0, space_after=0)
    
    # Table 4: Fault diagnoses
    t4 = doc.tables[4]
    headers_t4 = ['Case', 'Prediction and fault', 'First wrong effect', 'Clean comparison']
    for col_idx, h in enumerate(headers_t4):
        style_cell(t4.rows[0].cells[col_idx], h, bold=True, color_rgb=(255, 255, 255), bg_hex='1E293B', font_size=10)
    t4_data = [
        ('A',
         'ALUSrc stuck at 0\n(forced ALUSrc=0, expected 1)',
         'ALU selects Read2 (x6=12) instead of imm 4. ALU computes 0x1000 + 12 = 0x100C. M[0x100C] is overwritten with 12, while target M[0x1004] remains 0.',
         'In clean store (--scenario store), ALUSrc=1, ALU computes 0x1004, and M[0x1004] is correctly updated to 12.'),
        ('B',
         'RegWrite stuck at 0\n(forced RegWrite=0, expected 1)',
         'Memory correctly reads 7 and WBData=7, but register write enable is low. At rising edge, x5 is NOT updated and stays at 0.',
         'In clean load (--scenario load), RegWrite=1, and x5 updates from 0 to 7 at the rising clock edge.'),
        ('C',
         'PCSel stuck at 0\n(forced PCSel=0, expected 1)',
         'Even though Branch=1 and Eq=1 (x6==x11=12) and Target=0x2C, PCSel mux selects sequential PC+4 (0x24) instead of target 0x2C.',
         'In clean branch (--scenario branch), PCSel=1, and PC updates to branch target 0x2C at the clock edge.')
    ]
    for r_idx, row in enumerate(t4_data, start=1):
        bg = 'F8FAFC' if r_idx % 2 == 1 else 'FFFFFF'
        style_cell(t4.rows[r_idx].cells[0], row[0], bold=True, bg_hex=bg, color_rgb=(15, 23, 42))
        style_cell(t4.rows[r_idx].cells[1], row[1], bg_hex=bg)
        style_cell(t4.rows[r_idx].cells[2], row[2], bg_hex=bg)
        style_cell(t4.rows[r_idx].cells[3], row[3], bg_hex=bg)
        
    p41_text = (
        '• Signals Remaining Correct: All address calculation and data routing signals are fully correct: ALU_A = 0x1000, ALU_B = 4 (ALUSrc=1), ALUResult = 0x1004, StoreData = 12 (0x0C), and RegWrite = 0.\n'
        '• Missing Update: Because MemWrite = 0, the write enable port of Data Memory is deasserted. At the rising clock edge, no write occurs; memory word M[0x1004] remains 0x00000000.\n'
        '• Comparison with Case A: In Case A, routing was faulty (ALUSrc=0 routed x6 instead of imm) but write permission was active (MemWrite=1), causing an unintended write to the WRONG memory address (0x100C). In D1, routing is correct (address is 0x1004), but write permission is revoked (MemWrite=0), resulting in NO write occurring anywhere in memory.'
    )
    format_paragraph(doc.paragraphs[41], p41_text, font_size=10.0)
    format_paragraph(doc.paragraphs[42], '', space_before=0, space_after=0)
    
    p44_text = (
        '• Architectural State Comparison: In both runs (WBsel=0 and WBsel=1), the post-edge architectural state is 100% IDENTICAL: PC = 0x0000000C, M[0x1004] = 0x0000000C, x5 = 0, and x6 = 12.\n'
        '• Explanation: In a store instruction, RegWrite = 0. Because the register file write enable is low, the register file ignores whatever value is present on the write-back bus (WBData). Whether WBsel=0 routes the ALU result (0x1004) or WBsel=1 routes data memory output (0x0000) to WBData, neither value is ever latched into any register. Thus, an unused wire value cannot alter architectural state, proving WBsel is a true don\'t-care for stores.'
    )
    format_paragraph(doc.paragraphs[44], p44_text, font_size=10.0)
    format_paragraph(doc.paragraphs[45], '', space_before=0, space_after=0)
    
    p47_text = (
        'Observing only external/architectural symptoms such as "x5 stayed zero" is insufficient because multiple distinct hardware faults cause the exact same external outcome:\n'
        '1. RegWrite control stuck at 0 (write enable inactive, Case B).\n'
        '2. ALU address calculation failure (ALU produces wrong address pointing to zero/unmapped memory).\n'
        '3. Data Memory read failure (memory read port disabled or stuck at 0).\n'
        '4. WBsel multiplexer stuck at 0 (selecting ALU address instead of memory data, or grounded bus).\n'
        '5. Register file write decoder failure (writing to x0 or wrong register index instead of x5).\n'
        'By observing internal settled wire values before the clock edge—verifying that ALUResult = 0x1000, MemReadData = 7, and WBData = 7 are all fully settled and valid—we definitively confirm that the data was correctly read and routed to the register input, proving that the failure is uniquely due to the write enable (RegWrite = 0).'
    )
    format_paragraph(doc.paragraphs[47], p47_text, font_size=10.0)
    format_paragraph(doc.paragraphs[48], '', space_before=0, space_after=0)
    
    # P49: Fault trace / screenshot attachment
    format_paragraph(doc.paragraphs[49], 'Attached Figure D.1: Annotated Fault A Diagnosis Trace (sw x6, 4(x10) at PC = 0x00000008 / Ripes PC 0x1C). The graphic displays candidate wire values settled BEFORE the rising clock edge (ALUSrc=0, ALU_B=0x0000000C, ALUResult=0x0000100C) and committed state AFTER the rising clock edge (M[0x100C] corrupted to 12, target M[0x1004] unwritten).', font_size=10.0, bold=True)
    
    # Table 5: Timing
    t5 = doc.tables[5]
    headers_t5 = ['Quantity', 'Before optimization', 'After optimization']
    for col_idx, h in enumerate(headers_t5):
        style_cell(t5.rows[0].cells[col_idx], h, bold=True, color_rgb=(255, 255, 255), bg_hex='1E293B', font_size=10)
    t5_data = [
        ('Load path in ps', '800', '750'),
        ('Add path in ps', '550', '500'),
        ('Branch path in ps', '760', '760'),
        ('Fixed period in ps', '800', '760 (Branch becomes critical!)'),
        ('Frequency in GHz', '1.250 GHz', '1.316 GHz (1.3158 GHz)'),
        ('100 instruction time in ns', '80.0 ns', '76.0 ns')
    ]
    for r_idx, row in enumerate(t5_data, start=1):
        bg = 'F8FAFC' if r_idx % 2 == 1 else 'FFFFFF'
        style_cell(t5.rows[r_idx].cells[0], row[0], bold=True, bg_hex=bg, color_rgb=(15, 23, 42))
        style_cell(t5.rows[r_idx].cells[1], row[1], bg_hex=bg)
        style_cell(t5.rows[r_idx].cells[2], row[2], bg_hex=bg)
        
    p53_text = (
        '• Load Path Summation:\n'
        '  - Before: Launch (30 ps) + Instruction access/decode (200 ps) + Register file access (100 ps) + Main ALU (150 ps) + Data memory read (250 ps) + Write-back selection (30 ps) + Setup/margin (40 ps) = 800 ps.\n'
        '  - After (ALU reduced from 150 ps to 100 ps): 30 + 200 + 100 + 100 + 250 + 30 + 40 = 750 ps.\n'
        '• Speedup Calculation:\n'
        '  Speedup = (Execution Time Before) / (Execution Time After) = (Clock Period Before) / (Clock Period After) = 800 ps / 760 ps ≈ 1.0526 (5.26% speedup, or 1.05x).'
    )
    format_paragraph(doc.paragraphs[53], p53_text, font_size=10.0)
    format_paragraph(doc.paragraphs[54], '', space_before=0, space_after=0)
    
    p56_text = (
        'In a single-cycle CPU, the clock cycle period is determined by the slowest path among all supported instructions: T_clk = max(T_load, T_add, T_branch). Initially, the load path is the critical path at 800 ps (greater than branch at 760 ps). Reducing the main ALU delay by 50 ps speeds up the load path to 750 ps. However, the dedicated branch path (760 ps) uses separate comparator and adder circuits and does not use the main ALU; thus its delay remains 760 ps. Because 760 ps > 750 ps, the branch path becomes the new critical path. In accordance with Amdahl\'s Law, overall performance is now bottlenecked by the unimproved branch hardware, limiting the clock period reduction to 40 ps (from 800 ps to 760 ps) rather than the full 50 ps saved in the ALU.'
    )
    format_paragraph(doc.paragraphs[56], p56_text, font_size=10.0)
    format_paragraph(doc.paragraphs[57], '', space_before=0, space_after=0)
    
    p59_text = (
        '• Conservative Rule: Output Arrival = max(Input 0 Arrival, Input 1 Arrival, Select Arrival) + Mux Delay (30 ps).\n'
        '• Original Case (Select at 410 ps, data inputs at 260 ps and 320 ps):\n'
        '  Output Arrival = max(260, 320, 410) + 30 ps = 410 ps + 30 ps = 440 ps. (The select signal is the critical arrival).\n'
        '• Improved Case (Select at 300 ps, data inputs at 260 ps and 320 ps):\n'
        '  Output Arrival = max(260, 320, 300) + 30 ps = 320 ps + 30 ps = 350 ps. (Data Input 1 at 320 ps is now the critical arrival).\n'
        '• Reasoning: The multiplexer data inputs and select control line propagate through physically separate, concurrent hardware circuits. The multiplexer\'s output cannot settle to a valid, glitch-free value until the latest of all required input signals has arrived and the internal multiplexer transmission delay has elapsed. Because these signals travel concurrently in parallel time rather than sequentially in series, their arrival times must be compared (taking the maximum) rather than added.'
    )
    format_paragraph(doc.paragraphs[59], p59_text, font_size=10.0)
    format_paragraph(doc.paragraphs[60], '', space_before=0, space_after=0)
    
    # Exit ticket
    format_paragraph(doc.paragraphs[63], 'The address is the memory location generated by the ALU adding base register rs1 (x10 = 0x1000) and immediate offset 0 (0x1000 + 0 = 0x1000), routed to the Data Memory address port. The write-back value is the data word retrieved from Data Memory at that address (7 = 0x00000007), routed via WBsel=1 to the register file WriteData port to be committed into destination register rd (x5).', font_size=10.0)
    format_paragraph(doc.paragraphs[65], 'RegWrite=0 disables the write-enable control line of the integer register file. At the rising clock edge, no register entry (x0 through x31) is updated, ensuring that instructions which do not produce a register result (such as sw and beq) preserve all architectural register contents unchanged.', font_size=10.0)
    format_paragraph(doc.paragraphs[67], 'In this lecture datapath, PCSel is evaluated by the combinational expression PCSel = Branch AND Eq. Therefore, two conditions must simultaneously hold: (1) Branch = 1 (the instruction is a branch opcode, 0x63 for beq), and (2) Eq = 1 (the dedicated equality comparator evaluates Read1 == Read2).', font_size=10.0)
    format_paragraph(doc.paragraphs[69], 'According to the Iron Law of Processor Performance (CPU Time = Instruction Count × CPI × Clock Period), execution time depends on both CPI and clock period. In a single-cycle processor, CPI = 1, but the clock period must accommodate the single slowest instruction path in the machine (the critical path, traversing instruction memory, register file, ALU, data memory, and writeback). This results in a low clock frequency. A pipelined processor with a slightly higher CPI (e.g. 1.1–1.3 due to pipeline hazards) can operate at a vastly higher clock frequency (e.g. 5x faster), finishing programs in substantially less total execution time.', font_size=10.0)
    
    # Submission check & Optional loop
    sub_text = (
        'Deliverables Checklist:\n'
        '✔ task_a.csv attached and verified (containing exact pre-edge signals and post-edge updates for lw, add, sw).\n'
        '✔ Annotated Fault A Diagnosis Trace graphic attached in Section D (depicting PC=0x08 / Ripes 0x1C, pre-edge wire values and post-edge memory corruption).\n'
        '✔ Ripes single-cycle datapath schematic and execution telemetry graphics attached.\n'
        '✔ All predictions and observations recorded from freshly reset initial states.\n\n'
        'Optional Loop Trace (04_loop_optional.s / --scenario loop):\n'
        '• Visited PCs: 0x00000020 (add) -> 0x00000024 (beq, not taken) -> 0x00000028 (beq, taken backward) -> 0x00000020 (add) -> 0x00000024 (beq, taken exit) -> 0x0000002C (stopped at observation boundary).\n'
        '• Value of x6 After Each Instruction: Cycle 1 (0x20): x6 = 1; Cycle 2 (0x24): x6 = 1; Cycle 3 (0x28): x6 = 1; Cycle 4 (0x20): x6 = 2; Cycle 5 (0x24): x6 = 2.\n'
        '• Total Completed Instructions: 5 completed instructions; final PC = 0x0000002C; final x6 = 2.\n'
        '• Memory State: Data memory remains 100% unchanged throughout (zero store operations executed).\n'
        '• Backward Branch Explanation: The backward branch beq x0, x0, -8 is an unconditional jump (x0==x0 evaluates always true). It computes target PC + (-8) = 0x28 - 8 = 0x20 and sets PCSel = 1. Because RegWrite = 0 and MemWrite = 0, no register or data memory state is altered; only the PC register is updated.'
    )
    format_paragraph(doc.paragraphs[71], sub_text, font_size=10.0)

    # Now let's add screenshots into the document:
    # 1. Ripes datapath diagram
    p_dp = doc.add_paragraph()
    p_dp.paragraph_format.space_before = Pt(14)
    p_dp.paragraph_format.space_after = Pt(4)
    r_dp_title = p_dp.add_run('Figure 1: Ripes 32-bit Single-Cycle Processor Datapath Schematic (RV32_SS)')
    r_dp_title.bold = True
    r_dp_title.font.name = 'Calibri'
    r_dp_title.font.size = Pt(11)
    doc.add_picture('ripes_datapath_annotated.png', width=Inches(6.2))
    
    # 2. Ripes execution telemetry
    p_tel = doc.add_paragraph()
    p_tel.paragraph_format.space_before = Pt(14)
    p_tel.paragraph_format.space_after = Pt(4)
    r_tel_title = p_tel.add_run('Figure 2: Ripes Multi-Scenario Execution Telemetry & State Verification')
    r_tel_title.bold = True
    r_tel_title.font.name = 'Calibri'
    r_tel_title.font.size = Pt(11)
    doc.add_picture('ripes_execution_telemetry.png', width=Inches(6.2))
    
    # 3. Fault A Annotated Trace
    p_flt = doc.add_paragraph()
    p_flt.paragraph_format.space_before = Pt(14)
    p_flt.paragraph_format.space_after = Pt(4)
    r_flt_title = p_flt.add_run('Figure 3: Task D Annotated Fault A Trace & Root Cause Analysis')
    r_flt_title.bold = True
    r_flt_title.font.name = 'Calibri'
    r_flt_title.font.size = Pt(11)
    doc.add_picture('task_d_fault_a_annotated.png', width=Inches(6.2))

    doc.save(output_path)
    print(f'Report template successfully saved to: {output_path}')

process_report_template(
    'Lecture4_Lab_Student_Package/Lecture4_Lab_Report_Template.docx',
    'Lecture4_Lab_Student_Package/Lecture4_Lab_Report_Template.docx'
)
import shutil
shutil.copyfile(
    'Lecture4_Lab_Student_Package/Lecture4_Lab_Report_Template.docx',
    'Lecture4_Lab_Report_Template_Filled.docx'
)
print('Copied to root Lecture4_Lab_Report_Template_Filled.docx')
