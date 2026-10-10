import struct
import unittest
import tempfile
from pathlib import Path
from controller import Controller
from catalog import load_catalog
from memory import Enemy
from removal import Remover

class FakeMemory:
    def __init__(self,e):
        self.data={e.flags:b'\x12',e.ctrl+0x2a8:struct.pack('<f',1),e.action+0x560:b'\x00'}
        self.data[e.type_ptr+0x3c]=b'\x00'
        self.valid=True; self.writes=[]; self.writable=False; self.fail=None
    def read(self,a,n): return self.data[a]
    def enable_write(self): self.writable=True
    def validate(self,e,c): return self.valid
    def write(self,a,b):
        if a==self.fail: self.fail=None; raise OSError('simulated write failure')
        assert self.writable
        self.writes.append((a,b)); self.data[a]=b

class RemovalTests(unittest.TestCase):
    def setUp(self):
        self.e=Enemy(100,1000,210000,2000,3000,4000,5000,6000,7000)
        self.m=FakeMemory(self.e); self.r=Remover(self.m); self.context=(1,2,3,4)
        self.original=dict(self.m.data)
    def test_selected_only_and_restore_deselected(self):
        self.r.reconcile(self.context,[self.e],{'203'},{210000:'210'})
        self.assertEqual(self.m.writes,[])
        self.r.reconcile(self.context,[self.e],{'210'},{210000:'210'})
        self.assertEqual(self.m.data[self.e.flags],b'\x53')
        self.assertEqual(self.m.data[self.e.ctrl+0x2a8],struct.pack('<f',0))
        self.r.reconcile(self.context,[self.e],set(),{210000:'210'})
        self.assertEqual(self.m.data,self.original)
    def test_mask_preserves_other_game_flags(self):
        self.r.apply(self.e,self.context)
        self.m.data[self.e.flags]=b'\xd3'
        self.r.restore(self.e)
        self.assertEqual(self.m.data[self.e.flags],b'\x92')
    def test_invalid_identity_never_written_on_restore(self):
        self.r.apply(self.e,self.context); count=len(self.m.writes); self.m.valid=False
        self.assertFalse(self.r.restore(self.e))
        self.assertEqual(len(self.m.writes),count)
    def test_partial_apply_failure_remains_restorable(self):
        self.m.fail=self.e.ctrl+0x2a8
        with self.assertRaises(OSError): self.r.apply(self.e,self.context)
        self.assertEqual(self.r.restore_all(),[])
        self.assertEqual(self.m.data,self.original)
    def test_does_not_overwrite_external_speed_change(self):
        self.r.apply(self.e,self.context)
        changed=struct.pack('<f',0.5); self.m.data[self.e.ctrl+0x2a8]=changed
        self.r.restore(self.e)
        self.assertEqual(self.m.data[self.e.ctrl+0x2a8],changed)
    def test_unknown_variant_excluded(self):
        self.r.reconcile(self.context,[self.e],{'210'},{210100:'210'})
        self.assertEqual(self.m.writes,[])
    def test_only_three_fields_changed(self):
        self.r.apply(self.e,self.context)
        self.assertEqual({a for a,b in self.m.writes},set(self.original)-{self.e.type_ptr+0x3c})
    def test_settings_never_resume_memory_writes(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as home:
            resources=Path(__file__).parent
            c=Controller(resources,home); c.select({'210'})
            c.set_enabled(True)
            reopened=Controller(resources,home)
            self.assertEqual(reopened.selected,{'210'})
            self.assertFalse(reopened.enabled)
            self.assertIsNone(reopened.memory)
    def test_live_scholar_base_variants_and_boss_exclusion(self):
        catalog=load_catalog(Path(__file__).parent)
        groups={p:k for k,v in catalog.items() for p in v['params']}
        self.assertEqual(groups[301000],'301')
        self.assertEqual(groups[125000],'125')
        self.assertNotIn(212000,groups)
        self.assertNotIn(309600,groups)
        self.assertNotIn(309700,groups)
    def test_collision_restored_before_enemy_unfrozen(self):
        r=Remover(self.m,disable_collision=True)
        r.apply(self.e,self.context)
        self.assertEqual(self.m.data[self.e.type_ptr+0x3c],b'\x12')
        self.m.writes=[]
        r.restore(self.e)
        self.assertEqual(self.m.writes[0],(self.e.type_ptr+0x3c,b'\x00'))
        self.assertEqual(self.m.data,self.original)
    def test_unknown_collision_class_never_written(self):
        self.m.data[self.e.type_ptr+0x3c]=b'\xff'
        r=Remover(self.m,disable_collision=True)
        with self.assertRaises(RuntimeError): r.apply(self.e,self.context)
        self.assertEqual(self.m.writes,[])
    def test_ai_and_collision_restored_on_shutdown(self):
        outer=self
        class Hook:
            def __init__(self,memory): self.nodes=(); self.closed=False
            def set_nodes(self,nodes): self.nodes=tuple(nodes)
            def close(self):
                outer.assertEqual(outer.m.data,outer.original)
                self.nodes=(); self.closed=True
        r=Remover(self.m,disable_collision=True,disable_ai=True,ai_factory=Hook)
        r.reconcile(self.context,[self.e],{'210'},{210000:'210'})
        self.assertEqual(r.aihook.nodes,(self.e.node,))
        self.assertEqual(r.restore_all(),[])
        self.assertTrue(r.aihook.closed)
    def test_ai_required_before_direct_apply(self):
        r=Remover(self.m,disable_ai=True)
        with self.assertRaises(RuntimeError): r.apply(self.e,self.context)
        self.assertEqual(self.m.writes,[])
    def test_lockon_exclusion_required_before_hide(self):
        r=Remover(self.m,disable_lockon=True)
        with self.assertRaises(RuntimeError): r.apply(self.e,self.context)
        self.assertEqual(self.m.writes,[])
    def test_lockon_uses_selected_controllers_and_clears_on_deselect(self):
        class Hook:
            def __init__(self,m): self.nodes=(); self.closed=False
            def set_nodes(self,nodes): self.nodes=tuple(nodes)
            def close(self): self.nodes=(); self.closed=True
        r=Remover(self.m,disable_lockon=True,lockon_factory=Hook)
        r.reconcile(self.context,[self.e],{'210'},{self.e.param:'210'})
        self.assertEqual(r.lockon_hook.nodes,(self.e.ctrl,))
        self.assertNotEqual(r.lockon_hook.nodes,(self.e.node,))
        r.reconcile(self.context,[self.e],set(),{self.e.param:'210'})
        self.assertEqual(r.lockon_hook.nodes,())
        self.assertEqual(self.m.data,self.original)
        self.assertEqual(r.restore_all(),[])
        self.assertTrue(r.lockon_hook.closed)
    def test_lockon_install_failure_leaves_enemy_unchanged(self):
        class Hook:
            def __init__(self,m): self.nodes=()
            def set_nodes(self,nodes): raise OSError('simulated hook failure')
            def close(self): pass
        r=Remover(self.m,disable_lockon=True,lockon_factory=Hook)
        with self.assertRaises(OSError):
            r.reconcile(self.context,[self.e],{'210'},{self.e.param:'210'})
        self.assertEqual(self.m.writes,[])
        self.assertEqual(r.restore_all(),[])
    def test_ai_restore_still_runs_if_lockon_cleanup_fails(self):
        class LockHook:
            def close(self): raise OSError('simulated lock cleanup failure')
        class Ai:
            closed=False
            def close(self): self.closed=True
        r=Remover(self.m); r.lockon_hook=LockHook(); r.aihook=Ai()
        self.assertEqual(len(r.restore_all()),1)
        self.assertTrue(r.aihook.closed)
    def test_unloaded_entity_reported_as_skipped_without_stale_write(self):
        self.r.apply(self.e,self.context)
        count=len(self.m.writes); self.m.valid=False
        self.assertEqual(self.r.restore_all(),[])
        self.assertEqual(self.r.skipped_restores,1)
        self.assertEqual(len(self.m.writes),count)

if __name__=='__main__': unittest.main()
