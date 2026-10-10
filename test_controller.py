"""Exercise loading/resume and stop/error boundaries without a game process."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from controller import Controller
from memory import Loading
from winprocess import NotReady

class Stop:
    def __init__(self, count, callback=None):
        self.count=count; self.step=0; self.callback=callback
    def is_set(self): return self.step>=self.count
    def wait(self, _):
        self.step+=1
        if self.callback: self.callback(self.step)

class FakeMemory:
    def __init__(self, samples): self.samples=iter(samples); self.live=True
    def snapshot(self):
        value=next(self.samples)
        if isinstance(value,Exception): raise value
        return value, []
    def alive(self): return self.live
    def close(self): pass

class FakeRemover:
    applied=[]; fail=False
    def __init__(self,*_,**__): self.saved={}; self.skipped_restores=0
    def restore_all(self): return ['failure'] if self.fail else []
    def reconcile(self,context,*_): self.applied.append(context)

class LoadingTests(unittest.TestCase):
    A=(1,2,3,4); B=(5,6,7,8)
    def run_controller(self,samples,stop_at=None,fail=False):
        FakeRemover.applied=[]; FakeRemover.fail=fail
        with tempfile.TemporaryDirectory() as home:
            memory=FakeMemory(samples)
            c=Controller(Path(__file__).parent,home,adapter=lambda:memory)
            c.set_enabled(True)
            c.stop=Stop(len(samples),lambda step: c.set_enabled(False) if step==stop_at else None)
            with patch('controller.Remover',FakeRemover),patch('controller.time.monotonic',side_effect=range(100)):
                c.run()
            return c, list(FakeRemover.applied)
    def test_loading_resumes_only_after_new_context_stable(self):
        c,applied=self.run_controller([self.A]*3+[Loading('loading')]+[self.B]*3)
        self.assertEqual(applied,[self.A,self.B]); self.assertTrue(c.enabled)
    def test_direct_region_change_waits_again(self):
        _,applied=self.run_controller([self.A]*3+[self.B]*3)
        self.assertEqual(applied,[self.A,self.B])
    def test_f8_during_loading_cancels_resume(self):
        c,applied=self.run_controller([self.A]*3+[Loading('loading')]+[self.B]*3,stop_at=4)
        self.assertEqual(applied,[self.A]); self.assertFalse(c.enabled)
    def test_access_error_disables_resume(self):
        c,applied=self.run_controller([self.A]*3+[OSError('read failure')]+[self.B]*3)
        self.assertEqual(applied,[self.A]); self.assertFalse(c.enabled)
    def test_game_exit_disables_resume(self):
        c,applied=self.run_controller([self.A]*3+[NotReady('game exited')]+[self.B]*3)
        self.assertEqual(applied,[self.A]); self.assertFalse(c.enabled)
    def test_restore_failure_disables_resume(self):
        c,applied=self.run_controller([self.A,Loading('loading')]+[self.B]*3,fail=True)
        self.assertEqual(applied,[]); self.assertFalse(c.enabled)
        self.assertIsNotNone(c.state['restoration_error'])

if __name__=='__main__': unittest.main()
