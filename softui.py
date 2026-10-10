"""Soft rounded desktop layout; retains the existing controller interface."""
import ctypes
import tkinter as tk
import customtkinter as ctk
from PIL import Image
from art_catalog import ICONS, category_matches
from i18n import text, load_english, enemy_name, count_text

BG = '#f8f5ef'
INK = '#31483d'
MUTED = '#607367'
GREEN = '#607f69'
WHITE = '#fffdf8'
LINE = '#e5e6da'
MINT = '#edf4e8'

ctk.set_appearance_mode('light')
ctk.deactivate_automatic_dpi_awareness()
ctk.set_widget_scaling(1.0)
ctk.set_window_scaling(1.0)


def label(parent, text='', size=16, bold=False, color=INK, **kwargs):
    return ctk.CTkLabel(parent,text=text,text_color=color,
                        font=('맑은 고딕',size,'bold' if bold else 'normal'),**kwargs)


class SoftButton(ctk.CTkButton):
    def __init__(self,parent,primary=False,**kwargs):
        self.primary=primary
        super().__init__(parent,**kwargs)

    def configure(self,require_redraw=False,**kwargs):
        if self.primary and 'state' in kwargs:
            kwargs['fg_color']='#e2eadb' if kwargs['state']=='disabled' else GREEN
        super().configure(require_redraw=require_redraw,**kwargs)


def button(parent, text, command, primary=False):
    return SoftButton(parent,primary=primary,text=text,command=command,height=50,corner_radius=18,
                        font=('맑은 고딕',17,'bold' if primary else 'normal'),
                        fg_color=GREEN if primary else MINT,
                        hover_color='#506d58' if primary else '#e1edda',
                        text_color='white' if primary else INK,
                        text_color_disabled='#667668',border_width=0)


def check(parent, text, variable, command, size=16):
    return ctk.CTkCheckBox(parent,text=text,variable=variable,command=command,
                           font=('맑은 고딕',size),text_color=INK,
                           checkbox_width=24,checkbox_height=24,corner_radius=7,
                           border_width=2,border_color='#9aaa96',fg_color=GREEN,
                           hover_color='#7c9580',checkmark_color='white')


class Card(ctk.CTkFrame):
    def __init__(self,parent,name,image,variable,command):
        super().__init__(parent,fg_color=WHITE,corner_radius=24,
                         border_color=LINE,border_width=1)
        self.variable=variable; self.command=command
        self.check=check(self,'',variable,command)
        self.check.configure(width=26)
        self.check.pack(anchor='w',padx=15,pady=(13,0))
        self.art=ctk.CTkLabel(self,image=image,text='',height=112)
        self.art.pack(pady=(0,3))
        self.name=label(self,name,size=16,bold=True,wraplength=170)
        self.name.pack(padx=12)
        self.count=label(self,'현재 지역 0개체',size=14,color=MUTED)
        self.count.pack(pady=(3,16))
        for widget in (self,self.art,self.name,self.count):
            widget.bind('<Button-1>',self.click)
        self._canvas.configure(takefocus=True)
        self.bind('<space>',self.click)
        self.paint()

    def click(self,_=None):
        self.variable.set(not self.variable.get())
        self.command(); self._canvas.focus_set()
        return 'break'

    def paint(self):
        self.configure(fg_color='#eaf3e3' if self.variable.get() else WHITE,
                       border_color='#94af91' if self.variable.get() else LINE,
                       border_width=2 if self.variable.get() else 1)

    def set_count(self,value,language='ko'):
        self.count.configure(text=count_text(value,language))


class CuteLayout:
    def __init__(self,root,controller,resources):
        self.root=root; self.controller=controller; self.vars={}; self.rows={}; self.closing=False
        self.language=controller.snapshot()['language']
        self.english=load_english(resources); self.translated_widgets=[]
        self.key_down=False; self.user32=ctypes.WinDLL('user32')
        self.user32.GetAsyncKeyState.argtypes=[ctypes.c_int]
        self.user32.GetAsyncKeyState.restype=ctypes.c_short
        self.layout_signature=None
        root.tk.call('tk','scaling',4/3)
        root.title('편안한 드랭글레이그 · 다크소울 2 적 선택 (불편한 몬스터 필터)')
        height=max(800,min(940,root.winfo_screenheight()-100))
        root.geometry(f'1240x{height}'); root.minsize(1000,800); root.configure(bg=BG)
        self.images={i:ctk.CTkImage(light_image=Image.open(resources/'assets'/f'mascot-{i:02}.png'),size=(112,112))
                     for i in set(ICONS.values())|{8,5}}
        self.app_icon=tk.PhotoImage(file=str(resources/'assets'/'mascot-08.png'))
        root.iconphoto(True,self.app_icon)
        outer=ctk.CTkFrame(root,fg_color=BG,corner_radius=0)
        outer.pack(fill='both',expand=True,padx=26,pady=20)
        hero=ctk.CTkFrame(outer,fg_color=BG,corner_radius=0)
        hero.pack(fill='x',pady=(0,20))
        title=ctk.CTkFrame(hero,fg_color=BG,corner_radius=0)
        title.pack(side='left',fill='x',expand=True)
        language_bar=ctk.CTkFrame(title,fg_color=BG,corner_radius=0)
        language_bar.pack(fill='x',pady=(0,8))
        self.ui_label(language_bar,'DARK SOULS II  ·  ENEMY SELECTOR',size=13,color=GREEN).pack(side='left')
        self.language_choice=tk.StringVar(value='English' if self.language=='en' else '한국어')
        self.language_menu=ctk.CTkFrame(language_bar,corner_radius=24,
                       fg_color='#eeeadd',border_width=1,border_color='#e5dfcf')
        self.language_menu.pack(side='right',padx=(12,0))
        self.language_buttons={}
        for code,caption in (('ko','한국어'),('en','English')):
            option=ctk.CTkButton(self.language_menu,text=caption,
                       command=lambda value=caption:self.change_language(value),
                       width=108,height=38,corner_radius=19,border_width=0,
                       font=('맑은 고딕',15,'bold'),fg_color='#eeeadd',
                       hover_color='#e4ecdc',text_color=MUTED)
            option.pack(side='left',padx=(5,2) if code=='ko' else (2,5),pady=5)
            self.language_buttons[code]=option
        self.ui_label(title,'조금 더 편안한 드랭글레이그',size=30,bold=True).pack(anchor='w',pady=(9,7))
        self.ui_label(title,'마주치고 싶지 않은 몬스터를 골라 주세요.',size=16,color=MUTED).pack(anchor='w')
        badge=ctk.CTkFrame(title,fg_color='#e9efdf',corner_radius=14)
        badge.pack(anchor='w',pady=(10,0))
        self.ui_label(badge,'실시간 적용  ·  보스와 NPC는 선택 목록에서 제외',size=13,color=GREEN).pack(padx=12,pady=3)
        self.hero_icons=(5,8)
        for i in self.hero_icons:
            ctk.CTkLabel(hero,image=self.images[i],text='').pack(side='right',padx=8)
        body=ctk.CTkFrame(outer,fg_color=BG,corner_radius=0)
        body.pack(fill='both',expand=True)
        body.grid_columnconfigure(0,weight=1)
        body.grid_columnconfigure(1,weight=0)
        body.grid_rowconfigure(0,weight=1)
        left=ctk.CTkFrame(body,fg_color=BG,corner_radius=0)
        left.grid(row=0,column=0,sticky='nsew',padx=(0,20))
        self.sidebar=ctk.CTkScrollableFrame(body,width=346,fg_color=BG,corner_radius=0,
                          scrollbar_button_color='#d2dccd',scrollbar_button_hover_color='#aec3a8')
        self.sidebar.grid(row=0,column=1,sticky='nsew')
        self.search=tk.StringVar(); self.search.trace_add('write',self.filter)
        search_bar=ctk.CTkFrame(left,fg_color=BG,corner_radius=0)
        search_bar.pack(fill='x',pady=(0,12))
        self.ui_label(search_bar,'몬스터 검색',size=16,color=MUTED).pack(side='left',padx=(0,12))
        ctk.CTkEntry(search_bar,textvariable=self.search,
                    height=52,corner_radius=18,border_width=1,border_color=LINE,
                    fg_color=WHITE,text_color=INK,font=('맑은 고딕',17)).pack(side='left',fill='x',expand=True)
        self.only=tk.BooleanVar(value=False)
        self.ui_check(left,'현재 지역에서 발견된 종류만 보기',self.only,self.filter).pack(anchor='w',pady=(0,12))
        filters=ctk.CTkFrame(left,fg_color=BG,corner_radius=0)
        filters.pack(fill='x',pady=(0,14))
        self.show_images=tk.BooleanVar(value=True)
        self.ui_check(filters,'귀여운 그림 표시',self.show_images,self.change_images).pack(anchor='w')
        categories=ctk.CTkFrame(filters,fg_color=BG,corner_radius=0)
        categories.pack(fill='x',pady=(12,0))
        self.phobia=tk.BooleanVar(value=False)
        self.ui_check(categories,'공포증 관련',self.phobia,self.filter).pack(side='left')
        self.annoying=tk.BooleanVar(value=False)
        self.annoying_check=self.ui_check(categories,'짜증 유발 몬스터',self.annoying,self.filter)
        self.annoying_check.pack(side='left',padx=(24,0))
        self.ui_label(filters,'커뮤니티에서 자주 언급된 14종 · 필터는 목록만 좁혀 줍니다.\n두 분류를 함께 체크하면 두 목록을 모두 표시합니다.',size=13,color=MUTED,
              wraplength=450,justify='left').pack(anchor='w',pady=(8,0))
        box=ctk.CTkFrame(left,fg_color=BG,corner_radius=0)
        box.pack(fill='both',expand=True)
        self.canvas=tk.Canvas(box,bg=BG,highlightthickness=0)
        scroll=ctk.CTkScrollbar(box,orientation='vertical',command=self.canvas.yview,
                               fg_color=BG,button_color='#d2dccd',button_hover_color='#aec3a8')
        self.canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right',fill='y'); self.canvas.pack(side='left',fill='both',expand=True)
        self.list_frame=ctk.CTkFrame(self.canvas,fg_color=BG,corner_radius=0)
        self.window=self.canvas.create_window((0,0),window=self.list_frame,anchor='nw')
        self.list_frame.bind('<Configure>',lambda e:self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>',self.resize_cards)
        root.bind('<MouseWheel>',self.scroll_cards,add='+')
        selected=set(controller.snapshot()['selected'])
        for group,item in sorted(controller.catalog.items(),key=lambda pair:(pair[1]['name'],pair[0])):
            var=tk.BooleanVar(value=group in selected); self.vars[group]=var
            self.rows[group]=Card(self.list_frame,enemy_name(group,controller.catalog,self.english,self.language),self.images[ICONS[int(group)]],var,self.select)
        self.empty=self.ui_label(self.list_frame,'검색 조건에 맞는 몬스터가 없습니다.',size=16,color=MUTED)
        self.status=tk.StringVar(value='게임 연결을 기다리고 있습니다.')
        self.summary=tk.StringVar()
        self.chosen=tk.StringVar(value='0')
        self.live_counts=tk.StringVar(value='현재 지역 0개체  ·  적용 중 0개체')
        connection=self.panel(self.sidebar,'게임 연결')
        self.status_label=self.ui_label(connection,size=17,color=GREEN,textvariable=self.status,
                                wraplength=300,justify='left')
        self.status_label.pack(anchor='w',pady=(0,3))
        selection=self.panel(self.sidebar,'선택한 몬스터')
        numbers=ctk.CTkFrame(selection,fg_color=WHITE,corner_radius=0)
        numbers.pack(fill='x',pady=(0,4))
        self.ui_label(numbers,size=42,bold=True,color=GREEN,textvariable=self.chosen).pack(side='left')
        self.ui_label(numbers,'종 선택',size=17,color=MUTED).pack(side='left',padx=10,pady=(12,0))
        self.ui_label(selection,size=16,color=MUTED,textvariable=self.live_counts,wraplength=300,justify='left').pack(anchor='w',pady=(0,12))
        self.ui_button(selection,'선택 해제',self.clear).pack(fill='x')
        actions=self.panel(self.sidebar,'게임에 적용하기')
        self.offline=tk.BooleanVar(value=False)
        self.ui_check(actions,'게임을 오프라인으로 실행했습니다',self.offline,self.refresh_button,size=15).pack(anchor='w',pady=(2,14))
        self.toggle=self.ui_button(actions,'선택한 적 제거 시작',self.toggle_apply,primary=True)
        self.toggle.configure(height=58,corner_radius=20)
        self.toggle.pack(fill='x',pady=(0,14))
        hint=ctk.CTkFrame(actions,fg_color='#f4efdf',corner_radius=16)
        hint.pack(fill='x',pady=(0,12))
        self.ui_label(hint,'F8  ·  적용 중지와 복원',size=16,bold=True,color='#6b654b').pack(anchor='w',padx=14,pady=(12,4))
        self.ui_label(hint,'게임 화면에서도 사용할 수 있습니다.\n복원 전에 적과 거리를 두세요.',size=15,color='#6b654b',
              wraplength=280,justify='left').pack(anchor='w',padx=14,pady=(0,12))
        self.diagnostic=self.ui_button(actions,'진단 저장',controller.export)
        self.diagnostic.pack(fill='x')
        self.ui_label(self.sidebar,'시험판 · 장시간 사용은 미검증',size=14,color=MUTED).pack(anchor='w',padx=12,pady=(2,10))
        self.ui_label(outer,'그림은 종류를 나타내는 귀여운 아이콘입니다. 실제 게임 모습과 다를 수 있습니다.  ·  개발자 HJP',
              size=13,color=MUTED).pack(anchor='w',pady=(14,0))
        root.protocol('WM_DELETE_WINDOW',self.close)
        self.apply_language()
        self.update()

    def t(self,value):
        return text(value,self.language)

    def ui_label(self,parent,value='',**kwargs):
        widget=label(parent,self.t(value),**kwargs)
        if value: self.translated_widgets.append((widget,value))
        return widget

    def ui_button(self,parent,value,command,**kwargs):
        widget=button(parent,self.t(value),command,**kwargs)
        self.translated_widgets.append((widget,value))
        return widget

    def ui_check(self,parent,value,variable,command,**kwargs):
        widget=check(parent,self.t(value),variable,command,**kwargs)
        self.translated_widgets.append((widget,value))
        return widget

    def apply_language(self):
        for code,option in self.language_buttons.items():
            selected=code==self.language
            option.configure(text=('✓  ' if selected else '')+('한국어' if code=='ko' else 'English'),
                             fg_color=WHITE if selected else '#eeeadd',
                             hover_color='#f1f6eb' if selected else '#e4ecdc',
                             text_color=GREEN if selected else MUTED)
        for widget,value in self.translated_widgets:
            widget.configure(text=self.t(value))
        self.root.title(self.t('편안한 드랭글레이그 · 다크소울 2 적 선택 (불편한 몬스터 필터)'))
        for group,row in self.rows.items():
            row.name.configure(text=enemy_name(group,self.controller.catalog,self.english,self.language))
        self.layout_signature=None

    def change_language(self,choice):
        language='en' if choice=='English' else 'ko'
        self.controller.set_language(language); self.language=language
        self.language_choice.set(choice)
        self.apply_language(); self.render_state(self.controller.snapshot())

    def panel(self,parent,title):
        panel=ctk.CTkFrame(parent,fg_color=WHITE,corner_radius=24,border_width=1,border_color=LINE)
        panel.pack(fill='x',padx=3,pady=(0,12))
        content=ctk.CTkFrame(panel,fg_color=WHITE,corner_radius=0)
        content.pack(fill='both',expand=True,padx=20,pady=14)
        self.ui_label(content,title,size=20,bold=True).pack(anchor='w',pady=(0,12))
        return content

    def resize_cards(self,event):
        self.canvas.itemconfigure(self.window,width=event.width)
        self.filter()

    def scroll_cards(self,event):
        if str(event.widget).startswith(str(self.canvas)):
            self.canvas.yview_scroll(-int(event.delta/120),'units')

    def change_images(self):
        for row in self.rows.values():
            if self.show_images.get(): row.art.pack(after=row.check,pady=(0,3))
            else: row.art.pack_forget()

    def layout_cards(self,state,query,only,phobia=False,annoying=False):
        ordered=sorted(self.rows,key=lambda group:(enemy_name(group,self.controller.catalog,self.english,self.language).casefold(),group))
        visible=tuple(group for group in ordered if
                      (not query or query in self.controller.catalog[group]['name'].casefold()
                       or query in self.english[group]['name'].casefold() or query in group
                       or any(query in alias.casefold() for alias in self.english[group]['aliases']))
                      and (not only or state['counts'].get(group,0)>0)
                      and category_matches(group,phobia,annoying))
        columns=3 if self.canvas.winfo_width()>=630 else 2
        signature=(visible,columns)
        if signature==self.layout_signature: return
        self.layout_signature=signature
        for row in self.rows.values(): row.grid_forget()
        self.empty.grid_forget()
        for col in range(3): self.list_frame.columnconfigure(col,weight=1 if col<columns else 0)
        for n,group in enumerate(visible):
            self.rows[group].grid(row=n//columns,column=n%columns,sticky='nsew',padx=6,pady=7)
        if not visible: self.empty.grid(row=0,column=0,columnspan=columns,sticky='ew',pady=30)
