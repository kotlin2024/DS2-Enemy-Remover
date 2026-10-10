"""Windows process-memory adapter. Game installation files are read only."""
import ctypes as c
from ctypes import wintypes as w
import hashlib
from pathlib import Path
import struct

class ProcessEntry(c.Structure):
    _fields_ = [('size',w.DWORD),('usage',w.DWORD),('pid',w.DWORD),('heap',c.c_size_t),('module',w.DWORD),('threads',w.DWORD),('parent',w.DWORD),('priority',w.LONG),('flags',w.DWORD),('name',w.WCHAR*260)]

class ModuleEntry(c.Structure):
    _fields_ = [('size',w.DWORD),('id',w.DWORD),('pid',w.DWORD),('global_usage',w.DWORD),('usage',w.DWORD),('base',c.c_void_p),('length',w.DWORD),('module',w.HMODULE),('name',w.WCHAR*256),('path',w.WCHAR*260)]

class NotReady(RuntimeError):
    pass

def kernel():
    k = c.WinDLL('kernel32', use_last_error=True)
    specs = {
        'CreateToolhelp32Snapshot':([w.DWORD,w.DWORD],w.HANDLE),
        'Process32FirstW':([w.HANDLE,c.POINTER(ProcessEntry)],w.BOOL),
        'Process32NextW':([w.HANDLE,c.POINTER(ProcessEntry)],w.BOOL),
        'Module32FirstW':([w.HANDLE,c.POINTER(ModuleEntry)],w.BOOL),
        'Module32NextW':([w.HANDLE,c.POINTER(ModuleEntry)],w.BOOL),
        'OpenProcess':([w.DWORD,w.BOOL,w.DWORD],w.HANDLE),
        'CloseHandle':([w.HANDLE],w.BOOL),
        'GetExitCodeProcess':([w.HANDLE,c.POINTER(w.DWORD)],w.BOOL),
        'ReadProcessMemory':([w.HANDLE,c.c_void_p,c.c_void_p,c.c_size_t,c.POINTER(c.c_size_t)],w.BOOL),
        'WriteProcessMemory':([w.HANDLE,c.c_void_p,c.c_void_p,c.c_size_t,c.POINTER(c.c_size_t)],w.BOOL),
    }
    for name,(args,result) in specs.items():
        getattr(k,name).argtypes=args
        getattr(k,name).restype=result
    return k

def entries(k,flags,pid,cls,first,next_):
    snap=k.CreateToolhelp32Snapshot(flags,pid)
    if snap==c.c_void_p(-1).value:
        raise c.WinError(c.get_last_error())
    try:
        entry=cls(); entry.size=c.sizeof(entry)
        ok=getattr(k,first)(snap,c.byref(entry))
        while ok:
            yield cls.from_buffer_copy(entry)
            ok=getattr(k,next_)(snap,c.byref(entry))
    finally:
        k.CloseHandle(snap)

class Process:
    SHA256='0045931b8914504531b7864a9488d396dc50cbaf524964016e1d69c3d1173131'
    def __init__(self):
        self.k=kernel(); self.handle=None; self.can_write=False
        candidates=[p for p in entries(self.k,2,0,ProcessEntry,'Process32FirstW','Process32NextW') if p.name.lower()=='darksoulsii.exe']
        if not candidates:
            raise NotReady('다크소울 2 실행을 기다리고 있습니다.')
        if len(candidates)!=1:
            raise NotReady('게임이 여러 개 실행 중입니다.')
        self.pid=candidates[0].pid
        mods=list(entries(self.k,0x18,self.pid,ModuleEntry,'Module32FirstW','Module32NextW'))
        module=next(m for m in mods if m.name.lower()=='darksoulsii.exe')
        self.path=Path(module.path); self.base=module.base
        if hashlib.sha256(self.path.read_bytes()).hexdigest()!=self.SHA256:
            raise NotReady('확인한 스콜라 실행 파일과 다른 버전입니다. 연결을 중지했습니다.')
        self.handle=self.k.OpenProcess(0x1010,False,self.pid)
        if not self.handle:
            raise c.WinError(c.get_last_error())
        try:
            # Match the live executable as well as the disk file.
            for rva,expected in [(0x3f5219,b'\x48\x8b\x05'),(0x49d182,bytes.fromhex('48 39 BB C0 00 00 00'))]:
                if self.read(self.base+rva,len(expected))!=expected:
                    raise NotReady('게임 메모리 구조가 다릅니다. 연결을 중지했습니다.')
        except Exception:
            self.close(); raise

    def alive(self):
        code=w.DWORD()
        return bool(self.handle and self.k.GetExitCodeProcess(self.handle,c.byref(code)) and code.value==259)

    def enable_write(self):
        if self.can_write:
            return
        handle=self.k.OpenProcess(0x1038,False,self.pid)
        if not handle:
            raise c.WinError(c.get_last_error())
        self.k.CloseHandle(self.handle); self.handle=handle; self.can_write=True

    def read(self,address,size):
        if not 0x10000<=address<0x7fffffffffff or not 0<size<=4096:
            raise NotReady('유효하지 않은 메모리 주소입니다.')
        buffer=c.create_string_buffer(size); count=c.c_size_t()
        if not self.k.ReadProcessMemory(self.handle,address,buffer,size,c.byref(count)) or count.value!=size:
            raise c.WinError(c.get_last_error())
        return buffer.raw

    def write(self,address,data):
        if not self.can_write or not 0x10000<=address<0x7fffffffffff or not 0<len(data)<=64:
            raise NotReady('메모리 쓰기 조건을 확인할 수 없습니다.')
        buffer=c.create_string_buffer(data); count=c.c_size_t()
        if not self.k.WriteProcessMemory(self.handle,address,buffer,len(data),c.byref(count)) or count.value!=len(data):
            raise c.WinError(c.get_last_error())

    def ptr(self,address):
        return struct.unpack('<Q',self.read(address,8))[0]

    def integer(self,address):
        return struct.unpack('<i',self.read(address,4))[0]

    def close(self):
        if self.handle:
            self.k.CloseHandle(self.handle); self.handle=None
