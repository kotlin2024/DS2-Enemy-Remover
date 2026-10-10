"""Bilingual presentation; enemy English names come from English source data."""
import json
import re
from pathlib import Path

EN = {
 '편안한 드랭글레이그 · 다크소울 2 적 선택 (불편한 몬스터 필터)':'A Calmer Drangleic · DS2 Enemy Selector',
 '조금 더 편안한 드랭글레이그':'A calmer Drangleic',
 '마주치고 싶지 않은 몬스터를 골라 주세요.':'Choose the enemies you would rather skip.',
 '실시간 적용  ·  보스와 NPC는 선택 목록에서 제외':'Live controls · Bosses and NPCs excluded',
 '몬스터 검색':'Search enemies',
 '현재 지역에서 발견된 종류만 보기':'Only show enemies found in this area',
 '귀여운 그림 표시':'Show cute illustrations',
 '공포증 관련':'Phobia-related',
 '짜증 유발 몬스터':'Frustrating enemies',
 '커뮤니티에서 자주 언급된 14종 · 필터는 목록만 좁혀 줍니다.\n두 분류를 함께 체크하면 두 목록을 모두 표시합니다.':'14 families often mentioned by players. Filters only narrow the list.\nEnable both categories to show their combined list.',
 '검색 조건에 맞는 몬스터가 없습니다.':'No enemies match your filters.',
 '게임 연결':'Game connection', '선택한 몬스터':'Selected enemies',
 '종 선택':'families selected', '선택 해제':'Clear selection',
 '게임에 적용하기':'Apply to the game',
 '게임을 오프라인으로 실행했습니다':'My game is running offline',
 '선택한 적 제거 시작':'Start hiding selected enemies',
 '적용 중지 · 복원 (F8)':'Stop & restore (F8)',
 'F8  ·  적용 중지와 복원':'F8 · Stop and restore',
 '게임 화면에서도 사용할 수 있습니다.\n복원 전에 적과 거리를 두세요.':'Works while you are in the game.\nMove away from enemies before restoring them.',
 '진단 저장':'Save diagnostics',
 '시험판 · 장시간 사용은 미검증':'Beta · Long sessions have not been verified',
 '그림은 종류를 나타내는 귀여운 아이콘입니다. 실제 게임 모습과 다를 수 있습니다.  ·  개발자 HJP':'Illustrations represent enemy families and may differ from the game. · Developed by HJP',
 '이미 실행 중':'Already running',
 '이미 실행 중인 적 선택 도구를 사용하세요.':'Please use the enemy selector that is already open.',
 '게임 연결을 기다리고 있습니다.':'Waiting for the game connection.',
 '다크소울 2 실행을 기다리고 있습니다.':'Waiting for Dark Souls II to start.',
 '게임이 여러 개 실행 중입니다.':'Multiple game instances are running.',
 '확인한 스콜라 실행 파일과 다른 버전입니다. 연결을 중지했습니다.':'Unsupported Scholar executable. Connection stopped.',
 '게임 메모리 구조가 다릅니다. 연결을 중지했습니다.':'Unexpected game memory layout. Connection stopped.',
 '유효하지 않은 메모리 주소입니다.':'Invalid memory address.',
 '메모리 쓰기 조건을 확인할 수 없습니다.':'Memory write conditions could not be verified.',
 '게임이 종료되었습니다.':'The game has exited.',
 '캐릭터 또는 지역 로딩을 기다리고 있습니다.':'Waiting for the character or area to load.',
 '캐릭터가 살아 있는 플레이 화면을 기다리고 있습니다.':'Waiting for a living character in the game world.',
 '적 종류를 확인할 수 없습니다.':'Enemy identity could not be verified.',
 '적 목록이 변경 중이거나 범위를 벗어났습니다.':'The enemy list is changing or exceeds its bounds.',
 '지역이 변경 중입니다.':'The area is changing.',
 '적 좌표를 확인할 수 없습니다.':'Enemy coordinates could not be verified.',
 '적 또는 지역이 변경되어 적용을 멈췄습니다.':'Application stopped because the enemy or area changed.',
 '적 제어 구조가 완성되지 않았습니다.':'Enemy controls are not fully initialized.',
 '충돌 제어 구조를 확인할 수 없습니다.':'Collision controls could not be verified.',
 '확인하지 않은 적 충돌 분류입니다.':'Unsupported enemy collision category.',
 '적 상태 값이 예상 범위를 벗어났습니다.':'Enemy state is outside the expected bounds.',
 '적 속도 값이 예상 범위를 벗어났습니다.':'Enemy speed is outside the expected bounds.',
 '선택한 적의 락온 제외를 먼저 확인해야 합니다.':'Lock-on exclusion must be confirmed before hiding enemies.',
 '선택한 적의 AI 중지를 먼저 확인해야 합니다.':'AI suspension must be confirmed before hiding enemies.',
 '제거 대상 또는 지역이 변경되었습니다.':'The selected targets or area changed.',
 '게임 실행 스레드를 확인할 수 없습니다.':'Game threads could not be verified.',
 'AI 제어용 공간을 준비할 수 없습니다.':'Could not allocate memory for AI controls.',
 'AI 중지 대상이 범위를 벗어났습니다.':'The AI target list exceeds its bounds.',
 '복원을 완료하지 못했습니다. 게임을 다시 실행해 주세요.':'Restoration did not complete. Please restart the game.',
 '지역 이동 중 복원 확인 실패 · 게임을 다시 실행해 주세요.':'Restoration failed during travel. Please restart the game.',
 '복원 확인 실패 · 게임을 다시 실행해 주세요.':'Restoration could not be verified. Please restart the game.',
 '숨김·충돌 해제·AI 중지·락온 제외 적용 중':'Active: hidden, no collision, AI paused, excluded from lock-on',
 '새 지역 연결 확인 중 · 안정되면 자동 적용':'Checking the new area · Will resume once stable',
 '연결됨 · 적용 대기':'Connected · Waiting to apply',
 '로딩 중 · 연결이 안정되면 자동으로 다시 적용합니다.':'Loading · Will resume automatically once the connection is stable.',
 '게임 종료 또는 복원 오류로 적용을 중지했습니다.':'Stopped because the game exited or restoration failed.',
 '미리보기 · 게임 연결 없음':'Preview · No game connection',
 '락온 제외 복원 실패: ':'Lock-on restoration failed: ',
 'AI 중지 복원 실패: ':'AI restoration failed: ',
 '오류로 중지: ':'Stopped due to an error: ',
 '락온 제외 제어':'Lock-on controls', 'AI 제어':'AI controls',
 ' 명령이 다르거나 다른 도구가 변경했습니다.':' instructions differ or were modified by another tool.',
 ' 명령이 변경되어 덮어쓰지 않았습니다.':' instructions changed; they were not overwritten.',
 ' 명령 기록을 확인하지 못했습니다.':' instruction writes could not be verified.',
 ' 명령이 외부에서 변경되었습니다.':' instructions were modified externally.',
}

def text(value, language='ko'):
    if language!='en': return value
    if value in EN: return EN[value]
    # Dynamic error prefixes/owned hook names are composed by the backend.
    result=value
    for original in sorted(EN,key=len,reverse=True):
        result=result.replace(original,EN[original])
    if re.search('[가-힣]',result):
        # OS errors can be supplied in the user's Windows language.
        code=re.search(r'\[WinError (\d+)\]',value)
        return f'Windows error {code.group(1)}. Save diagnostics for details.' if code else 'Game check failed. Save diagnostics and restart the game if needed.'
    return result

def load_english(resources):
    return json.loads((Path(resources)/'english_names.json').read_text('utf-8'))

def enemy_name(group, catalog, english, language):
    return english[group]['name'] if language=='en' else catalog[group]['name']

def count_text(count, language):
    return f'{count} in this area' if language=='en' else f'현재 지역 {count}개체'

def live_text(loaded, active, language):
    return f'In this area: {loaded} · Hidden: {active}' if language=='en' else f'현재 지역 {loaded}개체  ·  적용 중 {active}개체'
