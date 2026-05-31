#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自适应学练考系统 v3.0 - PyQt5 GUI版
- 做对数学/物理题得⭐，3⭐换1❤，1❤抽一次实物奖励
- 升级得积分，英语题得积分
- 积分/⭐/❤持久化，错题本分析
"""

import random
import json
import os
import sys
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QTextEdit, QLineEdit,
    QMessageBox, QFrame, QScrollArea, QDesktopWidget
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor


# ==================== 题库（完全保留原内容） ====================
MATH_QUESTIONS = [
    {"text": "写出集合的交集符号", "answer": "∩", "explain": "交集表示两个集合的公共部分，符号是∩。", "level": 1, "video": "https://www.bilibili.com/video/BV1xx411c7mD?p=2"},
    {"text": "复数单位i的平方等于多少？", "answer": "-1", "explain": "i² = -1，是复数的基本定义。", "level": 1, "video": "https://www.bilibili.com/video/BV1gW411C7oM"},
    {"text": "向量的点积公式（坐标形式）", "answer": "x1x2+y1y2", "explain": "若a=(x1,y1), b=(x2,y2)，则a·b = x1x2 + y1y2。", "level": 1, "video": "https://www.bilibili.com/video/BV1ys411472E"},
    {"text": "sin²α+cos²α=?", "answer": "1", "explain": "同角三角函数的基本恒等式。", "level": 1, "video": "https://www.bilibili.com/video/BV1GJ411x7h7"},
    {"text": "等差数列通项公式", "answer": "an=a1+(n-1)d", "explain": "an = a1 + (n-1)d，d为公差。", "level": 1, "video": "https://www.bilibili.com/video/BV1Xx411r7tP"},
    {"text": "写出二次函数顶点坐标公式", "answer": "(-b/(2a), (4ac-b²)/(4a))", "explain": "对于y=ax²+bx+c，顶点横坐标x=-b/(2a)，纵坐标代入可得。", "level": 1, "video": "https://www.bilibili.com/video/BV1eJ411Q7G5"},
    {"text": "已知向量a=(2,3), b=(4,-1)，求a·b", "answer": "5", "explain": "2×4 + 3×(-1)=8-3=5。", "level": 2, "video": "https://www.bilibili.com/video/BV1ys411472E"},
    {"text": "若sinα=3/5，α为锐角，求cosα", "answer": "4/5", "explain": "sin²α+cos²α=1，cosα=√(1-9/25)=4/5。", "level": 2, "video": "https://www.bilibili.com/video/BV1GJ411x7h7"},
    {"text": "等比数列a1=2，q=3，求a4", "answer": "54", "explain": "a4 = a1·q³ = 2×27=54。", "level": 2, "video": "https://www.bilibili.com/video/BV1Xx411r7tP"},
    {"text": "求数据1,2,3,4,5的方差", "answer": "2", "explain": "平均数3，方差=[(1-3)²+...+(5-3)²]/5= (4+1+0+1+4)/5=2。", "level": 2, "video": "https://www.bilibili.com/video/BV1XW411A7fT"},
    {"text": "棱长为2的正方体体积", "answer": "8", "explain": "V=2³=8。", "level": 2, "video": "https://www.bilibili.com/video/BV1Eb411u7F8"},
    {"text": "指数运算：2³ × 2⁴ = ?", "answer": "128", "explain": "同底数幂相乘，指数相加：2⁷=128。", "level": 2, "video": "https://www.bilibili.com/video/BV1Ex411L7dW"},
    {"text": "三角形ABC中，a=3,b=4,∠C=60°，求c", "answer": "√13", "explain": "余弦定理：c² = a²+b²-2ab cosC = 9+16-2×3×4×0.5 = 13，c=√13。", "level": 3, "video": "https://www.bilibili.com/video/BV1PJ411W7bL"},
    {"text": "求函数y=2x²-4x+3的顶点坐标", "answer": "(1,1)", "explain": "x=-b/(2a)=4/4=1，代入y=2-4+3=1。", "level": 3, "video": "https://www.bilibili.com/video/BV1eJ411Q7G5"},
    {"text": "等差数列前n项和公式推导思路", "answer": "倒序相加", "explain": "S_n = (a1+an)·n/2，利用倒序相加法。", "level": 3, "video": "https://www.bilibili.com/video/BV1Xx411r7tP"},
]

ENGLISH_WORDS = [
    ("the", "这/那"), ("and", "和"), ("to", "到/向"), ("of", "...的"),
    ("a", "一个"), ("in", "在...里"), ("for", "为了"), ("is", "是"),
    ("on", "在...上"), ("that", "那个"), ("with", "和...一起"), ("by", "通过"),
    ("be", "是"), ("at", "在"), ("as", "作为"), ("from", "从"),
    ("it", "它"), ("have", "有"), ("not", "不"), ("this", "这个"),
    ("or", "或者"), ("but", "但是"), ("they", "他们"), ("we", "我们"),
    ("you", "你"), ("I", "我"), ("he", "他"), ("she", "她"),
    ("do", "做"), ("can", "能"), ("will", "将要"), ("would", "会"),
]

def build_english_questions(words_list):
    questions = []
    for idx, (word, meaning) in enumerate(words_list):
        level = 1 if idx < 10 else (2 if idx < 20 else 3)
        questions.append({
            "text": f"单词 '{word}' 的中文意思是？",
            "answer": meaning,
            "explain": f"'{word}' 的常用含义是 {meaning}，注意语境。",
            "level": level,
            "video": f"https://www.bilibili.com/video/BV1Tt411H7aY?p={idx%10+1}"
        })
    return questions

PHYSICS_QUESTIONS = [
    {"text": "打点计时器使用什么电源？频率多少？", "answer": "交流电 50Hz", "explain": "打点计时器使用交流电，周期0.02s，频率50Hz。", "level": 1, "video": "https://www.bilibili.com/video/BV1bW41137kL"},
    {"text": "胡克定律公式及物理意义", "answer": "F=kx", "explain": "弹簧弹力与形变量成正比，k为劲度系数。", "level": 1, "video": "https://www.bilibili.com/video/BV1bx411T7Pc"},
    {"text": "验证平行四边形定则时，两次拉橡皮筋要求什么相同？", "answer": "结点O位置相同", "explain": "为了保证合力与分力的作用效果相同。", "level": 1, "video": "https://www.bilibili.com/video/BV1jx411K7Tk"},
    {"text": "牛顿第二定律表达式", "answer": "F=ma", "explain": "物体加速度与合外力成正比，与质量成反比。", "level": 1, "video": "https://www.bilibili.com/video/BV1Qs411c7XB"},
    {"text": "平抛运动水平方向做什么运动？", "answer": "匀速直线运动", "explain": "水平方向不受力，速度不变。", "level": 1, "video": "https://www.bilibili.com/video/BV1ss411c7Wm"},
    {"text": "验证机械能守恒时，为什么重锤下落势能减少略大于动能增加？", "answer": "空气阻力/摩擦", "explain": "有阻力消耗一部分机械能。", "level": 2, "video": "https://www.bilibili.com/video/BV1Ex411Y7yP"},
    {"text": "测定电源电动势和内阻实验中，U-I图像纵轴截距表示什么？", "answer": "电动势E", "explain": "当I=0时U=E。", "level": 2, "video": "https://www.bilibili.com/video/BV1k4411d7pS"},
    {"text": "如何通过打点计时器求加速度？写出表达式", "answer": "a=(x4+x5+x6-x1-x2-x3)/(3T)^2", "explain": "利用逐差法减小误差。", "level": 3, "video": "https://www.bilibili.com/video/BV1bW41137kL"},
    {"text": "某弹簧原长10cm，挂200g钩码后长12cm，求劲度系数(g=10N/kg)", "answer": "100N/m", "explain": "F=mg=2N，Δx=0.02m，k=F/Δx=100N/m。", "level": 3, "video": "https://www.bilibili.com/video/BV1bx411T7Pc"},
]

ALL_QUESTIONS = {
    "math": MATH_QUESTIONS,
    "english": build_english_questions(ENGLISH_WORDS),
    "physics": PHYSICS_QUESTIONS,
}

# ==================== 错题本管理（完全保留原逻辑） ====================
MISTAKE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mistakes.json")
REWARD_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reward_data.json")

def load_mistakes():
    if os.path.exists(MISTAKE_FILE):
        with open(MISTAKE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"math": [], "english": [], "physics": []}

def save_mistakes(mistakes):
    with open(MISTAKE_FILE, "w", encoding="utf-8") as f:
        json.dump(mistakes, f, ensure_ascii=False, indent=2)

def add_mistake(subject, question, user_answer, correct_answer, explanation):
    mistakes = load_mistakes()
    mistakes[subject].append({
        "question": question,
        "user_answer": user_answer,
        "correct_answer": correct_answer,
        "explanation": explanation,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_mistakes(mistakes)


# ==================== 激励系统（保留原逻辑，弹窗改为QMessageBox） ====================
class RewardSystem:
    def __init__(self):
        self.parent_window = None
        self.load_data()
        self.reward_pool = [
            "💰 100元现金！可以向家长兑现",
            "🍔 请吃炸鸡一份",
            "🍲 请吃火锅一顿",
            "🧋 奶茶一杯（任意口味）",
            "🍕 披萨一份",
            "🎁 学生想吃的东西（和家长商量）",
            "📚 购买一本喜欢的课外书",
            "🎬 电影票一张"
        ]

    def set_parent(self, window):
        self.parent_window = window

    def load_data(self):
        if os.path.exists(REWARD_FILE):
            with open(REWARD_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.points = data.get("points", 0)
                self.stars = data.get("stars", 0)
                self.hearts = data.get("hearts", 0)
        else:
            self.points = 0
            self.stars = 0
            self.hearts = 0

    def save_data(self):
        with open(REWARD_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "points": self.points,
                "stars": self.stars,
                "hearts": self.hearts
            }, f, ensure_ascii=False, indent=2)

    def add_points(self, amount):
        self.points += amount
        self.save_data()

    def add_star(self, subject):
        """只在数学/物理正确时调用，加一颗星，满3颗自动变爱心并抽奖"""
        if subject not in ["math", "physics"]:
            return False
        self.stars += 1
        self.save_data()
        if self.stars >= 3:
            self.convert_stars_to_heart()
        return True

    def convert_stars_to_heart(self):
        exchange_count = self.stars // 3
        self.hearts += exchange_count
        self.stars -= exchange_count * 3
        self.save_data()
        for _ in range(exchange_count):
            self.show_reward_popup()

    def show_reward_popup(self):
        reward = random.choice(self.reward_pool)
        message = f"🎉 恭喜获得奖励！\n\n{reward}\n\n请找家长兑现吧！"
        if self.parent_window:
            QMessageBox.information(self.parent_window, "🎁 学习奖励", message)
        # 消耗一颗爱心
        if self.hearts > 0:
            self.hearts -= 1
            self.save_data()

    def add_english_reward(self):
        """英语正确奖励5积分"""
        self.add_points(5)


# ==================== 自适应训练引擎 ====================
class AdaptiveTrainer:
    def __init__(self, subject, questions):
        self.subject = subject
        self.questions = list(questions)
        self.level = 1
        self.correct_in_level = 0
        self.need_correct = 3
        self.mastered = set()
        self.all_questions_learned = False
        self.current_question = None
        self.pending_upgrade = False  # 标记下次next_question需要升级

    def get_current_questions(self):
        return [(i, q) for i, q in enumerate(self.questions)
                if q["level"] == self.level and i not in self.mastered]

    def next_question(self):
        """返回下一题，如果是升级/完成则返回特殊状态"""
        # 检查是否有待处理的升级
        if self.pending_upgrade:
            self.pending_upgrade = False
            if self.level < 3:
                self.level += 1
                self.correct_in_level = 0
                return ("upgrade", self.level)
            else:
                self.all_questions_learned = True
                return ("complete", None)

        available = self.get_current_questions()
        if not available:
            if self.level < 3:
                self.level += 1
                self.correct_in_level = 0
                return ("upgrade", self.level)
            else:
                self.all_questions_learned = True
                return ("complete", None)
        idx, q = random.choice(available)
        self.current_question = (idx, q)
        return ("question", q)

    def check_answer(self, user_ans):
        """检查答案，返回 (correct, message)"""
        if self.current_question is None:
            return (False, "没有当前题目")
        idx, q = self.current_question
        # 双向匹配：正确答案在用户答案中，或用户答案在正确答案中
        ans_lower = q["answer"].lower()
        user_lower = user_ans.lower()
        correct = (ans_lower in user_lower) or (user_lower in ans_lower) or (user_lower == ans_lower)
        if correct:
            self.correct_in_level += 1
            self.mastered.add(idx)
            # 检查是否需要升级：连续正确≥need_correct 且 当前难度已无剩余题目
            remaining = self.get_current_questions()
            if self.correct_in_level >= self.need_correct and not remaining and self.level < 3:
                self.pending_upgrade = True
            return (True, q)
        else:
            self.correct_in_level = 0
            return (False, q)

    def is_complete(self):
        return self.all_questions_learned


# ==================== 颜色主题 ====================
class Theme:
    PRIMARY = "#2196F3"
    SECONDARY = "#FF9800"
    SUCCESS = "#4CAF50"
    ERROR = "#F44336"
    BG_DARK = "#1a1a2e"
    BG_CARD = "#16213e"
    BG_LIGHT = "#0f3460"
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#b0b0b0"
    ACCENT = "#e94560"


# ==================== 自定义图标按钮 ====================
class NavButton(QPushButton):
    def __init__(self, text, emoji="", parent=None):
        super().__init__(parent)
        full_text = f"{emoji}  {text}" if emoji else text
        self.setText(full_text)
        self.setFont(QFont("Microsoft YaHei UI", 11))
        self.setMinimumHeight(48)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_CARD};
                color: {Theme.TEXT_PRIMARY};
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_LIGHT};
                border-left: 3px solid {Theme.PRIMARY};
            }}
            QPushButton:pressed {{
                background-color: {Theme.ACCENT};
            }}
        """)


# ==================== 主窗口 ====================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.reward = RewardSystem()
        self.trainer = None
        self.trainer_subject = None
        self.exam_questions = []
        self.exam_index = 0
        self.exam_score = 0
        self.exam_mistakes = []

        self.init_ui()
        self.reward.set_parent(self)

    def init_ui(self):
        self.setWindowTitle("自适应军考集训系统 v1.0 (激励版)")
        self.setMinimumSize(1000, 680)
        self.center_window()

        # 整体布局
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ---- 左侧导航 ----
        nav_panel = QWidget()
        nav_panel.setFixedWidth(200)
        nav_panel.setStyleSheet(f"background-color: {Theme.BG_DARK};")
        nav_layout = QVBoxLayout(nav_panel)
        nav_layout.setContentsMargins(10, 20, 10, 20)
        nav_layout.setSpacing(8)

        # 标题
        title_label = QLabel("🏆 学习系统")
        title_label.setFont(QFont("Microsoft YaHei UI", 16, QFont.Bold))
        title_label.setStyleSheet(f"color: {Theme.ACCENT}; padding: 10px 0 20px 0;")
        title_label.setAlignment(Qt.AlignCenter)
        nav_layout.addWidget(title_label)

        # 导航按钮
        self.btn_home = NavButton("首页", "🏠")
        self.btn_train = NavButton("自适应训练", "🎯")
        self.btn_study = NavButton("学习模式", "📚")
        self.btn_exam = NavButton("考试模式", "📝")
        self.btn_mistake = NavButton("错题本", "📖")
        self.btn_quit = NavButton("退出系统", "🚪")

        nav_layout.addWidget(self.btn_home)
        nav_layout.addWidget(self.btn_train)
        nav_layout.addWidget(self.btn_study)
        nav_layout.addWidget(self.btn_exam)
        nav_layout.addWidget(self.btn_mistake)
        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_quit)

        # 底部状态简表
        self.nav_status = QLabel("积分 0 | ⭐0 | ❤️0")
        self.nav_status.setFont(QFont("Microsoft YaHei UI", 9))
        self.nav_status.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; padding: 10px 0;")
        self.nav_status.setAlignment(Qt.AlignCenter)
        nav_layout.addWidget(self.nav_status)

        # ---- 右侧内容区 ----
        content_area = QWidget()
        content_area.setStyleSheet(f"background-color: {Theme.BG_DARK};")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # 顶部状态栏
        self.status_bar = QFrame()
        self.status_bar.setFixedHeight(50)
        self.status_bar.setStyleSheet(f"background-color: {Theme.BG_CARD};")
        bar_layout = QHBoxLayout(self.status_bar)
        bar_layout.setContentsMargins(20, 0, 20, 0)

        self.lbl_title = QLabel("🏠 首页")
        self.lbl_title.setFont(QFont("Microsoft YaHei UI", 14, QFont.Bold))
        self.lbl_title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")

        self.lbl_status = QLabel("")
        self.lbl_status.setFont(QFont("Microsoft YaHei UI", 11))
        self.lbl_status.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")

        bar_layout.addWidget(self.lbl_title)
        bar_layout.addStretch()
        bar_layout.addWidget(self.lbl_status)

        content_layout.addWidget(self.status_bar)

        # 中部 Stacked Widget
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack, 1)

        # 创建各页面
        self.page_home = self.create_home_page()
        self.page_train_subject = self.create_train_subject_page()
        self.page_training = self.create_training_page()
        self.page_study = self.create_study_page()
        self.page_exam = self.create_exam_page()
        self.page_mistake = self.create_mistake_page()
        self.stack.addWidget(self.page_home)         # 0
        self.stack.addWidget(self.page_train_subject) # 1
        self.stack.addWidget(self.page_training)      # 2
        self.stack.addWidget(self.page_study)         # 3
        self.stack.addWidget(self.page_exam)          # 4
        self.stack.addWidget(self.page_mistake)       # 5

        main_layout.addWidget(nav_panel)
        main_layout.addWidget(content_area, 1)

        # ---- 连接信号 ----
        self.btn_home.clicked.connect(lambda: self.switch_page(0, "🏠 首页"))
        self.btn_train.clicked.connect(lambda: self.switch_page(1, "🎯 自适应训练"))
        self.btn_study.clicked.connect(lambda: self.switch_page(3, "📚 学习模式"))
        self.btn_exam.clicked.connect(lambda: self.start_exam())
        self.btn_mistake.clicked.connect(lambda: self.show_mistake_page())
        self.btn_quit.clicked.connect(self.close)

        # 显示首页
        self.switch_page(0, "🏠 首页")
        self.refresh_status()
        # 定时刷新状态
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.refresh_status)
        self.status_timer.start(2000)

    def center_window(self):
        screen = QDesktopWidget().availableGeometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )

    def switch_page(self, index, title_text):
        self.stack.setCurrentIndex(index)
        self.lbl_title.setText(title_text)
        self.refresh_status()

    def refresh_status(self):
        status = f"积分 {self.reward.points}  |  ⭐ {self.reward.stars}  |  ❤️ {self.reward.hearts}"
        self.lbl_status.setText(status)
        self.nav_status.setText(status)

    # ==================== 页面构建 ====================

    def make_card(self, title, content_widget):
        """包装一个卡片式布局"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_CARD};
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        layout = QVBoxLayout(card)
        if title:
            lbl = QLabel(title)
            lbl.setFont(QFont("Microsoft YaHei UI", 13, QFont.Bold))
            lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; padding-bottom: 10px;")
            layout.addWidget(lbl)
        layout.addWidget(content_widget, 1)
        return card

    # -------- 首页 --------
    def create_home_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)

        # Welcome
        welcome = QLabel("🔥 自适应军考集训系统 v1.0")
        welcome.setFont(QFont("Microsoft YaHei UI", 24, QFont.Bold))
        welcome.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        welcome.setAlignment(Qt.AlignCenter)
        layout.addWidget(welcome)

        subtitle = QLabel("做对数学/物理题得⭐ · 3⭐换1❤抽奖 · 英语题得积分 · 错题本分析")
        subtitle.setFont(QFont("Microsoft YaHei UI", 12))
        subtitle.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; margin-bottom: 20px;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        # 激励系统展示
        reward_card = QFrame()
        reward_card.setStyleSheet(f"background-color: {Theme.BG_CARD}; border-radius: 12px; padding: 15px;")
        reward_layout = QVBoxLayout(reward_card)
        r_title = QLabel("📊 当前激励状态")
        r_title.setFont(QFont("Microsoft YaHei UI", 14, QFont.Bold))
        r_title.setStyleSheet(f"color: {Theme.ACCENT};")
        reward_layout.addWidget(r_title)

        self.home_status = QLabel()
        self.home_status.setFont(QFont("Microsoft YaHei UI", 16))
        self.home_status.setAlignment(Qt.AlignCenter)
        reward_layout.addWidget(self.home_status)

        # 更新home_status的定时器
        self.home_timer = QTimer()
        self.home_timer.timeout.connect(self.update_home_status)
        self.home_timer.start(1000)

        layout.addWidget(reward_card)

        # 快捷按钮
        quick_layout = QHBoxLayout()
        quick_btns = [
            ("🎯 开始训练", 1),
            ("📚 学习资料", 3),
            ("📝 模拟考试", 4),
            ("📖 错题本", 5),
        ]
        for text, idx in quick_btns:
            btn = QPushButton(text)
            btn.setFont(QFont("Microsoft YaHei UI", 12))
            btn.setMinimumHeight(60)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.BG_LIGHT};
                    color: {Theme.TEXT_PRIMARY};
                    border: none;
                    border-radius: 10px;
                    padding: 15px;
                }}
                QPushButton:hover {{
                    background-color: {Theme.ACCENT};
                }}
            """)
            if text == "📝 模拟考试":
                btn.clicked.connect(lambda checked: self.start_exam())
            elif text == "📖 错题本":
                btn.clicked.connect(lambda checked: self.show_mistake_page())
            else:
                btn.clicked.connect(lambda checked, i=idx: self.switch_page(i, self.get_title_for_index(i)))
            quick_layout.addWidget(btn)

        layout.addLayout(quick_layout)
        layout.addStretch()
        return page

    def get_title_for_index(self, idx):
        titles = {0: "🏠 首页", 1: "🎯 自适应训练", 3: "📚 学习模式", 4: "📝 考试模式", 5: "📖 错题本"}
        return titles.get(idx, "首页")

    def update_home_status(self):
        self.home_status.setText(
            f"积分 {self.reward.points} 分      ⭐ {self.reward.stars} 颗星      ❤️ {self.reward.hearts} 颗爱心"
        )

    # -------- 训练-选择学科 --------
    def create_train_subject_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)

        lbl = QLabel("选择学科开始自适应训练")
        lbl.setFont(QFont("Microsoft YaHei UI", 18, QFont.Bold))
        lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)

        desc = QLabel("连续答对3题提升难度等级，学完所有题目获得🏆")
        desc.setFont(QFont("Microsoft YaHei UI", 11))
        desc.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; margin-bottom: 20px;")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(15)

        subjects = [
            ("📐  数学", "math", Theme.PRIMARY),
            ("📖  英语", "english", Theme.SUCCESS),
            ("⚛️  物理", "physics", Theme.SECONDARY),
        ]
        for text, key, color in subjects:
            btn = QPushButton(text)
            btn.setFont(QFont("Microsoft YaHei UI", 16, QFont.Bold))
            btn.setMinimumHeight(80)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    border-radius: 12px;
                    padding: 15px;
                }}
                QPushButton:hover {{
                    background-color: {Theme.ACCENT};
                }}
            """)
            btn.clicked.connect(lambda checked, s=key: self.start_training(s))
            btn_layout.addWidget(btn)

        btn_back = QPushButton("返回首页")
        btn_back.setFont(QFont("Microsoft YaHei UI", 11))
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.TEXT_SECONDARY};
                border: 1px solid {Theme.TEXT_SECONDARY};
                border-radius: 8px;
                padding: 10px;
            }}
            QPushButton:hover {{
                color: {Theme.TEXT_PRIMARY};
                border-color: {Theme.TEXT_PRIMARY};
            }}
        """)
        btn_back.clicked.connect(lambda: self.switch_page(0, "🏠 首页"))

        btn_layout.addWidget(btn_back)
        layout.addLayout(btn_layout)
        layout.addStretch()
        return page

    def start_training(self, subject):
        self.trainer_subject = subject
        self.trainer = AdaptiveTrainer(subject, ALL_QUESTIONS[subject])
        self.switch_page(2, f"🎯 {subject.upper()} 训练")
        self.show_next_training_question()

    # -------- 训练答题 --------
    def create_training_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 30, 40, 30)

        # 顶部信息
        info_layout = QHBoxLayout()
        self.train_level_label = QLabel("难度: ⭐")
        self.train_level_label.setFont(QFont("Microsoft YaHei UI", 12, QFont.Bold))
        self.train_level_label.setStyleSheet(f"color: {Theme.SECONDARY};")
        self.train_progress_label = QLabel("连续正确: 0/3")
        self.train_progress_label.setFont(QFont("Microsoft YaHei UI", 12))
        self.train_progress_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")

        info_layout.addWidget(self.train_level_label)
        info_layout.addStretch()
        info_layout.addWidget(self.train_progress_label)
        layout.addLayout(info_layout)

        # 题目卡片
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_CARD};
                border-radius: 12px;
                padding: 25px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        self.train_question = QLabel("题目加载中...")
        self.train_question.setFont(QFont("Microsoft YaHei UI", 14))
        self.train_question.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        self.train_question.setWordWrap(True)
        card_layout.addWidget(self.train_question)

        # 答题区
        self.train_input = QLineEdit()
        self.train_input.setFont(QFont("Microsoft YaHei UI", 13))
        self.train_input.setPlaceholderText("在此输入你的答案...")
        self.train_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Theme.BG_LIGHT};
                color: {Theme.TEXT_PRIMARY};
                border: 2px solid {Theme.BG_LIGHT};
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {Theme.PRIMARY};
            }}
        """)
        self.train_input.returnPressed.connect(self.submit_training_answer)
        card_layout.addWidget(self.train_input)

        # 按钮
        btn_layout = QHBoxLayout()
        self.train_submit_btn = QPushButton("提交答案 (Enter)")
        self.train_submit_btn.setFont(QFont("Microsoft YaHei UI", 12, QFont.Bold))
        self.train_submit_btn.setMinimumHeight(45)
        self.train_submit_btn.setCursor(Qt.PointingHandCursor)
        self.train_submit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 25px;
            }}
            QPushButton:hover {{
                background-color: #1976D2;
            }}
        """)
        self.train_submit_btn.clicked.connect(self.submit_training_answer)

        self.train_continue_btn = QPushButton("下一题 →")
        self.train_continue_btn.setFont(QFont("Microsoft YaHei UI", 12))
        self.train_continue_btn.setMinimumHeight(45)
        self.train_continue_btn.setCursor(Qt.PointingHandCursor)
        self.train_continue_btn.setVisible(False)
        self.train_continue_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.SUCCESS};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 25px;
            }}
            QPushButton:hover {{
                background-color: #388E3C;
            }}
        """)
        self.train_continue_btn.clicked.connect(self.on_training_continue)

        self.train_back_btn = QPushButton("结束训练")
        self.train_back_btn.setFont(QFont("Microsoft YaHei UI", 11))
        self.train_back_btn.setCursor(Qt.PointingHandCursor)
        self.train_back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.TEXT_SECONDARY};
                border: 1px solid {Theme.TEXT_SECONDARY};
                border-radius: 8px;
                padding: 10px;
            }}
            QPushButton:hover {{
                color: {Theme.ERROR};
                border-color: {Theme.ERROR};
            }}
        """)
        self.train_back_btn.clicked.connect(lambda: self.switch_page(1, "🎯 自适应训练"))

        btn_layout.addWidget(self.train_submit_btn)
        btn_layout.addWidget(self.train_continue_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.train_back_btn)
        card_layout.addLayout(btn_layout)

        # 反馈区
        self.train_feedback = QTextEdit()
        self.train_feedback.setReadOnly(True)
        self.train_feedback.setFont(QFont("Microsoft YaHei UI", 11))
        self.train_feedback.setMinimumHeight(120)
        self.train_feedback.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Theme.BG_LIGHT};
                color: {Theme.TEXT_PRIMARY};
                border: none;
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        card_layout.addWidget(self.train_feedback)

        layout.addWidget(card, 1)
        return page

    def show_next_training_question(self):
        """加载下一题。用循环处理连续升级，避免递归栈溢出"""
        if self.trainer is None:
            return
        while True:
            result = self.trainer.next_question()
            result_type = result[0]
            if result_type == "question":
                q = result[1]
                self.train_question.setText(f"第 {len(self.trainer.mastered)+1} 题：{q['text']}")
                self.train_level_label.setText(f"难度: {'⭐' * self.trainer.level}")
                self.train_progress_label.setText(f"连续正确: {self.trainer.correct_in_level}/3")
                self.train_input.clear()
                self.train_input.setEnabled(True)
                self.train_submit_btn.setVisible(True)
                self.train_continue_btn.setVisible(False)
                self.train_feedback.clear()
                self.train_input.setFocus()
                break
            elif result_type == "upgrade":
                level = result[1]
                self.train_feedback.setText(f"🎉 恭喜升级到难度 {level} 星！获得 100 学习积分！")
                self.reward.add_points(100)
                self.refresh_status()
                QMessageBox.information(self, "🎉 升级成功", f"恭喜升级到难度 {level} 星！\n获得 100 学习积分！")
                # 继续循环加载下一题（或再次升级）
                continue
            elif result_type == "complete":
                self.train_feedback.setText("🏆 太棒了！你已经掌握了本学科所有题目！")
                self.train_input.setEnabled(False)
                self.train_submit_btn.setVisible(False)
                self.train_continue_btn.setVisible(False)
                QMessageBox.information(self, "🏆 恭喜", "太棒了！你已经掌握了本学科所有题目！")
                break

    def submit_training_answer(self):
        if self.trainer is None or self.trainer.current_question is None:
            return
        try:
            user_ans = self.train_input.text().strip()
            if not user_ans:
                self.train_feedback.setText("⚠️ 请输入答案后再提交")
                return

            idx, q = self.trainer.current_question
            correct, payload = self.trainer.check_answer(user_ans)

            if correct:
                # 激励
                if self.trainer_subject in ["math", "physics"]:
                    self.reward.add_star(self.trainer_subject)
                elif self.trainer_subject == "english":
                    self.reward.add_english_reward()

                video_link = payload.get('video', '')
                video_text = f"\n🎥 推荐视频：{video_link}" if video_link else ""
                self.train_feedback.setText(f"✅ 正确！\n讲解：{payload['explain']}{video_text}")
            else:
                video_link = q.get('video', '')
                video_text = f"\n🎥 推荐视频：{video_link}" if video_link else ""
                self.train_feedback.setText(
                    f"❌ 错误。\n正确答案：{q['answer']}\n讲解：{q['explain']}{video_text}"
                )
                add_mistake(self.trainer_subject, q["text"], user_ans, q["answer"], q["explain"])

            self.refresh_status()
            self.train_input.setEnabled(False)
            self.train_submit_btn.setVisible(False)
            self.train_continue_btn.setVisible(True)

            # 更新进度
            self.train_progress_label.setText(f"连续正确: {self.trainer.correct_in_level}/3")
        except Exception as e:
            self.train_feedback.setText(f"⚠️ 提交答案时出错：{str(e)}")

    def on_training_continue(self):
        if self.trainer and self.trainer.is_complete():
            return
        self.show_next_training_question()

    # -------- 学习模式 --------
    def create_study_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)

        lbl = QLabel("📚 学习模式 - 浏览全部资料")
        lbl.setFont(QFont("Microsoft YaHei UI", 16, QFont.Bold))
        lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        layout.addWidget(lbl)

        # 学科切换
        tab_layout = QHBoxLayout()
        self.study_btns = {}
        for text, key, color in [("📐 数学", "math", Theme.PRIMARY), ("📖 英语", "english", Theme.SUCCESS), ("⚛️ 物理", "physics", Theme.SECONDARY)]:
            btn = QPushButton(text)
            btn.setFont(QFont("Microsoft YaHei UI", 11))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 20px;
                }}
                QPushButton:hover {{
                    background-color: {Theme.ACCENT};
                }}
            """)
            btn.clicked.connect(lambda checked, k=key: self.show_study_content(k))
            tab_layout.addWidget(btn)
            self.study_btns[key] = btn
        layout.addLayout(tab_layout)

        # 内容区
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"background-color: transparent; border: none;")

        self.study_content = QWidget()
        self.study_content.setStyleSheet("background-color: transparent;")
        self.study_content_layout = QVBoxLayout(self.study_content)

        scroll.setWidget(self.study_content)
        layout.addWidget(scroll, 1)

        btn_back = QPushButton("返回首页")
        btn_back.setFont(QFont("Microsoft YaHei UI", 11))
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.TEXT_SECONDARY};
                border: 1px solid {Theme.TEXT_SECONDARY};
                border-radius: 8px;
                padding: 8px;
            }}
            QPushButton:hover {{
                color: {Theme.TEXT_PRIMARY};
                border-color: {Theme.TEXT_PRIMARY};
            }}
        """)
        btn_back.clicked.connect(lambda: self.switch_page(0, "🏠 首页"))
        layout.addWidget(btn_back)

        return page

    def show_study_content(self, subject):
        # 清除旧内容
        while self.study_content_layout.count():
            item = self.study_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        questions = ALL_QUESTIONS.get(subject, [])
        if not questions:
            lbl = QLabel("暂无题目数据")
            lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
            self.study_content_layout.addWidget(lbl)
            return

        for q in questions:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {Theme.BG_CARD};
                    border-radius: 8px;
                    padding: 12px;
                    margin: 4px 0;
                }}
            """)
            c_layout = QVBoxLayout(card)
            text = f"[难度{'⭐'*q['level']}] {q['text']}"
            q_lbl = QLabel(text)
            q_lbl.setFont(QFont("Microsoft YaHei UI", 11, QFont.Bold))
            q_lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
            q_lbl.setWordWrap(True)
            c_layout.addWidget(q_lbl)

            a_lbl = QLabel(f"答案：{q['answer']}")
            a_lbl.setStyleSheet(f"color: {Theme.SUCCESS};")
            c_layout.addWidget(a_lbl)

            e_lbl = QLabel(f"讲解：{q['explain']}")
            e_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
            e_lbl.setWordWrap(True)
            c_layout.addWidget(e_lbl)

            v_lbl = QLabel(f'🎥 <a href="{q.get("video", "#")}" style="color: {Theme.PRIMARY};">点击观看视频讲解</a>')
            v_lbl.setOpenExternalLinks(True)
            v_lbl.setStyleSheet(f"color: {Theme.PRIMARY};")
            c_layout.addWidget(v_lbl)

            self.study_content_layout.addWidget(card)

        self.study_content_layout.addStretch()

    # -------- 考试模式 --------
    def create_exam_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 30, 40, 30)

        # 考试信息
        self.exam_info = QLabel("📝 模拟考试")
        self.exam_info.setFont(QFont("Microsoft YaHei UI", 16, QFont.Bold))
        self.exam_info.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        layout.addWidget(self.exam_info)

        self.exam_progress = QLabel("准备开始...")
        self.exam_progress.setFont(QFont("Microsoft YaHei UI", 12))
        self.exam_progress.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        layout.addWidget(self.exam_progress)

        # 题目卡片
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_CARD};
                border-radius: 12px;
                padding: 25px;
            }}
        """)
        card_layout = QVBoxLayout(card)

        self.exam_question_label = QLabel("点击下方「开始考试」")
        self.exam_question_label.setFont(QFont("Microsoft YaHei UI", 14))
        self.exam_question_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        self.exam_question_label.setWordWrap(True)
        card_layout.addWidget(self.exam_question_label)

        self.exam_input = QLineEdit()
        self.exam_input.setFont(QFont("Microsoft YaHei UI", 13))
        self.exam_input.setPlaceholderText("输入答案...")
        self.exam_input.setEnabled(False)
        self.exam_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Theme.BG_LIGHT};
                color: {Theme.TEXT_PRIMARY};
                border: 2px solid {Theme.BG_LIGHT};
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {Theme.PRIMARY};
            }}
        """)
        self.exam_input.returnPressed.connect(self.submit_exam_answer)
        card_layout.addWidget(self.exam_input)

        btn_layout = QHBoxLayout()
        self.exam_start_btn = QPushButton("🚀 开始考试")
        self.exam_start_btn.setFont(QFont("Microsoft YaHei UI", 12, QFont.Bold))
        self.exam_start_btn.setMinimumHeight(45)
        self.exam_start_btn.setCursor(Qt.PointingHandCursor)
        self.exam_start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.SECONDARY};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 25px;
            }}
            QPushButton:hover {{
                background-color: #F57C00;
            }}
        """)
        self.exam_start_btn.clicked.connect(self.begin_exam)

        self.exam_submit_btn = QPushButton("提交答案 (Enter)")
        self.exam_submit_btn.setFont(QFont("Microsoft YaHei UI", 12, QFont.Bold))
        self.exam_submit_btn.setMinimumHeight(45)
        self.exam_submit_btn.setCursor(Qt.PointingHandCursor)
        self.exam_submit_btn.setVisible(False)
        self.exam_submit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 25px;
            }}
            QPushButton:hover {{
                background-color: #1976D2;
            }}
        """)
        self.exam_submit_btn.clicked.connect(self.submit_exam_answer)

        self.exam_next_btn = QPushButton("下一题 →")
        self.exam_next_btn.setFont(QFont("Microsoft YaHei UI", 12))
        self.exam_next_btn.setMinimumHeight(45)
        self.exam_next_btn.setCursor(Qt.PointingHandCursor)
        self.exam_next_btn.setVisible(False)
        self.exam_next_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.SUCCESS};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 25px;
            }}
            QPushButton:hover {{
                background-color: #388E3C;
            }}
        """)
        self.exam_next_btn.clicked.connect(self.next_exam_question)

        btn_layout.addWidget(self.exam_start_btn)
        btn_layout.addWidget(self.exam_submit_btn)
        btn_layout.addWidget(self.exam_next_btn)
        btn_layout.addStretch()
        card_layout.addLayout(btn_layout)

        self.exam_feedback = QTextEdit()
        self.exam_feedback.setReadOnly(True)
        self.exam_feedback.setFont(QFont("Microsoft YaHei UI", 11))
        self.exam_feedback.setMinimumHeight(100)
        self.exam_feedback.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Theme.BG_LIGHT};
                color: {Theme.TEXT_PRIMARY};
                border: none;
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        card_layout.addWidget(self.exam_feedback)

        layout.addWidget(card, 1)

        # 底部按钮
        btn_back = QPushButton("返回首页")
        btn_back.setFont(QFont("Microsoft YaHei UI", 11))
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.TEXT_SECONDARY};
                border: 1px solid {Theme.TEXT_SECONDARY};
                border-radius: 8px;
                padding: 8px;
            }}
            QPushButton:hover {{
                color: {Theme.TEXT_PRIMARY};
                border-color: {Theme.TEXT_PRIMARY};
            }}
        """)
        btn_back.clicked.connect(lambda: self.switch_page(0, "🏠 首页"))
        layout.addWidget(btn_back)

        return page

    def start_exam(self):
        self.exam_index = 0
        self.exam_score = 0
        self.exam_mistakes = []
        self.exam_questions = []
        for sub in ["math", "english", "physics"]:
            sub_q = random.sample(ALL_QUESTIONS[sub], min(3, len(ALL_QUESTIONS[sub])))
            self.exam_questions.extend([(sub, q) for q in sub_q])
        self.switch_page(4, "📝 考试模式")

    def begin_exam(self):
        if not self.exam_questions:
            self.start_exam()
        self.exam_index = 0
        self.exam_score = 0
        self.exam_mistakes = []
        self.exam_start_btn.setVisible(False)
        self.exam_submit_btn.setVisible(True)
        self.exam_input.setEnabled(True)
        self.exam_feedback.clear()
        self.show_exam_question()

    def show_exam_question(self):
        if self.exam_index >= len(self.exam_questions):
            self.finish_exam()
            return
        sub, q = self.exam_questions[self.exam_index]
        self.exam_info.setText(f"📝 模拟考试 - 第 {self.exam_index+1}/{len(self.exam_questions)} 题")
        self.exam_progress.setText(f"当前得分: {self.exam_score} 分")
        self.exam_question_label.setText(f"【{sub.upper()}】{q['text']}")
        self.exam_input.clear()
        self.exam_input.setEnabled(True)
        self.exam_submit_btn.setVisible(True)
        self.exam_next_btn.setVisible(False)
        self.exam_input.setFocus()

    def submit_exam_answer(self):
        if self.exam_index >= len(self.exam_questions):
            return
        try:
            user_ans = self.exam_input.text().strip()
            if not user_ans:
                self.exam_feedback.setText("⚠️ 请输入答案")
                return

            sub, q = self.exam_questions[self.exam_index]
            ans_lower = q["answer"].lower()
            user_lower = user_ans.lower()
            correct = (ans_lower in user_lower) or (user_lower in ans_lower) or (user_lower == ans_lower)

            if correct:
                self.exam_score += 10
                if sub in ["math", "physics"]:
                    self.reward.add_star(sub)
                elif sub == "english":
                    self.reward.add_english_reward()
                self.exam_feedback.setText(f"✅ 正确 +10分！\n讲解：{q['explain']}")
            else:
                self.exam_feedback.setText(f"❌ 错误。正确答案：{q['answer']}\n讲解：{q['explain']}")
                self.exam_mistakes.append((sub, q, user_ans))
                add_mistake(sub, q["text"], user_ans, q["answer"], q["explain"])

            self.refresh_status()
            self.exam_input.setEnabled(False)
            self.exam_submit_btn.setVisible(False)
            self.exam_next_btn.setVisible(True)
        except Exception as e:
            self.exam_feedback.setText(f"⚠️ 提交答案时出错：{str(e)}")

    def next_exam_question(self):
        self.exam_index += 1
        if self.exam_index >= len(self.exam_questions):
            self.finish_exam()
        else:
            self.show_exam_question()

    def finish_exam(self):
        self.exam_info.setText("📝 考试结束")
        total = len(self.exam_questions) * 10
        self.exam_question_label.setText(f"得分：{self.exam_score}/{total} 分")
        self.exam_input.setEnabled(False)
        self.exam_submit_btn.setVisible(False)
        self.exam_next_btn.setVisible(False)
        self.exam_start_btn.setVisible(True)
        self.exam_start_btn.setText("🔄 重新考试")

        result = f"📊 考试完成！\n得分：{self.exam_score}/{total}\n"
        if self.exam_mistakes:
            result += f"\n错题数：{len(self.exam_mistakes)} 道\n"
            for sub, q, wrong in self.exam_mistakes[:3]:
                result += f"\n【{sub}】{q['text'][:30]}...\n  你的答案：{wrong}  正确答案：{q['answer']}"
        else:
            result += "\n🎉 全部答对，太棒了！"

        self.exam_feedback.setText(result)
        QMessageBox.information(self, "📊 考试结果", result)

    # -------- 错题本 --------
    def create_mistake_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)

        lbl = QLabel("📖 错题本分析")
        lbl.setFont(QFont("Microsoft YaHei UI", 16, QFont.Bold))
        lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        layout.addWidget(lbl)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: transparent; border: none;")
        self.mistake_content = QWidget()
        self.mistake_content.setStyleSheet("background-color: transparent;")
        self.mistake_content_layout = QVBoxLayout(self.mistake_content)
        scroll.setWidget(self.mistake_content)
        layout.addWidget(scroll, 1)

        btn_back = QPushButton("返回首页")
        btn_back.setFont(QFont("Microsoft YaHei UI", 11))
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.TEXT_SECONDARY};
                border: 1px solid {Theme.TEXT_SECONDARY};
                border-radius: 8px;
                padding: 8px;
            }}
            QPushButton:hover {{
                color: {Theme.TEXT_PRIMARY};
                border-color: {Theme.TEXT_PRIMARY};
            }}
        """)
        btn_back.clicked.connect(lambda: self.switch_page(0, "🏠 首页"))

        # 清空错题本按钮
        btn_clear = QPushButton("🗑️ 清空错题本")
        btn_clear.setFont(QFont("Microsoft YaHei UI", 11))
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.ERROR};
                border: 1px solid {Theme.ERROR};
                border-radius: 8px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: {Theme.ERROR};
                color: white;
            }}
        """)
        btn_clear.clicked.connect(self.clear_mistakes)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_back)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_clear)
        layout.addLayout(btn_layout)

        return page

    def show_mistake_page(self):
        self.switch_page(5, "📖 错题本")
        # 清空并重新加载
        while self.mistake_content_layout.count():
            item = self.mistake_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        mistakes = load_mistakes()
        total = sum(len(v) for v in mistakes.values())

        if total == 0:
            lbl = QLabel("✅ 暂无错题，继续保持！")
            lbl.setFont(QFont("Microsoft YaHei UI", 14))
            lbl.setStyleSheet(f"color: {Theme.SUCCESS}; padding: 30px;")
            lbl.setAlignment(Qt.AlignCenter)
            self.mistake_content_layout.addWidget(lbl)
            return

        # 统计
        stats = QLabel(f"📊 总错题数：{total}")
        stats.setFont(QFont("Microsoft YaHei UI", 13, QFont.Bold))
        stats.setStyleSheet(f"color: {Theme.ACCENT}; padding: 10px 0;")
        self.mistake_content_layout.addWidget(stats)

        sub_names = {"math": "数学", "english": "英语", "physics": "物理"}
        for sub, lst in mistakes.items():
            if not lst:
                continue
            sub_title = QLabel(f"【{sub_names.get(sub, sub)}】共 {len(lst)} 道错题")
            sub_title.setFont(QFont("Microsoft YaHei UI", 12, QFont.Bold))
            sub_title.setStyleSheet(f"color: {Theme.SECONDARY}; padding: 8px 0;")
            self.mistake_content_layout.addWidget(sub_title)

            # 显示最近错题
            for item in lst[-5:]:
                card = QFrame()
                card.setStyleSheet(f"""
                    QFrame {{
                        background-color: {Theme.BG_CARD};
                        border-radius: 8px;
                        padding: 10px;
                        margin: 3px 0;
                        border-left: 3px solid {Theme.ERROR};
                    }}
                """)
                c_layout = QVBoxLayout(card)
                q_lbl = QLabel(f"📌 {item['question'][:60]}")
                q_lbl.setWordWrap(True)
                q_lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
                c_layout.addWidget(q_lbl)
                ans_lbl = QLabel(f"你的答案：{item['user_answer'][:30]}  |  正确答案：{item['correct_answer'][:30]}")
                ans_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
                c_layout.addWidget(ans_lbl)
                time_lbl = QLabel(f"🕐 {item.get('timestamp', '')}")
                time_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 9px;")
                c_layout.addWidget(time_lbl)
                self.mistake_content_layout.addWidget(card)

        self.mistake_content_layout.addStretch()

    def clear_mistakes(self):
        reply = QMessageBox.question(self, "确认清空",
                                     "确定要清空所有错题吗？此操作不可恢复！",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            save_mistakes({"math": [], "english": [], "physics": []})
            self.show_mistake_page()
            QMessageBox.information(self, "已清空", "错题本已清空！")


# ==================== 启动 ====================
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 全局暗色主题调色板
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(Theme.BG_DARK))
    palette.setColor(QPalette.WindowText, QColor(Theme.TEXT_PRIMARY))
    palette.setColor(QPalette.Base, QColor(Theme.BG_CARD))
    palette.setColor(QPalette.Text, QColor(Theme.TEXT_PRIMARY))
    palette.setColor(QPalette.Button, QColor(Theme.BG_LIGHT))
    palette.setColor(QPalette.ButtonText, QColor(Theme.TEXT_PRIMARY))
    palette.setColor(QPalette.Highlight, QColor(Theme.PRIMARY))
    palette.setColor(QPalette.HighlightedText, QColor(Theme.TEXT_PRIMARY))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
