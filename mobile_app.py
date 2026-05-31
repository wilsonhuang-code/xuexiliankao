#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自适应学练考系统 - 手机版 (Kivy)
将原PyQt5桌面程序转换为Android APK
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
from kivy.uix.checkbox import CheckBox
from kivy.uix.switch import Switch
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ListProperty
from kivy.lang import Builder
from kivy.utils import get_color_from_hex

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

# ==================== 数学题库 ====================
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
    
    return questions

MATH_QUESTIONS = build_math_questions()

# ==================== 物理题库 ====================
def build_physics_questions():
    questions = []
    exp1 = [
        ("打点计时器使用什么电源？频率多少？", "交流电 50Hz"), ("打点计时器打点周期", "0.02s"),
        ("平均速度公式", "v=Δx/Δt"), ("加速度公式（逐差法）", "a=(x₄+x₅+x₆-x₁-x₂-x₃)/(3T)²"),
    ]
    for text, ans in exp1:
        questions.append({"text": f"【匀变速直线运动】{text}", "answer": ans, "explain": ans, "level": 1, "video": ""})
    return questions

PHYSICS_QUESTIONS = build_physics_questions()

# ==================== 英语单词库 ====================
def generate_full_word_list():
    base = [
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
        ("baby", "婴儿", "/ˈbeɪbi/"), ("back", "后面", "/bæk/"),
        ("bad", "坏", "/bæd/"), ("bag", "包", "/bæɡ/"),
        ("ball", "球", "/bɔːl/"), ("ban", "禁止", "/bæn/"),
        ("bank", "银行", "/bæŋk/"), ("bar", "酒吧", "/bɑːr/"),
        ("base", "基础", "/beɪs/"), ("basketball", "篮球", "/ˈbɑːskɪtbɔːl/"),
        ("bathroom", "浴室", "/ˈbɑːθruːm/"), ("be", "是", "/biː/"),
        ("beach", "海滩", "/biːtʃ/"), ("bear", "忍受", "/beər/"),
        ("beat", "打", "/biːt/"), ("beautiful", "美丽", "/ˈbjuːtɪfəl/"),
        ("because", "因为", "/bɪˈkɒz/"), ("become", "变成", "/bɪˈkʌm/"),
        ("bed", "床", "/bed/"), ("before", "之前", "/bɪˈfɔːr/"),
        ("begin", "开始", "/bɪˈɡɪn/"), ("behind", "后面", "/bɪˈhaɪnd/"),
        ("believe", "相信", "/bɪˈliːv/"), ("bell", "钟", "/bel/"),
        ("beside", "旁边", "/bɪˈsaɪd/"), ("best", "最好", "/best/"),
        ("better", "更好", "/ˈbetər/"), ("between", "之间", "/bɪˈtwiːn/"),
        ("big", "大", "/bɪɡ/"), ("bike", "自行车", "/baɪk/"),
        ("bill", "账单", "/bɪl/"), ("bird", "鸟", "/bɜːd/"),
        ("birth", "出生", "/bɜːθ/"), ("bit", "一点", "/bɪt/"),
        ("black", "黑", "/blæk/"), ("blue", "蓝", "/bluː/"),
        ("board", "板", "/bɔːd/"), ("boat", "船", "/bəʊt/"),
        ("body", "身体", "/ˈbɒdi/"), ("book", "书", "/bʊk/"),
        ("boring", "无聊", "/ˈbɔːrɪŋ/"), ("born", "出生", "/bɔːn/"),
        ("borrow", "借", "/ˈbɒrəʊ/"), ("both", "两者", "/bəʊθ/"),
        ("bottle", "瓶子", "/ˈbɒtəl/"), ("bottom", "底部", "/ˈbɒtəm/"),
        ("bowl", "碗", "/bəʊl/"), ("box", "/bɒks/"),
        ("boy", "男孩", "/bɔɪ/"), ("brain", "大脑", "/breɪn/"),
        ("bread", "面包", "/bred/"), ("break", "打破", "/breɪk/"),
        ("bridge", "桥", "/brɪdʒ/"), ("bright", "明亮", "/braɪt/"),
        ("bring", "带来", "/brɪŋ/"), ("broad", "宽阔", "/brɔːd/"),
        ("brother", "兄弟", "/ˈbrʌðər/"), ("brown", "棕色", "/braʊn/"),
        ("brush", "刷子", "/brʌʃ/"), ("build", "建造", "/bɪld/"),
        ("burn", "燃烧", "/bɜːn/"), ("bus", "公交", "/bʌs/"),
        ("business", "商业", "/ˈbɪznəs/"), ("busy", "忙碌", "/ˈbɪzi/"),
        ("but", "但是", "/bʌt/"), ("buy", "买", "/baɪ/"),
        ("by", "通过", "/baɪ/"), ("cafe", "咖啡馆", "/ˈkæfeɪ/"),
        ("cage", "笼子", "/keɪdʒ/"), ("cake", "蛋糕", "/keɪk/"),
        ("calculate", "计算", "/ˈkælkjʊleɪt/"), ("call", "呼叫", "/kɔːl/"),
        ("calm", "平静", "/kɑːm/"), ("camera", "相机", "/ˈkæmərə/"),
        ("camp", "营地", "/kæmp/"), ("can", "能", "/kæn/"),
        ("cancel", "取消", "/ˈkænsəl/"), ("capital", "首都", "/ˈkæpɪtəl/"),
        ("car", "汽车", "/kɑːr/"), ("card", "卡片", "/kɑːd/"),
        ("care", "关心", "/keər/"), ("careful", "小心", "/ˈkeəfəl/"),
        ("carry", "携带", "/ˈkæri/"), ("case", "情况", "/keɪs/"),
        ("cash", "现金", "/kæʃ/"), ("cat", "猫", "/kæt/"),
        ("catch", "抓住", "/kætʃ/"), ("cause", "原因", "/kɔːz/"),
        ("celebrate", "庆祝", "/ˈselɪbreɪt/"), ("center", "中心", "/ˈsentər/"),
        ("certain", "确定", "/ˈsɜːtən/"), ("chair", "椅子", "/tʃeər/"),
        ("chance", "机会", "/tʃɑːns/"), ("change", "改变", "/tʃeɪndʒ/"),
        ("cheap", "便宜", "/tʃiːp/"), ("check", "检查", "/tʃek/"),
        ("cheer", "欢呼", "/tʃɪər/"), ("cheese", "奶酪", "/tʃiːz/"),
        ("chemistry", "化学", "/ˈkemɪstri/"), ("chess", "棋", "/tʃes/"),
        ("chicken", "鸡", "/ˈtʃɪkɪn/"), ("chief", "首领", "/tʃiːf/"),
        ("child", "孩子", "/tʃaɪld/"), ("choose", "选择", "/tʃuːz/"),
        ("church", "教堂", "/tʃɜːtʃ/"), ("cinema", "电影院", "/ˈsɪnəmə/"),
        ("city", "城市", "/ˈsɪti/"), ("class", "班级", "/klɑːs/"),
        ("classmate", "同学", "/ˈklɑːsmeɪt/"), ("clean", "清洁", "/kliːn/"),
        ("clear", "清晰", "/klɪər/"), ("clever", "聪明", "/ˈklevər/"),
        ("click", "点击", "/klɪk/"), ("climb", "爬", "/klaɪm/"),
        ("clock", "钟", "/klɒk/"), ("close", "关闭", "/kləʊz/"),
        ("clothes", "衣服", "/kləʊðz/"), ("cloud", "云", "/klaʊd/"),
        ("club", "俱乐部", "/klʌb/"), ("coach", "教练", "/kəʊtʃ/"),
        ("coal", "煤", "/kəʊl/"), ("coast", "海岸", "/kəʊst/"),
        ("coat", "外套", "/kəʊt/"), ("code", "代码", "/kəʊd/"),
        ("coffee", "咖啡", "/ˈkɒfi/"), ("cold", "冷", "/kəʊld/"),
        ("collect", "收集", "/kəˈlekt/"), ("college", "大学", "/ˈkɒlɪdʒ/"),
        ("color", "颜色", "/ˈkʌlər/"), ("come", "来", "/kʌm/"),
        ("comfort", "舒适", "/ˈkʌmfət/"), ("common", "普通", "/ˈkɒmən/"),
        ("communicate", "沟通", "/kəˈmjuːnɪkeɪt/"), ("community", "社区", "/kəˈmjuːnəti/"),
        ("company", "公司", "/ˈkʌmpəni/"), ("compare", "比较", "/kəmˈpeər/"),
        ("compete", "竞争", "/kəmˈpiːt/"), ("complete", "完整", "/kəmˈpliːt/"),
        ("computer", "电脑", "/kəmˈpjuːtər/"), ("concert", "音乐会", "/ˈkɒnsət/"),
        ("condition", "条件", "/kənˈdɪʃən/"), ("connect", "连接", "/kəˈnekt/"),
        ("consider", "考虑", "/kənˈsɪdər/"), ("continue", "继续", "/kənˈtɪnjuː/"),
        ("control", "控制", "/kənˈtrəʊl/"), ("convenient", "方便", "/kənˈviːniənt/"),
        ("cook", "烹饪", "/kʊk/"), ("cool", "凉爽", "/kuːl/"),
        ("copy", "复制", "/ˈkɒpi/"), ("core", "核心", "/kɔːr/"),
        ("corner", "角落", "/ˈkɔːnər/"), ("correct", "正确", "/kəˈrekt/"),
        ("cost", "成本", "/kɒst/"), ("cough", "咳嗽", "/kɒf/"),
        ("could", "可以", "/kʊd/"), ("count", "计数", "/kaʊnt/"),
        ("country", "国家", "/ˈkʌntri/"), ("couple", "夫妇", "/ˈkʌpəl/"),
        ("courage", "勇气", "/ˈkʌrɪdʒ/"), ("course", "课程", "/kɔːs/"),
        ("cousin", "表亲", "/ˈkʌzən/"), ("cover", "覆盖", "/ˈkʌvər/"),
        ("cow", "牛", "/kaʊ/"), ("create", "创造", "/kriˈeɪt/"),
        ("cross", "穿过", "/krɒs/"), ("crowd", "人群", "/kraʊd/"),
        ("cry", "哭", "/kraɪ/"), ("culture", "文化", "/ˈkʌltʃər/"),
        ("cup", "杯子", "/kʌp/"), ("current", "当前", "/ˈkʌrənt/"),
        ("custom", "习惯", "/ˈkʌstəm/"), ("customer", "顾客", "/ˈkʌstəmər/"),
        ("cut", "切", "/kʌt/"), ("cute", "可爱", "/kjuːt/"),
        ("daily", "每日", "/ˈdeɪli/"), ("dance", "跳舞", "/dɑːns/"),
        ("danger", "危险", "/ˈdeɪndʒər/"), ("dark", "黑暗", "/dɑːk/"),
        ("data", "数据", "/ˈdeɪtə/"), ("date", "日期", "/deɪt/"),
        ("daughter", "女儿", "/ˈdɔːtər/"), ("day", "天", "/deɪ/"),
        ("dead", "死", "/ded/"), ("deal", "交易", "/diːl/"),
        ("dear", "亲爱的", "/dɪər/"), ("death", "死亡", "/deθ/"),
        ("decide", "决定", "/dɪˈsaɪd/"), ("decision", "决定", "/dɪˈsɪʒən/"),
        ("deep", "深", "/diːp/"), ("defeat", "击败", "/dɪˈfiːt/"),
        ("defend", "保卫", "/dɪˈfend/"), ("degree", "程度", "/dɪˈɡriː/"),
        ("demand", "需求", "/dɪˈmɑːnd/"), ("deny", "否认", "/dɪˈnaɪ/"),
        ("depend", "依赖", "/dɪˈpend/"), ("describe", "描述", "/dɪˈskraɪb/"),
        ("desert", "沙漠", "/ˈdezət/"), ("deserve", "应得", "/dɪˈzɜːv/"),
        ("design", "设计", "/dɪˈzaɪn/"), ("desire", "渴望", "/dɪˈzaɪər/"),
        ("desktop", "桌面", "/ˈdesktɒp/"), ("develop", "发展", "/dɪˈveləp/"),
        ("devote", "奉献", "/dɪˈvəʊt/"), ("dialogue", "对话", "/ˈdaɪəlɒɡ/"),
        ("dictionary", "词典", "/ˈdɪkʃənəri/"), ("die", "死", "/daɪ/"),
        ("differ", "不同", "/ˈdɪfər/"), ("different", "不同", "/ˈdɪfərənt/"),
        ("difficult", "困难", "/ˈdɪfɪkəlt/"), ("dig", "挖", "/dɪɡ/"),
        ("dinner", "晚餐", "/ˈdɪnər/"), ("direct", "直接", "/dɪˈrekt/"),
        ("direction", "方向", "/dɪˈrekʃən/"), ("director", "导演", "/dɪˈrektər/"),
        ("dirty", "脏", "/ˈdɜːti/"), ("discover", "发现", "/dɪˈskʌvər/"),
        ("discuss", "讨论", "/dɪˈskʌs/"), ("disease", "疾病", "/dɪˈziːz/"),
        ("dish", "盘子", "/dɪʃ/"), ("distance", "距离", "/ˈdɪstəns/"),
        ("distant", "遥远", "/ˈdɪstənt/"), ("distinguish", "区分", "/dɪˈstɪŋɡwɪʃ/"),
        ("divide", "分开", "/dɪˈvaɪd/"), ("do", "做", "/duː/"),
        ("doctor", "医生", "/ˈdɒktər/"), ("document", "文件", "/ˈdɒkjʊmənt/"),
        ("dog", "狗", "/dɒɡ/"), ("dollar", "美元", "/ˈdɒlər/"),
        ("door", "门", "/dɔːr/"), ("double", "双倍", "/ˈdʌbəl/"),
        ("doubt", "怀疑", "/daʊt/"), ("down", "向下", "/daʊn/"),
        ("download", "下载", "/ˈdaʊnləʊd/"), ("drag", "拖", "/dræɡ/"),
        ("draw", "画", "/drɔː/"), ("dream", "梦", "/driːm/"),
        ("dress", "裙子", "/dres/"), ("drink", "喝", "/drɪŋk/"),
        ("drive", "驾驶", "/draɪv/"), ("drop", "掉落", "/drɒp/"),
        ("drug", "药物", "/drʌɡ/"), ("dry", "干", "/draɪ/"),
        ("duck", "鸭子", "/dʌk/"), ("due", "到期", "/djuː/"),
        ("during", "期间", "/ˈdjʊərɪŋ/"), ("dust", "灰尘", "/dʌst/"),
        ("duty", "责任", "/ˈdjuːti/"), ("each", "每个", "/iːtʃ/"),
        ("eager", "渴望", "/ˈiːɡər/"), ("ear", "耳朵", "/ɪər/"),
        ("early", "早", "/ˈɜːli/"), ("earn", "赚", "/ɜːn/"),
        ("earth", "地球", "/ɜːθ/"), ("east", "东", "/iːst/"),
        ("easy", "容易", "/ˈiːzi/"), ("eat", "吃", "/iːt/"),
        ("education", "教育", "/ˌedʒʊˈkeɪʃən/"), ("effect", "效果", "/ɪˈfekt/"),
        ("effort", "努力", "/ˈefət/"), ("egg", "蛋", "/eɡ/"),
        ("eight", "八", "/eɪt/"), ("either", "两者之一", "/ˈaɪðər/"),
        ("elderly", "老年人", "/ˈeldəli/"), ("electric", "电", "/ɪˈlektrɪk/"),
        ("elephant", "大象", "/ˈelɪfənt/"), ("else", "其他", "/els/"),
        ("email", "电子邮件", "/ˈiːmeɪl/"), ("empty", "空", "/ˈempti/"),
        ("enable", "使能够", "/ɪˈneɪbəl/"), ("encourage", "鼓励", "/ɪnˈkʌrɪdʒ/"),
        ("end", "结束", "/end/"), ("enemy", "敌人", "/ˈenəmi/"),
        ("energy", "能量", "/ˈenədʒi/"), ("engine", "引擎", "/ˈendʒɪn/"),
        ("engineer", "工程师", "/ˌendʒɪˈnɪər/"), ("enjoy", "享受", "/ɪnˈdʒɔɪ/"),
        ("enough", "足够", "/ɪˈnʌf/"), ("ensure", "确保", "/ɪnˈʃʊər/"),
        ("enter", "进入", "/ˈentər/"), ("entertain", "娱乐", "/ˌentəˈteɪn/"),
        ("enthusiasm", "热情", "/ɪnˈθjuːziæzəm/"), ("entire", "整个", "/ɪnˈtaɪər/"),
        ("environment", "环境", "/ɪnˈvaɪrənmənt/"), ("equal", "平等", "/ˈiːkwəl/"),
        ("escape", "逃跑", "/ɪˈskeɪp/"), ("especially", "特别", "/ɪˈspeʃəli/"),
        ("essay", "文章", "/ˈeseɪ/"), ("establish", "建立", "/ɪˈstæblɪʃ/"),
        ("evaluate", "评估", "/ɪˈvæljʊeɪt/"), ("even", "甚至", "/ˈiːvən/"),
        ("evening", "晚上", "/ˈiːvnɪŋ/"), ("event", "事件", "/ɪˈvent/"),
        ("eventually", "最终", "/ɪˈventʃuəli/"), ("ever", "曾经", "/ˈevər/"),
        ("every", "每个", "/ˈevri/"), ("exact", "精确", "/ɪɡˈzækt/"),
        ("exam", "考试", "/ɪɡˈzæm/"), ("examine", "检查", "/ɪɡˈzæmɪn/"),
        ("example", "例子", "/ɪɡˈzɑːmpəl/"), ("excellent", "优秀", "/ˈeksələnt/"),
        ("except", "除了", "/ɪkˈsept/"), ("exchange", "交换", "/ɪksˈtʃeɪndʒ/"),
        ("excite", "兴奋", "/ɪkˈsaɪt/"), ("excuse", "借口", "/ɪkˈskjuːz/"),
        ("exercise", "锻炼", "/ˈeksəsaɪz/"), ("exist", "存在", "/ɪɡˈzɪst/"),
        ("expect", "期望", "/ɪkˈspekt/"), ("expensive", "昂贵", "/ɪkˈspensɪv/"),
        ("experience", "经验", "/ɪkˈspɪəriəns/"), ("experiment", "实验", "/ɪkˈsperɪmənt/"),
        ("expert", "专家", "/ˈekspɜːt/"), ("explain", "解释", "/ɪkˈspleɪn/"),
        ("explore", "探索", "/ɪkˈsplɔːr/"), ("export", "出口", "/ɪkˈspɔːt/"),
        ("express", "表达", "/ɪkˈspres/"), ("extend", "扩展", "/ɪkˈstend/"),
        ("extra", "额外", "/ˈekstrə/"), ("extreme", "极端", "/ɪkˈstriːm/"),
        ("eye", "眼睛", "/aɪ/"), ("face", "脸", "/feɪs/"),
        ("fact", "事实", "/fækt/"), ("factory", "工厂", "/ˈfæktəri/"),
        ("fail", "失败", "/feɪl/"), ("fair", "公平", "/feər/"),
        ("fall", "落下", "/fɔːl/"), ("family", "家庭", "/ˈfæməli/"),
        ("famous", "著名", "/ˈfeɪməs/"), ("fan", "粉丝", "/fæn/"),
        ("far", "远", "/fɑːr/"), ("farm", "农场", "/fɑːm/"),
        ("fast", "快", "/fɑːst/"), ("fat", "胖", "/fæt/"),
        ("father", "父亲", "/ˈfɑːðər/"), ("fear", "恐惧", "/fɪər/"),
        ("feature", "特征", "/ˈfiːtʃər/"), ("feed", "喂养", "/fiːd/"),
        ("feel", "感觉", "/fiːl/"), ("female", "女性", "/ˈfiːmeɪl/"),
        ("fence", "栅栏", "/fens/"), ("fetch", "取", "/fetʃ/"),
        ("fever", "发烧", "/ˈfiːvər/"), ("few", "很少", "/fjuː/"),
        ("field", "田野", "/fiːld/"), ("fight", "战斗", "/faɪt/"),
        ("fill", "填满", "/fɪl/"), ("film", "电影", "/fɪlm/"),
        ("final", "最终", "/ˈfaɪnəl/"), ("find", "找到", "/faɪnd/"),
        ("fine", "好", "/faɪn/"), ("finger", "手指", "/ˈfɪŋɡər/"),
        ("finish", "完成", "/ˈfɪnɪʃ/"), ("fire", "火", "/ˈfaɪər/"),
        ("fish", "鱼", "/fɪʃ/"), ("fit", "适合", "/fɪt/"),
        ("five", "五", "/faɪv/"), ("fix", "修理", "/fɪks/"),
        ("flag", "旗", "/flæɡ/"), ("flat", "公寓", "/flæt/"),
        ("flight", "飞行", "/flaɪt/"), ("floor", "地板", "/flɔːr/"),
        ("flower", "花", "/ˈflaʊər/"), ("fly", "飞", "/flaɪ/"),
        ("focus", "焦点", "/ˈfəʊkəs/"), ("follow", "跟随", "/ˈfɒləʊ/"),
        ("food", "食物", "/fuːd/"), ("fool", "傻瓜", "/fuːl/"),
        ("foot", "脚", "/fʊt/"), ("for", "为了", "/fɔːr/"),
        ("force", "力量", "/fɔːs/"), ("foreign", "外国", "/ˈfɒrən/"),
        ("forest", "森林", "/ˈfɒrɪst/"), ("forget", "忘记", "/fəˈɡet/"),
        ("forgive", "原谅", "/fəˈɡɪv/"), ("form", "形式", "/fɔːm/"),
        ("forward", "向前", "/ˈfɔːwəd/"), ("four", "四", "/fɔːr/"),
        ("free", "自由", "/friː/"), ("freeze", "冻结", "/friːz/"),
        ("fresh", "新鲜", "/freʃ/"), ("friend", "朋友", "/frend/"),
        ("friendly", "友好", "/ˈfrendli/"), ("friendship", "友谊", "/ˈfrendʃɪp/"),
        ("from", "从", "/frɒm/"), ("front", "前面", "/frʌnt/"),
        ("fruit", "水果", "/fruːt/"), ("fuel", "燃料", "/ˈfjuːəl/"),
        ("full", "满", "/fʊl/"), ("fun", "乐趣", "/fʌn/"),
        ("function", "功能", "/ˈfʌŋkʃən/"), ("future", "未来", "/ˈfjuːtʃər/"),
    ]
    return base

ENGLISH_WORDS = generate_full_word_list()

ALL_QUESTIONS = {
    "math": MATH_QUESTIONS,
    "english": [{"text": f"单词 '{w}' 的中文意思是？", "answer": m, "explain": f"含义：{m}", "level": 1, "video": ""} for w, m, _ in ENGLISH_WORDS],
    "physics": PHYSICS_QUESTIONS,
}

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
        
        Label:
            id: title_label
            text: '自适应学练考系统'
            font_size: '18sp'
            bold: True
            color: 1, 1, 1, 1
        
        Label:
            id: status_label
            text: ''
            font_size: '14sp'
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
        
        Button:
            text: '首页'
            on_press: root.go_home()
        
        Button:
            text: '训练'
            on_press: root.go_training()
        
        Button:
            text: '学习'
            on_press: root.go_study()
        
        Button:
            text: '考试'
            on_press: root.go_exam()
        
        Button:
            text: '更多'
            on_press: root.go_more()

<TrainingPage>:
    orientation: 'vertical'
    padding: '15dp'
    spacing: '10dp'
    
    Label:
        id: level_label
        text: '难度: ⭐'
        font_size: '16sp'
        color: 1, 1, 1, 1
    
    Label:
        id: progress_label
        text: '连续正确: 0/3'
        font_size: '14sp'
        color: 0.9, 0.9, 0.9, 1
    
    Label:
        id: question_label
        text: '题目加载中...'
        font_size: '16sp'
        color: 1, 1, 1, 1
        text_size: self.width, None
        size_hint_y: None
        height: self.texture_size[1] if self.texture_size else '50dp'
        halign: 'center'
        valign: 'middle'
    
    TextInput:
        id: answer_input
        hint_text: '输入答案...'
        multiline: False
        size_hint_y: None
        height: '45dp'
        font_size: '16sp'
    
    BoxLayout:
        size_hint_y: None
        height: '50dp'
        spacing: '10dp'
        
        Button:
            id: submit_btn
            text: '提交'
            on_press: root.submit_answer()
        
        Button:
            id: next_btn
            text: '下一题'
            on_press: root.next_question()
            opacity: 0
        
        Button:
            text: '返回'
            on_press: root.go_back()
    
    Label:
        id: feedback_label
        text: ''
        font_size: '14sp'
        color: 1, 1, 1, 1
        text_size: self.width, None
        size_hint_y: None
        height: self.texture_size[1] if self.texture_size else '50dp'
        halign: 'center'

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
        
        TabbedPanelItem:
            text: '数学'
            
            ScrollView:
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height
                    padding: '10dp'
                    
                    Label:
                        id: math_content
                        text: ''
                        font_size: '14sp'
                        color: 1, 1, 1, 1
                        text_size: self.width, None
                        size_hint_y: None
                        height: self.texture_size[1] if self.texture_size else '100dp'
                        halign: 'left'
        
        TabbedPanelItem:
            text: '英语'
            
            ScrollView:
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height
                    padding: '10dp'
                    
                    Label:
                        id: english_content
                        text: ''
                        font_size: '14sp'
                        color: 1, 1, 1, 1
                        text_size: self.width, None
                        size_hint_y: None
                        height: self.texture_size[1] if self.texture_size else '100dp'
                        halign: 'left'
        
        TabbedPanelItem:
            text: '物理'
            
            ScrollView:
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height
                    padding: '10dp'
                    
                    Label:
                        id: physics_content
                        text: ''
                        font_size: '14sp'
                        color: 1, 1, 1, 1
                        text_size: self.width, None
                        size_hint_y: None
                        height: self.texture_size[1] if self.texture_size else '100dp'
                        halign: 'left'
    
    Button:
        text: '返回首页'
        size_hint_y: None
        height: '50dp'
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
    
    Label:
        id: progress_label
        text: '准备开始...'
        font_size: '14sp'
        color: 0.9, 0.9, 0.9, 1
    
    Label:
        id: question_label
        text: '点击「开始考试」'
        font_size: '16sp'
        color: 1, 1, 1, 1
        text_size: self.width, None
        size_hint_y: None
        height: self.texture_size[1] if self.texture_size else '50dp'
        halign: 'center'
    
    TextInput:
        id: answer_input
        hint_text: '输入答案...'
        multiline: False
        size_hint_y: None
        height: '45dp'
        font_size: '16sp'
    
    BoxLayout:
        size_hint_y: None
        height: '50dp'
        spacing: '10dp'
        
        Button:
            id: start_btn
            text: '开始考试'
            on_press: root.start_exam()
        
        Button:
            id: submit_btn
            text: '提交'
            on_press: root.submit_answer()
            opacity: 0
        
        Button:
            id: next_btn
            text: '下一题'
            on_press: root.next_question()
            opacity: 0
        
        Button:
            text: '返回'
            on_press: root.go_back()
    
    Label:
        id: feedback_label
        text: ''
        font_size: '14sp'
        color: 1, 1, 1, 1

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
        on_press: root.go_back()
'''

# ==================== 页面类 ====================
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
        result = self.trainer.next()
        typ = result[0]
        
        if typ == "question":
            q = result[1]
            self.ids.question_label.text = f"第{len(self.trainer.mastered) + 1}题：{q['text']}"
            self.ids.level_label.text = f"难度: {'⭐' * self.trainer.level}"
            self.ids.progress_label.text = f"连续正确: {self.trainer.correct_in_level}/3"
            self.ids.answer_input.text = ""
            self.ids.answer_input.disabled = False
            self.ids.submit_btn.opacity = 1
            self.ids.next_btn.opacity = 0
            self.ids.feedback_label.text = ""
        elif typ == "upgrade":
            level = result[1]
            self.ids.feedback_label.text = f"🎉 升级到难度{level}星！获得100积分"
        elif typ == "complete":
            self.ids.question_label.text = "🏆 完成本学科所有题目！"
            self.ids.answer_input.disabled = True
            self.ids.submit_btn.opacity = 0
            self.ids.next_btn.opacity = 0
    
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
        else:
            self.ids.feedback_label.text = f"❌ 错误。正确答案：{q['answer']}\n讲解：{q['explain']}"
        
        self.ids.answer_input.disabled = True
        self.ids.submit_btn.opacity = 0
        self.ids.next_btn.opacity = 1
    
    def go_back(self):
        App.get_running_app().root.go_home()

class StudyPage(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.load_content()
    
    def load_content(self):
        math_text = "\n".join([
            f"【难度{q['level']}星】{q['text']}\n答案：{q['answer']}\n讲解：{q['explain']}\n"
            for q in ALL_QUESTIONS["math"]
        ])
        self.ids.math_content.text = math_text
        
        english_text = "\n".join([
            f"{q['text']}\n答案：{q['answer']}\n讲解：{q['explain']}\n"
            for q in ALL_QUESTIONS["english"][:50]  # 只显示前50个
        ])
        self.ids.english_content.text = english_text
        
        physics_text = "\n".join([
            f"【难度{q['level']}星】{q['text']}\n答案：{q['answer']}\n讲解：{q['explain']}\n"
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
        self.ids.start_btn.opacity = 0
        self.ids.submit_btn.opacity = 1
        self.ids.answer_input.disabled = False
        self.show_question()
    
    def show_question(self):
        if self.index >= len(self.questions):
            self.finish_exam()
            return
        
        sub, q = self.questions[self.index]
        self.ids.info_label.text = f"第{self.index + 1}/{len(self.questions)}题"
        self.ids.progress_label.text = f"当前得分: {self.score}"
        self.ids.question_label.text = f"【{sub.upper()}】{q['text']}"
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
        else:
            self.ids.feedback_label.text = f"❌ 错误。正确答案：{q['answer']}\n讲解：{q['explain']}"
        
        self.ids.answer_input.disabled = True
        self.ids.submit_btn.opacity = 0
        self.ids.next_btn.opacity = 1
    
    def next_question(self):
        self.index += 1
        if self.index >= len(self.questions):
            self.finish_exam()
        else:
            self.show_question()
            self.ids.submit_btn.opacity = 1
            self.ids.next_btn.opacity = 0
            self.ids.answer_input.disabled = False
    
    def finish_exam(self):
        total = len(self.questions) * 10
        self.ids.info_label.text = "考试结束"
        self.ids.question_label.text = f"得分：{self.score}/{total}"
        self.ids.answer_input.disabled = True
        self.ids.submit_btn.opacity = 0
        self.ids.next_btn.opacity = 0
        self.ids.start_btn.opacity = 1
        self.ids.start_btn.text = "重新考试"
        self.ids.feedback_label.text = f"得分：{self.score}/{total}\n" + ("🎉 全部正确！" if self.score == total else f"错题数：{len(self.questions) - self.score // 10}")
    
    def go_back(self):
        App.get_running_app().root.go_home()

class MistakePage(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.load_mistakes()
    
    def load_mistakes(self):
        mistakes = []
        if os.path.exists(MISTAKE_FILE):
            with open(MISTAKE_FILE, "r", encoding="utf-8") as f:
                mistakes = json.load(f)
        
        layout = self.ids.mistake_layout
        layout.clear_widgets()
        
        if not mistakes:
            layout.add_widget(Label(
                text="✅ 暂无错题",
                font_size='16sp',
                color=(1, 1, 1, 1)
            ))
            return
        
        for item in mistakes[-20:]:  # 只显示最近20道
            card = BoxLayout(
                orientation='vertical',
                size_hint_y=None,
                height='100dp',
                padding='10dp',
                spacing='5dp'
            )
            card.add_widget(Label(
                text=f"📌 {item['question'][:80]}",
                font_size='14sp',
                color=(1, 1, 1, 1),
                halign='left'
            ))
            card.add_widget(Label(
                text=f"你的：{item['user_answer']}  正解：{item['correct_answer']}",
                font_size='12sp',
                color=(0.9, 0.9, 0.9, 1),
                halign='left'
            ))
            layout.add_widget(card)
    
    def go_back(self):
        App.get_running_app().root.go_home()

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
        
        # 欢迎语
        welcome = Label(
            text="🔥 自适应学练考系统",
            font_size='24sp',
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height='60dp'
        )
        layout.add_widget(welcome)
        
        subtitle = Label(
            text="做对数学/物理得⭐ · 3⭐换1❤抽奖",
            font_size='14sp',
            color=(0.9, 0.9, 0.9, 1),
            size_hint_y=None,
            height='40dp'
        )
        layout.add_widget(subtitle)
        
        # 功能按钮
        btn_layout = GridLayout(
            cols=2,
            spacing='10dp',
            size_hint_y=None,
            height='300dp'
        )
        
        buttons = [
            ("🎯 自适应训练", self.go_training),
            ("📚 学习模式", self.go_study),
            ("📝 考试模式", self.go_exam),
            ("📖 错题本", self.go_mistakes),
        ]
        
        for text, callback in buttons:
            btn = Button(
                text=text,
                font_size='16sp',
                size_hint_y=None,
                height='70dp'
            )
            btn.bind(on_press=callback)
            btn_layout.add_widget(btn)
        
        layout.add_widget(btn_layout)
        layout.add_widget(Label(size_hint_y=None, height='20dp'))  # 间距
        
        self.ids.title_label.text = "首页"
    
    def go_home(self):
        self.show_home()
    
    def go_training(self, *args):
        self.clear_content()
        layout = self.ids.content_layout
        
        # 学科选择
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
            height='50dp'
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
    
    def go_more(self, *args):
        # 更多功能（设置、学习计划等）
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
        
        # TODO: 添加更多功能入口
        
        back_btn = Button(
            text="返回首页",
            size_hint_y=None,
            height='50dp'
        )
        back_btn.bind(on_press=lambda btn: self.go_home())
        layout.add_widget(back_btn)
        
        self.ids.title_label.text = "更多"

# ==================== 应用类 ====================
class MobileApp(App):
    def build(self):
        Builder.load_string(KV)
        root = MainWindow()
        self.root = root
        return root
    
    def on_start(self):
        pass

if __name__ == "__main__":
    MobileApp().run()
