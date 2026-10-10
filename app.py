"""Native desktop front end. Applying is always off on launch."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import sys
import tempfile
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from controller import Controller
from cuteui import CuteLayout

RESOURCES=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
HOME=Path(os.environ.get('LOCALAPPDATA',str(Path.home())))/'DS2EnemySelector'

class App(CuteLayout):
    def __init__(self,root,controller):
        super().__init__(root,controller,RESOURCES)

    def select(self):
        self.controller.select({k for k,v in self.vars.items() if v.get()})
        for row in self.rows.values(): row.paint()
        self.refresh_button()

    def clear(self):
        for v in self.vars.values(): v.set(False)
        self.select()

    def filter(self,*_):
        if not hasattr(self,'canvas'): return
        state=self.controller.snapshot()
        self.layout_cards(state,self.search.get().strip().casefold(),self.only.get(),self.phobia.get(),self.annoying.get())

    def refresh_button(self):
        s=self.controller.snapshot()
        self.toggle.configure(text='적용 중지 · 복원 (F8)' if s['enabled'] else '선택한 적 제거 시작',state='normal' if s['enabled'] or (s['ready'] and self.offline.get() and s['selected']) else 'disabled')

    def toggle_apply(self):
        s=self.controller.snapshot()
        if s['enabled']: self.controller.set_enabled(False)
        elif s['ready'] and self.offline.get() and s['selected']: self.controller.set_enabled(True)
        self.refresh_button()

    def update(self):
        if self.closing: return
        pressed=bool(self.user32.GetAsyncKeyState(0x77)&0x8000)
        if pressed and not self.key_down:
            self.controller.set_enabled(False)
        self.key_down=pressed
        s=self.controller.snapshot()
        message=s['message']
        if s['restoration_error']: message+=' / '+s['restoration_error']
        self.status.set(message)
        self.chosen.set(str(len(s['selected'])))
        self.live_counts.set(f"현재 지역 {s['loaded']}개체  ·  적용 중 {s['active']}개체")
        self.summary.set(f"선택 {len(s['selected'])}종 · 현재 적 {s['loaded']}개체 · 적용 {s['active']}개체")
        for group,row in self.rows.items():
            row.set_count(s['counts'].get(group,0))
        self.filter(); self.refresh_button(); self.root.after(400,self.update)

    def close(self):
        self.closing=True; self.controller.close(); self.root.destroy()

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--smoke-test',type=Path); args=parser.parse_args()
    ctypes.windll.user32.SetProcessDPIAware()
    root=tk.Tk()
    if args.smoke_test:
        # No worker is started, so this UI check never opens the game process.
        with tempfile.TemporaryDirectory() as temp:
            c=Controller(RESOURCES,temp); app=App(root,c); root.update()
            args.smoke_test.write_text(json.dumps({'ui_created':True,'catalog_groups':len(c.catalog),'apply_disabled':str(app.toggle.cget('state'))=='disabled','worker_started':c.thread is not None},indent=2),encoding='utf-8')
            app.close()
    else:
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.CreateMutexW.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_wchar_p]
        kernel.CreateMutexW.restype=ctypes.c_void_p
        kernel.CloseHandle.argtypes=[ctypes.c_void_p]
        mutex=kernel.CreateMutexW(None,False,'Local\\DS2EnemySelectorBeta')
        if not mutex or ctypes.get_last_error()==183:
            messagebox.showinfo('이미 실행 중','이미 실행 중인 적 선택 도구를 사용하세요.',parent=root)
            if mutex: kernel.CloseHandle(mutex)
            root.destroy(); return
        try:
            c=Controller(RESOURCES,HOME); app=App(root,c); c.start(); root.mainloop()
        finally:
            kernel.CloseHandle(mutex)

if __name__=='__main__': main()
