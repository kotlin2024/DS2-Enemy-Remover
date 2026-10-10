"""DS2 Scholar 1.03 adapter. Offsets cross-checked with SilkySouls2."""
from dataclasses import dataclass
import math
import struct
from winprocess import Process, NotReady

class Loading(NotReady):
    """Temporary world transition in the same running game process."""
    pass

@dataclass(frozen=True)
class Enemy:
    node:int
    ctrl:int
    param:int
    param_ptr:int
    flags:int
    action:int
    physics:int
    position:int
    type_ptr:int=0

class GameMemory(Process):
    def context(self):
        if not self.alive():
            raise NotReady('게임이 종료되었습니다.')
        manager=self.ptr(self.base+0x16148f0)
        if not manager or self.integer(manager+0x24ac)!=30:
            raise Loading('캐릭터 또는 지역 로딩을 기다리고 있습니다.')
        player=self.ptr(manager+0xd0)
        ai=self.ptr(manager+0x28)
        map_id=self.integer(self.base+0x156d1c4)
        if not player or not ai or self.integer(player+0x168)<=0:
            raise Loading('캐릭터가 살아 있는 플레이 화면을 기다리고 있습니다.')
        return manager,player,ai,map_id

    def identity(self,node):
        ctrl=self.ptr(node+0x38)
        param_ptr=self.ptr(ctrl+0x38)
        param=self.integer(param_ptr+4)
        if not 0<param<2000000:
            raise NotReady('적 종류를 확인할 수 없습니다.')
        return Enemy(node,ctrl,param,param_ptr,self.ptr(ctrl+0xd8),self.ptr(ctrl+0xb8),
                     self.ptr(ctrl+0x100),self.ptr(ctrl+0xc8),self.ptr(ctrl+0xb0))

    def snapshot(self):
        context=self.context()
        node=self.ptr(context[2]+0x10)
        seen=set(); result=[]
        while node:
            if node in seen or len(seen)>=4096:
                raise NotReady('적 목록이 변경 중이거나 범위를 벗어났습니다.')
            seen.add(node)
            next_node=self.ptr(node+0x10)
            try:
                enemy=self.identity(node)
                if enemy.ctrl!=context[1]:
                    hp=self.integer(enemy.ctrl+0x168)
                    if 0<hp<10000000:
                        result.append(enemy)
            except (OSError,NotReady):
                # Never apply to unknown or half-initialized entries.
                pass
            node=next_node
        if context!=self.context():
            raise Loading('지역이 변경 중입니다.')
        return context,result

    def validate(self,enemy,context):
        try:
            return self.context()==context and enemy.ctrl!=context[1] and self.identity(enemy.node)==enemy and self.integer(enemy.ctrl+0x168)>0
        except (OSError,NotReady):
            return False

    def coords(self,enemy):
        coords=struct.unpack('<4f',self.read(enemy.ctrl+0x90,16))
        if not all(math.isfinite(x) and abs(x)<1000000 for x in coords):
            raise NotReady('적 좌표를 확인할 수 없습니다.')
        return coords
