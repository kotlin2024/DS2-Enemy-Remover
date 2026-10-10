"""Selected AI-node update bypass for the fingerprinted Scholar executable.

Only RAM is patched. Installation/restoration pause game threads briefly.
The trampoline allocation is retained until game exit so an in-flight thread
can finish safely after restoration. No game executable file is edited.
"""
from contextlib import contextmanager
import ctypes as c
from ctypes import wintypes as w
import struct
from winprocess import entries, NotReady

ORIGIN_RVA=0x423397
ORIGINAL=bytes.fromhex('48 8b d7 48 8b cb')
CALL=bytes.fromhex('ff 50 38')
MAX_NODES=4096

class ThreadEntry(c.Structure):
    _fields_=[('size',w.DWORD),('usage',w.DWORD),('tid',w.DWORD),('owner',w.DWORD),
              ('priority',w.LONG),('delta',w.LONG),('flags',w.DWORD)]

def relative_jump(source,target):
    return b'\xe9'+struct.pack('<i',target-source-5)

def assemble(code_address,table_address,origin):
    code=bytearray(); labels={}; fixups=[]
    def emit(data): code.extend(bytes.fromhex(data))
    def branch(op,label):
        emit(op); fixups.append((len(code),label)); code.extend(b'\x00'*4)
    def label(name): labels[name]=len(code)
    emit('9c 50 41 52 41 53')  # flags, rax, r10, r11
    emit('49 ba'); code.extend(struct.pack('<Q',table_address))
    emit('45 8b 1a 45 85 db')  # r11d=count; zero count runs original call
    branch('0f 84','original')
    emit('41 81 fb'); code.extend(struct.pack('<I',MAX_NODES))
    branch('0f 87','original')
    emit('49 83 c2 08')
    label('loop'); emit('49 3b 1a')  # rbx is the AI node, validated read-only
    branch('0f 84','skip')
    emit('49 83 c2 08 41 ff cb')
    branch('0f 85','loop')
    label('original'); emit('41 5b 41 5a 58 9d')
    code.extend(ORIGINAL)
    code.extend(relative_jump(code_address+len(code),origin+6))
    label('skip'); emit('41 5b 41 5a 58 9d')
    code.extend(relative_jump(code_address+len(code),origin+9))
    for offset,name in fixups:
        struct.pack_into('<i',code,offset,labels[name]-offset-4)
    return bytes(code)

class AiHook:
    origin_rva=ORIGIN_RVA
    original=ORIGINAL
    fingerprint=ORIGINAL+CALL
    build_payload=staticmethod(assemble)
    purpose='AI 제어'

    def __init__(self,memory):
        self.memory=memory; self.k=memory.k; self.origin=memory.base+self.origin_rva
        self.allocation=None; self.table=None; self.installed=False; self.jump=None
        self.nodes=()
        specs={
            'VirtualAllocEx':([w.HANDLE,c.c_void_p,c.c_size_t,w.DWORD,w.DWORD],c.c_void_p),
            'VirtualProtectEx':([w.HANDLE,c.c_void_p,c.c_size_t,w.DWORD,c.POINTER(w.DWORD)],w.BOOL),
            'FlushInstructionCache':([w.HANDLE,c.c_void_p,c.c_size_t],w.BOOL),
            'Thread32First':([w.HANDLE,c.POINTER(ThreadEntry)],w.BOOL),
            'Thread32Next':([w.HANDLE,c.POINTER(ThreadEntry)],w.BOOL),
            'OpenThread':([w.DWORD,w.BOOL,w.DWORD],w.HANDLE),
            'SuspendThread':([w.HANDLE],w.DWORD),
            'ResumeThread':([w.HANDLE],w.DWORD),
        }
        for name,(args,result) in specs.items():
            getattr(self.k,name).argtypes=args; getattr(self.k,name).restype=result

    @contextmanager
    def paused(self):
        handles=[]
        try:
            for t in list(entries(self.k,4,0,ThreadEntry,'Thread32First','Thread32Next')):
                if t.owner!=self.memory.pid: continue
                handle=self.k.OpenThread(2,False,t.tid)
                if not handle:
                    if c.get_last_error() in (87,1168): continue  # exited thread
                    raise c.WinError(c.get_last_error())
                if self.k.SuspendThread(handle)==0xffffffff:
                    error=c.get_last_error(); self.k.CloseHandle(handle)
                    raise c.WinError(error)
                handles.append(handle)
            if not handles: raise NotReady('게임 실행 스레드를 확인할 수 없습니다.')
            yield
        finally:
            for handle in reversed(handles):
                self.k.ResumeThread(handle); self.k.CloseHandle(handle)

    def bulk_write(self,address,data):
        for offset in range(0,len(data),64):
            self.memory.write(address+offset,data[offset:offset+64])

    def prepare(self):
        if self.allocation: return
        if self.memory.read(self.origin,len(self.fingerprint))!=self.fingerprint:
            raise NotReady(self.purpose+' 명령이 다르거나 다른 도구가 변경했습니다.')
        self.memory.enable_write()
        start=(self.origin&~0xffff)+0x2000000
        for offset in range(8192):
            address=start+offset*0x10000
            allocation=self.k.VirtualAllocEx(self.memory.handle,address,0x10000,0x3000,0x04)
            if allocation:
                break
        else:
            raise NotReady('AI 제어용 공간을 준비할 수 없습니다.')
        table=allocation+0x1000
        payload=self.build_payload(allocation,table,self.origin)
        self.bulk_write(allocation,payload)
        old=w.DWORD()
        if not self.k.VirtualProtectEx(self.memory.handle,allocation,0x1000,0x20,c.byref(old)):
            raise c.WinError(c.get_last_error())
        if not self.k.FlushInstructionCache(self.memory.handle,allocation,len(payload)):
            raise c.WinError(c.get_last_error())
        self.jump=relative_jump(self.origin,allocation)+b'\x90'*(len(self.original)-5)
        self.allocation=allocation; self.table=table

    def patch(self,expected,replacement):
        with self.paused():
            if self.memory.read(self.origin,len(expected))!=expected:
                raise NotReady(self.purpose+' 명령이 변경되어 덮어쓰지 않았습니다.')
            old=w.DWORD()
            if not self.k.VirtualProtectEx(self.memory.handle,self.origin,len(expected),0x40,c.byref(old)):
                raise c.WinError(c.get_last_error())
            try:
                try:
                    self.memory.write(self.origin,replacement)
                    if self.memory.read(self.origin,len(replacement))!=replacement:
                        raise NotReady(self.purpose+' 명령 기록을 확인하지 못했습니다.')
                    if not self.k.FlushInstructionCache(self.memory.handle,self.origin,len(replacement)):
                        raise c.WinError(c.get_last_error())
                except Exception:
                    self.memory.write(self.origin,expected)
                    self.k.FlushInstructionCache(self.memory.handle,self.origin,len(expected))
                    raise
            finally:
                ignored=w.DWORD()
                self.k.VirtualProtectEx(self.memory.handle,self.origin,len(expected),old.value,c.byref(ignored))

    def set_nodes(self,nodes):
        nodes=tuple(sorted(set(nodes)))
        if len(nodes)>MAX_NODES or any(not 0x10000<=n<0x7fffffffffff for n in nodes):
            raise NotReady('AI 중지 대상이 범위를 벗어났습니다.')
        if not nodes:
            self.close(); return
        self.prepare()
        if self.installed and self.memory.read(self.origin,len(self.original))!=self.jump:
            raise NotReady(self.purpose+' 명령이 외부에서 변경되었습니다.')
        if nodes!=self.nodes:
            # Publish count last; a concurrent reader never sees an oversized
            # list. Both old and new entries have already been validated.
            self.memory.write(self.table,struct.pack('<I',0))
            self.bulk_write(self.table+8,struct.pack('<'+'Q'*len(nodes),*nodes))
            self.memory.write(self.table,struct.pack('<I',len(nodes)))
            self.nodes=nodes
        if not self.installed:
            self.patch(self.original,self.jump); self.installed=True

    def close(self):
        if not self.allocation: return
        if not self.nodes and not self.installed: return
        if not self.memory.alive():
            self.installed=False; self.nodes=(); return
        self.memory.write(self.table,struct.pack('<I',0)); self.nodes=()
        if self.installed:
            self.patch(self.jump,self.original); self.installed=False
