# -*- coding: utf-8 -*-
"""
===============================================================
全能学练考系统 - 桌面版 v1.1（湖南生地会考增强版）
===============================================================
纯 tkinter 实现,无需浏览器和 Flask 服务端
功能:章节练习、模拟考试、错题本、语音播报、学习统计、湖南会考倒计时
题库生成完成！共 2114 道题，覆盖 59 个章节
  扩充题目: 已加载 5018 道新题目
  识图卡专项: 102 道题（覆盖102张图片）
  广东生地会考真题: 118 道题
  ★ 湖南生地会考真题（2021-2025）: 70 道题
  ★ 湖南生地生物核心专项: 40 道题
  ★ 湖南乡土地理专项v2（扩充版）: 74 道题
  ★ 连线匹配专项: 16 道题
  湘教地理填充图: 176 道题
题库总计: 约 8132 道题
===============================================================
新增功能 v1.1：
  ★ 湖南生地会考真题（2021-2025年湖南卷）
  ★ 湖南生地生物核心知识点专项（显微镜/细胞/八大系统等）
  ★ 湖南乡土地理专项（长株潭/洞庭湖/四水/交通/矿产等）
  ★ 连线匹配题型（生物+地理各专项连线题）
  ★ 湖南生地会考倒计时（首页显示距离6月18日天数）
===============================================================
"""

import os
import sys
import json
import random
import sqlite3
import threading
import pythoncom
import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Windows DPI 适配
if sys.platform == "win32":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

# ============ 路径配置 ============
# PyInstaller 打包后,__file__ 指向 _internal 目录,需要特殊处理
if getattr(sys, 'frozen', False):
    # 打包模式:EXE所在目录
    APP_DIR = os.path.dirname(sys.executable)
    _INTERNAL_DIR = os.path.join(APP_DIR, '_internal')
    sys.path.insert(0, _INTERNAL_DIR)
else:
    # 开发模式:脚本所在目录
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    _INTERNAL_DIR = APP_DIR

DB_PATH = os.path.join(APP_DIR, "study_data.db")
# 识图题图片目录：打包后在_internal下，开发模式在APP_DIR下
if getattr(sys, 'frozen', False):
    SHITU_IMG_DIR = os.path.join(_INTERNAL_DIR, "_shitu_images")
else:
    SHITU_IMG_DIR = os.path.join(APP_DIR, "_shitu_images")

# ============ 导入题库 ============
sys.path.insert(0, APP_DIR)
if _INTERNAL_DIR != APP_DIR:
    sys.path.insert(0, _INTERNAL_DIR)
from question_bank import QuestionBank

# ============ TTS 语音 ============
# 单线程+队列模式:专用TTS线程顺序处理播报,新请求自动打断旧播报,
# 避免多线程COM竞争导致死锁假死。
import pythoncom
import queue

_tts_voice_id = None        # 缓存中文语音ID
_tts_queue = queue.Queue()  # 播报请求队列
_tts_voice_obj = None       # 单线程内复用的SpVoice实例
_tts_stop_event = threading.Event()  # 停止信号
_tts_thread = None          # 工作线程引用

def _init_tts():
    global _tts_voice_id
    try:
        import win32com.client
        voice = win32com.client.Dispatch("SAPI.SpVoice")
        voices = voice.GetVoices()
        for i in range(voices.Count):
            v = voices.Item(i)
            desc = v.GetDescription()
            if "chinese" in desc.lower() or "zh" in desc.lower() or "huihui" in desc.lower():
                _tts_voice_id = v.Id
                break
        print(f"[TTS] 初始化成功,中文语音: {_tts_voice_id}")
    except Exception as e:
        _tts_voice_id = None
        print(f"[TTS] 初始化失败: {e}")

def _tts_worker():
    """TTS专用工作线程:单COM实例,永不死锁"""
    global _tts_voice_obj
    pythoncom.CoInitialize()
    try:
        import win32com.client
        _tts_voice_obj = win32com.client.Dispatch("SAPI.SpVoice")
        if _tts_voice_id:
            voices = _tts_voice_obj.GetVoices()
            for i in range(voices.Count):
                v = voices.Item(i)
                if v.Id == _tts_voice_id:
                    _tts_voice_obj.Voice = v
                    break
        _tts_voice_obj.Rate = 1
        _tts_voice_obj.Volume = 90
        print("[TTS] 工作线程已就绪")
    except Exception as e:
        print(f"[TTS] 工作线程初始化失败: {e}")
        pythoncom.CoUninitialize()
        return

    while not _tts_stop_event.is_set():
        try:
            text = _tts_queue.get(timeout=0.5)
        except queue.Empty:
            continue
        # 打断当前播报 (SVSFPurgeBeforeSpeak=1 | SVSFIsNotText=2)
        try:
            _tts_voice_obj.Speak(None, 3)
        except Exception:
            pass
        # 清空队列中旧请求,只播最新一条
        latest = text
        while True:
            try:
                latest = _tts_queue.get_nowait()
            except queue.Empty:
                break
        try:
            print(f"[TTS] 播报: {latest[:50]}")
            _tts_voice_obj.Speak(latest, 0)  # 同步(单线程内安全)
            print("[TTS] 播报完成")
        except Exception as e:
            print(f"[TTS] 播报失败: {e}")

    _tts_voice_obj = None
    pythoncom.CoUninitialize()
    print("[TTS] 工作线程已退出")

def speak_text(text):
    """语音播报(非阻塞):放入队列,由专用线程处理"""
    global _tts_thread
    if _tts_voice_id is None:
        return
    # 惰性启动工作线程
    if _tts_thread is None or not _tts_thread.is_alive():
        _tts_stop_event.clear()
        _tts_thread = threading.Thread(target=_tts_worker, daemon=True, name="TTS-Worker")
        _tts_thread.start()
    _tts_queue.put(text)

# ============ 数据库 ============
_db_lock = threading.Lock()

def get_db():
    db = sqlite3.connect(DB_PATH, check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    return db

def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS answer_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            question_id TEXT NOT NULL,
            chapter_id TEXT,
            user_answer TEXT,
            is_correct INTEGER DEFAULT 0,
            difficulty TEXT DEFAULT 'medium',
            question_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_records_session ON answer_records(session_id);
        CREATE INDEX IF NOT EXISTS idx_records_chapter ON answer_records(chapter_id);

        CREATE TABLE IF NOT EXISTS wrong_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id TEXT NOT NULL UNIQUE,
            chapter_id TEXT,
            question_text TEXT,
            question_type TEXT,
            options TEXT,
            correct_answer TEXT,
            user_answer TEXT,
            explanation TEXT,
            difficulty TEXT DEFAULT 'medium',
            topic TEXT,
            wrong_count INTEGER DEFAULT 1,
            last_wrong_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_wrong_chapter ON wrong_answers(chapter_id);

        CREATE TABLE IF NOT EXISTS chapter_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter_id TEXT NOT NULL UNIQUE,
            total_practiced INTEGER DEFAULT 0,
            total_correct INTEGER DEFAULT 0,
            last_practiced TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    db.commit()
    db.close()


# ============ 颜色主题 ============
class Theme:
    PRIMARY = "#4F46E5"
    PRIMARY_LIGHT = "#818CF8"
    PRIMARY_DARK = "#3730A3"
    ACTIVE = "#4F46E5"
    SUCCESS = "#10B981"
    SUCCESS_LIGHT = "#D1FAE5"
    DANGER = "#EF4444"
    DANGER_LIGHT = "#FEE2E2"
    WARNING = "#F59E0B"
    WARNING_LIGHT = "#FEF3C7"
    BG = "#F8FAFC"
    BG_CARD = "#FFFFFF"
    BG_SIDEBAR = "#1E1B4B"
    TEXT = "#1E293B"
    TEXT_SECONDARY = "#64748B"
    TEXT_LIGHT = "#94A3B8"
    BORDER = "#E2E8F0"

    DIFF_COLORS = {"easy": SUCCESS, "medium": WARNING, "hard": DANGER}
    DIFF_BG = {"easy": SUCCESS_LIGHT, "medium": WARNING_LIGHT, "hard": DANGER_LIGHT}
    DIFF_LABELS = {"easy": "简单", "medium": "中等", "hard": "困难"}
TYPE_COLORS = {"select": "#8B5CF6", "judge": Theme.WARNING, "fill": Theme.SUCCESS, "image_fill": "#EC4899", "image_hotspot": "#F59E0B"}
TYPE_LABELS = {"select": "单选题", "judge": "判断题", "fill": "填空题", "image_fill": "识图填空", "image_hotspot": "看图填图"}

# ============ 主窗口 ============
class StudyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("全能学练考系统")
        self.geometry("1280x800")
        self.minsize(960, 600)
        self.configure(bg=Theme.BG)

        # 状态
        self.qb = QuestionBank()
        self.mode = "practice"
        self.difficulty = "all"
        self.current_chapter = None
        self.questions = []
        self.current_index = 0
        self.answered = False
        self.selected_option = tk.IntVar(value=-1)
        self.selected_judge = tk.StringVar(value="")
        self.fill_var = tk.StringVar()
        self.fill_entries = []  # 多输入框（用于多答案填空题）
        self.fill_vars = []    # 多输入框对应的StringVar
        self.stats = {"total": 0, "correct": 0, "wrong": 0, "score": 0}
        self.session_id = datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(100, 999))
        self.voice_enabled = True
        self._is_maximized = False
        self.exam_timer_id = None
        self.exam_time_left = 0
        self._img_refs = []

        _init_tts()
        self._setup_styles()
        self._build_ui()
        self._load_chapter_tree()
        self._show_welcome()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._drag_bindings()

    # ──────────── 样式 ────────────
    def _setup_styles(self):
        self.default_font = tkfont.Font(family="Microsoft YaHei UI", size=11)
        self.title_font = tkfont.Font(family="Microsoft YaHei UI", size=20, weight="bold")
        self.question_font = tkfont.Font(family="Microsoft YaHei UI", size=14)
        self.option_font = tkfont.Font(family="Microsoft YaHei UI", size=12)
        self.small_font = tkfont.Font(family="Microsoft YaHei UI", size=10)
        self.badge_font = tkfont.Font(family="Microsoft YaHei UI", size=9, weight="bold")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", background=Theme.BG_CARD, foreground=Theme.TEXT,
            fieldbackground=Theme.BG_CARD, font=self.small_font, rowheight=32)
        style.map("Treeview", background=[("selected", Theme.PRIMARY)],
                  foreground=[("selected", "white")])

    # ──────────── 构建界面 ────────────
    def _build_ui(self):
        self._build_toolbar()

        self.pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.pane.pack(fill=tk.BOTH, expand=True)

        self.left_frame = tk.Frame(self.pane, bg=Theme.BG_SIDEBAR, width=260)
        self.pane.add(self.left_frame, weight=0)

        self.right_frame = tk.Frame(self.pane, bg=Theme.BG)
        self.pane.add(self.right_frame, weight=1)

        self._build_chapter_tree()

        # 内容区用 canvas+scrollbar
        self.content_canvas = tk.Canvas(self.right_frame, bg=Theme.BG, highlightthickness=0)
        self.content_scroll = ttk.Scrollbar(self.right_frame, orient=tk.VERTICAL,
                                             command=self.content_canvas.yview)
        self.content_frame = tk.Frame(self.content_canvas, bg=Theme.BG)

        self.content_frame.bind("<Configure>",
            lambda e: self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all")))
        self.content_canvas.create_window((0, 0), window=self.content_frame, anchor="nw",
                                          tags="content_win")
        self.content_canvas.configure(yscrollcommand=self.content_scroll.set)

        self.content_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.content_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 绑定滚动事件
        self.content_canvas.bind("<Configure>", self._on_canvas_resize)
        self.bind_all("<MouseWheel>",
            lambda e: self.content_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    def _on_canvas_resize(self, event):
        self.content_canvas.itemconfig("content_win", width=event.width)

    def _build_toolbar(self):
        # ── 第一行:Logo + 模式切换 + 采集器按钮 ──
        row1 = tk.Frame(self, bg=Theme.BG_CARD)
        row1.pack(fill=tk.X, side=tk.TOP)

        # Logo
        logo_frame = tk.Frame(row1, bg=Theme.BG_CARD)
        logo_frame.pack(side=tk.LEFT, padx=16, pady=8)

        logo_icon = tk.Label(logo_frame, text="学", bg=Theme.PRIMARY, fg="white",
                             font=tkfont.Font(family="Microsoft YaHei UI", size=16, weight="bold"),
                             width=2, height=1)
        logo_icon.pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(logo_frame, text="全能学练考", bg=Theme.BG_CARD, fg=Theme.PRIMARY,
                 font=tkfont.Font(family="Microsoft YaHei UI", size=16, weight="bold")).pack(side=tk.LEFT)

        # 模式切换(更醒目的大按钮)
        mode_frame = tk.Frame(row1, bg=Theme.BG_CARD)
        mode_frame.pack(side=tk.LEFT, padx=20, pady=8)

        self.mode_var = tk.StringVar(value="practice")
        modes = [("📖 章节练习", "practice"), ("📝 模拟考试", "exam"), ("📋 错题本", "wrongbook")]
        for text, val in modes:
            rb = tk.Radiobutton(mode_frame, text=text, variable=self.mode_var, value=val,
                                indicatoron=0, bg=Theme.BG, fg=Theme.TEXT_SECONDARY,
                                selectcolor=Theme.PRIMARY, activebackground=Theme.PRIMARY,
                                activeforeground="white",
                                font=self.option_font, padx=16, pady=6, bd=0,
                                relief=tk.FLAT, overrelief=tk.FLAT,
                                command=lambda v=val: self._on_mode_change(v))
            rb.pack(side=tk.LEFT, padx=3)

        # 工具按钮组(采集器 + OCR + 图片分析)
        tools_frame = tk.Frame(row1, bg=Theme.BG_CARD)
        tools_frame.pack(side=tk.LEFT, padx=12, pady=8)

        collector_btn = tk.Button(tools_frame, text="📥 题库采集器", bg=Theme.WARNING, fg="white",
                                   font=self.small_font, bd=0, padx=10, pady=4,
                                   activebackground="#E69500", activeforeground="white",
                                   command=self._launch_collector)
        collector_btn.pack(side=tk.LEFT, padx=2)

        ocr_btn = tk.Button(tools_frame, text="🔍 OCR识别", bg="#5B6ABF", fg="white",
                              font=self.small_font, bd=0, padx=10, pady=4,
                              activebackground="#4A5AAE", activeforeground="white",
                              command=self._launch_ocr_tool)
        ocr_btn.pack(side=tk.LEFT, padx=2)

        analyzer_btn = tk.Button(tools_frame, text="🤖 图片分析", bg="#16A085", fg="white",
                                   font=self.small_font, bd=0, padx=10, pady=4,
                                   activebackground="#0E8C74", activeforeground="white",
                                   command=self._launch_image_analyzer)
        analyzer_btn.pack(side=tk.LEFT, padx=2)

        # 退出按钮
        quit_btn = tk.Button(tools_frame, text="❌ 退出", bg=Theme.DANGER, fg="white",
                                font=self.small_font, bd=0, padx=10, pady=4,
                                activebackground="#C53030", activeforeground="white",
                                command=self._on_close)
        quit_btn.pack(side=tk.LEFT, padx=2)

        # 窗口控制按钮组(最右边)
        win_frame = tk.Frame(row1, bg=Theme.ACTIVE)
        win_frame.pack(side=tk.RIGHT, padx=(0, 8), pady=6)

        min_btn = tk.Button(win_frame, text="-", bg=Theme.ACTIVE, fg=Theme.TEXT,
                           font=tkfont.Font(size=12, weight="bold"), bd=0, padx=8, pady=0,
                           activebackground="#D0D5DC", activeforeground=Theme.TEXT,
                           command=lambda: self.iconify())
        min_btn.pack(side=tk.LEFT, padx=1)
        self.max_btn = tk.Button(win_frame, text="+", bg=Theme.ACTIVE, fg=Theme.TEXT,
                                  font=tkfont.Font(size=12, weight="bold"), bd=0, padx=8, pady=0,
                                  activebackground="#D0D5DC", activeforeground=Theme.TEXT,
                                  command=self._toggle_maximize)
        self.max_btn.pack(side=tk.LEFT, padx=1)

        # 右侧:湖南生地会考倒计时 + 考试计时器
        # ── 湖南生地会考倒计时 ──
        self.lbl_hunan_countdown = tk.Label(row1, text="", bg=Theme.BG_CARD,
                                             fg=Theme.WARNING, font=tkfont.Font(family="Microsoft YaHei UI", size=12, weight="bold"))
        self.lbl_hunan_countdown.pack(side=tk.RIGHT, padx=8, pady=8)
        self._update_countdown()  # 启动倒计时

        # 考试计时器
        self.lbl_timer = tk.Label(row1, text="", bg=Theme.BG_CARD,
                                   fg=Theme.DANGER, font=tkfont.Font(family="Microsoft YaHei UI", size=13, weight="bold"))
        self.lbl_timer.pack(side=tk.RIGHT, padx=8, pady=8)

        # 语音开关
        self.voice_btn = tk.Button(row1, text="🔊 语音", bg=Theme.BG, fg=Theme.SUCCESS,
                                    font=self.small_font, bd=0, padx=10, pady=4,
                                    command=self._toggle_voice)
        self.voice_btn.pack(side=tk.RIGHT, padx=4, pady=8)

        # ── 第二行:难度 + 统计 ──
        row2 = tk.Frame(self, bg=Theme.BG, height=36)
        row2.pack(fill=tk.X, side=tk.TOP)
        row2.pack_propagate(False)

        # 难度筛选
        diff_frame = tk.Frame(row2, bg=Theme.BG)
        diff_frame.pack(side=tk.LEFT, padx=16, pady=4)

        tk.Label(diff_frame, text="难度:", bg=Theme.BG, fg=Theme.TEXT_SECONDARY,
                 font=self.small_font).pack(side=tk.LEFT, padx=(0, 4))

        self.diff_var = tk.StringVar(value="all")
        diffs = [("全部", "all"), ("简单", "easy"), ("中等", "medium"), ("困难", "hard")]
        for text, val in diffs:
            rb = tk.Radiobutton(diff_frame, text=text, variable=self.diff_var, value=val,
                                indicatoron=0, bg=Theme.BG, fg=Theme.TEXT_SECONDARY,
                                selectcolor=Theme.PRIMARY, activebackground=Theme.PRIMARY,
                                activeforeground="white",
                                font=self.small_font, padx=10, pady=2, bd=0,
                                command=lambda: self._on_diff_change())
            rb.pack(side=tk.LEFT, padx=1)

        # 统计
        stats_frame = tk.Frame(row2, bg=Theme.BG)
        stats_frame.pack(side=tk.LEFT, padx=20, pady=4)

        self.lbl_total = tk.Label(stats_frame, text="📚 0", bg=Theme.BG,
                                   fg=Theme.TEXT, font=self.small_font)
        self.lbl_total.pack(side=tk.LEFT, padx=8)

        self.lbl_correct = tk.Label(stats_frame, text="✓ 0", bg=Theme.BG,
                                     fg=Theme.SUCCESS, font=self.small_font)
        self.lbl_correct.pack(side=tk.LEFT, padx=8)

        self.lbl_wrong = tk.Label(stats_frame, text="✗ 0", bg=Theme.BG,
                                   fg=Theme.DANGER, font=self.small_font)
        self.lbl_wrong.pack(side=tk.LEFT, padx=8)

        self.lbl_score = tk.Label(stats_frame, text="💯 0分", bg=Theme.BG,
                                   fg=Theme.TEXT, font=tkfont.Font(family="Microsoft YaHei UI", size=11, weight="bold"))
        self.lbl_score.pack(side=tk.LEFT, padx=8)

        self.lbl_rate = tk.Label(stats_frame, text="0%", bg=Theme.BG,
                                  fg=Theme.SUCCESS, font=tkfont.Font(family="Microsoft YaHei UI", size=11, weight="bold"))
        self.lbl_rate.pack(side=tk.LEFT, padx=8)

    def _build_chapter_tree(self):
        tk.Label(self.left_frame, text="📖 选择教材", bg=Theme.BG_SIDEBAR, fg=Theme.TEXT_LIGHT,
                 font=self.small_font).pack(anchor="w", padx=16, pady=(16, 4))

        tree_frame = tk.Frame(self.left_frame, bg=Theme.BG_SIDEBAR)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        self.tree = ttk.Treeview(tree_frame, show="tree", selectmode="browse")
        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    def _load_chapter_tree(self):
        self.tree.delete(*self.tree.get_children())
        subjects = self.qb.get_all_subjects()
        for subject in subjects:
            sid = subject["id"]
            sname = subject["name"]
            icon = "🌍" if sid == "geography" else "🧬"
            s_node = self.tree.insert("", "end", text=f"{icon} {sname}", open=True, values=(sid,))
            for grade in subject.get("grades", []):
                gid = grade["id"]
                gname = grade["name"]
                g_node = self.tree.insert(s_node, "end", text=f"  📕 {gname}", open=False, values=(gid,))
                for ch in grade.get("chapters", []):
                    cid = ch["id"]
                    cname = ch["name"]
                    cnt = ch.get("count", 0)
                    self.tree.insert(g_node, "end", text=f"    📄 {cname} ({cnt}题)",
                             values=(cid,), tags=("chapter",))

        # ── 添加专项章节(会考真题/湖南地理/识图卡/湘教地理) ──
        special_groups = [
            ("exam_real", "📝 会考真题", "exam_real_all"),
            ("hunan_geo", "🏔️ 湖南地理预测", "hunan_geo_all"),
            ("shitu", "🖼 识图卡专项", "shitu_all"),
            ("xj_geo", "🗺️ 湘教版地理填充图", "xj_geo_all"),
        ]
        icon_map = {"exam_real": "📝", "hunan_geo": "🏔️", "shitu": "🖼", "xj_geo": "🗺️"}
        for sgid, sgname, scid in special_groups:
            s_node = self.tree.insert("", "end", text=f"{icon_map[sgid]} {sgname}",
                                    open=True, values=(sgid,))
            count = len(self.qb.questions.get(scid, []))
            ch_name = {"exam_real_all": "生地会考真题(2021-2025)",
                        "hunan_geo_all": "湖南生地会考地理预测分析题",
                        "shitu_all": "识图卡全题库",
                        "xj_geo_all": "湘教版地理填充图识图题"}[scid]
            self.tree.insert(s_node, "end", text=f"  📄 {ch_name} ({count}题)",
                             values=(scid,), tags=("chapter",))

        self.tree.tag_configure("chapter", foreground="#C7D2FE")

    # ──────────── 事件处理 ────────────
    def _on_tree_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]
        values = self.tree.item(item, "values")
        if not values:
            return
        cid = values[0]
        if cid.startswith(("geo_", "bio_", "shitu_", "exam_", "hunan_", "special_", "xj_")):
            self.current_chapter = cid
            self._load_questions()

    def _on_mode_change(self, mode):
        if mode == "wrongbook":
            self._show_wrong_book()
            return
        self.mode = mode
        if self.current_chapter:
            self._load_questions()

    def _on_diff_change(self):
        self.difficulty = self.diff_var.get()
        if self.current_chapter:
            self._load_questions()

    def _toggle_voice(self):
        self.voice_enabled = not self.voice_enabled
        if self.voice_enabled:
            self.voice_btn.configure(text="🔊 语音开", fg=Theme.SUCCESS)
        else:
            self.voice_btn.configure(text="🔇 语音关", fg=Theme.TEXT_SECONDARY)

    def _change_bg_color(self):
        """更改背景颜色"""
        import tkinter.colorchooser
        color = tkinter.colorchooser.askcolor(title="选择背景颜色", initialcolor=Theme.BG)[1]
        if color:
            # 更新主题
            Theme.BG = color
            Theme.BG_CARD = color if color != "#1E293B" else "#334155"
            # 保存到数据库
            conn = sqlite3.connect(db_path)
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('bg_color', ?)", (color,))
            conn.commit()
            conn.close()
            # 提示重启
            import tkinter.messagebox
            tkinter.messagebox.showinfo("提示", "背景颜色已更换为: " + color + "\n\n请重启程序生效")

    def _launch_collector(self):
        """启动题库采集器"""
        import subprocess
        if getattr(sys, 'frozen', False):
            # 打包模式：工具脚本在 _internal 目录，需要系统Python环境运行
            base_dir = os.path.dirname(sys.executable)
            collector_path = os.path.join(base_dir, '_internal', 'quiz_collector.py')
            # 使用系统Python（打包版无法运行.py脚本）
            python_exe = 'python'
        else:
            # 开发模式
            base_dir = APP_DIR
            collector_path = os.path.join(base_dir, 'quiz_collector.py')
            python_exe = sys.executable
        if os.path.exists(collector_path):
            subprocess.Popen([python_exe, collector_path], cwd=base_dir)
        else:
            from tkinter import messagebox
            messagebox.showwarning("未找到", f"题库采集器文件不存在:\n{collector_path}")

    def _launch_ocr_tool(self):
        """启动OCR文字识别工具"""
        import subprocess
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
            ocr_path = os.path.join(base_dir, '_internal', 'ocr_tool.py')
            python_exe = 'python'
        else:
            base_dir = APP_DIR
            ocr_path = os.path.join(base_dir, 'ocr_tool.py')
            python_exe = sys.executable
        if os.path.exists(ocr_path):
            subprocess.Popen([python_exe, ocr_path], cwd=base_dir)
        else:
            from tkinter import messagebox
            messagebox.showwarning("未找到", f"OCR识别工具文件不存在:\n{ocr_path}")

    def _launch_image_analyzer(self):
        """启动图片内容智能分析器"""
        import subprocess
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
            analyzer_path = os.path.join(base_dir, '_internal', 'image_analyzer.py')
            python_exe = 'python'
        else:
            base_dir = APP_DIR
            analyzer_path = os.path.join(base_dir, 'image_analyzer.py')
            python_exe = sys.executable
        if os.path.exists(analyzer_path):
            subprocess.Popen([python_exe, analyzer_path], cwd=base_dir)
        else:
            from tkinter import messagebox
            messagebox.showwarning("未找到", f"图片分析工具文件不存在:\n{analyzer_path}")

    # ──────────── 加载题目 ────────────
    def _load_questions(self):
        self._stop_exam_timer()
        ch = self.current_chapter
        diff = self.diff_var.get()
        # 识图题：取全部题目（不受count限制），按图片分组连续显示
        if ch in ("shitu_all", "xj_geo_all"):
            questions = self.qb.get_questions_by_chapter(ch, mode=self.mode, count=9999, difficulty=diff)
            if questions:
                by_image = defaultdict(list)
                for q in questions:
                    by_image[q.get("image", "")].append(q)
                # 图片组随机排列，每组内顺序不变
                img_keys = list(by_image.keys())
                random.shuffle(img_keys)
                # 每组完整出现
                grouped = []
                for k in img_keys:
                    grouped.extend(by_image[k])
                questions = grouped
        else:
            questions = self.qb.get_questions_by_chapter(ch, mode=self.mode, count=50, difficulty=diff)

        # 选项打乱
        for q in questions:
            if q.get("type") == "select" and q.get("options"):
                correct_idx = q.get("answer")
                # 处理字符串答案（如 "A", "B", "C", "D"）转换为索引
                if isinstance(correct_idx, str) and correct_idx.upper() in "ABCD":
                    correct_idx = ord(correct_idx.upper()) - ord('A')
                    q["answer"] = correct_idx
                if isinstance(correct_idx, int) and 0 <= correct_idx < len(q["options"]):
                    correct_text = q["options"][correct_idx]
                    opts = q["options"][:]
                    random.shuffle(opts)
                    q["options"] = opts
                    try:
                        q["answer"] = opts.index(correct_text)
                    except ValueError:
                        pass
                    q["_correct_text"] = correct_text

        self.questions = questions
        self.current_index = 0
        self.answered = False
        self.stats = {"total": 0, "correct": 0, "wrong": 0, "score": 0}
        self._update_stats_display()

        # 调试日志
        try:
            with open("_load_debug.txt", "a", encoding="utf-8", buffering=1) as f:
                f.write(f"[load] chapter={ch} diff={diff} mode={self.mode} → loaded={len(questions)} questions\n")
                if questions:
                    from collections import Counter
                    imgs = Counter(q.get('image','') for q in questions)
                    for img, cnt in sorted(imgs.items()):
                        f.write(f"  image={img!r} count={cnt}\n")
        except Exception as e:
            pass

        if not questions:
            self._show_message("该章节暂无题目", "请选择其他章节")
            return

        if self.mode == "exam":
            self._start_exam_timer()

        self._render_question()

    # ──────────── 渲染题目 ────────────
    def _clear_content(self):
        for w in self.content_frame.winfo_children():
            w.destroy()
        self._img_refs.clear()

    def _render_question(self):
        self._clear_content()
        self.answered = False
        self.selected_option.set(-1)
        self.selected_judge.set("")
        self.fill_var.set("")
        for v in getattr(self, 'fill_vars', []):
            v.set("")
        self.fill_entries = []
        self.fill_vars = []

        if not self.questions:
            return

        q = self.questions[self.current_index]
        total = len(self.questions)
        progress = (self.current_index + 1) / total * 100

        # ── 进度条 ──
        prog_frame = tk.Frame(self.content_frame, bg=Theme.BG_CARD, padx=20, pady=12)
        prog_frame.pack(fill=tk.X, padx=16, pady=(8, 4))

        # 识图题显示同图题数量区间
        if q.get("image"):
            # 找到同一张图的所有题起始/结束索引
            img = q.get("image")
            same_img_indices = [i for i, x in enumerate(self.questions) if x.get("image") == img]
            start = same_img_indices[0] + 1
            end = same_img_indices[-1] + 1
            if len(same_img_indices) > 1:
                prog_label = f"🖼 第{start}-{end}题（共{end}题）"
            else:
                prog_label = f"📊 进度 {self.current_index + 1}/{total}"
        else:
            prog_label = f"📊 进度 {self.current_index + 1}/{total}"
        tk.Label(prog_frame, text=prog_label,
                 bg=Theme.BG_CARD, font=self.option_font).pack(side=tk.LEFT)

        stats_text = f"✅ {self.stats['correct']}  ❌ {self.stats['wrong']}  💯 {self.stats['total']}分"
        tk.Label(prog_frame, text=stats_text, bg=Theme.BG_CARD,
                 fg=Theme.TEXT_SECONDARY, font=self.small_font).pack(side=tk.RIGHT)

        # 进度条
        bar_frame = tk.Frame(self.content_frame, bg=Theme.BORDER, height=8)
        bar_frame.pack(fill=tk.X, padx=16, pady=(0, 8))
        bar_frame.pack_propagate(False)

        bar_fill = tk.Frame(bar_frame, bg=Theme.PRIMARY, height=8)
        bar_fill.place(relwidth=progress/100, relheight=1.0)

        # ── 题目卡片 ──
        card = tk.Frame(self.content_frame, bg=Theme.BG_CARD, padx=24, pady=20)
        card.pack(fill=tk.BOTH, expand=True, padx=16, pady=4)

        # 头部:类型 + 难度
        header = tk.Frame(card, bg=Theme.BG_CARD)
        header.pack(fill=tk.X, pady=(0, 12))

        q_type = q.get("type", "select")
        diff = q.get("difficulty", "medium")

        type_color = TYPE_COLORS.get(q_type, Theme.PRIMARY)
        tk.Label(header, text=f" {TYPE_LABELS.get(q_type, '题目')} ",
                 bg=type_color, fg="white", font=self.badge_font,
                 padx=8, pady=2).pack(side=tk.LEFT, padx=(0, 8))

        diff_color = Theme.DIFF_COLORS.get(diff, Theme.WARNING)
        diff_bg = Theme.DIFF_BG.get(diff, Theme.WARNING_LIGHT)
        tk.Label(header, text=f" {Theme.DIFF_LABELS.get(diff, '中等')} ",
                 bg=diff_bg, fg=diff_color, font=self.badge_font,
                 padx=8, pady=2).pack(side=tk.LEFT, padx=(0, 8))

        topic = q.get("topic", "知识点")
        tk.Label(header, text=f"📌 {topic}", bg=Theme.BG_CARD,
                 fg=Theme.TEXT_LIGHT, font=self.small_font).pack(side=tk.LEFT, padx=8)

        # 识图题图片
        if q.get("image"):
            hotspots = q.get("hotspots") if q.get("type") == "image_hotspot" else None
            self._show_question_image(card, q["image"], hotspots=hotspots)

        # 题目文本
        q_text = q.get("question", "")
        tk.Label(card, text=q_text, bg=Theme.BG_CARD, fg=Theme.TEXT,
                 font=self.question_font, wraplength=800, justify=tk.LEFT).pack(
            fill=tk.X, pady=(8, 20))

        # 选项
        self._render_options(card, q)

        # 答案结果显示区(初始隐藏)
        self.result_frame = tk.Frame(card, bg=Theme.BG_CARD)

        # 操作按钮
        btn_frame = tk.Frame(card, bg=Theme.BG_CARD)
        btn_frame.pack(fill=tk.X, pady=(20, 0))

        self.prev_btn = tk.Button(btn_frame, text="← 上一题", font=self.option_font,
                                   bg=Theme.BG, fg=Theme.TEXT_SECONDARY, bd=1,
                                   relief=tk.GROOVE, padx=16, pady=6,
                                   command=self._prev_question,
                                   state=tk.NORMAL if self.current_index > 0 else tk.DISABLED)
        self.prev_btn.pack(side=tk.LEFT)

        self.submit_btn = tk.Button(btn_frame, text="提交答案 →", font=self.option_font,
                                     bg=Theme.PRIMARY, fg="white", bd=0,
                                     padx=24, pady=8, cursor="hand2",
                                     command=self._submit_answer)
        self.submit_btn.pack(side=tk.RIGHT)

        self.content_canvas.yview_moveto(0)

    def _show_question_image(self, parent, image_ref, hotspots=None):
        try:
            from PIL import Image, ImageTk
            img_path = None
            # 标准化路径:去掉开头的 /
            ref = image_ref.lstrip("/")

            # 尝试多种候选路径
            candidates = []
            # 1. 直接作为 APP_DIR 下的文件名
            candidates.append(os.path.join(APP_DIR, ref))
            # 2. SHITU_IMG_DIR + 文件名
            fname = os.path.basename(ref)
            candidates.append(os.path.join(SHITU_IMG_DIR, fname))
            # 3. SHITU_IMG_DIR + 完整相对路径
            candidates.append(os.path.join(SHITU_IMG_DIR, ref))
            # 4. static/images/geo_maps
            candidates.append(os.path.join(APP_DIR, "static", "images", "geo_maps", fname))
            # 5. 湘教版图片：xj_01.png -> xj_01.jpeg（扩展名不同）
            if fname.startswith("xj_"):
                base = fname.rsplit(".", 1)[0]
                for ext in [".jpeg", ".jpg", ".bmp"]:
                    candidates.append(os.path.join(SHITU_IMG_DIR, base + ext))
                    candidates.append(os.path.join(APP_DIR, base + ext))
            # 6. 绝对路径直接用
            if os.path.isabs(image_ref) and os.path.exists(image_ref):
                candidates.insert(0, image_ref)

            for c in candidates:
                if os.path.exists(c):
                    img_path = c
                    break

            if img_path and os.path.exists(img_path):
                img = Image.open(img_path)
                img.thumbnail((500, 300), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self._img_refs.append(photo)

                if hotspots:
                    # 图片热点填空模式：用 Canvas 在图片上叠加白色输入框
                    container = tk.Frame(parent, bg=Theme.BG_CARD)
                    container.pack(pady=(0, 12))

                    canvas = tk.Canvas(container, width=img.width, height=img.height,
                                       bg=Theme.BG_CARD, highlightthickness=0)
                    canvas.pack()
                    canvas.create_image(0, 0, anchor=tk.NW, image=photo)

                    # 绑定点击图片放大
                    canvas.bind("<Button-1>", lambda e: self._show_full_image(img_path))

                    self.fill_entries = []
                    self.fill_vars = []
                    for hs in hotspots:
                        var = tk.StringVar()
                        w = hs.get("width", 8)
                        entry = tk.Entry(canvas, textvariable=var, font=self.small_font,
                                         width=w, relief=tk.SOLID, bd=1,
                                         bg="white", fg=Theme.TEXT, justify=tk.CENTER)
                        x = int(hs["x"] * img.width)
                        y = int(hs["y"] * img.height)
                        canvas.create_window(x, y, window=entry, anchor=tk.CENTER)
                        self.fill_vars.append(var)
                        self.fill_entries.append(entry)

                    tk.Label(container, text="点击图片可放大查看  |  请在白色框中填写对应结构名称",
                             bg=Theme.BG_CARD, fg=Theme.TEXT_LIGHT,
                             font=self.small_font).pack(pady=(4, 0))
                else:
                    img_label = tk.Label(parent, image=photo, bg=Theme.BG_CARD)
                    img_label.pack(pady=(0, 12))

                    tk.Label(parent, text="点击图片可放大查看", bg=Theme.BG_CARD,
                             fg=Theme.TEXT_LIGHT, font=self.small_font).pack(pady=(0, 8))

                    img_label.bind("<Button-1>", lambda e: self._show_full_image(img_path))
        except Exception as ex:
            tk.Label(parent, text=f"[图片加载失败: {image_ref}]", bg=Theme.BG_CARD,
                     fg=Theme.TEXT_LIGHT, font=self.small_font).pack(pady=(0, 12))

    def _show_full_image(self, img_path):
        try:
            from PIL import Image, ImageTk
            top = tk.Toplevel(self)
            top.title("图片查看")
            top.geometry("800x600")
            img = Image.open(img_path)
            img.thumbnail((750, 550), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            lbl = tk.Label(top, image=photo)
            lbl.image = photo
            lbl.pack(padx=20, pady=20)
        except Exception:
            pass

    def _render_options(self, parent, q):
        q_type = q.get("type", "select")

        if q_type == "select":
            letters = ["A", "B", "C", "D"]
            self._option_frames = []
            self._option_labels = []

            # 用两行两列网格布局，A左B右，C左D
            grid_frame = tk.Frame(parent, bg=Theme.BG_CARD)
            grid_frame.pack(fill=tk.BOTH, pady=4)

            options = q.get("options", [])
            # 安全检查：确保有选项
            if not options:
                tk.Label(parent, text="无选项数据", bg=Theme.BG_CARD, fg=Theme.TEXT_SECONDARY).pack(pady=20)
                return

            for i, opt in enumerate(options):
                if i >= len(letters):
                    break  # 超过4个选项则跳过
                col = i % 2          # 0=左, 1=右
                row = i // 2        # 0=上, 1=下

                f = tk.Frame(grid_frame, bg=Theme.BG, padx=12, pady=10,
                             cursor="hand2", relief=tk.SOLID, bd=1)
                f.grid(row=row, column=col, sticky="ew", padx=6, pady=4)
                grid_frame.grid_columnconfigure(col, weight=1)

                letter_lbl = tk.Label(f, text=letters[i], bg=Theme.BG_CARD,
                                       fg=Theme.TEXT_SECONDARY,
                                       font=self.option_font, width=2, height=1)
                letter_lbl.pack(side=tk.LEFT, padx=(0, 10))

                opt_lbl = tk.Label(f, text=opt, bg=Theme.BG, fg=Theme.TEXT,
                                   font=self.option_font, wraplength=360,
                                   justify=tk.LEFT, anchor="w")
                opt_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

                for widget in (f, letter_lbl, opt_lbl):
                    widget.bind("<Button-1>", lambda e, idx=i: self._select_option(idx))

                self._option_frames.append(f)
                self._option_labels.append((letter_lbl, opt_lbl))

        elif q_type == "judge":
            jf = tk.Frame(parent, bg=Theme.BG_CARD)
            jf.pack(fill=tk.X, pady=16)

            self._judge_frames = []
            for val, icon, text in [(True, "✓", "正确"), (False, "✗", "错误")]:
                f = tk.Frame(jf, bg=Theme.BG, padx=20, pady=16, cursor="hand2")
                f.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=8)

                tk.Label(f, text=icon, bg=Theme.BG, font=tkfont.Font(size=32),
                          fg=Theme.SUCCESS if val else Theme.DANGER).pack()
                tk.Label(f, text=text, bg=Theme.BG, font=self.option_font).pack()

                for widget in f.winfo_children():
                    widget.bind("<Button-1>", lambda e, v=val: self._select_judge(v))
                f.bind("<Button-1>", lambda e, v=val: self._select_judge(v))

                self._judge_frames.append((f, val))

        elif q_type in ("fill", "image_fill"):
            ff = tk.Frame(parent, bg=Theme.BG_CARD)
            ff.pack(fill=tk.X, pady=16)

            correct_answer = q.get("answer")
            is_list_answer = isinstance(correct_answer, list)

            if is_list_answer and len(correct_answer) > 1:
                # 多答案模式：每个答案一个输入框
                self.fill_entries = []
                self.fill_vars = []
                labels = ["①","②","③","④","⑤","⑥","⑦","⑧","⑨","⑩",
                           "⑪","⑫","⑬","⑭","⑮","⑯","⑰","⑱"]
                for i, ans in enumerate(correct_answer):
                    lbl_text = labels[i] if i < len(labels) else str(i+1)
                    row = tk.Frame(ff, bg=Theme.BG_CARD)
                    row.pack(fill=tk.X, pady=2)
                    tk.Label(row, text=lbl_text+".", bg=Theme.BG_CARD, fg=Theme.TEXT,
                             font=self.option_font, width=3, anchor='e').pack(side=tk.LEFT, padx=(0,6))
                    var = tk.StringVar()
                    entry = tk.Entry(row, textvariable=var, font=self.option_font, width=18,
                                     relief=tk.SOLID, bd=2)
                    entry.pack(side=tk.LEFT, ipady=4, padx=(0,8))
                    self.fill_vars.append(var)
                    self.fill_entries.append(entry)
                # 隐藏单输入框
                self.fill_var.set("")
            else:
                # 单答案模式：原有逻辑
                self.fill_entries = []
                self.fill_vars = []
                tk.Label(ff, text="请填写答案:", bg=Theme.BG_CARD, fg=Theme.TEXT_SECONDARY,
                         font=self.option_font).pack(side=tk.LEFT, padx=(0, 12))
                self.fill_entry = tk.Entry(ff, textvariable=self.fill_var,
                                            font=self.option_font, width=20,
                                            relief=tk.SOLID, bd=2)
                self.fill_entry.pack(side=tk.LEFT, ipady=4)

        elif q_type == "image_hotspot":
            # 图片热点填空：输入框已在图片上渲染，此处显示提示即可
            hint = tk.Frame(parent, bg=Theme.BG_CARD)
            hint.pack(fill=tk.X, pady=(8, 0))
            tk.Label(hint, text="💡 请在图片中白色输入框内填写对应结构名称",
                     bg=Theme.BG_CARD, fg=Theme.TEXT_SECONDARY,
                     font=self.small_font).pack(anchor=tk.W)

    def _select_option(self, idx):
        if self.answered:
            return
        self.selected_option.set(idx)
        for i, (f, (ll, ol)) in enumerate(zip(self._option_frames, self._option_labels)):
            if i == idx:
                f.configure(bg="#EEF2FF")
                ll.configure(bg=Theme.PRIMARY, fg="white")
                ol.configure(bg="#EEF2FF")
            else:
                f.configure(bg=Theme.BG)
                ll.configure(bg=Theme.BG_CARD, fg=Theme.TEXT_SECONDARY)
                ol.configure(bg=Theme.BG)

    def _select_judge(self, val):
        if self.answered:
            return
        self.selected_judge.set(str(val))
        for f, v in self._judge_frames:
            if v == val:
                f.configure(bg="#EEF2FF")
            else:
                f.configure(bg=Theme.BG)

    # ──────────── 提交答案 ────────────
    def _submit_answer(self):
        if self.answered:
            self._next_question()
            return

        q = self.questions[self.current_index]
        q_type = q.get("type", "select")
        user_answer = None
        user_answer_text = None

        if q_type == "select":
            user_answer = self.selected_option.get()
            if user_answer < 0:
                messagebox.showwarning("提示", "请先选择答案")
                return
            user_answer_text = q["options"][user_answer] if q.get("options") else None
        elif q_type == "judge":
            js = self.selected_judge.get()
            if not js:
                messagebox.showwarning("提示", "请先选择正确或错误")
                return
            user_answer = js == "True"
        elif q_type in ("fill", "image_fill", "image_hotspot"):
            correct_answer = q.get("answer")
            is_list_answer = isinstance(correct_answer, list) and len(correct_answer) > 1
            if is_list_answer or q_type == "image_hotspot":
                # 多输入框模式：收集所有输入
                user_answers = []
                for v in self.fill_vars:
                    user_answers.append(v.get().strip())
                if not any(user_answers):
                    messagebox.showwarning("提示", "请先填写答案")
                    return
                user_answer = user_answers
            else:
                user_answer = self.fill_var.get().strip()
                if not user_answer:
                    messagebox.showwarning("提示", "请先填写答案")
                    return

        self.answered = True
        self.stats["total"] += 1

        correct_answer = q.get("answer")
        # 处理字符串答案（如 "A", "B", "C", "D"）转换为索引
        if isinstance(correct_answer, str) and correct_answer.upper() in "ABCD":
            correct_answer = ord(correct_answer.upper()) - ord('A')
        correct_text = q.get("_correct_text")
        is_correct = False

        if q_type == "select":
            if correct_text and user_answer_text:
                is_correct = user_answer_text == correct_text
            else:
                is_correct = user_answer == correct_answer
        elif q_type == "judge":
            is_correct = user_answer == correct_answer
        elif q_type in ("fill", "image_fill", "image_hotspot"):
            correct_answer = q.get("answer")
            answers = [correct_answer] if not isinstance(correct_answer, list) else correct_answer
            if isinstance(user_answer, list):
                # 多输入框模式：逐个比对
                if len(user_answer) != len(answers):
                    is_correct = False
                else:
                    match_count = 0
                    for ua, ca in zip(user_answer, answers):
                        ua_s = str(ua).strip().lower()
                        ca_s = str(ca).strip().lower()
                        if q_type == "image_hotspot":
                            # 看图填图：要求精确匹配
                            match = ua_s == ca_s
                        else:
                            # 普通填空：允许互相包含（更宽松）
                            match = ca_s in ua_s or ua_s in ca_s
                        if match:
                            match_count += 1
                    is_correct = match_count == len(answers)
            else:
                is_correct = any(str(a).strip().lower() == str(user_answer).strip().lower() for a in answers)

        self._save_answer(q, user_answer, is_correct)
        self._show_result(q, is_correct, user_answer, correct_answer)

        if self.voice_enabled:
            voice_text = self._build_voice_text(q, is_correct, correct_answer)
            speak_text(voice_text)

        if self.current_index < len(self.questions) - 1:
            self.submit_btn.configure(text="下一题 →")
        else:
            self.submit_btn.configure(text="查看结果 →")

        self._update_stats_display()

    def _save_answer(self, q, user_answer, is_correct):
        chapter_id = q.get("id", "").rsplit("_", 2)[0] if "_" in q.get("id", "") else ""
        with _db_lock:
            db = get_db()
            try:
                db.execute("""
                    INSERT INTO answer_records (session_id, question_id, chapter_id, user_answer, is_correct, difficulty, question_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (self.session_id, q.get("id", ""), chapter_id,
                      str(user_answer), 1 if is_correct else 0,
                      q.get("difficulty", "medium"), q.get("type", "select")))

                if not is_correct:
                    qi = self.qb.get_question_info(q.get("id", ""))
                    db.execute("""
                        INSERT INTO wrong_answers (question_id, chapter_id, question_text, question_type,
                            options, correct_answer, user_answer, explanation, difficulty, topic, wrong_count, last_wrong_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                        ON CONFLICT(question_id) DO UPDATE SET
                            wrong_count = wrong_count + 1,
                            user_answer = excluded.user_answer,
                            last_wrong_at = CURRENT_TIMESTAMP
                    """, (q.get("id", ""), chapter_id,
                          qi.get("question", ""), qi.get("type", ""),
                          json.dumps(qi.get("options", []), ensure_ascii=False),
                          str(q.get("answer", "")), str(user_answer),
                          qi.get("explanation", ""), qi.get("difficulty", "medium"),
                          qi.get("topic", "")))

                if chapter_id:
                    db.execute("""
                        INSERT INTO chapter_progress (chapter_id, total_practiced, total_correct, last_practiced)
                        VALUES (?, 1, ?, CURRENT_TIMESTAMP)
                        ON CONFLICT(chapter_id) DO UPDATE SET
                            total_practiced = total_practiced + 1,
                            total_correct = total_correct + ?,
                            last_practiced = CURRENT_TIMESTAMP
                    """, (chapter_id, 1 if is_correct else 0, 1 if is_correct else 0))

                db.commit()
            finally:
                db.close()

    def _show_result(self, q, is_correct, user_answer, correct_answer):
        q_type = q.get("type", "select")

        # 标记选项颜色
        if q_type == "select":
            for i, (f, (ll, ol)) in enumerate(zip(self._option_frames, self._option_labels)):
                if i == correct_answer:
                    f.configure(bg=Theme.SUCCESS_LIGHT)
                    ll.configure(bg=Theme.SUCCESS, fg="white")
                    ol.configure(bg=Theme.SUCCESS_LIGHT)
                elif i == user_answer and not is_correct:
                    f.configure(bg=Theme.DANGER_LIGHT)
                    ll.configure(bg=Theme.DANGER, fg="white")
                    ol.configure(bg=Theme.DANGER_LIGHT)
        elif q_type == "judge":
            for f, v in self._judge_frames:
                if v == correct_answer:
                    f.configure(bg=Theme.SUCCESS_LIGHT)
                elif v == user_answer and not is_correct:
                    f.configure(bg=Theme.DANGER_LIGHT)
        elif q_type in ("fill", "image_fill", "image_hotspot"):
            correct_answer = q.get("answer")
            answers = [correct_answer] if not isinstance(correct_answer, list) else correct_answer
            if hasattr(self, "fill_entries") and len(self.fill_entries) > 0:
                for i, entry in enumerate(self.fill_entries):
                    match = False
                    if isinstance(user_answer, list) and i < len(user_answer) and i < len(answers):
                        ua_str = str(user_answer[i]).strip().lower()
                        ca_val = answers[i]
                        ca_str = str(ca_val[0] if isinstance(ca_val, list) else ca_val).strip().lower()
                        match = ua_str == ca_str or ca_str in ua_str or ua_str in ca_str
                    entry.configure(bg=Theme.SUCCESS_LIGHT if match else Theme.DANGER_LIGHT)
            elif hasattr(self, "fill_entry"):
                if is_correct:
                    self.fill_entry.configure(bg=Theme.SUCCESS_LIGHT)
                else:
                    self.fill_entry.configure(bg=Theme.DANGER_LIGHT)

        # 结果提示
        self.result_frame.pack(fill=tk.X, pady=(16, 0))

        if is_correct:
            badge = tk.Label(self.result_frame, text=" ✓ 回答正确 ",
                            bg=Theme.SUCCESS_LIGHT, fg=Theme.SUCCESS,
                            font=self.option_font, padx=12, pady=6)
            self.stats["correct"] += 1
            self.stats["score"] += 10  # 答对加10分
        else:
            badge = tk.Label(self.result_frame, text=" ✗ 回答错误 ",
                            bg=Theme.DANGER_LIGHT, fg=Theme.DANGER,
                            font=self.option_font, padx=12, pady=6)
            self.stats["wrong"] += 1
            self.stats["score"] -= 5   # 答错扣5分

            correct_display = self._format_correct_answer(q, correct_answer)
            tk.Label(self.result_frame, text=f"正确答案:{correct_display}",
                     bg=Theme.BG_CARD, fg=Theme.TEXT_SECONDARY, font=self.option_font).pack(side=tk.LEFT, padx=12)

        badge.pack(side=tk.LEFT)

        # 填空题：显示填好答案的题目文本（便于对照学习）
        if q_type in ("fill", "image_fill", "image_hotspot"):
            ca = q.get("answer", [])
            if isinstance(ca, list) and len(ca) > 0:
                filled_q = self._embed_answers_in_text(q.get("question", ""), ca)
                if filled_q != q.get("question", ""):
                    ans_text_frame = tk.Frame(self.result_frame, bg="#ECFDF5", padx=16, pady=12)
                    ans_text_frame.pack(fill=tk.X, pady=(12, 0))
                    tk.Label(ans_text_frame, text="📋 标准答案填空", bg="#ECFDF5", fg="#065F46",
                             font=self.badge_font).pack(anchor="w")
                    tk.Label(ans_text_frame, text=filled_q, bg="#ECFDF5", fg="#064E3B",
                             font=self.option_font, wraplength=700, justify=tk.LEFT).pack(anchor="w", pady=(4, 0))

        # 解析
        explanation = q.get("explanation", "")
        if explanation:
            exp_frame = tk.Frame(self.result_frame, bg="#FFFBEB", padx=16, pady=12)
            exp_frame.pack(fill=tk.X, pady=(12, 0))

            clean_exp = explanation
            for tag in ["【A错因】", "【B错因】", "【C错因】", "【关键点】", "【易错提示】"]:
                clean_exp = clean_exp.replace(tag, "\n• ")

            tk.Label(exp_frame, text="📖 解析", bg="#FFFBEB", fg="#92400E",
                     font=self.badge_font).pack(anchor="w")
            tk.Label(exp_frame, text=clean_exp.strip(), bg="#FFFBEB", fg="#78350F",
                     font=self.small_font, wraplength=700, justify=tk.LEFT).pack(anchor="w", pady=(4, 0))

    def _embed_answers_in_text(self, text, answers):
        """将题目文本中的填空横线替换为答案"""
        import re
        if not answers or not text:
            return text

        # 匹配常见的填空标记：A-Z 或 ①-⑳
        pattern = r'([A-Z①-⑳])(_{2,})'
        matches = list(re.finditer(pattern, text))
        if not matches:
            return text

        # 策略1：直接用原始答案
        raw_answers = [str(a).strip() for a in answers]
        if len(matches) == len(raw_answers):
            expanded = raw_answers
        else:
            # 策略2：尝试展开逗号分隔的答案
            expanded = []
            for a in answers:
                s = str(a).strip()
                if ',' in s and '，' not in s:
                    parts = [p.strip() for p in s.split(',')]
                    expanded.extend(parts)
                elif '，' in s:
                    parts = [p.strip() for p in s.split('，')]
                    expanded.extend(parts)
                else:
                    expanded.append(s)

            if len(matches) != len(expanded):
                # 策略3：仍不匹配，回退到原始答案，用"?"补齐或截断
                expanded = raw_answers[:]
                while len(expanded) < len(matches):
                    expanded.append("?")
                expanded = expanded[:len(matches)]

        # 从后往前替换，避免位置偏移
        result = text
        offset = 0
        for match, ans in zip(matches, expanded):
            start = match.start() + offset
            end = match.end() + offset
            marker = match.group(1)
            replacement = f"{marker}__{ans}__"
            result = result[:start] + replacement + result[end:]
            offset += len(replacement) - (end - start)

        return result

    def _format_correct_answer(self, q, correct_answer):
        q_type = q.get("type", "select")
        if q_type == "select":
            letters = ["A", "B", "C", "D"]
            idx = correct_answer if isinstance(correct_answer, int) else 0
            letter = letters[idx] if idx < len(letters) else "?"
            opt_text = q.get("options", [""])[idx] if idx < len(q.get("options", [])) else ""
            return f"{letter}、{opt_text}"
        elif q_type == "judge":
            return "正确" if correct_answer else "错误"
        else:
            if isinstance(correct_answer, list) and len(correct_answer) > 1:
                labels = ["①","②","③","④","⑤","⑥","⑦","⑧","⑨","⑩",
                           "⑪","⑫","⑬","⑭","⑮"]
                parts = []
                for i, a in enumerate(correct_answer):
                    lbl = labels[i] if i < len(labels) else str(i+1)
                    val = a[0] if isinstance(a, list) else a
                    parts.append(lbl + ": " + str(val))
                return "  |  ".join(parts)
            elif isinstance(correct_answer, list):
                return str(correct_answer[0])
            return str(correct_answer)

    def _build_voice_text(self, q, is_correct, correct_answer):
        if is_correct:
            return "回答正确,太棒了!"

        q_type = q.get("type", "select")
        if q_type == "select":
            letters = ["A", "B", "C", "D"]
            idx = correct_answer if isinstance(correct_answer, int) else 0
            letter = letters[idx] if idx < len(letters) else ""
            opt = q.get("options", [""])[idx] if idx < len(q.get("options", [])) else ""
            correct_part = f"正确答案是{letter},{opt}"
        elif q_type == "judge":
            correct_part = "正确答案是正确" if correct_answer else "正确答案是错误"
        else:
            ca = correct_answer if not isinstance(correct_answer, list) else "或".join(str(a) for a in correct_answer)
            correct_part = f"正确答案是{ca}"

        exp = q.get("explanation", "")
        if exp:
            exp = exp.split("【")[0].strip()
            if len(exp) > 80:
                exp = exp[:80] + "......"

        text = f"回答错误。{correct_part}。{exp}"
        return text[:150]

    def _update_stats_display(self):
        self.lbl_total.configure(text=f"📚 {self.stats['total']}")
        self.lbl_correct.configure(text=f"✓ {self.stats['correct']}")
        self.lbl_wrong.configure(text=f"✗ {self.stats['wrong']}")
        # 分值显示：答对绿色+分，答错红色-分
        score = self.stats.get('score', 0)
        if score >= 0:
            self.lbl_score.configure(text=f"💯 +{score}分", fg=Theme.SUCCESS)
        else:
            self.lbl_score.configure(text=f"💯 {score}分", fg=Theme.DANGER)
        rate = 0
        if self.stats["total"] > 0:
            rate = round(self.stats["correct"] / self.stats["total"] * 100)
        self.lbl_rate.configure(text=f"{rate}%")

    # ──────────── 上下题 ────────────
    def _prev_question(self):
        if self.current_index > 0:
            self.current_index -= 1
            self._render_question()

    def _next_question(self):
        if self.current_index < len(self.questions) - 1:
            self.current_index += 1
            self._render_question()
        else:
            self._show_complete()

    # ──────────── 完成页面 ────────────
    def _show_complete(self):
        self._stop_exam_timer()
        self._clear_content()

        total = self.stats["total"]
        correct = self.stats["correct"]
        wrong = self.stats["wrong"]
        rate = round(correct / max(total, 1) * 100)

        emoji = "🎉" if rate >= 80 else ("👍" if rate >= 60 else "💪")
        msg = "太棒了!" if rate >= 80 else ("还不错!" if rate >= 60 else "继续加油!")

        center = tk.Frame(self.content_frame, bg=Theme.BG)
        center.pack(fill=tk.BOTH, expand=True)

        inner = tk.Frame(center, bg=Theme.BG)
        inner.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(inner, text=emoji, font=tkfont.Font(size=64), bg=Theme.BG).pack(pady=(0, 16))
        tk.Label(inner, text=msg, font=self.title_font, bg=Theme.BG, fg=Theme.TEXT).pack()

        mode_text = "章节练习" if self.mode == "practice" else "模拟考试"
        tk.Label(inner, text=f"{mode_text}完成", font=self.option_font,
                 bg=Theme.BG, fg=Theme.TEXT_SECONDARY).pack(pady=(4, 24))

        nums = tk.Frame(inner, bg=Theme.BG)
        nums.pack(pady=8)

        for label, value, color in [
            ("总题数", total, Theme.PRIMARY),
            ("答对", correct, Theme.SUCCESS),
            ("答错", wrong, Theme.DANGER),
            ("正确率", f"{rate}%", Theme.SUCCESS if rate >= 60 else Theme.DANGER),
        ]:
            f = tk.Frame(nums, bg=Theme.BG, padx=20)
            f.pack(side=tk.LEFT, padx=8)
            tk.Label(f, text=str(value), font=tkfont.Font(size=36, weight="bold"),
                     bg=Theme.BG, fg=color).pack()
            tk.Label(f, text=label, font=self.small_font, bg=Theme.BG,
                     fg=Theme.TEXT_SECONDARY).pack()

        btns = tk.Frame(inner, bg=Theme.BG)
        btns.pack(pady=24)

        tk.Button(btns, text="🔄 重新开始", font=self.option_font,
                  bg=Theme.PRIMARY, fg="white", bd=0, padx=20, pady=8,
                  command=self._restart_practice).pack(side=tk.LEFT, padx=8)

        tk.Button(btns, text="📚 选择其他章节", font=self.option_font,
                  bg=Theme.BG, fg=Theme.TEXT_SECONDARY, bd=1, relief=tk.GROOVE,
                  padx=20, pady=8, command=self._show_welcome).pack(side=tk.LEFT, padx=8)

    def _restart_practice(self):
        self.stats = {"total": 0, "correct": 0, "wrong": 0, "score": 0}
        self._update_stats_display()
        self.current_index = 0
        self._render_question()

    # ──────────── 欢迎页 ────────────
    def _show_welcome(self):
        self._stop_exam_timer()
        self._clear_content()
        self.current_chapter = None
        self.questions = []

        # 用 frame 嵌套实现居中,不用 place()(canvas 内部 frame 的 place 定位不可靠)
        # 注意:不能用 pack_propagate(False),会阻止 content_frame 自动调整大小,
        # 导致后续 _render_question() 的所有内容也无法显示

        # 外层容器:撑满整个内容区
        outer = tk.Frame(self.content_frame, bg=Theme.BG)
        outer.pack(fill=tk.BOTH, expand=True)

        # 内层容器:垂直居中(用 pack 的 expand 实现)
        center = tk.Frame(outer, bg=Theme.BG)
        center.pack(expand=True)

        # 书本图标(用Label模拟)
        icon_frame = tk.Frame(center, bg=Theme.PRIMARY, width=80, height=80)
        icon_frame.pack(pady=(0, 20))
        icon_frame.pack_propagate(0)
        tk.Label(icon_frame, text="📖", font=tkfont.Font(size=40),
                 bg=Theme.PRIMARY, fg="white").pack(expand=True, fill=tk.BOTH)

        # 标题
        tk.Label(center, text="欢迎使用全能学练考系统",
                 font=tkfont.Font(family="Microsoft YaHei UI", size=26, weight="bold"),
                 bg=Theme.BG, fg=Theme.TEXT).pack()

        # 描述文字
        desc_text = "选择左侧教材目录,开始针对特定章节进行练习,巩固知识点。"
        desc_text += "系统包含海量精选题目,涵盖初中生物和地理全部知识点。"
        tk.Label(center, text=desc_text,
                 font=self.option_font, bg=Theme.BG, fg=Theme.TEXT_SECONDARY,
                 justify=tk.CENTER, wraplength=500).pack(pady=(12, 28))

        # 统计卡片
        stats_card = tk.Frame(center, bg=Theme.BG_CARD, padx=32, pady=20,
                              relief=tk.FLAT, bd=1)
        stats_card.pack()

        # 卡片标题
        tk.Label(stats_card, text="📊 题库统计",
                 font=tkfont.Font(family="Microsoft YaHei UI", size=13, weight="bold"),
                 bg=Theme.BG_CARD, fg=Theme.TEXT).pack(pady=(0, 16))

        total_q = self.qb.get_total_count()
        subject_count = len(self.qb.get_all_subjects())
        stats_data = [
            ("题目总数", f"{total_q}+", "道精选题目"),
            ("涵盖科目", str(subject_count), "个学科"),
            ("学期内容", "4", "个学期"),
            ("章节覆盖", "50+", "个章节"),
        ]

        for label, value, sub in stats_data:
            sf = tk.Frame(stats_card, bg=Theme.BG_CARD, padx=16, pady=10)
            sf.pack(side=tk.LEFT, padx=12)
            tk.Label(sf, text=value, font=tkfont.Font(size=28, weight="bold"),
                     bg=Theme.BG_CARD, fg=Theme.PRIMARY).pack()
            tk.Label(sf, text=label, font=self.small_font,
                     bg=Theme.BG_CARD, fg=Theme.TEXT_SECONDARY).pack()
            tk.Label(sf, text=sub, font=tkfont.Font(family="Microsoft YaHei UI", size=8),
                     bg=Theme.BG_CARD, fg=Theme.TEXT_LIGHT).pack()

        # 底部提示
        tk.Label(center, text="💡 提示:点击左侧章节即可开始练习,支持单选题/判断题/填空题/识图题四种题型",
                 font=self.small_font, bg=Theme.BG, fg=Theme.TEXT_LIGHT,
                 justify=tk.CENTER, wraplength=480).pack(pady=(28, 0))

    def _show_message(self, title, msg):
        self._clear_content()
        center = tk.Frame(self.content_frame, bg=Theme.BG)
        center.pack(fill=tk.BOTH, expand=True)
        inner = tk.Frame(center, bg=Theme.BG)
        inner.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(inner, text=title, font=self.title_font, bg=Theme.BG, fg=Theme.TEXT).pack()
        tk.Label(inner, text=msg, font=self.option_font, bg=Theme.BG, fg=Theme.TEXT_SECONDARY).pack(pady=8)

    # ──────────── 错题本 ────────────
    def _show_wrong_book(self):
        self._stop_exam_timer()
        self._clear_content()

        with _db_lock:
            db = get_db()
            try:
                rows = db.execute("""
                    SELECT * FROM wrong_answers ORDER BY last_wrong_at DESC LIMIT 100
                """).fetchall()
                wrong_list = []
                for row in rows:
                    item = dict(row)
                    if item.get("options"):
                        try:
                            item["options"] = json.loads(item["options"])
                        except Exception:
                            item["options"] = []
                    wrong_list.append(item)
            finally:
                db.close()

        header = tk.Frame(self.content_frame, bg=Theme.BG_CARD, padx=20, pady=12)
        header.pack(fill=tk.X, padx=16, pady=8)

        tk.Label(header, text="📋 错题本", font=tkfont.Font(size=18, weight="bold"),
                 bg=Theme.BG_CARD, fg=Theme.TEXT).pack(side=tk.LEFT)
        tk.Label(header, text=f"共 {len(wrong_list)} 道错题",
                 font=self.option_font, bg=Theme.BG_CARD, fg=Theme.TEXT_SECONDARY).pack(side=tk.LEFT, padx=12)

        if wrong_list:
            tk.Button(header, text="🔄 错题重练", font=self.option_font,
                      bg=Theme.PRIMARY, fg="white", bd=0, padx=12, pady=4,
                      command=lambda: self._start_wrong_practice(wrong_list)).pack(side=tk.RIGHT, padx=4)

        tk.Button(header, text="📚 返回", font=self.small_font,
                  bg=Theme.BG, fg=Theme.TEXT_SECONDARY, bd=1, relief=tk.GROOVE,
                  padx=8, pady=2, command=self._show_welcome).pack(side=tk.RIGHT, padx=4)

        if not wrong_list:
            tk.Label(self.content_frame, text="🎉 太棒了!暂无错题", font=self.title_font,
                     bg=Theme.BG, fg=Theme.SUCCESS).pack(pady=40)
            return

        for idx, item in enumerate(wrong_list):
            card = tk.Frame(self.content_frame, bg=Theme.BG_CARD, padx=16, pady=12)
            card.pack(fill=tk.X, padx=16, pady=4)

            ch = tk.Frame(card, bg=Theme.BG_CARD)
            ch.pack(fill=tk.X)

            q_type = item.get("question_type", "select")
            diff = item.get("difficulty", "medium")

            tk.Label(ch, text=f"#{idx+1}", bg=Theme.BG_CARD, fg=Theme.TEXT_LIGHT,
                     font=self.small_font).pack(side=tk.LEFT, padx=(0, 8))

            type_color = TYPE_COLORS.get(q_type, Theme.PRIMARY)
            tk.Label(ch, text=f" {TYPE_LABELS.get(q_type, '题目')} ",
                     bg=type_color, fg="white", font=self.badge_font, padx=6).pack(side=tk.LEFT, padx=(0, 4))

            diff_color = Theme.DIFF_COLORS.get(diff, Theme.WARNING)
            diff_bg = Theme.DIFF_BG.get(diff, Theme.WARNING_LIGHT)
            tk.Label(ch, text=f" {Theme.DIFF_LABELS.get(diff, '中等')} ",
                     bg=diff_bg, fg=diff_color, font=self.badge_font, padx=6).pack(side=tk.LEFT, padx=(0, 8))

            wc = item.get("wrong_count", 1)
            tk.Label(ch, text=f"做错{wc}次", bg=Theme.BG_CARD, fg=Theme.DANGER,
                     font=self.small_font).pack(side=tk.LEFT)

            wid = item.get("id")
            tk.Button(ch, text="✓ 移除", font=self.small_font,
                      bg=Theme.BG, fg=Theme.TEXT_SECONDARY, bd=0, padx=6,
                      command=lambda w=wid: self._remove_wrong(w)).pack(side=tk.RIGHT)

            q_text = item.get("question_text", "题目内容加载失败")
            tk.Label(card, text=q_text, bg=Theme.BG_CARD, fg=Theme.TEXT,
                     font=self.option_font, wraplength=700, justify=tk.LEFT).pack(
                fill=tk.X, pady=(8, 4), anchor="w")

            # 错题本中填空题显示填好答案的版本
            if q_type in ("fill", "image_fill", "image_hotspot"):
                ca_raw = item.get("correct_answer", "")
                if ca_raw and ca_raw != "?":
                    try:
                        import ast
                        ca_list = ast.literal_eval(ca_raw) if ca_raw.startswith("[") else [ca_raw]
                    except Exception:
                        ca_list = [ca_raw]
                    if isinstance(ca_list, list) and len(ca_list) > 0:
                        filled_q = self._embed_answers_in_text(q_text, ca_list)
                        if filled_q != q_text:
                            filled_frame = tk.Frame(card, bg="#ECFDF5", padx=12, pady=8)
                            filled_frame.pack(fill=tk.X, pady=(4, 4))
                            tk.Label(filled_frame, text="📋 标准答案填空", bg="#ECFDF5", fg="#065F46",
                                     font=self.small_font).pack(anchor="w")
                            tk.Label(filled_frame, text=filled_q, bg="#ECFDF5", fg="#064E3B",
                                     font=self.small_font, wraplength=700, justify=tk.LEFT).pack(anchor="w", pady=(2, 0))

            opts = item.get("options", [])
            if opts and isinstance(opts, list):
                letters = ["A", "B", "C", "D"]
                for i, opt in enumerate(opts[:4]):
                    tk.Label(card, text=f"  {letters[i]}. {opt}", bg=Theme.BG_CARD,
                             fg=Theme.TEXT_SECONDARY, font=self.small_font,
                             anchor="w").pack(fill=tk.X)

            ans_frame = tk.Frame(card, bg=Theme.BG_CARD)
            ans_frame.pack(fill=tk.X, pady=(8, 0))

            user_ans = item.get("user_answer", "?")
            correct_ans = item.get("correct_answer", "?")
            tk.Label(ans_frame, text=f"✗ 你的答案:{user_ans}", bg=Theme.DANGER_LIGHT,
                     fg=Theme.DANGER, font=self.small_font, padx=8, pady=2).pack(side=tk.LEFT, padx=(0, 8))
            tk.Label(ans_frame, text=f"✓ 正确答案:{correct_ans}", bg=Theme.SUCCESS_LIGHT,
                     fg=Theme.SUCCESS, font=self.small_font, padx=8, pady=2).pack(side=tk.LEFT)

            exp = item.get("explanation", "")
            if exp:
                clean = exp
                for tag in ["【A错因】", "【B错因】", "【C错因】", "【关键点】", "【易错提示】"]:
                    clean = clean.replace(tag, " | ")
                tk.Label(card, text=f"📖 {clean.strip()}", bg=Theme.BG_CARD,
                         fg=Theme.TEXT_SECONDARY, font=self.small_font,
                         wraplength=700, justify=tk.LEFT).pack(fill=tk.X, pady=(8, 0), anchor="w")

    def _remove_wrong(self, wrong_id):
        with _db_lock:
            db = get_db()
            try:
                db.execute("DELETE FROM wrong_answers WHERE id = ?", (wrong_id,))
                db.commit()
            finally:
                db.close()
        self._show_wrong_book()

    def _start_wrong_practice(self, wrong_list):
        questions = []
        for item in wrong_list:
            q = {
                "id": item.get("question_id", f"wrong_{item.get('id')}"),
                "type": item.get("question_type", "select"),
                "question": item.get("question_text", ""),
                "options": item.get("options", []),
                "answer": item.get("correct_answer"),
                "explanation": item.get("explanation", ""),
                "difficulty": item.get("difficulty", "medium"),
                "topic": item.get("topic", ""),
            }
            if q["type"] == "select" and isinstance(q["answer"], str):
                try:
                    q["answer"] = int(q["answer"])
                except ValueError:
                    pass
            elif q["type"] == "judge" and isinstance(q["answer"], str):
                q["answer"] = q["answer"].lower() in ("true", "1", "正确")

            questions.append(q)

        random.shuffle(questions)
        self.questions = questions[:50]
        self.current_index = 0
        self.answered = False
        self.stats = {"total": 0, "correct": 0, "wrong": 0, "score": 0}
        self.mode = "practice"
        self.mode_var.set("practice")
        self._update_stats_display()
        self._render_question()

    # ──────────── 考试计时器 ────────────
    def _start_exam_timer(self):
        self._stop_exam_timer()
        self.exam_time_left = 45 * 60
        self._tick_timer()

    def _tick_timer(self):
        if self.exam_time_left <= 0:
            self._show_complete()
            return
        mins = self.exam_time_left // 60
        secs = self.exam_time_left % 60
        self.lbl_timer.configure(text=f"⏱ {mins:02d}:{secs:02d}")
        if self.exam_time_left <= 300:
            self.lbl_timer.configure(fg=Theme.DANGER)
        self.exam_time_left -= 1
        self.exam_timer_id = self.after(1000, self._tick_timer)

    def _stop_exam_timer(self):
        if self.exam_timer_id:
            self.after_cancel(self.exam_timer_id)
            self.exam_timer_id = None
        self.lbl_timer.configure(text="")

    # ──────────── 拖拽 ────────────
    def _drag_bindings(self):
        """无边框窗口拖拽支持"""
        self._drag_data = {'x': 0, 'y': 0}
        def on_motion(event):
            deltax = event.x - self._drag_data['x']
            deltay = event.y - self._drag_data['y']
            x = self.winfo_x() + deltax
            y = self.winfo_y() + deltay
            self.geometry(f'+{x}+{y}')
        self.bind('<Button-1>', lambda e: self._drag_data.update({'x': e.x, 'y': e.y}))
        self.bind('<B1-Motion>', on_motion)

    # ──────────── 湖南生地会考倒计时 ────────────
    def _update_countdown(self):
        """更新湖南生地会考倒计时显示"""
        try:
            from datetime import date
            # 湖南生地会考通常在每年6月第三周周三（参考日期：6月18日）
            today = date.today()
            exam_date = date(today.year, 6, 18)
            if today > exam_date:
                exam_date = date(today.year + 1, 6, 18)  # 明年会考
            remaining = (exam_date - today).days
            if remaining == 0:
                text = "🔥 今天生地会考！加油！"
                self.lbl_hunan_countdown.config(fg=Theme.DANGER)
            elif remaining <= 7:
                text = f"⚡ 生地会考倒计时：{remaining} 天！"
                self.lbl_hunan_countdown.config(fg=Theme.DANGER)
            elif remaining <= 30:
                text = f"📅 生地会考倒计时：{remaining} 天"
                self.lbl_hunan_countdown.config(fg=Theme.WARNING)
            else:
                text = f"📅 生地会考倒计时：{remaining} 天"
                self.lbl_hunan_countdown.config(fg=Theme.TEXT_SECONDARY)
            self.lbl_hunan_countdown.config(text=text)
        except Exception:
            pass
        # 每小时更新一次
        self.after(3600000, self._update_countdown)  # 3600000ms = 1小时

    # ──────────── 关闭 ────────────
    def _toggle_maximize(self):
        """切换窗口最大化/还原"""
        if self._is_maximized:
            self._normal_geometry = self.geometry()
            self.geometry("1280x800")
            self._is_maximized = False
            self.max_btn.config(text="⬜")
        else:
            self._normal_geometry = self.geometry()
            self.attributes("-fullscreen", True)
            self._is_maximized = True
            self.max_btn.config(text="❐")

    def _on_close(self):
        self._stop_exam_timer()
        # 停止TTS工作线程
        _tts_stop_event.set()
        self.destroy()


# ============ 启动 ============
if __name__ == "__main__":
    if sys.platform == "win32":
        import io
        try:
            if hasattr(sys.stdout, "buffer"):
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
            if hasattr(sys.stderr, "buffer"):
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
        except Exception:
            pass

    init_db()

    print("\n" + "=" * 50)
    print("  全能学练考桌面版 v1.0 启动中...")
    print("=" * 50)

    app = StudyApp()
    app.mainloop()
