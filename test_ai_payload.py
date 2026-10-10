"""Execute actual trampoline bytes in an isolated x64 CPU emulator."""
from pathlib import Path
import struct
import unittest
from unicorn import Uc, UC_ARCH_X86, UC_MODE_64, UC_HOOK_CODE
from unicorn.x86_const import *
from aihook import assemble, MAX_NODES

class PayloadTests(unittest.TestCase):
    def execute(self,nodes,count=None):
        code=0x100000; table=0x101000; origin=0x200000
        uc=Uc(UC_ARCH_X86,UC_MODE_64)
        uc.mem_map(code,0x10000); uc.mem_map(origin,0x1000); uc.mem_map(0x300000,0x10000)
        uc.mem_write(code,assemble(code,table,origin))
        uc.mem_write(table,struct.pack('<II',len(nodes) if count is None else count,0)+b''.join(struct.pack('<Q',n) for n in nodes))
        before={UC_X86_REG_RAX:0x11111111,UC_X86_REG_RBX:0x55667788,UC_X86_REG_RCX:0x22222222,
                UC_X86_REG_RDX:0x33333333,UC_X86_REG_RDI:0x44444444,UC_X86_REG_R10:0x66666666,
                UC_X86_REG_R11:0x77777777,UC_X86_REG_RSP:0x308000,UC_X86_REG_EFLAGS:0x247}
        for reg,value in before.items(): uc.reg_write(reg,value)
        endpoint=[]
        def stop(uc,address,size,_):
            if address in (origin+6,origin+9):
                endpoint.append(address); uc.emu_stop()
        uc.hook_add(UC_HOOK_CODE,stop)
        uc.emu_start(code,origin+0x100,count=50000)
        self.assertEqual(len(endpoint),1)
        skip=endpoint[0]==origin+9
        for reg,value in before.items():
            if reg==UC_X86_REG_RCX and not skip: value=before[UC_X86_REG_RBX]
            if reg==UC_X86_REG_RDX and not skip: value=before[UC_X86_REG_RDI]
            self.assertEqual(uc.reg_read(reg),value,f'register {reg}')
        return skip
    def test_empty_list_runs_original(self): self.assertFalse(self.execute([]))
    def test_selected_node_skips_ai_call(self): self.assertTrue(self.execute([0x55667788]))
    def test_other_node_runs_original(self): self.assertFalse(self.execute([0x99999999]))
    def test_maximum_list_last_match(self): self.assertTrue(self.execute(list(range(0x10000,0x10000+MAX_NODES-1))+[0x55667788]))
    def test_bad_count_runs_original_without_scanning(self): self.assertFalse(self.execute([],MAX_NODES+1))

if __name__=='__main__': unittest.main()
