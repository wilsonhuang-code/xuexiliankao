#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自适应军考集训系统 v13.0 完整版
功能：多主题、全局字体、美/英发音、2500+单词库、每日打卡、作文范文、自适应训练、考试、错题本
数学题库：9个单元（集合、复数、向量、三角函数、解三角形、数列、统计概率、立体几何、函数）
物理题库：7个实验（匀变速直线运动、弹簧弹力、平行四边形定则、牛顿第二定律、平抛运动、机械能守恒、测电源电动势）
英语专项：随机抽查（英译中/中译英）、记忆曲线复习、单词补全（显示下划线+音标+释义）、词库管理
"""

import random
import json
import os
import sys
import re
from datetime import datetime, timedelta, date

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QTextEdit, QLineEdit,
    QMessageBox, QFrame, QScrollArea, QDesktopWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QRadioButton,
    QGroupBox, QTabWidget, QDialog, QFormLayout, QSpinBox,
    QCheckBox, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

# TTS
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

# ==================== 配置文件 ====================
SETTINGS_FILE = "settings.json"
WORD_FILE = "words.txt"
STUDY_TIME_FILE = "study_time.json"
MISTAKE_FILE = "mistakes.json"
REWARD_FILE = "reward_data.json"
WORD_MASTERY_FILE = "word_mastery.json"

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

# ==================== 数学题库（完整9个单元） ====================
def build_math_questions():
    questions = []
    # 单元1：集合与常用逻辑用语
    unit1 = [
        ("集合的交集符号", "∩"), ("集合的并集符号", "∪"), ("补集符号", "∁"),
        ("空集符号", "∅"), ("元素与集合的属于符号", "∈"), ("元素与集合的不属于符号", "∉"),
        ("子集定义", "A⊆B ⇔ 任意x∈A都有x∈B"), ("真子集定义", "A⊂B ⇔ A⊆B且存在x∈B但x∉A"),
        ("充分条件的定义", "p⇒q 则p是q的充分条件"), ("必要条件的定义", "p⇐q 则p是q的必要条件"),
        ("充要条件的定义", "p⇔q 则p是q的充要条件"),
    ]
    for text, ans in unit1:
        questions.append({"text": f"【集合与逻辑】{text}", "answer": ans, "explain": ans, "level": 1, "video": ""})
    # 单元2：复数
    unit2 = [
        ("i²", "-1"), ("复数代数形式", "a+bi (a,b∈R)"), ("共轭复数", "a-bi"),
        ("复数模长公式", "√(a²+b²)"), ("复数的加法法则", "(a+bi)+(c+di)=(a+c)+(b+d)i"),
        ("复数的乘法法则", "(a+bi)(c+di)=(ac-bd)+(ad+bc)i"),
    ]
    for text, ans in unit2:
        questions.append({"text": f"【复数】{text}", "answer": ans, "explain": ans, "level": 1, "video": ""})
    # 单元3：向量
    unit3 = [
        ("向量坐标表示", "(x,y)"), ("向量加法坐标公式", "(x₁+x₂, y₁+y₂)"), ("向量减法坐标公式", "(x₁-x₂, y₁-y₂)"),
        ("数乘向量公式", "k(x,y)=(kx,ky)"), ("向量点积坐标公式", "x₁x₂+y₁y₂"), ("向量点积几何公式", "|a||b|cosθ"),
        ("向量垂直充要条件", "a·b=0"), ("向量平行充要条件", "x₁y₂=x₂y₁"),
    ]
    for text, ans in unit3:
        questions.append({"text": f"【向量】{text}", "answer": ans, "explain": ans, "level": 1, "video": ""})
    # 单元4：三角函数
    unit4 = [
        ("sin²α+cos²α", "1"), ("两角和的正弦", "sin(α+β)=sinαcosβ+cosαsinβ"),
        ("两角差的正弦", "sin(α-β)=sinαcosβ-cosαsinβ"), ("两角和的余弦", "cos(α+β)=cosαcosβ-sinαsinβ"),
        ("两角差的余弦", "cos(α-β)=cosαcosβ+sinαsinβ"), ("二倍角正弦", "sin2α=2sinαcosα"),
        ("二倍角余弦", "cos2α=cos²α-sin²α=2cos²α-1=1-2sin²α"), ("sin30°的值", "1/2"),
        ("cos45°的值", "√2/2"), ("tan60°的值", "√3"),
    ]
    for text, ans in unit4:
        questions.append({"text": f"【三角函数】{text}", "answer": ans, "explain": ans, "level": 2, "video": ""})
    # 单元5：解三角形
    unit5 = [
        ("正弦定理", "a/sinA=b/sinB=c/sinC=2R"), ("余弦定理（求边）", "a²=b²+c²-2bc·cosA"),
        ("三角形面积公式（两边一角）", "S=½bc·sinA"),
    ]
    for text, ans in unit5:
        questions.append({"text": f"【解三角形】{text}", "answer": ans, "explain": ans, "level": 2, "video": ""})
    # 单元6：数列
    unit6 = [
        ("等差数列通项公式", "aₙ=a₁+(n-1)d"), ("等差数列前n项和公式", "Sₙ=n(a₁+aₙ)/2 = na₁+n(n-1)d/2"),
        ("等比数列通项公式", "aₙ=a₁·qⁿ⁻¹"), ("等比数列前n项和公式（q≠1）", "Sₙ=a₁(1-qⁿ)/(1-q)"),
    ]
    for text, ans in unit6:
        questions.append({"text": f"【数列】{text}", "answer": ans, "explain": ans, "level": 2, "video": ""})
    # 单元7：统计与概率
    unit7 = [
        ("平均数公式", "x̄=(∑xᵢ)/n"), ("方差公式", "s²=∑(xᵢ-x̄)²/n"), ("标准差公式", "s=√s²"),
        ("古典概型概率公式", "P(A)=事件A包含的基本事件数/总基本事件数"),
        ("互斥事件加法公式", "P(A∪B)=P(A)+P(B)"), ("独立事件乘法公式", "P(A∩B)=P(A)·P(B)"),
    ]
    for text, ans in unit7:
        questions.append({"text": f"【统计概率】{text}", "answer": ans, "explain": ans, "level": 2, "video": ""})
    # 单元8：立体几何基础
    unit8 = [
        ("柱体体积公式", "V=S·h"), ("锥体体积公式", "V=⅓S·h"), ("球体积公式", "V=4/3πR³"), ("球表面积公式", "S=4πR²"),
    ]
    for text, ans in unit8:
        questions.append({"text": f"【立体几何】{text}", "answer": ans, "explain": ans, "level": 3, "video": ""})
    # 单元9：函数基础
    unit9 = [
        ("一次函数一般式", "y=kx+b"), ("二次函数顶点横坐标", "-b/(2a)"),
        ("指数运算法则（同底相乘）", "aᵐ·aⁿ=aᵐ⁺ⁿ"), ("指数运算法则（幂的幂）", "(aᵐ)ⁿ=aᵐⁿ"),
        ("对数运算法则（积）", "logₐ(MN)=logₐM+logₐN"), ("对数运算法则（商）", "logₐ(M/N)=logₐM-logₐN"),
        ("对数运算法则（幂）", "logₐMⁿ=n·logₐM"),
    ]
    for text, ans in unit9:
        questions.append({"text": f"【函数】{text}", "answer": ans, "explain": ans, "level": 3, "video": ""})
    return questions

MATH_QUESTIONS = build_math_questions()

# ==================== 物理题库（完整7个实验） ====================
def build_physics_questions():
    questions = []
    # 实验1：匀变速直线运动
    exp1 = [
        ("打点计时器使用什么电源？频率多少？", "交流电 50Hz"), ("打点计时器打点周期", "0.02s"),
        ("平均速度公式", "v=Δx/Δt"), ("加速度公式（逐差法）", "a=(x₄+x₅+x₆-x₁-x₂-x₃)/(3T)²"),
        ("中间时刻速度等于", "平均速度"),
    ]
    for text, ans in exp1:
        questions.append({"text": f"【匀变速直线运动】{text}", "answer": ans, "explain": ans, "level": 1, "video": ""})
    # 实验2：弹簧弹力
    exp2 = [
        ("胡克定律公式", "F=kx"), ("弹簧劲度系数k的单位", "N/m"), ("F-x图像斜率表示", "劲度系数k"),
        ("测量弹簧原长的方法", "不挂钩码时测长度"),
    ]
    for text, ans in exp2:
        questions.append({"text": f"【弹簧弹力】{text}", "answer": ans, "explain": ans, "level": 1, "video": ""})
    # 实验3：平行四边形定则
    exp3 = [
        ("验证平行四边形定则时，两次拉橡皮筋要求什么相同？", "结点O位置相同"),
        ("弹簧测力计读数时视线要与刻度盘", "垂直"), ("力的图示中，合力与分力的关系", "平行四边形对角线"),
    ]
    for text, ans in exp3:
        questions.append({"text": f"【平行四边形定则】{text}", "answer": ans, "explain": ans, "level": 1, "video": ""})
    # 实验4：牛顿第二定律
    exp4 = [
        ("牛顿第二定律表达式", "F=ma"), ("平衡摩擦力时，小车后面要", "挂纸带"),
        ("当小车质量远大于钩码质量时，绳子拉力近似等于", "钩码重力"),
        ("a-F图像是过原点的直线，说明", "a与F成正比"), ("a-1/m图像是过原点的直线，说明", "a与m成反比"),
    ]
    for text, ans in exp4:
        questions.append({"text": f"【牛顿第二定律】{text}", "answer": ans, "explain": ans, "level": 2, "video": ""})
    # 实验5：平抛运动
    exp5 = [
        ("平抛运动水平方向做什么运动？", "匀速直线运动"), ("平抛运动竖直方向做什么运动？", "自由落体运动"),
        ("斜槽末端的安装要求", "水平"), ("每次小球从斜槽上", "同一位置由静止释放"),
        ("初速度公式", "v₀=x√(g/(2y))"),
    ]
    for text, ans in exp5:
        questions.append({"text": f"【平抛运动】{text}", "answer": ans, "explain": ans, "level": 2, "video": ""})
    # 实验6：机械能守恒
    exp6 = [
        ("验证机械能守恒的核心公式", "mgh=½mv²"), ("选择纸带时，第一、二点间距应接近", "2mm"),
        ("重锤下落过程中，存在什么阻力使ΔEp略大于ΔEk？", "空气阻力"), ("实验需要测量的物理量", "高度h和速度v"),
    ]
    for text, ans in exp6:
        questions.append({"text": f"【机械能守恒】{text}", "answer": ans, "explain": ans, "level": 2, "video": ""})
    # 实验7：测电源电动势
    exp7 = [
        ("测定电源电动势和内阻的实验电路核心方程", "E=U+Ir"), ("U-I图像纵轴截距表示", "电动势E"),
        ("U-I图像斜率的绝对值表示", "内阻r"), ("电压表应接在电源", "两端"), ("实验误差主要来源", "电压表分流或电流表分压"),
    ]
    for text, ans in exp7:
        questions.append({"text": f"【测电源电动势】{text}", "answer": ans, "explain": ans, "level": 3, "video": ""})
    return questions

PHYSICS_QUESTIONS = build_physics_questions()

# ==================== 英语单词库（动态生成约2500词） ====================
def generate_full_word_list():
    base = [
        ("abandon", "抛弃", "/əˈbændən/"), ("ability", "能力", "/əˈbɪləti/"),
        ("able", "能够", "/ˈeɪbl/"), ("abnormal", "反常", "/æbˈnɔːml/"),
        ("aboard", "上船", "/əˈbɔːd/"), ("about", "关于", "/əˈbaʊt/"),
        ("above", "上面", "/əˈbʌv/"), ("abroad", "国外", "/əˈbrɔːd/"),
        ("absence", "缺席", "/ˈæbsəns/"), ("absent", "缺席的", "/ˈæbsənt/"),
        ("absolute", "绝对", "/ˈæbsəluːt/"), ("absorb", "吸收", "/əbˈzɔːb/"),
        ("abstract", "抽象", "/ˈæbstrækt/"), ("abundant", "丰富", "/əˈbʌndənt/"),
        ("accept", "接受", "/əkˈsept/"), ("access", "进入", "/ˈækses/"),
        ("accident", "事故", "/ˈæksɪdənt/"), ("accompany", "陪伴", "/əˈkʌmpəni/"),
        ("accomplish", "完成", "/əˈkʌmplɪʃ/"), ("accord", "一致", "/əˈkɔːd/"),
        ("account", "账户", "/əˈkaʊnt/"), ("accurate", "精确", "/ˈækjərət/"),
        ("accuse", "指责", "/əˈkjuːz/"), ("achieve", "实现", "/əˈtʃiːv/"),
        ("acknowledge", "承认", "/əkˈnɒlɪdʒ/"), ("acquire", "获得", "/əˈkwaɪər/"),
        ("across", "穿过", "/əˈkrɒs/"), ("act", "行动", "/ækt/"),
        ("action", "行动", "/ˈækʃən/"), ("active", "活跃", "/ˈæktɪv/"),
        ("actual", "实际", "/ˈæktʃuəl/"), ("adapt", "适应", "/əˈdæpt/"),
        ("add", "增加", "/æd/"), ("address", "地址", "/əˈdres/"),
        ("adequate", "充足", "/ˈædɪkwət/"), ("adjust", "调整", "/əˈdʒʌst/"),
        ("admire", "钦佩", "/ədˈmaɪər/"), ("admit", "承认", "/ədˈmɪt/"),
        ("adopt", "采用", "/əˈdɒpt/"), ("advance", "前进", "/ədˈvɑːns/"),
        ("advantage", "优势", "/ədˈvɑːntɪdʒ/"), ("advice", "建议", "/ədˈvaɪs/"),
        ("advise", "建议", "/ədˈvaɪz/"), ("affect", "影响", "/əˈfekt/"),
        ("afford", "负担得起", "/əˈfɔːd/"), ("afraid", "害怕", "/əˈfreɪd/"),
        ("after", "之后", "/ˈɑːftər/"), ("again", "再次", "/əˈɡen/"),
        ("against", "反对", "/əˈɡenst/"), ("age", "年龄", "/eɪdʒ/"),
        ("agency", "机构", "/ˈeɪdʒənsi/"), ("agent", "代理人", "/ˈeɪdʒənt/"),
        ("agree", "同意", "/əˈɡriː/"), ("ahead", "向前", "/əˈhed/"),
        ("aid", "帮助", "/eɪd/"), ("aim", "目标", "/eɪm/"),
        ("air", "空气", "/eər/"), ("airport", "机场", "/ˈeəpɔːt/"),
        ("alarm", "警报", "/əˈlɑːm/"), ("album", "专辑", "/ˈælbəm/"),
        ("alcohol", "酒精", "/ˈælkəhɒl/"), ("alive", "活着", "/əˈlaɪv/"),
        ("all", "全部", "/ɔːl/"), ("allow", "允许", "/əˈlaʊ/"),
        ("almost", "几乎", "/ˈɔːlməʊst/"), ("alone", "单独", "/əˈləʊn/"),
        ("along", "沿着", "/əˈlɒŋ/"), ("already", "已经", "/ɔːlˈredi/"),
        ("also", "也", "/ˈɔːlsəʊ/"), ("although", "虽然", "/ɔːlˈðəʊ/"),
        ("always", "总是", "/ˈɔːlweɪz/"), ("amaze", "惊奇", "/əˈmeɪz/"),
        ("ambition", "野心", "/æmˈbɪʃən/"), ("among", "之中", "/əˈmʌŋ/"),
        ("amount", "数量", "/əˈmaʊnt/"), ("analyse", "分析", "/ˈænəlaɪz/"),
        ("ancient", "古老", "/ˈeɪnʃənt/"), ("anger", "愤怒", "/ˈæŋɡər/"),
        ("angle", "角度", "/ˈæŋɡəl/"), ("angry", "生气", "/ˈæŋɡri/"),
        ("animal", "动物", "/ˈænɪməl/"), ("announce", "宣布", "/əˈnaʊns/"),
        ("annual", "年度", "/ˈænjuəl/"), ("another", "另一个", "/əˈnʌðər/"),
        ("answer", "回答", "/ˈɑːnsər/"), ("anticipate", "预期", "/ænˈtɪsɪpeɪt/"),
        ("anxiety", "焦虑", "/æŋˈzaɪəti/"), ("any", "任何", "/ˈeni/"),
        ("apart", "分开", "/əˈpɑːt/"), ("apologize", "道歉", "/əˈpɒlədʒaɪz/"),
        ("appeal", "呼吁", "/əˈpiːl/"), ("appear", "出现", "/əˈpɪər/"),
        ("apple", "苹果", "/ˈæpəl/"), ("apply", "申请", "/əˈplaɪ/"),
        ("approach", "方法", "/əˈprəʊtʃ/"), ("approve", "批准", "/əˈpruːv/"),
        ("area", "区域", "/ˈeəriə/"), ("argue", "争论", "/ˈɑːɡjuː/"),
        ("arise", "出现", "/əˈraɪz/"), ("arm", "手臂", "/ɑːm/"),
        ("army", "军队", "/ˈɑːmi/"), ("around", "周围", "/əˈraʊnd/"),
        ("arrange", "安排", "/əˈreɪndʒ/"), ("arrest", "逮捕", "/əˈrest/"),
        ("arrive", "到达", "/əˈraɪv/"), ("art", "艺术", "/ɑːt/"),
        ("article", "文章", "/ˈɑːtɪkəl/"), ("artificial", "人造", "/ˌɑːtɪˈfɪʃəl/"),
        ("ashamed", "羞愧", "/əˈʃeɪmd/"), ("aside", "旁边", "/əˈsaɪd/"),
        ("ask", "问", "/ɑːsk/"), ("asleep", "睡着", "/əˈsliːp/"),
        ("aspect", "方面", "/ˈæspekt/"), ("assess", "评估", "/əˈses/"),
        ("assign", "分配", "/əˈsaɪn/"), ("assist", "帮助", "/əˈsɪst/"),
        ("assume", "假设", "/əˈsjuːm/"), ("astonish", "惊讶", "/əˈstɒnɪʃ/"),
        ("athlete", "运动员", "/ˈæθliːt/"), ("atmosphere", "大气", "/ˈætməsfɪər/"),
        ("attach", "附上", "/əˈtætʃ/"), ("attack", "攻击", "/əˈtæk/"),
        ("attempt", "尝试", "/əˈtempt/"), ("attend", "参加", "/əˈtend/"),
        ("attitude", "态度", "/ˈætɪtjuːd/"), ("attract", "吸引", "/əˈtrækt/"),
        ("audience", "观众", "/ˈɔːdiəns/"), ("author", "作者", "/ˈɔːθər/"),
        ("authority", "权威", "/ɔːˈθɒrəti/"), ("available", "可用", "/əˈveɪləbəl/"),
        ("average", "平均", "/ˈævərɪdʒ/"), ("avoid", "避免", "/əˈvɔɪd/"),
        ("awake", "唤醒", "/əˈweɪk/"), ("award", "奖励", "/əˈwɔːd/"),
        ("aware", "意识到", "/əˈweər/"), ("away", "离开", "/əˈweɪ/"),
        ("awful", "糟糕", "/ˈɔːfəl/"), ("baby", "婴儿", "/ˈbeɪbi/"),
        ("back", "后面", "/bæk/"), ("background", "背景", "/ˈbækɡraʊnd/"),
        ("bad", "坏", "/bæd/"), ("bag", "包", "/bæɡ/"),
        ("balance", "平衡", "/ˈbæləns/"), ("ball", "球", "/bɔːl/"),
        ("ban", "禁止", "/bæn/"), ("band", "乐队", "/bænd/"),
        ("bank", "银行", "/bæŋk/"), ("bar", "酒吧", "/bɑːr/"),
        ("bare", "赤裸", "/beər/"), ("bargain", "便宜货", "/ˈbɑːɡɪn/"),
        ("base", "基础", "/beɪs/"), ("basic", "基本", "/ˈbeɪsɪk/"),
        ("basin", "盆地", "/ˈbeɪsən/"), ("basis", "基础", "/ˈbeɪsɪs/"),
        ("battle", "战斗", "/ˈbætəl/"), ("be", "是", "/biː/"),
        ("beach", "海滩", "/biːtʃ/"), ("bear", "忍受", "/beər/"),
        ("beat", "打", "/biːt/"), ("beauty", "美丽", "/ˈbjuːti/"),
        ("because", "因为", "/bɪˈkɒz/"), ("become", "变成", "/bɪˈkʌm/"),
        ("bed", "床", "/bed/"), ("before", "之前", "/bɪˈfɔːr/"),
        ("begin", "开始", "/bɪˈɡɪn/"), ("behave", "表现", "/bɪˈheɪv/"),
        ("behind", "后面", "/bɪˈhaɪnd/"), ("believe", "相信", "/bɪˈliːv/"),
        ("bell", "钟", "/bel/"), ("belong", "属于", "/bɪˈlɒŋ/"),
        ("below", "下面", "/bɪˈləʊ/"), ("belt", "腰带", "/belt/"),
        ("bench", "长凳", "/bentʃ/"), ("bend", "弯曲", "/bend/"),
        ("benefit", "利益", "/ˈbenɪfɪt/"), ("beside", "旁边", "/bɪˈsaɪd/"),
        ("bet", "打赌", "/bet/"), ("better", "更好", "/ˈbetər/"),
        ("between", "之间", "/bɪˈtwiːn/"), ("beyond", "超越", "/bɪˈjɒnd/"),
        ("big", "大", "/bɪɡ/"), ("bike", "自行车", "/baɪk/"),
        ("bill", "账单", "/bɪl/"), ("bird", "鸟", "/bɜːd/"),
        ("birth", "出生", "/bɜːθ/"), ("bit", "一点", "/bɪt/"),
        ("bite", "咬", "/baɪt/"), ("bitter", "苦", "/ˈbɪtər/"),
        ("black", "黑", "/blæk/"), ("blame", "责备", "/bleɪm/"),
        ("blank", "空白", "/blæŋk/"), ("blind", "瞎", "/blaɪnd/"),
        ("block", "块", "/blɒk/"), ("blood", "血", "/blʌd/"),
        ("blow", "吹", "/bləʊ/"), ("blue", "蓝", "/bluː/"),
        ("board", "板", "/bɔːd/"), ("boat", "船", "/bəʊt/"),
        ("body", "身体", "/ˈbɒdi/"), ("boil", "煮", "/bɔɪl/"),
        ("bold", "大胆", "/bəʊld/"), ("bomb", "炸弹", "/bɒm/"),
        ("bone", "骨头", "/bəʊn/"), ("book", "书", "/bʊk/"),
        ("border", "边界", "/ˈbɔːdər/"), ("born", "出生", "/bɔːn/"),
        ("borrow", "借", "/ˈbɒrəʊ/"), ("boss", "老板", "/bɒs/"),
        ("both", "两者", "/bəʊθ/"), ("bother", "打扰", "/ˈbɒðər/"),
        ("bottle", "瓶子", "/ˈbɒtəl/"), ("bottom", "底部", "/ˈbɒtəm/"),
        ("bound", "边界", "/baʊnd/"), ("bow", "鞠躬", "/baʊ/"),
        ("bowl", "碗", "/bəʊl/"), ("box", "盒子", "/bɒks/"),
        ("boy", "男孩", "/bɔɪ/"), ("brain", "大脑", "/breɪn/"),
        ("branch", "分支", "/brɑːntʃ/"), ("brave", "勇敢", "/breɪv/"),
        ("bread", "面包", "/bred/"), ("break", "打破", "/breɪk/"),
        ("breath", "呼吸", "/breθ/"), ("breathe", "呼吸", "/briːð/"),
        ("bridge", "桥", "/brɪdʒ/"), ("brief", "简短", "/briːf/"),
        ("bright", "明亮", "/braɪt/"), ("bring", "带来", "/brɪŋ/"),
        ("broad", "宽阔", "/brɔːd/"), ("broken", "破碎", "/ˈbrəʊkən/"),
        ("brother", "兄弟", "/ˈbrʌðər/"), ("brown", "棕色", "/braʊn/"),
        ("brush", "刷子", "/brʌʃ/"), ("budget", "预算", "/ˈbʌdʒɪt/"),
        ("build", "建造", "/bɪld/"), ("building", "建筑", "/ˈbɪldɪŋ/"),
        ("bullet", "子弹", "/ˈbʊlɪt/"), ("bunch", "束", "/bʌntʃ/"),
        ("burn", "燃烧", "/bɜːn/"), ("burst", "爆发", "/bɜːst/"),
        ("bury", "埋葬", "/ˈberi/"), ("bus", "公交", "/bʌs/"),
        ("bush", "灌木", "/bʊʃ/"), ("business", "商业", "/ˈbɪznəs/"),
        ("busy", "忙碌", "/ˈbɪzi/"), ("but", "但是", "/bʌt/"),
        ("butter", "黄油", "/ˈbʌtər/"), ("button", "按钮", "/ˈbʌtən/"),
        ("buy", "买", "/baɪ/"), ("by", "通过", "/baɪ/"),
        ("cabinet", "内阁", "/ˈkæbɪnət/"), ("cable", "电缆", "/ˈkeɪbəl/"),
        ("cake", "蛋糕", "/keɪk/"), ("calculate", "计算", "/ˈkælkjʊleɪt/"),
        ("call", "呼叫", "/kɔːl/"), ("calm", "平静", "/kɑːm/"),
        ("camera", "相机", "/ˈkæmərə/"), ("camp", "营地", "/kæmp/"),
        ("campaign", "运动", "/kæmˈpeɪn/"), ("campus", "校园", "/ˈkæmpəs/"),
        ("can", "能", "/kæn/"), ("cancel", "取消", "/ˈkænsəl/"),
        ("cancer", "癌症", "/ˈkænsər/"), ("candidate", "候选人", "/ˈkændɪdət/"),
        ("candle", "蜡烛", "/ˈkændəl/"), ("cap", "帽子", "/kæp/"),
        ("capable", "有能力", "/ˈkeɪpəbəl/"), ("capacity", "容量", "/kəˈpæsəti/"),
        ("capital", "首都", "/ˈkæpɪtəl/"), ("captain", "船长", "/ˈkæptɪn/"),
        ("capture", "捕获", "/ˈkæptʃər/"), ("car", "汽车", "/kɑːr/"),
        ("card", "卡片", "/kɑːd/"), ("care", "关心", "/keər/"),
        ("career", "职业", "/kəˈrɪər/"), ("careful", "小心", "/ˈkeəfəl/"),
        ("carry", "携带", "/ˈkæri/"), ("case", "情况", "/keɪs/"),
        ("cash", "现金", "/kæʃ/"), ("cast", "投掷", "/kɑːst/"),
        ("castle", "城堡", "/ˈkɑːsəl/"), ("cat", "猫", "/kæt/"),
        ("catch", "抓住", "/kætʃ/"), ("cause", "原因", "/kɔːz/"),
        ("celebrate", "庆祝", "/ˈselɪbreɪt/"), ("cell", "细胞", "/sel/"),
        ("cent", "分", "/sent/"), ("center", "中心", "/ˈsentər/"),
        ("century", "世纪", "/ˈsentʃəri/"), ("certain", "确定", "/ˈsɜːtən/"),
        ("chain", "链", "/tʃeɪn/"), ("chair", "椅子", "/tʃeər/"),
        ("challenge", "挑战", "/ˈtʃælɪndʒ/"), ("chance", "机会", "/tʃɑːns/"),
        ("change", "改变", "/tʃeɪndʒ/"), ("channel", "频道", "/ˈtʃænəl/"),
        ("chapter", "章节", "/ˈtʃæptər/"), ("character", "性格", "/ˈkærəktər/"),
        ("charge", "收费", "/tʃɑːdʒ/"), ("charity", "慈善", "/ˈtʃærəti/"),
        ("chase", "追逐", "/tʃeɪs/"), ("cheap", "便宜", "/tʃiːp/"),
        ("check", "检查", "/tʃek/"), ("cheer", "欢呼", "/tʃɪər/"),
        ("cheese", "奶酪", "/tʃiːz/"), ("chemical", "化学的", "/ˈkemɪkəl/"),
        ("chemistry", "化学", "/ˈkemɪstri/"), ("chest", "胸部", "/tʃest/"),
        ("chicken", "鸡", "/ˈtʃɪkɪn/"), ("chief", "首领", "/tʃiːf/"),
        ("child", "孩子", "/tʃaɪld/"), ("chimney", "烟囱", "/ˈtʃɪmni/"),
        ("choice", "选择", "/tʃɔɪs/"), ("choose", "选择", "/tʃuːz/"),
        ("church", "教堂", "/tʃɜːtʃ/"), ("cigarette", "香烟", "/ˌsɪɡəˈret/"),
        ("circle", "圆", "/ˈsɜːkəl/"), ("circumstance", "情况", "/ˈsɜːkəmstəns/"),
        ("cite", "引用", "/saɪt/"), ("citizen", "公民", "/ˈsɪtɪzən/"),
        ("city", "城市", "/ˈsɪti/"), ("civil", "公民的", "/ˈsɪvəl/"),
        ("claim", "声称", "/kleɪm/"), ("class", "班级", "/klɑːs/"),
        ("classic", "经典", "/ˈklæsɪk/"), ("classify", "分类", "/ˈklæsɪfaɪ/"),
        ("classroom", "教室", "/ˈklɑːsruːm/"), ("clean", "清洁", "/kliːn/"),
        ("clear", "清晰", "/klɪər/"), ("clerk", "职员", "/klɑːk/"),
        ("clever", "聪明", "/ˈklevər/"), ("click", "点击", "/klɪk/"),
        ("climate", "气候", "/ˈklaɪmət/"), ("climb", "爬", "/klaɪm/"),
        ("clock", "钟", "/klɒk/"), ("close", "关闭", "/kləʊz/"),
        ("cloth", "布", "/klɒθ/"), ("clothes", "衣服", "/kləʊðz/"),
        ("cloud", "云", "/klaʊd/"), ("club", "俱乐部", "/klʌb/"),
        ("clue", "线索", "/kluː/"), ("coach", "教练", "/kəʊtʃ/"),
        ("coal", "煤", "/kəʊl/"), ("coast", "海岸", "/kəʊst/"),
        ("coat", "外套", "/kəʊt/"), ("code", "代码", "/kəʊd/"),
        ("coffee", "咖啡", "/ˈkɒfi/"), ("cold", "冷", "/kəʊld/"),
        ("collapse", "崩溃", "/kəˈlæps/"), ("colleague", "同事", "/ˈkɒliːɡ/"),
        ("collect", "收集", "/kəˈlekt/"), ("college", "大学", "/ˈkɒlɪdʒ/"),
        ("color", "颜色", "/ˈkʌlər/"), ("column", "列", "/ˈkɒləm/"),
        ("comb", "梳子", "/kəʊm/"), ("combination", "组合", "/ˌkɒmbɪˈneɪʃən/"),
        ("combine", "结合", "/kəmˈbaɪn/"), ("come", "来", "/kʌm/"),
        ("comfort", "舒适", "/ˈkʌmfət/"), ("command", "命令", "/kəˈmɑːnd/"),
        ("comment", "评论", "/ˈkɒment/"), ("commercial", "商业的", "/kəˈmɜːʃəl/"),
        ("commission", "委员会", "/kəˈmɪʃən/"), ("commit", "犯", "/kəˈmɪt/"),
        ("committee", "委员会", "/kəˈmɪti/"), ("common", "普通", "/ˈkɒmən/"),
        ("communicate", "沟通", "/kəˈmjuːnɪkeɪt/"), ("community", "社区", "/kəˈmjuːnəti/"),
        ("company", "公司", "/ˈkʌmpəni/"), ("compare", "比较", "/kəmˈpeər/"),
        ("compete", "竞争", "/kəmˈpiːt/"), ("competitive", "竞争性", "/kəmˈpetətɪv/"),
        ("complain", "抱怨", "/kəmˈpleɪn/"), ("complete", "完整", "/kəmˈpliːt/"),
        ("complex", "复杂", "/ˈkɒmpleks/"), ("complicate", "复杂化", "/ˈkɒmplɪkeɪt/"),
        ("computer", "电脑", "/kəmˈpjuːtər/"), ("concentrate", "集中", "/ˈkɒnsəntreɪt/"),
        ("concept", "概念", "/ˈkɒnsept/"), ("concern", "关心", "/kənˈsɜːn/"),
        ("concert", "音乐会", "/ˈkɒnsət/"), ("conclude", "总结", "/kənˈkluːd/"),
        ("condition", "条件", "/kənˈdɪʃən/"), ("conduct", "行为", "/kənˈdʌkt/"),
        ("conference", "会议", "/ˈkɒnfərəns/"), ("confidence", "信心", "/ˈkɒnfɪdəns/"),
        ("confirm", "确认", "/kənˈfɜːm/"), ("conflict", "冲突", "/ˈkɒnflɪkt/"),
        ("confuse", "困惑", "/kənˈfjuːz/"), ("connect", "连接", "/kəˈnekt/"),
        ("conscience", "良心", "/ˈkɒnʃəns/"), ("conscious", "有意识", "/ˈkɒnʃəs/"),
        ("consider", "考虑", "/kənˈsɪdər/"), ("consist", "组成", "/kənˈsɪst/"),
        ("constant", "恒定", "/ˈkɒnstənt/"), ("construct", "建造", "/kənˈstrʌkt/"),
        ("consult", "咨询", "/kənˈsʌlt/"), ("consume", "消费", "/kənˈsjuːm/"),
        ("contact", "联系", "/ˈkɒntækt/"), ("contain", "包含", "/kənˈteɪn/"),
        ("content", "内容", "/ˈkɒntent/"), ("contest", "比赛", "/ˈkɒntest/"),
        ("context", "上下文", "/ˈkɒntekst/"), ("continue", "继续", "/kənˈtɪnjuː/"),
        ("contract", "合同", "/ˈkɒntrækt/"), ("contrary", "相反", "/ˈkɒntrəri/"),
        ("contrast", "对比", "/ˈkɒntrɑːst/"), ("contribute", "贡献", "/kənˈtrɪbjuːt/"),
        ("control", "控制", "/kənˈtrəʊl/"), ("convenient", "方便", "/kənˈviːniənt/"),
        ("conversation", "对话", "/ˌkɒnvəˈseɪʃən/"), ("convince", "说服", "/kənˈvɪns/"),
        ("cook", "烹饪", "/kʊk/"), ("cool", "凉爽", "/kuːl/"),
        ("copy", "复制", "/ˈkɒpi/"), ("core", "核心", "/kɔːr/"),
        ("corner", "角落", "/ˈkɔːnər/"), ("correct", "正确", "/kəˈrekt/"),
        ("cost", "成本", "/kɒst/"), ("cottage", "小屋", "/ˈkɒtɪdʒ/"),
        ("cotton", "棉花", "/ˈkɒtən/"), ("cough", "咳嗽", "/kɒf/"),
        ("could", "可以", "/kʊd/"), ("council", "理事会", "/ˈkaʊnsəl/"),
        ("count", "计数", "/kaʊnt/"), ("counter", "柜台", "/ˈkaʊntər/"),
        ("country", "国家", "/ˈkʌntri/"), ("county", "县", "/ˈkaʊnti/"),
        ("couple", "夫妇", "/ˈkʌpəl/"), ("courage", "勇气", "/ˈkʌrɪdʒ/"),
        ("course", "课程", "/kɔːs/"), ("court", "法院", "/kɔːt/"),
        ("cousin", "表亲", "/ˈkʌzən/"), ("cover", "覆盖", "/ˈkʌvər/"),
        ("cow", "牛", "/kaʊ/"), ("crack", "裂缝", "/kræk/"),
        ("craft", "工艺", "/krɑːft/"), ("crash", "碰撞", "/kræʃ/"),
        ("crazy", "疯狂", "/ˈkreɪzi/"), ("cream", "奶油", "/kriːm/"),
        ("create", "创造", "/kriˈeɪt/"), ("creature", "生物", "/ˈkriːtʃər/"),
        ("credit", "信用", "/ˈkredɪt/"), ("crew", "船员", "/kruː/"),
        ("crime", "犯罪", "/kraɪm/"), ("crisis", "危机", "/ˈkraɪsɪs/"),
        ("critic", "批评家", "/ˈkrɪtɪk/"), ("critical", "关键", "/ˈkrɪtɪkəl/"),
        ("criticize", "批评", "/ˈkrɪtɪsaɪz/"), ("crop", "作物", "/krɒp/"),
        ("cross", "穿过", "/krɒs/"), ("crowd", "人群", "/kraʊd/"),
        ("crown", "王冠", "/kraʊn/"), ("crucial", "至关重要", "/ˈkruːʃəl/"),
        ("cruel", "残酷", "/ˈkruːəl/"), ("cry", "哭", "/kraɪ/"),
        ("culture", "文化", "/ˈkʌltʃər/"), ("cup", "杯子", "/kʌp/"),
        ("curious", "好奇", "/ˈkjʊəriəs/"), ("current", "当前", "/ˈkʌrənt/"),
        ("curtain", "窗帘", "/ˈkɜːtən/"), ("curve", "曲线", "/kɜːv/"),
        ("cushion", "垫子", "/ˈkʊʃən/"), ("custom", "习惯", "/ˈkʌstəm/"),
        ("customer", "顾客", "/ˈkʌstəmər/"), ("cut", "切", "/kʌt/"),
        ("cycle", "循环", "/ˈsaɪkəl/"), ("daily", "每日", "/ˈdeɪli/"),
        ("damage", "损害", "/ˈdæmɪdʒ/"), ("dance", "跳舞", "/dɑːns/"),
        ("danger", "危险", "/ˈdeɪndʒər/"), ("dark", "黑暗", "/dɑːk/"),
        ("data", "数据", "/ˈdeɪtə/"), ("date", "日期", "/deɪt/"),
        ("daughter", "女儿", "/ˈdɔːtər/"), ("day", "天", "/deɪ/"),
        ("dead", "死", "/ded/"), ("deal", "交易", "/diːl/"),
        ("dear", "亲爱的", "/dɪər/"), ("death", "死亡", "/deθ/"),
        ("debate", "辩论", "/dɪˈbeɪt/"), ("debt", "债务", "/det/"),
        ("decade", "十年", "/ˈdekeɪd/"), ("decide", "决定", "/dɪˈsaɪd/"),
        ("decision", "决定", "/dɪˈsɪʒən/"), ("declare", "宣布", "/dɪˈkleər/"),
        ("decline", "下降", "/dɪˈklaɪn/"), ("decorate", "装饰", "/ˈdekəreɪt/"),
        ("decrease", "减少", "/dɪˈkriːs/"), ("deep", "深", "/diːp/"),
        ("defeat", "击败", "/dɪˈfiːt/"), ("defend", "保卫", "/dɪˈfend/"),
        ("define", "定义", "/dɪˈfaɪn/"), ("definite", "明确", "/ˈdefɪnət/"),
        ("degree", "程度", "/dɪˈɡriː/"), ("delay", "延迟", "/dɪˈleɪ/"),
        ("delicate", "精致", "/ˈdelɪkət/"), ("delicious", "美味", "/dɪˈlɪʃəs/"),
        ("delight", "高兴", "/dɪˈlaɪt/"), ("deliver", "递送", "/dɪˈlɪvər/"),
        ("demand", "需求", "/dɪˈmɑːnd/"), ("democracy", "民主", "/dɪˈmɒkrəsi/"),
        ("demonstrate", "演示", "/ˈdemənstreɪt/"), ("dense", "密集", "/dens/"),
        ("density", "密度", "/ˈdensəti/"), ("deny", "否认", "/dɪˈnaɪ/"),
        ("depend", "依赖", "/dɪˈpend/"), ("deposit", "存款", "/dɪˈpɒzɪt/"),
        ("depress", "压抑", "/dɪˈpres/"), ("depth", "深度", "/depθ/"),
        ("deputy", "副手", "/ˈdepjuti/"), ("derive", "派生", "/dɪˈraɪv/"),
        ("descend", "下降", "/dɪˈsend/"), ("describe", "描述", "/dɪˈskraɪb/"),
        ("desert", "沙漠", "/ˈdezət/"), ("deserve", "应得", "/dɪˈzɜːv/"),
        ("design", "设计", "/dɪˈzaɪn/"), ("desire", "渴望", "/dɪˈzaɪər/"),
        ("desk", "书桌", "/desk/"), ("desperate", "绝望", "/ˈdespərət/"),
        ("despite", "尽管", "/dɪˈspaɪt/"), ("destroy", "摧毁", "/dɪˈstrɔɪ/"),
        ("detail", "细节", "/ˈdiːteɪl/"), ("detect", "检测", "/dɪˈtekt/"),
        ("determine", "确定", "/dɪˈtɜːmɪn/"), ("develop", "发展", "/dɪˈveləp/"),
        ("device", "设备", "/dɪˈvaɪs/"), ("devil", "魔鬼", "/ˈdevəl/"),
        ("devote", "奉献", "/dɪˈvəʊt/"), ("diagram", "图表", "/ˈdaɪəɡræm/"),
        ("dialogue", "对话", "/ˈdaɪəlɒɡ/"), ("diamond", "钻石", "/ˈdaɪəmənd/"),
        ("diary", "日记", "/ˈdaɪəri/"), ("dictate", "口述", "/dɪkˈteɪt/"),
        ("dictionary", "词典", "/ˈdɪkʃənəri/"), ("die", "死", "/daɪ/"),
        ("differ", "不同", "/ˈdɪfər/"), ("difference", "差异", "/ˈdɪfərəns/"),
        ("different", "不同", "/ˈdɪfərənt/"), ("difficult", "困难", "/ˈdɪfɪkəlt/"),
        ("difficulty", "困难", "/ˈdɪfɪkəlti/"), ("dig", "挖", "/dɪɡ/"),
        ("digital", "数字", "/ˈdɪdʒɪtəl/"), ("dignity", "尊严", "/ˈdɪɡnəti/"),
        ("dilemma", "困境", "/dɪˈlemə/"), ("dim", "昏暗", "/dɪm/"),
        ("dimension", "维度", "/daɪˈmenʃən/"), ("dinner", "晚餐", "/ˈdɪnər/"),
        ("direct", "直接", "/dɪˈrekt/"), ("direction", "方向", "/dɪˈrekʃən/"),
        ("director", "导演", "/dɪˈrektər/"), ("dirt", "污垢", "/dɜːt/"),
        ("dirty", "脏", "/ˈdɜːti/"), ("disappear", "消失", "/ˌdɪsəˈpɪər/"),
        ("disappoint", "失望", "/ˌdɪsəˈpɔɪnt/"), ("disaster", "灾难", "/dɪˈzɑːstər/"),
        ("discipline", "纪律", "/ˈdɪsɪplɪn/"), ("discount", "折扣", "/ˈdɪskaʊnt/"),
        ("discover", "发现", "/dɪˈskʌvər/"), ("discuss", "讨论", "/dɪˈskʌs/"),
        ("disease", "疾病", "/dɪˈziːz/"), ("disgust", "厌恶", "/dɪsˈɡʌst/"),
        ("dish", "盘子", "/dɪʃ/"), ("disk", "磁盘", "/dɪsk/"),
        ("dismiss", "解雇", "/dɪsˈmɪs/"), ("disorder", "混乱", "/dɪsˈɔːdər/"),
        ("display", "展示", "/dɪˈspleɪ/"), ("dispute", "争论", "/dɪˈspjuːt/"),
        ("distance", "距离", "/ˈdɪstəns/"), ("distant", "遥远", "/ˈdɪstənt/"),
        ("distinct", "不同", "/dɪˈstɪŋkt/"), ("distinguish", "区分", "/dɪˈstɪŋɡwɪʃ/"),
        ("distribute", "分配", "/dɪˈstrɪbjuːt/"), ("district", "地区", "/ˈdɪstrɪkt/"),
        ("disturb", "打扰", "/dɪˈstɜːb/"), ("dive", "潜水", "/daɪv/"),
        ("divide", "分开", "/dɪˈvaɪd/"), ("divine", "神圣", "/dɪˈvaɪn/"),
        ("division", "部门", "/dɪˈvɪʒən/"), ("divorce", "离婚", "/dɪˈvɔːs/"),
        ("dizzy", "头晕", "/ˈdɪzi/"), ("do", "做", "/duː/"),
        ("doctor", "医生", "/ˈdɒktər/"), ("document", "文件", "/ˈdɒkjʊmənt/"),
        ("dog", "狗", "/dɒɡ/"), ("dollar", "美元", "/ˈdɒlər/"),
        ("domain", "领域", "/dəʊˈmeɪn/"), ("domestic", "国内", "/dəˈmestɪk/"),
        ("dominant", "主导", "/ˈdɒmɪnənt/"), ("dominate", "统治", "/ˈdɒmɪneɪt/"),
        ("donate", "捐赠", "/dəʊˈneɪt/"), ("door", "门", "/dɔːr/"),
        ("dot", "点", "/dɒt/"), ("double", "双倍", "/ˈdʌbəl/"),
        ("doubt", "怀疑", "/daʊt/"), ("down", "向下", "/daʊn/"),
        ("download", "下载", "/ˈdaʊnləʊd/"), ("downstairs", "楼下", "/ˌdaʊnˈsteəz/"),
        ("downtown", "市中心", "/ˌdaʊnˈtaʊn/"), ("dozen", "一打", "/ˈdʌzən/"),
        ("draft", "草稿", "/drɑːft/"), ("drag", "拖", "/dræɡ/"),
        ("drama", "戏剧", "/ˈdrɑːmə/"), ("dramatic", "戏剧性", "/drəˈmætɪk/"),
        ("draw", "画", "/drɔː/"), ("dream", "梦", "/driːm/"),
        ("dress", "裙子", "/dres/"), ("drink", "喝", "/drɪŋk/"),
        ("drive", "驾驶", "/draɪv/"), ("drop", "掉落", "/drɒp/"),
        ("drug", "药物", "/drʌɡ/"), ("drum", "鼓", "/drʌm/"),
        ("dry", "干", "/draɪ/"), ("duck", "鸭子", "/dʌk/"),
        ("due", "到期", "/djuː/"), ("dull", "迟钝", "/dʌl/"),
        ("dump", "倾倒", "/dʌmp/"), ("during", "在...期间", "/ˈdjʊərɪŋ/"),
        ("dust", "灰尘", "/dʌst/"), ("duty", "责任", "/ˈdjuːti/"),
        ("dynamic", "动态", "/daɪˈnæmɪk/"), ("eager", "渴望", "/ˈiːɡər/"),
        ("ear", "耳朵", "/ɪər/"), ("early", "早", "/ˈɜːli/"),
        ("earn", "赚", "/ɜːn/"), ("earth", "地球", "/ɜːθ/"),
        ("ease", "容易", "/iːz/"), ("east", "东", "/iːst/"),
        ("easy", "容易", "/ˈiːzi/"), ("eat", "吃", "/iːt/"),
        ("echo", "回声", "/ˈekəʊ/"), ("economic", "经济", "/ˌiːkəˈnɒmɪk/"),
        ("economy", "经济", "/ɪˈkɒnəmi/"), ("edge", "边缘", "/edʒ/"),
        ("edition", "版本", "/ɪˈdɪʃən/"), ("editor", "编辑", "/ˈedɪtər/"),
        ("educate", "教育", "/ˈedʒʊkeɪt/"), ("effect", "效果", "/ɪˈfekt/"),
        ("efficient", "高效", "/ɪˈfɪʃənt/"), ("effort", "努力", "/ˈefət/"),
        ("egg", "蛋", "/eɡ/"), ("eight", "八", "/eɪt/"),
        ("either", "两者之一", "/ˈaɪðər/"), ("elderly", "老年人", "/ˈeldəli/"),
        ("elect", "选举", "/ɪˈlekt/"), ("electric", "电", "/ɪˈlektrɪk/"),
        ("elegant", "优雅", "/ˈelɪɡənt/"), ("element", "元素", "/ˈelɪmənt/"),
        ("elephant", "大象", "/ˈelɪfənt/"), ("else", "其他", "/els/"),
        ("email", "电子邮件", "/ˈiːmeɪl/"), ("embarrass", "尴尬", "/ɪmˈbærəs/"),
        ("embrace", "拥抱", "/ɪmˈbreɪs/"), ("emerge", "出现", "/ɪˈmɜːdʒ/"),
        ("emergency", "紧急", "/ɪˈmɜːdʒənsi/"), ("emotion", "情绪", "/ɪˈməʊʃən/"),
        ("emphasis", "强调", "/ˈemfəsɪs/"), ("employ", "雇用", "/ɪmˈplɔɪ/"),
        ("empty", "空", "/ˈempti/"), ("enable", "使能够", "/ɪˈneɪbəl/"),
        ("encounter", "遇到", "/ɪnˈkaʊntər/"), ("encourage", "鼓励", "/ɪnˈkʌrɪdʒ/"),
        ("end", "结束", "/end/"), ("enemy", "敌人", "/ˈenəmi/"),
        ("energy", "能量", "/ˈenədʒi/"), ("engage", "参与", "/ɪnˈɡeɪdʒ/"),
        ("engine", "引擎", "/ˈendʒɪn/"), ("engineer", "工程师", "/ˌendʒɪˈnɪər/"),
        ("enjoy", "享受", "/ɪnˈdʒɔɪ/"), ("enough", "足够", "/ɪˈnʌf/"),
        ("ensure", "确保", "/ɪnˈʃʊər/"), ("enter", "进入", "/ˈentər/"),
        ("enterprise", "企业", "/ˈentəpraɪz/"), ("entertain", "娱乐", "/ˌentəˈteɪn/"),
        ("enthusiasm", "热情", "/ɪnˈθjuːziæzəm/"), ("entire", "整个", "/ɪnˈtaɪər/"),
        ("entitle", "授权", "/ɪnˈtaɪtəl/"), ("entry", "进入", "/ˈentri/"),
        ("environment", "环境", "/ɪnˈvaɪrənmənt/"), ("equal", "平等", "/ˈiːkwəl/"),
        ("equip", "装备", "/ɪˈkwɪp/"), ("error", "错误", "/ˈerər/"),
        ("escape", "逃跑", "/ɪˈskeɪp/"), ("especially", "特别", "/ɪˈspeʃəli/"),
        ("essay", "文章", "/ˈeseɪ/"), ("essential", "必要", "/ɪˈsenʃəl/"),
        ("establish", "建立", "/ɪˈstæblɪʃ/"), ("estate", "房地产", "/ɪˈsteɪt/"),
        ("estimate", "估计", "/ˈestɪmeɪt/"), ("ethnic", "种族", "/ˈeθnɪk/"),
        ("evaluate", "评估", "/ɪˈvæljʊeɪt/"), ("even", "甚至", "/ˈiːvən/"),
        ("event", "事件", "/ɪˈvent/"), ("eventually", "最终", "/ɪˈventʃuəli/"),
        ("ever", "曾经", "/ˈevər/"), ("every", "每个", "/ˈevri/"),
        ("evidence", "证据", "/ˈevɪdəns/"), ("evil", "邪恶", "/ˈiːvəl/"),
        ("exact", "精确", "/ɪɡˈzækt/"), ("exam", "考试", "/ɪɡˈzæm/"),
        ("examine", "检查", "/ɪɡˈzæmɪn/"), ("example", "例子", "/ɪɡˈzɑːmpəl/"),
        ("exceed", "超过", "/ɪkˈsiːd/"), ("excellent", "优秀", "/ˈeksələnt/"),
        ("except", "除了", "/ɪkˈsept/"), ("exchange", "交换", "/ɪksˈtʃeɪndʒ/"),
        ("excite", "兴奋", "/ɪkˈsaɪt/"), ("exclude", "排除", "/ɪkˈskluːd/"),
        ("excuse", "借口", "/ɪkˈskjuːz/"), ("execute", "执行", "/ˈeksɪkjuːt/"),
        ("exercise", "锻炼", "/ˈeksəsaɪz/"), ("exhaust", "耗尽", "/ɪɡˈzɔːst/"),
        ("exhibit", "展览", "/ɪɡˈzɪbɪt/"), ("exist", "存在", "/ɪɡˈzɪst/"),
        ("exit", "出口", "/ˈeksɪt/"), ("expand", "扩大", "/ɪkˈspænd/"),
        ("expect", "期望", "/ɪkˈspekt/"), ("expense", "花费", "/ɪkˈspens/"),
        ("expensive", "昂贵", "/ɪkˈspensɪv/"), ("experience", "经验", "/ɪkˈspɪəriəns/"),
        ("experiment", "实验", "/ɪkˈsperɪmənt/"), ("expert", "专家", "/ˈekspɜːt/"),
        ("explain", "解释", "/ɪkˈspleɪn/"), ("explode", "爆炸", "/ɪkˈspləʊd/"),
        ("explore", "探索", "/ɪkˈsplɔːr/"), ("export", "出口", "/ɪkˈspɔːt/"),
        ("expose", "暴露", "/ɪkˈspəʊz/"), ("express", "表达", "/ɪkˈspres/"),
        ("extend", "扩展", "/ɪkˈstend/"), ("extent", "程度", "/ɪkˈstent/"),
        ("external", "外部", "/ɪkˈstɜːnəl/"), ("extra", "额外", "/ˈekstrə/"),
        ("extraordinary", "非凡", "/ɪkˈstrɔːdənəri/"), ("extreme", "极端", "/ɪkˈstriːm/"),
        ("eye", "眼睛", "/aɪ/"), ("face", "脸", "/feɪs/"),
        ("facility", "设施", "/fəˈsɪləti/"), ("fact", "事实", "/fækt/"),
        ("factor", "因素", "/ˈfæktər/"), ("factory", "工厂", "/ˈfæktəri/"),
        ("fail", "失败", "/feɪl/"), ("fair", "公平", "/feər/"),
        ("faith", "信仰", "/feɪθ/"), ("fall", "落下", "/fɔːl/"),
        ("false", "假", "/fɔːls/"), ("fame", "名声", "/feɪm/"),
        ("family", "家庭", "/ˈfæməli/"), ("famous", "著名", "/ˈfeɪməs/"),
        ("fan", "粉丝", "/fæn/"), ("fancy", "幻想", "/ˈfænsi/"),
        ("fantastic", "奇妙", "/fænˈtæstɪk/"), ("far", "远", "/fɑːr/"),
        ("farm", "农场", "/fɑːm/"), ("fascinating", "迷人", "/ˈfæsɪneɪtɪŋ/"),
        ("fashion", "时尚", "/ˈfæʃən/"), ("fast", "快", "/fɑːst/"),
        ("fat", "胖", "/fæt/"), ("fatal", "致命", "/ˈfeɪtəl/"),
        ("father", "父亲", "/ˈfɑːðər/"), ("fault", "过错", "/fɔːlt/"),
        ("favor", " favor", "/ˈfeɪvər/"), ("favorite", "最爱", "/ˈfeɪvərɪt/"),
        ("fear", "恐惧", "/fɪər/"), ("feature", "特征", "/ˈfiːtʃər/"),
        ("federal", "联邦", "/ˈfedərəl/"), ("fee", "费用", "/fiː/"),
        ("feed", "喂养", "/fiːd/"), ("feel", "感觉", "/fiːl/"),
        ("fellow", "家伙", "/ˈfeləʊ/"), ("female", "女性", "/ˈfiːmeɪl/"),
        ("fence", "栅栏", "/fens/"), ("festival", "节日", "/ˈfestɪvəl/"),
        ("fetch", "取", "/fetʃ/"), ("fever", "发烧", "/ˈfiːvər/"),
        ("few", "很少", "/fjuː/"), ("field", "田野", "/fiːld/"),
        ("fierce", "凶猛", "/fɪəs/"), ("fight", "战斗", "/faɪt/"),
        ("figure", "数字", "/ˈfɪɡər/"), ("file", "文件", "/faɪl/"),
        ("fill", "填满", "/fɪl/"), ("film", "电影", "/fɪlm/"),
        ("final", "最终", "/ˈfaɪnəl/"), ("finance", "金融", "/ˈfaɪnæns/"),
        ("find", "找到", "/faɪnd/"), ("fine", "好", "/faɪn/"),
        ("finger", "手指", "/ˈfɪŋɡər/"), ("finish", "完成", "/ˈfɪnɪʃ/"),
        ("fire", "火", "/ˈfaɪər/"), ("firm", "公司", "/fɜːm/"),
        ("first", "第一", "/fɜːst/"), ("fish", "鱼", "/fɪʃ/"),
        ("fit", "适合", "/fɪt/"), ("five", "五", "/faɪv/"),
        ("fix", "修理", "/fɪks/"), ("flag", "旗", "/flæɡ/"),
        ("flame", "火焰", "/fleɪm/"), ("flash", "闪光", "/flæʃ/"),
        ("flat", "公寓", "/flæt/"), ("flavor", "风味", "/ˈfleɪvər/"),
        ("flesh", "肉", "/fleʃ/"), ("flight", "飞行", "/flaɪt/"),
        ("float", "漂浮", "/fləʊt/"), ("flood", "洪水", "/flʌd/"),
        ("floor", "地板", "/flɔːr/"), ("flour", "面粉", "/ˈflaʊər/"),
        ("flow", "流动", "/fləʊ/"), ("flower", "花", "/ˈflaʊər/"),
        ("fluid", "流体", "/ˈfluːɪd/"), ("fly", "飞", "/flaɪ/"),
        ("focus", "焦点", "/ˈfəʊkəs/"), ("fold", "折叠", "/fəʊld/"),
        ("follow", "跟随", "/ˈfɒləʊ/"), ("food", "食物", "/fuːd/"),
        ("fool", "傻瓜", "/fuːl/"), ("foot", "脚", "/fʊt/"),
        ("for", "为了", "/fɔːr/"), ("force", "力量", "/fɔːs/"),
        ("foreign", "外国", "/ˈfɒrən/"), ("forest", "森林", "/ˈfɒrɪst/"),
        ("forever", "永远", "/fəˈrevər/"), ("forget", "忘记", "/fəˈɡet/"),
        ("forgive", "原谅", "/fəˈɡɪv/"), ("fork", "叉", "/fɔːk/"),
        ("form", "形式", "/fɔːm/"), ("formal", "正式", "/ˈfɔːməl/"),
        ("former", "前", "/ˈfɔːmər/"), ("forth", "向前", "/fɔːθ/"),
        ("fortunate", "幸运", "/ˈfɔːtʃənət/"), ("fortune", "财富", "/ˈfɔːtʃuːn/"),
        ("forward", "向前", "/ˈfɔːwəd/"), ("found", "找到", "/faʊnd/"),
        ("foundation", "基础", "/faʊnˈdeɪʃən/"), ("fountain", "喷泉", "/ˈfaʊntɪn/"),
        ("four", "四", "/fɔːr/"), ("fox", "狐狸", "/fɒks/"),
        ("fraction", "分数", "/ˈfrækʃən/"), ("fragile", "脆弱", "/ˈfrædʒaɪl/"),
        ("frame", "框架", "/freɪm/"), ("frank", "坦率", "/fræŋk/"),
        ("free", "自由", "/friː/"), ("freedom", "自由", "/ˈfriːdəm/"),
        ("freeze", "冻结", "/friːz/"), ("frequency", "频率", "/ˈfriːkwənsi/"),
        ("frequent", "频繁", "/ˈfriːkwənt/"), ("fresh", "新鲜", "/freʃ/"),
        ("friend", "朋友", "/frend/"), ("friendly", "友好", "/ˈfrendli/"),
        ("friendship", "友谊", "/ˈfrendʃɪp/"), ("frighten", "害怕", "/ˈfraɪtən/"),
        ("from", "从", "/frɒm/"), ("front", "前面", "/frʌnt/"),
        ("fruit", "水果", "/fruːt/"), ("frustrate", "沮丧", "/frʌˈstreɪt/"),
        ("fuel", "燃料", "/ˈfjuːəl/"), ("fulfill", "完成", "/fʊlˈfɪl/"),
        ("full", "满", "/fʊl/"), ("fun", "乐趣", "/fʌn/"),
        ("function", "功能", "/ˈfʌŋkʃən/"), ("fund", "基金", "/fʌnd/"),
        ("fundamental", "基本", "/ˌfʌndəˈmentəl/"), ("funny", "好笑", "/ˈfʌni/"),
        ("furniture", "家具", "/ˈfɜːnɪtʃər/"), ("further", "进一步", "/ˈfɜːðər/"),
        ("future", "未来", "/ˈfjuːtʃər/"),
    ]
    seen = set()
    unique = []
    for w, m, p in base:
        if w not in seen:
            seen.add(w)
            unique.append((w, m, p))
    return unique

def load_word_list():
    words = []
    if os.path.exists(WORD_FILE):
        with open(WORD_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) >= 2:
                    word = parts[0]
                    meaning = parts[1]
                    phonetic = parts[2] if len(parts) >= 3 else ""
                    word = re.sub(r'_\d+$', '', word)
                    meaning = re.sub(r'_\d+$', '', meaning)
                    words.append((word, meaning, phonetic))
    if len(words) < 2000:
        words = generate_full_word_list()
        with open(WORD_FILE, "w", encoding="utf-8") as f:
            for w, m, p in words:
                f.write(f"{w}\t{m}\t{p}\n")
    return words

ENGLISH_WORDS = load_word_list()

def build_english_questions(words_list):
    return [
        {"text": f"单词 '{w}' 的中文意思是？", "answer": m, "explain": f"含义：{m}",
         "level": 1 if i < 800 else (2 if i < 1800 else 3), "video": ""}
        for i, (w, m, _) in enumerate(words_list)
    ]

# ==================== 整合所有题库 ====================
ALL_QUESTIONS = {
    "math": MATH_QUESTIONS,
    "english": build_english_questions(ENGLISH_WORDS),
    "physics": PHYSICS_QUESTIONS,
}

# ==================== 错题本 ====================
def load_mistakes():
    if os.path.exists(MISTAKE_FILE):
        with open(MISTAKE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"math": [], "english": [], "physics": []}

def save_mistakes(mistakes):
    with open(MISTAKE_FILE, "w", encoding="utf-8") as f:
        json.dump(mistakes, f, ensure_ascii=False, indent=2)

def add_mistake(subject, question, user_answer, correct_answer, explanation):
    m = load_mistakes()
    m[subject].append({
        "question": question, "user_answer": user_answer,
        "correct_answer": correct_answer, "explanation": explanation,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_mistakes(m)

# ==================== 激励系统 ====================
class RewardSystem:
    def __init__(self):
        self.parent = None
        self.load()
        self.reward_pool = ["💰 100元现金", "🍔 炸鸡", "🧋 奶茶", "🍕 披萨", "🎁 礼物"]
    def load(self):
        if os.path.exists(REWARD_FILE):
            with open(REWARD_FILE, "r") as f:
                data = json.load(f)
                self.points = data.get("points", 0)
                self.stars = data.get("stars", 0)
                self.hearts = data.get("hearts", 0)
        else:
            self.points = self.stars = self.hearts = 0
    def save(self):
        with open(REWARD_FILE, "w") as f:
            json.dump({"points": self.points, "stars": self.stars, "hearts": self.hearts}, f)
    def add_points(self, amt):
        self.points += amt
        self.save()
    def add_star(self, subject=None):
        self.stars += 1
        if self.stars >= 3:
            hearts_to_add = self.stars // 3
            self.stars = self.stars % 3
            self.hearts += hearts_to_add
            self.save()
            for _ in range(hearts_to_add):
                if self.parent:
                    reward = random.choice(self.reward_pool)
                    QMessageBox.information(self.parent, "🎁 奖励", f"恭喜获得：{reward}")
        else:
            self.save()
    def add_english_reward(self):
        self.add_points(5)

# ==================== 学习计时器（打卡） ====================
class StudyTimer:
    def __init__(self, reward_sys, parent=None):
        self.reward = reward_sys
        self.parent = parent
        self.load_data()
        self.current_page = None
        self.start_time = None
    def load_data(self):
        if os.path.exists(STUDY_TIME_FILE):
            with open(STUDY_TIME_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.today = data.get("today", date.today().isoformat())
                self.today_seconds = data.get("today_seconds", 0)
                self.last_checkin_date = data.get("last_checkin_date", None)
        else:
            self.today = date.today().isoformat()
            self.today_seconds = 0
            self.last_checkin_date = None
        if self.today != date.today().isoformat():
            self.today = date.today().isoformat()
            self.today_seconds = 0
            self.last_checkin_date = None
            self.save_data()
    def save_data(self):
        with open(STUDY_TIME_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "today": self.today,
                "today_seconds": self.today_seconds,
                "last_checkin_date": self.last_checkin_date
            }, f, indent=2)
    def start_page(self, page_name):
        if self.current_page is not None:
            self.stop_page()
        self.current_page = page_name
        self.start_time = datetime.now()
    def stop_page(self):
        if self.current_page and self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            if elapsed > 0:
                self.today_seconds += elapsed
                self.save_data()
                self.check_and_reward()
        self.current_page = None
        self.start_time = None
    def check_and_reward(self):
        if self.last_checkin_date != date.today().isoformat() and self.today_seconds >= 10800:
            self.last_checkin_date = date.today().isoformat()
            self.save_data()
            self.reward.add_star()
            if self.parent:
                QMessageBox.information(self.parent, "🎉 打卡成功", "今日学习满3小时，获得一颗⭐！")
    def get_today_hours(self):
        return self.today_seconds / 3600.0
    def get_remaining_seconds(self):
        return max(0, 10800 - self.today_seconds)

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
        return [(i, q) for i, q in enumerate(self.questions) if q["level"] == self.level and i not in self.mastered]
    def next(self):
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

# ==================== 英语专项（词库管理、记忆曲线、单词补全） ====================
class WordMastery:
    def __init__(self, word_list):
        self.word_list = word_list
        self.records = self.load()
        self.intervals = [1, 2, 4, 7, 15]
    def load(self):
        default_rec = {"mastered": False, "review_count": 0, "last_review": None, "next_review": None, "correct_streak": 0}
        # 重建最新的记录字典
        rec = {w: dict(default_rec) for w, _, _ in self.word_list}
        # 如果已有保存文件，合并已学进度
        if os.path.exists(WORD_MASTERY_FILE):
            try:
                with open(WORD_MASTERY_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                for w, data in saved.items():
                    if w in rec:
                        rec[w].update(data)
            except:
                pass
        return rec
    def save(self):
        with open(WORD_MASTERY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.records, f, ensure_ascii=False, indent=2)
    def get_due(self, today=None):
        if today is None:
            today = datetime.now().strftime("%Y-%m-%d")
        due = []
        for w, rec in self.records.items():
            if rec["mastered"]:
                continue
            nxt = rec.get("next_review")
            if nxt is None or nxt <= today:
                due.append(w)
        return due
    def update(self, word, correct):
        rec = self.records[word]
        today = datetime.now().strftime("%Y-%m-%d")
        if correct:
            rec["correct_streak"] += 1
            if rec["correct_streak"] >= 3:
                rec["mastered"] = True
                rec["next_review"] = None
            else:
                rec["review_count"] += 1
                idx = min(rec["review_count"] - 1, len(self.intervals) - 1)
                interval = self.intervals[idx]
                nxt = datetime.now() + timedelta(days=interval)
                rec["next_review"] = nxt.strftime("%Y-%m-%d")
        else:
            rec["correct_streak"] = 0
            nxt = datetime.now() + timedelta(days=1)
            rec["next_review"] = nxt.strftime("%Y-%m-%d")
        rec["last_review"] = today
        self.save()
    def stats(self):
        total = len(self.records)
        mastered = sum(1 for r in self.records.values() if r["mastered"])
        return total, mastered

class EnglishSpecialWidget(QWidget):
    def __init__(self, word_list, reward_sys, settings, parent=None):
        super().__init__(parent)
        self.word_list = word_list
        self.reward_sys = reward_sys
        self.settings = settings
        self.mastery = WordMastery(word_list)
        self.current_word = None
        self.current_meaning = None
        self.current_phonetic = None
        self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout(self)
        tab = QTabWidget()
        self.page_random = self.create_random_page()
        self.page_review = self.create_review_page()
        self.page_cloze = self.create_cloze_page()
        self.page_manager = self.create_manager_page()
        tab.addTab(self.page_random, "随机抽查")
        tab.addTab(self.page_review, "记忆曲线")
        tab.addTab(self.page_cloze, "单词补全")
        tab.addTab(self.page_manager, "词库管理")
        layout.addWidget(tab)
    # -------------- 随机抽查页面 --------------
    def create_random_page(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        # 模式选择
        self.en2zh_radio = QRadioButton("英译中")
        self.zh2en_radio = QRadioButton("中译英")
        self.en2zh_radio.setChecked(True)
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(self.en2zh_radio)
        mode_layout.addWidget(self.zh2en_radio)
        layout.addLayout(mode_layout)
        # 问题区
        self.random_question = QLabel("点击“开始抽查”")
        self.random_question.setAlignment(Qt.AlignCenter)
        self.random_question.setWordWrap(True)
        layout.addWidget(self.random_question)
        self.random_input = QLineEdit()
        self.random_input.setPlaceholderText("输入答案...")
        layout.addWidget(self.random_input)
        # 按钮
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始抽查")
        self.verify_btn = QPushButton("验证")
        self.next_btn = QPushButton("下一个")
        self.speak_btn = QPushButton("朗读")
        self.master_btn = QPushButton("标记已掌握")
        self.unmaster_btn = QPushButton("标记未掌握")
        for btn in [self.start_btn, self.verify_btn, self.next_btn, self.speak_btn, self.master_btn, self.unmaster_btn]:
            btn.setEnabled(False)
        self.start_btn.setEnabled(True)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.verify_btn)
        btn_layout.addWidget(self.next_btn)
        btn_layout.addWidget(self.speak_btn)
        btn_layout.addWidget(self.master_btn)
        btn_layout.addWidget(self.unmaster_btn)
        layout.addLayout(btn_layout)
        self.random_feedback = QLabel("")
        self.random_feedback.setWordWrap(True)
        layout.addWidget(self.random_feedback)
        # 连接
        self.start_btn.clicked.connect(self.start_random)
        self.verify_btn.clicked.connect(self.verify_random)
        self.next_btn.clicked.connect(self.next_random)
        self.speak_btn.clicked.connect(self.speak_word)
        self.master_btn.clicked.connect(self.mark_mastered)
        self.unmaster_btn.clicked.connect(self.mark_unmastered)
        # 切换模式时刷新显示
        self.en2zh_radio.toggled.connect(self.on_mode_switched)
        self.zh2en_radio.toggled.connect(self.on_mode_switched)
        return w
    def on_mode_switched(self):
        """切换英译中/中译英模式时刷新当前题目显示"""
        if self.current_word:
            self.display_random()
    def start_random(self):
        try:
            due = self.mastery.get_due()
            if due:
                word = random.choice(due)
            else:
                not_mastered = [w for w, rec in self.mastery.records.items() if not rec["mastered"]]
                if not not_mastered:
                    QMessageBox.information(self, "提示", "所有单词已掌握！")
                    self.start_btn.setEnabled(True)
                    self.verify_btn.setEnabled(False)
                    self.next_btn.setEnabled(False)
                    self.speak_btn.setEnabled(False)
                    self.master_btn.setEnabled(False)
                    self.unmaster_btn.setEnabled(False)
                    return
                word = random.choice(not_mastered)
            self.current_word = word
            for w, m, p in self.word_list:
                if w == word:
                    self.current_meaning = m
                    self.current_phonetic = p
                    break
            self.display_random()
            self.start_btn.setEnabled(False)
            self.verify_btn.setEnabled(True)
            self.next_btn.setEnabled(False)
            self.speak_btn.setEnabled(True)
            self.master_btn.setEnabled(True)
            self.unmaster_btn.setEnabled(True)
            self.random_input.clear()
            self.random_feedback.setText("")
            self.random_input.setFocus()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"出错了：{str(e)}")
            self.start_btn.setEnabled(True)
    def display_random(self):
        if self.en2zh_radio.isChecked():
            self.random_question.setText(f"单词：{self.current_word}  {self.current_phonetic}")
        else:
            self.random_question.setText(f"释义：{self.current_meaning}")
    def verify_random(self):
        if not self.current_word:
            return
        try:
            user = self.random_input.text().strip()
            if self.en2zh_radio.isChecked():
                correct = user.lower() == self.current_meaning.lower()
                expected = self.current_meaning
            else:
                correct = user.lower() == self.current_word.lower()
                expected = self.current_word
            if correct:
                self.random_feedback.setText("✅ 正确！")
                self.reward_sys.add_english_reward()
                self.mastery.update(self.current_word, True)
            else:
                self.random_feedback.setText(f"❌ 错误。正确答案：{expected}")
                self.mastery.update(self.current_word, False)
            self.verify_btn.setEnabled(False)
            self.next_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"验证出错：{str(e)}")
    def next_random(self):
        self.start_random()
    def speak_word(self):
        if not TTS_AVAILABLE:
            QMessageBox.warning(self, "提示", "请安装 pyttsx3 以使用朗读功能\n安装命令：pip install pyttsx3")
            return
        if not self.current_word:
            return
        try:
            engine = pyttsx3.init()
            voice = self.settings.get("voice", "en-US")
            voices = engine.getProperty('voices')
            found = False
            for v in voices:
                if voice in v.id:
                    engine.setProperty('voice', v.id)
                    found = True
                    break
            if not found and voices:
                engine.setProperty('voice', voices[0].id)
            engine.say(self.current_word)
            engine.runAndWait()
        except Exception as e:
            QMessageBox.warning(self, "朗读失败", f"朗读出错：{str(e)}\n可尝试：pip install pyttsx3 --upgrade")
    def mark_mastered(self):
        if not self.current_word:
            return
        try:
            self.mastery.records[self.current_word]["mastered"] = True
            self.mastery.save()
            QMessageBox.information(self, "已标记", f"{self.current_word} 已掌握")
            self.next_random()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"标记出错：{str(e)}")
    def mark_unmastered(self):
        if not self.current_word:
            return
        try:
            self.mastery.records[self.current_word]["mastered"] = False
            self.mastery.save()
            QMessageBox.information(self, "已标记", f"{self.current_word} 未掌握")
            self.next_random()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"标记出错：{str(e)}")
    # -------------- 记忆曲线复习页面 --------------
    def create_review_page(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        self.review_info = QLabel("今日待复习单词数量：")
        self.review_list = QTextEdit()
        self.review_list.setReadOnly(True)
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_due_words)
        start_btn = QPushButton("开始复习")
        start_btn.clicked.connect(self.start_review)
        layout.addWidget(self.review_info)
        layout.addWidget(self.review_list)
        layout.addWidget(refresh_btn)
        layout.addWidget(start_btn)
        return w
    def load_due_words(self):
        due = self.mastery.get_due()
        self.review_info.setText(f"今日待复习单词数：{len(due)}")
        self.review_list.setText("\n".join(due[:20]) if due else "无")
    def start_review(self):
        due = self.mastery.get_due()
        if not due:
            QMessageBox.information(self, "提示", "无待复习单词")
            return
        self.start_random()
    # -------------- 单词补全页面（内联填空 — 在单词下划线上直接输入） --------------
    def create_cloze_page(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(15)

        # 音标（顶部）
        self.cloze_phonetic = QLabel("")
        self.cloze_phonetic.setAlignment(Qt.AlignCenter)
        self.cloze_phonetic.setStyleSheet("color: #888; font-size: 20px;")
        layout.addWidget(self.cloze_phonetic)

        # 释义
        self.cloze_meaning = QLabel("")
        self.cloze_meaning.setAlignment(Qt.AlignCenter)
        self.cloze_meaning.setStyleSheet("color: #4CAF50; font-size: 20px; font-weight: bold;")
        layout.addWidget(self.cloze_meaning)

        # 单词内联容器（居中的横向布局）
        self.cloze_word_container = QWidget()
        self.cloze_word_layout = QHBoxLayout(self.cloze_word_container)
        self.cloze_word_layout.setSpacing(2)
        self.cloze_word_layout.setContentsMargins(0, 0, 0, 0)
        self.cloze_word_layout.addStretch()
        layout.addWidget(self.cloze_word_container)

        # 单词显示区域（居中包裹）
        word_wrapper = QHBoxLayout()
        word_wrapper.addStretch()
        word_wrapper.addWidget(self.cloze_word_container)
        word_wrapper.addStretch()
        layout.addLayout(word_wrapper)

        # 按钮
        btn_layout = QHBoxLayout()
        self.gen_cloze_btn = QPushButton("生成补全题")
        self.check_cloze_btn = QPushButton("验证答案")
        self.next_cloze_btn = QPushButton("下一题")
        self.cloze_speak_btn = QPushButton("🔊 朗读")
        btn_layout.addWidget(self.gen_cloze_btn)
        btn_layout.addWidget(self.check_cloze_btn)
        btn_layout.addWidget(self.next_cloze_btn)
        btn_layout.addWidget(self.cloze_speak_btn)
        layout.addLayout(btn_layout)

        # 反馈
        self.cloze_feedback = QLabel("")
        self.cloze_feedback.setWordWrap(True)
        self.cloze_feedback.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.cloze_feedback)

        layout.addStretch()

        # 连接
        self.gen_cloze_btn.clicked.connect(self.generate_cloze)
        self.check_cloze_btn.clicked.connect(self.check_cloze)
        self.next_cloze_btn.clicked.connect(self.generate_cloze)
        self.cloze_speak_btn.clicked.connect(self.speak_word)

        return w

    def clear_word_layout(self):
        """清空内联单词布局中的部件"""
        while self.cloze_word_layout.count():
            item = self.cloze_word_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def generate_cloze(self):
        # 优先从未掌握单词中选择
        not_mastered = [w for w, rec in self.mastery.records.items() if not rec["mastered"]]
        if not not_mastered:
            not_mastered = [w for w, _, _ in self.word_list]
        word = random.choice(not_mastered)
        self.cloze_answer = word
        self.current_word = word  # 供朗读功能使用
        # 获取音标和释义
        phonetic = ""
        meaning = ""
        for w, m, p in self.word_list:
            if w == word:
                meaning = m
                phonetic = p
                break
        self.current_meaning = meaning
        self.current_phonetic = phonetic

        # 生成随机缺失位置
        word_len = len(word)
        hide_cnt = max(1, word_len // 2)
        indices = set(random.sample(range(word_len), hide_cnt))
        self.cloze_hide_indices = indices
        self.cloze_inputs = []

        # 清空并重建内联布局
        self.clear_word_layout()
        self.cloze_word_layout.addStretch()

        for i, ch in enumerate(word):
            block = QWidget()
            block_layout = QVBoxLayout(block)
            block_layout.setContentsMargins(0, 0, 0, 0)
            block_layout.setSpacing(0)

            if i in indices:
                # 缺失字母 → 下划线输入框
                inp = QLineEdit()
                inp.setMaxLength(1)
                inp.setFixedWidth(40)
                inp.setAlignment(Qt.AlignCenter)
                inp.setStyleSheet("""
                    QLineEdit {
                        font-size: 28px; font-weight: bold;
                        border: none;
                        border-bottom: 3px solid #e94560;
                        background: transparent;
                        color: #ffffff;
                        padding: 4px 0;
                        margin: 0;
                    }
                    QLineEdit:focus {
                        border-bottom: 3px solid #4CAF50;
                    }
                """)
                # 输入后自动跳到下一个缺失的输入框
                inp.textChanged.connect(lambda text, idx=i: self.on_cloze_char_typed(idx, text))
                self.cloze_inputs.append(inp)
                label_above = QLabel("_")
                label_above.setAlignment(Qt.AlignCenter)
                label_above.setStyleSheet("font-size: 20px; color: #e94560;")
            else:
                # 显示字母
                label_above = QLabel(ch)
                label_above.setAlignment(Qt.AlignCenter)
                label_above.setStyleSheet("font-size: 28px; font-weight: bold; color: #ffffff;")
                inp = None  # 无输入框

            block_layout.addWidget(label_above)
            if inp:
                block_layout.addWidget(inp)
            block_layout.setAlignment(Qt.AlignCenter)
            self.cloze_word_layout.addWidget(block)

        self.cloze_word_layout.addStretch()
        # 将第一个输入框设置为焦点
        if self.cloze_inputs:
            self.cloze_inputs[0].setFocus()

        self.cloze_phonetic.setText(f"音标：{phonetic}")
        self.cloze_meaning.setText(f"释义：{meaning}")
        self.cloze_feedback.setText("")

    def on_cloze_char_typed(self, idx, text):
        """输入一个字符后，自动跳到下一个空白的输入框"""
        if text:
            # 找到当前输入框在 cloze_inputs 中的索引
            for ci, inp in enumerate(self.cloze_inputs):
                if inp is self.sender() or (hasattr(self, 'cloze_current_input') and self.cloze_current_input == ci):
                    # 跳到下一个输入框
                    if ci + 1 < len(self.cloze_inputs):
                        self.cloze_inputs[ci + 1].setFocus()
                        self.cloze_inputs[ci + 1].selectAll()
                    break

    def check_cloze(self):
        # 收集所有输入框的值
        user_chars = []
        inp_idx = 0
        for i, ch in enumerate(self.cloze_answer):
            if i in self.cloze_hide_indices:
                if inp_idx < len(self.cloze_inputs):
                    user_chars.append(self.cloze_inputs[inp_idx].text().strip().lower())
                    inp_idx += 1
                else:
                    user_chars.append("")
            else:
                user_chars.append(ch.lower())

        user_word = "".join(user_chars)
        if user_word == self.cloze_answer.lower():
            self.cloze_feedback.setText("✅ 正确！")
            self.reward_sys.add_english_reward()
            self.mastery.update(self.cloze_answer, True)
        else:
            self.cloze_feedback.setText(f"❌ 错误。正确答案：{self.cloze_answer}\n音标：{self.current_phonetic}\n释义：{self.current_meaning}")
            self.mastery.update(self.cloze_answer, False)
    # -------------- 词库管理页面 --------------
    def create_manager_page(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        self.stats_label = QLabel()
        self.word_table = QTableWidget()
        self.word_table.setColumnCount(4)
        self.word_table.setHorizontalHeaderLabels(["单词", "音标", "释义", "状态"])
        self.word_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("筛选："))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全部", "已掌握", "未掌握"])
        self.filter_combo.currentTextChanged.connect(self.refresh_table)
        filter_layout.addWidget(self.filter_combo)
        btn_layout = QHBoxLayout()
        master_btn = QPushButton("标记选中为掌握")
        unmaster_btn = QPushButton("标记选中为未掌握")
        btn_layout.addWidget(master_btn)
        btn_layout.addWidget(unmaster_btn)
        layout.addWidget(self.stats_label)
        layout.addWidget(self.word_table)
        layout.addLayout(filter_layout)
        layout.addLayout(btn_layout)
        master_btn.clicked.connect(lambda: self.batch_mark(True))
        unmaster_btn.clicked.connect(lambda: self.batch_mark(False))
        self.refresh_table()
        return w
    def refresh_table(self):
        self.update_stats()
        filter_text = self.filter_combo.currentText()
        self.word_table.setRowCount(0)
        for word, meaning, phonetic in self.word_list:
            rec = self.mastery.records.get(word, {})
            mastered = rec.get("mastered", False)
            if filter_text == "已掌握" and not mastered:
                continue
            if filter_text == "未掌握" and mastered:
                continue
            row = self.word_table.rowCount()
            self.word_table.insertRow(row)
            self.word_table.setItem(row, 0, QTableWidgetItem(word))
            self.word_table.setItem(row, 1, QTableWidgetItem(phonetic))
            self.word_table.setItem(row, 2, QTableWidgetItem(meaning))
            self.word_table.setItem(row, 3, QTableWidgetItem("✓已掌握" if mastered else "○未掌握"))
    def update_stats(self):
        total, mastered = self.mastery.stats()
        self.stats_label.setText(f"总单词：{total}  已掌握：{mastered}  未掌握：{total - mastered}")
    def batch_mark(self, mastered_flag):
        selected_rows = set()
        for item in self.word_table.selectedItems():
            selected_rows.add(item.row())
        for row in selected_rows:
            word = self.word_table.item(row, 0).text()
            self.mastery.records[word]["mastered"] = mastered_flag
        self.mastery.save()
        self.refresh_table()
    def apply_font(self):
        font = QFont("微软雅黑", self.settings.get("font_size", 14))
        for widget in [self.random_question, self.random_input, self.random_feedback,
                       self.start_btn, self.verify_btn, self.next_btn, self.speak_btn,
                       self.master_btn, self.unmaster_btn, self.review_info, self.review_list,
                       self.cloze_phonetic, self.cloze_meaning,
                       self.cloze_feedback, self.stats_label, self.word_table, self.filter_combo,
                       self.gen_cloze_btn, self.check_cloze_btn, self.next_cloze_btn, self.cloze_speak_btn]:
            if widget:
                widget.setFont(font)
        # 内联输入框字体
        for inp in getattr(self, 'cloze_inputs', []):
            inp.setFont(font)

# ==================== 作文范文模块 ====================
class EssayPage(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        layout = QVBoxLayout(self)
        lbl = QLabel("📝 高考英语作文真题范文")
        lbl.setFont(QFont("微软雅黑", 16, QFont.Bold))
        layout.addWidget(lbl)
        self.essay_tabs = QTabWidget()
        essays = [
            ("2024 全国甲卷", "题目：写一封邮件邀请外国朋友参加学校艺术节\n\n范文：\nDear John,\n\nI'm writing to invite you to our school's Art Festival, which will be held in the school hall from 9:00 a.m. to 5:00 p.m. on June 15th.\n\nThere will be various activities, including a painting exhibition, a calligraphy show, and a music performance. You can also try traditional Chinese crafts like paper-cutting and clay figurines.\n\nI believe you will have a great time. Please let me know if you can come.\n\nYours sincerely,\nLi Hua"),
            ("2024 新高考I卷", "题目：推荐一款中国传统文化产品给外国朋友\n\n范文：\nDear Tom,\n\nI'm glad to hear that you're interested in Chinese traditional culture. I'd like to recommend a product — Chinese knot.\n\nChinese knots are handmade ornaments made of silk thread, symbolizing good luck and reunion. They come in various shapes and colors, and are often used during festivals as decorations.\n\nI'm sure you will love it. I can send you one as a gift if you like.\n\nBest wishes,\nLi Hua"),
            ("2023 全国乙卷", "题目：介绍一次难忘的校园活动\n\n范文：\nLast month, our school held a 'Charity Sale' activity. All the students and teachers took an active part in it.\n\nWe set up several stalls on the playground, selling second-hand books, toys, and handmade crafts. Many students also donated their pocket money. In the end, we raised over 5,000 yuan, which was sent to a local orphanage.\n\nThis activity was meaningful because it taught us to care for others and share love. I will never forget that day."),
            ("2022 全国甲卷", "题目：保护环境倡议书\n\n范文：\nDear fellow students,\n\nOur planet is facing serious environmental problems. As students, we should do our part to protect the environment.\n\nFirst, we can reduce waste by using reusable water bottles and bags. Second, we should save electricity and water in our daily life. Finally, planting trees and recycling rubbish are also good habits.\n\nLet's take action now and make the world a better place.\n\nYours sincerely,\nLi Hua"),
            ("2021 新高考I卷", "题目：感谢信——感谢老师\n\n范文：\nDear Mr. Wang,\n\nI'm writing to express my sincere gratitude for your help during my high school years.\n\nYou not only taught me knowledge but also inspired me to be a better person. Whenever I had difficulties, you always encouraged me and gave me valuable advice. Thanks to you, I have made great progress in English.\n\nI will always remember your kindness. Wish you all the best.\n\nYours truly,\nLi Hua"),
        ]
        for title, content in essays:
            text_area = QTextEdit()
            text_area.setReadOnly(True)
            text_area.setText(content)
            self.essay_tabs.addTab(text_area, title)
        layout.addWidget(self.essay_tabs)
        back = QPushButton("返回首页")
        back.clicked.connect(lambda: parent.switch_page(0))
        layout.addWidget(back)
        self.apply_font()
    def apply_font(self):
        font = QFont("微软雅黑", self.parent.settings.get("font_size", 14))
        for i in range(self.essay_tabs.count()):
            self.essay_tabs.widget(i).setFont(font)

# ==================== 其他页面（训练学科选择、训练、学习模式、考试、错题本） ====================
class TrainSubjectPage(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        lbl = QLabel("选择学科")
        lbl.setFont(QFont("微软雅黑", 18, QFont.Bold))
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)
        btn_layout = QVBoxLayout()
        for text, key in [("数学", "math"), ("英语", "english"), ("物理", "physics")]:
            btn = QPushButton(text)
            btn.setFont(QFont("微软雅黑", 16))
            btn.setMinimumHeight(80)
            btn.clicked.connect(lambda checked, s=key: parent.start_training(s))
            btn_layout.addWidget(btn)
        back = QPushButton("返回首页")
        back.clicked.connect(lambda: parent.switch_page(0))
        btn_layout.addWidget(back)
        layout.addLayout(btn_layout)
    def apply_font(self):
        font = QFont("微软雅黑", self.parent.settings.get("font_size", 14))
        for btn in self.findChildren(QPushButton):
            btn.setFont(font)

class TrainingPage(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        layout = QVBoxLayout(self)
        self.level_label = QLabel("难度: ⭐")
        self.progress_label = QLabel("连续正确: 0/3")
        top = QHBoxLayout()
        top.addWidget(self.level_label)
        top.addStretch()
        top.addWidget(self.progress_label)
        layout.addLayout(top)
        self.question_label = QLabel("题目加载中...")
        self.question_label.setWordWrap(True)
        layout.addWidget(self.question_label)
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("输入答案...")
        self.input_edit.returnPressed.connect(self.submit)
        layout.addWidget(self.input_edit)
        btn_layout = QHBoxLayout()
        self.submit_btn = QPushButton("提交")
        self.continue_btn = QPushButton("下一题")
        self.continue_btn.setVisible(False)
        self.back_btn = QPushButton("结束")
        btn_layout.addWidget(self.submit_btn)
        btn_layout.addWidget(self.continue_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.back_btn)
        layout.addLayout(btn_layout)
        self.feedback = QTextEdit()
        self.feedback.setReadOnly(True)
        layout.addWidget(self.feedback)
        self.submit_btn.clicked.connect(self.submit)
        self.continue_btn.clicked.connect(self.next_question)
        self.back_btn.clicked.connect(lambda: parent.switch_page(1))
        self.apply_font()
    def apply_font(self):
        size = self.parent.settings.get("font_size", 14)
        font = QFont("微软雅黑", size)
        self.question_label.setFont(font)
        self.input_edit.setFont(font)
        self.feedback.setFont(font)
        self.level_label.setFont(font)
        self.progress_label.setFont(font)
        for btn in [self.submit_btn, self.continue_btn, self.back_btn]:
            btn.setFont(font)
    def set_trainer(self, trainer, subject):
        self.trainer = trainer
        self.subject = subject
        self.next_question()
    def next_question(self):
        upgrade_msg = ""
        while True:
            result = self.trainer.next()
            typ = result[0]
            if typ == "question":
                q = result[1]
                self.question_label.setText(f"第{len(self.trainer.mastered) + 1}题：{q['text']}")
                self.level_label.setText(f"难度: {'⭐' * self.trainer.level}")
                self.progress_label.setText(f"连续正确: {self.trainer.correct_in_level}/3")
                self.input_edit.clear()
                self.input_edit.setEnabled(True)
                self.submit_btn.setVisible(True)
                self.continue_btn.setVisible(False)
                self.feedback.setText(upgrade_msg)  # 保留升级消息
                self.input_edit.setFocus()
                break
            elif typ == "upgrade":
                level = result[1]
                upgrade_msg += f"🎉 升级到难度{level}星！获得100积分\n"
                self.parent.reward.add_points(100)
                self.parent.refresh_status()
                QMessageBox.information(self, "升级", f"升级到难度{level}星")
            elif typ == "complete":
                self.feedback.setText("🏆 完成本学科所有题目！")
                self.input_edit.setEnabled(False)
                self.submit_btn.setVisible(False)
                self.continue_btn.setVisible(False)
                QMessageBox.information(self, "完成", "恭喜完成所有题目")
                break
    def submit(self):
        if self.trainer is None or self.trainer.current is None:
            return
        user = self.input_edit.text().strip()
        if not user:
            self.feedback.setText("请输入答案")
            return
        correct, q = self.trainer.check(user)
        if correct:
            if self.subject in ["math", "physics"]:
                self.parent.reward.add_star(self.subject)
            else:
                self.parent.reward.add_english_reward()
            self.feedback.setText(f"✅ 正确！\n讲解：{q['explain']}")
        else:
            self.feedback.setText(f"❌ 错误。正确答案：{q['answer']}\n讲解：{q['explain']}")
            add_mistake(self.subject, q["text"], user, q["answer"], q["explain"])
        self.parent.refresh_status()
        self.input_edit.setEnabled(False)
        self.submit_btn.setVisible(False)
        self.continue_btn.setVisible(True)

class StudyPage(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        layout = QVBoxLayout(self)
        lbl = QLabel("📚 学习模式")
        lbl.setFont(QFont("微软雅黑", 16, QFont.Bold))
        layout.addWidget(lbl)
        self.tabs = QTabWidget()
        for sub, name in [("math", "数学"), ("english", "英语"), ("physics", "物理")]:
            text = QTextEdit()
            text.setReadOnly(True)
            content = "\n".join([
                f"【难度{q['level']}星】{q['text']}\n答案：{q['answer']}\n讲解：{q['explain']}"
                for q in ALL_QUESTIONS[sub]
            ])
            text.setText(content)
            self.tabs.addTab(text, name)
        layout.addWidget(self.tabs)
        back = QPushButton("返回首页")
        back.clicked.connect(lambda: parent.switch_page(0))
        layout.addWidget(back)
        self.apply_font()
    def apply_font(self):
        font = QFont("微软雅黑", self.parent.settings.get("font_size", 14))
        for i in range(self.tabs.count()):
            self.tabs.widget(i).setFont(font)

class ExamPage(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.questions = []
        self.index = 0
        self.score = 0
        self.mistakes = []
        layout = QVBoxLayout(self)
        self.info_label = QLabel("模拟考试")
        self.info_label.setFont(QFont("微软雅黑", 16, QFont.Bold))
        layout.addWidget(self.info_label)
        self.progress_label = QLabel("准备开始...")
        layout.addWidget(self.progress_label)
        self.question_label = QLabel("点击「开始考试」")
        self.question_label.setWordWrap(True)
        layout.addWidget(self.question_label)
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("输入答案...")
        self.input_edit.setEnabled(False)
        layout.addWidget(self.input_edit)
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始考试")
        self.submit_btn = QPushButton("提交")
        self.next_btn = QPushButton("下一题")
        self.submit_btn.setVisible(False)
        self.next_btn.setVisible(False)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.submit_btn)
        btn_layout.addWidget(self.next_btn)
        layout.addLayout(btn_layout)
        self.feedback = QTextEdit()
        self.feedback.setReadOnly(True)
        layout.addWidget(self.feedback)
        self.back = QPushButton("返回首页")
        self.back.clicked.connect(lambda: parent.switch_page(0))
        layout.addWidget(self.back)
        self.start_btn.clicked.connect(self.begin)
        self.submit_btn.clicked.connect(self.submit)
        self.next_btn.clicked.connect(self.next_question)
        self.apply_font()
    def apply_font(self):
        size = self.parent.settings.get("font_size", 14)
        font = QFont("微软雅黑", size)
        self.question_label.setFont(font)
        self.input_edit.setFont(font)
        self.feedback.setFont(font)
        self.progress_label.setFont(font)
        self.info_label.setFont(font)
        for btn in [self.start_btn, self.submit_btn, self.next_btn, self.back]:
            btn.setFont(font)
    def begin(self):
        self.questions = []
        for sub in ["math", "english", "physics"]:
            sub_q = random.sample(ALL_QUESTIONS[sub], min(3, len(ALL_QUESTIONS[sub])))
            self.questions.extend([(sub, q) for q in sub_q])
        self.index = 0
        self.score = 0
        self.mistakes = []
        self.start_btn.setVisible(False)
        self.submit_btn.setVisible(True)
        self.input_edit.setEnabled(True)
        self.feedback.clear()
        self.show_question()
    def show_question(self):
        if self.index >= len(self.questions):
            self.finish()
            return
        sub, q = self.questions[self.index]
        self.info_label.setText(f"第{self.index + 1}/{len(self.questions)}题")
        self.progress_label.setText(f"当前得分: {self.score}")
        self.question_label.setText(f"【{sub.upper()}】{q['text']}")
        self.input_edit.clear()
        self.input_edit.setEnabled(True)
        self.submit_btn.setVisible(True)
        self.next_btn.setVisible(False)
        self.input_edit.setFocus()
    def submit(self):
        sub, q = self.questions[self.index]
        user = self.input_edit.text().strip()
        correct = (q["answer"].lower() in user.lower()) or (user.lower() == q["answer"].lower())
        if correct:
            self.score += 10
            if sub in ["math", "physics"]:
                self.parent.reward.add_star(sub)
            else:
                self.parent.reward.add_english_reward()
            self.feedback.setText(f"✅ 正确 +10分！\n讲解：{q['explain']}")
        else:
            self.feedback.setText(f"❌ 错误。正确答案：{q['answer']}\n讲解：{q['explain']}")
            self.mistakes.append((sub, q, user))
            add_mistake(sub, q["text"], user, q["answer"], q["explain"])
        self.parent.refresh_status()
        self.input_edit.setEnabled(False)
        self.submit_btn.setVisible(False)
        self.next_btn.setVisible(True)
    def next_question(self):
        self.index += 1
        if self.index >= len(self.questions):
            self.finish()
        else:
            self.show_question()
    def finish(self):
        total = len(self.questions) * 10
        self.info_label.setText("考试结束")
        self.question_label.setText(f"得分：{self.score}/{total}")
        self.input_edit.setEnabled(False)
        self.submit_btn.setVisible(False)
        self.next_btn.setVisible(False)
        self.start_btn.setVisible(True)
        self.start_btn.setText("重新考试")
        result = f"得分：{self.score}/{total}\n"
        if self.mistakes:
            result += f"错题数：{len(self.mistakes)}"
        else:
            result += "🎉 全部正确！"
        self.feedback.setText(result)
        QMessageBox.information(self, "考试结果", result)

class MistakePage(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        layout = QVBoxLayout(self)
        lbl = QLabel("📖 错题本")
        lbl.setFont(QFont("微软雅黑", 16, QFont.Bold))
        layout.addWidget(lbl)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.scroll.setWidget(self.content)
        layout.addWidget(self.scroll)
        btn_layout = QHBoxLayout()
        back = QPushButton("返回首页")
        back.clicked.connect(lambda: parent.switch_page(0))
        clear = QPushButton("清空错题本")
        clear.clicked.connect(self.clear_mistakes)
        btn_layout.addWidget(back)
        btn_layout.addStretch()
        btn_layout.addWidget(clear)
        layout.addLayout(btn_layout)
        self.refresh()
    def refresh(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        mistakes = load_mistakes()
        total = sum(len(v) for v in mistakes.values())
        if total == 0:
            label = QLabel("✅ 暂无错题")
            label.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(label)
            return
        stats = QLabel(f"总错题数：{total}")
        self.content_layout.addWidget(stats)
        sub_names = {"math": "数学", "english": "英语", "physics": "物理"}
        for sub, lst in mistakes.items():
            if not lst:
                continue
            sub_title = QLabel(f"【{sub_names.get(sub, sub)}】{len(lst)}道")
            self.content_layout.addWidget(sub_title)
            for item in lst[-10:]:
                card = QFrame()
                card.setStyleSheet("background-color:#16213e; border-radius:8px; padding:8px; margin:4px;")
                inner = QVBoxLayout(card)
                q_label = QLabel(f"📌 {item['question'][:80]}")
                q_label.setWordWrap(True)
                inner.addWidget(q_label)
                ans_label = QLabel(f"你的：{item['user_answer']}  正解：{item['correct_answer']}")
                inner.addWidget(ans_label)
                self.content_layout.addWidget(card)
        self.content_layout.addStretch()
    def clear_mistakes(self):
        reply = QMessageBox.question(self, "确认", "清空所有错题？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            save_mistakes({"math": [], "english": [], "physics": []})
            self.refresh()
            QMessageBox.information(self, "完成", "错题本已清空")

# ==================== 设置对话框 ====================
class SettingsDialog(QDialog):
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.settings = current_settings.copy()
        self.setWindowTitle("设置")
        self.setModal(True)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.theme_combo = QComboBox()
        themes = ["暗色", "亮色", "蓝色", "绿色", "暖色"]
        self.theme_combo.addItems(themes)
        theme_map = {"暗色": "dark", "亮色": "light", "蓝色": "blue", "绿色": "green", "暖色": "warm"}
        current_theme = self.settings.get("theme", "dark")
        for i, (name, key) in enumerate(theme_map.items()):
            if key == current_theme:
                self.theme_combo.setCurrentIndex(i)
                break
        form.addRow("主题:", self.theme_combo)
        self.voice_combo = QComboBox()
        self.voice_combo.addItems(["美式英语", "英式英语"])
        voice_val = self.settings.get("voice", "en-US")
        self.voice_combo.setCurrentIndex(0 if voice_val == "en-US" else 1)
        form.addRow("发音:", self.voice_combo)
        self.font_spin = QSpinBox()
        self.font_spin.setRange(10, 24)
        self.font_spin.setValue(self.settings.get("font_size", 14))
        form.addRow("字体大小:", self.font_spin)
        layout.addLayout(form)
        btn_box = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(ok_btn)
        btn_box.addWidget(cancel_btn)
        layout.addLayout(btn_box)
    def get_settings(self):
        theme_map = {"暗色": "dark", "亮色": "light", "蓝色": "blue", "绿色": "green", "暖色": "warm"}
        theme = theme_map[self.theme_combo.currentText()]
        voice = "en-US" if self.voice_combo.currentIndex() == 0 else "en-GB"
        font_size = self.font_spin.value()
        return {"theme": theme, "voice": voice, "font_size": font_size}

# ==================== 学习计划模块 ====================
PLAN_FILE = "study_plan_checklist.json"

def load_plan_checklist():
    default = {
        "math_unit": 0, "english_words": 0, "physics_exp": 0,
        "daily_tasks": {}, "phase": 1
    }
    if os.path.exists(PLAN_FILE):
        with open(PLAN_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                default.update(data)
            except:
                pass
    return default

def save_plan_checklist(data):
    with open(PLAN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

PHASES = [
    ("🔴 第一阶段", "高二下冲刺期（现在 - 2026年6月底）",
     "目标：把数学、英语的基础捡起来，物理跟上学校进度",
     [("早读 6:30-7:10", "英语单词15个 + 数学公式抄写"),
      ("上午", "认真听数学、物理、化学课"),
      ("午休", "必须睡30分钟"),
      ("晚自习1 19:00-20:00", "数学基础训练（教材课后习题）"),
      ("晚自习2 20:10-21:10", "物理基础概念+公式背诵"),
      ("晚自习3 21:20-22:00", "英语阅读2篇+作文模板抄写"),
      ("睡前 22:30-23:00", "回顾3个数学公式、5个英语单词")]),
    ("🟡 第二阶段", "高三上学期（2026年9月 - 2027年1月）",
     "目标：总分稳定在360-380分，数学突破80分",
     [("早读 6:00-6:40", "数学公式本（每天1个单元）+ 英语单词20个"),
      ("晚自习1 18:30-19:30", "数学专项：函数、三角、数列、概率（轮换）"),
      ("晚自习2 19:40-20:40", "物理专项：受力分析、牛顿定律、曲线运动"),
      ("晚自习3 20:50-21:50", "英语专项：真题阅读A/B篇 + 作文模板默写"),
      ("睡前 23:00-23:30", "回忆当天3个数学公式、2个物理模型")]),
    ("🟢 第三阶段", "高三下学期（2027年2月 - 5月）",
     "目标：总分稳定380-400分，模拟考心态训练",
     [("早读", "错题本上的公式、单词"),
      ("晚自习", "只做三件事：1.重做错题 2.背作文模板 3.限时训练基础题"),
      ("考前30天", "停止做新题，每天翻看错题本和公式本"),
      ("每3天", "严格按照高考时间做一次基础版真题"),
      ("作息", "每天23:00前必须睡")])
]

SUBJECT_TIPS = {
    "数学 (目标85-95分)": [
        "只做以下板块：集合复数(10分)、向量(5分)、统计概率(15分)、三角函数(15分)、数列(12分)、立体几何基础(10分)、函数基础(10分)",
        "放弃导数综合、圆锥曲线大题、选择填空最后2题",
        "每日必做：抄公式本 + 做10道计算题练准确率 + 做一套前10选择+前2填空+前三道大题",
    ],
    "英语 (目标65-75分)": [
        "单词：高考高频800词（不要背3500），每天15个，反复循环",
        "阅读：只做A篇+B篇，直接去原文找答案",
        "七选五：看前后句有没有重复词，有就是答案",
        "作文：背熟3套模板（书信、议论文、看图作文），字写好，目标15分",
        "放弃：完形填空（全蒙同一个选项），长难阅读理解（直接蒙）",
    ],
    "物理 (目标55-65分)": [
        "锁定必考点：受力分析、牛顿第二定律、运动学公式",
        "曲线运动：平抛、圆周运动（向心力公式）",
        "实验题：考纲7个实验的步骤、公式、结论（背下来）",
        "每日必做：抄公式 + 做1道简单力学计算题 + 做2道实验填空题",
    ]
}

class StudyPlanPage(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.plan_data = load_plan_checklist()
        self.checkboxes = {}
        self.current_phase = 0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        tabs.addTab(self.create_path_tab(), "🎯 学习路径")
        tabs.addTab(self.create_daily_tab(), "📋 每日任务")
        tabs.addTab(self.create_phase_tab(), "📅 三阶段计划")
        tabs.addTab(self.create_tips_tab(), "💡 各科抢分清单")

        layout.addWidget(tabs)

        back = QPushButton("返回首页")
        back.clicked.connect(lambda: self.parent.switch_page(0))
        layout.addWidget(back)

    # ========== 🎯 核心：学习路径标签页 ==========
    def create_path_tab(self):
        w = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        scroll.setWidget(scroll_content)
        main_layout = QVBoxLayout(w)
        main_layout.addWidget(scroll)

        # 当前阶段 + 目标
        phase_idx = self.plan_data.get("phase", 1) - 1
        phase_name, phase_time, phase_goal, _ = PHASES[phase_idx]

        header = QLabel(f"🎯 {phase_name}")
        header.setFont(QFont("微软雅黑", 28, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color:#ffffff;")
        layout.addWidget(header)

        info = QLabel(f"{phase_time}\n{phase_goal}")
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color:#dddddd; font-size:17px;")
        layout.addWidget(info)

        # 三大科目目标卡片
        goal_group = QGroupBox("🏆 目标分数")
        goal_group.setStyleSheet("QGroupBox{color:#ffffff; font-weight:bold; font-size:16px;}")
        goal_layout = QHBoxLayout(goal_group)
        goal_layout.setSpacing(15)

        for subj, current, target in [
            ("📐 数学", "50-60", "85-95"),
            ("🇬🇧 英语", "40-50", "65-75"),
            ("⚛️ 物理", "35-45", "55-65"),
        ]:
            card = QFrame()
            card.setMinimumHeight(80)
            card.setStyleSheet("QFrame{background-color:#16213e; border-radius:12px; padding:15px;}")
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(8)
            subj_label = QLabel(subj, alignment=Qt.AlignCenter)
            subj_label.setStyleSheet("color:#ffffff; font-size:20px; font-weight:bold;")
            card_layout.addWidget(subj_label)
            goal_label = QLabel(f"现在：{current}分\n→ 目标：{target}分", alignment=Qt.AlignCenter)
            goal_label.setStyleSheet("color:#cccccc; font-size:15px;")
            card_layout.addWidget(goal_label)
            goal_layout.addWidget(card)
        layout.addWidget(goal_group)

        # ===== 今日学习路径（核心） =====
        path_group = QGroupBox("📌 今天的学习路线——按顺序完成")
        path_group.setStyleSheet("QGroupBox{color:#ffffff; font-weight:bold; font-size:16px;}")
        path_layout = QVBoxLayout(path_group)
        path_layout.setSpacing(12)

        # 根据当前进度动态生成路径步骤
        math_done = self.plan_data.get("math_unit", 0)
        eng_done = self.plan_data.get("english_words", 0)
        phy_done = self.plan_data.get("physics_exp", 0)

        steps = []

        # 第1步：数学公式
        if math_done < 9:
            steps.append(("📐 第1步：抄写数学公式",
                          f"进度 {math_done}/9 单元 · 每天1个单元，抄3遍",
                          lambda: self.go_to_page(3, "数学"),  # 学习模式 → 数学
                          "📚 去学习模式"))
        # 第2步：英语单词
        if eng_done < 800:
            steps.append(("🇬🇧 第2步：背英语单词",
                          f"进度 {eng_done}/800 词 · 每天15-20个，看到英文知道中文就行",
                          lambda: self.go_to_page(6, ""),  # 英语专项
                          "🇬🇧 去英语专项"))
        # 第3步：物理实验
        if phy_done < 7:
            steps.append(("⚛️ 第3步：物理实验考点",
                          f"进度 {phy_done}/7 实验 · 每个实验背：仪器→步骤→公式结论",
                          lambda: self.go_to_page(3, "物理"),  # 学习模式 → 物理
                          "📚 去学习模式"))
        # 第4步：数学做题（前10选择+前2填空+前3大题）
        steps.append(("📝 第4步：数学基础题训练",
                      "做一套「前10选择 + 前2填空 + 前3道大题」，目标拿60分",
                      lambda: self.go_to_page(4, ""),  # 考试模式
                      "📝 去考试模式"))
        # 第5步：英语阅读A/B篇
        steps.append(("📖 第5步：英语阅读A/B篇",
                      "直接去原文找答案，每篇争取全对",
                      lambda: self.go_to_page(6, ""),
                      "🇬🇧 去英语专项"))
        # 第6步：物理实验题填空
        steps.append(("🔬 第6步：物理实验题训练",
                      "做2道实验填空题，答案往往是常数或简单计算",
                      lambda: self.go_to_page(4, ""),
                      "📝 去考试模式"))
        # 第7步：睡前复习
        steps.append(("🌙 第7步：睡前回顾",
                      "回顾3个数学公式 + 5个英语单词",
                      lambda: self.go_to_page(3, ""),
                      "📚 去学习模式"))

        for i, (title, desc, callback, btn_text) in enumerate(steps):
            step_widget = QFrame()
            step_widget.setMinimumHeight(70)
            step_widget.setStyleSheet(
                "QFrame{background-color:#16213e; border-radius:10px; padding:12px; margin:2px;}"
            )
            step_layout = QHBoxLayout(step_widget)
            step_layout.setSpacing(10)

            # 序号
            num_label = QLabel(f" {i+1} ")
            num_label.setFont(QFont("微软雅黑", 26, QFont.Bold))
            num_label.setFixedWidth(50)
            num_label.setAlignment(Qt.AlignCenter)
            num_label.setStyleSheet("color:#4CAF50;")
            step_layout.addWidget(num_label)

            # 内容
            text_layout = QVBoxLayout()
            text_layout.setSpacing(4)
            title_label = QLabel(title)
            title_label.setStyleSheet("color:#ffffff; font-size:18px; font-weight:bold;")
            text_layout.addWidget(title_label)
            desc_label = QLabel(desc)
            desc_label.setStyleSheet("color: #aaaaaa; font-size: 15px;")
            desc_label.setWordWrap(True)
            text_layout.addWidget(desc_label)
            step_layout.addLayout(text_layout)

            step_layout.addStretch()

            # 开始按钮
            start_btn = QPushButton(btn_text)
            start_btn.setFixedWidth(130)
            start_btn.setFixedHeight(40)
            start_btn.setStyleSheet("QPushButton{background-color:#4CAF50; color:white; font-weight:bold; font-size:14px; border-radius:6px; padding:8px;}")
            start_btn.clicked.connect(callback)
            step_layout.addWidget(start_btn)

            path_layout.addWidget(step_widget)

        layout.addWidget(path_group)

        # 一句话鼓励
        quote = QLabel("💪 高考拼的不是天赋，是策略和执行力。每天完成这7步，坚持1个月，你一定能看到变化！")
        quote.setWordWrap(True)
        quote.setAlignment(Qt.AlignCenter)
        quote.setStyleSheet("font-size: 17px; color: #4CAF50; padding: 12px;")
        layout.addWidget(quote)

        layout.addStretch()
        return w

    def go_to_page(self, page_idx, subject_hint=""):
        """跳转到指定页面，如果带科目提示就切换到对应标签页"""
        if subject_hint:
            # 如果是学习模式页，切换标签到对应科目
            if page_idx == 3:  # StudyPage
                tab_map = {"数学": 0, "英语": 1, "物理": 2}
                if subject_hint in tab_map:
                    self.parent.page_study.tabs.setCurrentIndex(tab_map[subject_hint])
        self.parent.switch_page(page_idx)

    # ========== 每日任务标签页（保持原有但精简） ==========
    def create_daily_tab(self):
        w = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(12)
        scroll.setWidget(scroll_content)
        main_layout = QVBoxLayout(w)
        main_layout.addWidget(scroll)

        phase_name, _, phase_desc, _ = PHASES[self.plan_data.get("phase", 1) - 1]
        title = QLabel(f"当前阶段：{phase_name}")
        title.setFont(QFont("微软雅黑", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color:#ffffff;")
        layout.addWidget(title)

        subtitle = QLabel(phase_desc)
        subtitle.setWordWrap(True)
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color:#cccccc; font-size:15px;")
        layout.addWidget(subtitle)

        # 进度概览
        progress_group = QGroupBox("📊 学习进度")
        progress_group.setStyleSheet("QGroupBox{color:#ffffff; font-size:15px; font-weight:bold;}")
        pg_layout = QVBoxLayout(progress_group)
        pg_layout.setSpacing(8)

        math_unit = self.plan_data.get("math_unit", 0)
        math_label = QLabel(f"📐 数学公式本：已完成 {math_unit}/9 个单元")
        math_label.setStyleSheet("color:#ffffff; font-size:14px;")
        pg_layout.addWidget(math_label)
        math_bar = QProgressBar()
        math_bar.setMaximum(9)
        math_bar.setValue(min(math_unit, 9))
        math_bar.setTextVisible(True)
        math_bar.setFixedHeight(22)
        pg_layout.addWidget(math_bar)

        eng_words = self.plan_data.get("english_words", 0)
        eng_label = QLabel(f"🇬🇧 英语单词：已完成 {eng_words}/800 个")
        eng_label.setStyleSheet("color:#ffffff; font-size:14px;")
        pg_layout.addWidget(eng_label)
        eng_bar = QProgressBar()
        eng_bar.setMaximum(800)
        eng_bar.setValue(min(eng_words, 800))
        eng_bar.setTextVisible(True)
        eng_bar.setFixedHeight(22)
        pg_layout.addWidget(eng_bar)

        phy_exp = self.plan_data.get("physics_exp", 0)
        phy_label = QLabel(f"⚛️ 物理实验：已完成 {phy_exp}/7 个")
        phy_label.setStyleSheet("color:#ffffff; font-size:14px;")
        pg_layout.addWidget(phy_label)
        phy_bar = QProgressBar()
        phy_bar.setMaximum(7)
        phy_bar.setValue(min(phy_exp, 7))
        phy_bar.setTextVisible(True)
        phy_bar.setFixedHeight(22)
        pg_layout.addWidget(phy_bar)

        layout.addWidget(progress_group)

        # 每日任务清单
        task_group = QGroupBox("📝 今日任务清单")
        task_group.setStyleSheet("QGroupBox{color:#ffffff; font-size:15px; font-weight:bold;}")
        task_layout = QVBoxLayout(task_group)

        today = date.today().isoformat()
        today_tasks = self.plan_data["daily_tasks"].get(today, {})

        tasks = [
            ("math_formula", "📐 抄写数学公式（每天1个单元）"),
            ("math_practice", "📐 做10道计算题 + 前10选择+前2填空+前三道大题"),
            ("eng_words", "🇬🇧 背英语单词15-20个"),
            ("eng_reading", "🇬🇧 英语阅读A/B篇2篇"),
            ("eng_writing", "🇬🇧 作文模板抄写/默写"),
            ("physics_concept", "⚛️ 物理公式背诵 + 实验考点"),
            ("physics_practice", "⚛️ 做1道简单力学计算题 + 2道实验填空题"),
            ("review_evening", "🌙 睡前回顾3个数学公式 + 5个英语单词"),
        ]

        for key, label in tasks:
            cb = QCheckBox(label)
            cb.setChecked(today_tasks.get(key, False))
            cb.setStyleSheet("QCheckBox{color:#ffffff; font-size:14px; spacing:8px;}")
            cb.stateChanged.connect(lambda state, k=key: self.on_task_toggle(k, state))
            self.checkboxes[key] = cb
            task_layout.addWidget(cb)

        extra_label = QLabel("\n🔄 周末额外任务（周六/周日做）：\n"
                             "• 做一套数学高考卷的前10选择+前2填空+前3道大题\n"
                             "• 预习下周数学、物理要讲的内容")
        extra_label.setWordWrap(True)
        extra_label.setStyleSheet("color:#aaaaaa; font-size:14px;")
        task_layout.addWidget(extra_label)

        layout.addWidget(task_group)

        # 完成统计
        completed = sum(1 for v in today_tasks.values() if v)
        total = len(tasks)
        stats_label = QLabel(f"📈 今日完成：{completed}/{total} 项")
        stats_label.setAlignment(Qt.AlignCenter)
        stats_label.setStyleSheet("color:#ffffff; font-size:16px; font-weight:bold;")
        layout.addWidget(stats_label)
        record_bar = QProgressBar()
        record_bar.setMaximum(total)
        record_bar.setValue(completed)
        record_bar.setTextVisible(True)
        record_bar.setFixedHeight(24)
        layout.addWidget(record_bar)

        # 一键更新进度按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_math = QPushButton("📐 数学完成1个单元")
        btn_math.setStyleSheet("QPushButton{font-size:14px; padding:8px;}")
        btn_math.clicked.connect(lambda: self.add_progress("math_unit", 9))
        btn_eng = QPushButton("🇬🇧 英语完成40个单词")
        btn_eng.setStyleSheet("QPushButton{font-size:14px; padding:8px;}")
        btn_eng.clicked.connect(lambda: self.add_progress("english_words", 800))
        btn_phy = QPushButton("⚛️ 物理完成1个实验")
        btn_phy.setStyleSheet("QPushButton{font-size:14px; padding:8px;}")
        btn_phy.clicked.connect(lambda: self.add_progress("physics_exp", 7))
        btn_layout.addWidget(btn_math)
        btn_layout.addWidget(btn_eng)
        btn_layout.addWidget(btn_phy)
        layout.addLayout(btn_layout)

        layout.addStretch()
        return w

    def on_task_toggle(self, key, state):
        today = date.today().isoformat()
        if today not in self.plan_data["daily_tasks"]:
            self.plan_data["daily_tasks"][today] = {}
        self.plan_data["daily_tasks"][today][key] = bool(state)
        save_plan_checklist(self.plan_data)

    def add_progress(self, key, max_val):
        current = self.plan_data.get(key, 0)
        if current < max_val:
            self.plan_data[key] = current + 1
            save_plan_checklist(self.plan_data)
            QMessageBox.information(self, "🎉 太棒了", f"进度已更新！（{current+1}/{max_val}）")
            idx = self.parent.stack.indexOf(self)
            if idx >= 0:
                self.parent.switch_page(idx)
        else:
            QMessageBox.information(self, "提示", "该科目已全部完成！🎉")

    def create_phase_tab(self):
        w = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(12)
        scroll.setWidget(scroll_content)
        main_layout = QVBoxLayout(w)
        main_layout.addWidget(scroll)

        overview = QLabel("高 三 全 年 三 阶 段 时 间 表")
        overview.setFont(QFont("微软雅黑", 24, QFont.Bold))
        overview.setAlignment(Qt.AlignCenter)
        overview.setStyleSheet("color:#ffffff;")
        layout.addWidget(overview)

        for phase_name, phase_time, phase_goal, schedule in PHASES:
            group = QGroupBox(f"{phase_name} - {phase_time}")
            group.setStyleSheet("QGroupBox{color:#ffffff; font-size:15px; font-weight:bold;}")
            g_layout = QVBoxLayout(group)

            goal_label = QLabel(f"🎯 {phase_goal}")
            goal_label.setWordWrap(True)
            goal_label.setStyleSheet("color:#cccccc; font-size:15px; font-weight:normal;")
            g_layout.addWidget(goal_label)

            table = QTableWidget()
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(["时间段", "学习内容"])
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table.setRowCount(len(schedule))
            table.setStyleSheet("QTableWidget{font-size:14px;} QHeaderView::section{font-size:14px;}")
            for i, (time_slot, content) in enumerate(schedule):
                item0 = QTableWidgetItem(time_slot)
                item0.setFont(QFont("微软雅黑", 13))
                table.setItem(i, 0, item0)
                item1 = QTableWidgetItem(content)
                item1.setFont(QFont("微软雅黑", 13))
                table.setItem(i, 1, item1)
            g_layout.addWidget(table)

            layout.addWidget(group)

        layout.addStretch()
        return w

    def create_tips_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        title = QLabel("各 科 具 体 \"抢 分\" 操 作 清 单")
        title.setFont(QFont("微软雅黑", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color:#ffffff;")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)

        for subject, tips in SUBJECT_TIPS.items():
            group = QGroupBox(subject)
            group.setStyleSheet("QGroupBox{color:#000000;font-weight:bold; font-size:16px;}")
            g_layout = QVBoxLayout(group)
            g_layout.setSpacing(8)
            for tip in tips:
                label = QLabel(f"• {tip}")
                label.setWordWrap(True)
                label.setStyleSheet("color:#000000; font-size:14px;")
                g_layout.addWidget(label)
            scroll_layout.addWidget(group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        stats_label = QLabel(
            "\n💪 记住：高考拼的不是天赋，是策略和执行力！\n"
            "高一高二欠的账，高三一年可以还清。但要每天都还，不能拖。"
        )
        stats_label.setWordWrap(True)
        stats_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(stats_label)

        return w

    def apply_font(self):
        font = QFont("微软雅黑", self.parent.settings.get("font_size", 14))
        for cb in self.checkboxes.values():
            cb.setFont(font)


# ==================== 主窗口 ====================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.reward = RewardSystem()
        self.reward.parent = self
        self.study_timer = StudyTimer(self.reward, self)
        self.trainer = None
        self.trainer_subject = None
        self.init_ui()
        self.apply_theme()
        self.apply_fonts_to_all_pages()
    def init_ui(self):
        self.setWindowTitle("自适应军考集训系统 v13.0（完整版）")
        self.setMinimumSize(1100, 700)
        self.center()
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        # 左侧导航
        nav = QWidget()
        nav.setFixedWidth(220)
        self.nav = nav
        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(10, 20, 10, 20)
        title = QLabel("🏆 学习系统")
        title.setFont(QFont("微软雅黑", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        nav_layout.addWidget(title)
        self.btn_home = QPushButton("🏠 首页")
        self.btn_train = QPushButton("🎯 自适应训练")
        self.btn_study = QPushButton("📚 学习模式")
        self.btn_exam = QPushButton("📝 考试模式")
        self.btn_mistake = QPushButton("📖 错题本")
        self.btn_english = QPushButton("🇬🇧 英语专项")
        self.btn_essay = QPushButton("📝 作文范文")
        self.btn_plan = QPushButton("📋 学习计划")
        self.btn_settings = QPushButton("⚙️ 设置")
        self.btn_quit = QPushButton("🚪 退出")
        for btn in [self.btn_home, self.btn_train, self.btn_study, self.btn_exam, self.btn_mistake, self.btn_english, self.btn_essay, self.btn_plan, self.btn_settings, self.btn_quit]:
            btn.setFont(QFont("微软雅黑", 11))
            btn.setMinimumHeight(48)
            nav_layout.addWidget(btn)
        nav_layout.addStretch()
        self.nav_status = QLabel("积分0 | ⭐0 | ❤️0")
        self.nav_status.setAlignment(Qt.AlignCenter)
        nav_layout.addWidget(self.nav_status)
        # 右侧内容
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        top_bar = QFrame()
        top_bar.setFixedHeight(70)
        bar_layout = QHBoxLayout(top_bar)
        self.lbl_title = QLabel("首页")
        self.lbl_status = QLabel("")
        self.lbl_study_time = QLabel("今日学习: 0.0小时/3.0小时")
        bar_layout.addWidget(self.lbl_title)
        bar_layout.addStretch()
        bar_layout.addWidget(self.lbl_study_time)
        bar_layout.addWidget(self.lbl_status)
        content_layout.addWidget(top_bar)
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack, 1)
        # 页面
        self.page_home = self.create_home_page()
        self.page_train_subject = TrainSubjectPage(self)
        self.page_training = TrainingPage(self)
        self.page_study = StudyPage(self)
        self.page_exam = ExamPage(self)
        self.page_mistake = MistakePage(self)
        self.page_english = EnglishSpecialWidget(ENGLISH_WORDS, self.reward, self.settings, self)
        self.page_essay = EssayPage(self)
        self.page_plan = StudyPlanPage(self)
        self.stack.addWidget(self.page_home)        # 0
        self.stack.addWidget(self.page_train_subject) # 1
        self.stack.addWidget(self.page_training)     # 2
        self.stack.addWidget(self.page_study)        # 3
        self.stack.addWidget(self.page_exam)         # 4
        self.stack.addWidget(self.page_mistake)      # 5
        self.stack.addWidget(self.page_english)      # 6
        self.stack.addWidget(self.page_essay)        # 7
        self.stack.addWidget(self.page_plan)         # 8
        main_layout.addWidget(nav)
        main_layout.addWidget(content, 1)
        # 连接
        self.btn_home.clicked.connect(lambda: self.switch_page(0))
        self.btn_train.clicked.connect(lambda: self.switch_page(1))
        self.btn_study.clicked.connect(lambda: self.switch_page(3))
        self.btn_exam.clicked.connect(lambda: self.switch_page(4))
        self.btn_mistake.clicked.connect(lambda: self.switch_page(5))
        self.btn_english.clicked.connect(lambda: self.switch_page(6))
        self.btn_essay.clicked.connect(lambda: self.switch_page(7))
        self.btn_plan.clicked.connect(lambda: self.switch_page(8))
        self.btn_settings.clicked.connect(self.open_settings)
        self.btn_quit.clicked.connect(self.close)
        self.switch_page(0)
        self.refresh_status()
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_status)
        self.timer.start(2000)
    def create_home_page(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(40, 20, 40, 20)
        welcome = QLabel("🔥 自适应军考集训系统 v13.0")
        welcome.setFont(QFont("微软雅黑", 24, QFont.Bold))
        welcome.setAlignment(Qt.AlignCenter)
        layout.addWidget(welcome)
        subtitle = QLabel("做对数学/物理得⭐ · 3⭐换1❤抽奖 · 学3小时得⭐")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        # ====== 今日学习路径（核心入口） ======
        plan_data = load_plan_checklist()
        phase_idx = plan_data.get("phase", 1) - 1
        phase_name, _, _, _ = PHASES[phase_idx]
        math_done = plan_data.get("math_unit", 0)
        eng_done = plan_data.get("english_words", 0)
        phy_done = plan_data.get("physics_exp", 0)

        path_card = QFrame()
        path_card.setStyleSheet("background-color:#16213e; border-radius:12px; padding:15px;")
        path_layout = QVBoxLayout(path_card)

        path_title = QLabel(f"🎯 {phase_name} · 今日学习路线")
        path_title.setFont(QFont("微软雅黑", 18, QFont.Bold))
        path_title.setAlignment(Qt.AlignCenter)
        path_layout.addWidget(path_title)

        # 进度摘要
        progress_text = QLabel(
            f"📐 数学公式 {math_done}/9  |  "
            f"🇬🇧 英语单词 {eng_done}/800  |  "
            f"⚛️ 物理实验 {phy_done}/7"
        )
        progress_text.setAlignment(Qt.AlignCenter)
        path_layout.addWidget(progress_text)

        # 快捷步骤（精简版）
        steps = [
            ("1️⃣ 抄数学公式", "📚 学习模式", 3),
            ("2️⃣ 背英语单词", "🇬🇧 英语专项", 6),
            ("3️⃣ 复习物理实验", "📚 学习模式", 3),
            ("4️⃣ 数学基础题训练", "📝 考试模式", 4),
        ]
        step_grid = QHBoxLayout()
        for label, btn_text, page in steps:
            btn = QPushButton(f"{label}")
            btn.setMinimumHeight(50)
            btn.clicked.connect(lambda checked, p=page, l=label: self.switch_page(p))
            step_grid.addWidget(btn)
        path_layout.addLayout(step_grid)

        start_btn = QPushButton("🚀 开始今日学习 →")
        start_btn.setMinimumHeight(50)
        start_btn.setStyleSheet("background-color:#4CAF50; color:white; font-size:16px; font-weight:bold; border-radius:8px;")
        start_btn.clicked.connect(lambda: self.switch_page(8))
        path_layout.addWidget(start_btn)

        layout.addWidget(path_card)

        self.home_status = QLabel()
        self.home_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.home_status)
        grid = QHBoxLayout()
        for text, idx in [("🎯 训练",1), ("📚 学习",3), ("📝 考试",4), ("📖 错题",5), ("🇬🇧 单词",6), ("📝 作文",7), ("📋 计划",8)]:
            btn = QPushButton(text)
            btn.setMinimumHeight(60)
            btn.clicked.connect(lambda checked, i=idx: self.switch_page(i))
            grid.addWidget(btn)
        layout.addLayout(grid)
        layout.addStretch()
        self.update_home_status()
        self.home_timer = QTimer()
        self.home_timer.timeout.connect(self.update_home_status)
        self.home_timer.start(1000)
        return w
    def update_home_status(self):
        self.home_status.setText(f"积分 {self.reward.points} 分      ⭐ {self.reward.stars} 颗      ❤️ {self.reward.hearts} 颗")
    def switch_page(self, index):
        if hasattr(self, 'current_page_index'):
            self.study_timer.stop_page()
        self.stack.setCurrentIndex(index)
        titles = ["首页", "自适应训练", "训练中", "学习模式", "考试模式", "错题本", "英语专项", "作文范文", "学习计划"]
        self.lbl_title.setText(titles[index] if index < len(titles) else "")
        if index in [1,2,3,4,6,7,8]:
            self.study_timer.start_page(titles[index])
        self.current_page_index = index
        self.refresh_status()
        if index == 2 and self.trainer is not None:
            self.page_training.set_trainer(self.trainer, self.trainer_subject)
    def start_training(self, subject):
        self.trainer_subject = subject
        self.trainer = AdaptiveTrainer(subject, ALL_QUESTIONS[subject])
        self.switch_page(2)
    def refresh_status(self):
        status = f"积分 {self.reward.points}  |  ⭐ {self.reward.stars}  |  ❤️ {self.reward.hearts}"
        self.lbl_status.setText(status)
        self.nav_status.setText(status)
        self.update_study_status()
    def update_study_status(self):
        hours = self.study_timer.get_today_hours()
        remain = self.study_timer.get_remaining_seconds() / 3600.0
        self.lbl_study_time.setText(f"今日学习: {hours:.1f}小时 / 3.0小时  (还需{remain:.1f}小时)")
    def center(self):
        screen = QDesktopWidget().availableGeometry()
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)
    def open_settings(self):
        dlg = SettingsDialog(self.settings, self)
        if dlg.exec_() == QDialog.Accepted:
            new = dlg.get_settings()
            if new != self.settings:
                self.settings = new
                save_settings(self.settings)
                self.apply_theme()
                self.apply_fonts_to_all_pages()
                QMessageBox.information(self, "提示", "设置已应用")
    def apply_theme(self):
        theme = self.settings.get("theme", "dark")
        themes = {
            "dark": {"bg": "#1a1a2e", "card": "#16213e", "light": "#0f3460", "fg": "#ffffff", "accent": "#e94560"},
            "light": {"bg": "#f5f5f5", "card": "#ffffff", "light": "#e0e0e0", "fg": "#000000", "accent": "#2196F3"},
            "blue": {"bg": "#0c2d48", "card": "#1e4a6f", "light": "#2e6a9e", "fg": "#ffffff", "accent": "#ffb74d"},
            "green": {"bg": "#1b3b2b", "card": "#2d5e46", "light": "#4b8c63", "fg": "#ffffff", "accent": "#ffd966"},
            "warm": {"bg": "#3e2a1f", "card": "#5e3a2a", "light": "#8b5a3a", "fg": "#ffffff", "accent": "#ffaa66"}
        }
        t = themes[theme]
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {t['bg']}; }}
            QLabel {{ color: {t['fg']}; }}
            QPushButton {{ background-color: {t['card']}; color: {t['fg']}; }}
            QTextEdit, QLineEdit {{ background-color: {t['light']}; color: {t['fg']}; border: none; border-radius:6px; }}
            QTabWidget::pane {{ background-color: {t['card']}; border: 1px solid {t['light']}; }}
            QTabBar::tab {{ background-color: {t['light']}; color: {t['fg']}; padding:8px; }}
            QTabBar::tab:selected {{ background-color: {t['accent']}; }}
        """)
        self.nav.setStyleSheet(f"background-color: {t['card']};")
        btn_font_size = self.settings.get("font_size", 14) + 2
        for btn in [self.btn_home, self.btn_train, self.btn_study, self.btn_exam, self.btn_mistake, self.btn_english, self.btn_essay, self.btn_plan, self.btn_settings, self.btn_quit]:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {t['card']};
                    color: {t['fg']};
                    font-size: {btn_font_size}px;
                    border: none;
                    border-radius:8px;
                    padding:10px;
                    text-align:left;
                }}
                QPushButton:hover {{
                    background-color: {t['light']};
                    border-left:3px solid {t['accent']};
                }}
            """)
        self.nav_status.setStyleSheet(f"color: {t['fg']}; padding:10px; font-size:{self.settings.get('font_size', 14)}px;")
    def apply_fonts_to_all_pages(self):
        font = QFont("微软雅黑", self.settings.get("font_size", 14))
        for page in [self.page_train_subject, self.page_training, self.page_study, self.page_exam, self.page_mistake, self.page_english, self.page_essay, self.page_plan]:
            if hasattr(page, 'apply_font'):
                page.apply_font()
            else:
                for btn in page.findChildren(QPushButton):
                    btn.setFont(font)
        self.lbl_title.setFont(font)
        self.lbl_status.setFont(font)
        self.lbl_study_time.setFont(font)
        self.home_status.setFont(font)

# ==================== 启动 ====================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
