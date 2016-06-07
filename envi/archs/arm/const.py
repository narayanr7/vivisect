MODE_ARM        = 0
MODE_THUMB      = 1
MODE_JAZELLE    = 2
MODE_THUMBEE    = 3

'''
Support for different ARM Instruction set versions
Note that the bit values COULD change as more are added so always use the name when referencing versions
'''
# name          bitmask                    decimal         hex
REV_ARMv4   =   0b0000000000000000000001 #        1        0x1
REV_ARMv4T  =   0b0000000000000000000010 #        2        0x2
REV_ARMv5   =   0b0000000000000000000100 #        4        0x4
REV_ARMv5T  =   0b0000000000000000001000 #        8        0x8
REV_ARMv5E  =   0b0000000000000000010000 #       16        0x10
REV_ARMv5J  =   0b0000000000000000100000 #       32        0x20
REV_ARMv5TE =   0b0000000000000001000000 #       64        0x40
REV_ARMv6   =   0b0000000000000010000000 #      128        0x80
REV_ARMv6T2 =   0b0000000000000100000000 #      256        0x100
REV_ARMv6M  =   0b0000000000001000000000 #      512        0x200
REV_ARMv7A  =   0b0000000000010000000000 #     1024        0x400
REV_ARMv7R  =   0b0000000000100000000000 #     2048        0x800
REV_ARMv7M  =   0b0000000001000000000000 #     4096        0x1000
REV_ARMv7EM =   0b0000000010000000000000 #     8192        0x2000
REV_ARMv8A  =   0b0000000100000000000000 #    16384        0x4000
REV_ARMv8R  =   0b0000001000000000000000 #    32768        0x8000
REV_ARMv8M  =   0b0000010000000000000000 #    65536        0x10000
REVS_ARMv4  = (REV_ARMv4 | REV_ARMv4T)
REVS_ARMv5  = (REV_ARMv5 | REV_ARMv5T | REV_ARMv5E | REV_ARMv5J | REV_ARMv5TE)
REVS_ARMv6  = (REV_ARMv6 | REV_ARMv6T2 | REV_ARMv6M)
REVS_ARMv7  = (REV_ARMv7A | REV_ARMv7R | REV_ARMv7M | REV_ARMv7EM) 
REVS_ARMv8  = (REV_ARMv8A | REV_ARMv8R | REV_ARMv8M)
REV_ALL = (REVS_ARMv4 | REVS_ARMv5 | REVS_ARMv6 | REVS_ARMv7 | REVS_ARMv8)

#Not sure, did from memory , needs to be confirmed
REVT_THUMB16 = (REVS_ARMv5 | REVS_ARMv6)
REVT_THUMB2  = (REVS_ARMv7 | REVS_ARMv8)
REVT_THUMBEE = (REVS_ARMv7 | REVS_ARMv8)

#In progress - Draft version
ARCH_REVS = {
    0:  ['ARMv4',     REV_ARMv4],
    1:  ['ARMv4T',    REV_ARMv4T],
    2:  ['ARMv5',     REV_ARMv5],
    3:  ['ARMv5T',    REV_ARMv5T],
    4:  ['ARMv5E',    REV_ARMv5E],
    5:  ['ARMv5J',    REV_ARMv5J],
    6:  ['ARMv5TE',   REV_ARMv5TE],
    7:  ['REV_ARMv6', REV_ARMv6],
    8:  ['ARMv6T2',   REV_ARMv6T2],
    9:  ['ARMv6M',    REV_ARMv6M],
    10: ['ARMv7A',    REV_ARMv7A],
    11: ['ARMv7R',    REV_ARMv7R],
    12: ['ARMv7M',    REV_ARMv7M],
    13: ['ARMv7EM',   REV_ARMv7EM],
    14: ['ARMv8A',    REV_ARMv8A],
    15: ['ARMv8R',    REV_ARMv8R],
    16: ['ARMv8M',    REV_ARMv8M],
    17: ['ARMALL',    REV_ALL]
}
ARCH_REVSLEN = len(ARCH_REVS) 

#IFLAGS - keep bottom 8-bits for cross-platform flags like envi.IF_NOFALL and envi.IF_BRFALL
IF_PSR_S     = 1<<32     # This DP instruciton can update CPSR
IF_B         = 1<<33     # Byte
IF_H         = 1<<35    # HalfWord
IF_S         = 1<<36    # Signed    #(not to be confused with IF_PSR_S which is the "update status" flag.
IF_D         = 1<<37    # Dword
IF_L         = 1<<38    # Long-store (eg. Dblword Precision) for STC
IF_T         = 1<<39    # Translate for strCCbt
IF_W         = 1<<40    # Write Back for STM/LDM (!)
IF_UM        = 1<<41    # User Mode Registers for STM/LDM (^) (obviously no R15)
IF_TT        = 1<<42    # Flag for STRT/LDRT and STRBT/LDRBT etc

IF_DAIB_SHFT = 56       # shift-bits to get DAIB bits down to 0.  this chops off the "is DAIB present" bit that the following store.
IF_DAIB_MASK = 7<<(IF_DAIB_SHFT-1)
IF_DA        = 1<<(IF_DAIB_SHFT-1)  # Decrement After
IF_IA        = 3<<(IF_DAIB_SHFT-1)  # Increment After
IF_DB        = 5<<(IF_DAIB_SHFT-1)  # Decrement Before
IF_IB        = 7<<(IF_DAIB_SHFT-1)  # Increment Before
IF_DAIB_B    = 5<<(IF_DAIB_SHFT-1)  # Before mask 
IF_DAIB_I    = 3<<(IF_DAIB_SHFT-1)  # Before mask 
IF_THUMB32   = 1<<50    # thumb32
IF_VQ        = 1<<51    # Adv SIMD: operation uses saturating arithmetic
IF_VR        = 1<<52    # Adv SIMD: operation performs rounding
IF_VD        = 1<<53    # Adv SIMD: operation doubles the result
IF_VH        = 1<<54    # Adv SIMD: operation halves the result
IF_SYS_MODE  = 1<<58    # instruction is encoded to be executed in SYSTEM mode, not USER mode
IF_F32       = 1<<59    # F64 SIMD
IF_F64       = 1<<60    # F64 SIMD
IF_F32S32    = 1<<61    # F64 SIMD
IF_F64S32    = 1<<62    # F64 SIMD
IF_F32U32    = 1<<63    # F64 SIMD
IF_F64U32    = 1<<64    # F64 SIMD
IF_F3264     = 1<<65    # F64 SIMD
IF_F6432     = 1<<66    # F64 SIMD
IF_F3216     = 1<<67    # F64 SIMD
IF_F1632     = 1<<68    # F64 SIMD
IF_S32F64    = 1<<69    # F64 SIMD
IF_S32F32    = 1<<70    # F64 SIMD
IF_U32F64    = 1<<71    # F64 SIMD
IF_U32F32    = 1<<72    # F64 SIMD

OF_W         = 1<<8     # Write back to 
OF_UM        = 1<<9     # Usermode, or if r15 included set current SPSR -> CPSR


OSZFMT_BYTE = "B"
OSZFMT_HWORD = "<H"  # Introduced in ARMv4
OSZFMT_WORD = "<I"
OSZ_BYTE = 1
OSZ_HWORD = 2
OSZ_WORD = 4

fmts = [None, OSZ_BYTE, OSZ_HWORD, None, OSZ_WORD]

COND_EQ     = 0x0        # z==1  (equal)
COND_NE     = 0x1        # z==0  (not equal)
COND_CS     = 0x2        # c==1  (carry set/unsigned higher or same)
COND_CC     = 0x3        # c==0  (carry clear/unsigned lower)
COND_MI     = 0x4        # n==1  (minus/negative)
COND_PL     = 0x5        # n==0  (plus/positive or zero)
COND_VS     = 0x6        # v==1  (overflow)
COND_VC     = 0x7        # v==0  (no overflow)
COND_HI     = 0x8        # c==1 and z==0  (unsigned higher)
COND_LO     = 0x9        # c==0  or z==1  (unsigned lower or same)
COND_GE     = 0xA        # n==v  (signed greater than or equal)  (n==1 and v==1) or (n==0 and v==0)
COND_LT     = 0xB        # n!=v  (signed less than)  (n==1 and v==0) or (n==0 and v==1)
COND_GT     = 0xC        # z==0 and n==v (signed greater than)
COND_LE     = 0xD        # z==1 and n!=v (signed less than or equal)
COND_AL     = 0xE        # always
COND_EXTENDED = 0xF        # special case - see conditional 0b1111

cond_codes = {
COND_EQ:"eq", # Equal Z set 
COND_NE:"ne", # Not equal Z clear 
COND_CS:"cs", #/HS Carry set/unsigned higher or same C set 
COND_CC:"cc", #/LO Carry clear/unsigned lower C clear 
COND_MI:"mi", # Minus/negative N set 
COND_PL:"pl", # Plus/positive or zero N clear 
COND_VS:"vs", # Overflow V set 
COND_VC:"vc", # No overflow V clear 
COND_HI:"hi", # Unsigned higher C set and Z clear 
COND_LO:"lo", # Unsigned lower or same C clear or Z set 
COND_GE:"ge", # Signed greater than or equal N set and V set, or N clear and V clear (N == V) 
COND_LT:"lt", # Signed less than N set and V clear, or N clear and V set (N!= V) 
COND_GT:"gt", # Signed greater than Z clear, and either N set and V set, or N clear and V clear (Z == 0,N == V) 
COND_LE:"le", # Signed less than or equal Z set, or N set and V clear, or N clear and V set (Z == 1 or N!= V) 
COND_AL:"", # Always (unconditional) - could be "al" but "" seems better...
COND_EXTENDED:"2", # See extended opcode table
}
cond_map = {
COND_EQ:0,      # Equal Z set 
COND_NE:1, # Not equal Z clear 
COND_CS:2, #/HS Carry set/unsigned higher or same C set 
COND_CC:3, #/LO Carry clear/unsigned lower C clear 
COND_MI:4, # Minus/negative N set 
COND_PL:5, # Plus/positive or zero N clear 
COND_VS:6, # Overflow V set 
COND_VC:7, # No overflow V clear 
COND_HI:8, # Unsigned higher C set and Z clear 
COND_LO:9, # Unsigned lower or same C clear or Z set 
COND_GE:10, # Signed greater than or equal N set and V set, or N clear and V clear (N == V) 
COND_LT:11, # Signed less than N set and V clear, or N clear and V set (N!= V) 
COND_GT:12, # Signed greater than Z clear, and either N set and V set, or N clear and V clear (Z == 0,N == V) 
COND_LE:13, # Signed less than or equal Z set, or N set and V clear, or N clear and V set (Z == 1 or N!= V) 
COND_AL:"", # Always (unconditional) - could be "al" but "" seems better...
COND_EXTENDED:"2", # See extended opcode table
}

PM_usr = 0b10000
PM_fiq = 0b10001
PM_irq = 0b10010
PM_svc = 0b10011
PM_mon = 0b10110
PM_abt = 0b10111
PM_hyp = 0b11010
PM_und = 0b11011
PM_sys = 0b11111

# reg stuff stolen from regs.py to support proc_modes
# these are in context of reg_table, not reg_data.  
#  ie. these are indexes into the lookup table.
REG_OFFSET_USR = 17 * (PM_usr&0xf)
REG_OFFSET_FIQ = 17 * (PM_fiq&0xf)
REG_OFFSET_IRQ = 17 * (PM_irq&0xf)
REG_OFFSET_SVC = 17 * (PM_svc&0xf)
REG_OFFSET_MON = 17 * (PM_mon&0xf)
REG_OFFSET_ABT = 17 * (PM_abt&0xf)
REG_OFFSET_HYP = 17 * (PM_hyp&0xf)
REG_OFFSET_UND = 17 * (PM_und&0xf)
REG_OFFSET_SYS = 17 * (PM_sys&0xf)
#REG_OFFSET_CPSR = 17 * 16
REG_OFFSET_CPSR = 16                    # CPSR is available in every mode, and PM_usr and PM_sys don't have an SPSR.

REG_SPSR_usr = REG_OFFSET_USR + 17
REG_SPSR_fiq = REG_OFFSET_FIQ + 17
REG_SPSR_irq = REG_OFFSET_IRQ + 17
REG_SPSR_svc = REG_OFFSET_SVC + 17
REG_SPSR_mon = REG_OFFSET_MON + 17
REG_SPSR_abt = REG_OFFSET_ABT + 17
REG_SPSR_hyp = REG_OFFSET_HYP + 17
REG_SPSR_und = REG_OFFSET_UND + 17
REG_SPSR_sys = REG_OFFSET_SYS + 17

REG_PC = 0xf
REG_LR = 0xe
REG_SP = 0xd
REG_BP = None
REG_CPSR = REG_OFFSET_CPSR
REG_FLAGS = REG_OFFSET_CPSR    #same location, backward-compat name
REG_EXT_S_FLAG = 0x200000
REG_EXT_D_FLAG = 0x400000

VFP_QWORD_REG_COUNT = 16    # VFPv4-D32

proc_modes = { # mode_name, short_name, description, offset, mode_reg_count, PSR_offset, privilege_level
    PM_usr: ("User Processor Mode", "usr", "Normal program execution mode", REG_OFFSET_USR, 15, REG_SPSR_usr, 0),
    PM_fiq: ("FIQ Processor Mode", "fiq", "Supports a high-speed data transfer or channel process", REG_OFFSET_FIQ, 8, REG_SPSR_fiq, 1),
    PM_irq: ("IRQ Processor Mode", "irq", "Used for general-purpose interrupt handling", REG_OFFSET_IRQ, 13, REG_SPSR_irq, 1),
    PM_svc: ("Supervisor Processor Mode", "svc", "A protected mode for the operating system", REG_OFFSET_SVC, 13, REG_SPSR_svc, 1),
    PM_mon: ("Monitor Processor Mode", "mon", "Secure Monitor Call exception", REG_OFFSET_MON, 13, REG_SPSR_mon, 1),
    PM_abt: ("Abort Processor Mode", "abt", "Implements virtual memory and/or memory protection", REG_OFFSET_ABT, 13, REG_SPSR_abt, 1),
    PM_hyp: ("Hyp Processor Mode", "hyp", "Hypervisor Mode", REG_OFFSET_HYP, 13, REG_SPSR_hyp, 2),
    PM_und: ("Undefined Processor Mode", "und", "Supports software emulation of hardware coprocessor", REG_OFFSET_UND, 13, REG_SPSR_und, 1),
    PM_sys: ("System Processor Mode", "sys", "Runs privileged operating system tasks (ARMv4 and above)", REG_OFFSET_SYS, 15, REG_SPSR_sys, 1),
}

PM_LNAME =  0
PM_SNAME =  1
PM_DESC =   2
PM_REGOFF = 3
PM_REGCNT = 4
PM_PSROFF   = 5
PM_PRIVLVL  = 6

PSR_APSR    = 2
PSR_SPSR    = 1
PSR_CPSR    = 0

INST_ENC_DP_IMM = 0 # Data Processing Immediate Shift
INST_ENC_MISC   = 1 # Misc Instructions

# Instruction encodings in arm v5
IENC_DP_IMM_SHIFT = 0 # Data processing immediate shift
IENC_MISC         = 1 # Miscellaneous instructions
IENC_MISC1        = 2 # Miscellaneous instructions again
IENC_DP_REG_SHIFT = 3 # Data processing register shift
IENC_MULT         = 4 # Multiplies & Extra load/stores
IENC_UNDEF        = 5 # Undefined instruction
IENC_MOV_IMM_STAT = 6 # Move immediate to status register
IENC_DP_IMM       = 7 # Data processing immediate
IENC_LOAD_IMM_OFF = 8 # Load/Store immediate offset
IENC_LOAD_REG_OFF = 9 # Load/Store register offset
IENC_ARCH_UNDEF   = 10 # Architecturally undefined
IENC_MEDIA        = 11 # Media instructions
IENC_LOAD_MULT    = 12 # Load/Store Multiple
IENC_BRANCH       = 13 # Branch
IENC_COPROC_RREG_XFER = 14  # mrrc/mcrr
IENC_COPROC_LOAD  = 15 # Coprocessor load/store and double reg xfers
IENC_COPROC_DP    = 16 # Coprocessor data processing
IENC_COPROC_REG_XFER = 17 # Coprocessor register transfers
IENC_SWINT        = 18 # Sofware interrupts
IENC_UNCOND       = 19 # unconditional wacko instructions
IENC_EXTRA_LOAD   = 20 # extra load/store (swp)
IENC_DP_MOVW      = 21 # 
IENC_DP_MOVT      = 22 # 
IENC_DP_MSR_IMM   = 23 # 
IENC_LOAD_STORE_WORD_UBYTE = 24

IENC_MAX        = 25

# offchutes
IENC_MEDIA_PARALLEL = ((IENC_MEDIA << 8) + 1) << 8
IENC_MEDIA_SAT      = ((IENC_MEDIA << 8) + 2) << 8
IENC_MEDIA_REV      = ((IENC_MEDIA << 8) + 3) << 8
IENC_MEDIA_SEL      = ((IENC_MEDIA << 8) + 4) << 8
IENC_MEDIA_USAD8    = ((IENC_MEDIA << 8) + 5) << 8
IENC_MEDIA_USADA8   = ((IENC_MEDIA << 8) + 6) << 8
IENC_MEDIA_EXTEND   = ((IENC_MEDIA << 8) + 7) << 8
IENC_MEDIA_PACK     = ((IENC_MEDIA << 8) + 8) << 8
IENC_UNCOND_CPS     = ((IENC_UNCOND << 8) + 1) << 8
IENC_UNCOND_SETEND  = ((IENC_UNCOND << 8) + 2) << 8
IENC_UNCOND_PLD     = ((IENC_UNCOND << 8) + 3) << 8
IENC_UNCOND_BLX     = ((IENC_UNCOND << 8) + 4) << 8
IENC_UNCOND_RFE     = ((IENC_UNCOND << 8) + 5) << 8


# The supported types of operand shifts (by the 2 bit field)
S_LSL = 0
S_LSR = 1
S_ASR = 2
S_ROR = 3
S_RRX = 4 # FIXME HACK XXX add this

shift_names = ("lsl", "lsr", "asr", "ror", "rrx")

SOT_REG = 0
SOT_IMM = 1

daib = ("da", "ia", "db", "ib")


def instrenc(encoding, index):
    return (encoding << 16) + index

INS_AND = IENC_DP_IMM_SHIFT << 16
INS_EOR = (IENC_DP_IMM_SHIFT << 16) + 1
INS_SUB = (IENC_DP_IMM_SHIFT << 16) + 2
INS_RSB = (IENC_DP_IMM_SHIFT << 16) + 3
INS_ADD = (IENC_DP_IMM_SHIFT << 16) + 4
INS_ADC = (IENC_DP_IMM_SHIFT << 16) + 5
INS_SBC = (IENC_DP_IMM_SHIFT << 16) + 6
INS_RSC = (IENC_DP_IMM_SHIFT << 16) + 7
INS_TST = (IENC_DP_IMM_SHIFT << 16) + 8
INS_TEQ = (IENC_DP_IMM_SHIFT << 16) + 9
INS_CMP = (IENC_DP_IMM_SHIFT << 16) + 10
INS_CMN = (IENC_DP_IMM_SHIFT << 16) + 11
INS_ORR = (IENC_DP_IMM_SHIFT << 16) + 12
INS_MOV = (IENC_DP_IMM_SHIFT << 16) + 13
INS_BIC = (IENC_DP_IMM_SHIFT << 16) + 14
INS_MVN = (IENC_DP_IMM_SHIFT << 16) + 15
INS_ORN = (IENC_DP_IMM_SHIFT << 16) + 12
INS_ADR = (IENC_DP_IMM_SHIFT << 16) + 16


INS_B       = instrenc(IENC_BRANCH, 0)
INS_BL      = instrenc(IENC_BRANCH, 1)
INS_BCC     = instrenc(IENC_BRANCH, 2)
INS_BX      = instrenc(IENC_MISC, 3)
INS_BXJ     = instrenc(IENC_MISC, 5)
INS_BLX     = IENC_UNCOND_BLX


INS_SWI     = IENC_SWINT


# FIXME: must fit these into the numbering scheme
INS_TB = 85
INS_LDREX = 85
INS_ORN = 85
INS_PKH = 85
INS_LSL = 85
INS_LSR = 85
INS_ASR = 85
INS_ROR = 85
INS_RRX = 85

INS_LDR = instrenc(IENC_LOAD_IMM_OFF,  0)
INS_STR = instrenc(IENC_LOAD_IMM_OFF,  1)


no_update_Rd = (INS_TST, INS_TEQ, INS_CMP, INS_CMN, )

