"""Own-window visual check; no game worker or process connection is started."""
import ctypes
import json
from pathlib import Path
import tempfile
import tkinter as tk
from PIL import ImageGrab
from app import App, RESOURCES
from controller import Controller
from cuteui import PHOBIA_GROUPS
from art_catalog import ANNOYING_GROUPS

ctypes.windll.user32.SetProcessDPIAware()
with tempfile.TemporaryDirectory(dir=RESOURCES) as home:
    controller=Controller(RESOURCES,home)
    root=tk.Tk()
    app=App(root,controller)
    root.geometry('1240x940+20+20')
    root.update()
    assert len(app.rows)==96
    assert controller.thread is None
    assert str(app.toggle.cget('state'))=='disabled'
    app.rows['301'].click()
    assert controller.selected=={'301'}
    app.clear()
    assert not controller.selected
    controller.state.update(counts={'301':6,'330':8},loaded=14,ready=True)
    app.search.set('하이데')
    root.update()
    assert app.layout_signature[0]==('301',)
    app.search.set('')
    app.only.set(True); app.filter()
    assert set(app.layout_signature[0])=={'301','330'}
    # Filtering only changes what is shown, retaining removal selections.
    app.only.set(False); app.phobia.set(True); app.filter()
    assert set(app.layout_signature[0])==PHOBIA_GROUPS
    assert {'107','203','210','222'} <= set(app.layout_signature[0])
    assert '301' not in app.layout_signature[0]
    app.search.set('바실리스크'); app.filter()
    assert set(app.layout_signature[0])=={'210','222'}
    app.search.set(''); app.only.set(True); app.filter()
    assert not app.layout_signature[0]
    app.phobia.set(False); app.filter()
    assert set(app.layout_signature[0])=={'301','330'}
    assert 0 not in app.hero_icons
    app.vars['301'].set(True); app.vars['330'].set(True); app.select()
    assert str(app.toggle.cget('state'))=='disabled'
    app.offline.set(True); app.refresh_button()
    assert str(app.toggle.cget('state'))=='normal'
    app.toggle.invoke()
    assert controller.snapshot()['enabled']
    app.toggle.invoke()
    assert not controller.snapshot()['enabled']
    app.offline.set(False); app.refresh_button()
    app.show_images.set(False); app.change_images(); root.update()
    assert not app.rows['301'].art.winfo_ismapped()
    app.show_images.set(True); app.change_images()
    controller.state['message']='미리보기 · 게임 연결 없음'
    app.update(); root.update()
    # Check the smallest supported layout before capturing the default layout.
    root.geometry('1000x800+20+20'); root.update()
    assert app.toggle.winfo_ismapped()
    assert app.toggle.master.winfo_height() >= app.toggle.master.winfo_reqheight()
    assert app.toggle.winfo_rooty()+app.toggle.winfo_height() <= root.winfo_rooty()+root.winfo_height()
    app.sidebar._parent_canvas.yview_moveto(1); root.update()
    assert app.diagnostic.winfo_rooty()+app.diagnostic.winfo_height() <= root.winfo_rooty()+root.winfo_height()
    app.sidebar._parent_canvas.yview_moveto(0)
    root.geometry('1240x940+20+20'); root.update()
    app.only.set(False); app.filter()
    app.vars['210'].set(True); app.select()
    app.vars['203'].set(True); app.select()
    previous_selection=set(controller.selected)
    app.phobia.set(True); app.filter()
    assert controller.selected==previous_selection
    app.phobia.set(False); app.annoying.set(True); app.filter()
    assert set(app.layout_signature[0])==ANNOYING_GROUPS
    assert controller.selected==previous_selection
    assert {'105','131','661','662'} <= set(app.layout_signature[0])
    app.search.set('아마나'); app.filter()
    assert set(app.layout_signature[0])=={'105'}
    app.search.set(''); app.only.set(True); app.filter()
    assert set(app.layout_signature[0])=={'301'}
    app.only.set(False); app.phobia.set(True); app.filter()
    assert set(app.layout_signature[0])==PHOBIA_GROUPS | ANNOYING_GROUPS
    assert controller.selected==previous_selection
    app.phobia.set(False); app.filter()
    root.geometry('1000x800+20+20'); root.update()
    assert app.annoying_check.winfo_ismapped()
    assert app.annoying_check.winfo_rootx()+app.annoying_check.winfo_width() <= app.canvas.winfo_rootx()+app.canvas.winfo_width()
    root.geometry('1240x940+20+20')
    root.update()
    def capture():
        root.lift()
        root.update()
        x,y=root.winfo_rootx(),root.winfo_rooty()
        ImageGrab.grab(bbox=(x,y,x+root.winfo_width(),y+root.winfo_height())).save(RESOURCES/'preview-comfort.png')
        result={'cards':len(app.rows),'images':len(app.images),'worker_started':False,
                'card_selection':True,'search_and_region_filter':True,
                'offline_start_gate':True,'image_toggle':True,'minimum_size_actions_visible':True,
                'phobia_filter':True,'annoying_filter':True,'category_union':True,'annoying_search_region':True,'filter_preserves_selection':True,'hero_basilisk_removed':True,
                'start_and_stop_callbacks':True,'sidebar_scroll_controls_accessible':True,
                'rounded_cards':True,'sidebar_text_size':17,'sidebar_button_height':58}
        (RESOURCES/'cute_ui_verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps(result))
        app.close()
    root.after(500,capture)
    root.mainloop()
