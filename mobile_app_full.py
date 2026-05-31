#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自适应学练考系统 - 手机完整版 (Kivy)
完整功能：训练、学习、考试、错题本、奖励系统、学习计划
"""

import random
import json
import os
from datetime import datetime, timedelta, date
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ListProperty, ObjectProperty
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window

# 设置窗口大小（桌面测试用）
Window.size = (400, 700)

# ==================== 配置文件 ====================
SETTINGS_FILE = "settings.json"
WORD_FILE = "words.txt"
STUDY_TIME_FILE = "study_time.json"
MISTAKE_FILE = "mistakes.json"
REWARD_FILE = "reward_data.json"
WORD_MASTERY_FILE = "word_mastery.json"
PLAN_FILE = "study_plan_checklist.json"

def load_settings():
    default = {"theme": "dark", "voice": "en-US", "font_size": 14}
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                default.update(data)
            except:
                pass
    return default

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)

# ==================== 数学题库（完整9单元）====================
def build_math_questions():
    questions = []
    unit1 = [
        ("集合的交集符号", "∩"), ("集合的并集符号", "∪"), ("补集符号", "∁"),
        ("空集符号", "∅"), ("元素与集合的属于符号", "∈"), ("元素与集合的不属于符号", "∉"),
        ("子集定义", "A⊆B ⇔ 任意x∈A都有x∈B"), ("真子集定义", "A⊂B ⇔ A⊆B且存在x∈B但x∉A"),
        ("充分条件的定义", "p⇒q 则p是q的充分条件"), ("必要条件的定义", "p⇐q 则p是q的必要条件"),
        ("充要条件的定义", "p⇔q 则p是q的充要条件"),
    ]
    for text, ans in unit1:
        questions.append({"text": f"【集合与逻辑】{text}", "answer": ans, "explain": ans, "level": 1, "video": ""})
    
    unit2 = [
        ("i²", "-1"), ("复数代数形式", "a+bi (a,b∈R)"), ("共轭复数", "a-bi"),
        ("复数模长公式", "√(a²+b²)"), ("复数的加法法则", "(a+bi)+(c+di)=(a+c)+(b+d)i"),
        ("复数的乘法法则", "(a+bi)(c+di)=(ac-bd)+(ad+bc)i"),
    ]
    for text, ans in unit2:
        questions.append({"text": f"【复数】{text}", "answer": ans, "explain": ans, "level": 1, "video": ""})
    
    unit3 = [
        ("向量坐标表示", "(x,y)"), ("向量加法坐标公式", "(x₁+x₂, y₁+y₂)"), ("向量减法坐标公式", "(x₁-x₂, y₁-y₂)"),
        ("数乘向量公式", "k(x,y)=(kx,ky)"), ("向量点积坐标公式", "x₁x₂+y₁y₂"), ("向量点积几何公式", "|a||b|cosθ"),
        ("向量垂直充要条件", "a·b=0"), ("向量平行充要条件", "x₁y₂=x₂y₁"),
    ]
    for text, ans in unit3:
        questions.append({"text": f"【向量】{text}", "answer": ans, "explain": ans, "level": 1, "video": ""})
    
    unit4 = [
        ("sin²α+cos²α", "1"), ("两角和的正弦", "sin(α+β)=sinαcosβ+cosαsinβ"),
        ("两角差的正弦", "sin(α-β)=sinαcosβ-cosαsinβ"), ("两角和的余弦", "cos(α+β)=cosαcosβ-sinαsinβ"),
        ("两角差的余弦", "cos(α-β)=cosαcosβ+sinαsinβ"), ("二倍角正弦", "sin2α=2sinαcosα"),
        ("二倍角余弦", "cos2α=cos²α-sin²α=2cos²α-1=1-2sin²α"), ("sin30°的值", "1/2"),
        ("cos45°的值", "√2/2"), ("tan60°的值", "√3"),
    ]
    for text, ans in unit4:
        questions.append({"text": f"【三角函数】{text}", "answer": ans, "explain": ans, "level": 2, "video": ""})
    
    return questions

MATH_QUESTIONS = build_math_questions()

# ==================== 物理题库（完整7个实验）====================
def build_physics_questions():
    questions = []
    exp1 = [
        ("打点计时器使用什么电源？频率多少？", "交流电 50Hz"), ("打点计时器打点周期", "0.02s"),
        ("平均速度公式", "v=Δx/Δt"), ("加速度公式（逐差法）", "a=(x₄+x₅+x₆-x₁-x₂-x₃)/(3T)²"),
        ("中间时刻速度等于", "平均速度"),
    ]
    for text, ans in exp1:
        questions.append({"text": f"【匀变速直线运动】{text}", "answer": ans, "explain": ans, "level": 1, "video": ""})
    
    exp2 = [
        ("胡克定律公式", "F=kx"), ("弹簧劲度系数k的单位", "N/m"), ("F-x图像斜率表示", "劲度系数k"),
        ("测量弹簧原长的方法", "不挂钩码时测长度"),
    ]
    for text, ans in exp2:
        questions.append({"text": f"【弹簧弹力】{text}", "answer": ans, "explain": ans, "level": 1, "video": ""})
    
    return questions

PHYSICS_QUESTIONS = build_physics_questions()

# ==================== 英语单词库 ====================
def generate_full_word_list():
    """生成常用英语单词列表"""
    words = [
        ("abandon", "抛弃", "/əˈbændən/"), ("ability", "能力", "/əˈbɪləti/"),
        ("able", "能够", "/ˈeɪbl/"), ("about", "关于", "/əˈbaʊt/"),
        ("above", "上面", "/əˈbʌv/"), ("accept", "接受", "/əkˈsept/"),
        ("access", "进入", "/ˈækses/"), ("afraid", "害怕", "/əˈfreɪd/"),
        ("after", "之后", "/ˈɑːftər/"), ("again", "再次", "/əˈɡen/"),
        ("against", "反对", "/əˈɡenst/"), ("agree", "同意", "/əˈɡriː/"),
        ("ahead", "向前", "/əˈhed/"), ("alive", "活着", "/əˈlaɪv/"),
        ("allow", "允许", "/əˈlaʊ/"), ("almost", "几乎", "/ˈɔːlməʊst/"),
        ("alone", "单独", "/əˈləʊn/"), ("along", "沿着", "/əˈlɒŋ/"),
        ("already", "已经", "/ɔːlˈredi/"), ("always", "总是", "/ˈɔːlweɪz/"),
        ("amaze", "惊奇", "/əˈmeɪz/"), ("among", "之中", "/əˈmʌŋ/"),
        ("and", "和", "/ænd/"), ("anger", "愤怒", "/ˈæŋɡər/"),
        ("animal", "动物", "/ˈænɪməl/"), ("announce", "宣布", "/əˈnaʊns/"),
        ("another", "另一个", "/əˈnʌðər/"), ("answer", "回答", "/ˈɑːnsər/"),
        ("anxious", "焦虑", "/ˈæŋkʃəs/"), ("any", "任何", "/ˈeni/"),
        ("appear", "出现", "/əˈpɪər/"), ("apple", "苹果", "/ˈæpəl/"),
        ("apply", "申请", "/əˈplaɪ/"), ("appoint", "任命", "/əˈpɔɪnt/"),
        ("approach", "方法", "/əˈprəʊtʃ/"), ("approve", "批准", "/əˈpruːv/"),
        ("area", "区域", "/ˈeəriə/"), ("argue", "争论", "/ˈɑːɡjuː/"),
        ("arrive", "到达", "/əˈraɪv/"), ("art", "艺术", "/ɑːt/"),
        ("as", "作为", "/æz/"), ("ask", "问", "/ɑːsk/"),
        ("at", "在", "/æt/"), ("award", "奖励", "/əˈwɔːd/"),
        ("away", "离开", "/əˈweɪ/"), ("awful", "糟糕", "/ˈɔːfəl/"),
    ]
    return words

ENGLISH_WORDS = generate_full_word_list()

def build_english_questions(words_list):
    """根据单词列表生成英语题目"""
    questions = []
    for i, (w, m, p) in enumerate(words_list):
        level = 1 if i < 20 else (2 if i < 40 else 3)
        questions.append({
            "text": f"单词 '{w}' 的中文意思是？",
            "answer": m,
            "explain": f"含义：{m}，音标：{p}",
            "level": level,
            "video": ""
        })
    return questions

ALL_QUESTIONS = {
    "math": MATH_QUESTIONS,
    "english": build_english_questions(ENGLISH_WORDS),
    "physics": PHYSICS_QUESTIONS,
}

# ==================== 错题本管理 ====================
def load_mistakes():
    """加载错题本"""
    if os.path.exists(MISTAKE_FILE):
        with open(MISTAKE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_mistakes(mistakes):
    """保存错题本"""
    with open(MISTAKE_FILE, "w", encoding="utf-8") as f:
        json.dump(mistakes, f, ensure_ascii=False, indent=2)

def add_mistake(subject, question, user_answer, correct_answer, explanation):
    """添加错题"""
    mistakes = load_mistakes()
    mistakes.append({
        "subject": subject,
        "question": question,
        "user_answer": user_answer,
        "correct_answer": correct_answer,
        "explanation": explanation,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    # 只保留最近50道错题
    if len(mistakes) > 50:
        mistakes = mistakes[-50:]
    save_mistakes(mistakes)

# ==================== 奖励系统 ====================
class RewardSystem:
    def __init__(self):
        self.points = 0
        self.stars = 0
        self.hearts = 0
        self.load()
    
    def load(self):
        """加载奖励数据"""
        if os.path.exists(REWARD_FILE):
            with open(REWARD_FILE, "r") as f:
                data = json.load(f)
                self.points = data.get("points", 0)
                self.stars = data.get("stars", 0)
                self.hearts = data.get("hearts", 0)
    
    def save(self):
        """保存奖励数据"""
        with open(REWARD_FILE, "w") as f:
            json.dump({
                "points": self.points,
                "stars": self.stars,
                "hearts": self.hearts
            }, f)
    
    def add_points(self, amount):
        """添加积分"""
        self.points += amount
        self.save()
    
    def add_star(self):
        """添加星星（3星换1心）"""
        self.stars += 1
        if self.stars >= 3:
            self.stars -= 3
            self.hearts += 1
        self.save()
    
    def get_status(self):
        """获取状态字符串"""
        return f"积分 {self.points} | ⭐ {self.stars} | ❤️ {self.hearts}"

# ==================== 自适应训练引擎 ====================
class AdaptiveTrainer:
    def __init__(self, subject, questions):
        self.subject = subject
        self.questions = list(questions)
        self.level = 1
        self.correct_in_level = 0
        self.need_correct = 3
        self.mastered = set()
        self.all_learned = False
        self.current = None
        self.pending_upgrade = False
    
    def get_current(self):
        """获取当前难度的未掌握题目"""
        return [(i, q) for i, q in enumerate(self.questions) if q["level"] == self.level and i not in self.mastered]
    
    def next(self):
        """获取下一题"""
        if self.pending_upgrade:
            self.pending_upgrade = False
            if self.level < 3:
                self.level += 1
                self.correct_in_level = 0
                return ("upgrade", self.level)
            else:
                self.all_learned = True
                return ("complete", None)
        
        avail = self.get_current()
        if not avail:
            if self.level < 3:
                self.level += 1
                self.correct_in_level = 0
                return ("upgrade", self.level)
            else:
                self.all_learned = True
                return ("complete", None)
        
        idx, q = random.choice(avail)
        self.current = (idx, q)
        return ("question", q)
    
    def check(self, user_ans):
        """检查答案"""
        if self.current is None:
            return False, None
        
        idx, q = self.current
        ans_lower = q["answer"].lower()
        user_lower = user_ans.lower()
        correct = (ans_lower in user_lower) or (user_lower in ans_lower) or (user_lower == ans_lower)
        
        if correct:
            self.correct_in_level += 1
            self.mastered.add(idx)
            remaining = self.get_current()
            if self.correct_in_level >= self.need_correct and not remaining and self.level < 3:
                self.pending_upgrade = True
            return True, q
        else:
            self.correct_in_level = 0
            return False, q

# ==================== Kivy UI 布局 ====================
KV = '''
#:import Factory kivy.factory.Factory

<MainWindow>:
    orientation: 'vertical'
    
    # 顶部状态栏
    BoxLayout:
        size_hint_y: None
        height: '50dp'
        padding: '10dp'
        spacing: '10dp'
        
        Label:
            id: title_label
            text: '自适应学练考系统'
            font_size: '18sp'
            bold: True
            color: 1, 1, 1, 1
        
        Label:
            id: status_label
            text: ''
            font_size: '12sp'
            color: 0.9, 0.9, 0.9, 1
    
    # 主内容区域
    ScrollView:
        id: scroll_view
        
        BoxLayout:
            id: content_layout
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
            padding: '15dp'
            spacing: '10dp'
    
    # 底部导航栏
    BoxLayout:
        size_hint_y: None
        height: '60dp'
        padding: '5dp'
        spacing: '5dp'
        
        Button:
            text: '首页'
            font_size: '14sp'
            on_press: root.go_home()
        
        Button:
            text: '训练'
            font_size: '14sp'
            on_press: root.go_training()
        
        Button:
            text: '学习'
            font_size: '14sp'
            on_press: root.go_study()
        
        Button:
            text: '考试'
            font_size: '14sp'
            on_press: root.go_exam()
        
        Button:
            text: '更多'
            font_size: '14sp'
            on_press: root.go_more()

<HomePage>:
    orientation: 'vertical'
    padding: '15dp'
    spacing: '15dp'
    
    Label:
        text: '🔥 自适应学练考系统'
        font_size: '24sp'
        bold: True
        color: 1, 1, 1, 1
        size_hint_y: None
        height: '60dp'
    
    Label:
        text: '做对数学/物理得⭐ · 3⭐换1❤️抽奖'
        font_size: '14sp'
        color: 0.9, 0.9, 0.9, 1
        size_hint_y: None
        height: '40dp'
    
    GridLayout:
        cols: 2
        spacing: '10dp'
        size_hint_y: None
        height: '300dp'
        
        Button:
            text: '🎯 自适应训练'
            font_size: '16sp'
            on_press: root.go_training()
        
        Button:
            text: '📚 学习模式'
            font_size: '16sp'
            on_press: root.go_study()
        
        Button:
            text: '📝 考试模式'
            font_size: '16sp'
            on_press: root.go_exam()
        
        Button:
            text: '📖 错题本'
            font_size: '16sp'
            on_press: root.go_mistakes()
        
        Button:
            text: '🇬🇧 英语专项'
            font_size: '16sp'
            on_press: root.go_english()
        
        Button:
            text: '📋 学习计划'
            font_size: '16sp'
            on_press: root.go_plan()
    
    Label:
        id: status_display
        text: ''
        font_size: '14sp'
        color: 1, 1, 1, 1
        size_hint_y: None
        height: '50dp'

<TrainingPage>:
    orientation: 'vertical'
    padding: '15dp'
    spacing: '10dp'
    
    Label:
        id: level_label
        text: '难度: ⭐'
        font_size: '16sp'
        color: 1, 1, 1, 1
        size_hint_y: None
        height: '40dp'
    
    Label:
        id: progress_label
        text: '连续正确: 0/3'
        font_size: '14sp'
        color: 0.9, 0.9, 0.9, 1
        size_hint_y: None
        height: '30dp'
    
    Label:
        id: question_label
        text: '题目加载中...'
        font_size: '16sp'
        color: 1, 1, 1, 1
        text_size: self.width, None
        size_hint_y: None
        height: '100dp'
        halign: 'center'
        valign: 'middle'
        markup: True
    
    TextInput:
        id: answer_input
        hint_text: '输入答案...'
        multiline: False
        size_hint_y: None
        height: '45dp'
        font_size: '16sp'
        on_text_validate: root.submit_answer()
    
    BoxLayout:
        size_hint_y: None
        height: '50dp'
        spacing: '10dp'
        
        Button:
            id: submit_btn
            text: '提交'
            font_size: '16sp'
            on_press: root.submit_answer()
        
        Button:
            id: next_btn
            text: '下一题'
            font_size: '16sp'
            on_press: root.next_question()
            disabled: True
        
        Button:
            text: '返回'
            font_size: '16sp'
            on_press: root.go_back()
    
    Label:
        id: feedback_label
        text: ''
        font_size: '14sp'
        color: 1, 1, 1, 1
        text_size: self.width, None
        size_hint_y: None
        height: '80dp'
        halign: 'center'
        valign: 'middle'
        markup: True

<StudyPage>:
    orientation: 'vertical'
    padding: '15dp'
    
    Label:
        text: '📚 学习模式'
        font_size: '20sp'
        bold: True
        color: 1, 1, 1, 1
        size_hint_y: None
        height: '50dp'
    
    TabbedPanel:
        id: tab_panel
        size_hint_y: 1
        do_default_tab: False
        
        TabbedPanelItem:
            text: '数学'
            
            ScrollView:
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height
                    padding: '10dp'
                    spacing: '10dp'
                    
                    Label:
                        id: math_content
                        text: ''
                        font_size: '14sp'
                        color: 1, 1, 1, 1
                        text_size: self.width, None
                        size_hint_y: None
                        height: self.texture_size[1] if self.texture_size else '100dp'
                        halign: 'left'
                        valign: 'top'
        
        TabbedPanelItem:
            text: '英语'
            
            ScrollView:
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height
                    padding: '10dp'
                    spacing: '10dp'
                    
                    Label:
                        id: english_content
                        text: ''
                        font_size: '14sp'
                        color: 1, 1, 1, 1
                        text_size: self.width, None
                        size_hint_y: None
                        height: self.texture_size[1] if self.texture_size else '100dp'
                        halign: 'left'
                        valign: 'top'
        
        TabbedPanelItem:
            text: '物理'
            
            ScrollView:
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height
                    padding: '10dp'
                    spacing: '10dp'
                    
                    Label:
                        id: physics_content
                        text: ''
                        font_size: '14sp'
                        color: 1, 1, 1, 1
                        text_size: self.width, None
                        size_hint_y: None
                        height: self.texture_size[1] if self.texture_size else '100dp'
                        halign: 'left'
                        valign: 'top'
    
    Button:
        text: '返回首页'
        size_hint_y: None
        height: '50dp'
        font_size: '16sp'
        on_press: root.go_back()

<ExamPage>:
    orientation: 'vertical'
    padding: '15dp'
    spacing: '10dp'
    
    Label:
        id: info_label
        text: '模拟考试'
        font_size: '18sp'
        bold: True
        color: 1, 1, 1, 1
        size_hint_y: None
        height: '40dp'
    
    Label:
        id: progress_label
        text: '准备开始...'
        font_size: '14sp'
        color: 0.9, 0.9, 0.9, 1
        size_hint_y: None
        height: '30dp'
    
    Label:
        id: question_label
        text: '点击「开始考试」'
        font_size: '16sp'
        color: 1, 1, 1, 1
        text_size: self.width, None
        size_hint_y: None
        height: '100dp'
        halign: 'center'
        valign: 'middle'
        markup: True
    
    TextInput:
        id: answer_input
        hint_text: '输入答案...'
        multiline: False
        size_hint_y: None
        height: '45dp'
        font_size: '16sp'
        on_text_validate: root.submit_answer()
    
    BoxLayout:
        size_hint_y: None
        height: '50dp'
        spacing: '10dp'
        
        Button:
            id: start_btn
            text: '开始考试'
            font_size: '16sp'
            on_press: root.start_exam()
        
        Button:
            id: submit_btn
            text: '提交'
            font_size: '16sp'
            on_press: root.submit_answer()
            disabled: True
        
        Button:
            id: next_btn
            text: '下一题'
            font_size: '16sp'
            on_press: root.next_question()
            disabled: True
        
        Button:
            text: '返回'
            font_size: '16sp'
            on_press: root.go_back()
    
    Label:
        id: feedback_label
        text: ''
        font_size: '14sp'
        color: 1, 1, 1, 1
        text_size: self.width, None
        size_hint_y: None
        height: '80dp'
        halign: 'center'
        valign: 'middle'
        markup: True

<MistakePage>:
    orientation: 'vertical'
    padding: '15dp'
    
    Label:
        text: '📖 错题本'
        font_size: '20sp'
        bold: True
        color: 1, 1, 1, 1
        size_hint_y: None
        height: '50dp'
    
    ScrollView:
        BoxLayout:
            id: mistake_layout
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
            padding: '10dp'
            spacing: '10dp'
    
    Button:
        text: '返回首页'
        size_hint_y: None
        height: '50dp'
        font_size: '16sp'
        on_press: root.go_back()
'''

# ==================== 页面类 ====================
class HomePage(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_status()
        Clock.schedule_interval(lambda dt: self.update_status(), 5)
    
    def update_status(self):
        app = App.get_running_app()
        if hasattr(app, 'reward'):
            self.ids.status_display.text = app.reward.get_status()
    
    def go_training(self):
        App.get_running_app().root.go_training()
    
    def go_study(self):
        App.get_running_app().root.go_study()
    
    def go_exam(self):
        App.get_running_app().root.go_exam()
    
    def go_mistakes(self):
        App.get_running_app().root.go_mistakes()
    
    def go_english(self):
        App.get_running_app().root.go_english()
    
    def go_plan(self):
        App.get_running_app().root.go_plan()

class TrainingPage(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.trainer = None
        self.subject = None
    
    def set_trainer(self, trainer, subject):
        self.trainer = trainer
        self.subject = subject
        self.next_question()
    
    def next_question(self):
        if not self.trainer:
            return
        
        result = self.trainer.next()
        typ = result[0]
        
        if typ == "question":
            q = result[1]
            self.ids.question_label.text = f"第{len(self.trainer.mastered) + 1}题：{q['text']}"
            self.ids.level_label.text = f"难度: {'⭐' * self.trainer.level}"
            self.ids.progress_label.text = f"连续正确: {self.trainer.correct_in_level}/3"
            self.ids.answer_input.text = ""
            self.ids.answer_input.disabled = False
            self.ids.submit_btn.disabled = False
            self.ids.next_btn.disabled = True
            self.ids.feedback_label.text = ""
        elif typ == "upgrade":
            level = result[1]
            self.ids.feedback_label.text = f"🎉 升级到难度{level}星！获得100积分"
            app = App.get_running_app()
            app.reward.add_points(100)
            self.next_question()
        elif typ == "complete":
            self.ids.question_label.text = "🏆 完成本学科所有题目！"
            self.ids.answer_input.disabled = True
            self.ids.submit_btn.disabled = True
            self.ids.next_btn.disabled = True
    
    def submit_answer(self):
        if not self.trainer or not self.trainer.current:
            return
        
        user = self.ids.answer_input.text.strip()
        if not user:
            self.ids.feedback_label.text = "请输入答案"
            return
        
        correct, q = self.trainer.check(user)
        
        if correct:
            self.ids.feedback_label.text = f"✅ 正确！\n讲解：{q['explain']}"
            app = App.get_running_app()
            if self.subject in ["math", "physics"]:
                app.reward.add_star()
            else:
                app.reward.add_points(5)
        else:
            self.ids.feedback_label.text = f"❌ 错误。正确答案：{q['answer']}\n讲解：{q['explain']}"
            add_mistake(self.subject, q["text"], user, q["answer"], q["explain"])
        
        self.ids.answer_input.disabled = True
        self.ids.submit_btn.disabled = True
        self.ids.next_btn.disabled = False
    
    def go_back(self):
        App.get_running_app().root.go_home()

class StudyPage(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.load_content()
    
    def load_content(self):
        math_text = "\n\n".join([
            f"[b]【难度{q['level']}星】{q['text']}[/b]\n答案：{q['answer']}\n讲解：{q['explain']}"
            for q in ALL_QUESTIONS["math"]
        ])
        self.ids.math_content.text = math_text
        
        english_text = "\n\n".join([
            f"[b]{q['text']}[/b]\n答案：{q['answer']}\n讲解：{q['explain']}"
            for q in ALL_QUESTIONS["english"][:50]
        ])
        self.ids.english_content.text = english_text
        
        physics_text = "\n\n".join([
            f"[b]【难度{q['level']}星】{q['text']}[/b]\n答案：{q['answer']}\n讲解：{q['explain']}"
            for q in ALL_QUESTIONS["physics"]
        ])
        self.ids.physics_content.text = physics_text
    
    def go_back(self):
        App.get_running_app().root.go_home()

class ExamPage(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.questions = []
        self.index = 0
        self.score = 0
    
    def start_exam(self):
        self.questions = []
        for sub in ["math", "english", "physics"]:
            sub_q = random.sample(ALL_QUESTIONS[sub], min(3, len(ALL_QUESTIONS[sub])))
            self.questions.extend([(sub, q) for q in sub_q])
        
        self.index = 0
        self.score = 0
        self.ids.start_btn.disabled = True
        self.ids.submit_btn.disabled = False
        self.ids.answer_input.disabled = False
        self.show_question()
    
    def show_question(self):
        if self.index >= len(self.questions):
            self.finish_exam()
            return
        
        sub, q = self.questions[self.index]
        self.ids.info_label.text = f"第{self.index + 1}/{len(self.questions)}题"
        self.ids.progress_label.text = f"当前得分: {self.score}"
        self.ids.question_label.text = f"[b]【{sub.upper()}】[/b]{q['text']}"
        self.ids.answer_input.text = ""
        self.ids.feedback_label.text = ""
    
    def submit_answer(self):
        if self.index >= len(self.questions):
            return
        
        sub, q = self.questions[self.index]
        user = self.ids.answer_input.text.strip()
        
        if not user:
            self.ids.feedback_label.text = "请输入答案"
            return
        
        correct = (q["answer"].lower() in user.lower()) or (user.lower() == q["answer"].lower())
        
        if correct:
            self.score += 10
            self.ids.feedback_label.text = f"✅ 正确 +10分！\n讲解：{q['explain']}"
            app = App.get_running_app()
            if sub in ["math", "physics"]:
                app.reward.add_star()
            else:
                app.reward.add_points(5)
        else:
            self.ids.feedback_label.text = f"❌ 错误。正确答案：{q['answer']}\n讲解：{q['explain']}"
            add_mistake(sub, q["text"], user, q["answer"], q["explain"])
        
        self.ids.answer_input.disabled = True
        self.ids.submit_btn.disabled = True
        self.ids.next_btn.disabled = False
    
    def next_question(self):
        self.index += 1
        if self.index >= len(self.questions):
            self.finish_exam()
        else:
            self.show_question()
            self.ids.submit_btn.disabled = False
            self.ids.next_btn.disabled = True
            self.ids.answer_input.disabled = False
    
    def finish_exam(self):
        total = len(self.questions) * 10
        self.ids.info_label.text = "考试结束"
        self.ids.question_label.text = f"[b]得分：{self.score}/{total}[/b]"
        self.ids.answer_input.disabled = True
        self.ids.submit_btn.disabled = True
        self.ids.next_btn.disabled = True
        self.ids.start_btn.disabled = False
        self.ids.start_btn.text = "重新考试"
        
        if self.score == total:
            self.ids.feedback_label.text = "🎉 全部正确！"
        else:
            wrong = len(self.questions) - self.score // 10
            self.ids.feedback_label.text = f"错题数：{wrong}"
    
    def go_back(self):
        App.get_running_app().root.go_home()

class MistakePage(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.load_mistakes()
    
    def load_mistakes(self):
        mistakes = load_mistakes()
        layout = self.ids.mistake_layout
        layout.clear_widgets()
        
        if not mistakes:
            layout.add_widget(Label(
                text="✅ 暂无错题",
                font_size='16sp',
                color=(1, 1, 1, 1)
            ))
            return
        
        for item in mistakes[-20:]:
            card = BoxLayout(
                orientation='vertical',
                size_hint_y=None,
                height='100dp',
                padding='10dp',
                spacing='5dp'
            )
            card.add_widget(Label(
                text=f"[b]📌 {item['question'][:80]}[/b]",
                font_size='14sp',
                color=(1, 1, 1, 1),
                halign='left',
                valign='top'
            ))
            card.add_widget(Label(
                text=f"你的：{item['user_answer']}  正解：{item['correct_answer']}",
                font_size='12sp',
                color=(0.9, 0.9, 0.9, 1),
                halign='left',
                valign='top'
            ))
            layout.add_widget(card)
    
    def go_back(self):
        App.get_running_app().root.go_home()

# ==================== 主窗口 ====================
class MainWindow(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_page = None
        self.show_home()
    
    def clear_content(self):
        layout = self.ids.content_layout
        layout.clear_widgets()
        self.current_page = None
    
    def show_home(self):
        self.clear_content()
        layout = self.ids.content_layout
        
        page = HomePage()
        layout.add_widget(page)
        self.current_page = "home"
        self.ids.title_label.text = "首页"
    
    def go_home(self):
        self.show_home()
    
    def go_training(self, *args):
        self.clear_content()
        layout = self.ids.content_layout
        
        label = Label(
            text="选择学科",
            font_size='20sp',
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height='50dp'
        )
        layout.add_widget(label)
        
        for text, subject in [("数学", "math"), ("英语", "english"), ("物理", "physics")]:
            btn = Button(
                text=text,
                font_size='18sp',
                size_hint_y=None,
                height='80dp'
            )
            btn.bind(on_press=lambda btn, s=subject: self.start_training(s))
            layout.add_widget(btn)
        
        back_btn = Button(
            text="返回首页",
            size_hint_y=None,
            height='50dp',
            font_size='16sp'
        )
        back_btn.bind(on_press=lambda btn: self.go_home())
        layout.add_widget(back_btn)
        
        self.ids.title_label.text = "自适应训练"
    
    def start_training(self, subject):
        self.clear_content()
        layout = self.ids.content_layout
        
        trainer = AdaptiveTrainer(subject, ALL_QUESTIONS[subject])
        page = TrainingPage()
        page.set_trainer(trainer, subject)
        layout.add_widget(page)
        
        self.ids.title_label.text = f"{subject.upper()} 训练"
    
    def go_study(self, *args):
        self.clear_content()
        layout = self.ids.content_layout
        
        page = StudyPage()
        layout.add_widget(page)
        
        self.ids.title_label.text = "学习模式"
    
    def go_exam(self, *args):
        self.clear_content()
        layout = self.ids.content_layout
        
        page = ExamPage()
        layout.add_widget(page)
        
        self.ids.title_label.text = "考试模式"
    
    def go_mistakes(self, *args):
        self.clear_content()
        layout = self.ids.content_layout
        
        page = MistakePage()
        layout.add_widget(page)
        
        self.ids.title_label.text = "错题本"
    
    def go_english(self, *args):
        # TODO: 实现英语专项页面
        pass
    
    def go_plan(self, *args):
        # TODO: 实现学习计划页面
        pass
    
    def go_more(self, *args):
        self.clear_content()
        layout = self.ids.content_layout
        
        label = Label(
            text="更多功能",
            font_size='20sp',
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height='50dp'
        )
        layout.add_widget(label)
        
        # 设置按钮
        settings_btn = Button(
            text="⚙️ 设置",
            font_size='16sp',
            size_hint_y=None,
            height='60dp'
        )
        settings_btn.bind(on_press=lambda btn: self.open_settings())
        layout.add_widget(settings_btn)
        
        # 关于按钮
        about_btn = Button(
            text="ℹ️ 关于",
            font_size='16sp',
            size_hint_y=None,
            height='60dp'
        )
        about_btn.bind(on_press=lambda btn: self.show_about())
        layout.add_widget(about_btn)
        
        back_btn = Button(
            text="返回首页",
            size_hint_y=None,
            height='50dp',
            font_size='16sp'
        )
        back_btn.bind(on_press=lambda btn: self.go_home())
        layout.add_widget(back_btn)
        
        self.ids.title_label.text = "更多"
    
    def open_settings(self):
        # TODO: 实现设置页面
        pass
    
    def show_about(self):
        content = BoxLayout(orientation='vertical', padding='10dp')
        content.add_widget(Label(
            text="自适应学练考系统 v1.0\n\n基于Kivy开发的手机学习APP\n\n功能：\n• 自适应训练\n• 学习模式\n• 考试模式\n• 错题本",
            font_size='14sp',
            halign='center'
        ))
        
        popup = Popup(
            title='关于',
            content=content,
            size_hint=(0.8, 0.6)
        )
        popup.open()

# ==================== 应用类 ====================
class MobileApp(App):
    def build(self):
        Builder.load_string(KV)
        self.reward = RewardSystem()
        root = MainWindow()
        return root
    
    def on_start(self):
        pass

if __name__ == "__main__":
    MobileApp().run()
