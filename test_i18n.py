import ast
import json
from pathlib import Path
import re
import tempfile
import unittest
from controller import Controller
from i18n import load_english, text

ROOT=Path(__file__).parent

class LanguageTests(unittest.TestCase):
    def test_all_english_families_cover_original_catalog(self):
        catalog=json.loads((ROOT/'catalog.json').read_text('utf-8'))
        english=load_english(ROOT)
        self.assertEqual(set(catalog),set(english))
        for group,row in english.items():
            self.assertNotRegex(row['name'],'[가-힣]')
            self.assertTrue(set(catalog[group]['variants'].values())<=set(row['aliases']))
        self.assertEqual(english['511']['name'],'Imperious Knight')
        self.assertEqual(english['654']['name'],'Scorcher')
    def test_language_persists_and_never_autostarts(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as home:
            c=Controller(ROOT,home); c.select({'105','661'}); c.set_enabled(True)
            c.set_language('en')
            self.assertTrue(c.enabled); self.assertEqual(c.selected,{'105','661'})
            fresh=Controller(ROOT,home)
            self.assertEqual(fresh.language,'en'); self.assertEqual(fresh.selected,c.selected)
            self.assertFalse(fresh.enabled)
            fresh.select({'105'}); self.assertEqual(Controller(ROOT,home).language,'en')
    def test_legacy_preferences_and_invalid_language(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as home:
            path=Path(home)/'settings.json'
            path.write_text(json.dumps({'selected':['105']}),encoding='utf-8')
            c=Controller(ROOT,home); self.assertEqual(c.language,'ko')
            with self.assertRaises(ValueError): c.set_language('fr')
            self.assertEqual(json.loads(path.read_text())['selected'],['105'])
    def test_backend_status_literals_have_english_presentations(self):
        for filename in ('controller.py','winprocess.py','memory.py','removal.py','aihook.py','lockon.py'):
            tree=ast.parse((ROOT/filename).read_text('utf-8'))
            for node in ast.walk(tree):
                if isinstance(node,ast.Constant) and isinstance(node.value,str) and re.search('[가-힣]',node.value):
                    translated=text(node.value,'en')
                    self.assertNotRegex(translated,'[가-힣]',(filename,node.value))
                    self.assertNotEqual(translated,'Game check failed. Save diagnostics and restart the game if needed.',(filename,node.value))
        self.assertIn('Lock-on controls',text('락온 제외 제어 명령이 외부에서 변경되었습니다.','en'))

if __name__=='__main__': unittest.main()
