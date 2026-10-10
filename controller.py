from collections import Counter
import json
from pathlib import Path
import threading
import time
from catalog import load_catalog
from memory import GameMemory, Loading
from removal import Remover
from winprocess import NotReady

class Controller:
    def __init__(self,resources,home,adapter=GameMemory):
        self.resources=Path(resources); self.home=Path(home); self.home.mkdir(parents=True,exist_ok=True)
        self.adapter=adapter
        self.catalog=load_catalog(resources)
        self.groups={p:k for k,v in self.catalog.items() for p in v['params']}
        self.selected=set(); self.language='ko'; self.enabled=False; self.export_requested=False
        self.memory=None; self.remover=None; self.last_context=None; self.context_since=0
        self.stop=threading.Event(); self.lock=threading.RLock()
        self.state={'message':'게임 연결을 기다리고 있습니다.','counts':{},'active':0,'loaded':0,'ready':False,'map':None,'restoration_error':None,'last_restore_skipped':0}
        self.load_settings(); self.thread=None

    def load_settings(self):
        try:
            settings=json.loads((self.home/'settings.json').read_text('utf-8'))
            if not isinstance(settings,dict) or not isinstance(settings.get('selected',[]),list):
                return
            self.selected={str(k) for k in settings.get('selected',[]) if str(k) in self.catalog}
            self.language=settings.get('language') if settings.get('language') in ('ko','en') else 'ko'
        except (OSError,ValueError,TypeError):
            pass

    def select(self,selected):
        with self.lock:
            self.selected=set(selected)&set(self.catalog)
            self.save_settings()

    def save_settings(self):
        data=json.dumps({'selected':sorted(self.selected),'language':self.language},ensure_ascii=False,indent=2)
        temp=self.home/'settings.tmp'; temp.write_text(data,encoding='utf-8'); temp.replace(self.home/'settings.json')

    def set_language(self,language):
        if language not in ('ko','en'): raise ValueError('Unsupported UI language')
        with self.lock:
            self.language=language; self.save_settings()

    def set_enabled(self,enabled):
        with self.lock:
            self.enabled=bool(enabled)

    def snapshot(self):
        with self.lock:
            return {**self.state,'selected':list(self.selected),'enabled':self.enabled,'language':self.language}

    def export(self):
        with self.lock:
            self.export_requested=True

    def start(self):
        self.thread=threading.Thread(target=self.run,name='DS2 memory worker',daemon=False)
        self.thread.start()

    def disconnect(self):
        if self.remover:
            errors=self.remover.restore_all()
            self.state['last_restore_skipped']=self.remover.skipped_restores
            if errors:
                self.state['restoration_error']='복원을 완료하지 못했습니다. 게임을 다시 실행해 주세요.'
            self.remover=None
        if self.memory:
            self.memory.close(); self.memory=None
        self.last_context=None

    def run(self):
        try:
            while not self.stop.is_set():
                try:
                    if self.memory is None:
                        self.memory=self.adapter()
                        self.remover=Remover(self.memory,disable_collision=True,disable_ai=True,disable_lockon=True)
                    context,enemies=self.memory.snapshot()
                    now=time.monotonic()
                    if context!=self.last_context:
                        if self.last_context is not None:
                            if self.remover.restore_all():
                                raise RuntimeError('지역 이동 중 복원 확인 실패 · 게임을 다시 실행해 주세요.')
                            self.remover=Remover(self.memory,disable_collision=True,disable_ai=True,disable_lockon=True)
                        self.last_context=context; self.context_since=now
                    counts=Counter(self.groups.get(e.param) for e in enemies)
                    counts.pop(None,None)
                    with self.lock:
                        enabled=self.enabled; selected=set(self.selected)
                        export=self.export_requested; self.export_requested=False
                    stable=now-self.context_since>=2
                    if enabled and stable:
                        self.remover.reconcile(context,enemies,selected,self.groups)
                    elif not enabled:
                        errors=self.remover.restore_all()
                        if errors:
                            self.state['restoration_error']='복원 확인 실패 · 게임을 다시 실행해 주세요.'
                    if export:
                        data={'pid':self.memory.pid,'context':context,'read_only_snapshot':True,
                              'enemies':[dict(param=e.param,group=self.groups.get(e.param),hp=self.memory.integer(e.ctrl+0x168),coords=self.memory.coords(e)) for e in enemies]}
                        (self.home/'diagnostic.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
                    with self.lock:
                        message=('숨김·충돌 해제·AI 중지·락온 제외 적용 중' if stable else '새 지역 연결 확인 중 · 안정되면 자동 적용') if enabled else '연결됨 · 적용 대기'
                        self.state.update(message=message,counts=dict(counts),active=len(self.remover.saved),loaded=len(enemies),ready=True,map=context[3])
                except Loading as error:
                    # Retain the user's intent only inside the same live process.
                    # Never retain old enemy pointers across a world transition.
                    errors=self.remover.restore_all() if self.remover else []
                    if self.remover:
                        self.state['last_restore_skipped']=self.remover.skipped_restores
                    alive=self.memory is not None and self.memory.alive()
                    self.last_context=None; self.context_since=0
                    if alive and not errors:
                        self.remover=Remover(self.memory,disable_collision=True,disable_ai=True,disable_lockon=True)
                        with self.lock:
                            message='로딩 중 · 연결이 안정되면 자동으로 다시 적용합니다.' if self.enabled else str(error)
                            self.state.update(message=message,ready=False,active=0,counts={},loaded=0,map=None)
                    else:
                        with self.lock:
                            self.enabled=False
                            if errors:
                                self.state['restoration_error']='복원 확인 실패 · 게임을 다시 실행해 주세요.'
                            self.state.update(message='게임 종료 또는 복원 오류로 적용을 중지했습니다.',ready=False,active=0,counts={},loaded=0)
                        self.disconnect()
                except (OSError,NotReady,ValueError,RuntimeError) as error:
                    with self.lock:
                        self.enabled=False
                        self.state.update(message=str(error),ready=False,active=0,counts={},loaded=0)
                    self.disconnect()
                except Exception as error:
                    with self.lock:
                        self.enabled=False
                        self.state.update(message=f'오류로 중지: {error}',ready=False)
                    self.disconnect()
                self.stop.wait(0.25)
        finally:
            self.disconnect()

    def close(self):
        self.stop.set()
        if self.thread:
            self.thread.join(5)
