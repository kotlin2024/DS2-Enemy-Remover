"""Exclude selected character controllers from the player's lock-on list.

The fingerprinted executable's PlayerLockTargetCtrl::Update builds its target
list at RVA382920. RDI is the validated candidate ChrCtrl; the original test
at RVA3829E7 precedes list insertion. Skipping to RVA382AE9 advances to the next
candidate and lets the engine retire the old target/list normally.
"""
import struct
from aihook import AiHook, MAX_NODES, relative_jump

ORIGIN_RVA=0x3829e7
SKIP_RVA=0x382ae9
ORIGINAL=bytes.fromhex('48 8b 87 d0 00 00 00')
TAIL=bytes.fromhex('f6 00 01 0f 85 f2 00 00 00')


def assemble(code_address,table_address,origin):
    code=bytearray(); labels={}; fixups=[]
    def emit(data): code.extend(bytes.fromhex(data))
    def branch(op,name):
        emit(op); fixups.append((len(code),name)); code.extend(b'\x00'*4)
    def label(name): labels[name]=len(code)
    emit('9c 50 41 52 41 53')  # Preserve flags, RAX, R10 and R11.
    emit('49 ba'); code.extend(struct.pack('<Q',table_address))
    emit('45 8b 1a 45 85 db')
    branch('0f 84','original')
    emit('41 81 fb'); code.extend(struct.pack('<I',MAX_NODES))
    branch('0f 87','original')
    emit('49 83 c2 08')
    label('loop'); emit('49 3b 3a')  # Compare RDI with owned ChrCtrl pointers.
    branch('0f 84','skip')
    emit('49 83 c2 08 41 ff cb'); branch('0f 85','loop')
    label('original'); emit('41 5b 41 5a 58 9d')
    code.extend(ORIGINAL)
    code.extend(relative_jump(code_address+len(code),origin+len(ORIGINAL)))
    label('skip'); emit('41 5b 41 5a 58 9d')
    code.extend(relative_jump(code_address+len(code),origin+SKIP_RVA-ORIGIN_RVA))
    for offset,name in fixups:
        struct.pack_into('<i',code,offset,labels[name]-offset-4)
    return bytes(code)


class LockOnHook(AiHook):
    origin_rva=ORIGIN_RVA
    original=ORIGINAL
    fingerprint=ORIGINAL+TAIL
    build_payload=staticmethod(assemble)
    purpose='락온 제외 제어'
