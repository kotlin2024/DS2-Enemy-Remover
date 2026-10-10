"""Hide/freeze with optional collision and selected AI pause.
No teleport, HP changes or game-file writes.
"""
from dataclasses import dataclass, field
import math
import struct
from winprocess import NotReady

@dataclass
class Saved:
    enemy:object
    context:tuple
    fields:list=field(default_factory=list)

class Remover:
    def __init__(self,memory,disable_collision=False,disable_ai=False,ai_factory=None,
                 disable_lockon=False,lockon_factory=None):
        self.memory=memory
        self.saved={}
        self.disable_collision=disable_collision
        self.disable_ai=disable_ai; self.aihook=None; self.ai_factory=ai_factory
        self.disable_lockon=disable_lockon; self.lockon_hook=None; self.lockon_factory=lockon_factory
        self.skipped_restores=0

    def guarded_write(self,enemy,context,address,data):
        if not self.memory.validate(enemy,context):
            raise NotReady('적 또는 지역이 변경되어 적용을 멈췄습니다.')
        self.memory.write(address,data)

    def capture(self,enemy,context):
        m=self.memory
        if not enemy.action or not enemy.flags:
            raise NotReady('적 제어 구조가 완성되지 않았습니다.')
        saved=Saved(enemy,context)
        # NoDraw 0x40: executable RVA 0x315680 tests [ChrCtrl+0xD8]->flags.
        # NoHit 0x01: SilkySouls2 Offsets.ChrCtrl.NoHit.
        specs=[(enemy.flags,1,None,0x41),
               (enemy.ctrl+0x2a8,4,struct.pack('<f',0),None),
               (enemy.action+0x560,1,b'\x01',None)]
        if self.disable_collision:
            if not enemy.type_ptr:
                raise NotReady('충돌 제어 구조를 확인할 수 없습니다.')
            # CT Permission 18/19=Noclip; DS2S-META Collision setter uses 18.
            permission=m.read(enemy.type_ptr+0x3c,1)[0]
            if permission not in (0,18,19):
                raise NotReady('확인하지 않은 적 충돌 분류입니다.')
            specs.append((enemy.type_ptr+0x3c,1,b'\x12',None))
        for address,size,replacement,mask in specs:
            original=m.read(address,size)
            if address==enemy.action+0x560 and original[0] not in (0,1):
                raise NotReady('적 상태 값이 예상 범위를 벗어났습니다.')
            if address==enemy.ctrl+0x2a8:
                speed=struct.unpack('<f',original)[0]
                if not math.isfinite(speed) or not 0<=speed<=10:
                    raise NotReady('적 속도 값이 예상 범위를 벗어났습니다.')
            if mask is not None:
                replacement=bytes([original[0]|mask])
            saved.fields.append((address,original,replacement,mask))
        return saved

    def apply(self,enemy,context):
        if self.disable_lockon and (self.lockon_hook is None or enemy.ctrl not in self.lockon_hook.nodes):
            raise NotReady('선택한 적의 락온 제외를 먼저 확인해야 합니다.')
        if self.disable_ai and (self.aihook is None or enemy.node not in self.aihook.nodes):
            raise NotReady('선택한 적의 AI 중지를 먼저 확인해야 합니다.')
        if enemy not in self.saved:
            saved=self.capture(enemy,context)
            self.memory.enable_write()
            self.saved[enemy]=saved
        saved=self.saved[enemy]
        for address,original,replacement,mask in saved.fields:
            current=self.memory.read(address,len(original))
            desired=bytes([current[0]|mask]) if mask is not None else replacement
            if current!=desired:
                self.guarded_write(enemy,context,address,desired)

    def restore(self,enemy):
        saved=self.saved.get(enemy)
        if saved is None:
            return True
        if not self.memory.validate(enemy,saved.context):
            del self.saved[enemy]
            self.skipped_restores+=1
            return False
        for address,original,replacement,mask in reversed(saved.fields):
            current=self.memory.read(address,len(original))
            if mask is not None:
                result=bytes([(current[0]&~mask)|(original[0]&mask)])
            elif current==replacement:
                result=original
            else:
                continue
            if current!=result:
                self.guarded_write(enemy,saved.context,address,result)
        del self.saved[enemy]
        return True

    def reconcile(self,context,enemies,selected,param_groups):
        live=set(enemies)
        for enemy in list(self.saved):
            if self.saved[enemy].context!=context or enemy not in live:
                del self.saved[enemy]
                self.skipped_restores+=1
            elif param_groups.get(enemy.param) not in selected:
                self.restore(enemy)
        targets=[e for e in enemies if param_groups.get(e.param) in selected]
        if self.disable_ai or self.disable_lockon:
            if not all(self.memory.validate(e,context) for e in targets):
                raise NotReady('제거 대상 또는 지역이 변경되었습니다.')
        if self.disable_lockon:
            if targets and self.lockon_hook is None:
                if self.lockon_factory is None:
                    from lockon import LockOnHook
                    self.lockon_factory=LockOnHook
                self.lockon_hook=self.lockon_factory(self.memory)
            if self.lockon_hook:
                self.lockon_hook.set_nodes([e.ctrl for e in targets])
        if self.disable_ai:
            if targets and self.aihook is None:
                if self.ai_factory is None:
                    from aihook import AiHook
                    self.ai_factory=AiHook
                self.aihook=self.ai_factory(self.memory)
            if self.aihook:
                self.aihook.set_nodes([e.node for e in targets])
        for enemy in enemies:
            if param_groups.get(enemy.param) in selected:
                self.apply(enemy,context)

    def restore_all(self):
        errors=[]
        for enemy in list(self.saved):
            try:
                self.restore(enemy)
            except Exception as error:
                errors.append(str(error))
        if self.lockon_hook:
            try:
                self.lockon_hook.close()
            except Exception as error:
                errors.append('락온 제외 복원 실패: '+str(error))
        if self.aihook:
            try:
                self.aihook.close()
            except Exception as error:
                errors.append('AI 중지 복원 실패: '+str(error))
        return errors
