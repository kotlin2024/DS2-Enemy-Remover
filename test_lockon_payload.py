"""CPU tests for selected-controller exclusion and preserved machine state."""
from pathlib import Path
import struct
import unittest
from unicorn import Uc, UC_ARCH_X86, UC_MODE_64, UC_HOOK_CODE
from unicorn.x86_const import *
from lockon import assemble, MAX_NODES, ORIGIN_RVA, SKIP_RVA, ORIGINAL

class LockOnPayloadTests(unittest.TestCase):
    def execute(self,targets,count=None):
        code=0x100000; table=0x101000; origin=0x200000; candidate=0x400000
        uc=Uc(UC_ARCH_X86,UC_MODE_64)
        for address,size in ((code,0x10000),(origin,0x1000),(0x300000,0x10000),(candidate,0x1000)):
            uc.mem_map(address,size)
        uc.mem_write(code,assemble(code,table,origin))
        uc.mem_write(table,struct.pack('<II',len(targets) if count is None else count,0)+b''.join(struct.pack('<Q',t) for t in targets))
        status=0xabcdef00
        uc.mem_write(candidate+0xd0,struct.pack('<Q',status))
        before={UC_X86_REG_RAX:0x11111111,UC_X86_REG_RBX:0x22222222,UC_X86_REG_RCX:0x33333333,
                UC_X86_REG_RDX:0x44444444,UC_X86_REG_RDI:candidate,UC_X86_REG_R10:0x66666666,
                UC_X86_REG_R11:0x77777777,UC_X86_REG_RSP:0x308000,UC_X86_REG_EFLAGS:0x247}
        for reg,value in before.items(): uc.reg_write(reg,value)
        endpoint=[]; skip_at=origin+SKIP_RVA-ORIGIN_RVA
        def stop(uc,address,size,_):
            if address in (origin+len(ORIGINAL),skip_at):
                endpoint.append(address); uc.emu_stop()
        uc.hook_add(UC_HOOK_CODE,stop)
        uc.emu_start(code,origin+0x1000,count=50000)
        self.assertEqual(len(endpoint),1)
        skipped=endpoint[0]==skip_at
        for reg,value in before.items():
            if reg==UC_X86_REG_RAX and not skipped: value=status
            self.assertEqual(uc.reg_read(reg),value,f'register {reg}')
        return skipped
    def test_selected_controller_is_excluded(self): self.assertTrue(self.execute([0x400000]))
    def test_unselected_controller_runs_original(self): self.assertFalse(self.execute([0x500000]))
    def test_empty_list_runs_original(self): self.assertFalse(self.execute([]))
    def test_maximum_table_last_match(self): self.assertTrue(self.execute(list(range(0x10000,0x10000+MAX_NODES-1))+[0x400000]))
    def test_invalid_count_fails_open(self): self.assertFalse(self.execute([],MAX_NODES+1))

if __name__=='__main__': unittest.main()
