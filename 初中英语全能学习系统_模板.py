import sys
import os
import pickle
import random
import re
import hashlib
import subprocess
from datetime import datetime, timedelta
# 程序鎵鍦录洰褰曪紙数据文章涓庣搴忔斁在同一目录析綍锛衣
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# ==================== 注册鐮佺郴缁衣====================
LICENSE_KEY = "EDU2026@ENGLISH"  # 加密密钥
# 璁稿彲璇佹枃浠舵斁鍦xe/鑴氭湰鎵鍦录洰褰曪紙鍏煎确打包鍜岃皟璇曪級
if getattr(sys, 'frozen', False):
    EXE_DIR = os.path.dirname(sys.executable)
else:
    EXE_DIR = os.path.dirname(os.path.abspath(__file__))
LICENSE_FILE = os.path.join(EXE_DIR, "license.dat")
def get_machine_code():
    """获取机器码(MAC地址+序列号，唯一不可复）"""
    code_parts = []
    try:
        import uuid
        mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
        code_parts.append(mac)
    except:
        code_parts.append("000000000000")
    try:
        # 获取C盘卷序列号更稳定（比mac更稳定，所有Windows都支持）
        if sys.platform == 'win32':
            result = subprocess.run(
                'vol C:',
                capture_output=True, text=True, shell=True, timeout=3
            )
            # 输出格式: "序列号涓衣XXXX-XXXX" 鎴衣"Volume Serial Number is XXXX-XXXX"
            vol_text = result.stdout
            m = re.search(r'[0-9A-Fa-f]{4}[-][0-9A-Fa-f]{4}', vol_text)
            if m:
                code_parts.append(m.group().replace('-', ''))
    except:
        pass
    # 缁勫悎骞跺搱甯衣
    raw = ''.join(code_parts)
    return hashlib.md5(raw.encode()).hexdigest()[:16].upper()
def generate_reg_code(machine_code):
    """根据机器码生成注册码"""
    key = LICENSE_KEY
    combined = machine_code + key
    h = hashlib.sha256(combined.encode()).hexdigest().upper()
    # 格式鍖栦负 XXXX-XXXX-XXXX-XXXX
    reg = '-'.join([h[i:i+4] for i in range(0, 16, 4)])
    return reg
def verify_license():
    """验证注册码"""
    try:
        if not os.path.exists(LICENSE_FILE):
            return False
        with open(LICENSE_FILE, 'r') as f:
            saved_code = f.read().strip()
        if not saved_code:
            return False
        machine_code = get_machine_code()
        expected = generate_reg_code(machine_code)
        return saved_code == expected
    except:
        return False
def save_license(reg_code):
    """保存注册码"""
    try:
        with open(LICENSE_FILE, 'w') as f:
            f.write(reg_code.strip())
        return True
    except:
        return False
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QListWidget, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QListWidget, QFileDialog,
                             QMessageBox, QTextEdit, QSplitter, QDialog, QDialogButtonBox, QRadioButton,
                             QButtonGroup, QScrollArea, QComboBox, QProgressBar, QFrame)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QTextCursor
from PyQt5.QtTextToSpeech import QTextToSpeech
from phonetic_dict import phonetic_dict  # 音标查词
# ==================== 常量定义 ====================
REVIEW_CYCLES = [1, 2, 4, 7, 15, 30]  # 复习间隔天数
# ==================== AI助手配置存储 ====================
import json as _json_module
AI_CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)) if not getattr(__import__('sys'), 'frozen', False)
    else os.path.dirname(__import__('sys').executable),
    "ai_config.json"
)
def load_ai_config():
    try:
        if os.path.exists(AI_CONFIG_FILE):
            with open(AI_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return _json_module.load(f)
    except Exception:
        pass
    return {
        "api_key": "",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "system_prompt": "你是一位专业的初中英语学习助手，擅长解答英语语法、词汇、写作等问题。请用简洁清晰的中文回答，必要时给出英文例句。"
    }
def save_ai_config(config):
    try:
        with open(AI_CONFIG_FILE, 'w', encoding='utf-8') as f:
            _json_module.dump(config, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
# ==================== AI流式请求线程 ====================
class AIStreamThread(QThread):
    """后台线程：流式调用 OpenAI 兼容 API"""
    chunk_received = pyqtSignal(str)   # 每收到一段文字就发
    finished_ok = pyqtSignal(str)      # 完整回复
    error_occurred = pyqtSignal(str)   # 错误信息
    def __init__(self, messages, config, parent=None):
        super().__init__(parent)
        self.messages = messages
        self.config = config
        self._full_text = ""
    def run(self):
        try:
            import urllib.request
            import ssl
            import json
            api_key = self.config.get("api_key", "").strip()
            base_url = self.config.get("base_url", "https://api.deepseek.com/v1").rstrip("/")
            model = self.config.get("model", "deepseek-chat")
            system_prompt = self.config.get("system_prompt", "")
            if not api_key:
                self.error_occurred.emit("❌ 请先在设置中填写 API Key")
                return
            # 构建消息列表
            msgs = []
            if system_prompt:
                msgs.append({"role": "system", "content": system_prompt})
            msgs.extend(self.messages)
            payload = json.dumps({
                "model": model,
                "messages": msgs,
                "stream": True,
                "temperature": 0.7,
                "max_tokens": 2048,
            }).encode("utf-8")
            url = base_url + "/chat/completions"
            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                method="POST"
            )
            ctx = ssl._create_unverified_context()
            with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
                for raw_line in resp:
                    line = raw_line.decode("utf-8").strip()
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data["choices"][0]["delta"]
                            content = delta.get("content", "")
                            if content:
                                self._full_text += content
                                self.chunk_received.emit(content)
                        except Exception:
                            pass
            self.finished_ok.emit(self._full_text)
        except Exception as e:
            self.error_occurred.emit(f"❌ 请求失败：{str(e)}")
# ==================== 奖励系统 ====================
class RewardSystem:
    """功能方法"""
    
    def __init__(self):
        self.stars = 0
        self.hearts = 0  # 初始0颗爱心，通过星星兑换
        self.max_hearts = 5  # 爱心上限
        
        # 等级系统（由爱心驱动）
        self.level = 1
        self.total_stars_earned = 0
        self.total_hearts_earned = 0  # 累计获得爱心数
        
        # 连续学习天数
        self.consecutive_days = 0
        self.last_checkin_date = None
        
        # 成就系统
        self.achievements = []
        self.achievement_list = self._init_achievements()
        
        # 连击奖励
        self.combo = 0
        self.max_combo = 0
        
        # 统计数据
        self.stats = {
            "total_correct": 0,
            "total_wrong": 0,
            "word_correct": 0,
            "phrase_correct": 0,
            "dialogue_correct": 0,
            "grammar_correct": 0,
            "grade7_word_correct": 0,
            "grade8_word_correct": 0,
            "grade9_word_correct": 0,
            "max_combo": 0,
        }
        
        # 学习计时
        self.daily_study_seconds = 0
        self.TWO_HOURS = 7200
        
        # 加载数据
        self.load_data()
    
    def _init_achievements(self):
        """初始化成就列表"""
        return [
            {"id": "first_star", "name": "初露锋芒", "desc": "获得第一颗★", "icon": "\u2b50", "condition": lambda s: s.total_stars_earned >= 1},
            {"id": "star_10", "name": "小有成就", "desc": "获得10颗★", "icon": "\u2b50", "condition": lambda s: s.total_stars_earned >= 10},
            {"id": "star_50", "name": "学富五车", "desc": "获得50颗★", "icon": "\ud83c\udfc5", "condition": lambda s: s.total_stars_earned >= 50},
            {"id": "star_100", "name": "学识渊博", "desc": "获得100颗★", "icon": "\ud83c\udf93", "condition": lambda s: s.total_stars_earned >= 100},
            {"id": "star_500", "name": "大师级", "desc": "获得500颗★", "icon": "\ud83c\udfc6", "condition": lambda s: s.total_stars_earned >= 500},
            {"id": "consecutive_3", "name": "持之以恒", "desc": "连续学习3天", "icon": "", "condition": lambda s: s.consecutive_days >= 3},
            {"id": "consecutive_7", "name": "一周坚持", "desc": "连续学习7天", "icon": "", "condition": lambda s: s.consecutive_days >= 7},
            {"id": "consecutive_30", "name": "月度达人", "desc": "连续学习30天", "icon": "", "condition": lambda s: s.consecutive_days >= 30},
            {"id": "level_5", "name": "初出茅庐", "desc": "达到5级", "icon": "", "condition": lambda s: s.level >= 5},
            {"id": "level_10", "name": "学有所成", "desc": "达到10级", "icon": "", "condition": lambda s: s.level >= 10},
            {"id": "level_20", "name": "学贯中西", "desc": "达到20级", "icon": "", "condition": lambda s: s.level >= 20},
            {"id": "combo_5", "name": "小试牛刀", "desc": "达成5连击", "icon": "⚡", "condition": lambda s: s.max_combo >= 5},
            {"id": "combo_10", "name": "龙卷风", "desc": "达成10连击", "icon": "", "condition": lambda s: s.max_combo >= 10},
            {"id": "combo_20", "name": "无人能敌", "desc": "达成20连击", "icon": "", "condition": lambda s: s.max_combo >= 20},
        ]
    
    def add_stars(self, count=1, reason=""):
        """获得星星 → 自动兑换爱心 → 自动升级"""
        self.stars += count
        self.total_stars_earned += count
        
        # 更新连击
        self.combo += 1
        if self.combo > self.max_combo:
            self.max_combo = self.combo
            self.stats["max_combo"] = self.max_combo
        
        msg_parts = [f"获得{count}★"]
        if self.combo >= 5:
            msg_parts.append(f"🔥{self.combo}连击")
        
        # ★→❤️ 自动兑换：每2星换1心
        heart_gained = 0
        while self.stars >= 2:
            self.stars -= 2
            heart_gained += 1
            self.hearts = min(self.hearts + 1, self.max_hearts)
            self.total_hearts_earned += 1
        
        if heart_gained > 0:
            msg_parts.append(f"兑换{heart_gained}❤️")
        
        # ❤️→等级 自动升级：每5心升1级
        level_gained = 0
        while self.hearts >= 5:
            self.hearts -= 5
            self.level += 1
            level_gained += 1
        
        if level_gained > 0:
            msg_parts.append(f"🎉升级到Lv.{self.level}！")
        
        # 检查成就
        new_achievement = self._check_achievements()
        if new_achievement:
            msg_parts.append(f"{new_achievement['icon']} 解锁成就：{new_achievement['name']}")
        
        return True, " | ".join(msg_parts)
    
    def add_hearts(self, count=1):
        """增加爱心"""
        old = self.hearts
        self.hearts = min(self.hearts + count, self.max_hearts)
        return True, f"恢复{self.hearts - old}颗心"
    
    def use_heart(self):
        """功能方法"""
        if self.hearts > 0:
            self.hearts -= 1
            self.combo = 0  # 连击中断
            return True
        return False  # 鐖卞績涓嶈冻
    
    def add_study_time(self, seconds=1):
        """澧炲姞学习时间锛岃嚜鍔目鏌墦鍗衣"""
        self.daily_study_seconds += seconds
        # 学到2小时且今天还没打卡，自动打卡
        if self.daily_study_seconds >= self.TWO_HOURS:
            result = self.daily_checkin()
            return result
        return False, None
    
    def daily_checkin(self):
        """每日打卡记录（学习满2小时自动触发）"""
        today = datetime.now().date()
        if self.last_checkin_date == today:
            return False, ""  # 今日已打卡
        
        # 检查是否连续
        if self.last_checkin_date == today - timedelta(days=1):
            self.consecutive_days += 1
        else:
            self.consecutive_days = 1
        
        self.last_checkin_date = today
        # 打卡仅记录，不恢复爱心（爱心需通过星星兑换）
        return True, f"今日学习2小时打卡成功！连续{self.consecutive_days}天"
    
    def wrong_answer(self):
        """答题错误处理"""
        self.combo = 0  # 连击中断
        self.stats["total_wrong"] += 1
        
        # 娑堣楃埍蹇衣
        if self.hearts > 0:
            self.use_heart()
            return True, f"鈾衣1锛屽墿浣{self.hearts}鈾衣"
        else:
            return False, "鈾凡鐢题畬锛岃审鏄庡鍐嶆潵鎴栧垎浜型幏寰椻櫏"
    
    def _check_achievements(self):
        """检查苟视频I解锁成"""
        for ach in self.achievement_list:
            if ach["id"] not in [a["id"] for a in self.achievements]:
                if ach["condition"](self):
                    self.achievements.append(ach)
                    return ach  # 杩斿洖未获得閿佺殑成就
        return None
    
    def get_level_progress(self):
        """获取当前等级进度（星星数 + 爱心数，每5心升级的剩余进度）"""
        return self.stars, self.hearts
    
    def get_reward_summary(self):
        """获取奖励系统摘要"""
        return {
            "stars": self.stars,
            "total_stars": self.total_stars_earned,
            "hearts": self.hearts,
            "max_hearts": self.max_hearts,
            "level": self.level,
            "total_hearts_earned": self.total_hearts_earned,
            "progress": self.get_level_progress(),
            "consecutive_days": self.consecutive_days,
            "combo": self.combo,
            "max_combo": self.max_combo,
            "achievements": self.achievements,
        }
    
    def save_data(self):
        """保存奖励数据"""
        data = {
            "stars": self.stars,
            "hearts": self.hearts,
            "level": self.level,
            "total_stars_earned": self.total_stars_earned,
            "total_hearts_earned": self.total_hearts_earned,
            "consecutive_days": self.consecutive_days,
            "last_checkin_date": str(self.last_checkin_date) if self.last_checkin_date else None,
            "achievements": [a["id"] for a in self.achievements],
            "combo": self.combo,
            "max_combo": self.max_combo,
            "stats": self.stats,
            "daily_study_seconds": self.daily_study_seconds,
            "last_save_date": str(datetime.now().date())
        }
        try:
            with open(os.path.join(EXE_DIR, "reward_data.pkl"), "wb") as f:
                pickle.dump(data, f)
        except Exception as e:
            print("Save reward data error:", e)
    
    def load_data(self):
        """加载奖励数据"""
        try:
            with open(os.path.join(EXE_DIR, "reward_data.pkl"), "rb") as f:
                data = pickle.load(f)
            
            self.stars = data.get("stars", 0)
            self.hearts = data.get("hearts", 0)  # 默认0颗爱心
            self.level = data.get("level", 1)
            self.total_stars_earned = data.get("total_stars_earned", 0)
            self.total_hearts_earned = data.get("total_hearts_earned", 0)
            self.consecutive_days = data.get("consecutive_days", 0)
            self.combo = data.get("combo", 0)
            self.max_combo = data.get("max_combo", 0)
            self.stats = data.get("stats", {
                "total_correct": 0,
                "total_wrong": 0,
                "word_correct": 0,
                "phrase_correct": 0,
                "dialogue_correct": 0,
                "grammar_correct": 0,
                "grade7_word_correct": 0,
                "grade8_word_correct": 0,
                "grade9_word_correct": 0,
                "max_combo": 0,
            })
            
            # 学习计时
            self.daily_study_seconds = data.get("daily_study_seconds", 0)
            
            # 读取成就
            unlocked_ids = data.get("achievements", [])
            self.achievements = [a for a in self.achievement_list if a["id"] in unlocked_ids]
            
            # 检查是否新的一天，重置学习时间
            last_save = data.get("last_save_date")
            today = str(datetime.now().date())
            if last_save != today:
                self.daily_study_seconds = 0
                # 检查连续打卡是否中断
                last_date = data.get("last_checkin_date")
                if last_date:
                    last_date = datetime.strptime(last_date, "%Y-%m-%d").date()
                    if last_date != datetime.now().date() - timedelta(days=1):
                        self.consecutive_days = 0
            
            # 读取上次打卡日期
            if data.get("last_checkin_date"):
                self.last_checkin_date = datetime.strptime(
                    data.get("last_checkin_date"), "%Y-%m-%d").date()
                
        except Exception as e:
            print("Load reward data error:", e)
# ==================== 初学者单词库（2,777+，按年级标注）====================
BUILTIN_WORD_LIST = [
    ('able', '能够；有能力的', '九年级'),
    ('about', '关于；大约', '七年级上册'),
    ('above', '在…上方', '七年级下册'),
    ('accept', '接受', '七年级上册'),
    ('accident', '事故', '七年级上册'),
    ('achieve', '取得；实现', '八年级上册'),
    ('across', '横过', '七年级上册'),
    ('act', '行动', '七年级上册'),
    ('active', '活跃的', '七年级下册'),
    ('activity', '活动', '八年级上册'),
    ('actor', '演员', '七年级上册'),
    ('actually', '实际上', '七年级下册'),
    ('add', '增加', '八年级下册'),
    ('address', '地址', '七年级上册'),
    ('advantage', '优势', '九年级'),
    ('advice', '建议', '七年级上册'),
    ('advise', '劝告', '七年级上册'),
    ('afford', '负担得起', '七年级下册'),
    ('afraid', '害怕的', '八年级下册'),
    ('after', '在…之后', '七年级下册'),
    ('afternoon', '下午', '七年级上册'),
    ('again', '又', '七年级上册'),
    ('against', '反对', '七年级上册'),
    ('age', '年龄', '七年级上册'),
    ('ago', '以前', '七年级上册'),
    ('agree', '同意', '八年级上册'),
    ('air', '空气', '七年级上册'),
    ('all', '全部', '七年级上册'),
    ('allow', '允许', '七年级上册'),
    ('almost', '几乎', '八年级上册'),
    ('alone', '单独的', '七年级下册'),
    ('along', '沿着', '七年级上册'),
    ('already', '已经', '七年级上册'),
    ('also', '也', '七年级上册'),
    ('although', '虽然', '八年级上册'),
    ('always', '总是', '七年级上册'),
    ('amazing', '令人惊异的', '八年级上册'),
    ('among', '在…之中', '七年级下册'),
    ('and', '和', '七年级上册'),
    ('angry', '生气的', '七年级下册'),
    ('animal', '动物', '七年级上册'),
    ('another', '另一个', '七年级上册'),
    ('answer', '回答', '七年级上册'),
    ('ant', '蚂蚁', '七年级上册'),
    ('any', '任何的', '七年级下册'),
    ('appear', '出现', '八年级上册'),
    ('apple', '苹果', '七年级上册'),
    ('area', '区域', '七年级上册'),
    ('arm', '手臂', '七年级上册'),
    ('around', '围绕', '七年级上册'),
    ('arrive', '到达', '七年级上册'),
    ('art', '艺术', '七年级上册'),
    ('article', '文章', '八年级上册'),
    ('as', '作为', '七年级上册'),
    ('ask', '问', '七年级上册'),
    ('asleep', '睡着的', '七年级下册'),
    ('at', '在', '七年级上册'),
    ('attend', '参加', '七年级上册'),
    ('attention', '注意力', '八年级下册'),
    ('August', '八月', '七年级下册'),
    ('aunt', '伯母', '八年级上册'),
    ('autumn', '秋天', '七年级下册'),
    ('avoid', '避免', '七年级上册'),
    ('awake', '醒来的', '七年级下册'),
    ('away', '离开', '七年级下册'),
    ('baby', '婴儿', '七年级上册'),
    ('back', '后面', '七年级上册'),
    ('bad', '坏的', '七年级上册'),
    ('bag', '包', '七年级上册'),
    ('ball', '球', '七年级下册'),
    ('banana', '香蕉', '七年级上册'),
    ('bank', '银行', '七年级下册'),
    ('base', '基础', '七年级上册'),
    ('basic', '基本的', '七年级下册'),
    ('basket', '篮子', '七年级上册'),
    ('basketball', '篮球', '七年级下册'),
    ('bathroom', '浴室', '七年级下册'),
    ('be', '是', '七年级上册'),
    ('beach', '海滩', '七年级上册'),
    ('bear', '熊；忍受', '八年级上册'),
    ('beautiful', '美丽的', '七年级下册'),
    ('because', '因为', '七年级上册'),
    ('become', '变成', '七年级上册'),
    ('bed', '床', '七年级上册'),
    ('bedroom', '卧室', '七年级下册'),
    ('bee', '蜜蜂', '七年级上册'),
    ('beef', '牛肉', '七年级上册'),
    ('before', '在…之前', '七年级下册'),
    ('begin', '开始', '七年级下册'),
    ('behind', '在…后面', '七年级下册'),
    ('believe', '相信', '七年级上册'),
    ('bell', '铃', '七年级上册'),
    ('belong', '属于', '七年级上册'),
    ('below', '在…下面', '七年级下册'),
    ('beside', '在…旁边', '七年级下册'),
    ('best', '最好的', '七年级下册'),
    ('better', '更好的', '七年级下册'),
    ('between', '在…之间', '七年级下册'),
    ('big', '大的', '七年级上册'),
    ('bike', '自行车', '七年级下册'),
    ('bill', '账单', '七年级上册'),
    ('bird', '鸟', '七年级上册'),
    ('birth', '出生', '七年级上册'),
    ('birthday', '生日', '七年级上册'),
    ('bit', '一点', '七年级下册'),
    ('black', '黑色的', '七年级上册'),
    ('blackboard', '黑板', '七年级上册'),
    ('blind', '盲的', '七年级上册'),
    ('block', '街区', '七年级上册'),
    ('blood', '血', '七年级上册'),
    ('blow', '吹', '七年级上册'),
    ('blue', '蓝色的', '七年级上册'),
    ('board', '木板', '七年级上册'),
    ('boat', '船', '七年级下册'),
    ('body', '身体', '七年级上册'),
    ('book', '书', '七年级上册'),
    ('boring', '无聊的', '七年级下册'),
    ('born', '出生的', '七年级下册'),
    ('borrow', '借入', '七年级上册'),
    ('boss', '老板', '七年级上册'),
    ('both', '两者都', '七年级下册'),
    ('bottle', '瓶子', '七年级上册'),
    ('bottom', '底部', '七年级上册'),
    ('bowl', '碗', '七年级上册'),
    ('box', '盒子', '七年级上册'),
    ('boy', '男孩', '七年级上册'),
    ('brain', '大脑', '七年级上册'),
    ('brave', '勇敢的', '八年级下册'),
    ('bread', '面包', '七年级上册'),
    ('break', '打破', '七年级上册'),
    ('breakfast', '早餐', '七年级下册'),
    ('bridge', '桥', '七年级上册'),
    ('bright', '明亮的', '七年级下册'),
    ('bring', '带来', '七年级下册'),
    ('brother', '兄弟', '七年级上册'),
    ('brown', '棕色的', '七年级下册'),
    ('brush', '刷子', '七年级上册'),
    ('build', '建造', '七年级上册'),
    ('building', '建筑物', '七年级下册'),
    ('burn', '燃烧', '七年级上册'),
    ('bus', '公共汽车', '八年级下册'),
    ('business', '生意', '七年级上册'),
    ('busy', '忙碌的', '七年级下册'),
    ('but', '但是', '七年级上册'),
    ('butter', '黄油', '七年级上册'),
    ('buy', '购买', '七年级上册'),
    ('by', '通过；靠', '七年级下册'),
    ('cake', '蛋糕', '七年级上册'),
    ('call', '打电话；称呼', '七年级上册'),
    ('camera', '照相机', '七年级下册'),
    ('camp', '营地', '七年级上册'),
    ('can', '能；罐头', '七年级上册'),
    ('candle', '蜡烛', '七年级上册'),
    ('cap', '帽子', '七年级上册'),
    ('car', '汽车', '七年级上册'),
    ('card', '卡片', '七年级上册'),
    ('care', '关心', '七年级上册'),
    ('careful', '小心的', '七年级上册'),
    ('carry', '搬运', '七年级上册'),
    ('cat', '猫', '七年级上册'),
    ('catch', '抓住', '七年级上册'),
    ('cause', '原因；引起', '八年级上册'),
    ('celebrate', '庆祝', '八年级上册'),
    ('cent', '分', '七年级上册'),
    ('center', '中心', '七年级上册'),
    ('century', '世纪', '七年级上册'),
    ('certain', '确定的', '七年级下册'),
    ('chair', '椅子', '七年级上册'),
    ('chance', '机会', '九年级'),
    ('change', '改变', '七年级上册'),
    ('character', '性格；角色', '八年级上册'),
    ('cheap', '便宜的', '七年级下册'),
    ('check', '检查', '九年级'),
    ('cheer', '欢呼', '七年级上册'),
    ('chemistry', '化学', '七年级上册'),
    ('chess', '国际象棋', '七年级下册'),
    ('chicken', '鸡肉；小鸡', '七年级上册'),
    ('child', '孩子', '七年级上册'),
    ('China', '中国', '七年级上册'),
    ('Chinese', '中国人；汉语', '七年级上册'),
    ('choice', '选择', '七年级上册'),
    ('choose', '选择', '七年级上册'),
    ('chopsticks', '筷子', '七年级上册'),
    ('Christmas', '圣诞节', '七年级下册'),
    ('church', '教堂', '七年级上册'),
    ('cinema', '电影院', '七年级下册'),
    ('circle', '圆', '七年级上册'),
    ('city', '城市', '七年级上册'),
    ('class', '班级；课', '七年级上册'),
    ('classmate', '同班同学', '七年级下册'),
    ('classroom', '教室', '七年级上册'),
    ('clean', '干净的；打扫', '七年级下册'),
    ('clear', '清晰的；清理', '八年级上册'),
    ('clever', '聪明的', '七年级下册'),
    ('climb', '爬', '七年级上册'),
    ('clock', '时钟', '七年级上册'),
    ('close', '关闭；接近的', '八年级上册'),
    ('clothes', '衣服', '七年级上册'),
    ('cloud', '云', '七年级上册'),
    ('club', '俱乐部', '七年级下册'),
    ('coach', '教练', '七年级上册'),
    ('coal', '煤', '七年级上册'),
    ('coast', '海岸', '七年级上册'),
    ('coat', '外套', '七年级上册'),
    ('coffee', '咖啡', '七年级上册'),
    ('coin', '硬币', '七年级上册'),
    ('cold', '冷的；感冒', '七年级下册'),
    ('collect', '收集', '七年级上册'),
    ('college', '大学', '七年级上册'),
    ('color', '颜色', '七年级上册'),
    ('come', '来', '七年级上册'),
    ('comfortable', '舒适的', '七年级下册'),
    ('common', '普通的', '九年级'),
    ('communicate', '沟通', '七年级上册'),
    ('community', '社区', '七年级上册'),
    ('company', '公司', '七年级上册'),
    ('compare', '比较', '七年级上册'),
    ('competition', '比赛', '八年级上册'),
    ('complete', '完成；完整的', '八年级上册'),
    ('computer', '电脑', '七年级上册'),
    ('concert', '音乐会', '七年级下册'),
    ('condition', '条件', '七年级上册'),
    ('confident', '自信的', '七年级下册'),
    ('connect', '连接', '七年级上册'),
    ('consider', '考虑', '八年级下册'),
    ('continue', '继续', '七年级上册'),
    ('control', '控制', '七年级上册'),
    ('cook', '烹饪；厨师', '八年级上册'),
    ('cool', '凉爽的；酷', '七年级下册'),
    ('copy', '复制', '七年级上册'),
    ('corner', '角落', '七年级上册'),
    ('correct', '正确的', '九年级'),
    ('cost', '花费', '七年级上册'),
    ('cotton', '棉花', '七年级上册'),
    ('cough', '咳嗽', '七年级上册'),
    ('could', '可以', '七年级上册'),
    ('count', '数数', '七年级上册'),
    ('country', '国家；乡村', '七年级下册'),
    ('couple', '夫妇；几个', '八年级上册'),
    ('courage', '勇气', '七年级上册'),
    ('course', '课程；当然', '八年级上册'),
    ('cousin', '表兄妹', '七年级下册'),
    ('cover', '覆盖', '七年级上册'),
    ('cow', '奶牛', '七年级上册'),
    ('crayon', '蜡笔', '七年级上册'),
    ('crazy', '疯狂的', '七年级下册'),
    ('create', '创造', '七年级上册'),
    ('cross', '穿过', '七年级下册'),
    ('cruel', '残酷的', '七年级下册'),
    ('cry', '哭', '七年级上册'),
    ('culture', '文化', '八年级上册'),
    ('cup', '杯子', '七年级上册'),
    ('cute', '可爱的', '七年级下册'),
    ('dad', '爸爸', '七年级上册'),
    ('daily', '每日的', '七年级下册'),
    ('dance', '跳舞', '七年级下册'),
    ('danger', '危险', '八年级下册'),
    ('dangerous', '危险的', '八年级下册'),
    ('dark', '黑暗的', '七年级下册'),
    ('date', '日期；约会', '八年级上册'),
    ('daughter', '女儿', '七年级上册'),
    ('day', '一天', '七年级上册'),
    ('dead', '死的', '七年级上册'),
    ('deaf', '聋的', '七年级上册'),
    ('deal', '处理；交易', '八年级上册'),
    ('dear', '亲爱的；昂贵的', '八年级下册'),
    ('death', '死亡', '七年级上册'),
    ('December', '十二月', '七年级下册'),
    ('decide', '决定', '八年级上册'),
    ('deep', '深的', '七年级上册'),
    ('deer', '鹿', '七年级上册'),
    ('degree', '度数；学位', '八年级上册'),
    ('good', '好的', '七年级上册'),
    ('morning', '早晨；上午', '七年级下册'),
    ('welcome', '欢迎', '七年级上册'),
    ('to', '向；到', '七年级下册'),
    ('thank', '谢谢', '七年级上册'),
    ('you', '你；你们', '七年级下册'),
    ('hello', '你好', '七年级上册'),
    ('hi', '嗨', '七年级上册'),
    ('I', '我', '七年级上册'),
    ('am', '是', '七年级上册'),
  ("I'm", '我是'),
    ('name', '名字', '七年级上册'),
    ('what', '什么', '七年级上册'),
    ('your', '你的', '七年级上册'),
    ('my', '我的', '七年级上册'),
    ('nice', '令人愉快的', '七年级下册'),
    ('meet', '遇见', '七年级上册'),
    ('too', '也；太', '七年级下册'),
    ('please', '请', '七年级上册'),
    ('excuse', '原谅', '七年级上册'),
    ('me', '我（宾格）', '八年级上册'),
    ('are', '是', '七年级上册'),
    ('yes', '是的', '七年级上册'),
    ('no', '不', '七年级上册'),
    ('it', '它', '七年级上册'),
    ('is', '是', '七年级上册'),
  ("that's", '那是'),
    ('not', '不', '七年级上册'),
    ('from', '来自', '七年级上册'),
    ('where', '哪里', '七年级上册'),
    ('Canada', '加拿大', '七年级下册'),
    ('the', '这/那', '七年级上册'),
    ('USA', '美国', '七年级上册'),
    ('UK', '英国', '七年级上册'),
    ('Japan', '日本', '七年级上册'),
    ('England', '英格兰', '七年级下册'),
    ('they', '他们', '七年级上册'),
    ('he', '他', '七年级上册'),
    ('she', '她', '七年级上册'),
    ('who', '谁', '七年级上册'),
    ('student', '学生', '七年级上册'),
    ('teacher', '老师', '七年级上册'),
    ('Mr.', '先生', '七年级上册'),
    ('Miss', '小姐', '七年级上册'),
    ('Ms.', '女士', '七年级上册'),
    ('Mrs.', '夫人', '七年级上册'),
    ('friend', '朋友', '七年级上册'),
    ('pen pal', '笔友', '七年级上册'),
    ('how', '怎样', '七年级上册'),
    ('old', '老的；...岁', '七年级上册'),
    ('number', '数字', '七年级上册'),
    ('one', '一', '七年级上册'),
    ('two', '二', '七年级上册'),
    ('three', '三', '七年级上册'),
    ('four', '四', '七年级上册'),
    ('five', '五', '七年级上册'),
    ('six', '六', '七年级上册'),
    ('seven', '七', '七年级上册'),
    ('eight', '八', '七年级上册'),
    ('nine', '九', '七年级上册'),
    ('ten', '十', '七年级上册'),
    ('eleven', '十一', '七年级上册'),
    ('twelve', '十二', '七年级上册'),
    ('thirteen', '十三', '七年级上册'),
    ('fourteen', '十四', '七年级上册'),
    ('fifteen', '十五', '七年级上册'),
    ('sixteen', '十六', '七年级上册'),
    ('seventeen', '十七', '七年级上册'),
    ('eighteen', '十八', '七年级上册'),
    ('nineteen', '十九', '七年级上册'),
    ('twenty', '二十', '七年级上册'),
    ('year', '年', '七年级上册'),
    ('years old', '岁', '七年级上册'),
    ('grade', '年级', '七年级上册'),
    ('in', '在...里面', '八年级上册'),
    ('an', '一个', '七年级上册'),
    ('eraser', '橡皮', '七年级上册'),
    ('map', '地图', '七年级上册'),
    ('pen', '钢笔', '七年级上册'),
    ('pencil', '铅笔', '七年级上册'),
    ('ruler', '尺子', '七年级上册'),
    ('desk', '书桌', '七年级上册'),
    ('school', '学校', '七年级上册'),
    ('have', '有', '七年级上册'),
    ('has', '有（第三人称单数）', '九年级'),
    ('small', '小的', '七年级上册'),
    ('long', '长的', '七年级上册'),
    ('short', '短的；矮的', '七年级上册'),
    ('hair', '头发', '七年级上册'),
    ('face', '脸', '七年级上册'),
    ('eye', '眼睛', '七年级上册'),
    ('ear', '耳朵', '七年级上册'),
    ('nose', '鼻子', '七年级上册'),
    ('mouth', '嘴巴', '七年级上册'),
    ('head', '头', '七年级上册'),
    ('neck', '脖子', '七年级上册'),
    ('hand', '手', '七年级上册'),
    ('leg', '腿', '七年级上册'),
    ('foot', '脚', '七年级上册'),
    ('feet', '脚（复数）', '七年级上册'),
    ('finger', '手指', '七年级上册'),
    ('wide', '宽的', '七年级上册'),
    ('round', '圆的', '七年级上册'),
    ('favorite', '最喜欢的', '七年级下册'),
    ('actress', '女演员', '七年级下册'),
    ('singer', '歌手', '七年级下册'),
    ('player', '选手', '七年级上册'),
    ('star', '明星', '七年级上册'),
    ('English', '英语', '七年级上册'),
    ('knife', '小刀', '七年级上册'),
    ('white', '白色', '七年级上册'),
    ('pink', '粉色', '七年级上册'),
    ('red', '红色', '七年级上册'),
    ('purple', '紫色', '七年级上册'),
    ('orange', '橙色', '七年级上册'),
    ('yellow', '黄色', '七年级上册'),
    ('green', '绿色', '七年级上册'),
    ('gray', '灰色', '七年级上册'),
    ('blond', '金色的', '七年级下册'),
    ('give', '给', '七年级上册'),
    ('letter', '信；字母', '七年级下册'),
    ('sorry', '抱歉', '七年级上册'),
    ('like', '喜欢', '七年级上册'),
    ('look', '看', '七年级下册'),
    ('same', '相同的', '七年级下册'),
    ('tall', '高的', '七年级上册'),
    ('know', '知道', '七年级上册'),
    ('new', '新的', '七年级上册'),
    ('parent', '父/母亲', '七年级上册'),
    ('mother', '母亲', '七年级上册'),
    ('father', '父亲', '七年级上册'),
    ('sister', '姐妹', '七年级上册'),
    ('grandmother', '祖母', '七年级上册'),
    ('grandfather', '祖父', '七年级上册'),
    ('grandparent', '祖父母', '七年级下册'),
    ('son', '儿子', '七年级上册'),
    ('uncle', '叔叔；舅舅', '八年级上册'),
    ('wife', '妻子', '七年级上册'),
    ('husband', '丈夫', '七年级上册'),
    ('family', '家庭', '七年级下册'),
    ('home', '家', '七年级下册'),
    ('photo', '照片', '七年级上册'),
    ('picture', '图片', '七年级上册'),
    ('so', '如此；所以', '八年级上册'),
    ('happy', '快乐的', '七年级下册'),
    ('sad', '悲伤的', '七年级下册'),
    ('only', '仅仅', '七年级上册'),
    ('young', '年轻的', '七年级上册'),
    ('right', '正确的；右边', '九年级'),
    ('then', '那么；然后', '七年级下册'),
    ('work', '工作', '七年级上册'),
    ('hospital', '医院', '七年级下册'),
    ('restaurant', '餐馆', '七年级上册'),
    ('shop', '商店', '七年级下册'),
    ('office', '办公室', '七年级下册'),
    ('farm', '农场', '七年级上册'),
    ('driver', '司机', '七年级上册'),
    ('farmer', '农民', '七年级上册'),
    ('nurse', '护士', '七年级上册'),
    ('doctor', '医生', '七年级上册'),
    ('worker', '工人', '七年级上册'),
    ('teach', '教', '七年级上册'),
    ('drive', '驾驶', '七年级上册'),
    ('job', '工作', '七年级上册'),
    ('time', '时间', '七年级下册'),
  ("o'clock", '点钟'),
    ('past', '过', '七年级上册'),
    ('half', '一半', '七年级下册'),
    ('quarter', '一刻钟', '七年级下册'),
    ('now', '现在', '七年级下册'),
    ('early', '早的', '七年级下册'),
    ('late', '迟的', '七年级上册'),
    ('watch', '手表；观看', '七年级下册'),
    ('TV', '电视', '七年级下册'),
    ('living room', '客厅', '七年级下册'),
    ('kitchen', '厨房', '七年级下册'),
    ('garden', '花园', '七年级上册'),
    ('dining room', '餐厅', '七年级上册'),
    ('floor', '地板；楼层', '八年级上册'),
    ('first', '第一', '七年级上册'),
    ('second', '第二', '七年级上册'),
    ('third', '第三', '七年级上册'),
    ('next', '下一个', '七年级上册'),
    ('today', '今天', '七年级下册'),
    ('tomorrow', '明天', '七年级下册'),
    ('Sunday', '星期日', '七年级下册'),
    ('Monday', '星期一', '七年级下册'),
    ('Tuesday', '星期二', '七年级下册'),
    ('Wednesday', '星期三', '七年级下册'),
    ('Thursday', '星期四', '七年级下册'),
    ('Friday', '星期五', '七年级下册'),
    ('Saturday', '星期六', '七年级下册'),
    ('week', '周', '七年级上册'),
    ('weekend', '周末', '七年级上册'),
    ('picnic', '野餐', '七年级上册'),
    ('homework', '作业', '七年级上册'),
    ('zoo', '动物园', '七年级下册'),
    ('park', '公园', '七年级上册'),
    ('library', '图书馆', '七年级上册'),
    ('supermarket', '超市', '七年级上册'),
    ('play', '玩；打', '七年级下册'),
    ('go', '去', '七年级上册'),
    ('get', '得到', '七年级上册'),
    ('let', '让', '七年级上册'),
    ('make', '使；做', '七年级下册'),
    ('want', '想要', '七年级上册'),
    ('would', '愿意', '七年级上册'),
    ('would like', '想要', '七年级上册'),
    ('sure', '当然', '七年级上册'),
    ('often', '经常', '七年级上册'),
    ('usually', '通常', '七年级下册'),
    ('never', '从不', '七年级上册'),
    ('sometimes', '有时', '七年级上册'),
    ('wake', '醒来', '七年级上册'),
    ('term', '学期', '七年级上册'),
    ('must', '必须', '七年级上册'),
    ('still', '仍然', '七年级上册'),
    ('on foot', '步行', '七年级上册'),
    ('subway', '地铁', '七年级下册'),
    ('ship', '轮船', '七年级下册'),
    ('sea', '海', '七年级上册'),
    ('train', '火车', '七年级下册'),
    ('plane', '飞机', '七年级下册'),
    ('gate', '大门', '七年级上册'),
    ('stop', '停止；车站', '八年级上册'),
    ('wait', '等待', '七年级上册'),
    ('walk', '步行', '七年级上册'),
    ('ride', '骑', '七年级下册'),
    ('take', '乘坐', '七年级上册'),
    ('finish', '结束', '七年级上册'),
    ('lesson', '课', '七年级上册'),
    ('subject', '科目', '七年级上册'),
    ('math', '数学', '七年级上册'),
    ('history', '历史', '七年级上册'),
    ('physics', '物理', '七年级上册'),
    ('geography', '地理', '七年级上册'),
    ('biology', '生物', '七年级上册'),
    ('politics', '政治', '七年级上册'),
    ('P.E.', '体育', '七年级上册'),
    ('music', '音乐', '七年级下册'),
    ('science', '科学', '八年级下册'),
    ('easy', '容易的', '七年级下册'),
    ('difficult', '困难的', '七年级下册'),
    ('interesting', '有趣的', '七年级下册'),
    ('important', '重要的', '八年级下册'),
    ('meeting', '会议', '七年级上册'),
    ('flag', '旗帜', '七年级上册'),
    ('raise', '升起', '七年级上册'),
    ('turn', '转弯', '七年级上册'),
    ('crossing', '十字路口', '七年级下册'),
    ('street', '街道', '七年级上册'),
    ('road', '路', '七年级上册'),
    ('avenue', '大道', '七年级上册'),
    ('left', '左边', '七年级上册'),
    ('north', '北', '七年级上册'),
    ('south', '南', '七年级上册'),
    ('east', '东', '七年级上册'),
    ('west', '西', '七年级上册'),
    ('neighbor', '邻居', '七年级上册'),
    ('neighborhood', '社区', '七年级上册'),
    ('store', '商店', '七年级下册'),
    ('museum', '博物馆', '七年级下册'),
    ('post office', '邮局', '七年级下册'),
    ('bookstore', '书店', '七年级上册'),
    ('parking lot', '停车场', '七年级下册'),
    ('railway station', '火车站', '七年级下册'),
    ('airport', '机场', '七年级上册'),
    ('hotel', '旅馆', '七年级上册'),
    ('room', '房间', '七年级下册'),
    ('door', '门', '七年级上册'),
    ('window', '窗户', '七年级上册'),
    ('wall', '墙', '七年级上册'),
    ('table', '桌子', '七年级上册'),
    ('sofa', '沙发', '七年级上册'),
    ('lamp', '灯', '七年级上册'),
    ('key', '钥匙', '七年级上册'),
    ('put', '放', '七年级下册'),
    ('move', '移动', '七年级上册'),
    ('party', '聚会', '七年级上册'),
    ('month', '月份', '七年级下册'),
    ('January', '一月', '七年级下册'),
    ('February', '二月', '七年级下册'),
    ('March', '三月', '七年级下册'),
    ('April', '四月', '七年级下册'),
    ('May', '五月', '七年级下册'),
    ('June', '六月', '七年级下册'),
    ('July', '七月', '七年级下册'),
    ('September', '九月', '七年级下册'),
    ('October', '十月', '七年级下册'),
    ('November', '十一月', '七年级下册'),
    ('calendar', '日历', '七年级上册'),
    ('plan', '计划', '八年级上册'),
    ('present', '礼物', '七年级上册'),
    ('song', '歌曲', '七年级下册'),
    ('sing', '唱歌', '七年级下册'),
    ('perform', '表演', '七年级上册'),
    ('magic', '魔术', '七年级上册'),
    ('trick', '戏法', '七年级上册'),
    ('wish', '祝愿', '七年级上册'),
    ('cut', '切', '七年级上册'),
    ('tell', '告诉', '七年级上册'),
    ('speak', '说', '七年级上册'),
    ('say', '说', '七年级上册'),
    ('talk', '谈话', '七年级上册'),
    ('measure', '测量', '七年级上册'),
    ('weigh', '称重', '七年级上册'),
    ('size', '尺寸；尺码', '七年级上册'),
    ('shape', '形状', '七年级上册'),
    ('square', '正方形', '七年级下册'),
    ('triangle', '三角形', '七年级下册'),
    ('season', '季节', '七年级下册'),
    ('weather', '天气', '七年级下册'),
    ('spring', '春天', '七年级下册'),
    ('summer', '夏天', '七年级下册'),
    ('winter', '冬天', '七年级下册'),
    ('warm', '温暖的', '七年级下册'),
    ('hot', '热的', '七年级下册'),
    ('cloudy', '多云的', '七年级下册'),
    ('sunny', '晴朗的', '七年级下册'),
    ('rainy', '下雨的', '七年级下册'),
    ('snowy', '下雪的', '七年级下册'),
    ('windy', '有风的', '七年级下册'),
    ('foggy', '有雾的', '七年级下册'),
    ('rain', '雨；下雨', '七年级下册'),
    ('snow', '雪；下雪', '七年级下册'),
    ('wind', '风', '七年级下册'),
    ('sun', '太阳', '七年级上册'),
    ('moon', '月亮', '七年级下册'),
    ('sky', '天空', '七年级上册'),
    ('temperature', '温度', '七年级上册'),
    ('low', '低的', '七年级上册'),
    ('high', '高的', '七年级上册'),
    ('holiday', '假期', '八年级上册'),
    ('trip', '旅行', '七年级上册'),
    ('travel', '旅游', '七年级上册'),
    ('visit', '参观', '七年级上册'),
    ('place', '地方', '七年级上册'),
    ('mountain', '山', '七年级上册'),
    ('river', '河流', '七年级上册'),
    ('lake', '湖', '七年级上册'),
    ('forest', '森林', '七年级上册'),
    ('field', '田野', '七年级上册'),
    ('wear', '穿', '七年级下册'),
    ('jacket', '夹克', '七年级上册'),
    ('sweater', '毛衣', '七年级上册'),
    ('scarf', '围巾', '七年级上册'),
    ('glove', '手套', '七年级上册'),
    ('hat', '帽子', '七年级上册'),
    ('shoe', '鞋子', '七年级上册'),
    ('sport', '运动', '七年级下册'),
    ('game', '游戏；比赛', '八年级上册'),
    ('volleyball', '排球', '七年级下册'),
    ('tennis', '网球', '七年级下册'),
    ('badminton', '羽毛球', '七年级下册'),
    ('table tennis', '乒乓球', '七年级下册'),
    ('soccer', '足球', '七年级下册'),
    ('football', '足球', '七年级下册'),
    ('baseball', '棒球', '七年级下册'),
    ('golf', '高尔夫', '七年级上册'),
    ('swimming', '游泳', '七年级下册'),
    ('running', '跑步', '七年级下册'),
    ('jumping', '跳跃', '七年级下册'),
    ('cycling', '骑自行车', '七年级下册'),
    ('rowing', '划船', '七年级下册'),
    ('skating', '滑冰', '七年级上册'),
    ('skiing', '滑雪', '七年级下册'),
    ('climbing', '爬山', '七年级上册'),
    ('hiking', '徒步', '七年级上册'),
    ('win', '赢', '七年级上册'),
    ('lose', '输', '七年级上册'),
    ('team', '队', '七年级上册'),
    ('race', '比赛', '八年级上册'),
    ('record', '记录', '七年级上册'),
    ('gold', '金牌', '七年级上册'),
    ('silver', '银牌', '七年级上册'),
    ('bronze', '铜牌', '七年级上册'),
    ('medal', '奖牌', '七年级上册'),
    ('champion', '冠军', '七年级上册'),
    ('event', '项目', '八年级下册'),
    ('practice', '练习', '八年级上册'),
    ('exercise', '锻炼', '八年级上册'),
    ('training', '训练', '七年级上册'),
    ('fit', '健康的', '八年级上册'),
    ('health', '健康', '八年级上册'),
    ('healthy', '健康的', '八年级上册'),
    ('strong', '强壮的', '七年级下册'),
    ('weak', '虚弱的', '七年级下册'),
    ('join', '加入', '七年级上册'),
    ('spend', '花费', '七年级上册'),
    ('prefer', '更喜欢', '七年级下册'),
    ('quite', '相当', '七年级上册'),
    ('ill', '生病的', '七年级下册'),
    ('sick', '生病的', '七年级下册'),
    ('disease', '疾病', '七年级上册'),
    ('fever', '发烧', '七年级上册'),
    ('headache', '头痛', '七年级上册'),
    ('toothache', '牙痛', '七年级上册'),
    ('stomachache', '胃痛', '七年级上册'),
    ('backache', '背痛', '七年级上册'),
    ('sore', '疼痛的', '七年级下册'),
    ('pain', '疼痛', '七年级上册'),
    ('hurt', '伤害', '七年级上册'),
    ('symptom', '症状', '七年级上册'),
    ('medicine', '药', '八年级下册'),
    ('pill', '药片', '八年级下册'),
    ('tablet', '药片', '八年级下册'),
    ('drug', '药物', '八年级下册'),
    ('prescription', '处方', '七年级上册'),
    ('patient', '病人', '八年级下册'),
    ('examine', '检查', '九年级'),
    ('suggest', '建议', '七年级上册'),
    ('lie', '躺', '七年级上册'),
    ('rest', '休息', '七年级上册'),
    ('stay', '停留', '七年级上册'),
    ('lift', '举起', '七年级上册'),
    ('tooth', '牙齿', '七年级上册'),
    ('teeth', '牙齿（复数）', '八年级上册'),
    ('prevent', '预防', '七年级上册'),
    ('smoke', '吸烟', '七年级上册'),
    ('drink', '喝', '七年级下册'),
    ('alcohol', '酒精', '七年级上册'),
    ('habit', '习惯', '七年级上册'),
    ('enough', '足够的', '八年级上册'),
    ('less', '更少', '七年级上册'),
    ('more', '更多', '七年级上册'),
    ('serious', '严重的', '八年级上册'),
    ('terrible', '糟糕的', '七年级下册'),
    ('worry', '担心', '八年级下册'),
    ('hobby', '爱好', '七年级上册'),
    ('interest', '兴趣', '七年级上册'),
    ('interested', '感兴趣的', '七年级下册'),
    ('collection', '收藏', '七年级上册'),
    ('stamp', '邮票', '八年级上册'),
    ('model', '模型', '七年级上册'),
    ('toy', '玩具', '七年级下册'),
    ('doll', '玩偶', '七年级下册'),
    ('robot', '机器人', '七年级下册'),
    ('paint', '绘画', '七年级上册'),
    ('painting', '画', '七年级上册'),
    ('draw', '画', '七年级上册'),
    ('drawing', '素描', '七年级上册'),
    ('photograph', '照片', '七年级上册'),
    ('photography', '摄影', '七年级上册'),
    ('read', '阅读', '七年级下册'),
    ('write', '写', '七年级下册'),
    ('story', '故事', '七年级上册'),
    ('poem', '诗歌', '七年级下册'),
    ('novel', '小说', '七年级上册'),
    ('magazine', '杂志', '八年级上册'),
    ('newspaper', '报纸', '八年级上册'),
    ('instrument', '乐器', '七年级上册'),
    ('piano', '钢琴', '七年级下册'),
    ('guitar', '吉他', '七年级下册'),
    ('violin', '小提琴', '七年级下册'),
    ('drum', '鼓', '七年级上册'),
    ('movie', '电影', '七年级下册'),
    ('film', '电影', '七年级下册'),
    ('theater', '剧院', '七年级上册'),
    ('show', '演出', '七年级上册'),
    ('tour', '旅游', '七年级上册'),
    ('journey', '旅程', '七年级上册'),
    ('adventure', '冒险', '七年级上册'),
    ('outdoor', '户外的', '七年级下册'),
    ('indoor', '室内的', '七年级下册'),
    ('free', '空闲的', '七年级下册'),
    ('spare', '空闲的', '七年级下册'),
    ('world', '世界', '七年级上册'),
    ('nation', '国家；民族', '七年级下册'),
    ('capital', '首都', '七年级上册'),
    ('population', '人口', '八年级下册'),
    ('language', '语言', '七年级上册'),
    ('custom', '习俗', '七年级上册'),
    ('tradition', '传统', '八年级上册'),
    ('famous', '著名的', '八年级上册'),
    ('popular', '流行的', '八年级上册'),
    ('develop', '发展', '八年级下册'),
    ('developed', '发达的', '七年级下册'),
    ('developing', '发展中的', '八年级下册'),
    ('modern', '现代的', '七年级下册'),
    ('ancient', '古代的', '七年级下册'),
    ('monument', '纪念碑', '七年级下册'),
    ('palace', '宫殿', '七年级上册'),
    ('tower', '塔', '七年级上册'),
    ('castle', '城堡', '七年级上册'),
    ('temple', '寺庙', '七年级上册'),
    ('nature', '自然', '七年级上册'),
    ('environment', '环境', '八年级下册'),
    ('protect', '保护', '七年级上册'),
    ('pollution', '污染', '八年级下册'),
    ('plant', '植物', '七年级上册'),
    ('ocean', '海洋', '七年级上册'),
    ('island', '岛屿', '七年级上册'),
    ('desert', '沙漠', '七年级上册'),
    ('climate', '气候', '七年级上册'),
    ('technology', '技术', '八年级下册'),
    ('information', '信息', '八年级上册'),
    ('message', '消息', '八年级上册'),
    ('email', '电子邮件', '七年级下册'),
    ('website', '网站', '八年级上册'),
    ('feeling', '感觉', '八年级上册'),
    ('excite', '使兴奋', '七年级下册'),
    ('excited', '兴奋的', '七年级下册'),
    ('exciting', '令人兴奋的', '八年级上册'),
    ('nervous', '紧张的', '八年级下册'),
    ('calm', '冷静的', '七年级下册'),
    ('relaxed', '放松的', '七年级下册'),
    ('pleased', '满意的', '七年级下册'),
    ('satisfied', '满意的', '七年级下册'),
    ('disappointed', '失望的', '七年级下册'),
    ('surprised', '惊讶的', '七年级下册'),
    ('amazed', '惊奇的', '七年级下册'),
    ('tired', '疲倦的', '七年级下册'),
    ('lonely', '孤独的', '七年级下册'),
    ('shy', '害羞的', '七年级下册'),
    ('proud', '骄傲的', '九年级'),
    ('silly', '愚蠢的', '七年级下册'),
    ('laugh', '笑', '七年级上册'),
    ('smile', '微笑', '七年级上册'),
    ('shout', '大喊', '七年级上册'),
    ('clap', '鼓掌', '七年级上册'),
    ('express', '表达', '七年级上册'),
    ('emotion', '情绪', '七年级上册'),
    ('mood', '心情', '七年级上册'),
    ('attitude', '态度', '七年级上册'),
    ('comfort', '安慰', '七年级上册'),
    ('encourage', '鼓励', '八年级下册'),
    ('support', '支持', '八年级下册'),
    ('understand', '理解', '七年级上册'),
    ('disagree', '不同意', '八年级上册'),
    ('refuse', '拒绝', '八年级上册'),
    ('tourist', '游客', '七年级上册'),
    ('traveler', '旅行者', '七年级下册'),
    ('passenger', '乘客', '七年级上册'),
    ('guide', '导游', '七年级上册'),
    ('destination', '目的地', '七年级下册'),
    ('route', '路线', '七年级上册'),
    ('schedule', '日程', '七年级上册'),
    ('ticket', '票', '八年级上册'),
    ('passport', '护照', '七年级上册'),
    ('visa', '签证', '七年级上册'),
    ('luggage', '行李', '七年级上册'),
    ('suitcase', '手提箱', '七年级上册'),
    ('pack', '打包', '七年级上册'),
    ('unpack', '拆包', '七年级上册'),
    ('depart', '出发', '七年级上册'),
    ('return', '返回', '七年级上册'),
    ('reach', '到达', '七年级上册'),
    ('station', '车站', '七年级上册'),
    ('port', '港口', '七年级上册'),
    ('terminal', '终点站', '七年级下册'),
    ('motel', '汽车旅馆', '七年级下册'),
    ('hostel', '青年旅舍', '七年级下册'),
    ('reserve', '预订', '七年级上册'),
    ('sightseeing', '观光', '七年级上册'),
    ('explore', '探索', '七年级上册'),
    ('experience', '经历', '七年级上册'),
    ('scenery', '风景', '七年级下册'),
    ('landscape', '景观', '七年级上册'),
    ('view', '景色', '七年级上册'),
    ('souvenir', '纪念品', '七年级下册'),
    ('gift', '礼物', '七年级上册'),
    ('memory', '记忆', '七年级上册'),
    ('recommend', '推荐', '九年级'),
    ('food', '食物', '七年级上册'),
    ('meal', '餐', '七年级上册'),
    ('lunch', '午餐', '七年级下册'),
    ('dinner', '晚餐', '七年级下册'),
    ('snack', '零食', '七年级上册'),
    ('dessert', '甜点', '七年级下册'),
    ('rice', '米饭', '七年级上册'),
    ('noodle', '面条', '七年级上册'),
    ('dumpling', '饺子', '七年级上册'),
    ('soup', '汤', '七年级上册'),
    ('porridge', '粥', '七年级上册'),
    ('salad', '沙拉', '七年级上册'),
    ('sandwich', '三明治', '七年级下册'),
    ('hamburger', '汉堡', '七年级上册'),
    ('pizza', '披萨', '七年级上册'),
    ('hot dog', '热狗', '七年级下册'),
    ('fries', '薯条', '七年级上册'),
    ('meat', '肉', '七年级上册'),
    ('pork', '猪肉', '七年级上册'),
    ('fish', '鱼', '七年级上册'),
    ('seafood', '海鲜', '七年级上册'),
    ('vegetable', '蔬菜', '七年级上册'),
    ('fruit', '水果', '七年级上册'),
    ('orange', '橙子', '七年级上册'),
    ('grape', '葡萄', '七年级上册'),
    ('tomato', '西红柿', '七年级下册'),
    ('potato', '土豆', '七年级上册'),
    ('carrot', '胡萝卜', '七年级下册'),
    ('cabbage', '卷心菜', '七年级下册'),
    ('boil', '煮', '七年级下册'),
    ('fry', '煎炸', '七年级上册'),
    ('steam', '蒸', '七年级上册'),
    ('bake', '烤', '七年级上册'),
    ('taste', '尝起来', '八年级上册'),
    ('smell', '闻起来', '八年级上册'),
    ('delicious', '美味的', '七年级下册'),
    ('yummy', '好吃的', '七年级下册'),
    ('sweet', '甜的', '七年级上册'),
    ('sour', '酸的', '七年级上册'),
    ('bitter', '苦的', '七年级上册'),
    ('spicy', '辣的', '七年级上册'),
    ('salty', '咸的', '七年级上册'),
    ('fresh', '新鲜的', '七年级上册'),
    ('junk food', '垃圾食品', '七年级下册'),
    ('clothing', '服装', '七年级上册'),
    ('try on', '试穿', '七年级下册'),
    ('style', '风格', '七年级下册'),
    ('design', '设计', '七年级上册'),
    ('fashion', '时尚', '七年级上册'),
    ('trendy', '时髦的', '七年级下册'),
    ('classic', '经典的', '七年级下册'),
    ('shirt', '衬衫', '七年级上册'),
    ('blouse', '女衬衫', '七年级下册'),
    ('T-shirt', 'T恤', '七年级上册'),
    ('vest', '背心', '七年级上册'),
    ('suit', '西装', '七年级上册'),
    ('jeans', '牛仔裤', '七年级上册'),
    ('pants', '裤子', '七年级上册'),
    ('trousers', '长裤', '七年级上册'),
    ('shorts', '短裤', '七年级上册'),
    ('skirt', '裙子', '七年级上册'),
    ('dress', '连衣裙', '七年级下册'),
    ('uniform', '制服', '七年级上册'),
    ('costume', '服装', '七年级上册'),
    ('boot', '靴子', '七年级上册'),
    ('sneaker', '运动鞋', '七年级下册'),
    ('sandal', '凉鞋', '七年级下册'),
    ('sock', '袜子', '七年级上册'),
    ('stocking', '长袜', '七年级上册'),
    ('belt', '腰带', '七年级下册'),
    ('tie', '领带', '七年级下册'),
    ('pocket', '口袋', '七年级上册'),
    ('button', '纽扣', '七年级上册'),
    ('zipper', '拉链', '七年级上册'),
    ('material', '材料', '七年级上册'),
    ('wool', '羊毛', '七年级上册'),
    ('silk', '丝绸', '七年级上册'),
    ('leather', '皮革', '七年级上册'),
    ('rapid', '快速的', '七年级下册'),
    ('proper', '恰当的', '七年级下册'),
    ('volunteer', '志愿者', '八年级下册'),
    ('grand', '宏伟的', '七年级下册'),
    ('grandpa', '爷爷', '七年级上册'),
    ('grandma', '奶奶', '七年级上册'),
    ('grandchild', '孙辈', '七年级上册'),
    ('grandson', '孙子', '七年级上册'),
    ('granddaughter', '孙女', '七年级上册'),
    ('relative', '亲戚', '八年级上册'),
    ('communication', '交流', '九年级'),
    ('postcard', '明信片', '七年级下册'),
    ('telegram', '电报', '七年级上册'),
    ('fax', '传真', '七年级上册'),
    ('cellphone', '手机', '七年级上册'),
    ('mobile phone', '手机', '七年级上册'),
    ('telephone', '电话', '七年级上册'),
    ('online', '在线', '八年级上册'),
    ('progress', '进步', '七年级上册'),
    ('success', '成功', '九年级'),
    ('successful', '成功的', '九年级'),
    ('reform', '改革', '七年级上册'),
    ('opening', '开放', '七年级下册'),
    ('policy', '政策', '七年级上册'),
    ('economy', '经济', '七年级上册'),
    ('society', '社会', '八年级下册'),
    ('education', '教育', '九年级'),
    ('medical', '医疗的', '七年级下册'),
    ('provide', '提供', '八年级下册'),
    ('offer', '提供', '八年级下册'),
    ('save', '拯救；节省', '八年级上册'),
    ('protection', '保护', '七年级上册'),
    ('pollute', '污染', '八年级下册'),
    ('waste', '浪费；废物', '八年级上册'),
    ('rubbish', '垃圾', '七年级上册'),
    ('garbage', '垃圾', '七年级上册'),
    ('trash', '垃圾', '七年级上册'),
    ('litter', '垃圾', '七年级上册'),
    ('dustbin', '垃圾箱', '七年级下册'),
    ('recycle', '回收', '七年级上册'),
    ('reuse', '再利用', '七年级下册'),
    ('reduce', '减少', '八年级下册'),
    ('plastic', '塑料', '七年级上册'),
    ('paper', '纸', '七年级上册'),
    ('energy', '能源', '七年级上册'),
    ('electricity', '电', '七年级上册'),
    ('power', '电力；力量', '八年级上册'),
    ('water', '水', '七年级上册'),
    ('resource', '资源', '七年级上册'),
    ('natural', '自然的', '七年级下册'),
    ('harm', '伤害', '七年级上册'),
    ('harmful', '有害的', '七年级下册'),
    ('safe', '安全的', '八年级下册'),
    ('safety', '安全', '八年级下册'),
    ('cut down', '砍伐', '七年级上册'),
    ('tree', '树', '七年级上册'),
    ('grass', '草', '七年级上册'),
    ('dirty', '脏的', '七年级下册'),
    ('low-carbon', '低碳的', '七年级下册'),
    ('lifestyle', '生活方式', '八年级上册'),
    ('action', '行动', '七年级上册'),
    ('take action', '采取行动', '七年级下册'),
    ('make a difference', '产生影响', '七年级下册'),
    ('global', '全球的', '七年级下册'),
    ('warming', '变暖', '七年级下册'),
    ('rise', '上升', '七年级上册'),
    ('spoken', '口语的', '七年级下册'),
    ('written', '书面的', '七年级上册'),
    ('native', '本地的', '七年级下册'),
    ('foreign', '外国的', '七年级下册'),
    ('official', '官方的', '七年级下册'),
    ('international', '国际的', '七年级下册'),
    ('understanding', '理解', '七年级上册'),
    ('translate', '翻译', '七年级上册'),
    ('translation', '翻译', '七年级上册'),
    ('interpreter', '口译员', '七年级下册'),
    ('translator', '翻译员', '七年级下册'),
    ('pronunciation', '发音', '七年级上册'),
    ('pronounce', '发音', '七年级上册'),
    ('accent', '口音', '七年级上册'),
    ('dialect', '方言', '七年级上册'),
    ('grammar', '语法', '七年级上册'),
    ('vocabulary', '词汇', '七年级上册'),
    ('word', '单词', '七年级上册'),
    ('phrase', '短语', '七年级上册'),
    ('sentence', '句子', '七年级上册'),
    ('paragraph', '段落', '七年级上册'),
    ('passage', '段落', '七年级上册'),
    ('text', '课文', '七年级上册'),
    ('composition', '作文', '七年级上册'),
    ('writing', '写作', '七年级下册'),
    ('reading', '阅读', '七年级下册'),
    ('listening', '听力', '七年级上册'),
    ('speaking', '口语', '七年级上册'),
    ('skill', '技能', '九年级'),
    ('ability', '能力', '九年级'),
    ('improve', '提高', '七年级上册'),
    ('master', '掌握', '七年级上册'),
    ('learn', '学习', '七年级上册'),
    ('study', '学习', '七年级上册'),
    ('review', '复习', '七年级上册'),
    ('remember', '记住', '七年级上册'),
    ('forget', '忘记', '七年级上册'),
    ('dictionary', '词典', '七年级上册'),
    ('reference', '参考', '七年级上册'),
    ('difference', '差异', '七年级上册'),
    ('similar', '相似的', '七年级下册'),
    ('funny', '有趣的', '七年级下册'),
    ('swim', '游泳', '七年级下册'),
    ('musician', '音乐家', '七年级下册'),
    ('help', '帮助', '七年级上册'),
    ('dream', '梦想', '七年级上册'),
    ('grow', '成长', '七年级上册'),
    ('scientist', '科学家', '八年级下册'),
    ('future', '将来', '七年级上册'),
    ('friendly', '友好的', '七年级下册'),
    ('excellent', '杰出的', '七年级下册'),
    ('fantastic', '极好的', '七年级下册'),
    ('lab', '实验室', '八年级下册'),
    ('hall', '大厅', '七年级上册'),
    ('matter', '问题', '七年级上册'),
    ('stomach', '胃', '七年级上册'),
    ('trouble', '麻烦', '七年级上册'),
    ('risk', '风险', '七年级下册'),
    ('decision', '决定', '八年级上册'),
    ('importance', '重要性', '八年级下册'),
    ('disabled', '残疾的', '七年级下册'),
    ('repair', '修理', '七年级上册'),
    ('development', '发展', '八年级下册'),
    ('research', '研究', '八年级下册'),
    ('countryside', '农村', '七年级上册'),
    ('horse', '马', '七年级上册'),
    ('exchange', '交换', '七年级上册'),
    ('abroad', '国外', '七年级上册'),
    ('according', '根据', '七年级上册'),
    ('ahead', '向前', '七年级上册'),
    ('aloud', '大声地', '七年级上册'),
    ('anger', '愤怒', '七年级上册'),
    ('anyone', '任何人', '七年级下册'),
    ('anything', '任何事', '七年级下册'),
    ('anyway', '无论如何', '七年级下册'),
    ('anywhere', '任何地方', '七年级下册'),
    ('argue', '争论', '七年级上册'),
    ('astronaut', '宇航员', '七年级下册'),
    ('attract', '吸引', '七年级上册'),
    ('audience', '观众', '七年级上册'),
    ('badly', '严重地', '八年级上册'),
    ('balloon', '气球', '七年级下册'),
    ('bamboo', '竹子', '七年级上册'),
    ('bath', '洗澡', '七年级下册'),
    ('battery', '电池', '七年级上册'),
    ('battle', '战斗', '七年级上册'),
    ('bean', '豆子', '七年级上册'),
    ('beat', '打败', '七年级上册'),
    ('beer', '啤酒', '七年级上册'),
    ('beginning', '开始', '七年级下册'),
    ('behave', '表现', '七年级上册'),
    ('bench', '长凳', '七年级上册'),
    ('bend', '弯曲', '七年级上册'),
    ('beneath', '在...下方', '八年级上册'),
    ('benefit', '好处', '七年级上册'),
    ('beyond', '超过', '七年级上册'),
    ('biscuit', '饼干', '七年级上册'),
    ('blame', '责备', '七年级上册'),
    ('blank', '空白的', '七年级下册'),
    ('bone', '骨头', '七年级上册'),
    ('breath', '呼吸', '七年级上册'),
    ('broad', '宽的', '七年级上册'),
    ('broken', '破碎的', '七年级下册'),
    ('bucket', '桶', '七年级上册'),
    ('bye', '再见', '七年级上册'),
    ('cafe', '咖啡馆', '七年级下册'),
    ('cage', '笼子', '七年级上册'),
    ('cancel', '取消', '七年级上册'),
    ('cancer', '癌症', '七年级上册'),
    ('candy', '糖果', '七年级上册'),
    ('captain', '船长', '七年级下册'),
    ('carpet', '地毯', '七年级上册'),
    ('cartoon', '卡通', '七年级上册'),
    ('case', '情况', '七年级上册'),
    ('cash', '现金', '七年级上册'),
    ('cattle', '牛', '七年级上册'),
    ('ceiling', '天花板', '七年级下册'),
    ('certainly', '当然', '七年级上册'),
    ('chain', '链子', '七年级上册'),
    ('chalk', '粉笔', '七年级上册'),
    ('challenge', '挑战', '九年级'),
    ('chant', '吟唱', '七年级下册'),
    ('cheat', '作弊', '七年级上册'),
    ('cheese', '奶酪', '七年级上册'),
    ('childhood', '童年', '七年级上册'),
    ('chocolate', '巧克力', '七年级下册'),
    ('chopstick', '筷子', '七年级上册'),
    ('cigarette', '香烟', '七年级上册'),
    ('citizen', '公民', '七年级上册'),
    ('click', '点击', '七年级下册'),
    ('cliff', '悬崖', '七年级上册'),
    ('clone', '克隆', '七年级上册'),
    ('cloth', '布', '七年级上册'),
    ('code', '代码', '七年级上册'),
    ('compete', '竞争', '七年级上册'),
    ('conduct', '实施', '七年级上册'),
    ('convenient', '方便的', '八年级下册'),
    ('conversation', '对话', '七年级上册'),
    ('cooker', '炊具', '七年级上册'),
    ('cookie', '饼干', '七年级上册'),
    ('crowd', '人群', '七年级上册'),
    ('customer', '顾客', '七年级上册'),
    ('defeat', '打败', '七年级上册'),
    ('defence', '防御', '七年级上册'),
    ('delight', '高兴', '七年级上册'),
    ('deliver', '递送', '七年级上册'),
    ('deny', '否认', '七年级上册'),
    ('describe', '描述', '八年级下册'),
    ('desire', '愿望', '七年级上册'),
    ('despite', '尽管', '七年级上册'),
    ('destroy', '破坏', '七年级上册'),
    ('devote', '奉献', '七年级上册'),
    ('dialog', '对话', '七年级上册'),
    ('diamond', '钻石', '七年级上册'),
    ('diary', '日记', '七年级上册'),
    ('die', '死', '七年级上册'),
    ('diet', '饮食', '七年级上册'),
    ('differ', '不同', '七年级上册'),
    ('dig', '挖', '七年级上册'),
    ('direct', '直接的', '七年级下册'),
    ('discover', '发现', '八年级下册'),
    ('discuss', '讨论', '七年级上册'),
    ('dish', '盘子', '八年级上册'),
    ('dismiss', '解散', '七年级上册'),
    ('display', '显示', '七年级上册'),
    ('distance', '距离', '七年级上册'),
    ('district', '区域', '七年级上册'),
    ('disturb', '打扰', '七年级上册'),
    ('dive', '潜水', '七年级上册'),
    ('divide', '分开', '七年级下册'),
    ('do', '做', '七年级下册'),
    ('document', '文件', '七年级上册'),
    ('dog', '狗', '七年级上册'),
    ('dollar', '美元', '七年级上册'),
    ('double', '双倍的', '七年级下册'),
    ('doubt', '怀疑', '七年级上册'),
    ('down', '向下', '七年级上册'),
    ('download', '下载', '七年级上册'),
    ('drop', '掉下', '七年级上册'),
    ('dry', '干的', '七年级上册'),
    ('duck', '鸭子', '七年级上册'),
    ('during', '在...期间', '八年级上册'),
    ('each', '每个', '七年级上册'),
    ('eager', '渴望的', '七年级下册'),
    ('earth', '地球', '七年级下册'),
    ('eat', '吃', '七年级下册'),
    ('educate', '教育', '九年级'),
    ('effect', '效果', '七年级上册'),
    ('effort', '努力', '八年级下册'),
    ('egg', '鸡蛋', '七年级上册'),
    ('either', '两者之一', '七年级上册'),
    ('elder', '年长的', '七年级上册'),
    ('elect', '选举', '七年级上册'),
    ('electric', '电的', '七年级上册'),
    ('elephant', '大象', '七年级上册'),
    ('else', '其他的', '七年级下册'),
    ('e-mail', '电子邮件', '七年级下册'),
    ('empty', '空的', '七年级上册'),
    ('end', '结束', '七年级上册'),
    ('enemy', '敌人', '七年级上册'),
    ('engine', '发动机', '七年级下册'),
    ('enjoy', '享受', '七年级上册'),
    ('enter', '进入', '七年级上册'),
    ('entrance', '入口', '七年级上册'),
    ('envelope', '信封', '七年级上册'),
    ('envy', '羡慕', '七年级上册'),
    ('equal', '平等的', '七年级下册'),
    ('equipment', '设备', '七年级上册'),
    ('escape', '逃跑', '七年级下册'),
    ('especially', '尤其', '七年级上册'),
    ('eve', '前夕', '七年级上册'),
    ('even', '甚至', '七年级上册'),
    ('evening', '晚上', '七年级下册'),
    ('ever', '曾经', '七年级上册'),
    ('every', '每个', '七年级上册'),
    ('everyone', '每个人', '八年级下册'),
    ('everything', '每件事', '七年级下册'),
    ('everywhere', '到处', '七年级上册'),
    ('exact', '精确的', '九年级'),
    ('example', '例子', '七年级上册'),
    ('except', '除了', '七年级上册'),
    ('exhibition', '展览', '七年级上册'),
    ('exist', '存在', '七年级上册'),
    ('expect', '期望', '八年级上册'),
    ('expensive', '贵的', '七年级上册'),
    ('experiment', '实验', '八年级下册'),
    ('explain', '解释', '八年级下册'),
    ('explode', '爆炸', '七年级上册'),
    ('fable', '寓言', '七年级上册'),
    ('fact', '事实', '七年级上册'),
    ('factory', '工厂', '七年级上册'),
    ('fail', '失败', '八年级下册'),
    ('fair', '公平的', '七年级下册'),
    ('faith', '信任', '七年级上册'),
    ('fall', '落下', '七年级上册'),
    ('fan', '风扇', '七年级下册'),
    ('far', '远的', '七年级上册'),
    ('farther', '更远的', '七年级下册'),
    ('fast', '快的', '七年级下册'),
    ('fat', '胖的', '七年级上册'),
    ('fear', '害怕', '八年级下册'),
    ('feed', '喂养', '七年级上册'),
    ('feel', '感觉', '八年级上册'),
    ('fetch', '取来', '七年级上册'),
    ('few', '很少', '七年级上册'),
    ('fierce', '凶猛的', '七年级下册'),
    ('fifth', '第五', '七年级上册'),
    ('fifty', '五十', '七年级上册'),
    ('fight', '打架', '七年级上册'),
    ('fill', '填充', '七年级上册'),
    ('final', '最后的', '七年级下册'),
    ('find', '找到', '七年级上册'),
    ('fine', '好的', '七年级上册'),
    ('fire', '火', '七年级上册'),
    ('fireman', '消防员', '七年级下册'),
    ('fix', '修理', '七年级上册'),
    ('flat', '平的', '七年级上册'),
    ('flee', '逃跑', '七年级下册'),
    ('flesh', '肉', '七年级上册'),
    ('flight', '航班', '七年级上册'),
    ('float', '漂浮', '七年级上册'),
    ('flood', '洪水', '七年级上册'),
    ('flour', '面粉', '七年级上册'),
    ('flow', '流动', '七年级上册'),
    ('flower', '花', '七年级上册'),
    ('fly', '飞', '七年级下册'),
    ('focus', '焦点', '七年级下册'),
    ('fog', '雾', '七年级上册'),
    ('fold', '折叠', '七年级上册'),
    ('follow', '跟随', '七年级上册'),
    ('fool', '傻子', '七年级上册'),
    ('for', '为了', '七年级上册'),
    ('force', '强迫', '七年级上册'),
    ('forever', '永远', '七年级上册'),
    ('forgive', '原谅', '七年级上册'),
    ('fork', '叉子', '七年级上册'),
    ('form', '形成', '七年级上册'),
    ('forty', '四十', '七年级上册'),
    ('forward', '向前', '七年级上册'),
    ('found', '建立', '七年级上册'),
    ('freedom', '自由', '七年级上册'),
    ('freeze', '结冰', '七年级上册'),
    ('fridge', '冰箱', '七年级上册'),
    ('frog', '青蛙', '七年级上册'),
    ('front', '前面', '七年级上册'),
    ('full', '满的', '七年级上册'),
    ('fun', '有趣的事', '七年级下册'),
    ('gather', '聚集', '七年级上册'),
    ('general', '普遍的', '七年级下册'),
    ('gentle', '温和的', '七年级下册'),
    ('gesture', '手势', '七年级上册'),
    ('girl', '女孩', '七年级上册'),
    ('glad', '高兴的', '七年级上册'),
    ('glass', '玻璃', '七年级上册'),
    ('goal', '目标', '七年级上册'),
    ('god', '神', '七年级上册'),
    ('golden', '金色的', '七年级下册'),
    ('govern', '统治', '七年级上册'),
    ('gradual', '逐渐的', '七年级下册'),
    ('grain', '谷物', '七年级上册'),
    ('grant', '授予', '七年级上册'),
    ('grateful', '感激的', '七年级下册'),
    ('grave', '坟墓', '七年级上册'),
    ('great', '伟大的', '七年级上册'),
    ('greet', '问候', '七年级上册'),
    ('ground', '地面', '七年级上册'),
    ('group', '小组', '七年级上册'),
    ('guarantee', '保证', '七年级上册'),
    ('guard', '守卫', '七年级上册'),
    ('guess', '猜测', '七年级上册'),
    ('guest', '客人', '七年级上册'),
    ('guilt', '内疚', '七年级上册'),
    ('gun', '枪', '七年级上册'),
    ('ham', '火腿', '七年级上册'),
    ('handkerchief', '手帕', '七年级上册'),
    ('handle', '处理', '七年级上册'),
    ('handsome', '英俊的', '七年级下册'),
    ('hang', '悬挂', '七年级上册'),
    ('happen', '发生', '八年级上册'),
    ('hard', '困难的', '七年级下册'),
    ('hardly', '几乎不', '八年级上册'),
    ('hate', '讨厌', '七年级上册'),
    ('hear', '听见', '七年级上册'),
    ('heart', '心脏', '七年级下册'),
    ('heat', '热量', '七年级下册'),
    ('heavy', '重的', '七年级上册'),
    ('height', '高度', '七年级上册'),
    ('helpful', '有帮助的', '七年级下册'),
    ('hen', '母鸡', '七年级上册'),
    ('her', '她的', '七年级上册'),
    ('here', '这里', '七年级上册'),
    ('hero', '英雄', '七年级上册'),
    ('hers', '她的', '七年级上册'),
    ('hill', '小山', '七年级上册'),
    ('him', '他', '七年级上册'),
    ('hip', '臀部', '七年级上册'),
    ('his', '他的', '七年级上册'),
    ('hit', '打击', '七年级上册'),
    ('hold', '握住', '七年级上册'),
    ('hole', '洞', '七年级上册'),
    ('holy', '神圣的', '七年级下册'),
    ('honest', '诚实的', '七年级下册'),
    ('hope', '希望', '八年级上册'),
    ('host', '主人', '七年级上册'),
    ('hour', '小时', '七年级上册'),
    ('house', '房子', '七年级上册'),
    ('housework', '家务', '七年级下册'),
    ('however', '然而', '八年级上册'),
    ('huge', '巨大的', '七年级上册'),
    ('humorous', '幽默的', '七年级下册'),
    ('hunger', '饥饿', '七年级上册'),
    ('hungry', '饿的', '七年级上册'),
    ('hurry', '赶紧', '七年级上册'),
    ('ice', '冰', '七年级上册'),
    ('ice cream', '冰淇淋', '七年级下册'),
    ('idea', '主意', '七年级上册'),
    ('idle', '懒惰的', '七年级下册'),
    ('if', '如果', '七年级上册'),
    ('ignore', '忽视', '七年级上册'),
    ('illegal', '非法的', '七年级下册'),
    ('imagine', '想象', '八年级下册'),
    ('immediate', '立即的', '七年级下册'),
    ('import', '进口', '七年级上册'),
    ('impossible', '不可能的', '八年级下册'),
    ('include', '包括', '七年级上册'),
    ('increase', '增加', '八年级下册'),
    ('indeed', '确实', '七年级上册'),
    ('independent', '独立的', '七年级下册'),
    ('India', '印度', '七年级上册'),
    ('Indian', '印度的', '七年级下册'),
    ('industry', '工业', '七年级上册'),
    ('influence', '影响', '七年级上册'),
    ('initial', '最初的', '七年级下册'),
    ('ink', '墨水', '七年级上册'),
    ('innocent', '无辜的', '七年级下册'),
    ('insect', '昆虫', '七年级上册'),
    ('inside', '里面', '七年级上册'),
    ('insist', '坚持', '七年级上册'),
    ('inspect', '检查', '九年级'),
    ('inspire', '激励', '八年级下册'),
    ('instant', '立即的', '七年级下册'),
    ('instead', '代替', '七年级上册'),
    ('institute', '机构', '七年级上册'),
    ('instruct', '指导', '七年级上册'),
    ('insure', '确保', '七年级上册'),
    ('intelligence', '智力', '七年级上册'),
    ('intend', '打算', '七年级上册'),
    ('Internet', '互联网', '八年级上册'),
    ('interview', '面试', '七年级上册'),
    ('into', '进入', '七年级上册'),
    ('introduce', '介绍', '八年级下册'),
    ('invent', '发明', '八年级下册'),
    ('invest', '投资', '七年级上册'),
    ('invite', '邀请', '七年级上册'),
    ('its', '它的', '七年级上册'),
    ('jade', '玉', '七年级上册'),
    ('janitor', '看门人', '七年级下册'),
    ('Japanese', '日语', '七年级上册'),
    ('joke', '笑话', '七年级上册'),
    ('journal', '期刊', '七年级上册'),
    ('joy', '快乐', '七年级下册'),
    ('judge', '判断', '九年级'),
    ('juice', '果汁', '七年级上册'),
    ('jump', '跳', '七年级下册'),
    ('just', '刚才', '七年级上册'),
    ('keep', '保持', '七年级上册'),
    ('kick', '踢', '七年级上册'),
    ('kill', '杀死', '七年级上册'),
    ('kilogram', '千克', '七年级上册'),
    ('kind', '善良的', '七年级下册'),
    ('king', '国王', '七年级上册'),
    ('kiss', '亲吻', '七年级上册'),
    ('kite', '风筝', '七年级下册'),
    ('knee', '膝盖', '七年级上册'),
    ('knock', '敲', '七年级上册'),
    ('knowledge', '知识', '九年级'),
    ('lack', '缺乏', '七年级上册'),
    ('ladder', '梯子', '七年级上册'),
    ('lady', '女士', '七年级上册'),
    ('land', '陆地', '七年级上册'),
    ('large', '大的', '七年级上册'),
    ('last', '最后的', '七年级下册'),
    ('latter', '后者的', '七年级下册'),
    ('law', '法律', '七年级上册'),
    ('lay', '放置', '七年级下册'),
    ('lazy', '懒惰的', '七年级下册'),
    ('lead', '领导', '七年级上册'),
    ('leaf', '叶子', '七年级上册'),
    ('leave', '离开', '七年级下册'),
    ('legal', '合法的', '七年级下册'),
    ('lemon', '柠檬', '七年级上册'),
    ('lend', '借出', '七年级上册'),
    ('length', '长度', '七年级上册'),
    ('level', '水平', '七年级上册'),
    ('life', '生命', '七年级上册'),
    ('light', '轻的', '七年级上册'),
    ('limit', '限制', '七年级上册'),
    ('line', '线', '七年级上册'),
    ('link', '链接', '七年级上册'),
    ('lion', '狮子', '七年级上册'),
    ('list', '列表', '七年级上册'),
    ('listen', '听', '七年级上册'),
    ('literature', '文学', '七年级上册'),
    ('little', '小的', '七年级上册'),
    ('live', '生活', '七年级上册'),
    ('load', '装载', '七年级上册'),
    ('loan', '贷款', '七年级上册'),
    ('local', '当地的', '七年级下册'),
    ('lock', '锁', '七年级上册'),
    ('loss', '损失', '七年级上册'),
    ('lot', '许多', '七年级上册'),
    ('loud', '大声的', '七年级上册'),
    ('love', '爱', '七年级上册'),
    ('lovely', '可爱的', '七年级下册'),
    ('luck', '运气', '七年级上册'),
    ('machine', '机器', '七年级上册'),
    ('mad', '生气的', '七年级下册'),
    ('mail', '邮件', '七年级下册'),
    ('main', '主要的', '七年级下册'),
    ('male', '男性的', '七年级下册'),
    ('man', '男人', '七年级上册'),
    ('manage', '管理', '七年级上册'),
    ('manager', '经理', '七年级上册'),
    ('many', '许多', '七年级上册'),
    ('mark', '标记', '七年级上册'),
    ('market', '市场', '七年级下册'),
    ('marriage', '婚姻', '七年级上册'),
    ('marry', '结婚', '七年级上册'),
    ('match', '比赛', '八年级上册'),
    ('may', '可以', '七年级上册'),
    ('maybe', '也许', '八年级上册'),
    ('mayor', '市长', '七年级上册'),
    ('mean', '意思是', '七年级上册'),
    ('meaning', '意思', '七年级上册'),
    ('medium', '中等的', '七年级下册'),
    ('melon', '瓜', '七年级上册'),
    ('melt', '融化', '七年级上册'),
    ('memorize', '记住', '七年级上册'),
    ('mental', '精神的', '七年级下册'),
    ('mention', '提到', '七年级上册'),
    ('menu', '菜单', '八年级上册'),
    ('mercy', '怜悯', '七年级上册'),
    ('merely', '仅仅', '七年级上册'),
    ('merry', '快乐的', '七年级下册'),
    ('mess', '混乱', '七年级上册'),
    ('metal', '金属', '七年级上册'),
    ('method', '方法', '七年级上册'),
    ('meter', '米', '七年级上册'),
    ('microphone', '麦克风', '七年级下册'),
    ('midday', '正午', '七年级上册'),
    ('midnight', '午夜', '七年级上册'),
    ('might', '可能', '八年级下册'),
    ('mile', '英里', '七年级上册'),
    ('milk', '牛奶', '七年级上册'),
    ('millimeter', '毫米', '七年级上册'),
    ('million', '百万', '七年级上册'),
    ('mind', '介意', '八年级上册'),
    ('mine', '我的', '七年级上册'),
    ('mineral', '矿物', '七年级上册'),
    ('minute', '分钟', '七年级上册'),
    ('mirror', '镜子', '七年级上册'),
    ('miss', '想念', '七年级上册'),
    ('mistake', '错误', '七年级上册'),
    ('mix', '混合', '七年级上册'),
    ('moment', '时刻', '七年级下册'),
    ('money', '钱', '七年级上册'),
    ('monitor', '监视器', '七年级下册'),
    ('monkey', '猴子', '七年级上册'),
    ('most', '最多的', '七年级下册'),
    ('motion', '运动', '七年级下册'),
    ('motor', '发动机', '七年级下册'),
    ('mouse', '老鼠', '七年级上册'),
    ('much', '许多', '七年级上册'),
    ('mud', '泥', '七年级上册'),
    ('multiply', '乘', '七年级上册'),
    ('murder', '谋杀', '七年级上册'),
    ('myself', '我自己', '七年级下册'),
    ('narrow', '窄的', '七年级上册'),
    ('national', '国家的', '七年级下册'),
    ('near', '近的', '七年级上册'),
    ('nearly', '几乎', '八年级上册'),
    ('necessary', '必要的', '八年级下册'),
    ('need', '需要', '七年级上册'),
    ('needle', '针', '七年级上册'),
    ('neglect', '忽视', '七年级上册'),
    ('neither', '两者都不', '七年级下册'),
    ('nephew', '侄子', '八年级上册'),
    ('nerve', '神经', '七年级上册'),
    ('net', '网', '七年级上册'),
    ('network', '网络', '七年级上册'),
    ('news', '新闻', '八年级上册'),
    ('niece', '侄女', '八年级上册'),
    ('night', '夜晚', '七年级下册'),
    ('nobody', '没有人', '七年级下册'),
    ('nod', '点头', '七年级下册'),
    ('noise', '噪音', '七年级上册'),
    ('none', '没有', '七年级上册'),
    ('noon', '正午', '七年级上册'),
    ('nor', '也不', '七年级上册'),
    ('normal', '正常的', '八年级上册'),
    ('note', '笔记', '七年级上册'),
    ('notebook', '笔记本', '七年级上册'),
    ('nothing', '没有东西', '七年级下册'),
    ('notice', '注意', '八年级下册'),
    ('nowhere', '无处', '七年级上册'),
    ('nut', '坚果', '七年级上册'),
    ('obey', '服从', '七年级上册'),
    ('object', '物体', '七年级上册'),
    ('observe', '观察', '七年级上册'),
    ('obvious', '明显的', '七年级下册'),
    ('of', '的', '七年级上册'),
    ('off', '离开', '七年级下册'),
    ('officer', '军官', '七年级上册'),
    ('oil', '油', '七年级上册'),
    ('okay', '好的', '七年级上册'),
    ('Olympic', '奥运的', '七年级下册'),
    ('on', '在...上面', '八年级上册'),
    ('once', '一次', '七年级上册'),
    ('open', '打开', '七年级下册'),
    ('operate', '操作', '七年级上册'),
    ('opinion', '意见', '七年级上册'),
    ('opposite', '相反的', '七年级下册'),
    ('optimistic', '乐观的', '七年级下册'),
    ('or', '或者', '七年级上册'),
    ('order', '命令', '七年级上册'),
    ('ordinary', '普通的', '九年级'),
    ('organize', '组织', '九年级'),
    ('other', '其他的', '七年级下册'),
    ('otherwise', '否则', '七年级上册'),
    ('ought', '应该', '七年级上册'),
    ('our', '我们的', '七年级下册'),
    ('ourselves', '我们自己', '七年级下册'),
    ('out', '出去', '七年级上册'),
    ('outline', '大纲', '七年级上册'),
    ('outstanding', '杰出的', '七年级下册'),
    ('oven', '烤箱', '七年级上册'),
    ('over', '结束', '七年级上册'),
    ('own', '自己的', '七年级下册'),
    ('owner', '主人', '七年级上册'),
    ('oxygen', '氧气', '七年级上册'),
    ('pace', '步速', '七年级上册'),
    ('package', '包裹', '七年级上册'),
    ('page', '页', '七年级上册'),
    ('pair', '一对', '七年级上册'),
    ('pale', '苍白的', '七年级下册'),
    ('pan', '平底锅', '七年级下册'),
    ('panda', '熊猫', '七年级上册'),
    ('pardon', '原谅', '七年级上册'),
    ('part', '部分', '七年级上册'),
    ('particular', '特别的', '九年级'),
    ('partly', '部分地', '七年级下册'),
    ('partner', '伙伴', '七年级上册'),
    ('pass', '通过', '七年级上册'),
    ('passive', '被动的', '七年级下册'),
    ('path', '小径', '七年级上册'),
    ('pattern', '模式', '七年级上册'),
    ('pay', '支付', '七年级上册'),
    ('peace', '和平', '七年级上册'),
    ('pear', '梨', '七年级上册'),
    ('penny', '便士', '七年级上册'),
    ('people', '人们', '七年级上册'),
    ('percent', '百分比', '七年级下册'),
    ('perfect', '完美的', '七年级下册'),
    ('perhaps', '也许', '八年级上册'),
    ('period', '时期', '七年级上册'),
    ('person', '人', '七年级上册'),
    ('personal', '个人的', '八年级下册'),
    ('persuade', '说服', '七年级上册'),
    ('pet', '宠物', '七年级上册'),
    ('phone', '电话', '七年级上册'),
    ('physical', '身体的', '七年级下册'),
    ('pick', '捡起', '七年级上册'),
    ('pie', '馅饼', '七年级上册'),
    ('piece', '碎片', '七年级上册'),
    ('pig', '猪', '七年级上册'),
    ('pile', '堆', '七年级上册'),
    ('pilot', '飞行员', '七年级下册'),
    ('pin', '别针', '七年级上册'),
    ('pioneer', '先锋', '七年级上册'),
    ('pipe', '管道', '七年级上册'),
    ('pity', '遗憾', '七年级上册'),
    ('plain', '平原', '七年级上册'),
    ('planet', '行星', '七年级上册'),
    ('plate', '盘子', '八年级上册'),
    ('playground', '操场', '七年级上册'),
    ('pleasant', '令人愉快的', '七年级下册'),
    ('pleasure', '愉快', '七年级下册'),
    ('plenty', '大量', '七年级上册'),
    ('plug', '插头', '七年级上册'),
    ('plus', '加上', '七年级上册'),
    ('poet', '诗人', '七年级上册'),
    ('point', '指向', '七年级上册'),
    ('police', '警察', '七年级下册'),
    ('policeman', '男警察', '七年级下册'),
    ('polite', '有礼貌的', '七年级下册'),
    ('political', '政治的', '七年级下册'),
    ('pool', '水池', '七年级上册'),
    ('poor', '穷的', '八年级上册'),
    ('pose', '摆姿势', '七年级下册'),
    ('position', '位置', '七年级上册'),
    ('positive', '积极的', '七年级下册'),
    ('possess', '拥有', '七年级上册'),
    ('possible', '可能的', '八年级下册'),
    ('post', '邮寄', '七年级下册'),
    ('pot', '锅', '七年级上册'),
    ('pound', '英镑', '七年级上册'),
    ('pour', '倾倒', '七年级上册'),
    ('powerful', '强大的', '七年级上册'),
    ('praise', '表扬', '七年级上册'),
    ('pray', '祈祷', '七年级上册'),
    ('predict', '预测', '七年级上册'),
    ('prepare', '准备', '七年级上册'),
    ('president', '总统', '七年级上册'),
    ('press', '压', '七年级上册'),
    ('pressure', '压力', '八年级下册'),
    ('pretend', '假装', '七年级上册'),
    ('pretty', '漂亮的', '七年级下册'),
    ('previous', '以前的', '七年级下册'),
    ('price', '价格', '七年级上册'),
    ('pride', '骄傲', '九年级'),
    ('primary', '主要的', '七年级下册'),
    ('prince', '王子', '七年级上册'),
    ('principle', '原则', '七年级上册'),
    ('print', '打印', '七年级上册'),
    ('prison', '监狱', '七年级上册'),
    ('prisoner', '囚犯', '七年级上册'),
    ('private', '私人的', '八年级下册'),
    ('prize', '奖品', '七年级上册'),
    ('probable', '可能的', '八年级下册'),
    ('problem', '问题', '七年级上册'),
    ('process', '过程', '七年级上册'),
    ('produce', '生产', '八年级下册'),
    ('product', '产品', '七年级上册'),
    ('professor', '教授', '七年级上册'),
    ('profit', '利润', '七年级上册'),
    ('program', '程序', '七年级上册'),
    ('project', '项目', '八年级下册'),
    ('promise', '承诺', '七年级上册'),
    ('prove', '证明', '七年级上册'),
    ('public', '公共的', '八年级下册'),
    ('publish', '出版', '七年级上册'),
    ('pull', '拉', '七年级上册'),
    ('pump', '泵', '七年级上册'),
    ('punish', '惩罚', '七年级上册'),
    ('pupil', '小学生', '七年级上册'),
    ('purpose', '目的', '七年级上册'),
    ('purse', '钱包', '七年级上册'),
    ('push', '推', '七年级上册'),
    ('qualification', '资格', '七年级上册'),
    ('quality', '质量', '九年级'),
    ('quantity', '数量', '七年级上册'),
    ('quarrel', '争吵', '七年级上册'),
    ('queen', '女王', '七年级上册'),
    ('question', '问题', '七年级上册'),
    ('quick', '迅速的', '七年级下册'),
    ('quiet', '安静的', '七年级下册'),
    ('quiz', '测验', '七年级上册'),
    ('radio', '收音机', '七年级下册'),
    ('rare', '稀有的', '七年级下册'),
    ('rat', '老鼠', '七年级上册'),
    ('rate', '比率', '七年级上册'),
    ('rather', '相当', '七年级上册'),
    ('raw', '生的', '七年级上册'),
    ('ray', '光线', '七年级上册'),
    ('react', '反应', '七年级上册'),
    ('ready', '准备好的', '七年级下册'),
    ('real', '真实的', '七年级下册'),
    ('realize', '意识到', '八年级下册'),
    ('receive', '收到', '七年级上册'),
    ('recent', '最近的', '七年级下册'),
    ('recently', '最近', '七年级上册'),
    ('recover', '恢复', '七年级上册'),
    ('refer', '参考', '七年级上册'),
    ('reflect', '反映', '七年级上册'),
    ('regular', '规律的', '七年级下册'),
    ('relate', '关联', '七年级上册'),
    ('relation', '关系', '八年级上册'),
    ('relax', '放松', '七年级下册'),
    ('release', '释放', '七年级下册'),
    ('religion', '宗教', '七年级上册'),
    ('rely', '依赖', '七年级上册'),
    ('remain', '保持', '七年级上册'),
    ('remind', '提醒', '七年级上册'),
    ('remote', '遥远的', '七年级下册'),
    ('remove', '移除', '七年级上册'),
    ('rent', '租金', '七年级上册'),
    ('repeat', '重复', '七年级上册'),
    ('replace', '替换', '七年级上册'),
    ('reply', '回复', '七年级上册'),
    ('report', '报告', '七年级上册'),
    ('reporter', '记者', '七年级上册'),
    ('request', '请求', '七年级上册'),
    ('require', '要求', '七年级上册'),
    ('resign', '辞职', '七年级上册'),
    ('resist', '抵制', '七年级上册'),
    ('resolve', '解决', '七年级上册'),
    ('respect', '尊重', '九年级'),
    ('respond', '回应', '七年级上册'),
    ('result', '结果', '八年级上册'),
    ('retire', '退休', '七年级上册'),
    ('reward', '奖励', '七年级上册'),
    ('rich', '富的', '八年级上册'),
    ('ring', '戒指', '七年级上册'),
    ('rock', '石头', '七年级上册'),
    ('rocket', '火箭', '七年级上册'),
    ('role', '角色', '七年级上册'),
    ('roll', '滚动', '七年级上册'),
    ('romantic', '浪漫的', '七年级下册'),
    ('roof', '屋顶', '七年级上册'),
    ('root', '根', '七年级上册'),
    ('rope', '绳子', '七年级上册'),
    ('rose', '玫瑰', '七年级上册'),
    ('rough', '粗糙的', '七年级下册'),
    ('row', '排', '七年级上册'),
    ('royal', '皇家的', '七年级下册'),
    ('rubber', '橡胶', '七年级上册'),
    ('rude', '粗鲁的', '七年级下册'),
    ('rule', '规则', '七年级上册'),
    ('run', '跑', '七年级下册'),
    ('rush', '冲', '七年级上册'),
    ('sail', '航行', '七年级上册'),
    ('sale', '销售', '七年级上册'),
    ('salt', '盐', '七年级上册'),
    ('sand', '沙子', '七年级上册'),
    ('sank', '下沉', '七年级上册'),
    ('satellite', '卫星', '七年级上册'),
    ('scene', '场景', '七年级上册'),
    ('scissors', '剪刀', '七年级上册'),
    ('score', '得分', '七年级上册'),
    ('scream', '尖叫', '七年级上册'),
    ('search', '搜索', '七年级上册'),
    ('seat', '座位', '八年级上册'),
    ('secret', '秘密', '七年级上册'),
    ('secretary', '秘书', '七年级上册'),
    ('section', '部分', '七年级上册'),
    ('see', '看见', '七年级下册'),
    ('seed', '种子', '七年级上册'),
    ('seek', '寻找', '七年级上册'),
    ('seem', '似乎', '八年级上册'),
    ('seldom', '很少', '七年级上册'),
    ('select', '选择', '七年级上册'),
    ('sell', '卖', '七年级上册'),
    ('send', '发送', '七年级上册'),
    ('sense', '感觉', '八年级上册'),
    ('separate', '分开', '七年级下册'),
    ('series', '系列', '七年级上册'),
    ('servant', '仆人', '七年级上册'),
    ('serve', '服务', '八年级上册'),
    ('service', '服务', '八年级上册'),
    ('set', '设置', '七年级上册'),
    ('settle', '解决', '七年级上册'),
    ('several', '几个', '七年级上册'),
    ('severe', '严重的', '八年级上册'),
    ('sex', '性别', '七年级上册'),
    ('shade', '阴凉处', '七年级下册'),
    ('shadow', '影子', '七年级上册'),
    ('shake', '摇动', '七年级上册'),
    ('shall', '将', '七年级上册'),
    ('shallow', '浅的', '七年级上册'),
    ('shame', '羞耻', '七年级上册'),
    ('share', '分享', '七年级上册'),
    ('sharp', '锋利的', '七年级下册'),
    ('sheep', '绵羊', '七年级上册'),
    ('sheet', '床单', '七年级上册'),
    ('shelf', '架子', '七年级上册'),
    ('shine', '闪耀', '七年级上册'),
    ('shock', '震惊', '七年级上册'),
    ('shoot', '射击', '七年级上册'),
    ('should', '应该', '七年级上册'),
    ('shoulder', '肩膀', '七年级上册'),
    ('shower', '淋浴', '七年级上册'),
    ('shut', '关闭', '七年级上册'),
    ('side', '边', '七年级上册'),
    ('sideway', '人行道', '七年级下册'),
    ('sight', '视力', '七年级上册'),
    ('sign', '标志', '七年级上册'),
    ('signal', '信号', '七年级上册'),
    ('silence', '沉默', '七年级上册'),
    ('simple', '简单的', '七年级下册'),
    ('since', '自从', '七年级上册'),
    ('single', '单个的', '七年级下册'),
    ('sink', '水槽', '七年级上册'),
    ('sir', '先生', '七年级上册'),
    ('sit', '坐', '七年级上册'),
    ('situation', '情况', '七年级上册'),
    ('skin', '皮肤', '七年级上册'),
    ('sleep', '睡觉', '七年级下册'),
    ('slide', '滑动', '七年级上册'),
    ('slight', '轻微的', '七年级下册'),
    ('slow', '慢的', '七年级上册'),
    ('smart', '聪明的', '七年级下册'),
    ('soap', '肥皂', '七年级上册'),
    ('social', '社会的', '八年级下册'),
    ('soft', '柔软的', '七年级下册'),
    ('software', '软件', '七年级上册'),
    ('soil', '土壤', '七年级上册'),
    ('soldier', '士兵', '七年级上册'),
    ('solid', '固体的', '七年级下册'),
    ('solution', '解决方案', '七年级下册'),
    ('solve', '解决', '七年级上册'),
    ('some', '一些', '七年级上册'),
    ('somebody', '某人', '七年级上册'),
    ('someone', '某人', '七年级上册'),
    ('something', '某事', '七年级上册'),
    ('somewhere', '某地', '七年级上册'),
    ('soon', '很快', '七年级下册'),
    ('sort', '种类', '七年级上册'),
    ('sound', '声音', '八年级上册'),
    ('space', '空间', '七年级上册'),
    ('speaker', '演讲者', '七年级下册'),
    ('special', '特别的', '九年级'),
    ('speech', '演讲', '七年级上册'),
    ('speed', '速度', '七年级上册'),
    ('spell', '拼写', '七年级下册'),
    ('spirit', '精神', '七年级上册'),
    ('spit', '吐痰', '七年级上册'),
    ('spite', '恶意', '七年级上册'),
    ('spoon', '勺子', '七年级上册'),
    ('spread', '传播', '七年级上册'),
    ('stage', '舞台', '七年级上册'),
    ('stair', '楼梯', '七年级上册'),
    ('stand', '站立', '七年级上册'),
    ('standard', '标准', '七年级上册'),
    ('start', '开始', '七年级下册'),
    ('state', '州', '七年级上册'),
    ('steal', '偷', '七年级上册'),
    ('steel', '钢', '七年级上册'),
    ('step', '步骤', '七年级上册'),
    ('stick', '粘贴', '七年级上册'),
    ('stone', '石头', '七年级上册'),
    ('storm', '暴风雨', '七年级下册'),
    ('stove', '炉子', '七年级上册'),
    ('straight', '直的', '七年级上册'),
    ('strange', '奇怪的', '七年级下册'),
    ('stress', '压力', '八年级下册'),
    ('strict', '严格的', '七年级下册'),
    ('strike', '罢工', '七年级上册'),
    ('struggle', '奋斗', '七年级上册'),
    ('stupid', '愚蠢的', '七年级下册'),
    ('succeed', '成功', '九年级'),
    ('such', '这样的', '七年级上册'),
    ('sugar', '糖', '七年级上册'),
    ('supper', '晚餐', '七年级下册'),
    ('supply', '提供', '八年级下册'),
    ('suppose', '假设', '七年级上册'),
    ('surface', '表面', '七年级上册'),
    ('surprise', '惊讶', '七年级上册'),
    ('switch', '开关', '七年级下册'),
    ('sword', '剑', '七年级上册'),
    ('symbol', '象征', '七年级上册'),
    ('system', '系统', '七年级上册'),
    ('tail', '尾巴', '七年级上册'),
    ('tale', '故事', '七年级上册'),
    ('tank', '坦克', '七年级上册'),
    ('tape', '磁带', '七年级下册'),
    ('task', '任务', '七年级上册'),
    ('taxi', '出租车', '七年级下册'),
    ('tea', '茶', '七年级上册'),
    ('tear', '眼泪', '七年级上册'),
    ('technical', '技术的', '八年级下册'),
    ('technique', '技巧', '七年级上册'),
    ('teenager', '青少年', '七年级下册'),
    ('television', '电视', '七年级下册'),
    ('tent', '帐篷', '七年级上册'),
    ('test', '测试', '七年级上册'),
    ('than', '比', '七年级上册'),
    ('that', '那个', '七年级上册'),
    ('their', '他们的', '七年级下册'),
    ('them', '他们', '七年级上册'),
    ('themselves', '他们自己', '七年级下册'),
    ('theory', '理论', '七年级上册'),
    ('there', '那里', '七年级上册'),
    ('therefore', '因此', '七年级上册'),
    ('thick', '厚的', '七年级上册'),
    ('thief', '小偷', '七年级上册'),
    ('thin', '瘦的', '七年级上册'),
    ('thing', '东西', '七年级上册'),
    ('think', '思考', '七年级上册'),
    ('thirsty', '渴的', '七年级上册'),
    ('thirty', '三十', '七年级上册'),
    ('this', '这个', '七年级上册'),
    ('those', '那些', '七年级上册'),
    ('though', '虽然', '八年级上册'),
    ('thought', '想法', '七年级上册'),
    ('thousand', '千', '七年级上册'),
    ('thread', '线', '七年级上册'),
    ('through', '通过', '七年级上册'),
    ('thumb', '大拇指', '七年级上册'),
    ('thunder', '雷声', '七年级上册'),
    ('tidy', '整洁的', '七年级下册'),
    ('tiger', '老虎', '七年级上册'),
    ('tight', '紧的', '七年级上册'),
    ('till', '直到', '七年级上册'),
    ('tin', '罐头', '七年级上册'),
    ('title', '标题', '七年级上册'),
    ('toe', '脚趾', '七年级上册'),
    ('toefl', '托福', '七年级上册'),
    ('together', '一起', '七年级上册'),
    ('toilet', '厕所', '七年级上册'),
    ('tongue', '舌头', '七年级上册'),
    ('tonight', '今晚', '七年级下册'),
    ('tool', '工具', '七年级上册'),
    ('top', '顶部', '七年级上册'),
    ('topic', '话题', '七年级上册'),
    ('total', '总的', '七年级上册'),
    ('touch', '触摸', '七年级上册'),
    ('toward', '朝向', '七年级上册'),
    ('towel', '毛巾', '七年级上册'),
    ('town', '城镇', '七年级上册'),
    ('trade', '贸易', '七年级上册'),
    ('traffic', '交通', '七年级上册'),
    ('transport', '运输', '七年级上册'),
    ('treasure', '财宝', '七年级上册'),
    ('treat', '对待', '七年级上册'),
    ('truck', '卡车', '七年级上册'),
    ('true', '真的', '七年级上册'),
    ('trust', '信任', '七年级上册'),
    ('truth', '真相', '七年级上册'),
    ('try', '尝试', '八年级上册'),
    ('twice', '两次', '七年级上册'),
    ('twin', '双胞胎', '七年级下册'),
    ('type', '类型', '七年级上册'),
    ('ugly', '丑陋的', '七年级下册'),
    ('umbrella', '雨伞', '七年级下册'),
    ('under', '在...下面', '八年级上册'),
    ('unit', '单元', '七年级上册'),
    ('universe', '宇宙', '七年级上册'),
    ('university', '大学', '七年级上册'),
    ('unless', '除非', '七年级上册'),
    ('unlike', '不像', '七年级上册'),
    ('until', '直到', '七年级上册'),
    ('unusual', '不寻常的', '七年级下册'),
    ('up', '向上', '七年级上册'),
    ('upon', '在...上面', '八年级上册'),
    ('upset', '心烦的', '七年级下册'),
    ('upstairs', '楼上', '七年级上册'),
    ('use', '使用', '七年级上册'),
    ('used', '用过的', '七年级下册'),
    ('useful', '有用的', '七年级下册'),
    ('useless', '无用的', '七年级下册'),
    ('user', '用户', '七年级上册'),
    ('usual', '通常的', '七年级下册'),
    ('valley', '山谷', '七年级上册'),
    ('valuable', '有价值的', '七年级下册'),
    ('value', '价值', '七年级上册'),
    ('variety', '种类', '七年级上册'),
    ('various', '各种各样的', '八年级上册'),
    ('vast', '广阔的', '七年级下册'),
    ('verb', '动词', '七年级上册'),
    ('very', '非常', '七年级上册'),
    ('victory', '胜利', '七年级上册'),
    ('video', '视频', '七年级上册'),
    ('village', '村庄', '七年级上册'),
    ('virtue', '美德', '七年级上册'),
    ('visitor', '访客', '七年级上册'),
    ('voice', '声音', '八年级上册'),
    ('voyage', '航行', '七年级上册'),
    ('wage', '工资', '七年级上册'),
    ('waist', '腰部', '七年级上册'),
    ('wallet', '钱包', '七年级上册'),
    ('wander', '漫步', '七年级上册'),
    ('war', '战争', '七年级上册'),
    ('warn', '警告', '七年级上册'),
    ('wash', '洗', '七年级下册'),
    ('wave', '波浪', '七年级上册'),
    ('way', '路', '七年级上册'),
    ('we', '我们', '七年级上册'),
    ('wealth', '财富', '八年级上册'),
    ('web', '网', '七年级上册'),
    ('weekday', '工作日', '七年级下册'),
    ('weight', '重量', '七年级上册'),
    ('welfare', '福利', '七年级上册'),
    ('well', '好', '七年级上册'),
    ('wet', '湿的', '七年级上册'),
    ('whatever', '无论什么', '七年级上册'),
    ('wheat', '小麦', '七年级上册'),
    ('wheel', '轮子', '七年级上册'),
    ('when', '什么时候', '七年级上册'),
    ('whether', '是否', '七年级上册'),
    ('which', '哪一个', '七年级上册'),
    ('while', '当...时候', '八年级上册'),
    ('whole', '整个的', '七年级下册'),
    ('whom', '谁', '七年级上册'),
    ('whose', '谁的', '七年级上册'),
    ('why', '为什么', '七年级上册'),
    ('wild', '野生的', '七年级下册'),
    ('will', '将', '七年级上册'),
    ('wine', '酒', '七年级上册'),
    ('wing', '翅膀', '七年级上册'),
    ('winner', '获胜者', '七年级下册'),
    ('wipe', '擦', '七年级上册'),
    ('wise', '明智的', '七年级下册'),
    ('with', '和...一起', '七年级上册'),
    ('within', '在...之内', '八年级上册'),
    ('without', '没有', '七年级上册'),
    ('wolf', '狼', '七年级上册'),
    ('woman', '女人', '七年级上册'),
    ('wonder', '想知道', '七年级下册'),
    ('wonderful', '精彩的', '七年级下册'),
    ('wood', '木头', '七年级上册'),
    ('workshop', '车间', '七年级上册'),
    ('worth', '值得', '七年级上册'),
    ('wound', '伤口', '七年级上册'),
    ('wrestle', '摔跤', '七年级上册'),
    ('wrong', '错误的', '七年级下册'),
    ('yard', '院子', '七年级上册'),
    ('yeah', '是的', '七年级上册'),
    ('yell', '大喊', '七年级上册'),
    ('yesterday', '昨天', '七年级下册'),
    ('yet', '还', '七年级上册'),
    ('yours', '你的', '七年级上册'),
    ('yourself', '你自己', '七年级下册'),
    ('youth', '青春', '七年级下册'),
    ('zebra', '斑马', '七年级上册'),
    ('zero', '零', '七年级上册'),
    ('zone', '区域', '七年级上册'),
# ==================== 二、初中常用短语（120+）====================
    ('taller', '更高的', '八年级上册'),
    ('shorter', '更矮的', '八年级上册'),
    ('stronger', '更强壮的', '八年级上册'),
    ('faster', '更快的', '八年级上册'),
    ('heavier', '更重的', '八年级上册'),
    ('longer', '更长的', '八年级上册'),
    ('louder', '更响亮的', '八年级上册'),
    ('better', '更好的', '八年级上册'),
    ('worse', '更差的', '八年级上册'),
    ('quietly', '安静地', '八年级上册'),
    ('loudly', '大声地', '八年级上册'),
    ('clearly', '清楚地', '八年级上册'),
    ('hard-working', '勤奋的', '八年级上册'),
    ('competition', '比赛；竞争', '八年级上册'),
    ('fantastic', '极好的', '八年级上册'),
    ('which', '哪一个', '八年级上册'),
    ('grade', '年级；成绩', '八年级上册'),
    ('similar', '相似的', '八年级上册'),
    ('necessary', '必要的', '八年级上册'),
    ('both', '两者都', '八年级上册'),
    ('should', '应该', '八年级上册'),
    ('example', '例子；榜样', '八年级上册'),
    ('excellent', '极好的；优秀的', '八年级上册'),
    ('comfortable', '舒适的', '八年级上册'),
    ('screen', '屏幕', '八年级上册'),
    ('close', '靠近的；关闭', '八年级上册'),
    ('cheaply', '便宜地', '八年级上册'),
    ('pretty', '漂亮的；相当', '八年级上册'),
    ('creative', '有创造力的', '八年级上册'),
    ('performer', '表演者', '八年级上册'),
    ('talent', '才能', '八年级上册'),
    ('common', '共同的；常见的', '八年级上册'),
    ('magician', '魔术师', '八年级上册'),
    ('beautifully', '漂亮地', '八年级上册'),
    ('role', '角色；作用', '八年级上册'),
    ('winner', '获胜者', '八年级上册'),
    ('prize', '奖品；奖金', '八年级上册'),
    ('everybody', '每人', '八年级上册'),
    ('choose', '选择', '八年级上册'),
    ('carefully', '小心地', '八年级上册'),
    ('fresh', '新鲜的', '八年级上册'),
    ('comfortably', '舒服地', '八年级上册'),
    ('writer', '作家', '八年级上册'),
    ('reporter', '记者', '八年级上册'),
    ('become', '变得；成为', '八年级上册'),
    ('main', '主要的', '八年级上册'),
    ('reason', '原因；理由', '八年级上册'),
    ('film', '电影', '八年级上册'),
    ('unlucky', '不幸的', '八年级上册'),
    ('lose', '丢失；输掉', '八年级上册'),
    ('ready', '准备好的', '八年级上册'),
    ('character', '角色；性格', '八年级上册'),
    ('simple', '简单的', '八年级上册'),
    ('army', '军队', '八年级上册'),
    ('action', '行动', '八年级上册'),
    ('educational', '有教育意义的', '八年级上册'),
    ('meaningless', '无意义的', '八年级上册'),
    ('enjoyable', '愉快的', '八年级上册'),
    ('discussion', '讨论', '八年级上册'),
    ('expect', '期待', '八年级上册'),
    ('though', '虽然；尽管', '八年级上册'),
    ('meaning', '意义；意思', '八年级上册'),
    ('stand', '站立；容忍', '八年级上册'),
    ('cinema', '电影院', '八年级上册'),
    ('joke', '玩笑', '八年级上册'),
    ('share', '分享；共用', '八年级上册'),
    ('foreign', '外国的', '八年级上册'),
    ('able', '能够的', '八年级上册'),
    ('reach', '到达；伸手', '八年级上册'),
    ('hand', '手；传递', '八年级上册'),
    ('touch', '触摸；感动', '八年级上册'),
    ('heart', '心脏；内心', '八年级上册'),
    ('fact', '事实；真相', '八年级上册'),
    ('break', '打破；弄坏', '八年级上册'),
    ('laugh', '笑；发笑', '八年级上册'),
    ('primary', '初级的；主要的', '八年级上册'),
    ('offer', '提供；出价', '八年级上册'),
    ('try', '尝试；努力', '八年级上册'),
    ('wonder', '想知道；惊奇', '八年级上册'),
    ('improve', '提高；改善', '八年级上册'),
    ('discuss', '讨论', '八年级上册'),
    ('difference', '不同；差异', '八年级上册'),
    ('bring', '带来', '八年级上册'),
    ('program', '节目；程序', '八年级上册'),
    ('hobby', '业余爱好', '八年级上册'),
    ('successful', '成功的', '八年级上册'),
    ('educational', '教育的', '八年级上册'),
    ('already', '已经', '八年级上册'),
    ('yet', '还；已经', '八年级上册'),
    ('ever', '曾经', '八年级上册'),
    ('never', '从不', '八年级上册'),
    ('just', '刚刚；仅仅', '八年级上册'),
    ('recently', '最近', '八年级上册'),
    ('abroad', '在国外', '八年级上册'),
    ('important', '重要的', '八年级上册'),
    ('probably', '很可能', '八年级上册'),
    ('seem', '似乎；好像', '八年级上册'),
    ('quite', '相当；十分', '八年级上册'),
    ('enough', '足够的；充分地', '八年级上册'),
    ('opinion', '意见；看法', '八年级上册'),
    ('relationship', '关系', '八年级上册'),
    ('communication', '交流；沟通', '八年级上册'),
    ('argue', '争论；辩论', '八年级上册'),
    ('instead', '代替；反而', '八年级上册'),
    ('offer', '主动提出；提供', '八年级上册'),
    ('communicate', '交流；沟通', '八年级上册'),
    ('elder', '年纪较长的', '八年级上册'),
    ('nervous', '紧张的', '八年级上册'),
    ('typical', '典型的', '八年级上册'),
    ('normal', '正常的；普通的', '八年级上册'),
    ('possibly', '可能地', '八年级上册'),
    ('physical', '身体的', '八年级上册'),
    ('result', '结果；后果', '八年级上册'),
    ('percent', '百分之…', '八年级上册'),
    ('online', '在线的', '八年级上册'),
    ('together', '在一起', '八年级上册'),
    ('although', '虽然；尽管', '八年级上册'),
    ('through', '通过；穿过', '八年级上册'),
    ('mind', '头脑；介意', '八年级上册'),
    ('question', '问题；疑问', '八年级上册'),
    ('habit', '习惯', '八年级上册'),
    ('moreover', '而且', '八年级上册'),
    ('least', '最小的；最少的', '八年级上册'),
    ('point', '观点；分数；点', '八年级上册'),
    ('travel', '旅行', '八年级上册'),
    ('weekday', '工作日', '八年级上册'),
    ('invite', '邀请', '八年级上册'),
    ('accept', '接受', '八年级上册'),
    ('prepare', '准备', '八年级上册'),
    ('available', '可获得的；有空的', '八年级上册'),
    ('forward', '向前', '八年级上册'),
    ('glad', '高兴的', '八年级上册'),
    ('without', '没有', '八年级上册'),
    ('surprise', '惊奇；使惊奇', '八年级上册'),
    ('glue', '胶水', '八年级上册'),
    ('suggestion', '建议', '八年级上册'),
    ('delete', '删除', '八年级上册'),
    ('flu', '流感', '八年级上册'),
    ('event', '大事；事件', '八年级上册'),
    ('guest', '客人；宾客', '八年级上册'),
    ('calendar', '日历', '八年级上册'),
    ('reply', '回答；回复', '八年级上册'),
    ('forward', '转交；发送', '八年级上册'),
    ('sad', '难过的；悲伤的', '八年级上册'),
    ('worried', '担心的', '八年级上册'),
    ('angry', '生气的', '八年级上册'),
    ('sorry', '抱歉的；难过的', '八年级上册'),
    ('advice', '建议', '八年级上册'),
    ('solve', '解决', '八年级上册'),
    ('trust', '信任', '八年级上册'),
    ('experience', '经验；经历', '八年级上册'),
    ('satisfy', '使满意', '八年级上册'),
    ('advise', '建议', '八年级上册'),
    ('situation', '情况；形势', '八年级上册'),
    ('certainly', '当然', '八年级上册'),
    ('understand', '理解', '八年级上册'),
    ('corner', '角落；拐角', '八年级上册'),
    ('explain', '解释', '八年级上册'),
    ('mistake', '错误', '八年级上册'),
    ('careful', '小心的', '八年级上册'),
    ('mine', '我的', '八年级上册'),
    ('theirs', '他/她们的', '八年级上册'),
    ('ours', '我们的', '八年级上册'),
    ('yours', '你的；你们的', '八年级上册'),
    ('hers', '她的', '八年级上册'),
    ('its', '它的', '八年级上册'),
    ('novel', '小说', '八年级上册'),
    ('page', '页；页码', '八年级上册'),
    ('pleased', '高兴的；满意的', '八年级上册'),
    ('attention', '注意', '八年级上册'),
    ('wonderful', '精彩的；绝妙的', '八年级上册'),
    ('scary', '恐怖的', '八年级上册'),
    ('relaxing', '令人放松的', '八年级上册'),
    ('boring', '无聊的', '八年级上册'),
    ('serious', '严肃的；认真的', '八年级上册'),
    ('outgoing', '外向的', '八年级上册'),
    ('once', '曾经；一旦', '八年级上册'),
    ('twice', '两次', '八年级上册'),
    ('full', '满的；饱的', '八年级上册'),
    ('result', '结果；成果', '八年级上册'),
    ('although', '虽然；即使', '八年级上册'),
    ('body', '身体', '八年级上册'),
    ('less', '较少的', '八年级上册'),
    ('least', '最少的', '八年级上册'),
    ('similar', '类似的', '八年级上册'),
    ('necessary', '必需的', '八年级上册'),
    ('education', '教育', '八年级上册'),
    ('popular', '流行的；受欢迎的', '八年级上册'),
    ('scientific', '科学的', '八年级上册'),
    ('perhaps', '也许；可能', '八年级上册'),
    ('machine', '机器', '八年级上册'),
    ('personal', '个人的；私人的', '八年级上册'),
    ('fight', '打架；争论', '八年级上册'),
    ('lonely', '孤独的', '八年级上册'),
    ('proper', '适当的；恰当的', '八年级上册'),
    ('pressure', '压力', '八年级上册'),
    ('compete', '竞争；对抗', '八年级上册'),
    ('continue', '继续；持续', '八年级上册'),
    ('compare', '比较', '八年级上册'),
    ('crazy', '疯狂的', '八年级上册'),
    ('cause', '造成；原因', '八年级上册'),
    ('usual', '通常的', '八年级上册'),
    ('offer', '提供；提议', '八年级上册'),
    ('support', '支持；帮助', '八年级上册'),
    ('development', '发展；发育', '八年级上册'),
    ('quickly', '快速地', '八年级上册'),
    ('fair', '公平的', '八年级上册'),
    ('unfair', '不公平的', '八年级上册'),
    ('repair', '修理；修补', '八年级上册'),
    ('trash', '垃圾；废物', '八年级上册'),
    ('stress', '压力；紧张', '八年级上册'),
    ('chore', '家务杂事', '八年级上册'),
    ('neighbor', '邻居', '八年级上册'),
    ('drop', '掉落；放弃', '八年级上册'),
    ('fairness', '公正；公平', '八年级上册'),
    ('illness', '疾病', '八年级上册'),
    ('independence', '独立', '八年级上册'),
    ('develop', '发展；培养', '八年级上册'),
    ('waste', '浪费；废弃物', '八年级上册'),
    ('provide', '提供；供给', '八年级上册'),
    ('anyway', '无论如何', '八年级上册'),
    ('neither', '两者都不', '八年级上册'),
    ('pass', '传递；通过', '八年级上册'),
    ('cheap', '便宜的', '八年级上册'),
    ('mirror', '镜子', '八年级上册'),
    ('matter', '问题；事情', '八年级下册'),
    ('sore', '疼痛的', '八年级下册'),
    ('stomachache', '胃痛', '八年级下册'),
    ('foot', '脚；英尺', '八年级下册'),
    ('neck', '颈；脖子', '八年级下册'),
    ('stomach', '胃；腹部', '八年级下册'),
    ('throat', '喉咙', '八年级下册'),
    ('fever', '发烧', '八年级下册'),
    ('lie', '躺；平躺', '八年级下册'),
    ('rest', '休息；剩余部分', '八年级下册'),
    ('cough', '咳嗽', '八年级下册'),
    ('toothache', '牙痛', '八年级下册'),
    ('headache', '头痛', '八年级下册'),
    ('break', '休息；打破', '八年级下册'),
    ('hurt', '受伤；疼痛', '八年级下册'),
    ('passenger', '乘客；旅客', '八年级下册'),
    ('trouble', '问题；苦恼', '八年级下册'),
    ('hit', '碰撞；打击', '八年级下册'),
    ('herself', '她自己', '八年级下册'),
    ('control', '控制；支配', '八年级下册'),
    ('spirit', '精神；心灵', '八年级下册'),
    ('death', '死；死亡', '八年级下册'),
    ('decision', '决定；抉择', '八年级下册'),
    ('sign', '标志；迹象', '八年级下册'),
    ('notice', '通知；注意', '八年级下册'),
    ('lonely', '孤独的；寂寞的', '八年级下册'),
    ('strong', '强壮的；强烈的', '八年级下册'),
    ('satisfaction', '满足；满意', '八年级下册'),
    ('joy', '高兴；愉快', '八年级下册'),
    ('owner', '所有者；主人', '八年级下册'),
    ('journey', '旅行；旅程', '八年级下册'),
    ('raise', '筹集；提高', '八年级下册'),
    ('several', '几个；数个', '八年级下册'),
    ('feeling', '感觉；感触', '八年级下册'),
    ('satisfy', '满足；使满意', '八年级下册'),
    ('imagine', '想象；设想', '八年级下册'),
    ('difficulty', '困难；难题', '八年级下册'),
    ('kindness', '仁慈；善良', '八年级下册'),
    ('understand', '理解；领会', '八年级下册'),
    ('change', '改变；变化', '八年级下册'),
    ('blind', '盲的；失明的', '八年级下册'),
    ('deaf', '聋的', '八年级下册'),
    ('specially', '特别地；专门地', '八年级下册'),
    ('fetch', '取来；拿来', '八年级下册'),
    ('train', '训练；火车', '八年级下册'),
    ('excited', '兴奋的；激动的', '八年级下册'),
    ('interested', '感兴趣的', '八年级下册'),
    ('carry', '拿；提；搬', '八年级下册'),
    ('train', '训练；培训', '八年级下册'),
    ('difference', '不同；差异', '八年级下册'),
    ('raise', '募集；提高', '八年级下册'),
    ('repair', '修理；修补', '八年级下册'),
    ('broken', '破碎的；坏掉的', '八年级下册'),
    ('wheel', '车轮；轮子', '八年级下册'),
    ('letter', '信；字母', '八年级下册'),
    ('clever', '聪明的；机灵的', '八年级下册'),
    ('understand', '理解；明白', '八年级下册'),
    ('opening', '开幕式； openings', '八年级下册'),
    ('shut', '关闭；关上', '八年级下册'),
    ('own', '自己的；拥有的', '八年级下册'),
    ('awful', '很坏的；极讨厌的', '八年级下册'),
    ('during', '在…期间', '八年级下册'),
    ('since', '自…以来', '八年级下册'),
    ('neighbor', '邻居', '八年级下册'),
    ('footstep', '脚步；脚步声', '八年级下册'),
    ('garbage', '垃圾；废料', '八年级下册'),
    ('fold', '折叠；对折', '八年级下册'),
    ('sweep', '打扫；清扫', '八年级下册'),
    ('floor', '地板；楼层', '八年级下册'),
    ('mess', '杂乱；不整洁', '八年级下册'),
    ('throw', '扔；投掷', '八年级下册'),
    ('neither', '两者都不', '八年级下册'),
    ('shirt', '衬衫', '八年级下册'),
    ('pass', '传递；通过', '八年级下册'),
    ('borrow', '借入；借用', '八年级下册'),
    ('lend', '借给；借出', '八年级下册'),
    ('finger', '手指', '八年级下册'),
    ('hate', '讨厌；厌恶', '八年级下册'),
    ('while', '当…时候；而', '八年级下册'),
    ('stress', '精神压力；紧张', '八年级下册'),
    ('waste', '浪费；垃圾', '八年级下册'),
    ('provide', '提供；供给', '八年级下册'),
    ('anyway', '无论如何；即使如此', '八年级下册'),
    ('develop', '发展；养成', '八年级下册'),
    ('fairness', '公正性；合理性', '八年级下册'),
    ('since', '自…以来；因为', '八年级下册'),
    ('fair', '合理的；公平的', '八年级下册'),
    ('unfair', '不合理的；不公平的', '八年级下册'),
    ('drop', '落下；掉下', '八年级下册'),
    ('illness', '疾病；生病', '八年级下册'),
    ('independent', '独立的；自主的', '八年级下册'),
    ('depend', '依靠；依赖', '八年级下册'),
    ('fairness', '公正；公平', '八年级下册'),
    ('cause', '原因；引起', '八年级下册'),
    ('usual', '通常的；平常的', '八年级下册'),
    ('neither', '两者都不；也不', '八年级下册'),
    ('while', '当...时候；然而', '八年级下册'),
    ('tail', '尾巴；尾部', '八年级下册'),
    ('excite', '使兴奋；使激动', '八年级下册'),
    ('crazy', '疯狂的；不理智的', '八年级下册'),
    ('instead', '代替；反而', '八年级下册'),
    ('offer', '提供；主动提出', '八年级下册'),
    ('support', '支持；帮助', '八年级下册'),
    ('development', '发展；成长', '八年级下册'),
    ('quickly', '迅速地；很快地', '八年级下册'),
    ('fair', '公平的；合理的', '八年级下册'),
    ('perhaps', '也许；可能', '八年级下册'),
    ('difficult', '困难的', '八年级下册'),
    ('shout', '呼喊；呼叫', '八年级下册'),
    ('realize', '意识到；实现', '八年级下册'),
    ('suddenly', '突然', '八年级下册'),
    ('strange', '奇怪的；陌生的', '八年级下册'),
    ('silence', '沉默；寂静', '八年级下册'),
    ('recently', '不久前；最近', '八年级下册'),
    ('terror', '恐怖；恐惧', '八年级下册'),
    ('truth', '真相；实情', '八年级下册'),
    ('whole', '全部的；整体的', '八年级下册'),
    ('memory', '记忆；回忆', '八年级下册'),
    ('report', '报道；报告', '八年级下册'),
    ('beat', '敲打；打败', '八年级下册'),
    ('realize', '理解；领会', '八年级下册'),
    ('complete', '完成；完整的', '八年级下册'),
    ('shocked', '震惊的', '八年级下册'),
    ('silence', '沉默；缄默', '八年级下册'),
    ('explain', '解释；说明', '八年级下册'),
    ('recent', '最近的', '八年级下册'),
    ('event', '事件；大事', '八年级下册'),
    ('passage', '章节；段落', '八年级下册'),
    ('student', '学生', '八年级下册'),
    ('completely', '完全地；彻底地', '八年级下册'),
    ('asleep', '睡着的', '八年级下册'),
    ('graduate', '毕业；毕业生', '八年级下册'),
    ('treasure', '珍宝；财富', '八年级下册'),
    ('island', '岛；岛屿', '八年级下册'),
    ('full', '满的；完全的', '八年级下册'),
    ('towards', '朝；向；对着', '八年级下册'),
    ('land', '陆地；土地；着陆', '八年级下册'),
    ('fiction', '小说；虚构', '八年级下册'),
    ('ship', '船', '八年级下册'),
    ('tool', '工具', '八年级下册'),
    ('gun', '枪；炮', '八年级下册'),
    ('mark', '迹象；标记；分数', '八年级下册'),
    ('sand', '沙；沙子', '八年级下册'),
    ('cannibal', '食人肉者', '八年级下册'),
    ('towards', '朝；向', '八年级下册'),
    ('land', '陆地；着陆', '八年级下册'),
    ('excitement', '激动；兴奋', '八年级下册'),
    ('band', '乐队；带子', '八年级下册'),
    ('forever', '永远', '八年级下册'),
    ('laughter', '笑声', '八年级下册'),
    ('beauty', '美；美丽', '八年级下册'),
    ('record', '记录；唱片', '八年级下册'),
    ('introduce', '介绍；引见', '八年级下册'),
    ('line', '行；排；线', '八年级下册'),
    ('introduction', '介绍；引进', '八年级下册'),
    ('success', '成功', '八年级下册'),
    ('belong', '属于', '八年级下册'),
    ('million', '百万', '八年级下册'),
    ('hundred', '百', '八年级下册'),
    ('thousand', '千', '八年级下册'),
    ('laugh', '笑；发笑', '八年级下册'),
    ('march', '行军；游行', '八年级下册'),
    ('achieve', '实现；达到', '八年级下册'),
    ('French', '法语；法国的', '八年级下册'),
    ('southern', '南方的', '八年级下册'),
    ('modern', '现代的；当代的', '八年级下册'),
    ('natural', '自然的', '八年级下册'),
    ('among', '在...之中；...之一', '八年级下册'),
    ('protect', '保护', '八年级下册'),
    ('include', '包括；包含', '八年级下册'),
    ('free', '自由的；免费的', '八年级下册'),
    ('conder', '考虑；认为', '八年级下册'),
    ('leader', '领导者；领袖', '八年级下册'),
    ('purpose', '目的；意图', '八年级下册'),
    ('awake', '醒着的', '八年级下册'),
    ('hardly', '几乎不', '八年级下册'),
    ('suddenly', '突然地', '八年级下册'),
    ('stone', '石头', '八年级下册'),
    ('silently', '沉默地', '八年级下册'),
    ('recently', '最近', '八年级下册'),
    ('instead', '代替', '八年级下册'),
    ('anyone', '任何人', '八年级下册'),
    ('somewhere', '在某处', '八年级下册'),
    ('beyond', '超出；超越', '八年级下册'),
    ('especially', '特别；尤其', '八年级下册'),
    ('discover', '发现；发觉', '八年级下册'),
    ('deep', '深的；深切的', '八年级下册'),
    ('offer', '提供；建议', '八年级下册'),
    ('surface', '表面；表层', '八年级下册'),
    ('perfect', '完美的；理想的', '八年级下册'),
    ('silver', '银；银色的', '八年级下册'),
    ('metal', '金属', '八年级下册'),
    ('rapid', '迅速的；快速的', '八年级下册'),
    ('progress', '进步；进展', '八年级下册'),
    ('secret', '秘密；秘诀', '八年级下册'),
    ('patient', '病人；耐心的', '八年级下册'),
    ('value', '价值；重视', '八年级下册'),
    ('trust', '信任；信赖', '八年级下册'),
    ('experience', '经历；体验', '八年级下册'),
    ('propose', '提议；求婚', '八年级下册'),
    ('write', '写；写作', '八年级下册'),
    ('collect', '收集；采集', '八年级下册'),
    ('actually', '实际上', '八年级下册'),
    ('simply', '简单地；仅仅', '八年级下册'),
    ('consider', '考虑；认为', '八年级下册'),
    ('hurry', '匆忙；赶快', '八年级下册'),
    ('return', '归还；返回', '八年级下册'),
    ('manage', '设法；管理', '八年级下册'),
    ('honest', '诚实的', '八年级下册'),
    ('regret', '后悔；遗憾', '八年级下册'),
    ('fascinating', '迷人的', '八年级下册'),
    ('peaceful', '和平的；平静的', '八年级下册'),
    ('rapid', '迅速的', '八年级下册'),
    ('unbelievable', '难以置信的', '八年级下册'),
    ('progress', '进步', '八年级下册'),
    ('social', '社交的；社会的', '八年级下册'),
    ('peace', '和平；安宁', '八年级下册'),
    ('perfect', '完美的', '八年级下册'),
    ('itself', '它自己', '八年级下册'),
    ('whether', '是否', '八年级下册'),
    ('whenever', '无论何时', '八年级下册'),
    ('northern', '北方的', '八年级下册'),
    ('especially', '尤其；特别', '八年级下册'),
    ('attract', '吸引', '八年级下册'),
    ('ancient', '古代的；古老的', '八年级下册'),
    ('treasure', '财富；珍宝', '八年级下册'),
    ('island', '岛屿', '八年级下册'),
    ('weekday', '工作日', '八年级下册'),
    ('lately', '最近；近来', '八年级下册'),
    ('counter', '柜台；计数器', '八年级下册'),
    ('particular', '特定的；特别的', '八年级下册'),
    ('gentle', '温和的；轻柔的', '八年级下册'),
    ('actually', '事实上；实际上', '八年级下册'),
    ('underground', '地下的', '八年级下册'),
    ('wallet', '钱包', '八年级下册'),
    ('sweet', '甜的；糖果', '八年级下册'),
    ('purse', '钱包；女用小包', '八年级下册'),
    ('march', '三月；行军', '八年级下册'),
    ('pronounce', '发音', '九年级'),
    ('increase', '增加；增长', '九年级'),
    ('speed', '速度；加速', '九年级'),
    ('partner', '搭档；伙伴', '九年级'),
    ('born', '天生的；出生的', '九年级'),
    ('ability', '能力；才能', '九年级'),
    ('brain', '大脑', '九年级'),
    ('active', '活跃的；积极的', '九年级'),
    ('attention', '注意；关注', '九年级'),
    ('connect', '连接；联系', '九年级'),
    ('overnight', '一夜之间', '九年级'),
    ('review', '复习；回顾', '九年级'),
    ('knowledge', '知识；学问', '九年级'),
    ('wisely', '明智地；聪明地', '九年级'),
    ('acquire', '获得；学到', '九年级'),
    ('outline', '大纲；轮廓', '九年级'),
    ('textbook', '教科书；课本', '九年级'),
    ('passage', '章节；段落', '九年级'),
    ('express', '表达；表示', '九年级'),
    ('discover', '发现；发觉', '九年级'),
    ('secret', '秘密；秘诀', '九年级'),
    ('looker', '观看者；检查员', '九年级'),
    ('term', '学期；术语', '九年级'),
    ('patient', '有耐心的；病人', '九年级'),
    ('repetition', '重复；反复', '九年级'),
    ('physics', '物理；物理学', '九年级'),
    ('chemist', '化学家；药剂师', '九年级'),
    ('pattern', '模式；方式', '九年级'),
    ('stranger', '陌生人', '九年级'),
    ('relative', '亲属；亲戚', '九年级'),
    ('steal', '偷；窃取', '九年级'),
    ('lay', '放置；安放；产卵', '九年级'),
    ('spread', '传播；展开', '九年级'),
    ('punish', '惩罚；处罚', '九年级'),
    ('warn', '警告；告诫', '九年级'),
    ('tradition', '传统', '九年级'),
    ('final', '最后的；最终的', '九年级'),
    ('folk', '民间的', '九年级'),
    ('hall', '大厅；礼堂', '九年级'),
    ('novel', '小说', '九年级'),
    ('eve', '前夕；前夜', '九年级'),
    ('ghost', '鬼；鬼魂', '九年级'),
    ('trick', '花招；把戏', '九年级'),
    ('treat', '招待；对待', '九年级'),
    ('spider', '蜘蛛', '九年级'),
    ('Christmas', '圣诞节', '九年级'),
    ('present', '礼物；现在的', '九年级'),
    ('dead', '死的；失去生命的', '九年级'),
    ('business', '生意；商业', '九年级'),
    ('warmth', '温暖；热情', '九年级'),
    ('spread', '传播；伸展', '九年级'),
    ('lie', '躺；位于；撒谎', '九年级'),
    ('admire', '钦佩；羡慕', '九年级'),
    ('tie', '领带；系；捆绑', '九年级'),
    ('circle', '圆圈；圈子', '九年级'),
    ('influence', '影响', '九年级'),
    ('private', '私人的；隐私的', '九年级'),
    ('request', '请求；要求', '九年级'),
    ('public', '公开的；公共的', '九年级'),
    ('suggestion', '建议', '九年级'),
    ('course', '课程；过程', '九年级'),
    ('avoid', '避免；回避', '九年级'),
    ('humorous', '幽默的；风趣的', '九年级'),
    ('silent', '不说话的；沉默的', '九年级'),
    ('helpful', '有帮助的', '九年级'),
    ('score', '得分；分数', '九年级'),
    ('background', '背景', '九年级'),
    ('interview', '采访；面试', '九年级'),
    ('Asian', '亚洲的；亚洲人', '九年级'),
    ('deal', '处理；对待', '九年级'),
    ('shyness', '害羞；腼腆', '九年级'),
    ('dare', '敢于；胆敢', '九年级'),
    ('crowd', '人群；拥挤', '九年级'),
    ('ton', '吨；大量', '九年级'),
    ('private', '私人的；私密的', '九年级'),
    ('guard', '守卫；警戒', '九年级'),
    ('require', '需要；要求', '九年级'),
    ('European', '欧洲的；欧洲人', '九年级'),
    ('African', '非洲的；非洲人', '九年级'),
    ('British', '英国的；英国人的', '九年级'),
    ('speech', '讲话；发言', '九年级'),
    ('public', '公众；公共的', '九年级'),
    ('ant', '蚂蚁', '九年级'),
    ('insect', '昆虫', '九年级'),
    ('influence', '影响；作用', '九年级'),
    ('seldom', '很少；不常', '九年级'),
    ('proud', '自豪的；骄傲的', '九年级'),
    ('absent', '缺席的；不在的', '九年级'),
    ('fail', '失败；未能做到', '九年级'),
    ('exactly', '确切地；准确地', '九年级'),
    ('pride', '自豪；骄傲', '九年级'),
    ('general', '总的；普遍的', '九年级'),
    ('introduction', '介绍；引言', '九年级'),
    ('conversation', '谈话；交谈', '九年级'),
    ('conclusion', '结论；结尾', '九年级'),
    ('related', '相关的；有联系的', '九年级'),
    ('energy', '精力；能量', '九年级'),
    ('imagine', '想象；设想', '九年级'),
    ('attitude', '态度', '九年级'),
    ('manage', '管理；设法完成', '九年级'),
    ('independent', '独立的；自主的', '九年级'),
    ('society', '社会', '九年级'),
    ('manner', '方式；举止；礼貌', '九年级'),
    ('polite', '有礼貌的', '九年级'),
    ('impolite', '无礼貌的', '九年级'),
    ('direct', '直接的；指导', '九年级'),
    ('address', '地址；演说', '九年级'),
    ('whom', '谁；什么人', '九年级'),
    ('underground', '地铁；地下的', '九年级'),
    ('parking', '停车', '九年级'),
    ('plenty', '大量；充足', '九年级'),
    ('corn', '玉米；谷物', '九年级'),
    ('university', '大学', '九年级'),
    ('ruler', '统治者；尺子', '九年级'),
    ('boil', '煮沸；烧开', '九年级'),
    ('remain', '保持；留下', '九年级'),
    ('situation', '情景；形势', '九年级'),
    ('symbol', '象征；标志', '九年级'),
    ('trade', '贸易；交易', '九年级'),
    ('attract', '吸引；引起', '九年级'),
    ('produce', '生产；制造', '九年级'),
    ('pleasant', '令人愉快的', '九年级'),
    ('surface', '表面；表层', '九年级'),
    ('material', '材料；原料', '九年级'),
    ('widely', '广泛地；普遍地', '九年级'),
    ('process', '过程；加工', '九年级'),
    ('complete', '完成；完整的', '九年级'),
    ('product', '产品；制品', '九年级'),
    ('local', '当地的；地方的', '九年级'),
    ('brand', '品牌；牌子', '九年级'),
    ('advertisement', '广告', '九年级'),
    ('situation', '形势；情况', '九年级'),
    ('transport', '运输；交通', '九年级'),
    ('postman', '邮递员', '九年级'),
    ('century', '世纪；百年', '九年级'),
    ('abroad', '在国外；到国外', '九年级'),
    ('wing', '翅膀；翼', '九年级'),
    ('bamboo', '竹子', '九年级'),
    ('section', '部分；区域', '九年级'),
    ('praise', '赞扬；表扬', '九年级'),
    ('ancient', '古代的；古老的', '九年级'),
    ('tower', '塔；塔楼', '九年级'),
    ('emperor', '皇帝', '九年级'),
    ('silk', '丝绸；丝织品', '九年级'),
    ('complete', '完成；结束', '九年级'),
    ('desert', '沙漠；抛弃', '九年级'),
    ('mystery', '神秘；奥秘', '九年级'),
    ('trade', '贸易；做买卖', '九年级'),
    ('valuable', '有价值的；宝贵的', '九年级'),
    ('taste', '品尝；味道', '九年级'),
    ('smell', '闻到；气味', '九年级'),
    ('remain', '仍然是；保持不变', '九年级'),
    ('national', '国家的；民族的', '九年级'),
    ('form', '形式；表格；形成', '九年级'),
    ('pleasure', '愉快；高兴', '九年级'),
    ('daily', '日常的；每日的', '九年级'),
    ('divide', '分开；划分', '九年级'),
    ('purpose', '目的；目标', '九年级'),
    ('astronaut', '宇航员', '九年级'),
    ('admire', '钦佩；欣赏', '九年级'),
    ('master', '掌握；主人', '九年级'),
    ('achievement', '成就；成绩', '九年级'),
    ('introduction', '介绍；引进', '九年级'),
    ('sail', '航行；起航', '九年级'),
    ('aboard', '在船上；上船', '九年级'),
    ('discovery', '发现；发觉', '九年级'),
    ('vehicle', '交通工具；车辆', '九年级'),
    ('unbelievable', '难以置信的', '九年级'),
    ('graduate', '毕业', '九年级'),
    ('congratulate', '祝贺', '九年级'),
    ('caring', '关心他人的；体贴的', '九年级'),
    ('section', '部分；节', '九年级'),
    ('gentle', '温柔的；轻柔的', '九年级'),
    ('poem', '诗；诗歌', '九年级'),
    ('single', '单个的；单一的', '九年级'),
    ('influence', '影响；作用于', '九年级'),
    ('sense', '感觉；意识', '九年级'),
    ('painting', '绘画；油画', '九年级'),
    ('sadness', '悲伤；悲痛', '九年级'),
    ('pain', '疼痛；痛苦', '九年级'),
    ('reflect', '反映；反射', '九年级'),
    ('perform', '表演；执行', '九年级'),
    ('recall', '回忆起；召回', '九年级'),
    ('wound', '伤口；创伤', '九年级'),
    ('master', '精通；掌握', '九年级'),
    ('method', '方法；办法', '九年级'),
    ('direction', '方向；指导', '九年级'),
    ('level', '水平；标准', '九年级'),
    ('certain', '确定的；一定的', '九年级'),
    ('according', '依照；根据', '九年级'),
    ('attention', '注意；留心', '九年级'),
    ('accidental', '意外的；偶然的', '九年级'),
    ('nearly', '几乎；差不多', '九年级'),
    ('invention', '发明；创造', '九年级'),
    ('inventor', '发明家；创造者', '九年级'),
    ('popularity', '普及；流行', '九年级'),
    ('doubt', '怀疑；疑惑', '九年级'),
    ('mention', '提到；说到', '九年级'),
    ('website', '网站', '九年级'),
    ('pioneer', '先驱；先锋', '九年级'),
    ('list', '列表；清单', '九年级'),
    ('technology', '技术', '九年级'),
    ('industry', '工业；行业', '九年级'),
    ('professional', '职业的；专业的', '九年级'),
    ('pleasure', '愉快；快乐', '九年级'),
    ('huge', '巨大的；庞大的', '九年级'),
    ('international', '国际的', '九年级'),
    ('experience', '经历；体验', '九年级'),
    ('sleepy', '困倦的；瞌睡的', '九年级'),
    ('remain', '保持；仍然是', '九年级'),
    ('painful', '痛苦的；疼痛的', '九年级'),
    ('express', '表达', '九年级'),
    ('spoken', '口语的；口头的', '九年级'),
    ('patient', '有耐心的；忍耐的', '九年级'),
    ('pronunciation', '发音；读音', '九年级'),
    ('speed', '速度；迅速', '九年级'),
    ('chemistry', '化学', '九年级'),
    ('pal', '伙伴；朋友', '九年级'),
    ('lifelong', '终身的；毕生的', '九年级'),
    ('wise', '明智的；聪明的', '九年级'),
    ('textbook', '教科书', '九年级'),
    ('memorize', '记住；熟记', '九年级'),
    ('grammar', '语法', '九年级'),
    ('sentence', '句子', '九年级'),
    ('pattern', '模式；句型', '九年级'),
    ('relative', '亲戚；亲属', '九年级'),
    ('lay', '放置；产卵', '九年级'),
    ('dessert', '甜点；甜品', '九年级'),
    ('garden', '花园；院子', '九年级'),
    ('treat', '款待；对待', '九年级'),
    ('warmth', '温暖；暖和', '九年级'),
    ('spread', '扩散；传播', '九年级'),
    ('lie', '位于；躺；撒谎', '九年级'),
    ('ancestors', '祖先；祖宗', '九年级'),
    ('private', '私人的；私有的', '九年级'),
    ('dare', '敢；敢于', '九年级'),
    ('speech', '发言；演讲', '九年级'),
    ('European', '欧洲的', '九年级'),
    ('African', '非洲的', '九年级'),
    ('British', '英国的', '九年级'),
    ('public', '大众；公共的', '九年级'),
    ('seldom', '很少', '九年级'),
    ('proud', '自豪的', '九年级'),
    ('absent', '缺席的', '九年级'),
    ('fail', '失败；不及格', '九年级'),
    ('exactly', '确切地', '九年级'),
    ('pride', '自豪', '九年级'),
    ('general', '总的；一般的', '九年级'),
    ('introduction', '介绍', '九年级'),
    ('conversation', '交谈；会话', '九年级'),
    ('conclusion', '结论', '九年级'),
    ('related', '有关的；相关的', '九年级'),
    ('energy', '能量；精力', '九年级'),
    ('manage', '管理；对付', '九年级'),
    ('independent', '独立的', '九年级'),
    ('impolite', '不礼貌的', '九年级'),
    ('direct', '直接的；指导的', '九年级'),
    ('whom', '谁', '九年级'),
    ('plenty', '充足；大量', '九年级'),
    ('corn', '谷物；玉米', '九年级'),
    ('product', '产品；产物', '九年级'),
    ('silk', '丝绸', '九年级'),
    ('mystery', '神秘的事物', '九年级'),
    ('valuable', '有价值的', '九年级'),
    ('national', '国家的', '九年级'),
    ('daily', '每日的；日常的', '九年级'),
    ('divide', '划分；分开', '九年级'),
    ('master', '掌握；精通', '九年级'),
    ('sail', '航；起航', '九年级'),
    ('discovery', '发现', '九年级'),
    ('method', '方法；方式', '九年级'),
    ('level', '水平；级别', '九年级'),
    ('according', '按照；根据', '九年级'),
    ('inventor', '发明家', '九年级'),
    ('popularity', '流行；人气', '九年级'),
    ('technology', '技术；科技', '九年级'),
    ('industry', '工业；产业', '九年级'),
    ('pronunciation', '发音', '九年级'),
    ('memorize', '记住；背', '九年级'),
]
BUILTIN_PHRASE_LIST = [ ('a few', '几个'),
  ('a little', '一点'),
  ('a lot of', '许多'),
  ('according to', '根据'),
  ('after all', '毕竟'),
  ('agree with', '同意'),
  ('all the time', '一直'),
  ('as long as', '只要'),
  ('as soon as', '一...就...'),
  ('as well', '也'),
  ('be afraid of', '害怕'),
  ('be angry with', '生...的气'),
  ('be born', '出生'),
  ('be busy with', '忙于'),
  ('be careful', '小心'),
  ('be different from', '与...不同'),
  ('be famous for', '以...闻名'),
  ('be fond of', '喜欢'),
  ('be full of', '充满'),
  ('be good at', '擅长'),
  ('be interested in', '对...感兴趣'),
  ('be late for', '迟到'),
  ('be made of', '由...制成'),
  ('be proud of', '为...骄傲'),
  ('be ready to', '准备好'),
  ('be responsible for', '对...负责'),
  ('be strict with', '对...严格'),
  ('be used to', '习惯于'),
  ('because of', '因为'),
  ('belong to', '属于'),
  ('both...and...', '两者都'),
  ('break down', '出故障'),
  ('break into', '闯入'),
  ('bring up', '抚养'),
  ('by accident', '偶然'),
  ('by mistake', '错误地'),
  ('by the way', '顺便说一下'),
  ('call back', '回电话'),
  ('call off', '取消'),
  ('care about', '关心'),
  ('carry out', '执行'),
  ('catch up with', '赶上'),
  ('check in', '办理入住'),
  ('check out', '退房'),
  ('cheer up', '振作起来'),
  ('come back', '回来'),
  ('come on', '加油；快点'),
  ('come out', '出来；出版'),
  ('come true', '实现'),
  ('communicate with', '与...交流'),
  ('compare with', '与...比较'),
  ('compete with', '与...竞争'),
  ('connect to', '连接'),
  ('cut down', '砍倒'),
  ('deal with', '处理'),
  ('depend on', '依靠'),
  ('die out', '灭绝'),
  ("do one's best", '尽力'),
  ('do well in', '在...做得好'),
  ('dream of', '梦想'),
  ('dress up', '打扮'),
  ('drop by', '顺便拜访'),
  ('each other', '彼此'),
  ('eat out', '外出就餐'),
  ('end up', '结束'),
  ('enjoy oneself', '玩得开心'),
  ('even if', '即使'),
  ('ever since', '自从'),
  ('every day', '每天'),
  ('fall asleep', '入睡'),
  ('fall down', '摔倒'),
  ('fall in love with', '爱上'),
  ('fall off', '掉下'),
  ('feel like', '想要'),
  ('fill in', '填写'),
  ('find out', '查明'),
  ('for example', '例如'),
  ('from now on', '从现在起'),
  ('from time to time', '不时'),
  ('get along with', '与...相处'),
  ('get away', '离开'),
  ('get back', '回来'),
  ('get in the way', '挡道'),
  ('get lost', '迷路'),
  ('get married', '结婚'),
  ('get off', '下车'),
  ('get on', '上车'),
  ('get over', '克服'),
  ('get ready for', '为...准备'),
  ('get together', '聚会'),
  ('get up', '起床'),
  ('give away', '赠送'),
  ('give back', '归还'),
  ('give out', '分发'),
  ('give up', '放弃'),
  ('go back', '回去'),
  ('go by', '经过'),
  ('go for a walk', '散步'),
  ('go off', '离开'),
  ('go on', '继续'),
  ('go out', '外出'),
  ('go over', '复习'),
  ('go through', '经历'),
  ('grow up', '长大'),
  ('hand in', '上交'),
  ('hand out', '分发'),
  ('hang out', '闲逛'),
  ('happen to', '发生在'),
  ('have a cold', '感冒'),
  ('have fun', '玩得开心'),
  ('have to', '不得不'),
  ('hear from', '收到...来信'),
  ('hold on', '稍等'),
  ('hurry up', '快点'),
  ('in a hurry', '匆忙'),
  ('in fact', '事实上'),
  ('in front of', '在...前面'),
  ('in order to', '为了'),
  ('in public', '公开地'),
  ('in the end', '最后'),
  ('in the future', '在未来'),
  ('in the morning', '在早上'),
  ('in time', '及时'),
  ('instead of', '代替'),
  ('join in', '参加'),
  ('jump down', '跳下'),
  ('keep away from', '远离'),
  ('keep on', '继续'),
  ('keep up with', '跟上'),
  ('knock at', '敲'),
  ('laugh at', '嘲笑'),
  ('lead to', '导致'),
  ('learn from', '向...学习'),
  ('leave for', '前往'),
  ('listen to', '听'),
  ('live on', '以...为生'),
  ('look after', '照顾'),
  ('look at', '看'),
  ('look for', '寻找'),
  ('look forward to', '期待'),
  ('look like', '看起来像'),
  ('look out', '小心'),
  ('look through', '浏览'),
  ('look up', '查阅'),
  ('make a decision', '做决定'),
  ('make a mistake', '犯错'),
  ('make a promise', '许下诺言'),
  ('make friends', '交朋友'),
  ('make noise', '制造噪音'),
  ('make progress', '取得进步'),
  ('make sure', '确保'),
  ('make up', '编造；弥补'),
  ("make up one's mind", '下定决心'),
  ('mix up', '混淆'),
  ('move away', '搬走'),
  ('move in', '搬进'),
  ('pay attention to', '注意'),
  ('pay for', '支付'),
  ('pick up', '捡起；接人'),
  ('point out', '指出'),
  ('prepare for', '准备'),
  ('put away', '收好'),
  ('put off', '推迟'),
  ('put on', '穿上'),
  ('put out', '扑灭'),
  ('put up', '张贴'),
  ('regard as', '视为'),
  ('run away', '逃跑'),
  ('run out of', '用完'),
  ('save up', '储蓄'),
  ('see off', '送行'),
  ('sell out', '售完'),
  ('send for', '派人去请'),
  ('separate from', '分离'),
  ('set off', '出发'),
  ('set up', '建立'),
  ('show up', '出现'),
  ('shut down', '关闭'),
  ('sit down', '坐下'),
  ('slow down', '减速'),
  ('so far', '到目前为止'),
  ('sort out', '整理'),
  ('stand up', '起立'),
  ('stay up', '熬夜'),
  ('stick to', '坚持'),
  ('stop doing', '停止做'),
  ('stop to do', '停下来去做'),
  ('succeed in', '成功'),
  ('take a break', '休息'),
  ('take a walk', '散步'),
  ('take after', '与...相像'),
  ('take away', '拿走'),
  ('take care of', '照顾'),
  ('take off', '起飞；脱下'),
  ('take out', '取出'),
  ('take part in', '参加'),
  ('take place', '发生'),
  ('take turns', '轮流'),
  ('talk about', '谈论'),
  ('talk with', '与...交谈'),
  ('teach oneself', '自学'),
  ('tell a story', '讲故事'),
  ('thanks to', '幸亏'),
  ('think about', '考虑'),
  ('think of', '想起'),
  ('throw away', '扔掉'),
  ('try on', '试穿'),
  ('try out', '试验'),
  ('turn down', '调低；拒绝'),
  ('turn off', '关掉'),
  ('turn on', '打开'),
  ('turn up', '调高；出现'),
  ('used to', '过去常常'),
  ('wait for', '等待'),
  ('wake up', '醒来'),
  ('walk into', '走进'),
  ('watch out', '小心'),
  ('work on', '从事于'),
  ('work out', '解决'),
  ('worry about', '担心'),
  ('write down', '写下'),
  ('write to', '写信给'),
  ('good morning', '早上好'),
  ('good afternoon', '下午好'),
  ('good evening', '晚上好'),
  ('good night', '晚安'),
  ('thank you', '谢谢你'),
  ('thanks a lot', '多谢'),
  ('nice to meet you', '很高兴见到你'),
  ('excuse me', '打扰一下；对不起'),
  ("what's your name", '你叫什么名字'),
  ('my name is', '我的名字是'),
  ('where are you from', '你来自哪里'),
  ('be from', '来自'),
  ('how old are you', '你多大了'),
  ('years old', '岁'),
  ('in English', '用英语'),
  ('give sb. sth.', '给某人某物'),
  ('here you are', '给你'),
  ("let's go", '让我们走吧'),
  ('want to do', '想要做'),
  ('would like to', '想要'),
  ('what about', '怎么样'),
  ('how about', '怎么样'),
  ('what time', '什么时间'),
  ('go to bed', '去睡觉'),
  ('have breakfast', '吃早餐'),
  ('have lunch', '吃午餐'),
  ('have dinner', '吃晚餐'),
  ('go to school', '去上学'),
  ('go home', '回家'),
  ('on weekdays', '在工作日'),
  ('on weekends', '在周末'),
  ('watch TV', '看电视'),
  ('do homework', '做作业'),
  ('play sports', '做运动'),
  ('play basketball', '打篮球'),
  ('play football', '踢足球'),
  ('play the piano', '弹钢琴'),
  ('play the guitar', '弹吉他'),
  ('by bus', '乘公共汽车'),
  ('by bike', '骑自行车'),
  ('by car', '乘小汽车'),
  ('by train', '乘火车'),
  ('by plane', '乘飞机'),
  ('by ship', '乘轮船'),
  ('on foot', '步行'),
  ('take a bus', '乘公共汽车'),
  ('take a taxi', '乘出租车'),
  ('at the bus stop', '在公共汽车站'),
  ('get to', '到达'),
  ('go along', '沿着...走'),
  ('turn left', '向左转'),
  ('turn right', '向右转'),
  ('across from', '在...对面'),
  ('next to', '紧挨着'),
  ('between...and...', '在...和...之间'),
  ('behind', '在...后面'),
  ('on the left', '在左边'),
  ('on the right', '在右边'),
  ('happy birthday', '生日快乐'),
  ('birthday party', '生日聚会'),
  ('make a wish', '许愿'),
  ('blow out', '吹灭'),
  ('cut the cake', '切蛋糕'),
  ('sing a song', '唱歌'),
  ('dance to music', '随着音乐跳舞'),
  ('take photos', '拍照'),
  ('have a good time', '玩得开心'),
  ("what's the weather like", '天气怎么样'),
  ('how is the weather', '天气怎么样'),
  ('fly a kite', '放风筝'),
  ('make a snowman', '堆雪人'),
  ('go swimming', '去游泳'),
  ('go hiking', '去徒步'),
  ('go camping', '去露营'),
  ('cheer on', '为...加油'),
  ('prefer...to...', '比起...更喜欢...'),
  ('quite a bit', '相当多'),
  ('spend time doing', '花时间做'),
  ('have a fever', '发烧'),
  ('have a cough', '咳嗽'),
  ('have a headache', '头痛'),
  ('have a stomachache', '胃痛'),
  ('see a doctor', '看医生'),
  ('take some medicine', '吃药'),
  ('lie down', '躺下'),
  ('have a rest', '休息'),
  ('drink enough water', '喝足够的水'),
  ('stay up late', '熬夜'),
  ('keep healthy', '保持健康'),
  ('collect stamps', '集邮'),
  ('listen to music', '听音乐'),
  ('watch movies', '看电影'),
  ('read books', '读书'),
  ("in one's free time", '在空闲时间'),
  ('be popular with', '受...欢迎'),
  ('all over the world', '全世界'),
  ('in the past', '在过去'),
  ('at present', '目前'),
  ('feel happy', '感到高兴'),
  ('feel sad', '感到悲伤'),
  ('feel angry', '感到生气'),
  ('feel worried', '感到担心'),
  ('feel excited', '感到兴奋'),
  ('calm down', '冷静下来'),
  ('go on a trip', '去旅行'),
  ('travel to', '去...旅行'),
  ('book a ticket', '预订票'),
  ('take photos', '拍照'),
  ('enjoy the scenery', '欣赏风景'),
  ('buy souvenirs', '买纪念品'),
  ('try local food', '品尝当地美食'),
  ('stay at a hotel', '住酒店'),
  ('junk food', '垃圾食品'),
  ('healthy food', '健康食品'),
  ('fast food', '快餐'),
  ('traditional food', '传统食物'),
  ('cook a meal', '做饭'),
  ('set the table', '摆餐具'),
  ('clear the table', '清理桌子'),
  ('wash dishes', '洗碗'),
  ('go shopping', '去购物'),
  ('on sale', '打折'),
  ('credit card', '信用卡'),
  ('cash on delivery', '货到付款'),
  ('keep in touch with', '与...保持联系'),
  ('achieve success', '取得成功'),
  ('economic development', '经济发展'),
  ('social progress', '社会进步'),
  ('educational reform', '教育改革'),
  ('protect the environment', '保护环境'),
  ('save energy', '节约能源'),
  ('reduce pollution', '减少污染'),
  ('recycle waste', '回收废物'),
  ('cut down trees', '砍伐树木'),
  ('global warming', '全球变暖'),
  ('climate change', '气候变化'),
  ('take action', '采取行动'),
  ('make a difference', '产生影响'),
  ('live a low-carbon life', '过低碳生活'),
  ('speak English', '说英语'),
  ('learn English', '学英语'),
  ('improve English', '提高英语'),
  ('English-speaking country', '英语国家'),
  ('native language', '母语'),
  ('foreign language', '外语'),
  ('translate into', '翻译成'),
  ('make friends with', '与...交朋友'),
  ('cultural difference', '文化差异'),
  ('How are you?', '你好吗？'),
  ('How do you do?', '你好！（初次见面）'),
  ('Good morning.', '早上好。'),
  ('Good afternoon.', '下午好。'),
  ('Good evening.', '晚上好。'),
  ('Good night.', '晚安。'),
  ('See you.', '再见。'),
  ('See you later.', '回头见。'),
  ('Take care.', '保重。'),
  ('Happy birthday!', '生日快乐！'),
  ('Congratulations!', '恭喜！'),
  ('Merry Christmas!', '圣诞快乐！'),
  ('Happy New Year!', '新年快乐！'),
  ('Thank you very much.', '非常感谢。'),
  ('You are welcome.', '不客气。'),
  ('I beg your pardon?', '请再说一遍？'),
  ('What is your name?', '你叫什么名字？'),
  ('My name is...', '我叫……'),
  ('Where are you from?', '你来自哪里？'),
  ('I am from...', '我来自……'),
  ('How old are you?', '你多大了？'),
  ('I am ... years old.', '我……岁。'),
  ("I don't understand.", '我不明白。'),
  ("I don't know.", '我不知道。'),
  ('Please say it again.', '请再说一遍。'),
  ('Please speak slowly.', '请说慢一点。'),
  ('What does ... mean?', '……是什么意思？'),
  ('How do you spell it?', '怎么拼写？'),
  ('Can you help me?', '你能帮我吗？'),
  ('May I ...?', '我可以……吗？'),
  ('You should ...', '你应该……'),
  ('You should not ...', '你不应该……'),
  ('You had better ...', '你最好……'),
  ('Why not ...?', '为什么不……？'),
  ('What about ...?', '……怎么样？'),
  ('Would you like to ...?', '你想……吗？'),
  ('I would love to.', '我很乐意。'),
  ("I'd love to, but ...", '我很想去，但是……'),
  ('It is very kind of you.', '你真好。'),
  ('again and again', '反复地'),
  ('all over', '遍及'),
  ('all right', '好的'),
  ('arrive in', '到达（大地方）'),
  ('arrive at', '到达（小地方）'),
  ('as usual', '像往常一样'),
  ('as...as', '和……一样'),
  ('ask for', '请求'),
  ('at first', '起初'),
  ('at last', '最后'),
  ('at least', '至少'),
  ('at most', '至多'),
  ('at once', '立刻'),
  ('at the same time', '同时'),
  ('at work', '在上班'),
  ('be able to', '能够'),
  ('be covered with', '被……覆盖'),
  ('be filled with', '充满'),
  ('be good for', '对……有益'),
  ('be made from', '由……制成（看不出原料）'),
  ('be pleased with', '对……满意'),
  ('be worth doing', '值得做'),
  ('before long', '不久以后'),
  ('break out', '爆发'),
  ('build up', '建立'),
  ('call up', '打电话给'),
  ('care for', '照顾'),
  ('carry on', '继续'),
  ('change into', '变成'),
  ('come down', '下来'),
  ('come from', '来自'),
  ('come up with', '想出'),
  ('cut up', '切碎'),
  ('divide into', '分成'),
  ('drop in', '顺便拜访'),
  ('eat up', '吃光'),
  ('either...or...', '要么……要么……'),
  ('even though', '虽然'),
  ('except for', '除了……之外'),
  ('face to face', '面对面'),
  ('fall behind', '落后'),
  ('far away', '遥远的'),
  ('for free', '免费'),
  ('for the time being', '暂时'),
  ('get close to', '接近'),
  ('get down to', '开始认真做'),
  ('get into trouble', '陷入麻烦'),
  ('give in', '屈服'),
  ('go abroad', '出国'),
  ('go away', '走开'),
  ('go fishing', '去钓鱼'),
  ('hang on', '坚持'),
  ('hang up', '挂断电话'),
  ('have trouble doing', '做……有困难'),
  ('help oneself to', '随便吃……'),
  ('hold up', '举起'),
  ('in all', '总共'),
  ('in common', '共同的'),
  ('in danger', '处于危险中'),
  ('in need of', '需要'),
  ('in other words', '换句话说'),
  ('in peace', '和平地'),
  ('in silence', '沉默地'),
  ('in surprise', '惊奇地'),
  ('in the way', '挡道'),
  ('just now', '刚才'),
  ('keep a diary', '写日记'),
  ('keep doing', '一直做'),
  ('keep off', '避开'),
  ('keep out', '不让……进入'),
  ('look ahead', '向前看'),
  ('look down upon', '看不起'),
  ('look into', '调查'),
  ('lots of', '许多'),
  ('make a living', '谋生'),
  ('make a noise', '吵闹'),
  ('make fun of', '取笑'),
  ('make use of', '利用'),
  ('mobile phone', '手机'),
  ('more and more', '越来越多'),
  ('neither...nor...', '既不……也不……'),
  ('no longer', '不再'),
  ('no matter', '无论'),
  ('not only...but also...', '不仅……而且……'),
  ('now and then', '偶尔'),
  ('of course', '当然'),
  ('on board', '在船上'),
  ('on business', '出差'),
  ('on display', '展出'),
  ('on duty', '值日'),
  ('on show', '展出'),
  ('on the phone', '在通电话'),
  ('on time', '准时'),
  ('on vacation', '在度假'),
  ('once again', '再一次'),
  ('once more', '再一次'),
  ('one after another', '一个接一个'),
  ('ought to', '应该'),
  ('out of breath', '上气不接下气'),
  ('out of sight', '看不见'),
  ('over and over again', '反复地'),
  ('play a role in', '在……中起作用'),
  ('play with', '玩弄'),
  ('plenty of', '大量的'),
  ('point at', '指着'),
  ('practise doing', '练习做……'),
  ('prevent...from...', '防止……做……'),
  ('put down', '放下'),
  ('quarrel with', '与……争吵'),
  ('rather than', '而不是'),
  ('rush hour', '高峰时间'),
  ("save one's life", '拯救某人的生命'),
  ('search for', '搜寻'),
  ('set free', '释放'),
  ('set out', '出发'),
  ('set an example', '树立榜样'),
  ('shake hands', '握手'),
  ('shout at', '对……大声叫嚷'),
  ('show off', '炫耀'),
  ('shut up', '闭嘴'),
  ('side by side', '肩并肩'),
  ('so that', '以便'),
  ('speak highly of', '高度评价'),
  ('spend...on...', '在……上花费……'),
  ('stand for', '代表'),
  ('stop...from...', '阻止……做……'),
  ('such as', '例如'),
  ('suit...to...', '适合……'),
  ('take a message', '捎口信'),
  ('take charge of', '负责'),
  ('take it easy', '别紧张'),
  ('take pride in', '为……感到自豪'),
  ('take the place of', '取代'),
  ('the more...the more...', '越……越……'),
  ('to be honest', '说实话'),
  ("to one's surprise", '令某人吃惊的是'),
  ("try one's best", '尽力'),
  ('turn into', '变成'),
  ('up and down', '上上下下'),
  ('up to', '多达'),
  ('would rather...than...', '宁愿……而不愿……'),
  ('at home', '在家'),
  ('at school', '在学校'),
  ('by subway', '乘地铁'),
  ('play volleyball', '打排球'),
  ('play tennis', '打网球'),
  ('play ping-pong', '打乒乓球'),
  ('play the violin', '拉小提琴'),
  ('draw pictures', '画画'),
  ('sing songs', '唱歌'),
  ('dance', '跳舞'),
  ('swim', '游泳'),
  ('run', '跑步'),
  ('jump', '跳'),
  ('walk', '走路'),
  ('ride a bike', '骑自行车'),
  ('help each other', '互相帮助'),
  ('study hard', '努力学习'),
  ('go skating', '去滑冰'),
  ('go skiing', '去滑雪'),
  ('go climbing', '去爬山'),
  ('write letters', '写信'),
  ('send emails', '发电子邮件'),
  ('make a call', '打电话'),
  ('do sports', '做运动'),
  ('eat vegetables', '吃蔬菜'),
  ('drink milk', '喝牛奶'),
  ('get up early', '早起'),
  ('do morning exercises', '做早操'),
  ('have a toothache', '牙痛'),
  ('take medicine', '吃药'),
  ('drink more water', '多喝水'),
  ('be ill', '生病'),
  ('be healthy', '健康的'),
  ('do exercise', '锻炼'),
  ('warm up', '热身'),
  ('cool down', '放松'),
  ('win the game', '赢得比赛'),
  ('lose the game', '输掉比赛'),
  ('play against', '与……对抗'),
  ('stay at home', '待在家里'),
  ('visit museums', '参观博物馆'),
  ('pass the exam', '通过考试'),
  ('fail the exam', '考试不及格'),
  ('get good grades', '取得好成绩'),
  ('study for a test', '备考'),
  ('work hard', '努力工作'),
  ('find a job', '找工作'),
  ('make money', '赚钱'),
  ('save money', '省钱'),
  ('spend money', '花钱'),
  ('borrow money', '借钱'),
  ('lend money', '借出钱'),
  ('buy gifts', '买礼物'),
  ('give presents', '送礼物'),
  ('have a party', '举办聚会'),
  ('make a cake', '做蛋糕'),
  ('light candles', '点蜡烛'),
  ('sing birthday song', '唱生日歌'),
  ('blow out candles', '吹蜡烛'),
  ('order food', '点餐'),
  ('pay the bill', '付账'),
  ('leave a message', '留言'),
  ('at the train station', '在火车站'),
  ('at the airport', '在机场'),
  ('ride in a car', '坐小汽车'),
  ('traffic jam', '交通堵塞'),
  ('traffic lights', '交通灯'),
  ('cross the road', '过马路'),
  ('walk on the sidewalk', '在人行道上走'),
  ('stop at the red light', '红灯停'),
  ('go at the green light', '绿灯行'),
  ('pollute the environment', '污染环境'),
  ('plant trees', '植树'),
  ('save water', '节约用水'),
  ('save electricity', '节约用电'),
  ('throw rubbish', '扔垃圾'),
  ('clean up', '打扫干净'),
  ('beautiful scenery', '美丽的风景'),
  ('places of interest', '名胜古迹'),
  ('take a vacation', '去度假'),
  ('go sightseeing', '去观光'),
  ('book a hotel', '预订酒店'),
  ('room service', '客房服务'),
  ('go boating', '去划船'),
  ('take a tour', '参加旅游'),
  ('guide book', '指南书'),
  ('travel agency', '旅行社'),
  ('on the way', '在路上'),
  ('no way', '决不'),
  ('lose way', '迷路'),
  ('lead the way', '带路'),
  ('feel nervous', '感到紧张'),
  ('feel relaxed', '感到放松'),
  ('feel proud', '感到骄傲'),
  ('feel sorry', '感到抱歉'),
  ('encourage sb. to do', '鼓励某人做'),
  ('support sb.', '支持某人'),
  ('keep trying', '继续努力'),
  ('achieve dream', '实现梦想'),
  ('succeed in doing', '成功做……'),
  ('fail to do', '未能做……'),
  ('be busy doing', '忙于做……'),
  ('be used to doing', '习惯于做……'),
  ('look forward to doing', '期待做……'),
  ('devote to doing', '致力于做……'),
  ('believe in', '相信……'),
  ('complain about', '抱怨……'),
  ('argue with', '与……争吵'),
  ('disagree with', '不同意……'),
  ('share with', '与……分享'),
  ('help with', '帮助做……'),
  ('provide with', '提供……'),
  ('fill with', '用……装满'),
  ('cover with', '用……覆盖'),
  ('connect with', '与……连接'),
  ('get on with', '与……相处'),
  ('come along with', '随同……'),
  ('go on with', '继续做……'),
  ('have something to do with', '与……有关'),
  ('have nothing to do with', '与……无关'),
  ('merry Christmas', '圣诞快乐'),
  ('happy New Year', '新年快乐'),
  ('you are welcome', '不客气'),
  ('I am sorry', '对不起'),
  ('that is OK', '没关系'),
  ('no problem', '没问题'),
  ('I think so', '我认为是这样'),
  ('I do not think so', '我不认为是这样'),
  ('maybe', '也许'),
  ('certainly', '当然'),
  ('sure', '确定'),
  ('I see', '我明白了'),
  ('I know', '我知道'),
  ('I do not know', '我不知道'),
  ('be bad for', '对...有害'),
  ('be same as', '与...相同'),
  ('be friendly to', '对...友好'),
  ('be strict in', '对...严格（某事）'),
  ('be used for', '被用来做...'),
  ('be used by', '被...使用'),
  ('be used as', '被用作...'),
  ('used to do', '过去常常做...'),
  ('have a sore throat', '喉咙痛'),
  ('take exercise', '锻炼'),
  ('keep fit', '保持健康'),
  ('keep silence', '保持安静'),
  ("keep one's word", '守信'),
  ("break one's word", '不守信'),
  ('make sense', '有意义'),
  ('in the beginning', '在开始时'),
  ('from then on', '从那时起'),
  ('sooner or later', '迟早'),
  ('time and time again', '反复地'),
  ('at the moment', '此刻'),
  ('right now', '现在'),
  ('right away', '立刻'),
  ('in fear', '恐惧地'),
  ('in joy', '高兴地'),
  ('in anger', '愤怒地'),
  ('in search of', '寻找...'),
  ('in charge of', '负责...'),
  ('in memory of', '纪念...'),
  ('in honor of', '为向...表示敬意'),
  ('in favor of', '支持...'),
  ('in case of', '假如...'),
  ('in spite of', '尽管...'),
  ('first of all', '首先'),
  ('to begin with', '首先'),
  ('secondly', '第二'),
  ('besides', '此外'),
  ('what is more', '而且'),
  ('moreover', '此外'),
  ('in addition', '另外'),
  ('finally', '最后'),
  ('in conclusion', '总之'),
  ('in summary', '总结'),
  ('on the one hand', '一方面'),
  ('on the other hand', '另一方面'),
  ('however', '然而'),
  ('nevertheless', '然而'),
  ('therefore', '因此'),
  ('thus', '因此'),
  ('as a result', '结果'),
  ('due to', '由于'),
  ('so as to', '以便'),
  ('such that', '如此...以至于...'),
  ('too...to...', '太...而不能...'),
  ('enough to', '足够做...'),
  ('develop rapidly', '发展迅速'),
  ('change a lot', '变化很大'),
  ('improve the environment', '改善环境'),
  ('plant more trees', '种更多的树'),
  ('public transport', '公共交通'),
  ('traffic accident', '交通事故'),
  ('obey the traffic rules', '遵守交通规则'),
  ('break the traffic rules', '违反交通规则'),
  ('on the sidewalk', '在人行道上'),
  ('get on the bus', '上车'),
  ('get off the bus', '下车'),
  ('wait for the bus', '等公共汽车'),
  ('miss the bus', '错过公共汽车'),
  ('catch the bus', '赶上公共汽车'),
  ('never mind', '没关系'),
  ('congratulations', '恭喜'),
  ('well done', '干得好'),
  ('what a pity', '真遗憾'),
  ('what a shame', '真可惜'),
  ('I hope so', '我希望如此'),
  ('I hope not', '我希望不会'),
  ('I am afraid so', '恐怕是这样的'),
  ('I am afraid not', '恐怕不是这样的'),
  ("I don't think so", '我不这样认为'),
  ('perhaps', '也许'),
  ('probably', '可能'),
  ('exactly', '确切地'),
  ('absolutely', '绝对地'),
      ('above all', '首先；尤其是'),
  ('absence from', '缺席；不接受'),
  ('accept ... as', '接受...为；认为...是'),
  ("achieve one's goal", "实现目标"),
  ('act as', '充当；担任'),
  ('add ... to ...', '把...加到...上'),
  ('add up to', '合计达；总共是'),
  ('add up', '加起来；合计'),
  ('admit doing sth.', '承认做过某事'),
  ('advise sb. (not) to do', '建议某人（不）做'),
  ('afford to do sth.', '负担得起做某事'),
  ('afraid of doing', '害怕做某事'),
  ('after a while', '过了一会儿'),
  ('again and again', '一再；反复'),
  ('agree on', '就...达成一致'),
  ('agree to do sth.', '同意做某事'),
  ('agree with sb.', '同意某人的看法'),
  ('ahead of', '在...前面；早于'),
  ('ahead of time', '提前'),
  ('aim at', '瞄准；旨在'),
  ('all at once', '突然；忽然'),
  ('all kinds of', '各种各样'),
  ('all of a sudden', '突然'),
  ('all over', '到处；遍及'),
  ('all over the country', '全国各地'),
  ('all the best', '万事如意'),
  ('all the same', '仍然；照样'),
  ('allow doing sth.', '允许做某事'),
  ('allow sb. to do', '允许某人做'),
  ('along with', '连同...一起；随同'),
  ('and so on', '等等'),
  ('angry with sb. for sth.', '因某事生某人的气'),
  ('answer the phone', '接电话'),
  ('apologize to sb. for sth.', '因某事向某人道歉'),
  ('appeal to', '对...有吸引力；呼吁'),
  ('apply for', '申请'),
  ('apply to', '适用于；应用于'),
  ('argue with sb. about sth.', '与某人争论某事'),
  ('around the world', '全世界'),
  ('arrive at/in', '到达（小/大地点）'),
  ('as ... as one can', '尽可能...地'),
  ('as a matter of fact', '事实上；其实'),
  ('as a result', '结果'),
  ('as a result of', '由于...的结果'),
  ('as a whole', '总体上'),
  ('as early as possible', '尽早'),
  ('as far as I know', '据我所知'),
  ('as follows', '如下'),
  ('as for / as to', '关于；至于'),
  ('as if / as though', '好像；仿佛'),
  ('as long as', '只要'),
  ('as many/much as possible', '尽可能多地'),
  ('as soon as', '一...就...'),
  ('as usual', '像往常一样'),
  ('as well', '也；还'),
  ('as well as', '既...又...；除...之外'),
  ('ask for advice/ help', '寻求建议/帮助'),
  ('ask for leave', '请假'),
  ('ask sb. for sth.', '向某人要某物'),
  ('at a time', '一次；每次'),
  ('at all costs', '不惜任何代价'),
  ('at all', '根本；究竟（否定句）'),
  ('at first', '起初；开始时'),
  ('at home and abroad', '国内外'),
  ('at last', '最后；终于'),
  ('at least', '至少'),
  ('at leisure', '有空；闲暇'),
  ('at lunch', '在午餐时'),
  ('at most', '最多'),
  ('at no time', '决不'),
  ('at once', '立刻；马上'),
  ('at one time', '曾经；一度'),
  ('at present', '目前'),
  ('at risk', '处于危险中'),
  ('at school', '在学校'),
  ("at somebody's expense", "由某人付费"),
  ('at the age of', '在...岁时'),
  ('at the beginning of', '在...之初'),
  ('at the bottom of', '在...底部'),
  ('at the cost of', '以...为代价'),
  ('at the end of', '在...末尾'),
  ('at the foot of', '在...脚下'),
  ('at the moment', '此刻；现在'),
  ('at the same time', '同时'),
  ('at the top of', '在...顶部'),
  ('at times', '有时；偶尔'),
  ('at work', '在工作'),
  ('attend a meeting', '参加会议'),
  ('attend a concert', '参加音乐会'),
  ('attach importance to', '重视'),
  ('avoid doing sth.', '避免做某事'),
  ('back and forth', '来回地；反复地'),
  ('be able to do', '能够做'),
  ('be about to do sth.', '即将做某事'),
  ('be absorbed in', '专心于；全神贯注于'),
  ('be active in', '活跃于；积极参加'),
  ('be afraid of', '害怕'),
  ('be angry with', '生某人的气'),
  ('be anxious about', '担心；焦虑'),
  ('be busy with / in', '忙于（某事/做）'),
  ('be careful about', '小心；注意'),
  ('be caught in the rain', '淋雨'),
  ('be close to', '接近；靠近'),
  ('be connected with', '与...有联系'),
  ('be covered with', '被...覆盖'),
  ('be different from', '与...不同'),
  ('be divided into', '被分成'),
  ('be famous / well-known for', '因...而著名'),
  ('be familiar to / with', '为...所熟悉/熟悉'),
  ('be far from', '远离；远非'),
  ('be fit for', '适合'),
  ('be fond of', '喜欢；喜爱'),
  ('be friendly to', '对...友好'),
  ('be full of', '充满'),
  ('be good at', '擅长'),
  ('be good for', '对...有益'),
  ('be good / kind to', '对...好/友善'),
  ('be grateful to sb. for sth.', '因某事感谢某人'),
  ('be happy with', '对...满意/高兴'),
  ('be harmful to', '对...有害'),
  ('be interested in', '对...感兴趣'),
  ('be known as', '被称为；被认为是'),
  ('be late for', '迟到'),
  ('be located in', '位于'),
  ('be mad with', '气疯了；对...发怒'),
  ('be made from/of', '由...制成（化学/物理变化）'),
  ('be made up of', '由...组成'),
  ('be pleased with', '对...满意'),
  ('be popular with', '受...欢迎'),
  ('be proud of', '以...自豪/骄傲'),
  ('be ready for', '为...做好准备'),
  ('be related to', '与...相关'),
  ('be responsible for', '负责；对...负责'),
  ('be rich in', '富含'),
  ('be rude to', '对...粗鲁'),
  ('be satisfied with', '对...满意'),
  ('be scared of', '害怕'),
  ('be seated', '坐下；就座'),
  ('be short of', '短缺；缺乏'),
  ('be sick of', '厌倦；厌烦'),
  ('be similar to', '与...相似'),
  ('be sorry for/about', '为...遗憾/抱歉'),
  ('be strict in / with', '严格要求（自己/他人）'),
  ('be strong in', '擅长'),
  ('be surprised at', '对...感到惊讶'),
  ('be supposed to do', '应该做；被期望做'),
  ('be sure of / about', '确信；对...有把握'),
  ('be terrified of', '非常害怕'),
  ('be tired of', '厌倦于'),
  ('be used to do', '被用来做'),
  ('be used to doing', '习惯于做'),
  ('be worried about', '担心'),
  ('be worth doing', '值得做'),
  ('bear / keep in mind', '记住；牢记'),
  ('because of', '因为；由于'),
  ('before long', '不久以后'),
  ("beg one's pardon", "请原谅；请再说一遍"),
  ('begin / start with', '以...开始'),
  ('believe in', '信仰；信任'),
  ('belong to', '属于'),
  ('beyond question', '毫无疑问'),
  ('bit by bit', '逐渐地；一点一点地'),
  ('blame sb. for sth.', '因某事责备某人'),
  ('blow away', '吹走'),
  ('blow down', '吹倒'),
  ('blow out', '吹灭'),
  ('break away from', '脱离；逃离'),
  ('break down', '出故障；分解；（身体）垮掉'),
  ('break into', '闯入；破门而入'),
  ('break off', '折断；中断'),
  ('break out', '爆发（战争、火灾等）'),
  ('break the law', '违反法律'),
  ('break the record', '打破记录'),
  ('break through', '突破'),
  ('break up', '破碎；解散；分手'),
  ('bring about', '引起；导致'),
  ('bring back', '带回来；使回忆起'),
  ('bring down', '降低；击落'),
  ('bring forward', '提出；提前'),
  ('bring in', '引进；赚得；收获'),
  ('bring out', '出版；生产；阐明'),
  ('bring up', '抚养；养育；呕吐；提出'),
  ('build up', '逐步建立；增强；积累'),
  ('burn down', '烧毁'),
  ('burn up', '烧光'),
  ('burst into laughter / tears', '大笑起来/大哭起来'),
  ('by accident / chance', '偶然；意外地'),
  ('by air / bus / car / train', '乘飞机/公交/车/火车'),
  ('by all means', '当然可以；一定'),
  ('by means of', '用；依靠'),
  ('by mistake', '错误地；无意中'),
  ('by no means', '绝不'),
  ('by oneself', '独自地；单独地'),
  ('by the end of', '到...末为止'),
  ('by the way', '顺便说一声'),
  ('by turns', '轮流'),
  ('call at / on', '拜访（某地/某人）'),
  ('call for', '要求；需要；号召'),
  ('call in', '召集；召来；来访'),
  ('call off', '取消'),
  ('call on / upon sb. to do', '号召/请求某人做'),
  ('call up', '打电话；召集；使人想起'),
  ('care about', '关心；在乎'),
  ('care for', '照顾；喜欢'),
  ('carry forward', '推进；发扬'),
  ('carry off', '夺走；成功完成'),
  ('carry on', '继续；进行'),
  ('carry out', '执行；贯彻；开展'),
  ('catch cold', '感冒'),
  ('catch fire', '着火'),
  ('catch hold of', '抓住'),
  ("catch one's breath", "喘口气；屏息"),
  ("catch one's eye", "引人注目"),
  ('catch sight of', '发现；看见'),
  ('catch up with', '赶上'),
  ("change one's mind", "改变主意"),
  ('cheer up', '振作起来；高兴起来'),
  ('clear away', '清除；消失'),
  ('clear up', '清理；放晴；（病情）好转'),
  ('come across', '偶然遇到；偶然发现'),
  ('come along', '一起来；进展'),
  ('come back', '回来；回想起来'),
  ('come down', '下降；落下'),
  ('come for', '来取；来找'),
  ('come from', '来自'),
  ('come into being / existence', '形成；产生；出现'),
  ('come into effect', '生效'),
  ('come into use', '开始使用'),
  ('come off', '成功；脱落；举行'),
  ('come on', '快点；加油；开始'),
  ('come out', '开花；出版；结果是'),
  ('come round / around', '恢复知觉；苏醒；顺便来访'),
  ('come to', '共计；达到；苏醒'),
  ('come true', '实现'),
  ('come up', '走近；发生；被提出'),
  ('come up with', '想出；提出'),
  ('compare ... to ...', '把...比作...'),
  ('compare ... with ...', '把...和...比较'),
  ('connect ... with ...', '把...和...连接起来'),
  ('consider ... (as) ...', '把...视为...'),
  ('consider doing', '考虑做某事'),
  ('continue to do / doing', '继续做'),
  ('contribute to', '有助于；贡献；捐献'),
  ('copy from', '抄袭；模仿'),
  ('count on / upon', '依赖；指望'),
  ('cover an area of ...', '占地面积...'),
  ('cut down', '砍倒；削减'),
  ('cut in', '插嘴；超车'),
  ('cut off', '切断；中断；隔绝'),
  ('cut out', '删去；剪下；停止'),
  ('cut up', '切碎'),
  ('day and night', '日夜；昼夜'),
  ('deal with / do with', '处理；对待'),
  ('depend on / upon', '依靠；取决于'),
  ('die from / of', '死于（外因/内因）'),
  ('die out', '灭绝；消失'),
  ('differ from', '不同于；与...不同'),
  ('dig up', '挖掘出；发现'),
  ('do damage to', '对...造成损害'),
  ('do experiments', '做实验'),
  ('do good to', '对...有益'),
  ('do harm to', '对...有害'),
  ('do morning exercises', '做早操'),
  ("do one's best", "尽最大努力"),
  ("do one's homework", "做作业"),
  ('do sb. a favor', '帮某人一个忙'),
  ('do some cleaning / shopping', '大扫除/购物'),
  ('do sports / exercise', '做运动/锻炼'),
  ('do well in', '在...方面做得好'),
  ('dream of / about', '梦想；渴望'),
  ('drop in / by / over', '顺道拜访'),
  ('due to', '由于；因为'),
  ('each other', '互相'),
  ("earn one's living", "谋生；糊口"),
  ('eat up', '吃光'),
  ('either ... or ...', '或者...或者...'),
  ('encourage sb. to do', '鼓励某人做'),
  ('enjoy oneself', '过得愉快'),
  ('equal to', '等于；能胜任'),
  ('escape from', '从...逃跑；逃避'),
  ('even if / though', '即使；虽然'),
  ('ever since then', '自从那时起'),
  ('every now and then', '不时；常常'),
  ('every other day', '每隔一天'),
  ('except for', '除了...之外（整体肯定局部除外）'),
  ('face to face', '面对面'),
  ('fall asleep', '入睡'),
  ('fall behind', '落后'),
  ('fall ill', '生病'),
  ('fall into', '落入；陷入'),
  ('fall off', '从...跌落；下降'),
  ('fall to pieces', '崩塌；破碎'),
  ('far from', '远非；完全不'),
  ('feel like doing', '想要做'),
  ('figure out', '弄清楚；计算出'),
  ('fill ... with ...', '用...装满...'),
  ('find out', '查明；发现'),
  ('fire at / on', '向...开火'),
  ('first of all', '首先'),
  ("fix one's eyes on", "注视；凝视"),
  ('focus on', '集中（注意力等）于'),
  ('fond of', '喜欢；爱好'),
  ('for a while', '暂时；一会儿'),
  ('for ever / forever', '永远'),
  ('for example / instance', '例如'),
  ('free of charge', '免费'),
  ('from generation to generation', '一代又一代'),
  ('from now on', '从今往后'),
  ('from place to place', '到处；从一个地方到另一个地方'),
  ('from time to time', '时常；不时'),
  ('from ... to ...', '从...到...'),
  ('gain / get / have access to', '可以获得；可以使用'),
  ('gather together', '聚集在一起'),
  ('generally speaking', '一般来说'),
  ('get / be used to (doing)', '习惯于（做）'),
  ('get along / on (with)', '（与...）相处；进展'),
  ('get around / round', '传开；四处走动'),
  ('get away (from)', '逃脱；离开'),
  ('get back', '回来；取回'),
  ('get close to', '接近；靠近'),
  ('get down to', '开始认真处理'),
  ('get hold of', '抓住；得到'),
  ('get in', '进入；到达；收割'),
  ('get into', '进入；养成（习惯）；陷入'),
  ('get into trouble', '陷入麻烦'),
  ('get off', '下车；脱下（衣服）'),
  ('get on / onto', '上车；登上；取得进展'),
  ('get on (well) with', '与...相处（融洽）'),
  ('get out', '出去；泄露；出版'),
  ('get over', '克服；从（疾病、打击中）恢复'),
  ('get rid of', '摆脱；除去'),
  ('get through', '通过；接通电话；完成'),
  ('get together', '聚会；相聚'),
  ('get up', '起床；起立'),
  ('give / lend a hand (to)', '帮助（某人）'),
  ('give a talk / speech', '做演讲/报告'),
  ('give away', '赠送；泄露；分发'),
  ('give back', '归还'),
  ('give in', '屈服；让步'),
  ('give lessons to', '给...上课'),
  ('give off', '发出（气味、热、光等）'),
  ('give out', '分发；用完；公布'),
  ('give performance / a concert', '演出/举办音乐会'),
  ('give rise to', '引起；导致'),
  ('give sb. a hand', '帮助某人'),
  ('give up', '放弃'),
  ('give way (to)', '让路；让步；给...腾出空间'),
  ('go ahead', '前进；去吧；说吧'),
  ('go against', '违反；不利于'),
  ('go bad / wrong', '变坏/出毛病'),
  ('go beyond', '超出；超过'),
  ('go by', '经过；（时间）过去'),
  ('go down', '下降；下沉'),
  ('go fishing / shopping / sightseeing / skating / swimming / boating / hiking / camping / climbing', '去钓鱼/购物/观光/滑冰/游泳/划船/徒步旅行/露营/登山'),
  ('go for', '去取；主张；适用于'),
  ('go in for', '参加；爱好'),
  ('go into', '进入；调查；从事'),
  ('go off', '响起（铃声等）；爆炸；变质'),
  ('go on (with) / go on doing', '继续（做某事）'),
  ('go on to do sth.', '接着做另一件事'),
  ('go out', '外出；（灯/火）熄灭'),
  ('go over', '仔细检查；复习'),
  ('go through', '经历；仔细检查；通过'),
  ('go up', '上升；上涨；建造'),
  ('go without', '没有...也能凑合'),
  ('good luck to', '祝...好运'),
  ('grow up', '长大；成长'),
  ('had better do', '最好做'),
  ('hand down', '传下来；往下传'),
  ('hand in', '交上；提交'),
  ('hand in hand', '手拉手；联合'),
  ('hand out', '分发'),
  ('hang on', '坚持；别挂断（电话）；稍等'),
  ('hang up', '挂断电话；悬挂'),
  ('happen to', '碰巧；发生'),
  ('have a (bad) cold', '患（重）感冒'),
  ('have a gift for', '有...的天赋'),
  ('have a good / great time', '玩得愉快；过得很开心'),
  ('have a headache / stomachache / toothache', '头痛/胃痛/牙痛'),
  ('have a match / meeting', '举行比赛/开会'),
  ('have a rest / swim / walk / talk / trip', '休息一下/游泳/散步/谈谈/旅游'),
  ('have (got) to', '必须；不得不'),
  ('have fun / trouble / difficulty (in) doing', '做某事开心/有困难'),
  ('have nothing to do with', '与...无关'),
  ('have something to do with', '与...有关'),
  ('head for / towards', '朝...方向行进'),
  ('hear about / of', '听说'),
  ('hear from', '收到...的来信/电话'),
  ('help oneself (to)', '自取；随便吃/用'),
  ('help out', '帮助摆脱困境'),
  ('help sb. with sth.', '在某方面帮助某人'),
  ('help sb. (to) do sth.', '帮助某人做某事'),
  ('here and there', '各处；处处'),
  ('hold a meeting / sports meet', '开会/举行运动会'),
  ('hold on', '等一等（电话）；坚持；抓住不放'),
  ("hold one's breath", "屏住呼吸"),
  ('hold out', '伸出；坚持；维持'),
  ('hold up', '举起；支撑；阻滞；抢劫'),
  ('hurry up', '赶快'),
  ('in a hurry', '匆忙地'),
  ('in a minute / moment', '立刻；马上'),
  ('in a sense', '在某种意义上'),
  ('in a word / in short / in brief', '简言之；总之'),
  ('in accordance with', '按照；根据；与...一致'),
  ('in addition (to)', '此外（还有）；另外'),
  ('in advance', '提前'),
  ('in all / total', '总共；总计'),
  ('in any case / event', '无论如何；总之'),
  ('in fact / reality', '事实上；实际上'),
  ('in favor of', '支持；赞成'),
  ('in front of', '在...前面（外部）'),
  ('in the front of', '在...前部（内部）'),
  ('in future / in the future', '今后/将来'),
  ('in general', '一般说来；大体上'),
  ('in half', '成两半'),
  ('in honor of', '为了纪念；向...表示敬意'),
  ('in order', '按顺序；整齐'),
  ('in order that / to', '为了；以便'),
  ('in other words', '换句话说；也就是说'),
  ('in part / parts', '部分地；有些部分'),
  ('in place', '在适当的位置；就位'),
  ('in place of / instead of', '代替；而不是'),
  ('in public', '公开地；当众'),
  ('in return (for)', '作为（对...的）回报/报答'),
  ('in secret / in private', '秘密地/私下'),
  ('in silence', '沉默地；无声地'),
  ('in space', '在太空；在空间'),
  ('in spite of / despite', '尽管；虽然'),
  ('in surprise', '惊奇地；惊讶'),
  ('in that case', '既然那样；假使那样的话'),
  ('in the afternoon / evening / morning', '下午/晚上/上午'),
  ('in the beginning / at first', '起初；开始'),
  ('in the center / middle of', '在...中心/中间'),
  ('in the course of', '在...期间；在...过程中'),
  ('in the day / daytime', '白天；日间'),
  ('in the distance', '在远处'),
  ('in the end / at last', '最后；终于'),
  ('in the face of', '面对；面对着'),
  ('in the field of', '在...领域'),
  ('in the form of', '以...形式'),
  ('in the future', '将来'),
  ('in the habit of', '有...的习惯'),
  ('in the hope / hoping that', '怀着...的希望'),
  ('in the least / not in the least', '丝毫（不）'),
  ('in the name of', '以...的名义'),
  ('in the open air / outdoors', '在户外；在野外'),
  ('in the past', '在过去'),
  ('in the way', '挡道；碍事'),
  ('in the world', '究竟；到底；世界上'),
  ('in time', '及时；迟早；终于'),
  ('in touch (with)', '（与...）保持联系'),
  ('in town', '在城里；在镇上'),
  ('in trouble', '处于困境中'),
  ('in turn', '依次；反过来'),
  ('in use', '在使用中'),
  ('in vain', '徒劳；白费力气'),
  ('instead', '相反；代替'),
  ('insist on doing', '坚持做某事'),
  ('join in / take part in', '参加；加入'),
  ('joke about', '拿...开玩笑'),
  ('keep a diary / record', '写日记/做记录'),
  ('keep / bear ... in mind', '记住；牢记'),
  ('keep an eye on', '留意；照看'),
  ('keep away (from)', '（使）离开/不接近'),
  ('keep back', '保留；阻止；隐瞒'),
  ('keep fit / healthy', '保持健康'),
  ('keep in touch (with)', '（与...）保持联系'),
  ('keep off', '（使）不接近；让开'),
  ('keep on doing (sth.)', '继续（做某事）'),
  ("keep one's balance", "保持平衡"),
  ("keep one's promise / word", "遵守诺言"),
  ("keep (one's) cool", "保持冷静"),
  ('keep out (of)', '（使）留在外面；不让入内'),
  ('keep to', '坚持；遵守；不偏离'),
  ('keep up (with)', '跟上；保持；继续；不落后'),
  ('kick off', '踢开；（比赛）开始'),
  ('knock at / on', '敲（门/窗）'),
  ('knock down', '撞倒；击倒；拆除'),
  ('knock into', '撞到...身上；偶然遇见'),
  ('know about / of', '了解；知道关于...的情况'),
  ('laugh at', '嘲笑'),
  ('lay / place / put emphasis on', '强调；注重；重视'),
  ('lay aside / by', '储存；储蓄；把...搁置一边'),
  ('lay down', '放下；规定；制定'),
  ('lead / live a ... life', '过着...的生活'),
  ('lead to', '导致；通向'),
  ('learn ... by heart', '背诵；熟记'),
  ('learn from', '向...学习；从...获得（教训等）'),
  ('leave ... alone', '不管；不理会；不打扰'),
  ('leave A for B', '离开A地去B地'),
  ('leave behind', '留下；遗忘；超过'),
  ('leave for', '动身去（某处）'),
  ('leave out', '遗漏；省略'),
  ('lend ... a hand', '帮...一把；助一臂之力'),
  ('let alone', '更不用说；听任；不打扰'),
  ('let down', '放下；使失望'),
  ('let go (of)', '放开；松手；释放'),
  ('let in', '让...进来；允许入内'),
  ('let off', '排放（烟雾等）；宽恕；放过'),
  ('let out', '放出；发出；泄漏；出租'),
  ('lie in', '在于'),
  ('line up', '排队；使整齐'),
  ('listen to / hear', '听'),
  ('live by / on', '靠...生活/以...为食'),
  ('live through', '经历过；度过；经受住'),
  ('live up to', '不辜负；做到；符合'),
  ('long for / to do', '渴望/想做'),
  ('look after / care for / take care of', '照顾；照料'),
  ('look ahead', '向前看；展望未来'),
  ('look at / see / watch / notice / observe', '看/看见/观看/注意到/观察'),
  ('look back (at / on / upon)', '回顾；回忆'),
  ('look down (up)on', '看不起；轻视'),
  ('look for / search for / seek / find / find out / discover', '寻找/搜寻/搜寻/找到/找出/发现'),
  ('look forward to (doing)', '盼望；期待（做）'),
  ('look into', '调查；观察；向里看'),
  ('look like', '看起来像'),
  ('look out / be careful', '当心；小心；注意'),
  ('look through', '浏览；仔细查看'),
  ('look up', '向上看；查阅；好转；看望'),
  ('lose contact / touch (with)', '（与...）失去联系'),
  ('lose face', '丢脸'),
  ('lose heart / courage', '丧失信心/勇气'),
  ("lose one's temper", "发脾气"),
  ('lose weight', '减肥'),
  ('lots of / a lot of / plenty of', '许多；大量'),
  ('make a decision / plan', '做决定/计划'),
  ('make a fire', '生火'),
  ('make a living / earn a living', '谋生'),
  ('make a mistake / mistakes', '犯错误/犯错'),
  ('make a noise', '吵闹/制造噪音'),
  ('make a promise / make an appointment', '许诺/约会'),
  ('make advances / progress', '取得进展/进步'),
  ('make friends (with)', '（与...）交朋友'),
  ('make it', '成功；赶上；及时到达'),
  ("make one's mind / make up one's mind (to)", "下定决心（做）"),
  ("make one's way (to)", "前往；（向...方向）前进"),
  ('make out', '辨认出；理解；填写'),
  ('make room / space (for)', '给...腾出地方/空间'),
  ('make sense (of)', '讲得通；有意义；理解'),
  ('make sure (of / that)', '确信；确定；务必；确保'),
  ('make the best / most use (of)', '充分利用'),
  ('make up', '组成；编造；化妆；补足；和解'),
  ('make up for', '补偿；弥补'),
  ('make way (for)', '让路给...；为...腾出空间'),
  ('mark the papers / exam', '批改试卷/考试'),
  ('mean doing / mean to do', '意味着做/打算做'),
  ('meet / satisfy the needs / demands of', '满足...的需求/要求'),
  ('mistake A for B / mistake ... for ...', '把A误认为B/把...误认为...'),
  ('mix up', '混淆；混合；搞糊涂'),
  ('more or less', '或多或少；差不多'),
  ('name ... after', '按...给...命名'),
  ('neither ... nor ...', '既不...也不...'),
  ('no more than / not more than', '仅仅；只是/不超过'),
  ('no wonder (that)', '难怪；不足为奇'),
  ('not any longer / no longer', '不再'),
  ('not any more / no more', '不再'),
  ('not as / so ... as ...', '不如...那样...'),
  ('not only ... but also ...', '不仅...而且...'),
  ('not ... but ...', '不是...而是...'),
  ('not ... until ...', '直到...才...'),
  ('now and then / from time to time / at times', '时而；不时；偶尔；有时'),
  ('now that', '既然；由于'),
  ('object to (doing)', '反对（做）'),
  ('occur to', '被想到；出现在脑海中'),
  ('of course / certainly / surely / naturally / obviously', '当然/无疑/确实/自然/显然'),
  ('off duty', '下班'),
  ('offer to do sth.', '主动提出做某事'),
  ('offer sb. sth.', '提供给某人某物'),
  ('on (a / the) visit (to)', '在访问...期间；在参观...中'),
  ('on (an / the) average (of)', '平均；平均起来'),
  ('on a large / small scale', '大规模地/小规模地'),
  ('on account of', '因为；由于'),
  ('on behalf of', '代表；为了...的利益'),
  ('on board', '在船（车/飞机）上'),
  ('on business', '出差；因公'),
  ('on condition (that)', '如果；在...条件下'),
  ('on duty', '值班；上班'),
  ('on earth', '到底；究竟'),
  ('on foot', '步行'),
  ('on guard', '站岗；值班；警惕'),
  ('on holiday / vacation / trip / tour / journey', '度假/假期/旅游/游览/旅程'),
  ('on land / sea', '在陆地/在海上'),
  ('on line / online', '在线'),
  ("on one's own / alone / independently", "独自地/独自/独立地"),
  ('on purpose / intentionally / deliberately', '故意地/有意地/蓄意地'),
  ('on the air / radio / TV / Internet', '正在广播/通过无线电/电视/互联网'),
  ('on the contrary / other hand', '正相反/另一方面'),
  ('on the edge / point / verge (of)', '在...边缘/在...之际'),
  ('on the increase / decrease / rise / fall / grow', '在增长/减少/上升/下跌/增长'),
  ('on the other hand', '另一方面'),
  ('on the point (of)', '正要...的时候'),
  ('on the radio / telephone / phone / Internet', '通过无线电/电话/电话/互联网'),
  ('on the road / way (to / home)', '在路上/途中（去/回家）'),
  ('on the side', '作为兼职；作为副业'),
  ('on the spot / scene / place / site', '在现场/现场/当场/现场'),
  ('once (and) for all / once more / again / once in a while', '一劳永逸/再一次/再次/从前/偶尔'),
  ('once / twice / three times / many / sometimes / often / usually / always / never / seldom / rarely', '一次/两次/三次/多次/有时/经常/通常/总是/从不/很少/很少'),
  ('open / close / lock / unlock / shut', '打开/关闭/锁住/开锁/关上'),
  ('operate on / perform an operation (on)', '给...做手术/给...动手术'),
  ('order / book / reserve / request / ask', '订购/预订/预订/请求/请求'),
  ('other than / except / but / apart from / besides', '除了/除了/但是/除...之外/此外'),
  ('out of breath / order / date / work / danger / trouble', '上气不接气/混乱/过期/故障/危险/麻烦'),
  ('outdoors / outdoor / indoor / indoors / inside / outside', '户外/户外的/室内/室内的/内部的/外部的'),
  ('over and over (again) / again and again', '一再/反复/再三/反复'),
  ('owe ... to ...', '把...归功于...'),
  ('pack up', '打包；收拾'),
  ('pardon / forgive / excuse / spare', '原谅/宽恕/原谅/饶恕'),
  ('pass away / die / depart / expire', '去世/死/离去/去世'),
  ('pass by / pass on / pass through / pass out / pass up', '经过/传递/通过/昏厥/错过'),
  ('pay attention (to) / notice', '注意/注意到'),
  ('pay back / repay / refund / compensate', '偿还/还款/退款/补偿'),
  ('pay cash / in cash / by credit card / installments', '付现金/用现金/信用卡/分期付款'),
  ('pay for / pay off / pay out / pay up', '支付/付清/付出/付清'),
  ('pay a visit (to) / visit / tour', '访问/参观/游览'),
  ('persist in / stick to / insist on', '坚持/坚持/坚持'),
  ('pick out / pick up / choose / select / prefer / favor', '挑出/捡起/选择/挑选/偏爱/青睐'),
  ('place / put / set emphasis / importance / stress', '放置/放置/设定重视/重要性/强调'),
  ('play a part (in) / play a role (in) / participate / join in', '扮演角色/起作用/参与/加入'),
  ('point at / point to / point out / indicate / show', '指向/指向/指出/表明/显示'),
  ('prefer ... to ... / rather (A) than (B)', '宁愿...而不愿/宁愿(A)也不愿(B)'),
  ('prepare for / get ready (for)', '为...做准备/做好准备'),
  ('prevent ... from (doing)', '阻止...（做）'),
  ('pride oneself on / be proud of', '自夸/为...感到骄傲'),
  ('print out / write out / set out / figure out', '打印输出/写出/出发/算出'),
  ('progress / advance / move forward / develop', '进步/前进/向前移动/发展'),
  ('promise / vow / guarantee', '承诺/发誓/保证'),
  ('protect / defend / guard ... from', '保护/保卫/守卫...'),
  ('provide / supply / equip ... with', '向...供应/供应/配备'),
  ('pull / push / drag / haul', '拉推拖曳拉'),
  ('put away / put back / put down / put off / put on / put out / put up / put up with', '放好/放回/记下/推迟/穿上/熄灭/搭建/忍受'),
  ('quite a few / quite a little / many / much / lots / plenty', '相当多/相当少/许多/很多/许多/大量'),
  ('rather than / instead of / unlike', '而不是/而不是/不像'),
  ('refer / admire / respect', '参考/钦佩/尊敬'),
  ('remind sb. / remind sb. that ...', '使某人想起/提醒某人'),
  ('replace A (with B)', '用B替换A'),
  ('respond / react / reply', '回应/反应/答复'),
  ('result / lead to / cause / bring about', '导致/导致/引起/引起'),
  ('right away / immediately / instantly / promptly', '立刻/立即/立刻/迅速'),
  ('ring / call / hang / pick / put', '打电话/呼叫/挂断/拿起/接通'),
  ('rob / steal / deprive', '抢夺/偷窃/剥夺'),
  ('run / chase / pursue / follow', '追赶/追逐/追求/跟随'),
  ("save one's life / save face / save up", "救某人的命/保全面子/储蓄"),
  ('see off / see to', '送行/负责'),
  ('sell / trade / exchange / barter', '卖完/交易/交换/物物交换'),
  ('send / call / summon', '发送/呼叫/召唤'),
  ('set sail / depart / head / voyage / travel / tour / trip', '出发/出发/朝...进发/航程/旅程/旅行/旅行'),
  ('set about / set out / set off / set up / start / begin / organize / arrange', '着手/出发/出发/建立/开始/开始/组织/安排'),
  ('set free / liberate / release / unchain', '释放/解放/释放/解开链条'),
  ('set out / set off / get going / get underway', '出发/出发/开始动手/开始'),
  ('set up / build / establish / create / organize / assemble / include / involve / embody', '建立/建造/建立/成立/创建/组织/汇编/包含/包含/体现'),
  ('settle / calm / quiet / slow / cool / dwindle / shrink / decline / drop', '安定/平静/安静/减速|冷却/减弱/缩小|减少/衰退/下跌'),
  ('show / display / exhibit / demonstrate / reveal / introduce / offer / provide', '带领展示/展览/呈现/演示/揭示/介绍/提供/供应'),
  ('show interest / be interested / concern / care / love / enjoy / attention', '表现出兴趣/感兴趣/关切关心爱喜好享受注意力'),
  ('side / support / help / favor / choose / elect / opt', '站边支持帮助青睐选择选举'),
  ('similar / alike / same / equal / consistent / steady / stable / firm / lasting / permanent / eternal', '相似相同同样相等一致恒定稳定稳固持久永久永恒'),
  ('sing high praise for / speak highly / / cherish / treasure / appreciate / enjoy', '高度赞扬高度评价珍视珍视欣赏享受'),
  ('slow / reduce speed / brake / halt / stop / cease / quit', '减速减速刹车停止暂停终止退出'),
  ('so as to / in order to / designed / aimed', '以便为了意在旨在'),
  ('so far / yet / still / already / recently / nowadays / today', '到目前为止尚仍然已经最近当今今天'),
  ('something / sort / kind / group / collection / bunch / batch / lot / heap / pile', '有点像有点儿种类组集合束批次一批负载堆堆积'),
  ('sooner or later / someday / eventually / finally / ultimately / in the end / time will tell', '迟早某日终有一天最终最后最终最终时间会证明'),
  ('speak / talk / discuss / debate / explain / describe / say / state / assert', '大胆说出谈论讨论辩论解释描述说陈述断言'),
  ('specialize / major / focus / depend / rely / base / assume', '专门研究主修专注依靠基于假设'),
  ('speed / accelerate / hasten / rush / worsen', '加速加速加速匆忙加重'),
  ('spend / cost / consume / waste / discard / give up', '花费成本消耗浪费丢弃放弃'),
  ('stand / bear / endure / suffer / face / tackle / manage / cope / deal', '站立承受忍耐遭受面临对付管理应付应对'),
  ('stand against / oppose / resist / challenge / dispute / doubt / denial / rejection / absurd', '反抗反对抵抗违抗挑战争议疑问否认否定不可能荒谬'),
  ('stand at / stand by / stand for / represent / signify / express / declare / affirm', '立正支持代表象征意味表达宣布断言肯定'),
  ('stand by / support / aid / back / advocate / defend / protect / empower / authorize', '支持支持援助支持倡导保卫保护保障授权授权'),
  ('stand for / represent / mean / imply / suggest / conclude / infer', '代表象征意味着暗示暗示结论推断'),
  ('stand out / visible / noticed / detected / distinguished / selected / chosen', '突出可见被发现被识别区分被选中'),
  ('stick / persist / insist / continue / keep on', '坚持坚持坚持继续坚持'),
  ('stop / give up / cease / break off', '停下手头放弃终止中断'),
  ('struggle / fight / compete / contend / wrestle', '斗争战斗竞争争夺搏斗'),
  ('succeed / manage / achieve / accomplish / win / triumph', '成功设法做到完成获胜胜利'),
  ('such as / including / especially / mainly / primarily', '例如包含尤其主要首先'),
  ('suit / fit / match / adapt / adjust / accommodate', '适合适合相配适应调整使自己适应'),
  ('supply / equip / furnish / provide / arm / burden', '供应配备装备提供装备使负担'),
  ('surprise / amaze / astonish / shock / stun', '使惊讶使吃惊使震惊震晕'),
  ('switch / turn / start / stop / open / close / operate / run / work', '开关转动开始停止打开关闭操作运行工作'),
  ('take it easy / take action / rest / break / holiday', '想当然采取行动休息休息假期'),
  ('take active part / participate / join / engage / volunteer / apply / try', '积极参加参与参加参与自愿申请选拔'),
  ('take pride / boast / show off / flaunt', '以自豪夸耀炫耀招摇'),
  ('take interest / care / worry / attend / pay attention', '感兴趣关心担心留意注意'),
  ('take away / remove / clear / delete / eliminate / cancel / withdraw / undo', '拿走移除清除删除消除废除撤回撤销'),
  ('take back / recall / reminisce / reflect / review', '收回回忆追忆反思回顾'),
  ('take care / look after / tend / nurse / guard / protect / defend', '小心照顾照料护理守卫保护保卫'),
  ('take charge / be responsible / control / manage / supervise / lead / guide', '接管负责控制管理监督领导引导'),
  ('take delight / pleasure / joy / satisfaction / happiness / excitement / bliss', '得到乐趣快乐高兴满足快乐兴奋极乐'),
  ('take down / write / note / record / register / document / list / sort', '取下写笔记记录登记存档记录列出分类'),
  ('take effect / become effective / valid / operational / functional / active', '生效有效可操作运行功能活跃'),
  ('take exercise / workout / train / keep fit / stay healthy / build strength', '锻炼锻炼训练保持健康保持健康增强体力'),
  ('take advantage / make best use / capitalize / exploit / utilize / leverage / apply', '充分利用充分利用利用利用利用利用应用'),
  ('take / regard / consider / view / accept / acknowledge / recognize / count / rate', '认为视为认为看待视为接受承认可为算作评定'),
  ('take it easy / relax / unwind / chill / rest / break / holiday', '放松放松放松冷静休息休息假期'),
  ('take account / consideration / notice / consider / weigh / include / remember', '考虑到考虑注意到考虑权衡纳入铭记'),
  ('take opportunity / seize / grasp / make best use / take advantage', '抓住机会抓住把握充分利用充分利用'),
  ('take off / depart / leave / begin / launch / fly / soar / rise', '起飞出发离开开始启动飞翱翔升高'),
  ('take on / assume / accept / shoulder / handle / tackle / address / adopt / acquire', '承担承担接受承受携带对付应对应对采纳获取'),
  ("take one's place / settle / feel relax / rest", "就座就位安定下来感觉自在放松休息"),
  ('take temperature / measure / examine / diagnose / treat / cure', '量体温测量检查诊断治疗治愈'),
  ('take time / patient / cautious / careful / prudent / watchful', '不着急有耐心审慎小心谨慎警惕'),
  ('take out / extract / remove / delete / omit / eradicate / cut / edit', '取出提取移除删除省略根除切除编辑'),
  ('take over / assume control / command / seize / dominate / rule / govern', '接管接管控制指挥夺取支配统治治理'),
  ('take part / participate / attend / appear / arrive / come / reach / succeed', '参加参与出席在场出现到达来到到达成功'),
  ('take place / happen / occur / arise / emerge / unfold / ensue', '发生发生发生产生涌现展开随之发生'),
  ('take sides / side / support / favor / lean / biased / partial / prejudiced', '站在一边支持支持偏向倾向于偏袒偏见'),
  ('tell apart / distinguish / differentiate / separate / identify / recognize / discern', '区分辨别区别分离识别认出辨别感知'),
  ('thank / grateful / thankful / appreciate / acknowledge / credit', '因感谢感激欣赏承认归功于'),
  ('that is / namely / in other words / particularly / especially / importantly / above all', '即也就是换句话说特别尤其最重要的是'),
  ('the day after tomorrow / yesterday / today / tomorrow / tonight / next / last week month year', '后天昨天今天明天今晚下周上周月年'),
  ('the moment / whenever / every time / each time / next last first time', '一每当每次每次下次上次首次'),
  ('think / reflect / consider / imagine / conceive / visualize', '思考反思考虑想象构想预想形象化'),
  ('think highly / opinion / regard / view / rate / rank / grade', '评价高看法视为看待评级排名分级'),
  ('thousands / hundreds / dozens / quantity / amount / lots / many / few / enough / several', '数千数百几把数量数量许多足够几个'),
  ('throw / cast away / aside / back / down / off / on / out / over / together / up upon', '抛四处投掷抛开扔回扔下脱掉穿上扔出递给一起抛起依赖'),
  ('to begin with / firstly / initially / originally / outset / start beginning', '首先最初最初起初开始时起初开始时'),
  ('to tell truth / honestly / frankly / candidly / plainly / bluntly / straight', '说实话诚实坦率坦率直截了当坦率直说'),
  ('too ... to / so ... that / enough ... to / merely / simply / just', '太不能如此如此足够仅仅仅仅只是'),
  ('top / beat / defeat / conquer / overcome / excel / shine / lead', '顶打败击败征服杰出闪耀领导'),
  ('total / add / sum / estimate / assess / judge / rate / rank / grade', '总计加总求和估算评估判断评级排名分级'),
  ('track / trace / follow / chase / hunt / find / discover / detect / locate / identify / pinpoint', '追踪尾随跟踪追逐搜寻找到发现检测定位确认精确找到'),
  ('trade / exchange / buy / sell / purchase / market / discount / bargain negotiate transaction', '交易交换购买销售购买营销折扣讨价谈判交易'),
  ('translate / interpret / decode / clarify / convert / transform / adapt / modify / alter', '翻译译成解释解码澄清转换转化适应修改更改'),
  ('travel / go / walk / jog / sprint / dash / race / fly / drive / ride / climb / swim / jump leap', '旅行去行走慢跑冲刺猛冲赛跑飞驾车骑行攀爬游泳跳飞跃'),
  ('treat / regard / consider / view / see / think / accept / acknowledge / count / rate', '对待视为认为看待认为接受承认可为算作评定'),
  ('try / attempt / endeavor / succeed / fail', '尝试尝试努力成功失败'),
  ('turn round / away / back / down / in / into / off / on / out / over / to / up', '转身走开返回拒绝上交变成关掉翻过来转向出现'),
  ('up / upside down / outdoors / outdoor / indoor / indoors / inside / exterior / outward', '上下颠倒户外户外的室内室内的内部的外部的向外'),
  ('used to / be used to / get used / become accustomed / grow accustomed', '过去常做习惯于习惯于变得习惯逐渐习惯'),
  ('wait / await / expect / hope / wish / want / desire / long / crave thirst', '等待等待期待盼望愿望想要渴望渴望渴求'),
  ('wake / awake / waken / arouse / stir / rise / emerge / appear / arrive / reach / succeed', '醒来唤醒唤醒唤起升起出现出现到达赶到成功'),
  ('walk out / go / date / court / propose / marry / divorce / split / break', '出走约会约会追求求婚订婚结婚离婚分离分手分手'),
  ('warn / caution / alert / advise / admonish', '警告告诫使警觉建议警告警告'),
  ('wash / clean / wipe / sweep / dust / polish / dirty / filthy / unhealthy', '冲走清洁擦拭扫除尘擦亮肮脏不健康'),
  ('watch out / beware / careful / cautious / wary / alert / guard / lookout / keep eye', '当心提防小心谨慎警惕警觉防范警戒搜寻留意'),
  ('wear / erode / deteriorate / decay / decline / degenerate / worsen / tear / crumble / disintegrate / apart', '磨损腐蚀恶化腐朽衰退退化恶化撕裂崩溃瓦解崩溃'),
  ('what / how / suppose / assuming / given / provided / condition', '怎么样如何假设假定已知假如条件'),
  ('wind / wrap / finish / complete / conclude / pack / go home', '结束放松结束完成结束打包回家'),
  ('wipe / clean / sweep / rub / erase / destroy / demolish / ruin / wreck / remove / delete / cancel', '消灭清除清扫擦掉抹去摧毁拆毁毁灭破坏消除移除删除取消'),
  ('with delight / pleasure / joy / satisfaction / enthusiasm / excitement / happiness / elation / bliss', '非常高兴愉快高兴满足热情兴奋快乐洋洋得意极乐'),
  ('with regard / reference / concerning / touching / relating / covering / spanning', '关于关于关于涉及有关关联涵盖跨越'),
  ('with exception / except / besides / excluding / leaving / barring / save / aside', '除除外此外不包括遗漏禁止除外'),
  ('with help / thanks / owing / due / because / virtue / through / via', '在帮助下幸亏由于因为凭借通过通过'),
  ('with intention / aim / goal / purpose / designed / meant / intended / aimed targeted', '怀着意图目标目的目的意在旨在针对针对'),
  ('with result / resulting / causing / giving / creating / occasioning', '结果是结果导致引起创造造成'),
  ('within / ability / capacity / range / means / limits / bounds / understanding / comprehension', '在能力范围内能力范围手段限制界限知识理解力'),
  ('without / delay / hesitation / doubt / cause / reason / excuse / warning / preparation / success / result', '毫不迟疑毫无疑问无原因无理由无借口无警告未做准备失败'),
  ('wonder / marvel / amazed / astonished / surprised / shocked / stunned / taken aback', '惊叹惊叹对惊讶震惊惊吓震晕吃惊'),
  ('word / verbatim / literally / exactly / accurately / correct / true / reliable / trustworthy / credible', '逐字一字不改字面意思精确准确正确真实可靠可信'),
  ('work / function / perform / behave / act / create / produce / generate', '致力于运行操作表现行为行动创造生产生成'),
  ('worry / anxious / concerned / troubled / disturbed / fret / agonize / sleep', '担心焦虑烦恼不安困扰苦恼痛苦失眠'),
  ('write / take notes / record / file / draft / compose / author / type / print / publish / broadcast', '写下记笔记记录存档起草创作作者打字打印发布广播'),
  ('year / day / month / week / time / repeatedly', '年复一年日复一月周复一周反复反复'),
  ('yes / maybe / perhaps / possibly / probably / certainly / clearly', '是否也许或许可能大概无疑清楚地'),
("definitely", "肯定地")]
# ==================== 语法知识数据 ====================
BUILTIN_DIALOGUES = [
    {
        'title': 'Greeting 初次见面',
        'en': "Tom: Hi, I'm Li Ming. Nice to meet you.\nLucy: Nice to meet you too, Li Ming. I'm Mary.\nTom: Where are you from?\nLucy: I'm from Canada.",
        'zh': 'Tom: 你好，我是李明。很高兴认识你。\nLucy: 也很高兴认识你，李明。我是玛丽。\nTom: 你来自哪里？\nLucy: 我来自加拿大。',
        'dialogue': [
            ["Hi, I'm Li Ming. Nice to meet you.", '你好，我是李明。很高兴认识你。'],
            ["Nice to meet you too, Li Ming. I'm Mary.", '也很高兴认识你，李明。我是玛丽。'],
            ['Where are you from?', '你来自哪里？'],
            ["I'm from Canada.", '我来自加拿大。'],
        ],
    },
    {
        'title': 'Asking for help 请求帮助',
        'en': "Tom: Excuse me, could you help me with this box?\nLucy: Sure, no problem. Where should I put it?\nTom: Just on the desk, please. Thank you so much!\nLucy: You're welcome.",
        'zh': 'Tom: 打扰一下，你能帮我搬这个箱子吗？\nLucy: 当然，没问题。放哪里？\nTom: 就放在桌子上。非常感谢！\nLucy: 不客气。',
        'dialogue': [
            ['Excuse me, could you help me with this box?', '打扰一下，你能帮我搬这个箱子吗？'],
            ['Sure, no problem. Where should I put it?', '当然，没问题。放哪里？'],
            ['Just on the desk, please. Thank you so much!', '就放在桌子上。非常感谢！'],
            ["You're welcome.", '不客气。'],
        ],
    },
    {
        'title': 'Shopping 购物',
        'en': "Tom: How much is this T-shirt?\nLucy: It's 25 dollars.\nTom: That's a bit expensive. Any discount?\nLucy: Sorry, it's on sale already. But you can have this one for 20 dollars.",
        'zh': 'Tom: 这件T恤多少钱？\nLucy: 25美元。\nTom: 有点贵。有折扣吗？\nLucy: 抱歉，已经在打折了。但你可以20美元买这件。',
        'dialogue': [
            ['How much is this T-shirt?', '这件T恤多少钱？'],
            ["It's 25 dollars.", '25美元。'],
            ["That's a bit expensive. Any discount?", '有点贵。有折扣吗？'],
            ["Sorry, it's on sale already. But you can have this one for 20 dollars.", '抱歉，已经在打折了。但你可以20美元买这件。'],
        ],
    },
    {
        'title': 'Ordering food 点餐',
        'en': "Tom: May I take your order?\nLucy: Yes, I'd like a cheeseburger and a medium Coke.\nTom: Anything else? Fries or salad?\nLucy: No, thanks. That's all.",
        'zh': 'Tom: 可以点餐了吗？\nLucy: 是的，我要一个芝士汉堡和中杯可乐。\nTom: 还要别的吗？薯条或沙拉？\nLucy: 不了，谢谢。就这些。',
        'dialogue': [
            ['May I take your order?', '可以点餐了吗？'],
            ["Yes, I'd like a cheeseburger and a medium Coke.", '是的，我要一个芝士汉堡和中杯可乐。'],
            ['Anything else? Fries or salad?', '还要别的吗？薯条或沙拉？'],
            ["No, thanks. That's all.", '不了，谢谢。就这些。'],
        ],
    },
    {
        'title': 'Asking for directions 问路',
        'en': "Tom: Excuse me, where is the nearest post office?\nLucy: Go straight for two blocks, then turn left. You'll see it on your right.\nTom: Is it far?\nLucy: No, about a 10-minute walk.",
        'zh': 'Tom: 打扰一下，最近的邮局在哪里？\nLucy: 直走两个街区，然后左转。它就在你右边。\nTom: 远吗？\nLucy: 不远，步行大约10分钟。',
        'dialogue': [
            ['Excuse me, where is the nearest post office?', '打扰一下，最近的邮局在哪里？'],
            ["Go straight for two blocks, then turn left. You'll see it on your right.", '直走两个街区，然后左转。它就在你右边。'],
            ['Is it far?', '远吗？'],
            ['No, about a 10-minute walk.', '不远，步行大约10分钟。'],
        ],
    },
    {
        'title': 'Weather 谈论天气',
        'en': "Tom: Beautiful day, isn't it?\nLucy: Yes, it's sunny and warm. Great for a picnic.\nTom: But the forecast says it might rain in the afternoon.\nLucy: Oh, maybe we should bring an umbrella.",
        'zh': 'Tom: 天气真好，不是吗？\nLucy: 是的，晴朗温暖。很适合野餐。\nTom: 但是天气预报说下午可能会下雨。\nLucy: 哦，也许我们应该带把伞。',
        'dialogue': [
            ["Beautiful day, isn't it?", '天气真好，不是吗？'],
            ["Yes, it's sunny and warm. Great for a picnic.", '是的，晴朗温暖。很适合野餐。'],
            ['But the forecast says it might rain in the afternoon.', '但是天气预报说下午可能会下雨。'],
            ['Oh, maybe we should bring an umbrella.', '哦，也许我们应该带把伞。'],
        ],
    },
    {
        'title': 'Making a phone call 打电话',
        'en': "Tom: Hello, may I speak to Tom?\nLucy: Speaking. Who's that?\nTom: This is Jerry. Are we still meeting at 3 PM?\nLucy: Sure. See you then.",
        'zh': 'Tom: 你好，请找汤姆接电话。\nLucy: 我就是。你是哪位？\nTom: 我是杰瑞。我们下午3点还见面吗？\nLucy: 当然。到时候见。',
        'dialogue': [
            ['Hello, may I speak to Tom?', '你好，请找汤姆接电话。'],
            ["Speaking. Who's that?", '我就是。你是哪位？'],
            ['This is Jerry. Are we still meeting at 3 PM?', '我是杰瑞。我们下午3点还见面吗？'],
            ['Sure. See you then.', '当然。到时候见。'],
        ],
    },
    {
        'title': 'Invitation 邀请',
        'en': "Tom: Are you free this Saturday? We're having a party at my place.\nLucy: That sounds great! What time?\nTom: Around 7 PM. You can bring a friend.\nLucy: OK, I'll be there. Thanks for inviting me.",
        'zh': 'Tom: 这周六你有空吗？我们在我家举办派对。\nLucy: 听起来很棒！几点？\nTom: 晚上7点左右。你可以带个朋友。\nLucy: 好的，我会去的。谢谢邀请。',
        'dialogue': [
            ["Are you free this Saturday? We're having a party at my place.", '这周六你有空吗？我们在我家举办派对。'],
            ['That sounds great! What time?', '听起来很棒！几点？'],
            ['Around 7 PM. You can bring a friend.', '晚上7点左右。你可以带个朋友。'],
            ["OK, I'll be there. Thanks for inviting me.", '好的，我会去的。谢谢邀请。'],
        ],
    },
    {
        'title': 'Talking about hobbies 谈论爱好',
        'en': 'Tom: What do you like to do in your free time?\nLucy: I enjoy reading and playing basketball.\nTom: Really? I also love basketball. Maybe we can play together sometime.\nLucy: That would be great!',
        'zh': 'Tom: 你空闲时间喜欢做什么？\nLucy: 我喜欢阅读和打篮球。\nTom: 真的吗？我也爱篮球。也许我们可以找时间一起打。\nLucy: 那太好了！',
        'dialogue': [
            ['What do you like to do in your free time?', '你空闲时间喜欢做什么？'],
            ['I enjoy reading and playing basketball.', '我喜欢阅读和打篮球。'],
            ['Really? I also love basketball. Maybe we can play together sometime.', '真的吗？我也爱篮球。也许我们可以找时间一起打。'],
            ['That would be great!', '那太好了！'],
        ],
    },
    {
        'title': 'At the library 在图书馆',
        'en': 'Tom: Excuse me, can I borrow this book?\nLucy: Sure. Do you have a library card?\nTom: Yes, here it is.\nLucy: OK, you can keep it for two weeks. Please return it on time.',
        'zh': 'Tom: 打扰一下，我可以借这本书吗？\nLucy: 当然。你有借书证吗？\nTom: 有，给你。\nLucy: 好的，你可以借两周。请按时归还。',
        'dialogue': [
            ['Excuse me, can I borrow this book?', '打扰一下，我可以借这本书吗？'],
            ['Sure. Do you have a library card?', '当然。你有借书证吗？'],
            ['Yes, here it is.', '有，给你。'],
            ['OK, you can keep it for two weeks. Please return it on time.', '好的，你可以借两周。请按时归还。'],
        ],
    },
    {
        'title': 'Travel plan 旅行计划',
        'en': "Tom: Where are you going for summer vacation?\nLucy: I'm planning to visit Beijing with my family.\nTom: Wonderful! What places will you see?\nLucy: The Great Wall, the Forbidden City, and the Summer Palace.",
        'zh': 'Tom: 你暑假要去哪里？\nLucy: 我计划和家人去北京。\nTom: 太棒了！你们会去哪些地方？\nLucy: 长城、故宫和颐和园。',
        'dialogue': [
            ['Where are you going for summer vacation?', '你暑假要去哪里？'],
            ["I'm planning to visit Beijing with my family.", '我计划和家人去北京。'],
            ['Wonderful! What places will you see?', '太棒了！你们会去哪些地方？'],
            ['The Great Wall, the Forbidden City, and the Summer Palace.', '长城、故宫和颐和园。'],
        ],
    },
    {
        'title': 'Apologizing 道歉',
        'en': "Tom: I'm really sorry I broke your cup.\nLucy: Don't worry about it. It was old anyway.\nTom: Still, I feel bad. Let me buy you a new one.\nLucy: No, it's fine. Thanks for apologizing.",
        'zh': 'Tom: 真的很抱歉，我打碎了你的杯子。\nLucy: 别担心。反正它已经很旧了。\nTom: 但我还是过意不去。让我给你买个新的吧。\nLucy: 不用，没关系。谢谢你的道歉。',
        'dialogue': [
            ["I'm really sorry I broke your cup.", '真的很抱歉，我打碎了你的杯子。'],
            ["Don't worry about it. It was old anyway.", '别担心。反正它已经很旧了。'],
            ['Still, I feel bad. Let me buy you a new one.', '但我还是过意不去。让我给你买个新的吧。'],
            ["No, it's fine. Thanks for apologizing.", '不用，没关系。谢谢你的道歉。'],
        ],
    },
    {
        'title': 'Talking about school 谈论学校',
        'en': "Tom: How many classes do you have today?\nLucy: Five. Math, English, science, history, and PE.\nTom: Which subject do you like best?\nLucy: I like science because it's interesting.",
        'zh': 'Tom: 你今天有几节课？\nLucy: 五节。数学、英语、科学、历史和体育。\nTom: 你最喜欢哪门课？\nLucy: 我喜欢科学，因为它有趣。',
        'dialogue': [
            ['How many classes do you have today?', '你今天有几节课？'],
            ['Five. Math, English, science, history, and PE.', '五节。数学、英语、科学、历史和体育。'],
            ['Which subject do you like best?', '你最喜欢哪门课？'],
            ["I like science because it's interesting.", '我喜欢科学，因为它有趣。'],
        ],
    },
    {
        'title': 'At the airport 在机场',
        'en': "Tom: Your flight is boarding now. Have a safe trip!\nLucy: Thank you. I'll call you when I land.\nTom: OK. Take care.\nLucy: You too. Bye!",
        'zh': 'Tom: 你的航班开始登机了。一路平安！\nLucy: 谢谢。我降落时给你打电话。\nTom: 好的。保重。\nLucy: 你也是。再见！',
        'dialogue': [
            ['Your flight is boarding now. Have a safe trip!', '你的航班开始登机了。一路平安！'],
            ["Thank you. I'll call you when I land.", '谢谢。我降落时给你打电话。'],
            ['OK. Take care.', '好的。保重。'],
            ['You too. Bye!', '你也是。再见！'],
        ],
    },
    {
        'title': 'Complimenting 赞美',
        'en': "Tom: I love your new haircut. It looks great on you.\nLucy: Oh, thank you! I was a bit nervous about it.\nTom: No need. You look fantastic.\nLucy: You're so kind.",
        'zh': 'Tom: 我喜欢你的新发型。很适合你。\nLucy: 哦，谢谢！我还有点紧张呢。\nTom: 不用。你看起来棒极了。\nLucy: 你真好。',
        'dialogue': [
            ['I love your new haircut. It looks great on you.', '我喜欢你的新发型。很适合你。'],
            ['Oh, thank you! I was a bit nervous about it.', '哦，谢谢！我还有点紧张呢。'],
            ['No need. You look fantastic.', '不用。你看起来棒极了。'],
            ["You're so kind.", '你真好。'],
        ],
    },
    {
        'title': 'At a restaurant 餐厅里',
        'en': "Tom: Are you ready to order?\nLucy: Yes. I'll have the steak, medium rare, with mashed potatoes.\nTom: And for you, sir?\nC: The same, but with a salad instead of potatoes.",
        'zh': 'Tom: 可以点菜了吗？\nLucy: 是的。我要牛排，五分熟，配土豆泥。\nTom: 先生，您呢？\nC: 一样，但是把土豆换成沙拉。',
        'dialogue': [
            ['Are you ready to order?', '可以点菜了吗？'],
            ["Yes. I'll have the steak, medium rare, with mashed potatoes.", '是的。我要牛排，五分熟，配土豆泥。'],
            ['And for you, sir?', '先生，您呢？'],
            ['The same, but with a salad instead of potatoes.', '一样，但是把土豆换成沙拉。'],
        ],
    },
    {
        'title': 'Giving advice 提建议',
        'en': "Tom: I'm always tired after school.\nLucy: Maybe you should go to bed earlier.\nTom: But I have so much homework.\nLucy: Try to manage your time better. Take short breaks.",
        'zh': 'Tom: 放学后我总是很累。\nLucy: 也许你应该早点睡觉。\nTom: 但是我作业很多。\nLucy: 试着更好地管理时间。短暂休息一下。',
        'dialogue': [
            ["I'm always tired after school.", '放学后我总是很累。'],
            ['Maybe you should go to bed earlier.', '也许你应该早点睡觉。'],
            ['But I have so much homework.', '但是我作业很多。'],
            ['Try to manage your time better. Take short breaks.', '试着更好地管理时间。短暂休息一下。'],
        ],
    },
    {
        'title': 'Talking about future 谈论未来',
        'en': "Tom: What do you want to be when you grow up?\nLucy: I want to be a doctor and help sick people.\nTom: That's a noble goal. I want to be a software engineer.\nLucy: Great! Let's work hard for our dreams.",
        'zh': 'Tom: 你长大后想做什么？\nLucy: 我想当医生，帮助病人。\nTom: 那是个崇高的目标。我想当软件工程师。\nLucy: 太好了！让我们为梦想努力。',
        'dialogue': [
            ['What do you want to be when you grow up?', '你长大后想做什么？'],
            ['I want to be a doctor and help sick people.', '我想当医生，帮助病人。'],
            ["That's a noble goal. I want to be a software engineer.", '那是个崇高的目标。我想当软件工程师。'],
            ["Great! Let's work hard for our dreams.", '太好了！让我们为梦想努力。'],
        ],
    },
    {
        'title': 'Emergency 紧急情况',
        'en': "Tom: Help! I need a doctor quickly.\nLucy: What happened?\nTom: My friend fell and hurt his leg badly.\nLucy: Don't move him. I'll call 911 right now.",
        'zh': 'Tom: 救命！我需要医生，快点。\nLucy: 发生了什么事？\nTom: 我朋友摔倒了，腿伤得很重。\nLucy: 别动他。我马上打急救电话。',
        'dialogue': [
            ['Help! I need a doctor quickly.', '救命！我需要医生，快点。'],
            ['What happened?', '发生了什么事？'],
            ['My friend fell and hurt his leg badly.', '我朋友摔倒了，腿伤得很重。'],
            ["Don't move him. I'll call 911 right now.", '别动他。我马上打急救电话。'],
        ],
    },
    {
        'title': 'Farewell 告别',
        'en': "Tom: I'm moving to another city next week.\nLucy: Oh, I'm sorry to hear that. We'll miss you.\nTom: I'll miss you too. Let's keep in touch.\nLucy: Definitely. Good luck with everything.",
        'zh': 'Tom: 我下周要搬到另一个城市了。\nLucy: 哦，听到这消息很难过。我们会想你的。\nTom: 我也会想你们。我们保持联系。\nLucy: 一定。祝你一切顺利。',
        'dialogue': [
            ["I'm moving to another city next week.", '我下周要搬到另一个城市了。'],
            ["Oh, I'm sorry to hear that. We'll miss you.", '哦，听到这消息很难过。我们会想你的。'],
            ["I'll miss you too. Let's keep in touch.", '我也会想你们。我们保持联系。'],
            ['Definitely. Good luck with everything.', '一定。祝你一切顺利。'],
        ],
    },
    {
        'title': 'Daily Routine 日常生活',
        'en': "Tom: What time do you usually get up?\nLucy: I usually get up at 6:30 AM.\nTom: That's early! Do you have breakfast at home?\nLucy: Yes, my mom makes breakfast for me every day.",
        'zh': 'Tom: 你通常几点起床？\nLucy: 我通常早上6:30起床。\nTom: 那么早！你在家吃早餐吗？\nLucy: 是的，我妈妈每天给我做早餐。',
        'dialogue': [
            ['What time do you usually get up?', '你通常几点起床？'],
            ['I usually get up at 6:30 AM.', '我通常早上6:30起床。'],
            ["That's early! Do you have breakfast at home?", '那么早！你在家吃早餐吗？'],
            ['Yes, my mom makes breakfast for me every day.', '是的，我妈妈每天给我做早餐。'],
        ],
    },
    {
        'title': 'Weekend Plans 周末计划',
        'en': "Tom: Do you have any plans for this weekend?\nLucy: I'm going to the park with my family. How about you?\nTom: I think I'll stay home and read some books.\nLucy: That sounds relaxing!",
        'zh': 'Tom: 这个周末你有什么计划吗？\nLucy: 我要和家人去公园。你呢？\nTom: 我想我会待在家里看书。\nLucy: 听起来很放松！',
        'dialogue': [
            ['Do you have any plans for this weekend?', '这个周末你有什么计划吗？'],
            ["I'm going to the park with my family. How about you?", '我要和家人去公园。你呢？'],
            ["I think I'll stay home and read some books.", '我想我会待在家里看书。'],
            ['That sounds relaxing!', '听起来很放松！'],
        ],
    },
    {
        'title': 'Family 家庭',
        'en': 'Tom: How many people are there in your family?\nLucy: There are four—my parents, my sister and me.\nTom: Do you get along well with your sister?\nLucy: Yes, we often help each other with homework.',
        'zh': 'Tom: 你家有几口人？\nLucy: 四口人——我父母、我姐姐和我。\nTom: 你和姐姐相处得好吗？\nLucy: 是的，我们经常互相帮助做作业。',
        'dialogue': [
            ['How many people are there in your family?', '你家有几口人？'],
            ['There are four—my parents, my sister and me.', '四口人——我父母、我姐姐和我。'],
            ['Do you get along well with your sister?', '你和姐姐相处得好吗？'],
            ['Yes, we often help each other with homework.', '是的，我们经常互相帮助做作业。'],
        ],
    },
    {
        'title': 'Favorite Food 最喜欢的食物',
        'en': "Tom: What's your favorite food?\nLucy: I love noodles, especially beef noodles.\nTom: That's my favorite too! Which restaurant has the best noodles?\nLucy: There's a small shop near our school. It's delicious and cheap.",
        'zh': 'Tom: 你最喜欢的食物是什么？\nLucy: 我喜欢面条，特别是牛肉面。\nTom: 那也是我最喜欢的！哪家餐厅的面最好吃？\nLucy: 我们学校附近有个小店。又好吃又便宜。',
        'dialogue': [
            ["What's your favorite food?", '你最喜欢的食物是什么？'],
            ['I love noodles, especially beef noodles.', '我喜欢面条，特别是牛肉面。'],
            ["That's my favorite too! Which restaurant has the best noodles?", '那也是我最喜欢的！哪家餐厅的面最好吃？'],
            ["There's a small shop near our school. It's delicious and cheap.", '我们学校附近有个小店。又好吃又便宜。'],
        ],
    },
    {
        'title': 'Sports 运动',
        'en': 'Tom: Which sport do you like best?\nLucy: I like basketball. I play it every Saturday.\nTom: Really? I like badminton. Do you want to play together sometime?\nLucy: Sure! That would be fun.',
        'zh': 'Tom: 你最喜欢哪项运动？\nLucy: 我喜欢篮球。我每周六都打。\nTom: 真的吗？我喜欢羽毛球。有空我们一起打吧？\nLucy: 好啊！那会很有趣。',
        'dialogue': [
            ['Which sport do you like best?', '你最喜欢哪项运动？'],
            ['I like basketball. I play it every Saturday.', '我喜欢篮球。我每周六都打。'],
            ['Really? I like badminton. Do you want to play together sometime?', '真的吗？我喜欢羽毛球。有空我们一起打吧？'],
            ['Sure! That would be fun.', '好啊！那会很有趣。'],
        ],
    },
    {
        'title': 'Movies 电影',
        'en': "Tom: Did you watch that new movie last weekend?\nLucy: No, I didn't. Is it good?\nTom: Yes! It's a comedy and very funny.\nLucy: Maybe I'll watch it this weekend with my friends.",
        'zh': 'Tom: 你上周末看了那部新电影吗？\nLucy: 没有，我没看。好看吗？\nTom: 好看！是喜剧片，非常搞笑。\nLucy: 也许我这周末和朋友一起去看。',
        'dialogue': [
            ['Did you watch that new movie last weekend?', '你上周末看了那部新电影吗？'],
            ["No, I didn't. Is it good?", '没有，我没看。好看吗？'],
            ["Yes! It's a comedy and very funny.", '好看！是喜剧片，非常搞笑。'],
            ["Maybe I'll watch it this weekend with my friends.", '也许我这周末和朋友一起去看。'],
        ],
    },
    {
        'title': 'Birthday Party 生日派对',
        'en': "Tom: When is your birthday?\nLucy: It's on May 12th. I'm having a party at my house.\nTom: That's next Saturday! Can I come?\nLucy: Of course! I'll send you the address.",
        'zh': 'Tom: 你的生日是什么时候？\nLucy: 5月12日。我要在家里办派对。\nTom: 那是下周六！我可以来吗？\nLucy: 当然可以！我会把地址发给你。',
        'dialogue': [
            ['When is your birthday?', '你的生日是什么时候？'],
            ["It's on May 12th. I'm having a party at my house.", '5月12日。我要在家里办派对。'],
            ["That's next Saturday! Can I come?", '那是下周六！我可以来吗？'],
            ["Of course! I'll send you the address.", '当然可以！我会把地址发给你。'],
        ],
    },
    {
        'title': 'Holidays 假期',
        'en': 'Tom: Where did you go during the summer holiday?\nLucy: I went to Beijing with my parents.\nTom: Wow! Did you visit the Great Wall?\nLucy: Yes, it was amazing. I took lots of photos.',
        'zh': 'Tom: 暑假你去哪里了？\nLucy: 我和父母去了北京。\nTom: 哇！你去爬长城了吗？\nLucy: 去了，太壮观了。我拍了很多照片。',
        'dialogue': [
            ['Where did you go during the summer holiday?', '暑假你去哪里了？'],
            ['I went to Beijing with my parents.', '我和父母去了北京。'],
            ['Wow! Did you visit the Great Wall?', '哇！你去爬长城了吗？'],
            ['Yes, it was amazing. I took lots of photos.', '去了，太壮观了。我拍了很多照片。'],
        ],
    },
    {
        'title': 'Clothes Shopping 买衣服',
        'en': "Tom: Can I help you find anything?\nLucy: Yes, I'm looking for a jacket.\nTom: What size are you? We have S, M, L and XL.\nLucy: I think M. Can I try it on?\nTom: Sure, the fitting room is over there.",
        'zh': 'Tom: 需要我帮你找什么吗？\nLucy: 是的，我想买一件夹克。\nTom: 你穿什么尺码？我们有S、M、L和XL。\nLucy: 我想是M。我可以试穿吗？\nTom: 当然，试衣间在那边。',
        'dialogue': [
            ['Can I help you find anything?', '需要我帮你找什么吗？'],
            ["Yes, I'm looking for a jacket.", '是的，我想买一件夹克。'],
            ['What size are you? We have S, M, L and XL.', '你穿什么尺码？我们有S、M、L和XL。'],
            ['I think M. Can I try it on?', '我想是M。我可以试穿吗？'],
            ['Sure, the fitting room is over there.', '当然，试衣间在那边。'],
        ],
    },
    {
        'title': 'Asking Permission 请求许可',
        'en': 'Tom: Mom, can I go to the library after school?\nLucy: Sure, but come back before 6 PM.\nTom: OK, I will. I need to return some books.\nLucy: Be careful on the way.',
        'zh': 'Tom: 妈妈，放学后我可以去图书馆吗？\nLucy: 可以，但下午6点前回来。\nTom: 好的，我会的。我要还一些书。\nLucy: 路上小心。',
        'dialogue': [
            ['Mom, can I go to the library after school?', '妈妈，放学后我可以去图书馆吗？'],
            ['Sure, but come back before 6 PM.', '可以，但下午6点前回来。'],
            ['OK, I will. I need to return some books.', '好的，我会的。我要还一些书。'],
            ['Be careful on the way.', '路上小心。'],
        ],
    },
    {
        'title': 'Making Appointments 预约',
        'en': "Tom: Hello, I'd like to make an appointment with Dr. Smith.\nLucy: What day works for you?\nTom: Is next Monday afternoon available?\nLucy: Yes, 3 PM is fine. Please arrive 10 minutes early.",
        'zh': 'Tom: 你好，我想预约史密斯医生。\nLucy: 你哪天方便？\nTom: 下周一下午有空吗？\nLucy: 有，下午3点可以。请提前10分钟到。',
        'dialogue': [
            ["Hello, I'd like to make an appointment with Dr. Smith.", '你好，我想预约史密斯医生。'],
            ['What day works for you?', '你哪天方便？'],
            ['Is next Monday afternoon available?', '下周一下午有空吗？'],
            ['Yes, 3 PM is fine. Please arrive 10 minutes early.', '有，下午3点可以。请提前10分钟到。'],
        ],
    },
    {
        'title': 'Health and Exercise 健康与锻炼',
        'en': "Tom: You look very healthy. Do you exercise often?\nLucy: Yes, I run for 30 minutes every morning.\nTom: That's great! I should exercise more too.\nLucy: Why don't we run together tomorrow morning?",
        'zh': 'Tom: 你看起来很健康。你经常锻炼吗？\nLucy: 是的，我每天早上跑30分钟。\nTom: 太棒了！我也应该多锻炼。\nLucy: 我们明天早上一起跑吧？',
        'dialogue': [
            ['You look very healthy. Do you exercise often?', '你看起来很健康。你经常锻炼吗？'],
            ['Yes, I run for 30 minutes every morning.', '是的，我每天早上跑30分钟。'],
            ["That's great! I should exercise more too.", '太棒了！我也应该多锻炼。'],
            ["Why don't we run together tomorrow morning?", '我们明天早上一起跑吧？'],
        ],
    },
    {
        'title': 'Internet and Technology 互联网与科技',
        'en': "Tom: How often do you use the Internet?\nLucy: Almost every day. I use it for study and fun.\nTom: Me too. But my parents limit my screen time.\nLucy: Same here. They say it's not good for my eyes.",
        'zh': 'Tom: 你多久上一次网？\nLucy: 几乎每天。我用它来学习和娱乐。\nTom: 我也是。但我父母限制我的屏幕时间。\nLucy: 我也是。他们说对眼睛不好。',
        'dialogue': [
            ['How often do you use the Internet?', '你多久上一次网？'],
            ['Almost every day. I use it for study and fun.', '几乎每天。我用它来学习和娱乐。'],
            ['Me too. But my parents limit my screen time.', '我也是。但我父母限制我的屏幕时间。'],
            ["Same here. They say it's not good for my eyes.", '我也是。他们说对眼睛不好。'],
        ],
    },
    {
        'title': 'Taking a Bus 乘公交车',
        'en': 'Tom: Excuse me, does this bus go to the train station?\nLucy: Yes, it goes there. You need to get off at the fifth stop.\nTom: How much is the ticket?\nLucy: Two yuan. Please put the money in the box.',
        'zh': 'Tom: 打扰一下，这趟公交车去火车站吗？\nLucy: 是的，去那里。你要在第5站下车。\nTom: 车票多少钱？\nLucy: 两元。请把钱放进箱子里。',
        'dialogue': [
            ['Excuse me, does this bus go to the train station?', '打扰一下，这趟公交车去火车站吗？'],
            ['Yes, it goes there. You need to get off at the fifth stop.', '是的，去那里。你要在第5站下车。'],
            ['How much is the ticket?', '车票多少钱？'],
            ['Two yuan. Please put the money in the box.', '两元。请把钱放进箱子里。'],
        ],
    },
    {
        'title': 'At the Hotel 在酒店',
        'en': 'Tom: I have a reservation under the name Li Ming.\nLucy: Let me check... Yes, a single room for two nights.\nTom: Does the room have free Wi-Fi?\nLucy: Yes, and breakfast is included too.',
        'zh': 'Tom: 我用李明这个名字预订了房间。\nLucy: 我查一下……是的，一间单人房，住两晚。\nTom: 房间有免费Wi-Fi吗？\nLucy: 有，而且早餐也包含在内。',
        'dialogue': [
            ['I have a reservation under the name Li Ming.', '我用李明这个名字预订了房间。'],
            ['Let me check... Yes, a single room for two nights.', '我查一下……是的，一间单人房，住两晚。'],
            ['Does the room have free Wi-Fi?', '房间有免费Wi-Fi吗？'],
            ['Yes, and breakfast is included too.', '有，而且早餐也包含在内。'],
        ],
    },
    {
        'title': 'Complaining 投诉',
        'en': "Tom: Excuse me, I ordered beef noodles but this is chicken noodles.\nLucy: Oh, I'm very sorry. Let me check your order.\nTom: I've been waiting for 30 minutes already.\nLucy: I apologize. Your correct order will be ready in 5 minutes.",
        'zh': 'Tom: 打扰一下，我点的是牛肉面，但这是鸡肉面。\nLucy: 哦，非常抱歉。让我查一下你的订单。\nTom: 我已经等了30分钟了。\nLucy: 我道歉。你正确的订单5分钟内就好。',
        'dialogue': [
            ['Excuse me, I ordered beef noodles but this is chicken noodles.', '打扰一下，我点的是牛肉面，但这是鸡肉面。'],
            ["Oh, I'm very sorry. Let me check your order.", '哦，非常抱歉。让我查一下你的订单。'],
            ["I've been waiting for 30 minutes already.", '我已经等了30分钟了。'],
            ['I apologize. Your correct order will be ready in 5 minutes.', '我道歉。你正确的订单5分钟内就好。'],
        ],
    },
    {
        'title': 'Making Friends 交朋友',
        'en': "Tom: Hi, is this seat taken?\nLucy: No, it's free. Sit down, please.\nTom: Thanks. I'm new here. What's your name?\nLucy: I'm Tom. Nice to meet you!",
        'zh': 'Tom: 你好，这个座位有人坐吗？\nLucy: 没有，空的。请坐。\nTom: 谢谢。我是新来的。你叫什么名字？\nLucy: 我叫汤姆。很高兴认识你！',
        'dialogue': [
            ['Hi, is this seat taken?', '你好，这个座位有人坐吗？'],
            ["No, it's free. Sit down, please.", '没有，空的。请坐。'],
            ["Thanks. I'm new here. What's your name?", '谢谢。我是新来的。你叫什么名字？'],
            ["I'm Tom. Nice to meet you!", '我叫汤姆。很高兴认识你！'],
        ],
    },
    {
        'title': 'After-school Activities 课后活动',
        'en': "Tom: Which club did you join this term?\nLucy: I joined the English club. We practice speaking every Tuesday.\nTom: That's cool. I joined the art club.\nLucy: Really? Can you draw cartoons?",
        'zh': 'Tom: 这学期你参加了哪个社团？\nLucy: 我参加了英语社团。我们每周二练习口语。\nTom: 太酷了。我参加了美术社团。\nLucy: 真的吗？你会画漫画吗？',
        'dialogue': [
            ['Which club did you join this term?', '这学期你参加了哪个社团？'],
            ['I joined the English club. We practice speaking every Tuesday.', '我参加了英语社团。我们每周二练习口语。'],
            ["That's cool. I joined the art club.", '太酷了。我参加了美术社团。'],
            ['Really? Can you draw cartoons?', '真的吗？你会画漫画吗？'],
        ],
    },
    {
        'title': 'Shopping for Gifts 买礼物',
        'en': "Tom: I want to buy a gift for my friend's birthday.\nLucy: How about a book or a music box?\nTom: She loves reading. A book is a good idea.\nLucy: There's a bookstore on the second floor.",
        'zh': 'Tom: 我想给朋友的生日买个礼物。\nLucy: 书或者音乐盒怎么样？\nTom: 她喜欢阅读。书是个好主意。\nLucy: 二楼有一家书店。',
        'dialogue': [
            ["I want to buy a gift for my friend's birthday.", '我想给朋友的生日买个礼物。'],
            ['How about a book or a music box?', '书或者音乐盒怎么样？'],
            ['She loves reading. A book is a good idea.', '她喜欢阅读。书是个好主意。'],
            ["There's a bookstore on the second floor.", '二楼有一家书店。'],
        ],
    },
    {
        'title': 'Talking about Seasons 谈论季节',
        'en': "Tom: Which season do you like best?\nLucy: I like autumn best. The weather is cool and the leaves are beautiful.\nTom: I prefer spring. Everything comes back to life.\nLucy: That's true. Spring is full of hope.",
        'zh': 'Tom: 你最喜欢哪个季节？\nLucy: 我最喜欢秋天。天气凉爽，树叶很美。\nTom: 我更喜欢春天。万物复苏。\nLucy: 没错。春天充满希望。',
        'dialogue': [
            ['Which season do you like best?', '你最喜欢哪个季节？'],
            ['I like autumn best. The weather is cool and the leaves are beautiful.', '我最喜欢秋天。天气凉爽，树叶很美。'],
            ['I prefer spring. Everything comes back to life.', '我更喜欢春天。万物复苏。'],
            ["That's true. Spring is full of hope.", '没错。春天充满希望。'],
        ],
    },
    {
        'title': 'Job Interview',
        'en': "Tom: Good morning. Please sit down. I'm Mr. Brown, the HR manager.\nLucy: Good morning, Mr. Brown. Thank you for having me.\nTom: Could you tell me something about yourself?\nLucy: My name is Li Hua. I graduated from Beijing University with a degree in English. I have been working as an English teacher for three years.\nTom: Why do you want to change your job?\nLucy: I want to challenge myself in a new environment. Your company has a good reputation and I think I can learn a lot here.\nTom: What are your strengths?\nLucy: I am patient, responsible, and I can communicate well with people. I also have good computer skills.\nTom: Can you work under pressure?\nLucy: Yes, I can. Teaching requires me to handle pressure every day, so I am used to it.\nTom: What is your greatest weakness?\nLucy: Sometimes I work too hard and forget to take breaks. I am trying to improve my time management.\nTom: Do you have any questions for me?\nLucy: Yes, what would a typical workday look like for this position?\nTom: You would handle international business communications and translate documents.\nLucy: That sounds interesting. When can I know the result?\nTom: We will inform you within one week. Thank you for coming today.\nLucy: Thank you, Mr. Brown. I look forward to hearing from you.",
        'zh': 'Tom: 早上好，请坐。我是布朗先生，人力资源经理。\nLucy: 早上好，布朗先生，谢谢您给我这个机会。\nTom: 能介绍一下你自己吗？\nLucy: 我叫李华，毕业于北京大学英语专业。我已经做了三年英语老师了。\nTom: 你为什么想换工作？\nLucy: 我想在新环境中挑战自己。贵公司声誉很好，我觉得能在这里学到很多东西。\nTom: 你的优势是什么？\nLucy: 我有耐心、负责任，善于与人沟通，而且电脑技能也不错。\nTom: 你能承受压力吗？\nLucy: 能。教学本身每天都要承受压力，所以我已经习惯了。\nTom: 你最大的缺点是什么？\nLucy: 有时候我工作太努力忘记休息。我正在努力改善时间管理。\nTom: 你有什么问题想问我的吗？\nLucy: 是的，这个职位的典型工作日是什么样的？\nTom: 你将处理国际商务沟通和文件翻译工作。\nLucy: 听起来很有趣。我什么时候能知道结果？\nTom: 我们会在一周内通知你。谢谢你今天来面试。\nLucy: 谢谢您，布朗先生。期待您的好消息。',
        'dialogue': [
            ['Good morning. Please have a seat.', '早上好，请坐。'],
            ["Thank you. I'm here for the interview.", '谢谢，我是来参加面试的。'],
            ['Tell me about yourself.', '请介绍一下你自己。'],
            ['I graduated from Peking University last year.', '我去年毕业于北京大学。'],
            ["What's your major?", '你学的是什么专业？'],
            ['My major is Computer Science.', '我的专业是计算机科学。'],
            ['Do you have any work experience?', '你有工作经验吗？'],
            ['I had an internship at a tech company.', '我在一家科技公司实习过。'],
            ['Why do you want to work here?', '你为什么想在这里工作？'],
            ['Because your company is a leader in AI.', '因为贵公司是人工智能领域的领导者。'],
            ['What are your strengths?', '你的优点是什么？'],
            ["I'm good at Python and problem solving.", '我擅长Python和解决问题。'],
            ['When can you start?', '你什么时候能开始工作？'],
            ['I can start next month.', '我下个月可以开始。'],
            ["We'll call you next week. Thank you.", '我们下周会给你打电话，谢谢。'],
        ],
    },
    {
        'title': 'At the Hospital',
        'en': 'Tom: Good afternoon. What brings you here today?\nLucy: Good afternoon, doctor. I have been feeling very tired lately and I cannot sleep well at night.\nTom: How long has this been going on?\nLucy: For about two weeks. I also have a headache sometimes.\nTom: Do you have any other symptoms? Like a fever or a cough?\nLucy: No fever, but I do have a dry cough now and then.\nTom: Let me check your temperature and blood pressure first. Please sit here.\nLucy: OK, doctor.\nTom: Your temperature is normal, but your blood pressure is a little high. Are you under a lot of stress recently?\nLucy: Yes, I have an important exam coming up and I am very worried about it.\nTom: I see. You need to relax more. Are you doing any exercise?\nLucy: Not really. I am too busy with my studies.\nTom: That might be part of the problem. I recommend you take a walk for 30 minutes every day and get enough sleep.\nLucy: Should I take some medicine?\nTom: I will give you some mild sleeping pills. Take one before bed, but only for one week. Do not rely on them for too long.\nLucy: I understand. Is there anything else I should pay attention to?\nTom: Try to avoid coffee and tea in the evening. Also, do not use your phone before sleeping.\nLucy: Got it. Thank you very much, doctor.\nTom: You are welcome. Come back if the symptoms continue. Take care of yourself.',
        'zh': 'Tom: 下午好，今天哪里不舒服？\nLucy: 下午好，医生。我最近总觉得非常疲倦，晚上也睡不好。\nTom: 这样持续多久了？\nLucy: 大概两周了。有时候还会头痛。\nTom: 还有其他症状吗？比如发烧或咳嗽？\nLucy: 不发烧，但偶尔会干咳。\nTom: 先让我检查一下你的体温和血压。请坐这里。\nLucy: 好的，医生。\nTom: 体温正常，但血压有点高。你最近压力大吗？\nLucy: 是的，有一个重要考试快要来了，我非常担心。\nTom: 我明白了。你需要多放松。你有运动吗？\nLucy: 几乎没有。我学习太忙了。\nTom: 这可能是原因之一。我建议你每天散步30分钟，保证充足睡眠。\nLucy: 我需要吃药吗？\nTom: 我给你开一些温和的安眠药。睡前吃一片，只吃一周，不要长期依赖。\nLucy: 我明白了。还有什么需要注意的吗？\nTom: 晚上尽量避免喝咖啡和茶。还有，睡前不要玩手机。\nLucy: 明白了。非常感谢您，医生。\nTom: 不客气。如果症状持续就再来复查。多保重。',
        'dialogue': [
            ["Good morning. I'd like to see a doctor.", '早上好，我想看医生。'],
            ['Do you have an appointment?', '你有预约吗？'],
            ["No, I don't. I feel terrible.", '没有，我感觉很难受。'],
            ['What seems to be the problem?', '你哪里不舒服？'],
            ['I have a fever and a sore throat.', '我发烧，喉咙痛。'],
            ['How long have you been feeling this way?', '你这样多久了？'],
            ['Since yesterday evening.', '从昨天晚上开始的。'],
            ['Let me check your temperature.', '让我量一下你的体温。'],
            ["It's 38.5 degrees. You have a cold.", '38.5度，你感冒了。'],
            ['Do I need any medicine?', '我需要吃药吗？'],
            ["Yes, I'll prescribe some medicine.", '是的，我会开一些药。'],
            ['How often should I take it?', '我应该多久吃一次？'],
            ['Three times a day after meals.', '每天三次，饭后服用。'],
            ['Should I stay in bed?', '我需要卧床休息吗？'],
            ['Yes, get plenty of rest and drink water.', '是的，多休息，多喝水。'],
        ],
    },
    {
        'title': 'Shopping for Clothes',
        'en': 'Tom: Good afternoon. Can I help you with something today?\nLucy: Yes, please. I am looking for a suit for a job interview.\nTom: We have some nice suits over here. What color do you prefer?\nLucy: I prefer dark blue or black.\nTom: How about this one? It is a dark blue suit, size M. It looks very professional.\nLucy: It looks nice. Can I try it on?\nTom: Of course. The fitting room is right over there.\nLucy: Thank you. ... How do I look?\nTom: It fits you very well! The style is very suitable for an interview.\nLucy: Great! I will take it. Do you have a white shirt to go with it?\nTom: Yes, we have several. What size do you wear?\nLucy: I wear size 40.\nTom: Here is a white shirt, size 40. And we have a red tie that goes well with it.\nLucy: The red tie is too bright. Do you have a dark blue one?\nTom: Let me check... Yes, here it is. The dark blue tie matches perfectly.\nLucy: Perfect! How much is everything together?\nTom: The suit is 680 yuan, the shirt is 180 yuan, and the tie is 90 yuan. That is 950 yuan in total.\nLucy: That is a bit expensive. Is there any discount?\nTom: We have a 20 percent discount today, so you will pay 760 yuan.\nLucy: That is much better. I will pay by credit card.\nTom: No problem. Please sign here. Thank you for shopping with us!\nLucy: Thank you for your help!',
        'zh': 'Tom: 下午好。有什么可以帮您的吗？\nLucy: 是的，我想买一套求职面试穿的西装。\nTom: 这边有几套不错的。请问您喜欢什么颜色？\nLucy: 深蓝色或黑色都可以。\nTom: 这套怎么样？深蓝色，M码，看起来非常职业。\nLucy: 看起来不错。我能试穿一下吗？\nTom: 当然可以。试衣间在那边。\nLucy: 谢谢。……看起来怎么样？\nTom: 非常合身！款式很适合面试。\nLucy: 太好了！就买这件了。你们有配套的白衬衫吗？\nTom: 有的，有好几款。您穿多大尺码？\nLucy: 40码。\nTom: 这件白衬衫，40码。还有一条红色领带很搭配。\nLucy: 红色太亮了。有没有深蓝色的？\nTom: 我找找……有的，在这里。深蓝色领带非常匹配。\nLucy: 完美！一共多少钱？\nTom: 西装680元，衬衫180元，领带90元。总共950元。\nLucy: 有点贵了。能打折吗？\nTom: 今天打八折，您只需付760元。\nLucy: 那好多了。我用信用卡付款。\nTom: 没问题。请在这里签字。谢谢光临！\nLucy: 谢谢你的帮助！',
        'dialogue': [
            ['Can I help you find anything?', '需要我帮你找什么吗？'],
            ["I'm looking for a winter coat.", '我想找一件冬季外套。'],
            ['What size do you wear?', '你穿什么尺码？'],
            ["I think I'm a medium.", '我想我是中号。'],
            ['Here are some coats in medium.', '这些是中号的外套。'],
            ['This one looks nice. Can I try it on?', '这件看起来不错，能试穿吗？'],
            ['Sure, the fitting room is over there.', '当然，试衣间在那边。'],
            ['How does it fit?', '合身吗？'],
            ["It's a bit tight in the shoulders.", '肩膀有点紧。'],
            ["Try this one. It's a larger size.", '试试这件，尺码大一点。'],
            ['This one is much better. How much is it?', '这件好多了，多少钱？'],
            ["It's on sale for two hundred yuan.", '打折后两百元。'],
            ["That's a good price. I'll take it.", '价格不错，我买了。'],
            ['Would you like to pay by cash or card?', '你用现金还是卡支付？'],
            ['Card, please. Thank you!', '刷卡，谢谢！'],
        ],
    },
    {
        'title': 'At the Restaurant',
        'en': 'Tom: Good evening. Welcome to Golden Dragon Restaurant. Do you have a reservation?\nLucy: Yes, under the name Wang.\nTom: Right this way, please. Here is your table.\nLucy: Thank you. Can we see the menu, please?\nTom: Of course. Here you are. Our special today is Beijing Roast Duck.\nLucy: That sounds delicious. Let me have a look at the menu first.\nTom: Take your time. I will come back to take your order.\nLucy: Thank you.\n... (a few minutes later) ...\nTom: Are you ready to order?\nLucy: Yes, we would like the Beijing Roast Duck, a plate of fried rice, and some vegetables.\nTom: Would you like soup or salad to start?\nLucy: A vegetable soup, please.\nTom: And to drink?\nLucy: A bottle of still water and one glass of orange juice, please.\nTom: Got it. Beijing Roast Duck, vegetable soup, fried rice, vegetables, still water, and orange juice.\nLucy: Yes, that is correct. Also, could we have some more tea?\nTom: Of course. I will bring it right away.\n... (after the meal) ...\nTom: How was everything?\nLucy: It was wonderful, thank you. Could we have the bill, please?\nTom: Sure. Here it is. That comes to 360 yuan.\nLucy: Here is 400 yuan. Keep the change.\nTom: Thank you very much! I hope you enjoyed your meal. Please come again!',
        'zh': 'Tom: 晚上好，欢迎光临金龙饭店。请问您有预约吗？\nLucy: 有的，姓王。\nTom: 请这边走。您的桌子在这边。\nLucy: 谢谢。我们可以看一下菜单吗？\nTom: 当然，给您。我们的今日推荐是北京烤鸭。\nLucy: 听起来很好吃。让我先看看菜单。\nTom: 您慢慢看，我一会儿来为您点餐。\nLucy: 谢谢。\n……（几分钟后）……\nTom: 请问准备好点餐了吗？\nLucy: 是的，我们想要北京烤鸭、一份炒饭和一些蔬菜。\nTom: 想要先来点汤或沙拉吗？\nLucy: 麻烦来一份蔬菜汤。\nTom: 饮料呢？\nLucy: 一瓶矿泉水和一杯橙汁，谢谢。\nTom: 好的。北京烤鸭、蔬菜汤、炒饭、蔬菜、矿泉水和橙汁。\nLucy: 对，没错。另外，可以再给我们添点茶吗？\nTom: 当然，我马上送来。\n……（用餐结束后）……\nTom: 请问菜品如何？\nLucy: 非常美味，谢谢。可以买单了吗？\nTom: 好的，这是账单。一共360元。\nLucy: 这是400元，不用找了。\nTom: 非常感谢！希望您用餐愉快。欢迎下次光临！',
        'dialogue': [
            ['Table for two, please.', '请安排一张两人桌。'],
            ['Smoking or non-smoking?', '吸烟区还是非吸烟区？'],
            ['Non-smoking, please.', '非吸烟区，谢谢。'],
            ["Follow me. Here's your table.", '跟我来，这是你们的桌子。'],
            ['Can I get you something to drink?', '你们想喝点什么？'],
            ["I'll have a glass of orange juice.", '我要一杯橙汁。'],
            ["And I'll have a cola, please.", '我要一杯可乐。'],
            ['Are you ready to order?', '你们准备好点餐了吗？'],
            ["Yes, I'd like the beef noodles.", '是的，我要牛肉面。'],
            ['And for you?', '你呢？'],
            ["I'll have the chicken rice.", '我要鸡肉饭。'],
            ['Would you like any side dishes?', '你们要配菜吗？'],
            ["No, thank you. That's all.", '不用了，谢谢，就这些。'],
            ['Enjoy your meal!', '请慢用！'],
            ['The food is delicious! Can we get the bill?', '食物很好吃！能给我们账单吗？'],
            ["Here you are. That'll be sixty yuan.", '给你们，一共六十元。'],
        ],
    },
    {
        'title': 'Travel Planning',
        'en': 'Tom: Summer vacation is coming soon. Have you made any plans?\nLucy: I am thinking about going to Shanghai. Have you ever been there?\nTom: Yes, I went there two years ago. It is a modern and exciting city.\nLucy: Really? What places did you visit?\nTom: I visited the Bund, Nanjing Road, the Oriental Pearl Tower, and Yuyuan Garden. They were all amazing.\nLucy: That sounds great! How long should I stay there?\nTom: I think four or five days is enough to see the main attractions.\nLucy: Do you know a good hotel near the Bund?\nTom: There is a nice hotel called Park Hyatt. It is close to the river and the service is excellent.\nLucy: How much does it cost per night?\nTom: Around 800 yuan per night for a standard room. But if you book online early, you can get a discount.\nLucy: Good idea. Should I book the hotel first or buy the train tickets first?\nTom: I think you should buy the train tickets first, because they sell out quickly during holidays.\nLucy: You are right. Which train should I take?\nTom: The high-speed train is the fastest. It only takes about five hours from here to Shanghai.\nLucy: Perfect! I will start planning it this weekend.\nTom: Have a great trip! And do not forget to try the local food in Shanghai.\nLucy: I definitely will. Thank you for all the advice!',
        'zh': 'Tom: 暑假快到了，你有什么计划吗？\nLucy: 我想去上海。你去过那里吗？\nTom: 去过，两年前去的。那是一座现代化又迷人的城市。\nLucy: 真的吗？你去了哪些地方？\nTom: 我去了外滩、南京路、东方明珠塔和豫园。都非常棒。\nLucy: 听起来太棒了！我应该在那里待几天？\nTom: 我觉得四五天足够看完主要景点了。\nLucy: 你知道外滩附近有什么好酒店吗？\nTom: 有个叫柏悦的酒店很不错，靠近黄浦江，服务也很好。\nLucy: 每晚多少钱？\nTom: 标准间大约800元一晚。但如果提前网上预订，可以打折。\nLucy: 好主意。我是先订酒店还是先买车票？\nTom: 我觉得应该先买车票，因为节假日车票卖得很快。\nLucy: 你说得对。我应该坐什么车？\nTom: 高铁最快，从这里到上海只要五个小时左右。\nLucy: 太好了！我这周末就开始计划。\nTom: 祝你旅途愉快！别忘了尝尝上海的本地美食。\nLucy: 一定会的！谢谢你的建议！',
        'dialogue': [
            ['Where should we go for the holiday?', '假期我们应该去哪里？'],
            ['How about Sanya? The beach is beautiful.', '三亚怎么样？海滩很美。'],
            ['That sounds great! When should we go?', '听起来很棒！我们什么时候去？'],
            ['How about next Saturday?', '下周六怎么样？'],
            ['Perfect. Should we book a hotel?', '完美，我们需要订酒店吗？'],
            ["Yes, I'll look for a nice hotel online.", '是的，我会在网上找一家好的酒店。'],
            ['What about the flight?', '机票怎么办？'],
            ['I can book the tickets this afternoon.', '我今天下午可以订票。'],
            ['How long should we stay?', '我们应该待多久？'],
            ['Five days would be good.', '五天应该不错。'],
            ['What should we pack?', '我们应该带什么？'],
            ['Sunscreen, swimsuits, and casual clothes.', '防晒霜、泳衣和休闲衣服。'],
            ['Should I bring a camera?', '我应该带相机吗？'],
            ["Definitely! We'll want photos.", '当然！我们会想要拍照的。'],
            ["I can't wait! This will be amazing.", '我等不及了！这将会很棒。'],
        ],
    },
    {
        'title': 'At the Hotel',
        'en': 'Tom: Good evening. Welcome to Sunshine Hotel. How can I help you?\nLucy: Good evening. I have a reservation. My name is Zhang Wei.\nTom: Let me check... Yes, Mr. Zhang. You have booked a double room for three nights.\nLucy: That is correct.\nTom: Could you please show me your ID?\nLucy: Here you are.\nTom: Thank you. Your room number is 508 on the fifth floor. Here is your key card.\nLucy: Thank you. What time is breakfast?\nTom: Breakfast is served from 7 AM to 10 AM in the restaurant on the second floor.\nLucy: Does the room have free Wi-Fi?\nTom: Yes, it does. The password is on the card beside your bed.\nLucy: Great. Is there a gym in the hotel?\nTom: Yes, the gym is on the first floor and it is open 24 hours.\nLucy: Wonderful. And could you wake me up at 7 o clock tomorrow morning?\nTom: Of course. What way would you prefer, by phone or by knocking on the door?\nLucy: By phone, please.\nTom: No problem. Is there anything else you need?\nLucy: Could I have an extra towel, please?\nTom: Sure, I will send someone to bring one to your room right away.\nLucy: Thank you very much.\nTom: You are welcome. Enjoy your stay!',
        'zh': 'Tom: 晚上好，欢迎光临阳光酒店。有什么可以帮您的？\nLucy: 晚上好，我预约了房间。我姓张，名伟。\nTom: 让我查一下……是的，张先生。您预订了一间双人间，住三晚。\nLucy: 没错。\nTom: 请出示一下您的身份证好吗？\nLucy: 给您。\nTom: 谢谢。您的房间是五楼508室。这是您的房卡。\nLucy: 谢谢。早餐几点供应？\nTom: 早餐早上7点到10点，在二楼餐厅供应。\nLucy: 房间里有免费Wi-Fi吗？\nTom: 有的，密码在您床边那张卡片上。\nLucy: 太好了。酒店有健身房吗？\nTom: 有的，健身房在一楼，24小时开放。\nLucy: 太棒了。另外，能在明天早上7点叫醒我吗？\nTom: 当然可以。您希望用什么方式叫您，电话还是敲门？\nLucy: 电话吧。\nTom: 没问题。还有什么需要吗？\nLucy: 能再加一条毛巾吗？\nTom: 好的，我马上派人送到您房间。\nLucy: 非常感谢。\nTom: 不客气，祝您入住愉快！',
        'dialogue': [
            ['Good evening. I have a reservation.', '晚上好，我有预订。'],
            ['Under what name, please?', '请问以什么名字预订的？'],
            ['Zhang Wei. I booked online.', '张伟，我在网上预订的。'],
            ['Let me check... Yes, here it is.', '让我查一下……是的，找到了。'],
            ["You're in room 1208. Here's your key card.", '你在1208号房间，这是你的房卡。'],
            ['Is breakfast included?', '包含早餐吗？'],
            ['Yes, breakfast is served from 7 to 10.', '是的，早餐供应时间是7点到10点。'],
            ['Great. Where is the elevator?', '太好了，电梯在哪里？'],
            ["It's just around the corner.", '就在拐角处。'],
            ['Excuse me, where is the gym?', '打扰一下，健身房在哪里？'],
            ['The gym is on the third floor.', '健身房在三楼。'],
            ['What time does it close?', '什么时候关门？'],
            ["It's open until 10 PM.", '开放到晚上10点。'],
            ['Can I get room service?', '我可以要客房服务吗？'],
            ['Yes, just dial 0 from your room.', '可以，从房间拨0就行。'],
        ],
    },
    {
        'title': 'School Life',
        'en': 'Tom: Hi, Tom! Have you finished the English homework?\nLucy: Not yet. I was working on the math problems until late last night.\nTom: The math homework is also due today! I forgot all about it.\nLucy: Oh no! We should finish it during lunch break.\nTom: Good idea. By the way, are you going to the school talent show next Friday?\nLucy: Yes, I signed up for it. I will play the piano.\nTom: That is so cool! I also want to join, but I do not have any special skills.\nLucy: You could sing a song or tell a joke. Everyone has something to share.\nTom: Maybe I will just watch this year and prepare something for next year.\nLucy: That is fine too. Have you decided which club to join this term?\nTom: I am thinking about joining the science club. What about you?\nLucy: I want to join the basketball team. I heard the coach is very strict but very good.\nTom: The coach is really good. My brother was on the team last year and he learned a lot.\nLucy: That is great! Oh, it is almost time for class. See you at lunch.\nTom: See you! Do not forget to bring your homework!\nLucy: I will not! Bye!',
        'zh': 'Tom: 嗨，汤姆！你的英语作业做完了吗？\nLucy: 还没呢。我昨晚一直在做数学题，做到很晚。\nTom: 数学作业今天也要交啊！我全忘了。\nLucy: 糟糕！我们午休时应该把它做完。\nTom: 好主意。对了，下周五的学校才艺表演你去吗？\nLucy: 去啊，我报名了。我要弹钢琴。\nTom: 太酷了！我也想参加，但我没有什么特长。\nLucy: 你可以唱首歌或讲个笑话。每个人都有自己的闪光点。\nTom: 也许我今年先观看，明年再准备一个节目。\nLucy: 那也好。你决定这学期参加什么社团了吗？\nTom: 我想参加科学社。你呢？\nLucy: 我想加入篮球队。听说教练很严格但很厉害。\nTom: 教练真的很棒。我哥哥去年在队里，学到了很多东西。\nLucy: 太棒了！哦，快上课了。午餐时见。\nTom: 见！别忘了带作业！\nLucy: 不会忘的！再见！',
        'dialogue': [
            ['How was your first day at school?', '你上学第一天怎么样？'],
            ['It was good! I like my new classmates.', '很好！我喜欢我的新同学。'],
            ["What's your favorite subject?", '你最喜欢的科目是什么？'],
            ['I love English and P.E.', '我喜欢英语和体育。'],
            ['Who is your English teacher?', '你的英语老师是谁？'],
            ["Mr. Brown. He's from America.", '布朗先生，他来自美国。'],
            ["That's cool! Is he strict?", '太酷了！他严格吗？'],
            ['Not really. He makes learning fun.', '不严格，他让学习变得有趣。'],
            ['What clubs are you in?', '你参加了什么社团？'],
            ['I joined the basketball team.', '我加入了篮球队。'],
            ['When do you practice?', '你们什么时候训练？'],
            ['Every Tuesday and Thursday after school.', '每周二和周四放学后。'],
            ['That sounds like a lot of fun.', '听起来很有趣。'],
            ['It is! You should join too.', '是的！你也应该加入。'],
            ['Maybe I will! See you tomorrow.', '也许我会！明天见。'],
        ],
    },
    {
        'title': 'Hobbies and Interests',
        'en': 'Tom: Hi, Lily! What do you like to do in your free time?\nLucy: I love painting. I take art classes every Saturday.\nTom: That sounds fun! What kind of paintings do you like to do?\nLucy: I mostly do oil paintings. I think the colors are richer and more expressive.\nTom: I wish I could paint. I only know how to draw stick figures.\nLucy: Everyone starts somewhere. You should try it. It is very relaxing.\nTom: What about you? Do you have any other hobbies?\nLucy: Yes, I also enjoy reading novels and playing the guitar.\nTom: You can play the guitar? That is impressive!\nLucy: Well, I am still learning. I have been taking lessons for about six months.\nTom: That is great progress! I want to pick up a hobby too, but I do not know where to start.\nLucy: What do you enjoy doing most?\nTom: I like listening to music and watching movies.\nLucy: Have you thought about learning a musical instrument? Music and movies are related to art.\nTom: That is a good idea. Maybe I can start with the ukulele. It looks easy to learn.\nLucy: Yes, it is! And it is not expensive. You should get one and learn some basic chords.\nTom: I will think about it. Thanks for the advice, Lily.\nLucy: You are welcome. We can paint and play music together sometime!\nTom: That would be amazing!',
        'zh': 'Tom: 嗨，莉莉！你空闲时间喜欢做什么？\nLucy: 我喜欢画画。每个周六都上美术课。\nTom: 听起来很有趣！你喜欢画什么样的画？\nLucy: 我主要画油画。我觉得油画的色彩更丰富、更有表现力。\nTom: 我真希望我也会画画。我只会画火柴人。\nLucy: 每个人都是从头开始的。你应该试试，画画很放松。\nTom: 你呢？还有其他爱好吗？\nLucy: 有啊，我还喜欢看小说和弹吉他。\nTom: 你会弹吉他？太厉害了！\nLucy: 嗯，我还在学。上了大概六个月的课了。\nTom: 进步很大啊！我也想培养一个爱好，但不知道从哪里开始。\nLucy: 你最喜欢做什么？\nTom: 我喜欢听音乐和看电影。\nLucy: 有没有想过学一种乐器？音乐和电影都与艺术有关。\nTom: 好主意。也许我可以先从尤克里里开始，看起来比较容易学。\nLucy: 是啊！而且不贵。你可以买一把，学一些基础和弦。\nTom: 我考虑一下。谢谢你的建议，莉莉。\nLucy: 不客气。以后我们可以一起画画、一起弹音乐！\nTom: 那太好了！',
        'dialogue': [
            ['What do you like to do in your free time?', '你空闲时间喜欢做什么？'],
            ['I enjoy reading and playing guitar.', '我喜欢阅读和弹吉他。'],
            ["That's interesting! What kind of books?", '真有趣！你喜欢什么类型的书？'],
            ['I love science fiction and history.', '我喜欢科幻小说和历史书。'],
            ['How long have you played guitar?', '你弹吉他多久了？'],
            ["About three years. I'm still learning.", '大约三年了，我还在学习。'],
            ['Do you play any sports?', '你做运动吗？'],
            ['Yes, I play badminton every weekend.', '是的，我每个周末都打羽毛球。'],
            ['Who do you play with?', '你和谁一起打？'],
            ["My sister. She's really good!", '我姐姐，她打得很好！'],
            ['Do you like watching movies?', '你喜欢看电影吗？'],
            ['Yes! My favorite genre is comedy.', '喜欢！我最喜欢的类型是喜剧。'],
            ["Who's your favorite actor?", '你最喜欢的演员是谁？'],
            ['I love Jackie Chan. His movies are funny.', '我喜欢成龙，他的电影很搞笑。'],
            ['We should watch a movie together sometime!', '我们应该找个时间一起看电影！'],
        ],
    },
    {
        'title': 'Environmental Protection',
        'en': 'Tom: Hi, Jack! I saw you carrying a reusable water bottle. That is a great habit!\nLucy: Thank you! I think it is important to reduce plastic waste. Every year, millions of plastic bottles end up in the ocean.\nTom: You are right. The ocean pollution is getting worse. What else can we do to protect the environment?\nLucy: We can use less electricity, take public transportation, and recycle whenever possible.\nTom: I usually ride my bike to school. It is good for both health and the environment.\nLucy: That is awesome! I should start doing that too.\nTom: And we can plant more trees. Trees clean the air and provide homes for animals.\nLucy: Our school is organizing a tree-planting activity next month. Will you join?\nTom: Yes, I will! Count me in. Where will the trees be planted?\nLucy: In the park near our school. The local government is supporting this activity.\nTom: That is wonderful. I will tell my parents and ask them to join as well.\nLucy: Great idea! The more people, the better. We should also save water.\nTom: Definitely. I always turn off the tap while brushing my teeth.\nLucy: Small actions make a big difference. If everyone does a little, it adds up to a lot.\nTom: Absolutely. Let us do our best to protect our planet!\nLucy: Yes! This is the only Earth we have. Let us take care of it together.',
        'zh': 'Tom: 嗨，杰克！我看到你带了一个可重复使用的水壶。这个习惯真棒！\nLucy: 谢谢！我觉得减少塑料垃圾很重要。每年有数百万个塑料瓶流入海洋。\nTom: 你说得对。海洋污染越来越严重了。我们还能做什么来保护环境？\nLucy: 我们可以少用电、乘公共交通出行、尽可能回收利用。\nTom: 我通常骑自行车上学。这样对健康和环境都有好处。\nLucy: 太棒了！我也应该开始骑自行车了。\nTom: 我们还可以种更多的树。树木净化空气，为动物提供家园。\nLucy: 我们学校下个月要组织一次植树活动，你要参加吗？\nTom: 好的，算我一个！种在哪里？\nLucy: 在我们学校附近的公园。当地政府支持这个活动。\nTom: 太棒了。我告诉父母，让他们也参加。\nLucy: 好主意！人越多越好。我们还应该节约用水。\nTom: 没错。我刷牙时总是关掉水龙头。\nLucy: 小行动带来大改变。如果每个人做一点，汇集起来就很可观了。\nTom: 说得好。让我们尽力保护地球！\nLucy: 是的！地球是我们唯一的家，让我们一起保护它。',
        'dialogue': [
            ['Have you heard about the new recycling policy?', '你听说了新的回收政策吗？'],
            ['Yes, it started this month.', '听说了，这个月开始实施的。'],
            ['Do you separate your trash at home?', '你在家里垃圾分类吗？'],
            ['Of course! We have four bins.', '当然！我们有四个垃圾桶。'],
            ["That's great. What can we recycle?", '太好了，什么可以回收？'],
            ['Paper, plastic, glass, and metal.', '纸张、塑料、玻璃和金属。'],
            ['What about food waste?', '食物垃圾呢？'],
            ['That goes in the wet waste bin.', '食物垃圾放在湿垃圾桶里。'],
            ['Should we stop using plastic bags?', '我们应该停止使用塑料袋吗？'],
            ['Yes, we should use reusable bags.', '是的，我们应该用可重复使用的袋子。'],
            ['What else can we do to help the environment?', '我们还能做什么来保护环境？'],
            ['Walk or bike instead of driving.', '走路或骑自行车而不是开车。'],
            ['That makes sense. Save energy too?', '有道理，还要节约能源？'],
            ['Yes, turn off lights when you leave.', '是的，离开时关灯。'],
            ['Small actions make a big difference!', '小小的行动能带来大改变！'],
        ],
    },
    {
        'title': 'Future Plans',
        'en': 'Tom: Tom, what do you want to be when you grow up?\nLucy: I want to be a computer programmer. I love coding and solving problems with technology.\nTom: That is a popular career these days. Have you been learning programming?\nLucy: Yes, I have been teaching myself Python for about a year. I also joined the coding club at school.\nTom: That sounds very serious. What kind of programs do you want to create?\nLucy: I want to develop apps that help people learn languages. I think technology can make education more accessible.\nTom: That is a meaningful goal! Do you plan to go to university?\nLucy: Yes, I want to study computer science at a good university. Maybe Tsinghua or Peking University.\nTom: Those are great schools. They have excellent computer science programs.\nLucy: I know. I need to work very hard to get in. What about you? What are your future plans?\nTom: I want to become a veterinarian. I love animals and I want to help them.\nLucy: That is wonderful! Where do you plan to study?\nTom: I want to study at an agricultural university. They have good veterinary programs.\nLucy: I am sure you will do great. We both have clear goals now.\nTom: Yes! We should study hard and never give up on our dreams.\nLucy: Absolutely. Let us support each other and work hard together!\nTom: Deal! Good luck to both of us!\nLucy: Good luck!',
        'zh': 'Tom: 汤姆，你长大后想做什么？\nLucy: 我想当一名程序员。我喜欢编程，喜欢用技术解决问题。\nTom: 这是最近很热门的职业。你一直在学编程吗？\nLucy: 是的，我自学Python大概一年了。我还参加了学校的编程社团。\nTom: 听起来很认真啊。你想开发什么样的程序？\nLucy: 我想开发帮助人们学习语言的应用程序。我觉得科技可以让教育更加普及。\nTom: 这是很有意义的目标！你打算上大学吗？\nLucy: 是的，我想上一所好大学的计算机专业。可能是清华或北大。\nTom: 那些都是很好的学校，计算机专业很棒。\nLucy: 我知道。我需要非常努力才能考进去。你呢？你有什么未来计划？\nTom: 我想当一名兽医。我喜欢动物，我想帮助它们。\nLucy: 太棒了！你打算在哪里学习？\nTom: 我想上一所农业大学，那里有很好的兽医专业。\nLucy: 我相信你一定能做到。我们现在都有明确的目标了。\nTom: 是的！我们应该努力学习，永不放弃梦想。\nLucy: 没错！让我们互相支持，一起努力！\nTom: 一言为定！祝我们两个都好运！\nLucy: 好运！',
        'dialogue': [
            ['What do you want to be in the future?', '你将来想做什么？'],
            ['I want to be a doctor.', '我想成为一名医生。'],
            ["That's amazing! Why do you want that?", '太棒了！为什么想当医生？'],
            ['I want to help sick people.', '我想帮助生病的人。'],
            ['Do you need to study medicine?', '你需要学医吗？'],
            ['Yes, it takes many years of study.', '是的，需要学习很多年。'],
            ['Where do you want to work?', '你想在哪里工作？'],
            ['Maybe in a hospital in Beijing.', '也许在北京的一家医院。'],
            ['What about your friend Li Ming?', '你的朋友李明呢？'],
            ['He wants to be a computer programmer.', '他想成为计算机程序员。'],
            ["That's a growing field.", '那是一个不断发展的领域。'],
            ['Yes, technology is the future.', '是的，科技就是未来。'],
            ["Do you think you'll achieve your dream?", '你认为你会实现梦想吗？'],
            ["I hope so! I'll work hard.", '希望如此！我会努力的。'],
            ["I'm sure you will. Good luck!", '我相信你会的，祝你好运！'],
        ],
    },
    {
        'title': 'Shopping in the Supermarket 超市购物',
        'en': 'Tom: Can I help you?\nLucy: Yes, I want to buy some vegetables.\nTom: What kind do you like?\nLucy: I like tomatoes and potatoes.\nTom: Here you are.\nLucy: How much are they?\nTom: Thirty yuan in total.\nLucy: Here is the money.\nTom: Thank you. Have a nice day!\nLucy: You too!',
        'zh': 'Tom: 需要帮忙吗？\nLucy: 是的，我想买一些蔬菜。\nTom: 你喜欢哪种？\nLucy: 我喜欢西红柿和土豆。\nTom: 给你。\nLucy: 多少钱？\nTom: 一共30元。\nLucy: 给你钱。\nTom: 谢谢。祝你愉快！\nLucy: 你也是！',
        'dialogue': [
            ['Can I help you?', '需要帮忙吗？'],
            ['Yes, I want to buy some vegetables.', '是的，我想买一些蔬菜。'],
            ['What kind do you like?', '你喜欢哪种？'],
            ['I like tomatoes and potatoes.', '我喜欢西红柿和土豆。'],
            ['Here you are.', '给你。'],
            ['How much are they?', '多少钱？'],
            ['Thirty yuan in total.', '一共30元。'],
            ['Here is the money.', '给你钱。'],
            ['Thank you. Have a nice day!', '谢谢。祝你愉快！'],
            ['You too!', '你也是！'],
        ],
    },
    {
        'title': 'At the Railway Station 火车站',
        'en': 'Tom: Excuse me, where is the ticket office?\nLucy: It is over there, near the entrance.\nTom: Thank you. By the way, when does the train leave?\nLucy: At 3:30 p.m.\nTom: Which platform is it?\nLucy: Platform 5.\nTom: Thank you very much.\nLucy: You are welcome. Have a good trip!\nTom: Thanks!',
        'zh': 'Tom: 打扰一下，售票处在哪里？\nLucy: 在那边，入口附近。\nTom: 谢谢。顺便问一下，火车什么时候开？\nLucy: 下午3:30。\nTom: 几号站台？\nLucy: 5号站台。\nTom: 非常感谢。\nLucy: 不客气。旅途愉快！\nTom: 谢谢！',
        'dialogue': [
            ['Excuse me, where is the ticket office?', '打扰一下，售票处在哪里？'],
            ['It is over there, near the entrance.', '在那边，入口附近。'],
            ['Thank you. By the way, when does the train leave?', '谢谢。顺便问一下，火车什么时候开？'],
            ['At 3:30 p.m.', '下午3:30。'],
            ['Which platform is it?', '几号站台？'],
            ['Platform 5.', '5号站台。'],
            ['Thank you very much.', '非常感谢。'],
            ['You are welcome. Have a good trip!', '不客气。旅途愉快！'],
            ['Thanks!', '谢谢！'],
        ],
    },
    {
        'title': 'Seeing the Doctor 看医生',
        'en': 'Tom: What is wrong with you?\nLucy: I have a fever and a headache.\nTom: How long have you been like this?\nLucy: Since yesterday evening.\nTom: Let me check your temperature.\nLucy: Is it serious?\nTom: No, just a cold. Take this medicine and drink more water.\nLucy: Thank you, doctor.\nTom: Have a good rest.',
        'zh': 'Tom: 你怎么了？\nLucy: 我发烧并且头痛。\nTom: 这样多久了？\nLucy: 从昨天晚上开始的。\nTom: 让我量一下体温。\nLucy: 严重吗？\nTom: 不严重，只是感冒。吃这个药，多喝热水。\nLucy: 谢谢你，医生。\nTom: 好好休息。',
        'dialogue': [
            ['What is wrong with you?', '你怎么了？'],
            ['I have a fever and a headache.', '我发烧并且头痛。'],
            ['How long have you been like this?', '这样多久了？'],
            ['Since yesterday evening.', '从昨天晚上开始的。'],
            ['Let me check your temperature.', '让我量一下体温。'],
            ['Is it serious?', '严重吗？'],
            ['No, just a cold. Take this medicine and drink more water.', '不严重，只是感冒。吃这个药，多喝热水。'],
            ['Thank you, doctor.', '谢谢你，医生。'],
            ['Have a good rest.', '好好休息。'],
        ],
    },
    {
        'title': 'Weather Report 天气预报',
        'en': 'Tom: What is the weather like today?\nLucy: It is sunny and warm.\nTom: What about tomorrow?\nLucy: It will be cloudy and cool.\nTom: Will it rain?\nLucy: I think so. You should take an umbrella.\nTom: Good idea. I hope it will not rain heavily.\nLucy: The weather report says it will be light rain.\nTom: That is great!',
        'zh': 'Tom: 今天天气怎么样？\nLucy: 晴朗且温暖。\nTom: 明天呢？\nLucy: 多云且凉爽。\nTom: 会下雨吗？\nLucy: 我想会的。你应该带把伞。\nTom: 好主意。希望不要下大雨。\nLucy: 天气预报说是小雨。\nTom: 太好了！',
        'dialogue': [
            ['What is the weather like today?', '今天天气怎么样？'],
            ['It is sunny and warm.', '晴朗且温暖。'],
            ['What about tomorrow?', '明天呢？'],
            ['It will be cloudy and cool.', '多云且凉爽。'],
            ['Will it rain?', '会下雨吗？'],
            ['I think so. You should take an umbrella.', '我想会的。你应该带把伞。'],
            ['Good idea. I hope it will not rain heavily.', '好主意。希望不要下大雨。'],
            ['The weather report says it will be light rain.', '天气预报说是小雨。'],
            ['That is great!', '太好了！'],
        ],
    },
    {
        'title': 'Part-time Job Interview 兼职面试',
        'en': 'Tom: Why do you want this job?\nLucy: I want to gain some work experience.\nTom: Have you worked before?\nLucy: No, but I am a quick learner.\nTom: What is your schedule like?\nLucy: I am free on weekends and after school.\nTom: How old are you?\nLucy: I am 16 years old.\nTom: OK. We will call you next week.\nLucy: Thank you very much.',
        'zh': 'Tom: 你为什么想要这份工作？\nLucy: 我想获得一些工作经验。\nTom: 你以前工作过吗？\nLucy: 没有，但我学东西很快。\nTom: 你的时间安排怎么样？\nLucy: 周末和放学后有空。\nTom: 你多大了？\nLucy: 我16岁。\nTom: 好的。我们下周会打电话给你。\nLucy: 非常感谢。',
        'dialogue': [
            ['Why do you want this job?', '你为什么想要这份工作？'],
            ['I want to gain some work experience.', '我想获得一些工作经验。'],
            ['Have you worked before?', '你以前工作过吗？'],
            ['No, but I am a quick learner.', '没有，但我学东西很快。'],
            ['What is your schedule like?', '你的时间安排怎么样？'],
            ['I am free on weekends and after school.', '周末和放学后有空。'],
            ['How old are you?', '你多大了？'],
            ['I am 16 years old.', '我16岁。'],
            ['OK. We will call you next week.', '好的。我们下周会打电话给你。'],
            ['Thank you very much.', '非常感谢。'],
        ],
    },
    {
        'title': 'Sports Meeting 运动会',
        'en': 'Tom: Did you take part in the sports meeting?\nLucy: Yes, I took part in the 100-meter race.\nTom: Did you win?\nLucy: No, I came in third.\nTom: That is still very good!\nLucy: Thank you. What about you?\nTom: I took part in the long jump.\nLucy: Did you win a prize?\nTom: Yes, I won first prize!\nLucy: Congratulations!',
        'zh': 'Tom: 你参加运动会了吗？\nLucy: 是的，我参加了100米赛跑。\nTom: 你赢了吗？\nLucy: 没有，我得了第三名。\nTom: 那也已经很好了！\nLucy: 谢谢。你呢？\nTom: 我参加了跳远。\nLucy: 你得奖了吗？\nTom: 是的，我得了一等奖！\nLucy: 恭喜！',
        'dialogue': [
            ['Did you take part in the sports meeting?', '你参加运动会了吗？'],
            ['Yes, I took part in the 100-meter race.', '是的，我参加了100米赛跑。'],
            ['Did you win?', '你赢了吗？'],
            ['No, I came in third.', '没有，我得了第三名。'],
            ['That is still very good!', '那也已经很好了！'],
            ['Thank you. What about you?', '谢谢。你呢？'],
            ['I took part in the long jump.', '我参加了跳远。'],
            ['Did you win a prize?', '你得奖了吗？'],
            ['Yes, I won first prize!', '是的，我得了一等奖！'],
            ['Congratulations!', '恭喜！'],
        ],
    },
    {
        'title': 'Library Rules 图书馆规则',
        'en': 'Tom: Can I borrow these books?\nLucy: Yes, but you must return them in two weeks.\nTom: Can I renew them?\nLucy: Yes, you can renew them online.\nTom: Is there a fine for late returns?\nLucy: Yes, one yuan per day.\nTom: I see. Can I take photos here?\nLucy: No, photos are not allowed.\nTom: OK, I will obey the rules.\nLucy: Thank you for your cooperation.',
        'zh': 'Tom: 我可以借这些书吗？\nLucy: 可以，但你必须在两周内归还。\nTom: 我可以续借吗？\nLucy: 可以，你可以在网上续借。\nTom: 晚还书有罚款吗？\nLucy: 有，每天一元。\nTom: 我明白了。我可以在这里拍照吗？\nLucy: 不可以，不允许拍照。\nTom: 好的，我会遵守规定。\nLucy: 谢谢你的配合。',
        'dialogue': [
            ['Can I borrow these books?', '我可以借这些书吗？'],
            ['Yes, but you must return them in two weeks.', '可以，但你必须在两周内归还。'],
            ['Can I renew them?', '我可以续借吗？'],
            ['Yes, you can renew them online.', '可以，你可以在网上续借。'],
            ['Is there a fine for late returns?', '晚还书有罚款吗？'],
            ['Yes, one yuan per day.', '有，每天一元。'],
            ['I see. Can I take photos here?', '我明白了。我可以在这里拍照吗？'],
            ['No, photos are not allowed.', '不可以，不允许拍照。'],
            ['OK, I will obey the rules.', '好的，我会遵守规定。'],
            ['Thank you for your cooperation.', '谢谢你的配合。'],
        ],
    },
    {
        'title': 'Festival Celebration 节日庆祝',
        'en': 'Tom: What is your favorite festival?\nLucy: My favorite festival is the Spring Festival.\nTom: Why do you like it?\nLucy: Because I can get red packets and eat delicious food.\nTom: What do you usually do?\nLucy: We have a big family dinner and watch TV together.\nTom: That sounds wonderful!\nLucy: Welcome to my home this Spring Festival!\nTom: Thank you! I would love to.',
        'zh': 'Tom: 你最喜欢什么节日？\nLucy: 我最喜欢春节。\nTom: 你为什么喜欢它？\nLucy: 因为我可以收到红包，还能吃到美味的食物。\nTom: 你们通常做什么？\nLucy: 我们吃一顿丰盛的家庭晚餐，一起看电视。\nTom: 听起来太棒了！\nLucy: 今年春节欢迎来我家！\nTom: 谢谢！我很乐意。',
        'dialogue': [
            ['What is your favorite festival?', '你最喜欢什么节日？'],
            ['My favorite festival is the Spring Festival.', '我最喜欢春节。'],
            ['Why do you like it?', '你为什么喜欢它？'],
            ['Because I can get red packets and eat delicious food.', '因为我可以收到红包，还能吃到美味的食物。'],
            ['What do you usually do?', '你们通常做什么？'],
            ['We have a big family dinner and watch TV together.', '我们吃一顿丰盛的家庭晚餐，一起看电视。'],
            ['That sounds wonderful!', '听起来太棒了！'],
            ['Welcome to my home this Spring Festival!', '今年春节欢迎来我家！'],
            ['Thank you! I would love to.', '谢谢！我很乐意。'],
        ],
    },
    {
        'title': 'Internet Safety 网络安全',
        'en': 'Tom: Do you often go online?\nLucy: Yes, I use the Internet every day.\nTom: What do you usually do online?\nLucy: I chat with friends and search for information.\nTom: Do you know about internet safety?\nLucy: Not really. What should I pay attention to?\nTom: Do not give out personal information.\nLucy: I see. Anything else?\nTom: Do not meet online friends alone.\nLucy: Thank you for telling me.',
        'zh': 'Tom: 你经常上网吗？\nLucy: 是的，我每天都上网。\nTom: 你通常在上网做什么？\nLucy: 我和朋友聊天，搜索信息。\nTom: 你知道网络安全吗？\nLucy: 不太清楚。我应该注意什么？\nTom: 不要泄露个人信息。\nLucy: 我明白了。还有其他的吗？\nTom: 不要单独见网友。\nLucy: 谢谢你告诉我。',
        'dialogue': [
            ['Do you often go online?', '你经常上网吗？'],
            ['Yes, I use the Internet every day.', '是的，我每天都上网。'],
            ['What do you usually do online?', '你通常在上网做什么？'],
            ['I chat with friends and search for information.', '我和朋友聊天，搜索信息。'],
            ['Do you know about internet safety?', '你知道网络安全吗？'],
            ['Not really. What should I pay attention to?', '不太清楚。我应该注意什么？'],
            ['Do not give out personal information.', '不要泄露个人信息。'],
            ['I see. Anything else?', '我明白了。还有其他的吗？'],
            ['Do not meet online friends alone.', '不要单独见网友。'],
            ['Thank you for telling me.', '谢谢你告诉我。'],
        ],
    },
    {
        'title': 'Volunteer Work 志愿者工作',
        'en': 'Tom: What did you do last weekend?\nLucy: I did volunteer work at the old peoples home.\nTom: What did you do there?\nLucy: I cleaned the rooms and talked with the old people.\nTom: That is so nice of you!\nLucy: Thank you. It made me very happy.\nTom: I want to join you next time.\nLucy: Great! We go there every month.\nTom: I will contact you then.',
        'zh': 'Tom: 上周末你做了什么？\nLucy: 我在养老院做了志愿者工作。\nTom: 你在那里做了什么？\nLucy: 我打扫房间，和老人们聊天。\nTom: 你真是太好了！\nLucy: 谢谢。这让我非常开心。\nTom: 下次我想加入你们。\nLucy: 太好了！我们每个月都去。\nTom: 到时候我会联系你。',
        'dialogue': [
            ['What did you do last weekend?', '上周末你做了什么？'],
            ['I did volunteer work at the old peoples home.', '我在养老院做了志愿者工作。'],
            ['What did you do there?', '你在那里做了什么？'],
            ['I cleaned the rooms and talked with the old people.', '我打扫房间，和老人们聊天。'],
            ['That is so nice of you!', '你真是太好了！'],
            ['Thank you. It made me very happy.', '谢谢。这让我非常开心。'],
            ['I want to join you next time.', '下次我想加入你们。'],
            ['Great! We go there every month.', '太好了！我们每个月都去。'],
            ['I will contact you then.', '到时候我会联系你。'],
        ],
    },
    {
        'title': 'Shopping in the Supermarket',
        'en': 'Tom: Can I help you?\nLucy: Yes, I want to buy some vegetables.\nTom: What kind do you like?\nLucy: I like tomatoes and potatoes.\nTom: Here you are.\nLucy: How much are they?\nTom: Thirty yuan in total.\nLucy: Here is the money.\nTom: Thank you. Have a nice day!\nLucy: You too!',
        'zh': 'Tom: 需要帮忙吗？\nLucy: 是的，我想买一些蔬菜。\nTom: 你喜欢哪种？\nLucy: 我喜欢西红柿和土豆。\nTom: 给你。\nLucy: 多少钱？\nTom: 一共30元。\nLucy: 给你钱。\nTom: 谢谢。祝你愉快！\nLucy: 你也是！',
        'dialogue': [
            ['Can I help you?', '需要帮忙吗？'],
            ['Yes, I want to buy some vegetables.', '是的，我想买一些蔬菜。'],
            ['What kind do you like?', '你喜欢哪种？'],
            ['I like tomatoes and potatoes.', '我喜欢西红柿和土豆。'],
            ['Here you are.', '给你。'],
            ['How much are they?', '多少钱？'],
            ['Thirty yuan in total.', '一共30元。'],
            ['Here is the money.', '给你钱。'],
            ['Thank you. Have a nice day!', '谢谢。祝你愉快！'],
            ['You too!', '你也是！'],
        ],
    },
    {
        'title': 'At the Railway Station',
        'en': 'Tom: Excuse me, where is the ticket office?\nLucy: It is over there, near the entrance.\nTom: Thank you. By the way, when does the train leave?\nLucy: At 3:30 p.m.\nTom: Which platform is it?\nLucy: Platform 5.\nTom: Thank you very much.\nLucy: You are welcome. Have a good trip!\nTom: Thanks!',
        'zh': 'Tom: 打扰一下，售票处在哪里？\nLucy: 在那边，入口附近。\nTom: 谢谢。顺便问一下，火车什么时候开？\nLucy: 下午3:30。\nTom: 几号站台？\nLucy: 5号站台。\nTom: 非常感谢。\nLucy: 不客气。旅途愉快！\nTom: 谢谢！',
        'dialogue': [
            ['Excuse me, where is the ticket office?', '打扰一下，售票处在哪里？'],
            ['It is over there, near the entrance.', '在那边，入口附近。'],
            ['Thank you. By the way, when does the train leave?', '谢谢。顺便问一下，火车什么时候开？'],
            ['At 3:30 p.m.', '下午3:30。'],
            ['Which platform is it?', '几号站台？'],
            ['Platform 5.', '5号站台。'],
            ['Thank you very much.', '非常感谢。'],
            ['You are welcome. Have a good trip!', '不客气。旅途愉快！'],
            ['Thanks!', '谢谢！'],
        ],
    },
    {
        'title': 'Seeing the Doctor',
        'en': 'Tom: What is wrong with you?\nLucy: I have a fever and a headache.\nTom: How long have you been like this?\nLucy: Since yesterday evening.\nTom: Let me check your temperature.\nLucy: Is it serious?\nTom: No, just a cold. Take this medicine and drink more water.\nLucy: Thank you, doctor.\nTom: Have a good rest.',
        'zh': 'Tom: 你怎么了？\nLucy: 我发烧并且头痛。\nTom: 这样多久了？\nLucy: 从昨天晚上开始的。\nTom: 让我量一下体温。\nLucy: 严重吗？\nTom: 不严重，只是感冒。吃这个药，多喝热水。\nLucy: 谢谢你，医生。\nTom: 好好休息。',
        'dialogue': [
            ['What is wrong with you?', '你怎么了？'],
            ['I have a fever and a headache.', '我发烧并且头痛。'],
            ['How long have you been like this?', '这样多久了？'],
            ['Since yesterday evening.', '从昨天晚上开始的。'],
            ['Let me check your temperature.', '让我量一下体温。'],
            ['Is it serious?', '严重吗？'],
            ['No, just a cold. Take this medicine and drink more water.', '不严重，只是感冒。吃这个药，多喝热水。'],
            ['Thank you, doctor.', '谢谢你，医生。'],
            ['Have a good rest.', '好好休息。'],
        ],
    },
    {
        'title': 'Weather Report Chat',
        'en': 'Tom: What is the weather like today?\nLucy: It is sunny and warm.\nTom: What about tomorrow?\nLucy: It will be cloudy and cool.\nTom: Will it rain?\nLucy: I think so. You should take an umbrella.\nTom: Good idea. I hope it will not rain heavily.\nLucy: The weather report says it will be light rain.\nTom: That is great!',
        'zh': 'Tom: 今天天气怎么样？\nLucy: 晴朗且温暖。\nTom: 明天呢？\nLucy: 多云且凉爽。\nTom: 会下雨吗？\nLucy: 我想会的。你应该带把伞。\nTom: 好主意。希望不要下大雨。\nLucy: 天气预报说是小雨。\nTom: 太好了！',
        'dialogue': [
            ['What is the weather like today?', '今天天气怎么样？'],
            ['It is sunny and warm.', '晴朗且温暖。'],
            ['What about tomorrow?', '明天呢？'],
            ['It will be cloudy and cool.', '多云且凉爽。'],
            ['Will it rain?', '会下雨吗？'],
            ['I think so. You should take an umbrella.', '我想会的。你应该带把伞。'],
            ['Good idea. I hope it will not rain heavily.', '好主意。希望不要下大雨。'],
            ['The weather report says it will be light rain.', '天气预报说是小雨。'],
            ['That is great!', '太好了！'],
        ],
    },
    {
        'title': 'Part-time Job Interview',
        'en': 'Tom: Why do you want this job?\nLucy: I want to gain some work experience.\nTom: Have you worked before?\nLucy: No, but I am a quick learner.\nTom: What is your schedule like?\nLucy: I am free on weekends and after school.\nTom: How old are you?\nLucy: I am 16 years old.\nTom: OK. We will call you next week.\nLucy: Thank you very much.',
        'zh': 'Tom: 你为什么想要这份工作？\nLucy: 我想获得一些工作经验。\nTom: 你以前工作过吗？\nLucy: 没有，但我学东西很快。\nTom: 你的时间安排怎么样？\nLucy: 周末和放学后有空。\nTom: 你多大了？\nLucy: 我16岁。\nTom: 好的。我们下周会打电话给你。\nLucy: 非常感谢。',
        'dialogue': [
            ['Why do you want this job?', '你为什么想要这份工作？'],
            ['I want to gain some work experience.', '我想获得一些工作经验。'],
            ['Have you worked before?', '你以前工作过吗？'],
            ['No, but I am a quick learner.', '没有，但我学东西很快。'],
            ['What is your schedule like?', '你的时间安排怎么样？'],
            ['I am free on weekends and after school.', '周末和放学后有空。'],
            ['How old are you?', '你多大了？'],
            ['I am 16 years old.', '我16岁。'],
            ['OK. We will call you next week.', '好的。我们下周会打电话给你。'],
            ['Thank you very much.', '非常感谢。'],
        ],
    },
    {
        'title': 'Sports Meeting',
        'en': 'Tom: Did you take part in the sports meeting?\nLucy: Yes, I took part in the 100-meter race.\nTom: Did you win?\nLucy: No, I came in third.\nTom: That is still very good!\nLucy: Thank you. What about you?\nTom: I took part in the long jump.\nLucy: Did you win a prize?\nTom: Yes, I won first prize!\nLucy: Congratulations!',
        'zh': 'Tom: 你参加运动会了吗？\nLucy: 是的，我参加了100米赛跑。\nTom: 你赢了吗？\nLucy: 没有，我得了第三名。\nTom: 那也已经很好了！\nLucy: 谢谢。你呢？\nTom: 我参加了跳远。\nLucy: 你得奖了吗？\nTom: 是的，我得了一等奖！\nLucy: 恭喜！',
        'dialogue': [
            ['Did you take part in the sports meeting?', '你参加运动会了吗？'],
            ['Yes, I took part in the 100-meter race.', '是的，我参加了100米赛跑。'],
            ['Did you win?', '你赢了吗？'],
            ['No, I came in third.', '没有，我得了第三名。'],
            ['That is still very good!', '那也已经很好了！'],
            ['Thank you. What about you?', '谢谢。你呢？'],
            ['I took part in the long jump.', '我参加了跳远。'],
            ['Did you win a prize?', '你得奖了吗？'],
            ['Yes, I won first prize!', '是的，我得了一等奖！'],
            ['Congratulations!', '恭喜！'],
        ],
    },
    {
        'title': 'Library Rules',
        'en': 'Tom: Can I borrow these books?\nLucy: Yes, but you must return them in two weeks.\nTom: Can I renew them?\nLucy: Yes, you can renew them online.\nTom: Is there a fine for late returns?\nLucy: Yes, one yuan per day.\nTom: I see. Can I take photos here?\nLucy: No, photos are not allowed.\nTom: OK, I will obey the rules.\nLucy: Thank you for your cooperation.',
        'zh': 'Tom: 我可以借这些书吗？\nLucy: 可以，但你必须在两周内归还。\nTom: 我可以续借吗？\nLucy: 可以，你可以在网上续借。\nTom: 晚还书有罚款吗？\nLucy: 有，每天一元。\nTom: 我明白了。我可以在这里拍照吗？\nLucy: 不可以，不允许拍照。\nTom: 好的，我会遵守规定。\nLucy: 谢谢你的配合。',
        'dialogue': [
            ['Can I borrow these books?', '我可以借这些书吗？'],
            ['Yes, but you must return them in two weeks.', '可以，但你必须在两周内归还。'],
            ['Can I renew them?', '我可以续借吗？'],
            ['Yes, you can renew them online.', '可以，你可以在网上续借。'],
            ['Is there a fine for late returns?', '晚还书有罚款吗？'],
            ['Yes, one yuan per day.', '有，每天一元。'],
            ['I see. Can I take photos here?', '我明白了。我可以在这里拍照吗？'],
            ['No, photos are not allowed.', '不可以，不允许拍照。'],
            ['OK, I will obey the rules.', '好的，我会遵守规定。'],
            ['Thank you for your cooperation.', '谢谢你的配合。'],
        ],
    },
    {
        'title': 'Festival Celebration',
        'en': 'Tom: What is your favorite festival?\nLucy: My favorite festival is the Spring Festival.\nTom: Why do you like it?\nLucy: Because I can get red packets and eat delicious food.\nTom: What do you usually do?\nLucy: We have a big family dinner and watch TV together.\nTom: That sounds wonderful!\nLucy: Welcome to my home this Spring Festival!\nTom: Thank you! I would love to.',
        'zh': 'Tom: 你最喜欢什么节日？\nLucy: 我最喜欢春节。\nTom: 你为什么喜欢它？\nLucy: 因为我可以收到红包，还能吃到美味的食物。\nTom: 你们通常做什么？\nLucy: 我们吃一顿丰盛的家庭晚餐，一起看电视。\nTom: 听起来太棒了！\nLucy: 今年春节欢迎来我家！\nTom: 谢谢！我很乐意。',
        'dialogue': [
            ['What is your favorite festival?', '你最喜欢什么节日？'],
            ['My favorite festival is the Spring Festival.', '我最喜欢春节。'],
            ['Why do you like it?', '你为什么喜欢它？'],
            ['Because I can get red packets and eat delicious food.', '因为我可以收到红包，还能吃到美味的食物。'],
            ['What do you usually do?', '你们通常做什么？'],
            ['We have a big family dinner and watch TV together.', '我们吃一顿丰盛的家庭晚餐，一起看电视。'],
            ['That sounds wonderful!', '听起来太棒了！'],
            ['Welcome to my home this Spring Festival!', '今年春节欢迎来我家！'],
            ['Thank you! I would love to.', '谢谢！我很乐意。'],
        ],
    },
    {
        'title': 'Internet Safety',
        'en': 'Tom: Do you often go online?\nLucy: Yes, I use the Internet every day.\nTom: What do you usually do online?\nLucy: I chat with friends and search for information.\nTom: Do you know about internet safety?\nLucy: Not really. What should I pay attention to?\nTom: Do not give out personal information.\nLucy: I see. Anything else?\nTom: Do not meet online friends alone.\nLucy: Thank you for telling me.',
        'zh': 'Tom: 你经常上网吗？\nLucy: 是的，我每天都上网。\nTom: 你通常在上网做什么？\nLucy: 我和朋友聊天，搜索信息。\nTom: 你知道网络安全吗？\nLucy: 不太清楚。我应该注意什么？\nTom: 不要泄露个人信息。\nLucy: 我明白了。还有其他的吗？\nTom: 不要单独见网友。\nLucy: 谢谢你告诉我。',
        'dialogue': [
            ['Do you often go online?', '你经常上网吗？'],
            ['Yes, I use the Internet every day.', '是的，我每天都上网。'],
            ['What do you usually do online?', '你通常在上网做什么？'],
            ['I chat with friends and search for information.', '我和朋友聊天，搜索信息。'],
            ['Do you know about internet safety?', '你知道网络安全吗？'],
            ['Not really. What should I pay attention to?', '不太清楚。我应该注意什么？'],
            ['Do not give out personal information.', '不要泄露个人信息。'],
            ['I see. Anything else?', '我明白了。还有其他的吗？'],
            ['Do not meet online friends alone.', '不要单独见网友。'],
            ['Thank you for telling me.', '谢谢你告诉我。'],
        ],
    },
    {
        'title': 'Volunteer Work',
        'en': 'Tom: What did you do last weekend?\nLucy: I did volunteer work at the old peoples home.\nTom: What did you do there?\nLucy: I cleaned the rooms and talked with the old people.\nTom: That is so nice of you!\nLucy: Thank you. It made me very happy.\nTom: I want to join you next time.\nLucy: Great! We go there every month.\nTom: I will contact you then.',
        'zh': 'Tom: 上周末你做了什么？\nLucy: 我在养老院做了志愿者工作。\nTom: 你在那里做了什么？\nLucy: 我打扫房间，和老人们聊天。\nTom: 你真是太好了！\nLucy: 谢谢。这让我非常开心。\nTom: 下次我想加入你们。\nLucy: 太好了！我们每个月都去。\nTom: 到时候我会联系你。',
        'dialogue': [
            ['What did you do last weekend?', '上周末你做了什么？'],
            ['I did volunteer work at the old peoples home.', '我在养老院做了志愿者工作。'],
            ['What did you do there?', '你在那里做了什么？'],
            ['I cleaned the rooms and talked with the old people.', '我打扫房间，和老人们聊天。'],
            ['That is so nice of you!', '你真是太好了！'],
            ['Thank you. It made me very happy.', '谢谢。这让我非常开心。'],
            ['I want to join you next time.', '下次我想加入你们。'],
            ['Great! We go there every month.', '太好了！我们每个月都去。'],
            ['I will contact you then.', '到时候我会联系你。'],
        ],
    },
]
BUILTIN_GRAMMAR_EXERCISES = {
    "七年级": [  # 七年级
        {
            "title": "一般现在时",
            "grade": 7,
            "questions": [
                {"q": "We ___ (not watch) TV in the morning.", "a": "don't watch"},
                {"q": "He ___ (not like) coffee.", "a": "doesn't like"},
                {"q": "___ you ___ (go) to school every day衣", "a": "Do, go"},
                {"q": "___ he ___ (speak) English衣", "a": "Does, speak"},
                {"q": "My mother ___ (cook) dinner every evening.", "a": "cooks"},
                {"q": "They ___ (not live) in Beijing.", "a": "don't live"},
                {"q": "The sun ___ (rise) in the east.", "a": "rises"},
                {"q": "She ___ (wash) her hair every other day.", "a": "washes"},
                {"q": "I ___ (not eat) enough fruit.", "a": "don't eat"},
                {"q": "He always ___ (walk) to work.", "a": "walks"},
                {"q": "We ___ (study) English at school.", "a": "study"},
                {"q": "The shop ___ (open) at 9 am.", "a": "opens"},
                {"q": "She ___ (not like) horror movies.", "a": "doesn't like"},
                {"q": "___ they ___ (play) tennis on weekends衣", "a": "Do, play"},
                {"q": "It ___ (snow) a lot in winter here.", "a": "snows"},
                # 涓鑸法幇鍦目椂琛厖棰樼洰 (30閬衣
                {"q": "He always ___ (tell) the truth.", "a": "tells"},
                {"q": "My father ___ (work) in a bank.", "a": "works"},
                {"q": "She ___ (not like) playing tennis.", "a": "does not like"},
                {"q": "The sun ___ (rise) in the east.", "a": "rises"},
                {"q": "Water ___ (boil) at 100 degrees.", "a": "boils"},
                {"q": "___ she ___ (have) a sister衣", "a": "Does, have"},
                {"q": "The train ___ (leave) at 8 pm every day.", "a": "leaves"},
                {"q": "I ___ (not know) his phone number.", "a": "do not know"},
                {"q": "We ___ (enjoy) reading books.", "a": "enjoy"},
                {"q": "She ___ (teach) English at a school.", "a": "teaches"},
                {"q": "Birds ___ (fly) south in winter.", "a": "fly"},
                {"q": "He never ___ (eat) fast food.", "a": "eats"},
                {"q": "The store ___ (open) at 9 am daily.", "a": "opens"},
                {"q": "My mother ___ (not work) on Sundays.", "a": "does not work"},
                {"q": "Where ___ he ___ (live)衣", "a": "does, live"},
                {"q": "She ___ (finish) her homework every evening.", "a": "finishes"},
                {"q": "They ___ (have) lunch at 12 o'clock.", "a": "have"},
                {"q": "I ___ (believe) in myself.", "a": "believe"},
                {"q": "The earth ___ (go) around the sun.", "a": "goes"},
                {"q": "He ___ (not smoke) cigarettes.", "a": "does not smoke"},
                {"q": "My sister ___ (study) medicine at university.", "a": "studies"},
                {"q": "How ___ she ___ (feel) today衣", "a": "does, feel"},
                {"q": "The river ___ (flow) to the sea.", "a": "flows"},
                {"q": "We ___ (not watch) TV on weekdays.", "a": "do not watch"},
                {"q": "He ___ (drive) to work every day.", "a": "drives"},
                {"q": "She ___ (sing) beautifully.", "a": "sings"},
                {"q": "___ you ___ (play) the piano衣", "a": "Do, play"},
                {"q": "I usually ___ (go) to bed at 10 pm.", "a": "go"},
            ]
        },
        {
            "title": "棰戝害鍓判瘝",
            "questions": [
                {"q": "I ___ (鎬绘槸) get up at 6 am.", "a": "always"},
                {"q": "She ___ (閫氬父) goes to school by bus.", "a": "usually"},
                {"q": "They ___ (缁忓父) play football after school.", "a": "often"},
                {"q": "He ___ (鏈夋椂) watches TV in the evening.", "a": "sometimes"},
                {"q": "I ___ (寰堝皯) eat fast food.", "a": "seldom"},
                {"q": "She ___ (浠庝笉) eats meat.", "a": "never"},
                {"q": "We ___ (鎬绘槸) help each other.", "a": "always"},
                {"q": "He is ___ (鎬绘槸) late for school.", "a": "always"},
                {"q": "I ___ (閫氬父) do my homework at 8 pm.", "a": "usually"},
                {"q": "They ___ (缁忓父) go to the library.", "a": "often"},
                {"q": "She ___ (鏈夋椂) cooks dinner for us.", "a": "sometimes"},
                {"q": "I ___ (寰堝皯) go to the cinema.", "a": "seldom"},
                {"q": "He ___ (浠庝笉) smokes.", "a": "never"},
                {"q": "We are ___ (鎬绘槸) happy to see you.", "a": "always"},
                {"q": "My father ___ (閫氬父) reads newspapers after dinner.", "a": "usually"},
                # 棰戝害鍓判瘝琛厖棰樼洰 (35閬衣
                {"q": "I ___ (鎬绘槸) arrive on time.", "a": "always"},
                {"q": "She ___ (閫氬父) has coffee in the morning.", "a": "usually"},
                {"q": "We ___ (缁忓父) go hiking in the mountains.", "a": "often"},
                {"q": "He ___ (鏈夋椂) forgets his keys.", "a": "sometimes"},
                {"q": "They ___ (寰堝皯) eat at restaurants.", "a": "seldom"},
                {"q": "I ___ (浠庝笉) drink alcohol.", "a": "never"},
                {"q": "She is ___ (鎬绘槸) late for meetings.", "a": "always"},
                {"q": "He ___ (閫氬父) exercises in the morning.", "a": "usually"},
                {"q": "___ (鎬绘槸) tell the truth.", "a": "Always"},
                {"q": "I ___ (閫氬父) finish my work by 5 pm.", "a": "usually"},
                {"q": "She ___ (缁忓父) visits her grandparents.", "a": "often"},
                {"q": "He ___ (鏈夋椂) works on weekends.", "a": "sometimes"},
                {"q": "They ___ (寰堝皯) complain about anything.", "a": "seldom"},
                {"q": "I ___ (浠庝笉) smoke cigarettes.", "a": "never"},
                {"q": "We ___ (鎬绘槸) do our best.", "a": "always"},
                {"q": "She ___ (閫氬父) goes to bed early.", "a": "usually"},
                {"q": "He ___ (缁忓父) reads books before sleeping.", "a": "often"},
                {"q": "___ (鏈夋椂) I feel tired in the afternoon.", "a": "Sometimes"},
                {"q": "They ___ (寰堝皯) make mistakes.", "a": "seldom"},
                {"q": "I ___ (浠庝笉) give up easily.", "a": "never"},
                {"q": "She ___ (鎬绘槸) smiles at everyone.", "a": "always"},
                {"q": "He ___ (閫氬父) drives to work.", "a": "usually"},
                {"q": "We ___ (缁忓父) play basketball together.", "a": "often"},
                {"q": "She ___ (鏈夋椂) cooks dinner for us.", "a": "sometimes"},
                {"q": "They ___ (寰堝皯) go to the cinema.", "a": "seldom"},
                {"q": "I ___ (浠庝笉) argue with my parents.", "a": "never"},
                {"q": "He is ___ (鎬绘槸) happy.", "a": "always"},
                {"q": "She ___ (閫氬父) wakes up at 6 am.", "a": "usually"},
                {"q": "We ___ (缁忓父) have tests at school.", "a": "often"},
                {"q": "He ___ (鏈夋椂) forgets to do homework.", "a": "sometimes"},
                {"q": "They ___ (寰堝皯) travel abroad.", "a": "seldom"},
                {"q": "I ___ (浠庝笉) eat fast food.", "a": "never"},
                {"q": "___ (鎬绘槸) be honest.", "a": "Always"},
                {"q": "She ___ (閫氬父) listens to music.", "a": "usually"},
            ]
        },
        {
            "title": "浠嬭瘝",
            "questions": [
                {"q": "My birthday is ___ May 5th.", "a": "on"},
                {"q": "I get up ___ 7 o'clock.", "a": "at"},
                {"q": "The meeting is ___ Monday.", "a": "on"},
                {"q": "We have classes ___ the morning.", "a": "in"},
                {"q": "She was born ___ 2010.", "a": "in"},
                {"q": "The cat is ___ the table.", "a": "under"},
                {"q": "The book is ___ the desk.", "a": "on"},
                {"q": "He is sitting ___ me.", "a": "beside"},
                {"q": "Spring comes ___ winter.", "a": "after"},
                {"q": "She goes to school ___ bus.", "a": "by"},
                {"q": "I usually go to school ___ 7:30 ___ the morning.", "a": "at, in"},
                {"q": "There is a bridge ___ the river.", "a": "over"},
                {"q": "The cat is hiding ___ the door.", "a": "behind"},
                {"q": "I'll meet you ___ the school gate.", "a": "at"},
                {"q": "She is interested ___ music.", "a": "in"},
                {"q": "He is good ___ playing football.", "a": "at"},
                {"q": "The boy ___ blue is my brother.", "a": "in"},
                {"q": "I usually get up ___ 6:30 ___ weekdays.", "a": "at, on"},
                {"q": "There is a map ___ the wall.", "a": "on"},
                {"q": "I like reading ___ bed.", "a": "in"},
                # 浠嬭瘝琛厖棰樼洰 (30閬衣
                {"q": "My birthday is ___ June 1st.", "a": "on"},
                {"q": "We will meet ___ Sunday morning.", "a": "on"},
                {"q": "I was born ___ 2005.", "a": "in"},
                {"q": "He came here ___ the morning of July 3rd.", "a": "on"},
                {"q": "The letter arrived ___ the evening.", "a": "in"},
                {"q": "There is a bird ___ the tree.", "a": "in"},
                {"q": "The cat is sleeping ___ the bed.", "a": "under"},
                {"q": "She is standing ___ the door.", "a": "at"},
                {"q": "I will see you ___ the airport.", "a": "at"},
                {"q": "He is good ___ English.", "a": "at"},
                {"q": "I am interested ___ science.", "a": "in"},
                {"q": "We went to Beijing ___ train.", "a": "by"},
                {"q": "I came here ___ foot.", "a": "on"},
                {"q": "The picture is ___ the wall.", "a": "on"},
                {"q": "He is sitting ___ his sister.", "a": "beside"},
                {"q": "She arrived ___ 8 pm.", "a": "at"},
                {"q": "We have classes ___ weekdays.", "a": "on"},
                {"q": "Let's meet ___ the school gate.", "a": "at"},
                {"q": "The bridge is ___ the river.", "a": "over"},
                {"q": "The dog is running ___ the cat.", "a": "after"},
                {"q": "Spring comes ___ winter.", "a": "after"},
                {"q": "He sat ___ the two windows.", "a": "between"},
                {"q": "The hospital is ___ the school and the bank.", "a": "between"},
                {"q": "We sat ___ the back of the room.", "a": "in"},
                {"q": "I live ___ Beijing.", "a": "in"},
                {"q": "The book is ___ page 50.", "a": "on"},
                {"q": "I'll be back ___ an hour.", "a": "in"},
                {"q": "The movie starts ___ 7 o'clock.", "a": "at"},
                {"q": "She was born ___ a cold morning.", "a": "on"},
                {"q": "They arrived ___ night.", "a": "at"},
            ]
        },
        {
            "title": "鎯呮佸姩璇峜an/may/must",
            "questions": [
                {"q": "I ___ swim very well.", "a": "can"},
                {"q": "___ I come in衣 (词根眰璁稿彲)", "a": "May"},
                {"q": "You ___ finish your homework first. (必须)", "a": "must"},
                {"q": "She ___ speak English and Chinese.", "a": "can"},
                {"q": "___ you play the piano衣", "a": "Can"},
                {"q": "He ___ not come to the party tonight.", "a": "can"},
                {"q": "Students ___ obey the school rules. (必须)", "a": "must"},
                {"q": "___ I use your pen衣 (绀艰矊词根眰)", "a": "May"},
                {"q": "You ___ not smoke here. (绂佹考)", "a": "must"},
                {"q": "___ your brother ride a bike衣", "a": "Can"},
                {"q": "I'm sorry, I ___ (涓嶈兘) go with you.", "a": "cannot"},
                {"q": "You ___ be careful when crossing the road. (必须)", "a": "must"},
                {"q": "___ I go now衣 (可以测互鍚衣", "a": "May"},
                {"q": "We ___ see the stars at night.", "a": "can"},
                {"q": "You ___ not park here. (绂佹考)", "a": "must"},
                # 鎯呮佸姩璇峜an/may/must琛厖棰樼洰 (35閬衣
                {"q": "I ___ swim very well.", "a": "can"},
                {"q": "She ___ speak French.", "a": "can"},
                {"q": "___ I borrow your book衣", "a": "May"},
                {"q": "You ___ be 18 years old to enter.", "a": "must"},
                {"q": "He ___ not drive without a license.", "a": "can"},
                {"q": "___ I help you衣", "a": "May"},
                {"q": "You ___ follow the rules.", "a": "must"},
                {"q": "I ___ not tell a lie.", "a": "must"},
                {"q": "___ we go now衣", "a": "Can"},
                {"q": "The students ___ listen carefully.", "a": "must"},
                {"q": "I ___ see the stars at night.", "a": "can"},
                {"q": "___ your sister ride a bike衣", "a": "Can"},
                {"q": "You ___ not eat in class.", "a": "must"},
                {"q": "We ___ finish the work today.", "a": "must"},
                {"q": "He ___ come tomorrow if he has time.", "a": "may"},
                {"q": "___ I know your name衣", "a": "May"},
                {"q": "You ___ pay before you leave.", "a": "must"},
                {"q": "I ___ not solve this problem.", "a": "can"},
                {"q": "___ we go to the park衣", "a": "Can"},
                {"q": "She ___ be at home now.", "a": "may"},
                {"q": "You ___ keep quiet in the library.", "a": "must"},
                {"q": "I ___ not understand this question.", "a": "can"},
                {"q": "___ I sit here衣", "a": "May"},
                {"q": "You ___ not tell anyone.", "a": "must"},
                {"q": "He ___ speak three languages.", "a": "can"},
                {"q": "It ___ rain later.", "a": "may"},
                {"q": "We ___ go home now.", "a": "can"},
                {"q": "___ I use your phone衣", "a": "May"},
                {"q": "You ___ be on time for school.", "a": "must"},
                {"q": "I ___ not hear you clearly.", "a": "can"},
                {"q": "She ___ come if she wants.", "a": "may"},
                {"q": "They ___ not swim in the river.", "a": "must"},
                {"q": "___ we help you衣", "a": "Can"},
                {"q": "You ___ do your homework first.", "a": "must"},
                {"q": "I ___ not believe him.", "a": "can"},
            ]
        },
        {
            "title": "祈使句",
            "questions": [
                {"q": "___ (请坐), please.", "a": "Sit down"},
                {"q": "___ (打开) the door, please.", "a": "Open"},
                {"q": "___ (不要说话) in class.", "a": "Don't talk"},
                {"q": "___ (不要跑) in the hallway.", "a": "Don't run"},
                {"q": "___ (请安静), everyone.", "a": "Be quiet"},
                {"q": "___ (看) the blackboard.", "a": "Look at"},
                {"q": "___ (听) the teacher carefully.", "a": "Listen to"},
                {"q": "___ (不要迟到) for school.", "a": "Don't be late"},
                {"q": "___ (打开) your books, please.", "a": "Open"},
                {"q": "___ (关) the lights when you leave.", "a": "Turn off"},
                {"q": "___ (不要玩) with fire!", "a": "Don't play"},
                {"q": "___ (吃) your vegetables.", "a": "Eat"},
                {"q": "___ (写) your name on the paper.", "a": "Write"},
                {"q": "___ (起立), please.", "a": "Stand up"},
                {"q": "___ (不要忘记) to bring your homework.", "a": "Don't forget"},
                # 绁堜娇可以鍏呴理目录衣(35閬衣
                # 祈使句补充练习题(35道)
                {"q": "___ (保持安静), please.", "a": "Be quiet"},
                {"q": "___ (不要跑) in the hallway.", "a": "Don't run"},
                {"q": "___ (坐下), please.", "a": "Sit down"},
                {"q": "___ (关于笂) the door.", "a": "Close"},
                {"q": "___ (关上) the door.", "a": "Close"},
                {"q": "___ (不要说话) during the exam.", "a": "Don't talk"},
                {"q": "___ (看) at the blackboard.", "a": "Look"},
                {"q": "___ (不要迟到) for school.", "a": "Don't be late"},
                {"q": "___ (起立), everyone.", "a": "Stand up"},
                {"q": "___ (关) the lights when you leave.", "a": "Turn off"},
                {"q": "___ (不要玩) with fire.", "a": "Don't play"},
                {"q": "___ (喝) some water.", "a": "Drink"},
                {"q": "___ (写) your name on the paper.", "a": "Write"},
                {"q": "___ (不要担心), everything will be fine.", "a": "Don't worry"},
                {"q": "___ (等待) your turn.", "a": "Wait for"},
                {"q": "___ (不要) give up.", "a": "Don't"},
                {"q": "___ (努力学习) hard.", "a": "Work hard"},
                {"q": "___ (帮助) your mother at home.", "a": "Help"},
                {"q": "___ (不要) make noise.", "a": "Don't"},
                {"q": "___ (注意) your spelling.", "a": "Pay attention to"},
                {"q": "___ (照顾好自己).", "a": "Take care of yourself"},
                {"q": "___ (不要) be angry.", "a": "Don't"},
                {"q": "___ (早起) early every day.", "a": "Get up"},
                {"q": "___ (刷牙) twice a day.", "a": "Brush your teeth"},
                {"q": "___ (不要) touch the hot pot.", "a": "Don't"},
                {"q": "___ (跟我读) after me.", "a": "Read after me"},
                {"q": "___ (鎶婇煶涔愬叧灏忎竴点.", "a": "Turn down the music"},
                {"q": "___ (把声音) 关小一点.", "a": "Turn down the music"},
                {"q": "___ (把电视) 打开).", "a": "Turn on the TV"},
                {"q": "___ (不要) leave the room.", "a": "Don't"},
                {"q": "___ (鎺掗槦) for the bus.", "a": "Wait in line"},
                {"q": "___ (涓嶈论) waste food.", "a": "Don't"},
                {"q": "___ (淇濇寔鍋悍).", "a": "Stay healthy"},
            ]
        },
        {
            "title": "一般将来时 (will/be going to)",
            "grade": 7,
            "questions": [
                {"q": "I ___ (visit) my grandparents tomorrow.", "a": "will visit"},
                {"q": "She ___ (go) to Beijing next week.", "a": "is going to go"},
                {"q": "They ___ (play) football this afternoon.", "a": "will play"},
                {"q": "Look at the dark clouds! It ___ (rain).", "a": "is going to rain"},
                {"q": "We ___ (have) a meeting next Monday.", "a": "are going to have"},
                {"q": "___ you ___ (join) us tonight?", "a": "Will, join"},
                {"q": "She ___ (finish) the work in two hours.", "a": "will finish"},
                {"q": "I promise I ___ (not tell) anyone your secret.", "a": "will not tell"},
                {"q": "There ___ (be) a concert this Saturday evening.", "a": "will be"},
                {"q": "He ___ (be) 18 years old next month.", "a": "will be"},
                {"q": "My father ___ (buy) me a new bike for my birthday.", "a": "is going to buy"},
                {"q": "___ they ___ (come) to the party?", "a": "Are, going to come"},
                {"q": "I think robots ___ (do) more housework in the future.", "a": "will do"},
                {"q": "She ___ (start) her new job tomorrow morning.", "a": "is going to start"},
                {"q": "We ___ (travel) to Yunnan during the summer holiday.", "a": "will travel"},
                {"q": "___ you please open the window? (请求)", "a": "Will"},
                {"q": "I hope you ___ (have) a great time.", "a": "will have"},
                {"q": "Don't worry. I ___ (help) you with your homework.", "a": "will help"},
                {"q": "The train ___ (arrive) at 5 pm according to the schedule.", "a": "arrives"},
                {"q": "What ___ you ___ (do) when you grow up?", "a": "are, going to do"},
                {"q": "I ___ (send) you an email as soon as I get home.", "a": "will send"},
                {"q": "If it rains tomorrow, we ___ (cancel) the trip.", "a": "will cancel"},
                {"q": "I'm sure he ___ (like) this gift.", "a": "will like"},
                {"q": "They ___ (build) a new bridge across the river next year.", "a": "are going to build"},
                {"q": "The plane ___ (take) off in twenty minutes.", "a": "takes off"},
                {"q": "I ___ (not stay) here any longer.", "a": "am not going to stay"},
                {"q": "Maybe she ___ (change) her mind later.", "a": "will change"},
                {"q": "When ___ you ___ (pay) me back?", "a": "are, going to pay"},
                {"q": "I promise I ___ (be) on time from now on.", "a": "will be"},
                {"q": "Look! The bus ___ (come).", "a": "is coming"},
                {"q": "Next Friday, we ___ (hold) a sports meeting.", "a": "are going to hold"},
                {"q": "I ___ (call) you when I arrive in Shanghai.", "a": "will call"},
                {"q": "What time ___ the movie ___ (begin)?", "a": "does, begin"},
                {"q": "I hope everything ___ (be) fine soon.", "a": "will be"},
                {"q": "He ___ (turn) 20 next birthday.", "a": "will turn"},
                {"q": "We ___ (not have) any classes next week.", "a": "won't have"},
                {"q": "Who ___ (give) a speech at the meeting?", "a": "is going to give"},
                {"q": "No matter what happens, I ___ (support) you.", "a": "will support"},
                {"q": "The weather report says it ___ (be) sunny tomorrow.", "a": "will be"},
                {"q": "I ___ (wait) for you at the gate at 7 o'clock.", "a": "will wait"},
                {"q": "She has decided that she ___ (study) abroad.", "a": "is going to study"},
                {"q": "When I grow up, I ___ (become) a scientist.", "a": "am going to become"},
                {"q": "I bet he ___ (be) late again today.", "a": "will be"},
                {"q": "We ___ (celebrate) Mom's birthday this Sunday.", "a": "are going to celebrate"},
            ]
        },
        {
            "title": "现在进行时",
            "grade": 7,
            "questions": [
                {"q": "Look! It ___ (rain) outside now.", "a": "is raining"},
                {"q": "Listen! Someone ___ (sing) in the classroom.", "a": "is singing"},
                {"q": "They ___ (play) basketball on the playground.", "a": "are playing"},
                {"q": "I ___ (do) my homework right now.", "a": "am doing"},
                {"q": "She ___ (read) a book in the library at the moment.", "a": "is reading"},
                {"q": "Be quiet. The baby ___ (sleep).", "a": "is sleeping"},
                {"q": "Where is Tom? He ___ (take) a shower.", "a": "is taking"},
                {"q": "My parents ___ (watch) TV in the living room.", "a": "are watching"},
                {"q": "Why ___ you ___ (cry)?", "a": "are, crying"},
                {"q": "The children ___ (fly) kites in the park.", "a": "are flying"},
                {"q": "It ___ (not snow) now. It's just very cold.", "a": "isn't snowing"},
                {"q": "___ they ___ (wait) for the bus?", "a": "Are, waiting"},
                {"q": "He always ___ (complain) about something. (表示不满)", "a": "is always complaining"},
                {"q": "We ___ (learn) English these days.", "a": "are learning"},
                {"q": "More and more people ___ (use) mobile phones.", "a": "are using"},
                {"q": "The world ___ (change) rapidly.", "a": "is changing"},
                {"q": "What ___ you ___ (look) for?", "a": "are, looking"},
                {"q": "She ___ (work) on a new project this month.", "a": "is working"},
                {"q": "I can't talk right now. I ___ (drive).", "a": "am driving"},
                {"q": "___ it getting dark already?", "a": "Is"},
                {"q": "The price of houses ___ (rise) fast.", "a": "is rising"},
                {"q": "Please call back later. We ___ (have) dinner now.", "a": "are having"},
                {"q": "Tom is good at sports. He ___ (practice) swimming every day.", "a": "is practicing"},
                {"q": "Shh! The teacher ___ (come).", "a": "is coming"},
                {"q": "You ___ (always/leave) your things everywhere!", "a": "are always leaving"},
                {"q": "This year more students ___ (study) Chinese.", "a": "are studying"},
                {"q": "Why ___ he ___ (run) so fast?", "a": "is, running"},
                {"q": "I'm sorry. She ___ (not feel) well today.", "a": "isn't feeling"},
                {"q": "The company ___ (grow) quickly under new management.", "a": "is growing"},
                {"q": "We ___ (plan) a surprise party for her birthday.", "a": "are planning"},
                {"q": "These days technology ___ (develop) faster than ever.", "a": "is developing"},
                {"q": "The number of cars on the road ___ (increase).", "a": "is increasing"},
                {"q": "What ___ you ___ (think) about?", "a": "are, thinking"},
                {"q": "I ___ (stay) with my aunt while my parents are away.", "a": "am staying"},
                {"q": "The population of this city ___ (become) larger and larger.", "a": "is becoming"},
                {"q": "My brother ___ (save) money to buy a new car.", "a": "is saving"},
                {"q": "We ___ (get) ready for the final exam.", "a": "are getting"},
                {"q": "Why ___ everyone ___ (laugh)?", "a": "are, laughing"},
                {"q": "She ___ (wear) a beautiful dress today.", "a": "is wearing"},
                {"q": "I ___ (write) a letter to my pen pal.", "a": "am writing"},
                {"q": "They ___ (not speak) to each other these days.", "a": "aren't speaking"},
                {"q": "Our team ___ (do) very well this season.", "a": "is doing"},
                {"q": "I ___ (look) for my keys. Have you seen them?", "a": "am looking"},
                {"q": "The economy ___ (improve) gradually.", "a": "is improving"},
                {"q": "What ___ you ___ (do) this weekend?", "a": "are, doing"},
            ]
        },
        {
            "title": "名词（数/所有格/不可数名词）",
            "grade": 7,
            "questions": [
                {"q": "There are three ___ (box) on the desk.", "a": "boxes"},
                {"q": "I bought two ___ (knife) yesterday.", "a": "knives"},
                {"q": "How many ___ (child) are there in your family?", "a": "children"},
                {"q": "The ___ (leaf) turn yellow in autumn.", "a": "leaves"},
                {"q": "Three ___ (man) are fishing by the river.", "a": "men"},
                {"q": "I need some ___ (paper) to write on.", "a": "paper"},
                {"q": "Please give me two ___ (piece) of cake.", "a": "pieces"},
                {"q": "The ___ (hero) story moved everyone.", "a": "hero's"},
                {"q": "This is my ___ (mother) car.", "a": "mother's"},
                {"q": "___ (Tom and Jack) school is near here.", "a": "Tom and Jack's"},
                {"q": "Today is ___ (teacher) Day.", "a": "Teachers'"},
                {"q": "I went to the ___ (dentist) yesterday.", "a": "dentist's"},
                {"q": "There is lots of ___ (water) in the bottle.", "a": "water"},
                {"q": "She has two ___ (sister).", "a": "sisters"},
                {"q": "The ___ (boy) favorite toy is broken.", "a": "boy's"},
                {"q": "I have a lot of ___ (homework) to do.", "a": "homework"},
                {"q": "Many ___ (foreign) visit China every year.", "a": "foreigners"},
                {"q": "The ___ (news) is very exciting.", "a": "news"},
                {"q": "Two ___ (wolf) were seen in the forest.", "a": "wolves"},
                {"q": "All the ___ (student) books are on the desk.", "a": "students'"},
                {"q": "I'd like some ___ (bread) and milk.", "a": "bread"},
                {"q": "The cat caught three ___ (mouse) last night.", "a": "mice"},
                {"q": "There are many ___ (sheep) on the hill.", "a": "sheep"},
                {"q": "How much ___ (furniture) did you buy?", "a": "furniture"},
                {"q": "I need some ___ (advice). Can you help me?", "a": "advice"},
                {"q": "The ___ (police) are looking for him.", "a": "police"},
                {"q": "Physics ___ (be) my favorite subject.", "a": "is"},
                {"q": "His ___ (foot) hurt after the long walk.", "a": "feet"},
                {"q": "She brushed her ___ (tooth) before bed.", "a": "teeth"},
                {"q": "I saw many ___ (deer) in the zoo.", "a": "deer"},
                {"q": "Please give me some ___ (information) about the hotel.", "a": "information"},
                {"q": "The ___ (Chinese) are friendly people.", "a": "Chinese"},
                {"q": "Mathematics ___ (be) difficult but useful.", "a": "is"},
                {"q": "I have two ___ (brother-in-law).", "a": "brothers-in-law"},
                {"q": "She has beautiful ___ (eye).", "a": "eyes"},
                {"q": "There is ___ (fish) on the plate.", "a": "fish"},
                {"q": "The ___ (glass) on the table are dirty.", "a": "glasses"},
                {"q": "He gave me some good ___ (suggestion).", "a": "suggestions"},
                {"q": "There isn't much ___ (time) left.", "a": "time"},
                {"q": "The ___ (people) here are very kind.", "a": "people"},
                {"q": "I had some ___ (noodle) for lunch.", "a": "noodles"},
                {"q": "___ (Mary and Tom) mothers are both teachers.", "a": "Mary's and Tom's"},
                {"q": "This is ___ (someone else) bag.", "a": "someone else's"},
                {"q": "I bought two ___ (loaf) of bread.", "a": "loaves"},
                {"q": "There are sixty ___ (woman) teachers in our school.", "a": "women"},
                {"q": "The ___ (government) has made a new plan.", "a": "government"},
                {"q": "He has rich ___ (experience) in teaching.", "a": "experience"},
                {"q": "All ___ (equipment) must be checked.", "a": "equipment"},
                {"q": "Her ___ (hair) is long and black.", "a": "hair"},
                {"q": "The ___ (German) make excellent cars.", "a": "Germans"},
                {"q": "I need to buy some ___ (fruit).", "a": "fruit"},
                {"q": "There are many ___ (photo) in the album.", "a": "photos"},
            ]
        },
        {
            "title": "冠词 (a/an/the)",
            "grade": 7,
            "questions": [
                {"q": "There is ___ 'u' and ___ 's' in the word 'us'.", "a": "a, an"},
                {"q": "I saw ___ elephant at the zoo yesterday.", "a": "an"},
                {"q": "The boy in ___ blue is my brother.", "a": "/ (不填)"},
                {"q": "___ earth goes around ___ sun.", "a": "The, the"},
                {"q": "He is ___ honest boy.", "a": "an"},
                {"q": "I usually play ___ piano after school.", "a": "the"},
                {"q": "Let's go for ___ walk after dinner.", "a": "a"},
                {"q": "___ Great Wall is one of the wonders.", "a": "The"},
                {"q": "She wants to be ___ engineer when she grows up.", "a": "an"},
                {"q": "My father works in ___ hospital.", "a": "a"},
                {"q": "I had ___ breakfast and went to school.", "a": "/ (不填)"},
                {"q": "___ moon is bright tonight.", "a": "The"},
                {"q": "He is ___ tallest student in our class.", "a": "the"},
                {"q": "I want to be ___ doctor like my mother.", "a": "a"},
                {"q": "___ Chinese is a difficult language.", "a": "/ (不填)"},
                {"q": "She plays ___ guitar very well.", "a": "the"},
                {"q": "It is ___ useful book.", "a": "a"},
                {"q": "I go to school by ___ bus.", "a": "/ (不填)"},
                {"q": "He was born in ___ May.", "a": "/ (不填)"},
                {"q": "___ rich should help the poor.", "a": "The"},
                {"q": "There is ___ map on the wall.", "a": "a"},
                {"q": "She is ___ university student.", "a": "a"},
                {"q": "I have ___ idea. Let's try it!", "a": "an"},
                {"q": "___ Yellow River is the second longest river.", "a": "The"},
                {"q": "He plays ___ chess very well.", "a": "/ (不填)"},
                {"q": "This is ___ best movie I've ever seen.", "a": "the"},
                {"q": "What ___ lovely day it is!", "a": "a"},
                {"q": "I met him ___ hour ago.", "a": "an"},
                {"q": "She is ___ only child in her family.", "a": "the"},
                {"q": "___ more you read, ___ more you know.", "a": "The, the"},
                {"q": "He joined ___ army last year.", "a": "the"},
                {"q": "What ___ interesting story it is!", "a": "an"},
                {"q": "I usually go to bed at ___ night.", "a": "/ (不填)"},
                {"q": "___ United States is a big country.", "a": "The"},
                {"q": "He is ___ European.", "a": "a"},
                {"q": "She wants to travel around ___ world.", "a": "the"},
                {"q": "This is ___ first time I've been here.", "a": "the"},
                {"q": "I saw ___ one-eyed man at the door.", "a": "a"},
                {"q": "___ old need care and love.", "a": "The"},
                {"q": "He has ___ headache.", "a": "a"},
                {"q": "She went there by ___ train.", "a": "/ (不填)"},
                {"q": "What ___ bad weather!", "a": "/ (不填)"},
                {"q": "He is ___ honor to our school.", "a": "an"},
                {"q": "I live on ___ twelfth floor.", "a": "the"},
                {"q": "___ Smiths are coming for dinner.", "a": "The"},
                {"q": "He plays ___ basketball after school.", "a": "/ (不填)"},
                {"q": "She is ___ most careful girl I know.", "a": "the"},
                {"q": "I have ___ lunch at school every day.", "a": "/ (不填)"},
                {"q": "He became ___ famous writer.", "a": "a"},
                {"q": "___ blind need our help.", "a": "The"},
            ]
        },
        {
            "title": "数词 (基数词/序数词/分数)",
            "grade": 7,
            "questions": [
                {"q": "There are ___ (twelve) months in a year.", "a": "twelve"},
                {"q": "Today is his ___ (nine) birthday.", "a": "ninth"},
                {"q": "March is the ___ (three) month of the year.", "a": "third"},
                {"q": "About ___ (thousand) people attended the concert.", "a": "thousand"},
                {"q": "He finished ___ (two) in the race.", "a": "second"},
                {"q": "Millions of ___ (visit) come here every year.", "a": "visitors"},
                {"q": "The ___ (twenty-one) century is the information age.", "a": "twenty-first"},
                {"q": "There are ___ (hundred) of birds in the tree.", "a": "hundreds"},
                {"q": "He lives on the ___ (five) floor.", "a": "fifth"},
                {"q": "About two ___ (third) of the students are boys.", "a": "thirds"},
                {"q": "It happened in the ___ (1940s).", "a": "1940s"},
                {"q": "Room ___ (305) is on the third floor.", "a": "305"},
                {"q": "He got up at ___ (6:45) this morning.", "a": "a quarter to seven / 6:45"},
                {"q": "It is about ___ (5000) kilometers from here.", "a": "five thousand / 5000"},
                {"q": "The ___ (one) lesson is easy.", "a": "first"},
                {"q": "He is only in his ___ (40).", "a": "forties"},
                {"q": "Every ___ (four) years, there is a World Cup.", "a": "four"},
                {"q": "It took us ___ (one and a half) hours.", "a": "one and a half"},
                {"q": "About ___ (80%) of the work is done.", "a": "eighty percent / 80%"},
                {"q": "He was born in ___ (1998).", "a": "1998"},
                {"q": "There are ___ (seven) days in a week.", "a": "seven"},
                {"q": "December is the ___ (twelve) month.", "a": "twelfth"},
                {"q": "Thousands of ___ (people) lost their homes.", "a": "people"},
                {"q": "He came out ___ (one) in the exam.", "a": "first"},
                {"q": "The ___ (two) chapter is about grammar.", "a": "second"},
                {"q": "Millions of ___ (year) ago, dinosaurs lived here.", "a": "years"},
                {"q": "He is ___ (18) years old.", "a": "eighteen"},
                {"q": "Please turn to page ___ (56).", "a": "56"},
                {"q": "The building is ___ (100) meters tall.", "a": "one hundred / hundred"},
                {"q": "It happened on July ___, 2023.", "a": "4th / the fourth / four"},
                {"q": "He lives at ___ (Room 1012).", "a": "Room 1012"},
                {"q": "About ___ (3/5) of the earth is covered by water.", "a": "three fifths / 3/5"},
                {"q": "In his ___ (30), he started his own business.", "a": "thirties"},
                {"q": "The ___ (21st) century began in 2001.", "a": "21st / twenty-first"},
                {"q": "It costs $ ___ (5.99).", "a": "five ninety-nine / five point nine nine"},
                {"q": "___ (2) plus ___ (3) equals ___ (5).", "a": "Two, three, five"},
                {"q": "China has a history of over ___ (5000) years.", "a": "five thousand / 5000"},
                {"q": "There are ___ (60) seconds in a minute.", "a": "sixty"},
                {"q": "She ranked ___ (3rd) in the competition.", "a": "third"},
            ]
        },
        {
            "title": "连词 (and/but/or/so/because/if/although)",
            "grade": 7,
            "questions": [
                {"q": "Study hard, ___ you will pass the exam.", "a": "and"},
                {"q": "He is rich ___ unhappy.", "a": "but"},
                {"q": "Would you like tea ___ coffee?", "a": "or"},
                {"q": "It was raining, ___ we stayed at home.", "a": "so"},
                {"q": "He didn't come ___ he was ill.", "a": "because"},
                {"q": "You can go by bus ___ by taxi.", "a": "or"},
                {"q": "Not only you ___ also he was praised.", "a": "but"},
                {"q": "Hurry up, ___ you will be late.", "a": "or"},
                {"q": "I like both singing ___ dancing.", "a": "and"},
                {"q": "He is neither rich ___ famous.", "a": "nor"},
                {"q": "She didn't say anything, ___ I knew what she meant.", "a": "but/yet"},
                {"q": "It was cold, ___ he went out without a coat.", "a": "yet/but"},
                {"q": "Either you ___ I am wrong.", "a": "or"},
                {"q": "Work hard, ___ your dream will come true.", "a": "and"},
                {"q": "He is tired ___ he worked all night.", "a": "because/since/as"},
                {"q": "I don't know ___ he will come or not.", "a": "whether/if"},
                {"q": "It's not cheap, ___ it's very good.", "a": "but"},
                {"q": "Do you want to leave ___ stay?", "a": "or"},
                {"q": "He is young, ___ he knows a lot.", "a": "but/yet"},
                {"q": "It rained heavily, ___ the game was cancelled.", "a": "so"},
                {"q": "I waited ___ he came back.", "a": "until/till"},
                {"q": "I didn't know it ___ you told me.", "a": "until"},
                {"q": "Although he is old, ___ he works hard.", "a": "yet/(不填)"},
                {"q": "Both Tom ___ Mary are good students.", "a": "and"},
                {"q": "Neither he nor she ___ right.", "a": "is"},
                {"q": "The weather was bad, ___ we still went hiking.", "a": "but/yet"},
                {"q": "I was hungry, ___ I ate two sandwiches.", "a": "so"},
                {"q": "Is this yours ___ mine?", "a": "or"},
                {"q": "You can take a taxi, ___ you can walk.", "a": "or"},
                {"q": "Not only does he sing well, ___ dances beautifully.", "a": "but he also"},
                {"q": "She is smart ___ beautiful.", "a": "and"},
                {"q": "Hurry up, ___ you'll miss the bus.", "a": "or/otherwise"},
                {"q": "It was late, ___ I went to bed anyway.", "a": "but/yet"},
                {"q": "He is tired ___ sleepy.", "a": "and"},
                {"q": "I don't know ___ to laugh or cry.", "a": "whether"},
                {"q": "He didn't study hard, ___ he failed the exam.", "a": "so"},
                {"q": "He looks happy ___ sad. I can't tell.", "a": "or"},
                {"q": "She can speak ___ English ___ French.", "a": "both, and"},
                {"q": "___ it was raining, they played football.", "a": "Although/Though"},
                {"q": "Keep trying, ___ you'll succeed eventually.", "a": "and"},
                {"q": "I like apples, ___ I don't like bananas.", "a": "but"},
            ]
        },
        {
            "title": "there be 句型",
            "grade": 7,
            "questions": [
                {"q": "There ___ (be) a book on the desk.", "a": "is"},
                {"q": "There ___ (be) some water in the cup.", "a": "is"},
                {"q": "There ___ (be) many students in the classroom.", "a": "are"},
                {"q": "There ___ (be) a pen and two pencils in the box.", "a": "is"},
                {"q": "There ___ (be) no air on the moon.", "a": "is"},
                {"q": "___ (there be) a meeting tomorrow afternoon?", "a": "Will there be / Is there going to be"},
                {"q": "There used to ___ (be) a tree here.", "a": "be"},
                {"q": "There ___ (be) going to be a football match.", "a": "is"},
                {"q": "How many people ___ (there be) in your family?", "a": "are there"},
                {"q": "There must ___ (be) something wrong with the computer.", "a": "be"},
                {"q": "There seems ___ (be) a mistake in the bill.", "a": "to be"},
                {"q": "There ___ (be) no doubt about the result.", "a": "is"},
                {"q": "There may ___ (be) another way to solve this.", "a": "be"},
                {"q": "Once there lived ___ (live) an old man in the village.", "a": "an old man"},
                {"q": "There stands ___ (stand) a tall tree in front of the house.", "a": "a tall tree"},
                {"q": "There lies ___ (lie) a small village at the foot of the mountain.", "a": "a small village"},
                {"q": "There have ___ (be) great changes in my hometown.", "a": "been"},
                {"q": "There might ___ (be) someone at the door.", "a": "be"},
                {"q": "There ought to ___ (be) more buses on this route.", "a": "be"},
                {"q": "There happened ___ (be) nobody in the room.", "a": "to be"},
                {"q": "There ___ (be) nothing we can do now.", "a": "is"},
                {"q": "There ___ (be) few people who know the truth.", "a": "are"},
                {"q": "There ___ (have) been many accidents here.", "a": "has"},
                {"q": "There doesn't seem ___ (be) much hope.", "a": "to be"},
                {"q": "There ___ (be) a lot of work to do.", "a": "is"},
                {"q": "There appeared ___ (appear) a ship on the horizon.", "a": "a ship"},
                {"q": "There remains ___ (remain) one problem to solve.", "a": "one problem"},
                {"q": "There came ___ (come) a loud knock at the door.", "a": "a loud knock"},
                {"q": "There ___ (not be) enough food for everyone.", "a": "isn't/is not"},
                {"q": "There ___ (be) several reasons for his failure.", "a": "are"},
                {"q": "___ (there be) any news about the missing plane?", "a": "Is there"},
                {"q": "There shouldn't ___ (be) any noise in the library.", "a": "be"},
                {"q": "There flows ___ (flow) a river through the town.", "a": "a river"},
                {"q": "There exists ___ (exist) a solution to every problem.", "a": "a solution"},
                {"q": "There followed ___ (follow) a long silence.", "a": "a long silence"},
                {"q": "There arose ___ (arise) a new problem.", "a": "a new problem"},
                {"q": "There ___ (be) no need to hurry.", "a": "is"},
            ]
        },
        {
            "title": "感叹句",
            "grade": 7,
            "questions": [
                {"q": "___ beautiful flower it is!", "a": "What a"},
                {"q": "___ fast he runs!", "a": "How"},
                {"q": "___ interesting the movie is!", "a": "How"},
                {"q": "___ clever boy he is!", "a": "What a"},
                {"q": "___ delicious the food tastes!", "a": "How"},
                {"q": "___ terrible weather we are having!", "a": "What"},
                {"q": "___ carefully he drives!", "a": "How"},
                {"q": "___ nice music it is!", "a": "What"},
                {"q": "___ hard the students are working!", "a": "How"},
                {"q": "___ exciting news you brought us!", "a": "What"},
                {"q": "___ lovely girls they are!", "a": "What"},
                {"q": "___ slowly the old man walks!", "a": "How"},
                {"q": "___ wonderful idea you have!", "a": "What a/wonderful"},
                {"q": "___ beautiful the flowers look!", "a": "How"},
                {"q": "___ brave the firefighter is!", "a": "How"},
                {"q": "___ great progress you have made!", "a": "What"},
                {"q": "___ high the mountain is!", "a": "How"},
                {"q": "___ foolish mistake he made!", "a": "What a"},
                {"q": "___ well she speaks English!", "a": "How"},
                {"q": "___ fun it is to swim in summer!", "a": "What"},
                {"q": "___ a lovely day it is today!", "a": "What"},
                {"q": "___ quickly time flies!", "a": "How"},
                {"q": "___ amazing magic show it was!", "a": "What an"},
                {"q": "___ kind the old lady is!", "a": "How"},
                {"q": "___ important it is to learn English!", "a": "How"},
                {"q": "___ terrible noise they are making!", "a": "What a"},
                {"q": "___ heavily it is snowing!", "a": "How"},
                {"q": "___ beautiful place Hangzhou is!", "a": "What a"},
                {"q": "___ fast the car goes!", "a": "How"},
                {"q": "___ interesting book this is!", "a": "What an"},
                {"q": "___ careless he was!", "a": "How"},
                {"q": "___ good time we had at the party!", "a": "What a"},
                {"q": "___ pretty the girl looks in that dress!", "a": "How"},
                {"q": "___ delicious smell!", "a": "What a"},
                {"q": "___ brave of you to say that!", "a": "How"},
                {"q": "___ lovely weather we're having!", "a": "What"},
                {"q": "___ well she sings!", "a": "How"},
                {"q": "___ expensive this car is!", "a": "How"},
                {"q": "___ nice surprise it was!", "a": "What a"},
                {"q": "___ happily the children are playing!", "a": "How"},
            ]
        },
    ],
    "七年级下学期": [
        {
            "title": "一般过去时",
            "questions": [
                {"q": "I ___ (go) to the park yesterday.", "a": "went"},
                {"q": "She ___ (visit) her grandparents last weekend.", "a": "visited"},
                {"q": "They ___ (play) football yesterday.", "a": "played"},
                {"q": "He ___ (watch) TV last night.", "a": "watched"},
                {"q": "We ___ (have) a great time at the party.", "a": "had"},
                {"q": "I ___ (eat) an apple this morning.", "a": "ate"},
                {"q": "She ___ (buy) a new dress yesterday.", "a": "bought"},
                {"q": "The meeting ___ (begin) at 8 o'clock.", "a": "began"},
                {"q": "He ___ (not go) to school yesterday.", "a": "didn't go"},
                {"q": "___ you ___ (see) the movie last night衣", "a": "Did, see"},
                {"q": "___ she ___ (finish) her homework衣", "a": "Did, finish"},
                {"q": "I ___ (not eat) breakfast this morning.", "a": "didn't eat"},
                {"q": "They ___ (come) to China last year.", "a": "came"},
                {"q": "She ___ (make) a cake for me.", "a": "made"},
                {"q": "We ___ (take) a taxi to the airport.", "a": "took"},
                {"q": "He ___ (write) a letter to his friend.", "a": "wrote"},
                {"q": "I ___ (read) an interesting book.", "a": "read"},
                {"q": "Where ___ you ___ (go) yesterday衣", "a": "did, go"},
                {"q": "They ___ (build) a new hospital last year.", "a": "built"},
                {"q": "She ___ (cry) when she heard the news.", "a": "cried"},
                # 一般过去时琛厖棰樼洰 (30閬衣
                {"q": "I ___ (study) English yesterday.", "a": "studied"},
                {"q": "She ___ (clean) her room last week.", "a": "cleaned"},
                {"q": "They ___ (walk) to school every day.", "a": "walked"},
                {"q": "He ___ (call) me last night.", "a": "called"},
                {"q": "We ___ (enjoy) the party yesterday.", "a": "enjoyed"},
                {"q": "She ___ (not stay) at home.", "a": "did not stay"},
                {"q": "I ___ (think) about it for a long time.", "a": "thought"},
                {"q": "He ___ (bring) a gift for me.", "a": "brought"},
                {"q": "They ___ (fight) with each other.", "a": "fought"},
                {"q": "She ___ (buy) a new dress yesterday.", "a": "bought"},
                {"q": "We ___ (travel) to Beijing last summer.", "a": "traveled"},
                {"q": "He ___ (not believe) the story.", "a": "did not believe"},
                {"q": "I ___ (receive) a letter from my friend.", "a": "received"},
                {"q": "She ___ (decide) to study harder.", "a": "decided"},
                {"q": "They ___ (leave) early this morning.", "a": "left"},
                {"q": "He ___ (meet) his old friend yesterday.", "a": "met"},
                {"q": "I ___ (lend) him my book.", "a": "lent"},
                {"q": "She ___ (feel) tired after the long trip.", "a": "felt"},
                {"q": "We ___ (hope) to see you soon.", "a": "hoped"},
                {"q": "He ___ (keep) his promise.", "a": "kept"},
                {"q": "I ___ (lose) my way in the city.", "a": "lost"},
                {"q": "She ___ (teach) at this school for 10 years.", "a": "taught"},
                {"q": "They ___ (understand) the lesson.", "a": "understood"},
                {"q": "He ___ (sleep) early last night.", "a": "slept"},
                {"q": "I ___ (not know) about it.", "a": "did not know"},
                {"q": "She ___ (begin) to learn English at age 6.", "a": "began"},
                {"q": "We ___ (choose) the blue one.", "a": "chose"},
                {"q": "He ___ (drive) to work yesterday.", "a": "drove"},
            ]
        },
        {
            "title": "过去进行时",
            "questions": [
                {"q": "I ___ ___ (watch) TV at 8 pm yesterday.", "a": "was watching"},
                {"q": "She ___ ___ (cook) when I came home.", "a": "was cooking"},
                {"q": "They ___ ___ (play) football at 4 pm yesterday.", "a": "were playing"},
                {"q": "He ___ ___ (sleep) when the phone rang.", "a": "was sleeping"},
                {"q": "We ___ ___ (have) dinner at that time.", "a": "were having"},
                {"q": "What ___ you ___ (do) at 9 pm last night衣", "a": "were, doing"},
                {"q": "I ___ ___ (read) while she ___ ___ (sing).", "a": "was reading, was singing"},
                {"q": "When I saw him, he ___ ___ (run).", "a": "was running"},
                {"q": "It ___ ___ (rain) when we left.", "a": "was raining"},
                {"q": "The children ___ ___ (play) when the teacher came in.", "a": "were playing"},
                {"q": "I ___ ___ (not sleep) when you called.", "a": "was not sleeping"},
                {"q": "___ you ___ (study) at 10 pm last night衣", "a": "Were, studying"},
                {"q": "While I ___ ___ (walk) home, I met an old friend.", "a": "was walking"},
                {"q": "He ___ ___ (write) a letter when I visited him.", "a": "was writing"},
                {"q": "They ___ ___ (not talk) when the teacher came in.", "a": "were not talking"},
                # 杩囧幓杩涜格鏃惰鍏呴理目录衣(35閬衣
                {"q": "I ___ ___ (read) a book at 8 pm last night.", "a": "was reading"},
                {"q": "She ___ ___ (cook) when the doorbell rang.", "a": "was cooking"},
                {"q": "They ___ ___ (play) football at 4 pm yesterday.", "a": "were playing"},
                {"q": "He ___ ___ (sleep) when the phone rang.", "a": "was sleeping"},
                {"q": "We ___ ___ (have) dinner at 7 pm.", "a": "were having"},
                {"q": "What ___ you ___ (do) at 9 pm last night衣", "a": "were, doing"},
                {"q": "I ___ ___ (read) while she ___ ___ (sing).", "a": "was reading, was singing"},
                {"q": "When I saw him, he ___ ___ (run).", "a": "was running"},
                {"q": "It ___ ___ (rain) when we left.", "a": "was raining"},
                {"q": "The children ___ ___ (play) when the teacher came in.", "a": "were playing"},
                {"q": "I ___ ___ (not sleep) when you called.", "a": "was not sleeping"},
                {"q": "___ you ___ (study) at 10 pm last night衣", "a": "Were, studying"},
                {"q": "While I ___ ___ (walk) home, I met an old friend.", "a": "was walking"},
                {"q": "He ___ ___ (write) a letter when I visited him.", "a": "was writing"},
                {"q": "She ___ ___ (watch) TV at that time.", "a": "was watching"},
                {"q": "The baby ___ ___ (cry) all night.", "a": "was crying"},
                {"q": "We ___ ___ (talk) about you.", "a": "were talking"},
                {"q": "He ___ ___ (not listen) to music.", "a": "was not listening"},
                {"q": "What ___ she ___ (do) when you called衣", "a": "was, doing"},
                {"q": "I ___ ___ (wait) for the bus.", "a": "was waiting"},
                {"q": "They ___ ___ (not play) games at that moment.", "a": "were not playing"},
                {"q": "She ___ ___ (think) about the problem.", "a": "was thinking"},
                {"q": "The sun ___ ___ (shine) when we left.", "a": "was shining"},
                {"q": "We ___ ___ (plan) our trip.", "a": "were planning"},
                {"q": "He ___ ___ (drive) when the accident happened.", "a": "was driving"},
                {"q": "I ___ ___ (not feel) well yesterday.", "a": "was not feeling"},
                {"q": "She ___ ___ (practice) the piano.", "a": "was practicing"},
                {"q": "They ___ ___ (swim) in the pool.", "a": "were swimming"},
                {"q": "The wind ___ ___ (blow) strongly.", "a": "was blowing"},
                {"q": "I ___ ___ (shop) when I saw my teacher.", "a": "was shopping"},
                {"q": "He ___ ___ (work) in the garden.", "a": "was working"},
                {"q": "We ___ ___ (clean) the house.", "a": "were cleaning"},
                {"q": "She ___ ___ (draw) a picture.", "a": "was drawing"},
            ]
        },
        {
            "title": "形容词比较级和最高级",
            "questions": [
                {"q": "Tom is ___ (tall) than Jerry.", "a": "taller"},
                {"q": "This book is ___ (interesting) than that one.", "a": "more interesting"},
                {"q": "She is ___ (beautiful) in our class.", "a": "the most beautiful"},
                {"q": "My room is ___ (big) than yours.", "a": "bigger"},
                {"q": "He runs ___ (fast) in his school.", "a": "the fastest"},
                {"q": "This is ___ (good) movie I have ever seen.", "a": "the best"},
                {"q": "Summer is ___ (hot) than spring.", "a": "hotter"},
                {"q": "My English is ___ (good) than before.", "a": "better"},
                {"q": "This movie is ___ (bad) than that one.", "a": "worse"},
                {"q": "He is ___ (thin) than his brother.", "a": "thinner"},
                {"q": "This is ___ (bad) day of my life.", "a": "the worst"},
                {"q": "Health is ___ (important) than money.", "a": "more important"},
                {"q": "Which is ___ (big), the sun or the moon衣", "a": "bigger"},
                {"q": "The weather is getting ___ (warm) and ___ (warm).", "a": "warmer, warmer"},
                {"q": "She is ___ (hard-working) student in the class.", "a": "the most hard-working"},
                {"q": "He is ___ (tall) of all the boys.", "a": "the tallest"},
                {"q": "This question is ___ (easy) than that one.", "a": "easier"},
                {"q": "Shanghai is one of ___ (big) cities in China.", "a": "the biggest"},
                {"q": "She sings ___ (well) in our class.", "a": "the best"},
                {"q": "This road is ___ (wide) than that one.", "a": "wider"},
                # 形容词比较级和最高级琛厖棰樼洰 (30閬衣
                {"q": "Tom is ___ (tall) than any other student in the class.", "a": "taller"},
                {"q": "This is ___ (easy) question I have ever seen.", "a": "the easiest"},
                {"q": "He is ___ (clever) boy in our class.", "a": "the cleverest"},
                {"q": "My sister is three years ___ (old) than me.", "a": "older"},
                {"q": "She is ___ (beautiful) than her sister.", "a": "more beautiful"},
                {"q": "This is ___ (interesting) book I have ever read.", "a": "the most interesting"},
                {"q": "The weather today is ___ (bad) than yesterday.", "a": "worse"},
                {"q": "This is ___ (cold) winter in 10 years.", "a": "the coldest"},
                {"q": "He is ___ (young) of the three brothers.", "a": "the youngest"},
                {"q": "This problem is ___ (difficult) than that one.", "a": "more difficult"},
                {"q": "She sings ___ (well) than her sister.", "a": "better"},
                {"q": "He is ___ (happy) man in the world.", "a": "the happiest"},
                {"q": "China is ___ (large) than Japan.", "a": "larger"},
                {"q": "This movie is ___ (popular) among young people.", "a": "the most popular"},
                {"q": "The blue car runs ___ (fast) than the red one.", "a": "faster"},
                {"q": "He is ___ (rich) man in our town.", "a": "the richest"},
                {"q": "This lesson is ___ (important) than the last one.", "a": "more important"},
                {"q": "She is ___ (careful) than her brother.", "a": "more careful"},
                {"q": "Today is ___ (hot) day of the year.", "a": "the hottest"},
                {"q": "He is ___ (brave) soldier in the army.", "a": "the bravest"},
                {"q": "This book is ___ (expensive) than that one.", "a": "more expensive"},
                {"q": "She is ___ (pretty) than her cousin.", "a": "prettier"},
                {"q": "This is ___ (delicious) food I have ever tasted.", "a": "the most delicious"},
                {"q": "He is ___ (kind) man I know.", "a": "the kindest"},
                {"q": "Running is ___ (healthy) than swimming.", "a": "healthier"},
                {"q": "This is ___ (wonderful) movie I have ever seen.", "a": "the most wonderful"},
                {"q": "She looks ___ (beautiful) today.", "a": "more beautiful"},
                {"q": "This is ___ (dangerous) animal in the world.", "a": "the most dangerous"},
                {"q": "He is ___ (friendly) than his brother.", "a": "friendlier"},
            ]
        },
        {
            "title": "不定代词",
            "questions": [
                {"q": "I have ___ (涓浜衣 money.", "a": "some"},
                {"q": "Do you have ___ (浠讳綍) questions衣", "a": "any"},
                {"q": "There is ___ (娌湁浜衣 in the room.", "a": "nobody"},
                {"q": "___ (鏈変汉) is waiting for you outside.", "a": "Someone"},
                {"q": "I have ___ (娌湁) to say.", "a": "nothing"},
                {"q": "___ (姣忎釜) student has a book.", "a": "Every"},
                {"q": "I didn't see ___ (浠讳綍浜衣.", "a": "anyone"},
                {"q": "___ (涓呴兘) of them are students.", "a": "Both"},
                {"q": "___ (涓呴兘涓衣 of the answers is correct.", "a": "Neither"},
                {"q": "You can take ___ (浠讳竴) of the two books.", "a": "either"},
                {"q": "There isn't ___ (浠讳綍) water in the glass.", "a": "any"},
                {"q": "I want ___ (涓浜衣 tea.", "a": "some"},
                {"q": "Would you like ___ (涓浜衣 coffee衣", "a": "some"},
                {"q": "There is ___ (鏌愮墿) on the table.", "a": "something"},
                {"q": "I have ___ (璁稿套) friends.", "a": "many"},
                {"q": "There is ___ (灏戦噺) milk left.", "a": "a little"},
                {"q": "I have ___ (鍑犱釜) good books.", "a": "a few"},
                {"q": "___ (鎵鏈衣 of the students passed the exam.", "a": "All"},
                {"q": "There is ___ (浠涔堜篃娌湁) in the box.", "a": "nothing"},
                {"q": "___ (鏈変汉) stole my bag.", "a": "Someone"},
                # 不定代词琛厖棰樼洰 (30閬衣
                {"q": "I have ___ (涓浜衣 apples.", "a": "some"},
                {"q": "Is there ___ (浠讳綍) water in the glass衣", "a": "any"},
                {"q": "___ (娌湁浜衣 knows the answer.", "a": "Nobody"},
                {"q": "There is ___ (鏌愮墿) important on the table.", "a": "something"},
                {"q": "I know ___ (姣忎釜浜衣 in this class.", "a": "everyone"},
                {"q": "___ (姣忎釜浜衣 should do their best.", "a": "Everybody"},
                {"q": "There is ___ (娌'粈涔衣 to worry about.", "a": "nothing"},
                {"q": "___ (涓衣 of them are right.", "a": "Both"},
                {"q": "___ (涓呴兘涓衣 of the answers is correct.", "a": "Neither"},
                {"q": "You can take ___ (浠讳竴) of these books.", "a": "either"},
                {"q": "I have ___ (鍑犱釜) friends here.", "a": "a few"},
                {"q": "There is only ___ (涓点 milk left.", "a": "a little"},
                {"q": "___ (鎵鏈衣 the students are here.", "a": "All"},
                {"q": "I have ___ (璁稿套) work to do.", "a": "much"},
                {"q": "There are ___ (寰堝套) people in the park.", "a": "many"},
                {"q": "Do you have ___ (浠讳綍) questions衣", "a": "any"},
                {"q": "___ (娌'汉) was at home when I called.", "a": "Nobody"},
                {"q": "I saw ___ (鏌愪汉) in the garden.", "a": "someone"},
                {"q": "There is ___ (娌'粈涔衣 new in today's newspaper.", "a": "nothing"},
                {"q": "___ (姣忎釜) of us has a dream.", "a": "Each"},
                {"q": "I need ___ (涓浜衣 help.", "a": "some"},
                {"q": "Is there ___ (浠讳綍浜衣 who can help me衣", "a": "anyone"},
                {"q": "I have ___ (瓒冲) time.", "a": "enough"},
                {"q": "___ (鍏朵粬) students went to the party.", "a": "Other"},
                {"q": "This book is different from ___ (鍏朵粬鐨衣 ones.", "a": "other"},
                {"q": "___ (璁稿套) of the students passed the exam.", "a": "Many"},
                {"q": "___ (涓浜衣 of the cake was left.", "a": "Some"},
                {"q": "___ (娌湁) of them came to the meeting.", "a": "None"},
            ]
        },
    ],
    "八年级上学期": [
        {
            "title": "现在完成时",""
            "questions": [
                {"q": "I ___ ___ (finish) my homework already.", "a": "have finished"},
                {"q": "She ___ ___ (visit) Beijing twice.", "a": "has visited"},
                {"q": "They ___ ___ (live) here for five years.", "a": "have lived"},
                {"q": "He ___ ___ (not see) the movie yet.", "a": "has not seen"},
                {"q": "___ you ever ___ (eat) sushi衣", "a": "Have, eaten"},
                {"q": "We ___ just ___ (come) back from Shanghai.", "a": "have, come"},
                {"q": "She ___ already ___ (read) three books.", "a": "has, read"},
                {"q": "I ___ (know) him since 2010.", "a": "have known"},
                {"q": "He ___ (study) English for six years.", "a": "has studied"},
                {"q": "___ she ___ (finish) her work yet衣", "a": "Has, finished"},
                {"q": "They ___ never ___ (be) to the Great Wall.", "a": "have, been"},
                {"q": "My father ___ (work) here since 2015.", "a": "has worked"},
                {"q": "I ___ (not hear) from him recently.", "a": "have not heard"},
                {"q": "___ you ___ (see) the new film yet衣", "a": "Have, seen"},
                {"q": "She ___ just ___ (leave) the office.", "a": "has, left"},
                {"q": "We ___ already ___ (have) lunch.", "a": "have, had"},
                {"q": "He ___ ___ (lose) his key.", "a": "has lost"},
                {"q": "How long ___ you ___ (live) here衣", "a": "have, lived"},
                {"q": "She ___ (be) a teacher since 2018.", "a": "has been"},
                {"q": "I ___ ___ (learn) a lot from this book.", "a": "have learned"},
                # 现在完成时 填充目录(30题
                {"q": "I ___ ___ (read) this book three times.", "a": "have read"},
                {"q": "She ___ ___ (go) to Shanghai.", "a": "has gone"},
                {"q": "We ___ ___ (live) here since 2015.", "a": "have lived"},
                {"q": "He ___ ___ (not finish) his homework yet.", "a": "has not finished"},
                {"q": "___ you ever ___ (travel) abroad衣", "a": "Have, traveled"},
                {"q": "I ___ just ___ (eat) breakfast.", "a": "have, eaten"},
                {"q": "She ___ already ___ (leave) for Beijing.", "a": "has, left"},
                {"q": "I ___ (know) him for many years.", "a": "have known"},
                {"q": "He ___ (study) English for three years.", "a": "has studied"},
                {"q": "___ she ___ (call) you yet衣", "a": "Has, called"},
                {"q": "They ___ never ___ (be) to Japan.", "a": "have, been"},
                {"q": "My father ___ (work) here since 2010.", "a": "has worked"},
                {"q": "I ___ (not see) him lately.", "a": "have not seen"},
                {"q": "___ you ___ (receive) my letter衣", "a": "Have, received"},
                {"q": "She ___ ___ (buy) a new car.", "a": "has bought"},
                {"q": "We ___ already ___ (have) dinner.", "a": "have, had"},
                {"q": "He ___ ___ (lose) his keys.", "a": "has lost"},
                {"q": "How long ___ you ___ (wait) here衣", "a": "have, waited"},
                {"q": "She ___ (be) a teacher for five years.", "a": "has been"},
                {"q": "I ___ ___ (make) many mistakes.", "a": "have made"},
                {"q": "They ___ ___ (move) to a new house.", "a": "have moved"},
                {"q": "___ he ___ (write) the report衣", "a": "Has, written"},
                {"q": "I ___ never ___ (try) this food before.", "a": "have, never tried"},
                {"q": "She ___ ___ (grow) a lot this year.", "a": "has grown"},
                {"q": "We ___ ___ (meet) before.", "a": "have met"},
                {"q": "He ___ just ___ (arrive).", "a": "has just arrived"},
                {"q": "I ___ (read) that book already.", "a": "have read"},
                {"q": "They ___ ___ (change) a lot.", "a": "have changed"},
                {"q": "She ___ ___ (become) a doctor.", "a": "has become"},
            ]
        },
        {
            "title": "被动语态",""
            "questions": [
                {"q": "English ___ ___ (speak) all over the world.", "a": "is spoken"},
                {"q": "The book ___ ___ (write) by Lu Xun.", "a": "was written"},
                {"q": "Rice ___ ___ (grow) in the south.", "a": "is grown"},
                {"q": "The classroom ___ ___ (clean) every day.", "a": "is cleaned"},
                {"q": "The window ___ ___ (break) by the boy.", "a": "was broken"},
                {"q": "This song ___ often ___ (sing) by children.", "a": "is, sung"},
                {"q": "The letter ___ ___ (send) last week.", "a": "was sent"},
                {"q": "A new hospital ___ ___ (build) next year.", "a": "will be built"},
                {"q": "Tea ___ ___ (produce) in many parts of China.", "a": "is produced"},
                {"q": "The trees ___ ___ (plant) last spring.", "a": "were planted"},
                {"q": "The car ___ ___ (make) in Germany.", "a": "was made"},
                {"q": "Homework ___ ___ (must do) on time.", "a": "must be done"},
                {"q": "The bridge ___ ___ (build) in 2000.", "a": "was built"},
                {"q": "The dog ___ ___ (find) in the garden.", "a": "was found"},
                {"q": "The house ___ ___ (paint) white.", "a": "is painted"},
                {"q": "Many trees ___ ___ (cut) down every year.", "a": "are cut"},
                {"q": "The question ___ ___ (discuss) at the meeting.", "a": "was discussed"},
                {"q": "The work ___ ___ (finish) before 5 pm.", "a": "was finished"},
                {"q": "The meeting ___ ___ (hold) in Room 301.", "a": "was held"},
                {"q": "These books ___ (should return) to the library.", "a": "should be returned"},
                # 琚识姩璇解佽鍏呴理目录衣(30閬衣
                {"q": "English ___ ___ (speak) in many countries.", "a": "is spoken"},
                {"q": "The book ___ ___ (write) by a famous author.", "a": "was written"},
                {"q": "Rice ___ ___ (grow) in the south of China.", "a": "is grown"},
                {"q": "The classroom ___ ___ (clean) every day.", "a": "is cleaned"},
                {"q": "The window ___ ___ (break) by the boy yesterday.", "a": "was broken"},
                {"q": "This song ___ often ___ (sing) by children.", "a": "is, sung"},
                {"q": "The letter ___ ___ (send) last week.", "a": "was sent"},
                {"q": "A new school ___ ___ (build) next year.", "a": "will be built"},
                {"q": "Tea ___ ___ (produce) in many parts of China.", "a": "is produced"},
                {"q": "Many trees ___ ___ (plant) last spring.", "a": "were planted"},
                {"q": "The car ___ ___ (make) in Germany.", "a": "was made"},
                {"q": "Homework ___ ___ (must finish) on time.", "a": "must be finished"},
                {"q": "The bridge ___ ___ (complete) in 2020.", "a": "was completed"},
                {"q": "The dog ___ ___ (find) in the park.", "a": "was found"},
                {"q": "The house ___ ___ (paint) white.", "a": "is painted"},
                {"q": "Many trees ___ ___ (cut) down every year.", "a": "are cut"},
                {"q": "The question ___ ___ (discuss) at the meeting.", "a": "was discussed"},
                {"q": "The work ___ ___ (finish) before 5 pm.", "a": "was finished"},
                {"q": "The meeting ___ ___ (hold) in Room 301.", "a": "was held"},
                {"q": "These photos ___ ___ (take) last summer.", "a": "were taken"},
                {"q": "The movie ___ ___ (watch) by millions of people.", "a": "was watched"},
                {"q": "The problem ___ ___ (solve) tomorrow.", "a": "will be solved"},
                {"q": "The song ___ ___ (like) by many young people.", "a": "is liked"},
                {"q": "The food ___ ___ (eat) by the children.", "a": "was eaten"},
                {"q": "The story ___ ___ (tell) by my grandmother.", "a": "was told"},
                {"q": "English ___ ___ (teach) in our school.", "a": "is taught"},
                {"q": "The room ___ ___ (not use) now.", "a": "is not used"},
                {"q": "The flowers ___ ___ (water) every day.", "a": "are watered"},
                {"q": "The baby ___ ___ (look) after by her mother.", "a": "is looked"},
            ]
        },
        {
            "title": "情态动词推测",
            "questions": [
                {"q": "The light is on. He ___ be at home. (推断)", "a": "must"},
                {"q": "She has a key. That ___ be her house. (可以判兘)", "a": "could"},
                {"q": "He is not here. He ___ be in the library. (可以判兘)", "a": "may"},
                {"q": "That ___ be true. I don't believe it. (不能彲鑳衣", "a": "can't"},
                {"q": "It ___ rain later. Take an umbrella. (可以判兘)", "a": "might"},
                {"q": "You have worked all day. You ___ be tired. (推断)", "a": "must"},
                {"q": "He is running late. He ___ have missed the bus. (可以判兘)", "a": "may"},
                {"q": "That ___ be John. He is in Beijing now. (不能彲鑳衣", "a": "can't"},
                {"q": "The ground is wet. It ___ have rained last night. (推断)", "a": "must"},
                {"q": "She looks pale. She ___ be sick. (可以判兘)", "a": "might"},
                {"q": "There's someone at the door. Who ___ it be衣 (可以判兘)", "a": "could"},
                {"q": "I'm not sure, but she ___ be at the gym. (可以判兘)", "a": "may"},
                {"q": "He ___ be serious. That's a joke, right衣 (不能彲鑳衣", "a": "can't"},
                {"q": "They've been driving for hours. They ___ be tired. (推断)", "a": "must"},
                {"q": "She ___ know the answer. She studied very hard. (推断)", "a": "must"},
                # 情态动词推测琛厖棰樼洰 (35閬衣
                {"q": "The light is on. He ___ be at home. (推断)", "a": "must"},
                {"q": "She has a key. That ___ be her house. (可以判兘)", "a": "could"},
                {"q": "He is not here. He ___ be in the library. (可以判兘)", "a": "may"},
                {"q": "That ___ be true. I don't believe it. (不能彲鑳衣", "a": "can't"},
                {"q": "It ___ rain later. Take an umbrella. (可以判兘)", "a": "might"},
                {"q": "You have worked all day. You ___ be tired. (推断)", "a": "must"},
                {"q": "He is running late. He ___ have missed the bus. (可以判兘)", "a": "may"},
                {"q": "That ___ be John. He is in Beijing now. (不能彲鑳衣", "a": "can't"},
                {"q": "The ground is wet. It ___ have rained last night. (推断)", "a": "must"},
                {"q": "She looks pale. She ___ be sick. (可以判兘)", "a": "might"},
                {"q": "There's someone at the door. Who ___ it be衣 (可以判兘)", "a": "could"},
                {"q": "I'm not sure, but she ___ be at the gym. (可以判兘)", "a": "may"},
                {"q": "He ___ be serious. That's a joke, right衣 (不能彲鑳衣", "a": "can't"},
                {"q": "They've been driving for hours. They ___ be tired. (推断)", "a": "must"},
                {"q": "He is very smart. He ___ pass the exam. (可以判兘)", "a": "should"},
                {"q": "The sky is dark. It ___ rain soon. (可以判兘)", "a": "might"},
                {"q": "She didn't eat breakfast. She ___ be hungry. (可以判兘)", "a": "might"},
                {"q": "He has a lot of money. He ___ afford it. (推断)", "a": "can"},
                {"q": "The restaurant is closed. It ___ be open now. (不能彲鑳衣", "a": "can't"},
                {"q": "She is a doctor. She ___ help the patient. (推断)", "a": "can"},
                {"q": "He didn't study. He ___ pass the test. (可以判兘)", "a": "might not"},
                {"q": "The road is wet. It ___ rained last night. (推断)", "a": "must have"},
                {"q": "He is laughing. He ___ heard the joke. (推断)", "a": "must have"},
                {"q": "She looks happy. She ___ won the game. (推断)", "a": "must have"},
                {"q": "He is not answering. He ___ be sleeping. (可以判兘)", "a": "might be"},
                {"q": "The light is off. He ___ be sleeping. (推断)", "a": "must be"},
                {"q": "She has a fever. She ___ be ill. (推断)", "a": "must be"},
                {"q": "He is laughing. He ___ be joking. (可以判兘)", "a": "must be"},
                {"q": "They are not here. They ___ left. (推断)", "a": "must have"},
                {"q": "The door is locked. Nobody ___ be inside. (推断)", "a": "can"},
                {"q": "She didn't come to school. She ___ be sick. (可以判兘)", "a": "might"},
                {"q": "He looks tired. He ___ worked all night. (推断)", "a": "must have"},
                {"q": "The test is easy. Everyone ___ pass it. (推断)", "a": "should"},
                {"q": "She didn't answer the phone. She ___ be busy. (可以判兘)", "a": "might"},
            ]
        },
        {
            "title": "直接引语和间接引语",""
            "questions": [
                {"q": 'He said: "I am tired." He said ___ ___ ___ tired.', "a": "that he was"},
                {"q": 'She said: "I like music." She said ___ ___ ___ music.', "a": "that she liked"},
                {"q": 'He said: "I will come." He said ___ ___ ___ come.', "a": "that he would"},
                {"q": 'She said: "I can swim." She said ___ ___ ___ swim.', "a": "that she could"},
                {"q": 'He asked: "Are you OK衣" He asked ___ ___ ___ OK.', "a": "if I was"},
                {"q": 'She asked: "Do you like it衣" She asked ___ ___ ___ it.', "a": "if I liked"},
                {"q": 'He asked: "Where do you live衣" He asked ___ ___ ___.', "a": "where I lived"},
                {"q": 'She asked: "What is your name衣" She asked ___ ___ ___ was.', "a": "what my name"},
                {"q": 'Tom said: "I am reading." Tom said ___ ___ ___ reading.', "a": "that he was"},
                {"q": 'He said: "I have finished." He said ___ ___ ___ finished.', "a": "that he had"},
                {"q": 'She said: "I was there yesterday." She said ___ ___ ___ there the day before.', "a": "that she was"},
                {"q": '"I bought a car," he said. He said ___ ___ ___ a car.', "a": "that he had bought"},
                {"q": "Mother said: 'Don't run.' Mother told me ___ ___ ___ .", "a": "not to run"},
                {"q": "The teacher said: 'Be quiet.' The teacher told us ___ ___ ___ .", "a": "to be quiet"},
                {"q": 'He said: "I am happy." He said ___ he ___ happy.', "a": "that, was"},
                # 目录存帴寮曡析鍜岄棿鎺紩璇鍏呴理目录衣(35閬衣
                {"q": 'He said: "I am tired." He said ___ ___ ___ tired.', "a": "that he was"},
                {"q": 'She said: "I like music." She said ___ ___ ___ music.', "a": "that she liked"},
                {"q": 'He said: "I will come." He said ___ ___ ___ come.', "a": "that he would"},
                {"q": 'She said: "I can swim." She said ___ ___ ___ swim.', "a": "that she could"},
                {"q": 'He asked: "Are you OK衣" He asked ___ ___ ___ OK.', "a": "if I was"},
                {"q": 'She asked: "Do you like it衣" She asked ___ ___ ___ it.', "a": "if I liked"},
                {"q": 'He asked: "Where do you live衣" He asked ___ ___ ___.', "a": "where I lived"},
                {"q": 'She asked: "What is your name衣" She asked ___ ___ ___ was.', "a": "what my name"},
                {"q": 'Tom said: "I am reading." Tom said ___ ___ ___ reading.', "a": "that he was"},
                {"q": 'He said: "I have finished." He said ___ ___ ___ finished.', "a": "that he had"},
                {"q": 'She said: "I was there yesterday." She said ___ ___ ___ there the day before.', "a": "that she was"},
                {"q": '"I bought a car," he said. He said ___ ___ ___ a car.', "a": "that he had bought"},
                {"q": "Mother said: 'Don't run.' Mother told me ___ ___ ___ .", "a": "not to run"},
                {"q": "The teacher said: 'Be quiet.' The teacher told us ___ ___ ___ .", "a": "to be quiet"},
                {"q": 'He said: "I am happy." He said ___ he ___ happy.', "a": "that, was"},
                {"q": 'He said: "I will go tomorrow." He said he ___ go the next day.', "a": "would"},
                {"q": 'She said: "I saw him yesterday." She said she ___ him the day before.', "a": "had seen"},
                {"q": 'He said: "I am studying." He said he ___ ___ .', "a": "was studying"},
                {"q": 'She said: "I will call you." She said she ___ call me.', "a": "would"},
                {"q": 'He asked: "Did you see Mary?" He asked if I ___ Mary.', "a": "had seen"},
                {"q": 'She asked: "Where will you go?" She asked where I ___ go.', "a": "would"},
                {"q": "He said: \"I don't like it.\" He said he ___ like it.", "a": "didn't"},
                {"q": 'She said: "I can speak English." She said she ___ speak English.', "a": "could"},
                {"q": 'He said: "I must leave." He said he ___ leave.', "a": "had to"},
                {"q": 'She asked: "How are you衣" She asked how I ___ .', "a": "was"},
                {"q": "He asked: \"When did you come?\" He asked when I ___ .", "a": "had came"},
                {"q": "She said: \"I am feeling well.\" She said she ___ feeling well.", "a": "was"},
                {"q": "He said: \"I will be there at 5.\" He said he ___ be there at 5.", "a": "would"},
                {"q": "She said: \"I don't need help.\" She said she ___ need help.", "a": "didn't"},
                {"q": "He asked: \"Are you coming?\" He asked if I ___ coming.", "a": "was"},
                {"q": "She said: \"I want to go.\" She said she ___ to go.", "a": "wanted"},
                {"q": 'The doctor said: "Take this medicine." The doctor told me ___ this medicine.', "a": "to take"},
                {"q": "Mother said: 'Don't play in the street.' Mother told me ___ ___ in the street.", "a": "not to play"},
                {"q": "Father said: 'Come home early.' Father told me ___ home early.", "a": "to come"},
                {"q": "He said: 'Be careful.' He told me ___ ___ .", "a": "to be careful"},
                # 目录存帴寮曡鍜岄棿鎺紩璇鍏呴棰樼洰
                {"q": 'She said: "I will be back tomorrow." She said she ___ be back the next day.', "a": "would"},
                {"q": "Teacher said: 'Open your books.' The teacher told us ___ our books.", "a": "to open"},
            ]
        },
        {
            "title": "过去将来时 (would/was going to)",
            "grade": 8,
            "questions": [
                {"q": "He said he ___ (come) the next day.", "a": "would come"},
                {"q": "She told me she ___ (go) to Shanghai.", "a": "was going to go"},
                {"q": "They promised they ___ (help) us.", "a": "would help"},
                {"q": "I knew he ___ (not agree) with the plan.", "a": "would not agree"},
                {"q": "She asked what ___ (happen) in the future.", "a": "would happen"},
                {"q": "He said he ___ (visit) his grandma that weekend.", "a": "was going to visit"},
                {"q": "I thought I ___ (never forget) that day.", "a": "would never forget"},
                {"q": "Nobody knew when the war ___ (end).", "a": "would end"},
                {"q": "She hoped she ___ (pass) the exam.", "a": "would pass"},
                {"q": "He told me he ___ (buy) a new car.", "a": "was going to buy"},
                {"q": "They believed technology ___ (change) our lives.", "a": "would change"},
                {"q": "I wondered if I ___ (see) him again.", "a": "would see"},
                {"q": "She said she ___ (marry) the next month.", "a": "was going to marry"},
                {"q": "We didn't know where we ___ (spend) the holiday.", "a": "would spend"},
                {"q": "He asked when the meeting ___ (begin).", "a": "would begin"},
                {"q": "I thought it probably ___ (rain) later.", "a": "would rain"},
                {"q": "She promised she ___ (write) to me every week.", "a": "would write"},
                {"q": "They expected the price ___ (fall).", "a": "would fall"},
                {"q": "I was afraid I ___ (be) late.", "a": "was going to be"},
                {"q": "Who knew what ___ (become) of us?", "a": "would become"},
                {"q": "He said he ___ (can) come if he had time.", "a": "could/would be able to"},
                {"q": "I knew she ___ (not give) up easily.", "a": "would not give"},
                {"q": "They planned they ___ (build) a factory there.", "a": "were going to build"},
                {"q": "She imagined she ___ (travel) around the world.", "a": "would travel"},
                {"q": "I asked who ___ (win) the game.", "a": "would win"},
                {"q": "Nobody expected it ___ (be) so difficult.", "a": "would be"},
                {"q": "He hoped the weather ___ (be) fine.", "a": "would be"},
                {"q": "She said she ___ (finish) by Friday.", "a": "would finish"},
                {"q": "I thought everything ___ (work) out.", "a": "would work"},
                {"q": "They believed the team ___ (succeed).", "a": "would succeed"},
                {"q": "He told me he ___ (return) home soon.", "a": "would return / was going to return"},
                {"q": "I worried that I ___ (fail) the test.", "a": "would fail"},
                {"q": "She dreamed she ___ (fly) like a bird.", "a": "would fly"},
                {"q": "We agreed we ___ (meet) again soon.", "a": "would meet"},
                {"q": "I didn't think he ___ (remember) me.", "a": "would remember"},
                {"q": "They predicted the world ___ (need) more energy.", "a": "would need"},
                {"q": "She wished she ___ (know) the answer.", "a": "would know / knew"},
                {"q": "I assumed it ___ (take) about an hour.", "a": "would take"},
                {"q": "Everyone knew he ___ (try) his best.", "a": "would try"},
                {"q": "She mentioned she ___ (move) to a new city.", "a": "was going to move"},
                {"q": "I feared something bad ___ (happen).", "a": "would happen"},
                {"q": "They announced a new school ___ (open).", "a": "would open"},
                {"q": "He confessed he ___ (lie) to me before.", "a": "had lied / would lie"},
                {"q": "We hoped peace ___ (last) forever.", "a": "would last"},
            ]
        },
        {
            "title": "非谓语动词 (动词不定式/to do)",
            "grade": 8,
            "questions": [
                {"q": "I want ___ (go) shopping this weekend.", "a": "to go"},
                {"q": "He decided ___ (buy) a new computer.", "a": "to buy"},
                {"q": "She hopes ___ (see) you again soon.", "a": "to see"},
                {"q": "They plan ___ (visit) the Great Wall.", "a": "to visit"},
                {"q": "It is important ___ (learn) English well.", "a": "to learn"},
                {"q": "He refused ___ (answer) my question.", "a": "to answer"},
                {"q": "She offered ___ (help) me with my homework.", "a": "to help"},
                {"q": "I'd love ___ (join) your party.", "a": "to join"},
                {"q": "He agreed ___ (go) with us.", "a": "to go"},
                {"q": "She seems ___ (know) the answer.", "a": "to know"},
                {"q": "It takes me an hour ___ (get) to school.", "a": "to get"},
                {"q": "He told me ___ (not be) late again.", "a": "not to be"},
                {"q": "The teacher asked us ___ (keep) quiet.", "a": "to keep"},
                {"q": "I was surprised ___ (hear) the news.", "a": "to hear"},
                {"q": "She is too young ___ (drive) a car.", "a": "to drive"},
                {"q": "He is old enough ___ (go) to school alone.", "a": "to go"},
                {"q": "I have something important ___ (tell) you.", "a": "to tell"},
                {"q": "She needs someone ___ (help) her.", "a": "to help"},
                {"q": "He is always the first ___ (come) and last ___ (leave).", "a": "to come, to leave"},
                {"q": "I don't know what ___ (say).", "a": "to say"},
                {"q": "Can you teach me how ___ (swim)?", "a": "to swim"},
                {"q": "She chose ___ (stay) at home rather than go out.", "a": "to stay"},
                {"q": "He pretended ___ (sleep) when I came in.", "a": "to be sleeping / to sleep"},
                {"q": "I prefer ___ (stay) at home on rainy days.", "a": "to stay"},
                {"q": "They invited me ___ (attend) the meeting.", "a": "to attend"},
                {"q": "It is very kind of you ___ (help) me.", "a": "to help"},
                {"q": "She worked hard ___ (pass) the exam.", "a": "to pass"},
                {"q": "He warned me not ___ (believe) strangers.", "a": "to believe"},
                {"q": "I found it difficult ___ (solve) this problem.", "a": "to solve"},
                {"q": "She asked where ___ (buy) this book.", "a": "to buy"},
                {"q": "The question is too hard ___ (answer).", "a": "to answer"},
                {"q": "He encouraged me ___ (try) again.", "a": "to try"},
                {"q": "I saw him ___ (enter) the room.", "a": "enter / enter"},
                {"q": "She made me ___ (do) it again.", "a": "do"},
                {"q": "I heard her ___ (sing) in the next room.", "a": "sing"},
                {"q": "My parents allow me ___ (watch) TV after homework.", "a": "to watch"},
                {"q": "He was seen ___ (cross) the street alone.", "a": "to cross"},
            ]
        },
        {
            "title": "非谓语动词 (动名词/-ing)",
            "grade": 8,
            "questions": [
                {"q": "I enjoy ___ (read) books in my free time.", "a": "reading"},
                {"q": "He gave up ___ (smoke) last year.", "a": "smoking"},
                {"q": "She avoids ___ (go) out alone at night.", "a": "going"},
                {"q": "They finished ___ (clean) the room just now.", "a": "cleaning"},
                {"q": "I suggest ___ (take) a break.", "a": "taking"},
                {"q": "He practices ___ (play) the piano every day.", "a": "playing"},
                {"q": "She minds ___ (open) the window?", "a": "opening"},
                {"q": "I can't help ___ (laugh) when I see him.", "a": "laughing"},
                {"q": "They keep ___ (ask) me the same question.", "a": "asking"},
                {"q": "He admitted ___ (make) a mistake.", "a": "making"},
                {"q": "She considers ___ (study) abroad.", "a": "studying"},
                {"q": "I imagine ___ (live) on a small island.", "a": "living"},
                {"q": "He denied ___ (steal) the money.", "a": "stealing"},
                {"q": "She missed ___ (catch) the early bus.", "a": "missing / having missed"},
                {"q": "They look forward to ___ (see) you again.", "a": "seeing"},
                {"q": "I am used to ___ (get) up early.", "a": "getting"},
                {"q": "He is interested in ___ (learn) Chinese.", "a": "learning"},
                {"q": "She is afraid of ___ (be) alone in the dark.", "a": "being"},
                {"q": "They are excited about ___ (go) on a trip.", "a": "going"},
                {"q": "I apologize for ___ (be) late.", "a": "being"},
                {"q": "He insisted on ___ (pay) for the meal.", "a": "paying"},
                {"q": "She succeeded in ___ (pass) the exam.", "a": "passing"},
                {"q": "I feel like ___ (have) a rest.", "a": "having"},
                {"q": "He spends too much time ___ (play) games.", "a": "playing"},
                {"q": "She has difficulty in ___ (understand) him.", "a": "understanding"},
                {"q": "It is worth ___ (visit) that museum.", "a": "visiting"},
                {"q": "They talked about ___ (move) to a bigger city.", "a": "moving"},
                {"q": "I can't stand ___ (wait) in long lines.", "a": "waiting"},
                {"q": "He regrets ___ (say) those hurtful words.", "a": "saying / having said"},
                {"q": "She dreams of ___ (become) a famous singer.", "a": "becoming"},
                {"q": "Thank you for ___ (come) to my party.", "a": "coming"},
                {"q": "He is busy ___ (prepare) for the exam.", "a": "preparing"},
                {"q": "She stopped ___ (talk) and started working.", "a": "talking"},
                {"q": "I remember ___ (meet) him somewhere before.", "a": "meeting / having met"},
                {"q": "He forgot ___ (lock) the door.", "a": "locking"},
                {"q": "She tried ___ (use) a different method.", "a": "using"},
                {"q": "They started ___ (realize) the importance.", "a": "realizing"},
                {"q": "I need to practice ___ (speak) English more.", "a": "speaking"},
                {"q": "He keeps ___ (improve) himself every day.", "a": "improving"},
                {"q": "She is good at ___ (organize) events.", "a": "organizing"},
                {"q": "They are responsible for ___ (clean) the classroom.", "a": "cleaning"},
                {"q": "I am proud of ___ (win) the competition.", "a": "winning / having won"},
                {"q": "He is capable of ___ (do) great things.", "a": "doing"},
                {"q": "She complained about ___ (have) too much work.", "a": "having"},
            ]
        },
        {
            "title": "构词法 (前缀/后缀)",
            "grade": 8,
            "questions": [
                {"q": "He is very ___ (help) to everyone. (有帮助的)", "a": "helpful"},
                {"q": "The story is really ___ (interest). (有趣的)", "a": "interesting"},
                {"q": "I was ___ (bore) by the movie. (感到无聊)", "a": "bored"},
                {"q": "She showed great ___ (kind) to the old man. (善良)", "a": "kindness"},
                {"q": "It was a ___ (sun) day yesterday. (晴朗的)", "a": "sunny"},
                {"q": "He ___ (happy) agreed to help. (不快乐地→不愿意地)", "a": "unhappily"},
                {"q": "This is ___ (possible) the best restaurant. (可能地)", "a": "possibly"},
                {"q": "She felt ___ (comfort) in the new chair. (舒适的)", "a": "comfortable"},
                {"q": "The ___ (invent) changed the world. (发明家)", "a": "inventor/invention"},
                {"q": "We should protect our ___ (environment). (环境)", "a": "environment"},
                {"q": "He is ___ (known) in his field. (未知的)", "a": "unknown"},
                {"q": "She ___ (like) eating vegetables. (不喜欢)", "a": "dislikes/disliked"},
                {"q": "It was an ___ (forget) experience. (难忘的)", "a": "unforgettable"},
                {"q": "He acted very ___ (brave) in the fire. (勇敢地)", "a": "bravely"},
                {"q": "The ___ (perform) were excellent. (表演者)", "a": "performers"},
                {"q": "She has made great ___ (improve) recently. (进步)", "a": "improvement(s)"},
                {"q": "It is ___ (health) to exercise daily. (健康的)", "a": "healthy"},
                {"q": "He ___ (lead) the team to victory. (领导→带领)", "a": "led"},
                {"q": "The ___ (science) won the Nobel Prize. (科学家)", "a": "scientist"},
                {"q": "She is ___ (true) sorry about the mistake. (真正地)", "a": "truly"},
                {"q": "This is a ___ (wonder) piece of art. (精彩的)", "a": "wonderful"},
                {"q": "He ___ (appearance) suddenly from behind. (出现)", "a": "appeared"},
                {"q": "The ___ (compete) comes from all over the world. (竞争者)", "a": "competitors"},
                {"q": "She showed great ___ (determine) to succeed. (决心)", "a": "determination"},
                {"q": "It was an ___ (usual) experience. (不同寻常的)", "a": "unusual"},
                {"q": "He is ___ (employ) by a big company. (雇佣→受雇于)", "a": "employed"},
                {"q": "The ___ (educate) system needs reform. (教育)", "a": "education"},
                {"q": "She ___ (courage) me to keep trying. (鼓励)", "a": "encouraged"},
                {"q": "It is ___ (legal) to park here. (非法的)", "a": "illegal"},
                {"q": "The government should take ___ (act). (行动)", "a": "action"},
                {"q": "He is ___ (able) to walk after the accident. (残疾的)", "a": "disabled / unable"},
                {"q": "She felt ___ (hope) when she heard the news. (无望的)", "a": "hopeless"},
                {"q": "The ___ (paint) is very famous. (画家)", "a": "painter/painting"},
                {"q": "It was ___ (care) of him to lose the key. (粗心的)", "a": "careless"},
                {"q": "He ___ (agree) with my opinion. (不同意)", "a": "disagreed"},
                {"q": "The ___ (visit) enjoyed their trip. (游客)", "a": "visitors"},
                {"q": "She is ___ (luck) to win the prize. (幸运的)", "a": "lucky"},
                {"q": "It was a ___ (mean) discussion. (有意义的)", "a": "meaningful"},
                {"q": "He ___ (simple) smiled and said nothing. (仅仅)", "a": "simply"},
                {"q": "The ___ (art) drew a beautiful picture. (艺术家)", "a": "artist"},
                {"q": "She is ___ (confidence) about the exam. (自信的)", "a": "confident"},
                {"q": "We must reduce air ___ (pollute). (污染)", "a": "pollution"},
                {"q": "He ___ (safe) reached home. (安全地)", "a": "safely"},
                {"q": "The ___ (library) helped me find the book. (图书管理员)", "a": "librarian"},
                {"q": "She showed great ___ (friend) to newcomers. (友好)", "a": "friendliness/friendship"},
                {"q": "It is ___ (danger) to swim alone. (危险的)", "a": "dangerous"},
                {"q": "He ___ (writer) many popular books. (写作→写了)", "a": "wrote/has written"},
                {"q": "The ___ (own) of the dog is looking for it. (主人)", "a": "owner"},
                {"q": "She ___ (decision) to leave early. (决定→做出决定)", "a": "decided"},
                {"q": "The ___ (translate) did a great job. (翻译者)", "a": "translator"},
                {"q": "He is ___ (patience) with children. (耐心的)", "a": "patient"},
                {"q": "It was a ___ (history) moment. (历史的)", "a": "historical"},
                {"q": "The ___ (music) played beautifully. (音乐家)", "a": "musician"},
                {"q": "She ___ (choice) the red dress. (选择→选中了)", "a": "chose"},
                {"q": "We need more ___ (nature) resources. (自然的)", "a": "natural"},
                {"q": "He is known for his ___ (generous). (慷慨)", "a": "generosity/generousness"},
                {"q": "The ___ (farm) grows vegetables. (农民)", "a": "farmer"},
                {"q": "She ___ (quick) finished the work. (迅速地)", "a": "quickly"},
                {"q": "It was a great ___ (achieve) for her. (成就)", "a": "achievement"},
                {"q": "He ___ (creation) a beautiful painting. (创造→创作了)", "a": "created"},
                {"q": "The ___ (report) wrote a good article. (记者)", "a": "reporter"},
                {"q": "She is ___ (active) involved in charity. (积极地)", "a": "actively"},
                {"q": "It was a ___ (tradition) Chinese festival. (传统的)", "a": "traditional"},
                {"q": "The ___ (govern) visited the school. (州长/政府官员)", "a": "governor/official"},
                {"q": "He ___ (silent) sat in the corner. (沉默地)", "a": "silently"},
            ]
        },
    ],
    "九年级": [
        {
            "title": "定语从句",
            "questions": [
                {"q": "The man ___ is standing there is my teacher.", "a": "who"},
                {"q": "The book ___ I bought yesterday is interesting.", "a": "which"},
                {"q": "This is the house ___ I was born.", "a": "where"},
                {"q": "The girl ___ you met is my sister.", "a": "whom"},
                {"q": "The movie ___ we saw was very boring.", "a": "that"},
                {"q": "The woman ___ lives next door is a doctor.", "a": "who"},
                {"q": "This is the best book ___ I have ever read.", "a": "that"},
                {"q": "The school ___ I studied is very famous.", "a": "where"},
                {"q": "The boy ___ mother is a singer is my classmate.", "a": "whose"},
                {"q": "Do you know the reason ___ he was absent衣", "a": "why"},
                {"q": "I have a friend ___ can speak five languages.", "a": "who"},
                {"q": "The pen ___ you gave me writes well.", "a": "that"},
                {"q": "This is the park ___ we often play.", "a": "where"},
                {"q": "He is the man ___ helped me.", "a": "who"},
                {"q": "The table ___ is made of wood is very strong.", "a": "which"},
                {"q": "I don't like people ___ talk too much.", "a": "who"},
                {"q": "The hotel ___ we stayed was very clean.", "a": "where"},
                {"q": "This is the car ___ color is red.", "a": "whose"},
                {"q": "He is the teacher ___ we respect most.", "a": "whom"},
                {"q": "The city ___ I was born is very beautiful.", "a": "where"},
            ]
        },
        {
            "title": "状语从句",
            "questions": [
                {"q": "I think ___ he is right. (that/if/whether)", "a": "that"},
                {"q": "She said ___ she would come.", "a": "that"},
                {"q": "I don't know ___ he will come or not.", "a": "whether"},
                {"q": "Can you tell me ___ the station is衣", "a": "where"},
                {"q": "He asked me ___ I liked the movie.", "a": "if"},
                {"q": "I wonder ___ she is.", "a": "who"},
                {"q": "Please tell me ___ I should do next.", "a": "what"},
                {"q": "Do you know ___ he lives衣", "a": "where"},
                {"q": "She asked ___ the train had left.", "a": "if"},
                {"q": "I'm sure ___ he will win.", "a": "that"},
                {"q": "He didn't tell me ___ he was late.", "a": "why"},
                {"q": "I remember ___ I put the key.", "a": "where"},
                {"q": "The teacher said ___ practice makes perfect.", "a": "that"},
                {"q": "I don't understand ___ he said.", "a": "what"},
                {"q": "Could you tell me ___ the hospital is衣", "a": "where"},
                {"q": "He asked ___ I could help him.", "a": "if"},
                {"q": "I don't know ___ book this is.", "a": "whose"},
                {"q": "She told me ___ she was leaving.", "a": "that"},
                {"q": "Nobody knows ___ will happen next.", "a": "what"},
                {"q": "He wondered ___ she would say yes.", "a": "whether"},
            ]
        },
        {
            "title": "鐘惰析浠庡彞",
            "questions": [
                {"q": "I will wait ___ you come back. (目录村埌)", "a": "until"},
                {"q": "___ it rains, we will stay at home. (濡傛灉)", "a": "If"},
                {"q": "She was doing her homework ___ I came in. (褰衣..鏃衣", "a": "when"},
                {"q": "___ he is young, he knows a lot. (铏界劧)", "a": "Although"},
                {"q": "I got up early ___ I could catch the first bus. (浠究)", "a": "so that"},
                {"q": "___ you study hard, you will pass the exam. (濡傛灉)", "a": "If"},
                {"q": "He is ___ tired ___ he can't walk. (濡傛验...浠嚦浜衣", "a": "so, that"},
                {"q": "She speaks English ___ she were a native speaker. (濂藉儚)", "a": "as if"},
                {"q": "I didn't go to bed ___ I finished my homework. (目录村埌)", "a": "until"},
                {"q": "___ there is a will, there is a way. (鍝习噷)", "a": "Where"},
                {"q": "Take an umbrella ___ it rains. (浠槻)", "a": "in case"},
                {"q": "She was ___ angry ___ she couldn't speak. (濡傛验...浠嚦浜衣", "a": "so, that"},
                {"q": "___ he was tired, he kept working. (铏界劧)", "a": "Although"},
                {"q": "I'll call you ___ I get there. (涓...尾", "a": "as soon as"},
                {"q": "___ he finished his work, he left. (涓...尾", "a": "As soon as"},
                {"q": "You will succeed ___ you work hard. (可以复论)", "a": "as long as"},
                {"q": "___ the sun rises, the birds start singing. (褰衣", "a": "When"},
                {"q": "We won't go out ___ the rain stops. (目录村埌)", "a": "until"},
                {"q": "___ he was old, he was still active. (铏界劧)", "a": "Although"},
                {"q": "She studies hard ___ she can get good grades. (涓轰簡)", "a": "so that"},
            ]
        },
        {
            "title": "铏氭嫙璇解皵",
            "questions": [
                {"q": "If I ___ (be) you, I would study harder.", "a": "were"},
                {"q": "If I had time, I ___ (go) to the party.", "a": "would go"},
                {"q": "If she knew the answer, she ___ (tell) us.", "a": "would tell"},
                {"q": "If it ___ (rain) tomorrow, we would stay home.", "a": "rained"},
                {"q": "I wish I ___ (can) fly.", "a": "could"},
                {"q": "I wish I ___ (be) taller.", "a": "were"},
                {"q": "If I had money, I ___ (buy) a new car.", "a": "would buy"},
                {"q": "She wishes she ___ (have) a better job.", "a": "had"},
                {"q": "If he ___ (study) harder, he would pass the exam.", "a": "studied"},
                {"q": "I wish it ___ (not rain) so often here.", "a": "didn't rain"},
                {"q": "If I ___ (be) rich, I would travel around the world.", "a": "were"},
                {"q": "He talks as if he ___ (know) everything.", "a": "knew"},
                {"q": "I wish I ___ (have) more free time.", "a": "had"},
                {"q": "If she ___ (come), I would tell her the truth.", "a": "came"},
                {"q": "If I were you, I ___ (accept) the offer.", "a": "would accept"},
                # 铏氭嫙璇琛厖棰樼洰 (35閬衣
                {"q": "If I ___ (have) a million dollars, I would buy a big house.", "a": "had"},
                {"q": "If he ___ (be) here, he would help us.", "a": "were"},
                {"q": "If she ___ (not be) so busy, she would come.", "a": "were not"},
                {"q": "If we ___ (start) earlier, we would not be late.", "a": "had started"},
                {"q": "If it ___ (not rain), we would go to the park.", "a": "did not rain"},
                {"q": "I wish I ___ (know) the answer.", "a": "knew"},
                {"q": "He wishes he ___ (can) speak Japanese.", "a": "could"},
                {"q": "She wishes she ___ (be) a doctor.", "a": "were"},
                {"q": "I wish it ___ (be) sunny today.", "a": "were"},
                {"q": "If I ___ (have) met you earlier, I would have invited you.", "a": "had met"},
                {"q": "If he ___ (study), he would have passed.", "a": "had studied"},
                {"q": "If she ___ (not miss) the bus, she would not have been late.", "a": "had not missed"},
                {"q": "I wish I ___ (not lose) my wallet.", "a": "had not lost"},
                {"q": "He talks as if he ___ (be) a professor.", "a": "were"},
                {"q": "She looks as if she ___ (see) a ghost.", "a": "had seen"},
                {"q": "If I were the president, I ___ (make) better laws.", "a": "would make"},
                {"q": "If it ___ (be) warmer, we would go swimming.", "a": "were"},
                {"q": "I suggest that he ___ (take) a rest.", "a": "take"},
                {"q": "It is important that everyone ___ (be) on time.", "a": "be"},
                {"q": "The doctor suggested that she ___ (not work) so hard.", "a": "not work"},
                {"q": "It is necessary that we ___ (protect) the environment.", "a": "protect"},
                {"q": "If I ___ (can) fly, I would travel around the world.", "a": "could"},
                {"q": "I wish I ___ (have) a magic power.", "a": "had"},
                {"q": "If he ___ (tell) me earlier, I would have helped him.", "a": "had told"},
                {"q": "She behaves as if she ___ (own) the place.", "a": "owned"},
                {"q": "It is recommended that the meeting ___ (postpone).", "a": "be postponed"},
                {"q": "If I ___ (be) taller, I would join the basketball team.", "a": "were"},
                {"q": "I wish I ___ (can) go back in time.", "a": "could"},
                {"q": "If we ___ (have) enough money, we would buy a car.", "a": "had"},
                {"q": "She acts as if she ___ (know) everything.", "a": "knew"},
                {"q": "It is vital that he ___ (arrive) on time.", "a": "arrive"},
                {"q": "If there ___ (be) no water, nothing could live.", "a": "were"},
                {"q": "I wish I ___ (be) more confident.", "a": "were"},
                {"q": "If it ___ (not be) for your help, I would have failed.", "a": "had not been"},
            ]
        },
        {
            "title": "主谓一致",""
            "questions": [
                {"q": "The boy ___ (like) playing basketball.", "a": "likes"},
                {"q": "The students ___ (be) in the classroom.", "a": "are"},
                {"q": "Everyone ___ (have) their own dreams.", "a": "has"},
                {"q": "Either you or he ___ (be) wrong.", "a": "is"},
                {"q": "Neither the teacher nor the students ___ (be) here.", "a": "are"},
                {"q": "There ___ (be) a book and two pens on the desk.", "a": "is"},
                {"q": "The news ___ (be) very exciting.", "a": "is"},
                {"q": "Mathematics ___ (be) my favorite subject.", "a": "is"},
                {"q": "The pair of shoes ___ (be) very expensive.", "a": "is"},
                {"q": "The police ___ (be) looking for the thief.", "a": "are"},
                {"q": "She as well as her friends ___ (be) happy.", "a": "is"},
                {"q": "The population of China ___ (be) very large.", "a": "is"},
                {"q": "Two-thirds of the water ___ (be) polluted.", "a": "is"},
                {"q": "A number of students ___ (be) playing outside.", "a": "are"},
                {"q": "The number of students ___ (be) 50.", "a": "is"},
                {"q": "My family ___ (be) all tall.", "a": "are"},
                {"q": "My family ___ (be) a happy one.", "a": "is"},
                {"q": "___ there any milk in the fridge衣", "a": "Is"},
                {"q": "Both he and I ___ (be) students.", "a": "are"},
                {"q": "Either answer ___ (be) correct.", "a": "is"},
                # 涓昏皳涓鑷琛厖棰樼洰 (30閬衣
                {"q": "Each student ___ (have) a desk.", "a": "has"},
                {"q": "Every teacher and student ___ (be) excited.", "a": "is"},
                {"q": "No one ___ (know) the answer.", "a": "knows"},
                {"q": "Something ___ (be) wrong with the plan.", "a": "is"},
                {"q": "Nothing ___ (matter) to him now.", "a": "matters"},
                {"q": "One of my friends ___ (live) in Beijing.", "a": "lives"},
                {"q": "Many a student ___ (have) failed this exam.", "a": "has"},
                {"q": "All the food ___ (be) eaten.", "a": "was"},
                {"q": "The glasses ___ (be) on the table.", "a": "are"},
                {"q": "Ten dollars ___ (be) too expensive.", "a": "is"},
                {"q": "Two hours ___ (be) enough for this work.", "a": "is"},
                {"q": "There ___ (be) some books and a pencil on the desk.", "a": "are"},
                {"q": "There ___ (be) a pencil and some books on the desk.", "a": "is"},
                {"q": "The United Nations ___ (have) its headquarters in New York.", "a": "has"},
                {"q": "The news ___ (be) encouraging.", "a": "is"},
                {"q": "Physics ___ (be) difficult for me.", "a": "is"},
                {"q": "The United States ___ (be) a big country.", "a": "is"},
                {"q": "Three-fourths of the surface of the earth ___ (be) covered with water.", "a": "is"},
                {"q": "The injured ___ (be) taken to the hospital.", "a": "were"},
                {"q": "The living ___ (have) the right to vote.", "a": "have"},
                {"q": "Half of the students ___ (be) absent today.", "a": "are"},
                {"q": "One and a half hours ___ (have) passed.", "a": "has"},
                {"q": "Neither you nor I ___ (be) right.", "a": "am"},
                {"q": "Not only the teacher but also the students ___ (be) excited.", "a": "are"},
                {"q": "Someone ___ (have) left the light on.", "a": "has"},
                {"q": "Nobody ___ (seem) to understand.", "a": "seems"},
                {"q": "This kind of book ___ (sell) well.", "a": "sells"},
                {"q": "The kind of books ___ (be) valuable.", "a": "are"},
                {"q": "There ___ (be) a lot of furniture in the room.", "a": "is"},
                {"q": "Early to bed and early to rise ___ (make) a man healthy.", "a": "makes"},
                {"q": "The Arabian Nights ___ (be) an interesting story.", "a": "is"},
                {"q": "Tom with his parents ___ (be) going to Japan.", "a": "is"},
                {"q": "The teacher together with the students ___ (be) reading in the library.", "a": "is"},
                {"q": "Each of them ___ (have) a dictionary.", "a": "has"},
                {"q": "Neither of the two answers ___ (be) correct.", "a": "is"},
                {"q": "Either of the plans ___ (be) acceptable.", "a": "is"},
                {"q": "What ___ (be) the news衣", "a": "is"},
                {"q": "Where ___ (be) your glasses衣", "a": "are"},
            ]
        },
    ],
}
# ==================== 鑻辫析作文棰樺簱 ====================
ESSAY_TOPICS = [
    {
        "category": "涓考汉鎴愰暱",
        "topics": [
            {
                "title": "My English Study",
                "requirement": "涓夊勾鐨勫垵涓组法涔犵敓娲诲嵆灏嗙粨鏉燂紝璇蜂互My English Study涓洪理锛岃皥璋堜綘鍦选嫳璇组法涔犱腑鐨勫洶闅俱佹敹鑾峰拰经验銆衣",""
                "requirement_en": "Your junior high school life is coming to an end. Please write about your difficulties, gains and experience in English learning.",
                "hints": ["difficulties", "improvements", "experience/suggestions", "80-100 words"],
                "sample": "My English Study\n\nI have learned English for three years. At first, I found it very difficult to remember new words and understand grammar. I often made mistakes in spelling and pronunciation.\n\nHowever, I didn't give up. I made a study plan and practiced English every day. I listened to English songs, watched English movies and talked with my classmates in English. Gradually, my English improved a lot.\n\nNow I can speak English confidently and communicate with foreigners. I think the key to learning English is hard work and persistence. Where there is a will, there is a way."
            },
            {
                "title": "My Dream",
                "requirement": "姣忎釜浜洪兘鏈夎嚜宸辩殑姊】兂锛岃审浠y Dream涓洪理锛屽啓涓绡囩煭鏂囦粙缁嶄綘鐨勬鎯充互可以婂辑浣曞疄鐜板畠銆衣",""
                "requirement_en": "Everyone has a dream. Write about your dream and how you plan to achieve it.",
                "hints": ["what is your dream", "why", "how to achieve it", "80 words"],
                "sample": "My Dream\n\nEveryone has a dream. My dream is to become an English teacher. I want to help students learn English well and open their eyes to the world.\n\nWhen I was in primary school, my English teacher was very kind and patient. She made English classes interesting and fun. From then on, I decided to be a teacher like her.\n\nTo achieve my dream, I will study hard at English and other subjects. I will go to a good university and learn how to be a good teacher. I believe my dream will come true one day."
            },
            {
                "title": "How to Be a Good Learner",
                "requirement": "涓轰簡鎻愰珮学习鏁堢巼锛岃审浣犱互How to be a good learner衣涓洪理锛屽啓涓绡衣0字左右的英语短文谈谈你的看法。",""
                "requirement_en": "To improve learning efficiency, write a short passage about how to be a good learner.",
                "hints": ["good habits", "study methods", "attitude", "80 words"],
                "sample": "How to Be a Good Learner\n\nAs a good learner, we should have good study habits. First, it's important to plan our time well. We should make a study schedule and follow it. Second, we should preview the lessons before class and review them after class. Third, we should ask questions when we don't understand something.\n\nBesides, we need to develop our interests in learning. Interest is the best teacher. We should also work hard and never give up. Only in this way can we become good learners."
            },
        ]
    },
    {
        "category": "校园生活",
        "topics": [
            {
                "title": "My School Life",
                "requirement": "璇蜂互My School Life涓洪理锛屾弿杩颁綘鐨勬牎鍥释敓娲伙紝鍖呮嫭学习銆佹椿鍔题拰可以嬭皧銆衣",""
                "requirement_en": "Describe your school life, including study, activities and friendship.",
                "hints": ["classes/teachers", "after-school activities", "friends", "80-100 words"],
                "sample": "My School Life\n\nMy school life is colorful and enjoyable. I go to school from Monday to Friday. We have many interesting subjects like English, math and science. My teachers are all kind and helpful.\n\nAfter class, I often play basketball with my classmates. We also have a school library where I can read all kinds of books. On weekends, I sometimes join the school club activities.\n\nI have made many good friends at school. We help each other and share happiness. I love my school life very much."
            },
            {
                "title": "My Favorite Subject",
                "requirement": "鍦目墍鏈夌殑绉戠洰涓紝浣犳渶鍠滄点鍝考竴绉戯紵涓轰粈涔堬紵璇蜂互My Favorite Subject涓洪理鍐欎竴绡囩煭鏂囥衣",""
                "requirement_en": "Which subject do you like best and why衣 Write a short passage.",
                "hints": ["which subject", "reasons", "what you learned", "80 words"],
                "sample": "My Favorite Subject\n\nAmong all the subjects, I like English best. English is a useful language. It is spoken in many countries around the world. If we learn English well, we can communicate with people from different countries.\n\nOur English teacher is very humorous and patient. She always makes the class lively and interesting. We learn English by singing songs, watching videos and playing games.\n\nI think English is not difficult if you put your heart into it. I will keep learning English and try my best to improve it."
            },
        ]
    },
    {
        "category": "鐜量框淇濇姢",
        "topics": [
            {
                "title": "How to Protect the Environment",
                "requirement": "当前环境问题日益严重，以How to Protect the Environment为题，讨论我们应该如何保护环境。",""
                "requirement_en": "Environmental problems are becoming more serious. Write about how to protect the environment.",
                "hints": ["save water/electricity", "reduce waste", "plant trees", "80-100 words"],
                "sample": "How to Protect the Environment\n\nThe environment is very important for all of us. But today, the environment is becoming worse and worse. We must do something to protect it.\n\nFirst, we should save water and electricity in our daily life. Don't forget to turn off the lights when we leave a room. Second, we'd better not use plastic bags. We can use cloth bags instead. Third, we should plant more trees and reduce waste.\n\nIn a word, everyone should play a part in protecting the environment. Let's take action now to make our world a better place."
            },
            {
                "title": "Low-carbon Life",
                "requirement": "浣庣鐢熸椿姝E湪琚型秺鏉秺澶氱殑浜烘帴可以楋紝璇疯皥璋堜綘瀵逛綆纰崇敓娲荤殑鐪嬫硶鍜屽缓璁衣",""
                "requirement_en": "Low-carbon life is becoming popular. Give your opinions and suggestions.",
                "hints": ["what is low-carbon life", "why important", "suggestions", "80 words"],
                "sample": "Low-carbon Life\n\nLow-carbon life means we should try to reduce energy and produce less pollution. It is good for our environment.\n\nThere are many things we can do. First, we can walk or ride a bike instead of taking a car. This can reduce air pollution. Second, we should turn off lights and computers when we don't use them. Third, we can reuse water and save paper.\n\nEveryone can make a difference. Let's start from small things and live a low-carbon life."
            },
        ]
    },
    {
        "category": "绀句細鐑释偣",
        "topics": [
            {
                "title": "The Internet and Our Life",
                "requirement": "浜掕仈设置戝湪鎴戜滑鐨勭敓娲讳腑瓒婃潵瓒婇噸瑕侊紝璇疯皥璋堜簰鑱旂綉鐨勫埄涓庡紛銆衣",""
                "requirement_en": "The Internet is playing an important role in our life. Talk about its advantages and disadvantages.",
                "hints": ["advantages", "disadvantages", "your opinion", "80-100 words"],
                "sample": "The Internet and Our Life\n\nWith the development of technology, the Internet becomes more and more important in our daily life.\n\nOn the one hand, the Internet brings us a lot of benefits. We can get information quickly, study online, shop without leaving home, and communicate with friends far away. It makes our life easier and more colorful.\n\nOn the other hand, the Internet also has some disadvantages. Some students spend too much time on computer games, which is bad for their study and health. There is also some bad information on the Internet.\n\nIn my opinion, we should use the Internet in a proper way. We should make good use of it and stay away from its bad side."
            },
            {
                "title": "My View on Mobile Phones",
                "requirement": "鎵嬫満鍦项潚灏戝勾涓答秺鏉秺鏅析強锛岃审璋堣皥浣犲批涓组法鐢熶娇鐢目墜鏈虹殑鐪嬫硶銆衣",""
                "requirement_en": "Mobile phones are popular among teenagers. Give your opinion on students using mobile phones.",
                "hints": ["reasons for using", "problems", "your suggestion", "80 words"],
                "sample": "My View on Mobile Phones\n\nNowadays, more and more middle school students have mobile phones. I think it has both good and bad sides.\n\nOn the one hand, mobile phones can help us keep in touch with our parents and friends. We can also use them to search for information and learn English.\n\nOn the other hand, some students spend too much time playing games or chatting on the phone. This is bad for their study and health. Also, using phones too much is bad for our eyes.\n\nI think students should use mobile phones wisely. We should only use them when necessary and not let them affect our study."
            },
        ]
    },
    {
        "category": "浼犵粺鏂囧寲",
        "topics": [
            {
                "title": "My Favorite Festival",
                "requirement": "璇蜂互My Favorite Festival涓洪理锛屼粙缁嶄綘鏈鍠滄点鐨勪紶缁熻妭鏃衣",""
                "requirement_en": "Introduce your favorite traditional festival.",
                "hints": ["name of festival", "time", "activities", "reasons", "80 words"],
                "sample": "My Favorite Festival\n\nMy favorite festival is the Spring Festival. It is the most important traditional festival in China. It usually comes in January or February.\n\nBefore the festival, people clean their houses and buy new clothes. On the eve of the festival, family members get together and have a big dinner. We eat dumplings and watch the Spring Festival Gala on TV. Children are very happy because they can get red packets from their parents and grandparents.\n\nI love the Spring Festival because it is a time for family reunion. Everyone is happy and we can enjoy the warm feeling of being together."
            },
            {
                "title": "Chinese Traditional Culture",
                "requirement": "涓组浗鏂囧寲鍗氬绮炬繁锛岃审浠嬬粛涓椤逛綘鏈鍠滄点鐨勪腑鍥戒紶缁熸枃鍖栵紙濡備功娉曘佸壀绾搞佷含鍓瓑锛夈衣",""
                "requirement_en": "Chinese culture is rich and profound. Introduce one traditional culture you like best.",
                "hints": ["what it is", "features", "why you like it", "80-100 words"],
                "sample": "Chinese Traditional Culture\n\nThere are many traditional Chinese cultures, such as paper-cutting, Beijing Opera and Chinese calligraphy. Among them, I like Chinese calligraphy best.\n\nChinese calligraphy is an art of writing Chinese characters with a brush. It has a long history of thousands of years. Practicing calligraphy can make us calm and patient. It is also a good way to understand Chinese culture.\n\nI started to learn calligraphy when I was eight. At first, it was difficult for me to hold the brush well. But with my teacher's help, I have made great progress. Now I can write beautiful Chinese characters. I am proud of our traditional culture."
            },
        ]
    },
    {
        "category": "鍋悍鐢熸椿",
        "topics": [
            {
                "title": "How to Keep Healthy",
                "requirement": "当前学生身体素质逐年下降的现状，以How to Keep Healthy为题，写一篇约80词的短文。谈谈你的看法和建议。",""
                "requirement_en": "Health is very important. Write about how to keep healthy.",
                "hints": ["healthy diet", "exercise", "good habits", "80 words"],
                "sample": "How to Keep Healthy\n\nHealth is very important for everyone. Do you know how to keep healthy衣 Here are some suggestions.\n\nFirst, we should eat healthy food. We need to eat more vegetables and fruits, and eat less junk food. Drinking enough water is also necessary. Second, we should do exercise every day. Running, swimming and playing ball games are good choices. Third, we should have enough sleep and keep a good mood.\n\nIn a word, a healthy lifestyle can help us stay healthy and happy. Let's start from today!"
            },
            {
                "title": "My Hobby",
                "requirement": "姣忎釜浜洪兘鏈夎嚜宸辩殑鐖卞锛岃审浠y Hobby涓洪理锛屼粙缁嶄綘鐨勭埍濂戒互可以婂畠甯~粰浣犵殑濂藉銆衣",""
                "requirement_en": "Everyone has a hobby. Introduce your hobby and the benefits it brings.",
                "hints": ["what your hobby is", "when/how you started", "benefits", "80 words"],
                "sample": "My Hobby\n\nMy hobby is reading books. I started reading when I was six years old. My mother bought me many picture books and I fell in love with them.\n\nReading brings me many benefits. First, reading can open my mind and help me learn more about the world. Second, it improves my English and writing skills. Third, reading is a good way to relax. When I read a good book, I forget all my worries.\n\nI spend about an hour reading every day. I hope I can read more good books in the future."
            },
        ]
    },
    {
        "category": "鍘嗗勾鐪熼理",
        "topics": [
            {
                "title": "How to Keep Healthy (2021真题)",
                "requirement": "当前学生身体素质逐年下降的现状，以How to Keep Healthy为题，写一篇约80词的短文。谈谈你的看法和建议。",""
                "requirement_en": "Students' physical fitness is declining year by year. Write about how to keep healthy.",
                "hints": ["reasons: too much homework, junk food", "suggestions: exercise, balanced diet, enough sleep", "80 words"],
                "sample": "How to Keep Healthy\n\nNowadays students' physical fitness is declining year by year. I think there are some reasons. Students have too much homework to do, so they have little time to have sports. Some students eat too much junk food. That's also bad for their health.\n\nThen, how to keep healthy衣 Here is some useful advice. First, students should do more exercise. Second, students should eat a balanced diet. They should eat more vegetables and fruits, and try to eat less junk food. Finally, enough sleep is also very important."
            },
            {
                "title": "How to Behave Well (2021真题)",
                "requirement": "涓洪厤鍚堟枃鏄庡缓璁炬椿鍔构紝浠ow to Behave Well涓洪理锛屽啓涓绡衣0-80璇嶇殑鑻辫析鐭解枃可以傝禌銆衣",""
                "requirement_en": "Write about how to behave well in public.",
                "hints": ["be on time, no dirty words", "be polite, help others", "obey traffic rules, no littering", "60-80 words"],
                "sample": "How to Behave Well\n\nAs a student, we should behave well. First, I think it's very important to do everything on time and keep promises. Never lie to others or say dirty words. Next, we should be polite to others and ready to help people in need. Then we'd better not talk loudly in public. Don't throw litter or spit about. And remember to obey traffic rules. Finally, learn to work with others. We need good team work in our life."
            },
            {
                "title": "Would You Like to Live in School衣 (2021真题)",
                "requirement": "灏盬ould You Like to Live in School衣杩欎竴璇濋理灞曞紑璋冩煡銆傛牴鎹题鏍煎唴瀹癸紝鐢选嫳璇组啓涓绡囩煭文本眹鎶皟鏌粨鏋溿衣",""
                "requirement_en": "Report the survey results about whether students prefer to live in school or at home.",
                "hints": ["most students: live in school", "reasons: convenience, learn to look after themselves", "some: at home, relax better", "your opinion", "80-100 words"],
                "sample": "Would You Like to Live in School衣\n\nWould you like to live in school衣 We had a survey about it and here's the result. Most students prefer to live in school because they find it convenient to communicate with their classmates. Also, they can learn how to look after themselves in this way.\n\nHowever, some students think living at home is a better choice. The main reason is that they can relax better at home. Besides, they can spend more time with their family members.\n\nAs for me, I'd like to live in school. That's because I can spend more time on study. What's more, it's a wonderful experience to live with other classmates."
            },
            {
                "title": "Once I Was Praised (2022真题)",
                "requirement": "浣犵敤闆惰姳閽卞仛浜嗕竴浠跺緢鏈夋剰涔夌殑浜嬶紝璇风敤鑻辫析鍐欎竴绡囩煭鏂囧悜鏍嫳文本姤鎶曠造銆傚唴瀹瑰寘鎷词簨鎯呯粡杩囧拰涓考汉鎰熷彈銆衣",""
                "requirement_en": "Write about a meaningful thing you did with your pocket money. Include details and your feelings.",
                "hints": ["what you did", "why you did it", "how others reacted", "your feelings", "80-100 words"],
                "sample": "Once I Was Praised\n\nOnce I was praised because I did something meaningful with my pocket money. One day, I happened to know some students in a school were hungry for knowledge but they didn't have enough books. I decided to offer my help. With all the pocket money I saved, I bought some books online, and gave them away to the school. My parents were very happy and praised me when they heard about it. They said I did a meaningful thing. I believe that every little bit helps. I will continue to do what I can to help others."
            },
            {
                "title": "My Weekend Housework (2022真题)",
                                "requirement": "以 Weekend Housework 为题写一篇约80词的短文，谈谈你周末常做哪些活动，并说明你喜欢和不喜欢的家务。",
                "requirement_en": "Write about your weekend housework. Which chores do you like and dislike衣",
                "hints": ["what housework you do", "which you like/dislike", "why", "70 words"],
                "sample": "My Weekend Housework\n\nOn last Saturday morning I got up at about seven o'clock. After breakfast, I went to the store and bought some food for the family. I like doing the shopping. I think it's fun. Then I swept the floor. I didn't do the laundry and the dishes. I don't like doing any washing. In the afternoon I cleaned the yard. After that I folded my clothes and made my bed."
            },
            {
                "title": "The Ways for Students to Relax (2022真题)",
                "requirement": "閽堝批瀛~敓学习时间闀裤佸帇鍔涘鐨勬儏鍐碉紝鐝释骇灏盩he Ways for Students to Relax杩涜格璁选认銆傝审鏍规嵁提示鍐欎竴浠芥眹鎶潗鏂欍衣",""
                "requirement_en": "Write a report about the discussion on how students can relax.",
                "hints": ["Terry's opinion: watch TV, play games, hang out", "your own opinion", "80 words"],
                "sample": "Dear Mr. Griffin,\n\nRecently I have had a discussion about The Ways for Students to Relax with Terry, a student from Class One Grade Two. In his opinion, the best ways are watching TV and playing computer games. He also believes that sometimes hanging out with friends isn't a bad way.\n\nHowever, I'm not quite agreeable with him. I think listening to music and playing sports are good ways because they can help us keep healthy. I often play ping-pong after class and I find it really helpful to both my health and my study. Besides, I think chatting with our friends isn't a bad way. It can help me get on better with my friends."
            },
            {
                "title": "My Future Plan (2023鐪熼理)",
                "requirement": "高中毕业后你将回母校看望老师。请你以Future Plan为题，写一篇100字左右的作文，谈谈为教育事业奉献力量的决心。",""
                "requirement_en": "You decide to become a middle school teacher. Write about your future plan and determination.",
                "hints": ["what you want to be", "reasons", "your determination", "100 words"],
                "sample": "My Future Plan\n\nI decided to be a middle teacher after college. There are many reasons contribute to this decision. First, when I was a little boy, I have been dreaming of being a teacher. It seemed so fascinate to me and I hope I can make my dream come true. And, I like so much to be with middle school students. Most of the students at that age are full of youthful spirit and I am sure their passion would pass to me.\n\nThe most important reason is that our country needs plenty of teachers. I am ready to be a teacher and hope all the persons with lofty ideals may dedicate themselves to this meaningful career."
            },
            {
                "title": "I Believe I Can Fly (2023鐪熼理)",
                "requirement": "鐢辨瓕鏇睮 Believe I Can Fly鐨勬劅鎯冲紩鍑猴紝浠 Believe I Can Fly涓洪理锛屽弬鍔犺嫳文本潅蹇楃殑寰佹枃姣旇禌銆衣",""
                "requirement_en": "Write about how the song 'I Believe I Can Fly' inspires you.",
                "hints": ["confidence is important", "dreams keep us going", "your opinion", "80 words"],
                "sample": "I Believe I Can Fly\n\nI Believe I Can Fly is a nice song by R.Kelly. This song tells us that confidence is very important. When a person has confidence, he believes in himself. He believes that he can and will succeed, and this gives him the courage to try new things. Dreams and confidence are what keep us going on in the face of difficulties. No one can achieve success without them. If you believe you can fly, then you can really fly someday. I think I will never give up whenever I meet any difficulties. I'll remember confidence is the promise for achieving success."
            },
            {
                "title": "Ideal Jobs Survey (2024鐪熼理)",
                "requirement": "閽堝批鐞嗘兂鍜岃亴涓氬彂灞曞仛浜嗕竴娆皟鏌傝审浠H灏忕粍鍐欎竴绡囪嫳鏂囩煭鏂囧悜鏍姤鎶曠造銆衣",""
                "requirement_en": "Write a report about the survey on students' ideal jobs.",
                "hints": ["Mary: fashion designer", "Kate: gardener", "Mike: writer", "Tom: cook", "you: your ideal job", "80 words"],
                "sample": "Ideal Jobs Survey\n\nRecently we did a survey in our class in order to learn about students' ideal jobs. Here's a report about my group members' ideas. Mary wants to be a fashion designer because she likes beautiful clothes and is good at drawing. Kate wants to be a gardener, she loves plants, and she wants to make the cities better. Mike would like to be a writer. He'd like to share his wonderful stories with others. Tom would like to be a cook. He'd like to cook delicious food for others. I would like to be a policeman. I want to protect the people safe. Hopefully everyone can realize their dreams in the future."
            },
            {
                "title": "Tomorrow's Life (2024鐪熼理)",
                "requirement": "鏈句懆鑻辫析璇惧法涔犲洿缁曚富棰楾omorrow's Life灞曞紑銆傝审浣犳牴鎹推彁绀轰粠鐢熸椿銆佸伐浣溿佸判搴释瓑鏂归潰锛屽啓涓绡囪嫳璇类綔鏂囥衣",""
                "requirement_en": "Describe your vision of tomorrow's life - life, work and family in the future.",
                "hints": ["life in the future", "work", "family", "your imagination", "80-100 words"],
                "sample": "Tomorrow's Life\n\nWhat will life be like tomorrow衣 I think it will be very different from today. In the future, we will have robots to help us with housework. They can clean rooms, cook meals and even look after old people. People will work at home with computers, so there will be less traffic on the roads. Families will spend more time together. We will travel to other planets for holidays. The environment will be better because people will use clean energy. I believe tomorrow's life will be more convenient and enjoyable. I am looking forward to it."
            },
            {
                "title": "Traffic Safety Proposal (2024真题)",
                "requirement": "假定你是班长。前几天班上有一名同学因交通事故受伤。现请你以班会形式写一份安全倡议书，注意交通安全。",
                "requirement_en": "Write a proposal about traffic safety after a classmate was hit by a car.",
                "hints": ["background: accident", "current traffic problems", "call for action", "80-100 words"],
                "sample": "Dear Classmates,\n\nThe other day, one of our classmates was knocked down by a car at the crossing. It is not the car driver but the student himself who is to blame because he ran through the red light.\n\nRecords show that an increasing number of people die in traffic accidents every year, most of whom walk regardless of speed limits, talk and laugh while riding bikes and cross the road without noticing the traffic lights. This will not only do harm to their own lives but also put other people in danger.\n\nOnly when everybody is aware of the problem can we be safe on roads."
            },
            {
                "title": "Don't Keep Your Worries (2025鐪熼理)",
                "requirement": "鐝类笂瀵瑰埆鎶婄儲鎭奸椃鍦题績閲屽仛浜嗕竴娆皟鏌紝词根牴鎹题皟鏌粨鏋滃啓涓绡囨姤鍛娿衣0%娲诲姩灏戜綋璐题樊锛衣0%浣滀笟澶氬法涓氬帇鍔涘锛衣0%鐖舵瘝瑕佹眰涓矡閫氬皯銆衣",""
                "requirement_en": "Write a report about a survey on students' worries and suggestions to solve them.",
                "hints": ["20%: weak health, no exercise", "50%: too much homework", "30%: strict parents", "your advice", "80 words"],
                "sample": "Don't Keep Your Worries\n\nOur class has made a survey about students' worries. About fifty percent of the students in our class are worried about their homework and studies. They feel too much stress. About thirty percent of the students think their parents are too strict with them. They don't often talk with their parents. The other twenty percent say they are weak in health. They complain that they have almost no time for their hobbies or exercise.\n\nSo I hope that our teachers will give us less homework. And I advise our parents to allow us to spend some time doing outdoor activities. In this way, we will be happier.",
            },
            {
                "title": "Sports Make Us Better (2024湖南真题)",
                "requirement": "学校英文报以“Sports Make Us Better”为题征文。请你结合自身经历，写一篇短文投稿，内容包括：(1) 你喜欢的运动及原因；(2) 运动带给你的好处。",
                "requirement_en": "Write a short article titled \"Sports Make Us Better\" for your school newspaper, including: (1) your favorite sport and why; (2) the benefits sports bring you.",
                "hints": ["favorite sport", "reasons why you like it", "benefits: health, friendship, confidence", "80-100 words"],
                "sample": "Sports Make Us Better\\n\\nSports play an important role in my life. My favorite sport is basketball, which I have been playing for three years.\\n\\nI love basketball for several reasons. Firstly, it helps me build a strong body. After playing basketball regularly, I feel more energetic and hardly get sick. Secondly, I have made many friends through this sport. We encourage each other and work together as a team. Most importantly, basketball has taught me the value of cooperation and perseverance. When our team faces difficulties, we never give up easily.\\n\\nIn conclusion, sports not only improve our physical health but also shape our character. Let's do sports and become better!"
            },
            {
                "title": "Mistakes — Steps Toward Success",
                "requirement": "每个人都会犯错误。请你以“Mistakes — Steps Toward Success”为题，根据以下要点提示，用英语写一篇短文：1. 讲述你的一次犯错经历；2. 你从中获得的启示。",
                "requirement_en": "Write an essay titled \"Mistakes — Steps Toward Success\" about: 1. an experience when you made a mistake; 2. what you learned from it.",
                "hints": ["your mistake experience", "how you felt", "what lesson you learned", "80-100 words"],
                "sample": "Mistakes — Steps Toward Success\\n\\nEveryone makes mistakes. I once made a big mistake in an English speech contest. Because I didn't prepare well enough, I forgot my lines on the stage. I stood there feeling embarrassed, with my face turning red.\\n\\nHowever, this mistake taught me a valuable lesson. I realized that success comes from thorough preparation and practice. Since then, I always spend more time preparing for important events. More importantly, I learned that making mistakes is not terrible — what matters is whether we can learn from them and become better.\\n\\nAs the saying goes, \"Failure is the mother of success.\" Mistakes are actually steps toward success if we face them bravely."
            },
            {
                "title": "How to Keep Safe Online",
                "requirement": "随着互联网的发展，网络安全变得越来越重要。请你以“How to Keep Safe Online”为题，写一篇英语短文，介绍如何保护自己的网络安全。内容包括：1. 不透露个人信息；2. 不随意添加陌生人；3. 遇到问题寻求帮助。",
                "requirement_en": "Write an essay titled \"How to Keep Safe Online\" about internet safety. Include: 1. Don't reveal personal information; 2. Don't add strangers casually; 3. Seek help when facing problems.",
                "hints": ["personal information protection", "stranger danger", "ask parents or teachers for help", "80-100 words"],
                "sample": "How to Keep Safe Online\\n\\nWith the rapid development of the Internet, online safety has become increasingly important. Here are some suggestions on how to keep safe online.\\n\\nFirst of all, we should never reveal personal information such as our name, address, phone number or school name to strangers online. This information could be used by bad people to harm us. Secondly, we must be careful about adding strangers as friends on social media. Not everyone online is who they claim to be. Thirdly, if we meet anything strange or uncomfortable online, we should tell our parents or teachers immediately instead of trying to solve it ourselves.\\n\\nIn short, let's keep safety in mind while enjoying the convenience of the Internet."
            },
            {
                "title": "Thank You, My Teacher",
                "requirement": "在你的学习生涯中，一定有一位老师对你影响很大。请你以“Thank You, My Teacher”为题，用英语写一篇短文，内容包括：1. 这位老师是谁；2. 他/她对你的帮助或影响；3. 你的感谢之情。",
                "requirement_en": "Write an essay titled \"Thank You, My Teacher\" about a teacher who influenced you greatly. Include: 1. Who the teacher is; 2. How he/she helped or influenced you; 3. Your gratitude.",
                "hints": ["who is the teacher", "specific help or influence", "express thanks", "80-100 words"],
                "sample": "Thank You, My Teacher\\n\\nAmong all my teachers, Ms. Li, my English teacher, has influenced me the most. I would like to express my sincere thanks to her.\\n\\nWhen I first entered junior high school, my English was very poor and I almost lost confidence. It was Ms. Li who encouraged me patiently. She spent extra time helping me with my pronunciation and grammar after class. Whenever I made progress, she praised me warmly. Thanks to her help, my English improved greatly and I even won the first prize in the English speech contest last term.\\n\\nDear Ms. Li, thank you for your kindness and patience. You are not only a teacher but also a friend who lights up my path of learning!"
            },
            {
                "title": "The Value of Reading",
                "requirement": "阅读对人成长很重要。请你以“The Value of Reading”为题，根据以下要点提示，写一篇英语短文：1. 阅读的好处（至少两点）；2. 你的阅读习惯；3. 倡议大家多读书。",
                "requirement_en": "Write an essay titled \"The Value of Reading\" about: 1. Benefits of reading (at least two points); 2. Your reading habits; 3. Call on everyone to read more.",
                "hints": ["benefits: knowledge, imagination, vocabulary", "your reading habits", "encourage others to read", "80-100 words"],
                "sample": "The Value of Reading\\n\\nReading is one of the most valuable habits we can develop. In my opinion, reading benefits us in many ways.\\n\\nFirstly, reading opens a window to the world. Through books, we can learn about different cultures, histories and ideas without traveling far. Secondly, reading improves our language skills and enriches our vocabulary. The more we read, the better we write and speak. Personally, I read at least half an hour every day before going to bed. I enjoy both storybooks and science magazines.\\n\\nIn conclusion, reading is like a good friend who always accompanies us. Let's develop the habit of reading and make it a part of our daily life!"
            },
            {
                "title": "Let's Protect Animals",
                "requirement": "动物是人类的朋友，但很多动物正面临生存危机。请你以“Let's Protect Animals”为题，写一篇英语短文，呼吁大家保护动物。要点：1. 动物面临的困境；2. 保护动物的重要性；3. 我们应该如何做。",
                "requirement_en": "Write an essay titled \"Let's Protect Animals\" calling on people to protect animals. Include: 1. Difficulties animals face; 2. Importance of protecting them; 3. What we should do.",
                "hints": ["animals in danger", "why important to protect", "what we can do", "80-100 words"],
                "sample": "Let's Protect Animals\\n\\nAnimals are our friends on this planet. However, many animals are facing serious survival crises nowadays. Some species have even disappeared from the earth forever.\\n\\nProtecting animals is extremely important. Animals help maintain the balance of nature. If one species disappears, it may affect the whole ecosystem. Besides, animals bring color and joy to our world. Imagine a world without birds singing or fish swimming — how boring it would be!\\n\\nSo what can we do? First, we should refuse to buy products made from wild animals. Second, we can protect their living environment by planting more trees and reducing pollution. Finally, let's spread the knowledge of animal protection to people around us. Let's act now to protect our animal friends!"
            },
            {
                "title": "Volunteer Work",
                "requirement": "志愿服务不仅能帮助他人，也能让自己成长。请以“Volunteer Work”为题，写一篇英语短文，内容包括：1. 你做过或想做的志愿活动；2. 志愿服务的好处；3. 号召更多人参与。",
                "requirement_en": "Write an essay titled \"Volunteer Work\". Include: 1. Volunteer activities you have done or want to do; 2. The benefits of volunteering; 3. Call on more people to participate.",
                "hints": ["volunteer activity examples", "benefits: helping others, self-growth", "call for participation", "80-100 words"],
                "sample": "Volunteer Work\\n\\nVolunteering is meaningful and rewarding. Last summer vacation, I volunteered at our city library. My job was to help readers find books and keep the books in order. Although the work was tiring, I felt very happy when I saw the satisfied smiles on people's faces.\\n\\nVolunteer work brings many benefits. On one hand, we can help those in need and make our society warmer. On the other hand, we can learn new skills, make new friends and gain valuable experiences through volunteering. These things cannot be learned from textbooks.\\n\\nI strongly encourage everyone to try volunteer work. Even small acts of kindness can make a big difference. Let's contribute our share to building a better world!"
            },
            {
                "title": "Chinese Food",
                "requirement": "中国美食闻名世界。请你以“Chinese Food”为题，用英语写一篇短文，向外国朋友介绍一种你喜欢的中国食物。内容包括：1. 这种食物是什么；2. 它的特点（原料/做法/味道等）；3. 为什么你喜欢它。",
                "requirement_en": "Write an essay titled \"Chinese Food\" introducing a Chinese dish you like to foreign friends. Include: 1. What the food is; 2. Its features (ingredients/method/taste); 3. Why you like it.",
                "hints": ["name of the food", "ingredients, how to make, taste", "why you like it", "80-100 words"],
                "sample": "Chinese Food\\n\\nChina has a long history of delicious food culture. Among all kinds of Chinese dishes, dumplings (jiaozi) are my favorite.\\n\\nDumplings are a traditional Chinese food, especially popular during the Spring Festival. They are usually made of thin flour wrappers filled with meat and vegetables. There are various ways to cook them, including boiling, steaming and frying. Dumplings taste delicious with their juicy filling and soft skin.\\n\\nThe reason why I love dumplings is not only their wonderful taste but also the special meaning behind them. In Chinese culture, dumplings symbolize family reunion and good fortune. Every time I eat dumplings made by my grandmother, I feel the warmth of family love. If you come to China, don't forget to try dumplings!"
            },
            {
                "title": "Traffic Safety",
                "requirement": "交通安全关系到每个人的生命安全。请你以“Traffic Safety”为题，写一篇英语短文，倡导文明出行。内容包括：1. 交通安全的重要性；2. 常见的交通违法行为；3. 安全出行的建议（至少两条）。",
                "requirement_en": "Write an essay titled \"Traffic Safety\" promoting safe travel. Include: 1. Importance of traffic safety; 2. Common traffic violations; 3. At least two safety suggestions.",
                "hints": ["importance of safety", "running red lights, using phones while riding", "follow rules, wear helmets", "80-100 words"],
                "sample": "Traffic Safety\\n\\nTraffic safety is closely related to everyone's life. Every year, thousands of people get injured or even lose their lives in traffic accidents. Therefore, it is crucial for us to pay attention to traffic safety.\\n\\nNowadays, some traffic violations are still common. Some people run red lights, some ride electric bikes against the traffic flow, and some even use mobile phones while driving or riding. These behaviors are extremely dangerous!\\n\\nTo ensure our safety, we should always follow traffic rules. First, obey the traffic lights and signs. Never run red lights. Second, when riding electric bikes, we should wear helmets and never carry too many passengers. Third, pedestrians should use crosswalks when crossing roads. Let's all be responsible travelers and keep ourselves safe!"
            },
            {
                "title": "My Hometown",
                "requirement": "每个人都有自己的家乡，家乡承载着我们美好的回忆。请你以“My Hometown”为题，写一篇英语短文，介绍一下你的家乡。要点：1. 家乡的位置和环境；2. 家乡的特色（风景、美食、名人等）；3. 你对家乡的感情。",
                "requirement_en": "Write an essay titled \"My Hometown\" introducing your hometown. Include: 1. Location and environment; 2. Special features (scenery, food, famous people); 3. Your feelings about hometown.",
                "hints": ["where is your hometown", "special scenery, food, people", "love and pride", "80-100 words"],
                "sample": "My Hometown\\n\\nMy hometown is a beautiful city located in the south of Hunan Province. It is surrounded by green mountains and clear rivers, with fresh air and pleasant weather all year round.\\n\\nThere are many special things about my hometown. The most famous scenic spot is Dongjiang Lake, whose water is so clear that it looks like a mirror. Our local food is also worth mentioning — especially the spicy fish and fermented tofu, which attract visitors from all over the country. Besides, my hometown has produced many talented people in different fields.\\n\\nI love my hometown deeply. It is not only a beautiful place but also where I grew up with countless warm memories. No matter where I go, my hometown will always hold a special place in my heart. Welcome to my hometown!"
            },
            {
                "title": "Teamwork",
                "requirement": "团队合作在我们的学习和生活中非常重要。请你以“Teamwork”为题，写一篇英语短文，谈一谈你对团队合作的看法。要点：1. 团队合作的重要性；2. 你的一次团队合作经历；3. 从中学到了什么。",
                "requirement_en": "Write an essay titled \"Teamwork\" sharing your views. Include: 1. Importance of teamwork; 2. An experience of working in a team; 3. What you learned.",
                "hints": ["why teamwork matters", "your team experience", "lessons learned", "80-100 words"],
                "sample": "Teamwork\\n\\nThere is a famous saying: \"Many hands make light work.\" Teamwork plays an essential role in our study and daily life.\\n\\nLast month, our class took part in the school sports meeting relay race. At first, we didn't cooperate well and fell behind. However, we didn't blame each other. Instead, we practiced together during breaks, helping teammates who ran slower improve their skills. On the final race day, we passed the baton smoothly and won the first prize!\\n\\nFrom this experience, I deeply understood that teamwork is not just about individual ability, but about trusting and supporting each other. Everyone has strengths and weaknesses. When we work as a team, we can achieve much more than working alone. Let's value teamwork!"
            },
            {
                "title": "A Trip to Zhangjiajie",
                "requirement": "张家界是湖南著名的旅游景点。假设你上个月和家人去了张家界旅游。请以“A Trip to Zhangjiajie”为题，写一篇英语短文，介绍你的旅行经历。要点：1. 时间和交通方式；2. 游览的主要景点；3. 你的感受。",
                "requirement_en": "Write an essay titled \"A Trip to Zhangjiajie\" about your trip there last month with family. Include: 1. Time and transport; 2. Main attractions visited; 3. Your feelings.",
                "hints": ["when and how you went", "Tianmen Mountain, Avatar mountains, etc.", "feelings and thoughts", "80-100 words"],
                "sample": "A Trip to Zhangjiajie\\n\\nLast month, I went on a memorable trip to Zhangjiajie with my parents during the National Day holiday. We took a high-speed train and arrived there in about three hours.\\n\\nZhangjiajie is truly amazing! We visited Tianmen Mountain first. Standing on the glass skywalk, I felt as if I were walking in the clouds. Then we explored the Yuanjiajie Scenic Area, where the towering sandstone pillars reminded me of the movie \"Avatar.\" The scenery was breathtaking! We also took the world-famous Bailong Elevator, which is the tallest outdoor elevator in the world.\\n\\nThis trip was unforgettable. I was not only impressed by the magnificent natural beauty but also proud of the wonders of my homeland. I hope to visit Zhangjiajie again in the future!"
            },
            {
                "title": "My Opinion on Homework",
                "requirement": "关于家庭作业，同学们有不同的看法。有人认为作业有助于巩固知识，也有人认为作业太多会影响身心健康。请你以“My Opinion on Homework”为题，写一篇英语短文，谈谈你的看法。要点：1. 不同人的观点；2. 你的观点和理由；3. 给老师的建议。",
                "requirement_en": "Write an essay titled \"My Opinion on Homework\". Include: 1. Different viewpoints; 2. Your opinion and reasons; 3. Suggestions for teachers.",
                "hints": ["different opinions on homework", "your view and reasons", "suggestions for teachers", "80-100 words"],
                "sample": "My Opinion on Homework\\n\\nHomework has always been a hot topic among students. Some students believe homework helps consolidate knowledge, while others think too much homework affects physical and mental health.\\n\\nIn my opinion, homework is necessary but the amount matters. Proper homework can help us review what we have learned in class and develop good study habits. However, excessive homework leaves us no time for hobbies, exercise or rest. As a result, we may feel stressed and tired, which is not good for our growth.\\n\\nTherefore, I would like to offer some suggestions to teachers. First, please assign homework of appropriate quantity and quality. Second, vary the types of homework — not just exercises but also creative tasks like making posters or shooting videos. I believe reasonable homework will benefit us more!"
            },
            {
                "title": "Saving Water",
                "requirement": "水是生命之源，但水资源日益紧缺。请你以“Saving Water”为题，写一篇英语短文，号召大家节约用水。要点：1. 水资源现状；2. 节约用水的重要性；3. 日常生活中的节水方法（至少三条）。",
                "requirement_en": "Write an essay titled \"Saving Water\" calling on people to save water. Include: 1. Current water situation; 2. Importance of saving water; 3. At least three ways to save water in daily life.",
                "hints": ["water shortage problem", "why save water", "turn off tap, reuse water, fix leaks", "80-100 words"],
                "sample": "Saving Water\\n\\nWater is the source of life. However, freshwater resources on our planet are very limited and many places are facing serious water shortage.\\n\\nSaving water is extremely important. Without water, there would be no life on Earth. Every drop of water is precious. Wasting water today means our children may face an even worse water crisis tomorrow.\\n\\nHere are some simple ways to save water in our daily lives. First, turn off the tap tightly after washing hands or brushing teeth. Second, reuse water — for example, use the water from washing rice or vegetables to water flowers. Third, take shorter showers instead of baths. Fourth, fix dripping taps promptly. These small actions can make a big difference if everyone does them. Let's start saving water from now on!"
            },
            {
                "title": "My Favorite Season",
                "requirement": "一年有四季，每个季节都有不同的特点。请你以“My Favorite Season”为题，写一篇英语短文，说说你最喜欢的季节。要点：1. 你最喜欢的季节是什么；2. 这个季节的特点（天气、活动、景色等）；3. 你为什么喜欢这个季节。",
                "requirement_en": "Write an essay titled \"My Favorite Season\". Include: 1. Which season you like best; 2. Features of this season (weather, activities, scenery); 3. Why you like it.",
                "hints": ["which season", "weather, activities, scenery", "reasons to love it", "80-100 words"],
                "sample": "My Favorite Season\\n\\nAmong the four seasons, autumn is my favorite.\\n\\nAutumn in Hunan is particularly beautiful. The weather in autumn is cool and comfortable — neither too hot nor too cold. The gentle breeze blows away the summer heat, making people feel refreshed. Golden leaves fall from the trees, painting the ground in beautiful colors. It is also the season of harvest. Farmers are busy gathering crops in the fields, and fruit markets are full of fresh oranges and persimmons.\\n\\nI love autumn for several reasons. First, the pleasant weather makes it perfect for outdoor activities like hiking and camping. Second, autumn brings the Mid-Autumn Festival, when family members gather to enjoy mooncakes together. Most importantly, autumn reminds us that hard work leads to harvest. That is why autumn will always be my favorite season."
            },
        ]
    },
]
class WordFillWidget(QWidget):
    """单词填空控件 - 自定义输入(LineEdit)"""
    def __init__(self, word, missing_pos, parent=None):
        super().__init__(parent)
        self.word = word
        self.missing_pos = missing_pos
        self.missing_char = word[missing_pos].lower()
        self.user_input = ""
        self.setFixedHeight(120)
        self.setMinimumWidth(600)
        # 甯冨眬
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(0)
        prefix = word[:missing_pos]
        suffix = word[missing_pos+1:]
        font = QFont("微软雅黑", 48, QFont.Bold)
        # 鍓嶇紑
        if prefix:
            lbl = QLabel(prefix)
            lbl.setFont(font)
            lbl.setStyleSheet("color: #333; background: transparent;")
            layout.addWidget(lbl)
        # 输入区域（自定义控件）
        self.input_label = QLabel("_")
        self.input_label.setFont(font)
        self.input_label.setAlignment(Qt.AlignCenter)
        self.input_label.setFixedSize(80, 100)
        self.input_label.setStyleSheet("""
            color: #1cb0f6;
            background: transparent;
            border-bottom: 4px solid #1cb0f6;
            padding-bottom: 2px;
        """)
        self.input_label.setFocusPolicy(Qt.StrongFocus)
        self.input_label.installEventFilter(self)
        layout.addWidget(self.input_label)
        # 鍚庣紑
        if suffix:
            lbl = QLabel(suffix)
            lbl.setFont(font)
            lbl.setStyleSheet("color: #333; background: transparent;")
            layout.addWidget(lbl)
        layout.addStretch()
    def eventFilter(self, obj, event):
        if obj == self.input_label:
            if event.type() == event.KeyPress:
                key = event.key()
                text = event.text().lower()
                # 可以练帴可以楀瓧姣嶈緭鍏衣
                if text and text.isalpha() and len(text) == 1:
                    self.user_input = text
                    self.input_label.setText(text)
                    self.input_label.setStyleSheet("""
                        color: #1cb0f6;
                        background: transparent;
                        border-bottom: 4px solid #1cb0f6;
                    """)
                    return True
                elif key == Qt.Key_Backspace and self.user_input:
                    self.user_input = ""
                    self.input_label.setText("_")
                    self.input_label.setStyleSheet("""
                        color: #cccccc;
                        background: transparent;
                        border-bottom: 4px solid #1cb0f6;
                    """)
                    return True
                else:
                    return True  # 蹇界暐鍏朵粬閿衣
        return super().eventFilter(obj, event)
    def showEvent(self, event):
        super().showEvent(event)
        self.input_label.setFocus()
class PhraseFillWidget(QWidget):
    """短语填空控件 - 填空(显示be ___ at, ~ good)"""
    def __init__(self, phrase, missing_idx, words, missing_word, parent=None):
        super().__init__(parent)
        self.words = words
        self.missing_idx = missing_idx
        self.missing_word = missing_word
        self.user_input = ""
        self.setFixedHeight(120)
        self.setMinimumWidth(800)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)
        font = QFont("Microsoft YaHei", 36, QFont.Bold)
        for i, word in enumerate(words):
            if i > 0:
                space_lbl = QLabel("  ")
                space_lbl.setFont(font)
                space_lbl.setStyleSheet("background: transparent;")
                layout.addWidget(space_lbl)
            if i == missing_idx:
                # 鏁磋瘝输入妗衣
                self.input_edit = QLineEdit()
                self.input_edit.setFont(font)
                self.input_edit.setFixedWidth(max(200, len(missing_word) * 45))
                self.input_edit.setAlignment(Qt.AlignCenter)
                self.input_edit.setPlaceholderText("_" * len(missing_word))
                self.input_edit.setStyleSheet("""
                    QLineEdit {
                        color: #1cb0f6;
                        background: transparent;
                        border: none;
                        border-bottom: 4px solid #1cb0f6;
                        padding-bottom: 2px;
                    }
                """)
                self.input_edit.textChanged.connect(
                    lambda t, self=self: setattr(self, "user_input", t.strip())
                )
                layout.addWidget(self.input_edit)
            else:
                lbl = QLabel(word)
                lbl.setFont(font)
                lbl.setStyleSheet("color: #333; background: transparent;")
                layout.addWidget(lbl)
        layout.addStretch()
    def showEvent(self, event):
        super().showEvent(event)
        if hasattr(self, "input_edit"):
            self.input_edit.setFocus()
class EnglishLearningTool(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 检查敞鍐衣
        if not verify_license():
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QMessageBox, QApplication
            dialog = QDialog()
            dialog.setWindowTitle("程序注册")
            dialog.setFixedSize(500, 300)
            dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowCloseButtonHint)  # 禁用关闭按钮
            layout = QVBoxLayout(dialog)
            
            machine_code = get_machine_code()
            layout.addWidget(QLabel("本软件需要注册后才能使用"))
            
            # 机器码+ 复制按钮
            code_layout = QHBoxLayout()
            code_label = QLabel(f"机器码：{machine_code}")
            code_label.setFont(QFont('Consolas', 12, QFont.Bold))
            code_label.setStyleSheet("color: #d32f2f; padding: 5px;")
            code_layout.addWidget(code_label)
            
            copy_btn = QPushButton("\U0001f4cb 复制")
            copy_btn.setStyleSheet("""
                QPushButton { background-color: #4a90e2; color: white; padding: 4px 12px;
                             border-radius: 4px; border: none; font-size: 11px; }
                QPushButton:hover { background-color: #357abd; }
            """)
            def copy_code():
                QApplication.clipboard().setText(machine_code)
                QMessageBox.information(dialog, "已复制", "机器码已复制到剪贴板")
            copy_btn.clicked.connect(copy_code)
            code_layout.addWidget(copy_btn)
            code_layout.addStretch()
            layout.addLayout(code_layout)
            
            layout.addWidget(QLabel("请将机器码发送给作者获取注册码"))
            
            input_layout = QHBoxLayout()
            reg_input = QLineEdit()
            reg_input.setPlaceholderText("请输入答案...")
            reg_input.setFont(QFont('微软雅黑', 11))
            input_layout.addWidget(reg_input)
            layout.addLayout(input_layout)
            
            result_holder = {"registered": False}
            
            def do_register():
                code = reg_input.text().strip()
                if not code:
                    QMessageBox.warning(dialog, "错误", "请输入验证码")
                    return
                expected = generate_reg_code(machine_code)
                if code == expected:
                    save_license(code)
                    QMessageBox.information(dialog, "成功", "注册成功！感谢您的使用")
                    result_holder["registered"] = True
                    dialog.accept()
                else:
                    QMessageBox.warning(dialog, "错误", "注册码有误，请重新输入")
            
            def do_exit():
                result_holder["registered"] = False
                dialog.reject()
            
            btn_layout = QHBoxLayout()
            ok_btn = QPushButton("注册")
            ok_btn.setStyleSheet("""
                QPushButton { background-color: #4a90e2; color: white; font-size: 14px;
                             padding: 8px 30px; border-radius: 6px; border: none; }
                QPushButton:hover { background-color: #357abd; }
            """)
            ok_btn.clicked.connect(do_register)
            btn_layout.addWidget(ok_btn)
            
            exit_btn = QPushButton("退出")
            exit_btn.setStyleSheet("""
                QPushButton { background-color: #d32f2f; color: white; font-size: 14px;
                             padding: 8px 30px; border-radius: 6px; border: none; }
                QPushButton:hover { background-color: #b71c1c; }
            """)
            exit_btn.clicked.connect(do_exit)
            btn_layout.addWidget(exit_btn)
            layout.addLayout(btn_layout)
            
            dialog.exec_()
            
            # 濡傛灉鏈练垚鍔熸敞鍐岋紝閫鍑虹底
            if not result_holder["registered"]:
                sys.exit(0)
        
        self.init_tts()
        self._load_data()
        self.reward = RewardSystem()  # 初始化鍖栧鍔辩郴缁衣
        self._completed_stages = []  # 宸查氬叧鐨勫叧鍗衣
        self.init_ui()
        self._init_reward_ui()  # 添加到界面（在主窗口创建之后）
        self._populate_ui()
        # 鍚量姩后缀樉绀哄法涔犺填鍒掓点杩庨
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(500, self._show_welcome_plan)
    def _show_welcome_plan(self):
        """启动后显示欢迎信息和学习计划提示"""
        pass  # 可扩展为弹出欢迎对话框
    @staticmethod
    def _clean(s):
        """鍘婚櫎鏍囩偣锛岃浆灏忓啓锛岀敤浜庣瓟妗堟瘮杈衣"""
        return re.sub(r'[^\w\u4e00-\u9fff]', '', s).lower()
    def _load_data(self):
        """加载数据（不依赖UI）"""
        self.words = list(BUILTIN_WORD_LIST)
        self.phrases = list(BUILTIN_PHRASE_LIST)
        self.dialogues = list(BUILTIN_DIALOGUES)
        # 先从内置词库构建dict（含年级映射），用于后续去重
        self.word_lib = {}
        self.word_to_grade = {}  # 单词→年级映射表，用于关卡统计
        for item in self.words:
            if len(item) >= 3:
                en, zh, grade = item[:3]
                self.word_to_grade[en] = grade
            else:
                en, zh = item[:2]
            self.word_lib[en] = zh
        self.phrase_lib = {}
        self.phrase_to_grade = {}  # 短语年级映射
        for item in self.phrases:
            if len(item) >= 3:
                en, zh, grade = item[:3]
                self.phrase_to_grade[en] = grade
            else:
                en, zh = item[:2]
            self.phrase_lib[en] = zh
        # 尝试加载外部词库文件（追加模式，保留内置年级信息不被覆盖）
        try:
            with open(os.path.join(BASE_DIR, 'word_lib.txt'), 'r', encoding='utf-8') as f:
                lines = f.read().strip().split('\n')
                if lines and lines[0]:
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        if '|' in line:
                            en, zh = line.split('|', 1)
                        else:
                            parts = line.split(None, 1)
                            if len(parts) < 2:
                                continue
                            en, zh = parts[0], parts[1]
                        en, zh = en.strip(), zh.strip()
                        # 追加：仅当内置词库中不存在该单词时才添加
                        if en not in self.word_lib:
                            self.words.append((en, zh))
                            self.word_lib[en] = zh  # 无年级标记
        except Exception as e:
            print('Load word_lib.txt error:', e)
        # 尝试加载外部短语库文件（追加模式）
        try:
            with open(os.path.join(BASE_DIR, 'phrase_lib.txt'), 'r', encoding='utf-8') as f:
                lines = f.read().strip().split('\n')
                if lines and lines[0]:
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        if '|' in line:
                            en, zh = line.split('|', 1)
                        else:
                            parts = line.split(None, 1)
                            if len(parts) < 2:
                                continue
                            en, zh = parts[0], parts[1]
                        en, zh = en.strip(), zh.strip()
                        if en not in self.phrase_lib:
                            self.phrases.append((en, zh))
                            self.phrase_lib[en] = zh  # 无年级标记
        except Exception as e:
            print('Load phrase_lib.txt error:', e)
        # File paths for save/load
        self.word_lib_path = os.path.join(BASE_DIR, "word_lib.txt")
        self.phrase_lib_path = os.path.join(BASE_DIR, "phrase_lib.txt")
        self.word_review_path = os.path.join(BASE_DIR, "word_review.pkl")
        self.phrase_review_path = os.path.join(BASE_DIR, "phrase_review.pkl")
        # Review records
        self.word_review_records = []
        try:
            with open(self.word_review_path, 'rb') as f:
                self.word_review_records = pickle.load(f)
        except Exception:
            self.word_review_records = []
        self.phrase_review_records = []
        try:
            with open(self.phrase_review_path, 'rb') as f:
                self.phrase_review_records = pickle.load(f)
        except Exception:
            self.phrase_review_records = []
    def _populate_ui(self):
        """填充UI列表（依赖UI已创建，支持年级过滤）"""
        # 填充单词列表（按当前年级选择过滤）
        self.update_word_list()
        # 填充短语列表（按当前年级选择过滤）
        self.update_phrase_list()
        
        # 填充对话列表
        for d in self.dialogues:
            self.dialogue_list.addItem(d.get('title', ''))
        
        # Update review tips
        if hasattr(self, 'update_word_review_tip'):
            self.update_word_review_tip()
        if hasattr(self, 'update_phrase_review_tip'):
            self.update_phrase_review_tip()
    # ==================== 奖励系统 UI 涓庨泦鎴衣====================
    def _init_reward_ui(self):
        """初始化鍖栧鍔辩郴缁烾I显示锛堝簳閮录姸鎬佹爮锛衣"""
        from PyQt5.QtWidgets import QStatusBar
        
        self.reward_bar = QStatusBar()
        self.reward_bar.setStyleSheet("""
            QStatusBar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #fff8e1, stop:1 #e8f5e9);
                border-top: 2px solid #ffd54f;
                padding: 4px 12px;
                font-family: 微软雅黑;
                font-size: 13px;
            }
        """)
        
        # 滚动学习鎻愰啋
        self.ticker_label = QLabel("")
        self.ticker_label.setStyleSheet("""
            color: #c62828; font-weight: bold; font-size: 13px; 
            padding: 0 10px; background: transparent;
        """)
        self.ticker_label.setMinimumWidth(500)
        self.reward_bar.addWidget(self.ticker_label, 1)
        # 滚动鍔录敾
        self._ticker_text = ""
        self._ticker_pos = 0
        self._ticker_timer = QTimer(self)
        self._ticker_timer.timeout.connect(self._tick_scroll)
        self._ticker_timer.start(250)  # 姣衣50ms滚动涓娆衣
        
        self.reward_star_label = QLabel("⭐ 0")
        self.reward_star_label.setStyleSheet("color: #f57c00; font-weight: bold; font-size: 15px; padding: 0 8px;")
        
        self.reward_heart_label = QLabel("❤️ 0/5")
        self.reward_heart_label.setStyleSheet("color: #e53935; font-weight: bold; font-size: 15px; padding: 0 8px;")
        
        self.reward_level_label = QLabel("Lv.1")
        self.reward_level_label.setStyleSheet("color: #1565c0; font-weight: bold; font-size: 14px; padding: 0 8px;")
        
        self.reward_combo_label = QLabel("连击:0")
        self.reward_combo_label.setStyleSheet("color: #6a1b9a; font-weight: bold; font-size: 14px; padding: 0 8px;")
        
        self.reward_achieve_label = QLabel("\U0001f3c6 成就:0")
        self.reward_achieve_label.setStyleSheet("color: #2e7d32; font-weight: bold; font-size: 14px; padding: 0 8px;")
        
        separator = QLabel("━")
        separator.setStyleSheet("color: #bdbdbd; padding: 0 2px;")
        separator2 = QLabel("│")
        separator2.setStyleSheet("color: #bdbdbd; padding: 0 2px;")
        separator3 = QLabel("│")
        separator3.setStyleSheet("color: #bdbdbd; padding: 0 2px;")
        separator4 = QLabel("│")
        separator4.setStyleSheet("color: #bdbdbd; padding: 0 2px;")
        
        self.reward_bar.addWidget(self.reward_star_label)
        self.reward_bar.addWidget(separator)
        self.reward_bar.addWidget(self.reward_heart_label)
        self.reward_bar.addWidget(separator2)
        self.reward_bar.addWidget(self.reward_level_label)
        self.reward_bar.addWidget(separator3)
        self.reward_bar.addWidget(self.reward_combo_label)
        self.reward_bar.addWidget(separator4)
        self.reward_bar.addWidget(self.reward_achieve_label)
        
        # 可以充晶学习计时/打卡显示
        from PyQt5.QtWidgets import QPushButton
        self.reward_bar.addPermanentWidget(QLabel("   "))
        self.study_timer_label = QLabel("")
        self.study_timer_label.setStyleSheet("color: #1565c0; font-weight: bold; font-size: 13px; padding: 0 8px;")
        self.reward_bar.addPermanentWidget(self.study_timer_label)
        
        self.checkin_status_label = QLabel("今日已打卡")
        self.checkin_status_label.setStyleSheet("color: #888; font-size: 11px; padding: 0 4px;")
        self.reward_bar.addPermanentWidget(self.checkin_status_label)
        
        self.setStatusBar(self.reward_bar)
        self._update_reward_display()
        
        # 学习计时鍣衣- 姣忕规璁椂
        self.study_timer = QTimer(self)
        self.study_timer.timeout.connect(self._on_study_timer)
        self.study_timer.start(1000)  # 每秒计时
        
        # 初始化做题活动跟踪（用于5分钟提醒）
        self._last_activity_time = datetime.now()
        self._last_reminder_time = datetime.now()
    def _on_study_timer(self):
        """每秒学习计时"""
        if not hasattr(self, 'reward'):
            return
        r = self.reward
        # 更新学习秒数
        r.daily_study_seconds += 1
        # 每30秒保存一次数据（减少IO，关闭时也会保存）
        if r.daily_study_seconds % 30 == 0:
            # 更新关卡进度（六关卡体系）
            self._update_current_stage()
            r.save_data()
        
        # 每5分钟检查是否有做题活动，无活动则提醒
        FIVE_MIN = 300  # 5分钟 = 300秒
        if r.daily_study_seconds % FIVE_MIN == 0 and hasattr(self, '_last_activity_time'):
            now = datetime.now()
            idle_seconds = (now - self._last_activity_time).total_seconds()
            # 如果超过4分钟没有活动且距离上次提醒已超过5分钟
            if idle_seconds >= 240 and (now - self._last_reminder_time).total_seconds() >= 300:
                self._last_reminder_time = now
                self.reward_bar.showMessage("⏰ 同学，该做题啦！别让时间悄悄溜走~ 💪", 5000)
        # 更新计时显示（不每次保存，减少IO）
        secs = r.daily_study_seconds
        hours = secs // 3600
        mins = (secs % 3600) // 60
        secs_remain = secs % 60
        if hours > 0:
            self.study_timer_label.setText(f"\u23f1 {hours}时{mins}分{secs_remain}秒")
        else:
            self.study_timer_label.setText(f"\u23f1 {mins}分{secs_remain}秒")
        # 检查是否达到2小时且今天还没打卡
        today = datetime.now().date()
        if secs >= r.TWO_HOURS and r.last_checkin_date != today:
            ok, msg = r.daily_checkin()
            if ok:
                r.save_data()
                self._update_reward_display()
                self.checkin_status_label.setText("\u2705 已打卡！连续" + str(r.consecutive_days) + "天")
                self.checkin_status_label.setStyleSheet("color: green; font-size: 11px; padding: 0 4px;")
                self.study_timer_label.setText("\u23f1 已学习2h+ \u2705")
                self.study_timer_label.setStyleSheet("color: #4caf50; font-weight: bold; font-size: 13px; padding: 0 8px;")
            return
        # 更新进度百分比
        if secs < r.TWO_HOURS:
            pct = int(secs / r.TWO_HOURS * 100)
            self.checkin_status_label.setText(f"\U0001f4ca 学习进度 {pct}% (2h自动打卡)")
            self.checkin_status_label.setStyleSheet("color: #ff9800; font-size: 11px; padding: 0 4px;")
        # 如果今天已经打卡完成，显示完成状态
        if r.last_checkin_date == today:
            self.checkin_status_label.setText("\u2705 今日已打卡")
            self.checkin_status_label.setStyleSheet("color: green; font-size: 11px; padding: 0 4px;")
            self.study_timer_label.setStyleSheet("color: #4caf50; font-weight: bold; font-size: 13px; padding: 0 8px;")
    def _tick_scroll(self):
        """奖励区滚动字幕效果（显示在ticker_label上，不影响连击）"""
        if not self._ticker_text:
            return
        self._ticker_pos = (self._ticker_pos + 1) % (len(self._ticker_text) + 20)
        visible = self._ticker_text[self._ticker_pos:] + " " * 20 + self._ticker_text[:self._ticker_pos]
        # 使用滚动提醒标签，不覆盖连击显示
        self.ticker_label.setText(visible[:50])
    def _update_reward_display(self):
        """更新奖励系统UI显示"""
        if not hasattr(self, 'reward') or not hasattr(self, 'reward_star_label'):
            return
        r = self.reward
        self.reward_star_label.setText(f"\u2b50 {r.total_stars_earned}")
        self.reward_heart_label.setText(f"\u2764\ufe0f {r.hearts}/{r.max_hearts}")
        self.reward_level_label.setText(f"Lv.{r.level}")
        self.reward_combo_label.setText(f"\u26a1连击:{r.combo}")
        self.reward_achieve_label.setText(f"\U0001f3c6 成就:{len(r.achievements)}")
    def _update_current_stage(self):
        """根据答题进度更新关卡（八关卡体系）
        规则：
          80%七年级单词 + 80%八年级单词 → 解锁短语
          80%短语 → 解锁语法
          80%语法(七+八) → 解锁口语(对话)
          80%口语(对话) → 解锁作文
        """
        r = self.reward
        stats = r.stats
        
        # 80%阈值（基于词库总量）
        GRADE7_WORD_80PCT = 1459   # 七年级1,823词 × 80%
        GRADE8_WORD_80PCT = 516    # 八年级644词 × 80%
        PHRASE_80PCT = 1218        # 短语1,522条 × 80%
        GRAMMAR_80PCT = 936        # 语法1,170题(七781+八389) × 80%
        DIALOGUE_80PCT = 56        # 对话70场景 × 80%
        
        grade7 = stats.get("grade7_word_correct", 0)
        grade8 = stats.get("grade8_word_correct", 0)
        phrase = stats.get("phrase_correct", 0)
        grammar = stats.get("grammar_correct", 0)
        dialogue = stats.get("dialogue_correct", 0)
        
        # 从最高关卡往下判断
        if dialogue >= DIALOGUE_80PCT:
            stats["current_stage"] = 4  # 作文已解锁
        elif grammar >= GRAMMAR_80PCT:
            stats["current_stage"] = 3  # 对话已解锁
        elif phrase >= PHRASE_80PCT:
            stats["current_stage"] = 2  # 语法已解锁
        elif grade7 >= GRADE7_WORD_80PCT and grade8 >= GRADE8_WORD_80PCT:
            stats["current_stage"] = 1  # 短语已解锁
        else:
            stats["current_stage"] = 0  # 仅单词可用
        
        self._update_tab_access()
        self._update_reward_display()
    def _check_star_award(self, mode="word", word_grade=None):
        """答题正确：统计+每100总正确→1★，自动兑换❤️→升级"""
        if not hasattr(self, 'reward'):
            return
        r = self.reward
        
        # 记录最后活动时间（用于5分钟提醒）
        self._last_activity_time = datetime.now()
        
        # 总正确数
        r.stats["total_correct"] += 1
        
        # 各模式统计 + 年级统计
        if mode == "word":
            r.stats["word_correct"] += 1
            if word_grade:
                if "七年级" in str(word_grade):
                    r.stats["grade7_word_correct"] = r.stats.get("grade7_word_correct", 0) + 1
                elif "八年级" in str(word_grade):
                    r.stats["grade8_word_correct"] = r.stats.get("grade8_word_correct", 0) + 1
                elif "九年级" in str(word_grade):
                    r.stats["grade9_word_correct"] = r.stats.get("grade9_word_correct", 0) + 1
        elif mode == "phrase":
            r.stats["phrase_correct"] += 1
        elif mode == "dialogue":
            r.stats["dialogue_correct"] += 1
        elif mode == "grammar":
            r.stats["grammar_correct"] = r.stats.get("grammar_correct", 0) + 1
        
        total = r.stats["total_correct"]
        word_total = r.stats.get("word_correct", 0)
        
        # 每100总正确 → 1★
        if total > 0 and total % 100 == 0:
            ok, msg = r.add_stars(1, reason=mode)
            if ok:
                self.reward_bar.showMessage(msg, 4000)
            self._update_reward_display()
            r.save_data()
        else:
            self._update_reward_display()
            r.save_data()
        
        # 每次答题后即时更新关卡解锁状态
        self._update_current_stage()
        
        # 随机系统每100单词额外提示
        if mode == "word" and word_total > 0 and word_total % 100 == 0:
            self.reward_bar.showMessage(f"🎯 随机系统单词累计答对{word_total}题！继续加油！", 3000)
    
    def _reward_wrong_answer(self):
        """答题错误时扣除爱心"""
        if not hasattr(self, 'reward') or not hasattr(self, 'reward_bar'):
            return
        r = self.reward
        _, msg = r.wrong_answer()
        self.reward_bar.showMessage(msg, 3000)
        self._update_reward_display()
        r.save_data()
    def init_tts(self):
        self.tts = None
        try:
            self.tts = QTextToSpeech()
            print("TTS: QTextToSpeech OK")
        except Exception as e:
            print("QTextToSpeech failed:", e)
            try:
                import pyttsx3
                self.tts = pyttsx3.init()
                print("TTS: pyttsx3 OK")
            except Exception as e2:
                print("pyttsx3 also failed:", e2)
                self.tts = None
        # 璇煶选项
        self.voice_options = {
            "US-Female": "Zira",
            "US-Male": "David",
            "UK-Female": "Susan",
            "UK-Male": "George",
        }
        self.selected_voice = "US-Female"
    def on_voice_changed(self, voice_name):
        """鍒囨崲璇煶"""
        self.selected_voice = voice_name
        if self.tts and hasattr(self.tts, "setProperty"):
            try:
                voices = self.tts.availableVoices()
                for v in voices:
                    if self.voice_options.get(voice_name, "") in v.name():
                        self.tts.setProperty("voice", v.id())
                        break
            except: pass
    def speak(self, text):
        """TTS鏈楄备 - 鏀统寔QTextToSpeech鍜宲yttsx3锛屼笉闃诲UI"""
        if self.tts is None or not text or not text.strip():
            return
        text = text.strip()
        try:
            if hasattr(self.tts, 'say'):
                # QTextToSpeech - say() is async, just need event loop to process it
                self.tts.say(text)
            elif hasattr(self.tts, 'engine'):  # pyttsx3
                self.tts.say(text)
                self.tts.runAndWait()
        except Exception as e:
            try:
                with open(os.path.join(BASE_DIR, '_tts_error.log'), 'a', encoding='utf-8') as log:
                    log.write('speak error: ' + str(e))
            except Exception:
                pass
    def init_ui(self):
        self.setWindowTitle("初中英语全能学习系统 | 内置填空 | 单词/短语/对话")
        self.setMinimumSize(1100, 700)
        self.resize(1400, 800)
        self.setStyleSheet("background-color: #f5f5f5;")
        self.font = QFont("微软雅黑", 12)
        self.title_font = QFont("微软雅黑", 14, QFont.Bold)
        # ---------- 语音选择工具栏----------
        from PyQt5.QtWidgets import QToolBar
        toolbar = QToolBar("璇煶璁剧疆", self)
        toolbar.setMovable(False)
        toolbar.setStyleSheet("QToolBar { border: none; background: #f0f0f0; padding: 4px 10px; spacing: 6px; }")
        voice_label = QLabel("语音:")
        voice_label.setFont(QFont("微软雅黑", 10))
        self.voice_combobox = QComboBox()
        self.voice_combobox.addItems(["US-Female", "US-Male", "UK-Female", "UK-Male"])
        self.voice_combobox.setFixedWidth(120)
        self.voice_combobox.setFont(QFont("微软雅黑", 10))
        self.voice_combobox.currentTextChanged.connect(self.on_voice_changed)
        toolbar.addWidget(voice_label)
        toolbar.addWidget(self.voice_combobox)
        self.addToolBar(Qt.TopToolBarArea, toolbar)
        # ---------- end 璇煶宸叿鏍衣----------
        self.main_tabs = QTabWidget()
        self.setCentralWidget(self.main_tabs)
        self.main_tabs.tabBar().setUsesScrollButtons(True)
        self.word_tab = QWidget()
        self.phrase_tab = QWidget()
        self.dialogue_tab = QWidget()
        self.grammar_tab = QWidget()
        self.essay_tab = QWidget()
        self.plan_tab = QWidget()
        self.ai_tab = QWidget()
        self.main_tabs.addTab(self.plan_tab, "📋 学习计划")
        self.main_tabs.addTab(self.word_tab, "📝 单词 (2430+)")
        self.main_tabs.addTab(self.phrase_tab, "📑 短语 (320+)")
        self.main_tabs.addTab(self.dialogue_tab, "💬 对话 (70场景)")
        self.main_tabs.addTab(self.grammar_tab, '📖 语法知识')
        self.main_tabs.addTab(self.essay_tab, '✍️ 英语作文')
        self.main_tabs.addTab(self.ai_tab, '🤖 AI助手')
        self.main_tabs.setStyleSheet("""
            QTabWidget::tab-bar {alignment: center;}
            QTabBar::tab {
                background-color: #e0e0e0; color: #333; font-size: 14px;
                font-family: Microsoft YaHei; padding: 10px 25px; margin-right: 5px;
                border-radius: 8px 8px 0 0; border: none;
            }
            QTabBar::tab:selected, QTabBar::tab:hover {
                background-color: #4a90e2; color: white;
            }
            QTabBar::tab:disabled {
                background-color: #f0f0f0; color: #bbb;
            }
            QTabWidget::pane {
                border: 1px solid #e0e0e0; border-radius: 0 0 8px 8px;
                background-color: white;
            }
        """)
        self._setup_plan_tab()
        self.setup_word_module()
        self.setup_phrase_module()
        self.setup_dialogue_module()
        self._setup_grammar_tab()
        self._setup_essay_tab()
        self._setup_ai_tab()
    # ==================== AI 助手 Tab ====================
    def _setup_ai_tab(self):
        """设置 AI 助手 Tab（流式实时显示）"""
        from PyQt5.QtWidgets import QGroupBox, QSizePolicy
        self._ai_config = load_ai_config()
        self._ai_history = []        # [{"role":"user","content":"..."}, ...]
        self._ai_thread = None       # 当前正在运行的线程
        self._ai_streaming = False   # 是否正在流式输出
        layout = QVBoxLayout(self.ai_tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        # ---------- 顶部设置栏 ----------
        settings_group = QGroupBox("⚙️ API 设置")
        settings_group.setFont(QFont("Microsoft YaHei", 10))
        settings_layout = QHBoxLayout(settings_group)
        settings_layout.setSpacing(8)
        settings_layout.addWidget(QLabel("Base URL:"))
        self._ai_url_edit = QLineEdit(self._ai_config.get("base_url", ""))
        self._ai_url_edit.setPlaceholderText("https://api.deepseek.com/v1")
        self._ai_url_edit.setMinimumWidth(220)
        self._ai_url_edit.setFont(QFont("Consolas", 10))
        settings_layout.addWidget(self._ai_url_edit)
        settings_layout.addWidget(QLabel("API Key:"))
        self._ai_key_edit = QLineEdit(self._ai_config.get("api_key", ""))
        self._ai_key_edit.setPlaceholderText("sk-xxxxxx...")
        self._ai_key_edit.setEchoMode(QLineEdit.Password)
        self._ai_key_edit.setMinimumWidth(180)
        self._ai_key_edit.setFont(QFont("Consolas", 10))
        settings_layout.addWidget(self._ai_key_edit)
        settings_layout.addWidget(QLabel("模型:"))
        self._ai_model_combo = QComboBox()
        self._ai_model_combo.addItems([
            "deepseek-chat", "deepseek-reasoner",
            "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo",
        ])
        self._ai_model_combo.setEditable(True)
        self._ai_model_combo.setCurrentText(self._ai_config.get("model", "deepseek-chat"))
        self._ai_model_combo.setFont(QFont("Microsoft YaHei", 10))
        self._ai_model_combo.setMinimumWidth(160)
        settings_layout.addWidget(self._ai_model_combo)
        save_cfg_btn = QPushButton("💾 保存设置")
        save_cfg_btn.setStyleSheet("""
            QPushButton { background:#4a90e2; color:white; border-radius:5px;
                          padding:5px 14px; font-size:12px; border:none; }
            QPushButton:hover { background:#357abd; }
        """)
        save_cfg_btn.clicked.connect(self._ai_save_config)
        settings_layout.addWidget(save_cfg_btn)
        clear_btn = QPushButton("🗑️ 清空对话")
        clear_btn.setStyleSheet("""
            QPushButton { background:#e57373; color:white; border-radius:5px;
                          padding:5px 14px; font-size:12px; border:none; }
            QPushButton:hover { background:#c62828; }
        """)
        clear_btn.clicked.connect(self._ai_clear_chat)
        settings_layout.addWidget(clear_btn)
        layout.addWidget(settings_group)
        # ---------- 对话历史区域 ----------
        self._ai_chat_display = QTextEdit()
        self._ai_chat_display.setReadOnly(True)
        self._ai_chat_display.setFont(QFont("Microsoft YaHei", 12))
        self._ai_chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 12px;
                line-height: 1.6;
            }
        """)
        self._ai_chat_display.setHtml("""
            <div style="color:#aaa; text-align:center; margin-top:40px; font-size:15px;">
            🤖 你好！我是你的英语学习 AI 助手<br><br>
            你可以问我：<br>
            • 单词释义 / 例句 / 辨析<br>
            • 语法讲解 / 题目解析<br>
            • 作文批改 / 润色建议<br>
            • 任何英语学习问题<br>
            </div>
        """)
        layout.addWidget(self._ai_chat_display, stretch=1)
        # ---------- 状态栏 ----------
        self._ai_status_label = QLabel("")
        self._ai_status_label.setFont(QFont("Microsoft YaHei", 10))
        self._ai_status_label.setStyleSheet("color: #4a90e2; padding: 2px 4px;")
        layout.addWidget(self._ai_status_label)
        # ---------- 输入区域 ----------
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        self._ai_input = QTextEdit()
        self._ai_input.setPlaceholderText("输入你的问题，按 Ctrl+Enter 发送...")
        self._ai_input.setFont(QFont("Microsoft YaHei", 12))
        self._ai_input.setMaximumHeight(90)
        self._ai_input.setMinimumHeight(60)
        self._ai_input.setStyleSheet("""
            QTextEdit {
                border: 2px solid #dee2e6; border-radius: 8px; padding: 8px;
                background: white;
            }
            QTextEdit:focus { border-color: #4a90e2; }
        """)
        # Ctrl+Enter 发送
        self._ai_input.installEventFilter(self)
        input_layout.addWidget(self._ai_input, stretch=1)
        send_btn_layout = QVBoxLayout()
        self._ai_send_btn = QPushButton("发送\n(Ctrl+↵)")
        self._ai_send_btn.setFixedSize(90, 70)
        self._ai_send_btn.setFont(QFont("Microsoft YaHei", 11))
        self._ai_send_btn.setStyleSheet("""
            QPushButton { background:#4a90e2; color:white; border-radius:8px;
                          border:none; font-weight:bold; }
            QPushButton:hover { background:#357abd; }
            QPushButton:disabled { background:#bbb; color:#fff; }
        """)
        self._ai_send_btn.clicked.connect(self._ai_send_message)
        send_btn_layout.addWidget(self._ai_send_btn)
        input_layout.addLayout(send_btn_layout)
        layout.addLayout(input_layout)
    def eventFilter(self, obj, event):
        """拦截 AI 输入框的 Ctrl+Enter"""
        from PyQt5.QtCore import QEvent
        if hasattr(self, '_ai_input') and obj is self._ai_input:
            if event.type() == QEvent.KeyPress:
                from PyQt5.QtCore import Qt as Qt2
                if (event.key() == Qt2.Key_Return and
                        event.modifiers() == Qt2.ControlModifier):
                    self._ai_send_message()
                    return True
        return super().eventFilter(obj, event)
    def _ai_save_config(self):
        """保存 AI 配置"""
        self._ai_config["api_key"] = self._ai_key_edit.text().strip()
        self._ai_config["base_url"] = self._ai_url_edit.text().strip()
        self._ai_config["model"] = self._ai_model_combo.currentText().strip()
        save_ai_config(self._ai_config)
        self._ai_status_label.setText("✅ 设置已保存")
        QTimer.singleShot(2000, lambda: self._ai_status_label.setText(""))
    def _ai_clear_chat(self):
        """清空对话历史"""
        self._ai_history.clear()
        self._ai_chat_display.setHtml("""
            <div style="color:#aaa; text-align:center; margin-top:40px; font-size:15px;">
            🤖 对话已清空，随时可以开始新的对话！
            </div>
        """)
        self._ai_status_label.setText("")
    def _ai_append_message(self, role, content, is_streaming=False):
        """
        向对话区追加一条消息气泡。
        role: 'user' | 'assistant'
        is_streaming: True 表示这是正在流式写入的气泡（先插入占位）
        """
        if role == "user":
            color = "#e3f2fd"
            align = "right"
            label = "你"
            border = "#90caf9"
        else:
            color = "#f1f8e9"
            align = "left"
            label = "🤖 AI助手"
            border = "#a5d6a7"
        html = f"""
        <div style="text-align:{align}; margin: 6px 0;">
            <span style="font-size:11px; color:#888;">{label}</span><br>
            <div style="display:inline-block; background:{color}; border:1px solid {border};
                 border-radius:10px; padding:10px 14px; max-width:85%;
                 text-align:left; font-size:13px; line-height:1.7;
                 word-wrap:break-word; white-space:pre-wrap;">{content}</div>
        </div>
        <br>
        """
        cursor = self._ai_chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self._ai_chat_display.setTextCursor(cursor)
        self._ai_chat_display.insertHtml(html)
        # 滚动到底部
        self._ai_chat_display.verticalScrollBar().setValue(
            self._ai_chat_display.verticalScrollBar().maximum()
        )
    def _ai_send_message(self):
        """发送用户消息并启动 AI 回复"""
        if self._ai_streaming:
            return
        text = self._ai_input.toPlainText().strip()
        if not text:
            return
        # 读取最新配置
        self._ai_config["api_key"] = self._ai_key_edit.text().strip()
        self._ai_config["base_url"] = self._ai_url_edit.text().strip()
        self._ai_config["model"] = self._ai_model_combo.currentText().strip()
        if not self._ai_config["api_key"]:
            QMessageBox.warning(self, "提示", "请先填写 API Key 并保存设置！")
            return
        # 清空输入框，展示用户消息
        self._ai_input.clear()
        self._ai_append_message("user", text)
        # 加入历史
        self._ai_history.append({"role": "user", "content": text})
        # 准备 AI 回复占位区域（直接在 display 末尾追加，后续逐字追加）
        self._ai_streaming = True
        self._ai_send_btn.setEnabled(False)
        self._ai_status_label.setText("⏳ AI 正在思考...")
        self._ai_stream_buffer = ""
        self._ai_reply_started = False  # 标记是否已插入回复气泡header
        # 启动后台线程
        self._ai_thread = AIStreamThread(
            messages=list(self._ai_history),
            config=dict(self._ai_config),
        )
        self._ai_thread.chunk_received.connect(self._ai_on_chunk)
        self._ai_thread.finished_ok.connect(self._ai_on_done)
        self._ai_thread.error_occurred.connect(self._ai_on_error)
        self._ai_thread.start()
    def _ai_on_chunk(self, chunk):
        """收到流式片段，追加到显示区"""
        if not self._ai_reply_started:
            # 首次插入 AI 回复气泡头部
            self._ai_reply_started = True
            self._ai_status_label.setText("💬 AI 正在回复...")
            cursor = self._ai_chat_display.textCursor()
            cursor.movePosition(QTextCursor.End)
            self._ai_chat_display.setTextCursor(cursor)
            # 插入气泡开头（不闭合 div，后续追加内容）
            self._ai_chat_display.insertHtml(
                '<div style="text-align:left; margin: 6px 0;">'
                '<span style="font-size:11px; color:#888;">🤖 AI助手</span><br>'
                '<div id="ai-bubble" style="display:inline-block; background:#f1f8e9;'
                ' border:1px solid #a5d6a7; border-radius:10px; padding:10px 14px;'
                ' max-width:85%; text-align:left; font-size:13px; line-height:1.7;'
                ' word-wrap:break-word; white-space:pre-wrap;">'
            )
        self._ai_stream_buffer += chunk
        # 追加文本（纯文本，保留换行）
        cursor = self._ai_chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self._ai_chat_display.setTextCursor(cursor)
        # 将换行转为 <br>，其他内容安全转义
        safe_chunk = chunk.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        self._ai_chat_display.insertHtml(safe_chunk)
        # 持续滚动到底部
        self._ai_chat_display.verticalScrollBar().setValue(
            self._ai_chat_display.verticalScrollBar().maximum()
        )
    def _ai_on_done(self, full_text):
        """流式完成，收尾"""
        # 关闭气泡 div
        if self._ai_reply_started:
            cursor = self._ai_chat_display.textCursor()
            cursor.movePosition(QTextCursor.End)
            self._ai_chat_display.setTextCursor(cursor)
            self._ai_chat_display.insertHtml("</div></div><br>")
        # 加入历史
        if full_text:
            self._ai_history.append({"role": "assistant", "content": full_text})
        self._ai_streaming = False
        self._ai_send_btn.setEnabled(True)
        self._ai_status_label.setText(f"✅ 回复完成（{len(full_text)} 字）")
        QTimer.singleShot(3000, lambda: self._ai_status_label.setText(""))
    def _ai_on_error(self, err_msg):
        """请求出错"""
        self._ai_append_message("assistant", err_msg)
        self._ai_streaming = False
        self._ai_send_btn.setEnabled(True)
        self._ai_status_label.setText("")
    def setup_word_module(self):
        self.word_sub_tabs = QTabWidget()
        layout = QVBoxLayout(self.word_tab)
        # 年级筛选工具栏
        grade_layout = QHBoxLayout()
        grade_label = QLabel('选择年级：')
        grade_label.setFont(QFont('微软雅黑', 12))
        self.word_grade_combo = QComboBox()
        self.word_grade_combo.addItems(['全部', '七年级上册', '七年级下册', '八年级上册', '八年级下册', '九年级'])
        self.word_grade_combo.setFont(QFont('微软雅黑', 12))
        self.word_grade_combo.currentTextChanged.connect(self._on_word_grade_changed)
        grade_layout.addWidget(grade_label)
        grade_layout.addWidget(self.word_grade_combo)
        grade_layout.addStretch()
        layout.addLayout(grade_layout)
        layout.addWidget(self.word_sub_tabs)
        self.word_manage = QWidget()
        self.word_random = QWidget()
        self.word_review = QWidget()
        self.word_completion = QWidget()
        self.word_sub_tabs.addTab(self.word_manage, "词库管理")
        self.word_sub_tabs.addTab(self.word_random, "随机抽查 + 默认听写模式")
        self.word_sub_tabs.addTab(self.word_review, "记忆曲线复习")
        self.word_sub_tabs.addTab(self.word_completion, "✍️ 单词补全 (内置填空)")
        self.word_sub_tabs.setStyleSheet("""
            QTabWidget::tab-bar {alignment: left;}
            QTabBar::tab {
                background-color: #e8e8e8; color: #333; font-size: 12px;
                font-family: 微软雅黑; padding: 6px 20px;
                border-radius: 6px 6px 0 0;
            }
            QTabBar::tab:selected { background-color: #4a90e2; color: white; }
        """)
        self.setup_word_manage_tab()
        self.setup_word_random_tab()
        self.setup_word_review_tab()
        self.setup_word_completion_tab()
    def setup_word_manage_tab(self):
        layout = QVBoxLayout(self.word_manage)
        layout.setContentsMargins(30, 20, 30, 20)
        btn_layout = QHBoxLayout()
        self.word_import_btn = QPushButton("导入词库")
        self.word_export_btn = QPushButton("导出词库(TXT)")
        self.word_add_btn = QPushButton("添加单词")
        self.word_del_btn = QPushButton("删除选中")
        for btn in (self.word_import_btn, self.word_export_btn, self.word_add_btn, self.word_del_btn):
            btn.setStyleSheet("""
                QPushButton { background-color: #4a90e2; color: white; font-family: 微软雅黑;
                              font-size: 12px; padding: 8px 15px; border: none; border-radius: 6px; }
                QPushButton:hover { background-color: #357abd; }
            """)
        btn_layout.addWidget(self.word_import_btn)
        btn_layout.addWidget(self.word_export_btn)
        btn_layout.addWidget(self.word_add_btn)
        btn_layout.addWidget(self.word_del_btn)
        layout.addLayout(btn_layout)
        layout.addSpacing(15)
        input_layout = QHBoxLayout()
        self.word_input = QLineEdit()
        self.word_input.setPlaceholderText("请输入答案...")
        self.meaning_input = QLineEdit()
        self.meaning_input.setPlaceholderText("请输入答案...")
        for inp in (self.word_input, self.meaning_input):
            inp.setStyleSheet("padding: 8px 10px; border: 1px solid #e0e0e0; border-radius: 6px;")
        input_layout.addWidget(self.word_input)
        input_layout.addWidget(self.meaning_input)
        layout.addLayout(input_layout)
        layout.addSpacing(15)
        self.word_list = QListWidget()
        self.word_list.setFont(self.font)
        self.word_list.setStyleSheet("border: 1px solid #e0e0e0; border-radius: 6px;")
        self.word_list.itemDoubleClicked.connect(lambda item: self.speak(re.sub(r'\s*\[.*?\]\s*$', '', item.text().split(" - ")[0]).strip()))
        layout.addWidget(self.word_list)
        self.word_import_btn.clicked.connect(self.import_word_lib)
        self.word_export_btn.clicked.connect(self.export_word_lib)
        self.word_add_btn.clicked.connect(self.add_word)
        self.word_del_btn.clicked.connect(self.delete_word)
    def setup_word_random_tab(self):
        layout = QVBoxLayout(self.word_random)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)
        mode_layout = QHBoxLayout()
        mode_layout.addStretch()
        mode_label = QLabel("")
        mode_label.setFont(self.font)
        self.word_mode_en2zh = QRadioButton("英译中(显示英文,输入中文)")
        self.word_mode_zh2en = QRadioButton("中译英(显示中文,输入英文)")
        self.word_mode_en2zh.setChecked(True)
        self.word_mode_group = QButtonGroup()
        self.word_mode_group.addButton(self.word_mode_en2zh)
        self.word_mode_group.addButton(self.word_mode_zh2en)
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.word_mode_en2zh)
        mode_layout.addWidget(self.word_mode_zh2en)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        self.word_card = QLabel("点击下方按钮开始练习")
        self.word_card.setFont(QFont("微软雅黑", 24, QFont.Bold))
        self.word_card.setAlignment(Qt.AlignCenter)
        self.word_card.setStyleSheet("background-color: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 10px; padding: 30px;")
        layout.addWidget(self.word_card)
        self.word_meaning_label = QLabel()
        self.word_meaning_label.setFont(QFont("微软雅黑", 16))
        self.word_meaning_label.setAlignment(Qt.AlignCenter)
        self.word_meaning_label.setVisible(False)
        layout.addWidget(self.word_meaning_label)
        dict_title = QLabel("\U0001f4dd 听写模式：根据上方内容输入答案，系统自动验证")
        dict_title.setFont(self.font)
        dict_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(dict_title)
        input_row = QHBoxLayout()
        self.word_dict_input = QLineEdit()
        self.word_dict_input.setPlaceholderText("请输入答案...")
        self.word_dict_input.returnPressed.connect(self.check_word_dictation)
        self.word_dict_input.setStyleSheet("padding: 10px; border: 1px solid #e0e0e0; border-radius: 6px; font-size: 14px;")
        self.word_dict_check = QPushButton("验证答案")
        self.word_dict_next = QPushButton("下一个单词")
        for btn in (self.word_dict_check, self.word_dict_next):
            btn.setStyleSheet("""
                QPushButton { background-color: #4a90e2; color: white; font-size: 14px;
                              padding: 10px 20px; min-width: 80px;
                              border-radius: 6px; border: none; }
                QPushButton:hover { background-color: #357abd; }
            """)
        self.word_dict_next.setStyleSheet("background-color: #6c757d;")
        input_row.addWidget(self.word_dict_input)
        input_row.addWidget(self.word_dict_check)
        input_row.addWidget(self.word_dict_next)
        layout.addLayout(input_row)
        line = QLabel("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        line.setAlignment(Qt.AlignCenter)
        line.setStyleSheet("color: #cccccc;")
        layout.addWidget(line)
        btn_layout = QHBoxLayout()
        self.word_start_btn = QPushButton("开始练习")
        self.word_show_btn = QPushButton("查看答案")
        self.word_speak_btn = QPushButton("\U0001f50a 播报单词")
        self.word_mastered_btn = QPushButton("已掌握")
        self.word_unmastered_btn = QPushButton("未掌握")
        for btn in (self.word_start_btn, self.word_show_btn, self.word_speak_btn, self.word_mastered_btn, self.word_unmastered_btn):
            btn.setStyleSheet("""
                QPushButton { background-color: #4a90e2; color: white; font-size: 14px;
                              padding: 10px 25px; min-width: 100px;
                              border-radius: 8px; border: none; }
                QPushButton:hover { background-color: #357abd; }
            """)
            btn.setMinimumWidth(100)
        self.word_show_btn.setEnabled(False)
        self.word_speak_btn.setEnabled(False)
        self.word_mastered_btn.setEnabled(False)
        self.word_unmastered_btn.setEnabled(False)
        btn_layout.addWidget(self.word_start_btn)
        btn_layout.addWidget(self.word_show_btn)
        btn_layout.addWidget(self.word_speak_btn)
        btn_layout.addWidget(self.word_mastered_btn)
        btn_layout.addWidget(self.word_unmastered_btn)
        layout.addLayout(btn_layout)
        self.word_dict_result = QLabel()
        self.word_dict_result.setAlignment(Qt.AlignCenter)
        self.word_dict_result.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.word_dict_result)
        layout.addStretch()
        self.word_start_btn.clicked.connect(self.start_word_random)
        self.word_show_btn.clicked.connect(self.show_word_meaning)
        self.word_speak_btn.clicked.connect(lambda: self.speak(self._get_word_display_text()))
        self.word_mastered_btn.clicked.connect(self.word_mark_mastered)
        self.word_unmastered_btn.clicked.connect(self.word_mark_unmastered)
        self.word_dict_check.clicked.connect(self.check_word_dictation)
        self.word_dict_next.clicked.connect(self.next_word_dictation)
        self.word_mode_en2zh.toggled.connect(self.refresh_word_display)
        self.word_mode_zh2en.toggled.connect(self.refresh_word_display)
        self.current_word = None
    def _get_word_display_text(self):
        if self.current_word is None:
            return ""
        if self.word_mode_en2zh.isChecked():
            return self.current_word
        else:
            return self.word_lib.get(self.current_word, "")
    def _on_word_grade_changed(self, grade_text):
        """年级筛选变化时刷新单词列表"""
        self.update_word_list()
    def refresh_word_display(self):
        if self.current_word:
            self.word_card.setText(self._get_word_display_text())
            self.word_meaning_label.setVisible(False)
            self.word_dict_input.clear()
            self.word_dict_result.setText("")
            if self.word_mode_en2zh.isChecked():
                self.word_dict_input.setPlaceholderText("请输入答案...")
            else:
                self.word_dict_input.setPlaceholderText("请输入答案...")
    def start_word_random(self):
        if not self.word_lib:
            QMessageBox.warning(self, "提示", "词库为空")
            return
        # 根据年级筛选候选单词
        grade = self.word_grade_combo.currentText()
        candidates = list(self.word_lib.keys())
        if grade != '全部':
            candidates = [w for w in candidates if grade in self.word_to_grade.get(w, '')]
        if not candidates:
            QMessageBox.warning(self, "鎻愮杽", f"当前筛选（{grade}）下没有单词")
            return
        self.current_word = random.choice(candidates)
        self.word_card.setText(self._get_word_display_text())
        self.word_meaning_label.setVisible(False)
        self.word_dict_input.clear()
        self.word_dict_result.setText("")
        self.word_show_btn.setEnabled(True)
        self.word_speak_btn.setEnabled(True)
        self.word_mastered_btn.setEnabled(True)
        self.word_unmastered_btn.setEnabled(True)
        if self.word_mode_en2zh.isChecked():
            self.word_dict_input.setPlaceholderText("请输入答案...")
        else:
            self.word_dict_input.setPlaceholderText("请输入答案...")
    def show_word_meaning(self):
        if self.current_word:
            self.word_meaning_label.setText(self.word_lib[self.current_word])
            self.word_meaning_label.setVisible(True)
    def check_word_dictation(self):
        if self.current_word is None:
            QMessageBox.warning(self, "请先开始练习")
            return
        user = self.word_dict_input.text().strip()
        if not user:
            self.word_dict_result.setText("...")
            self.word_dict_result.setStyleSheet("color: orange;")
            return
        # 获取褰撳墠单词鐨勫勾绾俊鎭衣
        current_grade = getattr(self, 'word_to_grade', {}).get(self.current_word, None)
        if self.word_mode_en2zh.isChecked():
            correct = self.word_lib[self.current_word]
            if self._clean(user) == self._clean(correct):
                self.word_dict_result.setText("✅ 回答正确！")
                self.word_dict_result.setStyleSheet("color: green; font-size: 14px;")
                self._check_star_award("word", word_grade=current_grade)
            else:
                self.word_dict_result.setText(f"❌ 错误，正确答案：{correct}")
                self.word_dict_result.setStyleSheet("color: red; font-size: 14px;")
                self._reward_wrong_answer()
        else:
            correct = self.current_word
            if self._clean(user) == self._clean(correct):
                self.word_dict_result.setText("✅ 回答正确！")
                self.word_dict_result.setStyleSheet("color: green; font-size: 14px;")
                self._check_star_award("word", word_grade=current_grade)
            else:
                self.word_dict_result.setText(f"❌ 错误，正确答案：{correct}")
                self.word_dict_result.setStyleSheet("color: red; font-size: 14px;")
                self._reward_wrong_answer()
    def next_word_dictation(self):
        self.start_word_random()
    def word_mark_mastered(self):
        self.next_word_dictation()
    def word_mark_unmastered(self):
        if self.current_word is None:
            return
        word = self.current_word
        meaning = self.word_lib[word]
        existing = next((r for r in self.word_review_records if r["word"] == word), None)
        today = datetime.now().date()
        if existing:
            existing["next_review_date"] = today + timedelta(days=REVIEW_CYCLES[0])
            existing["cycle_index"] = 0
        else:
            self.word_review_records.append({
                "word": word, "meaning": meaning,
                "next_review_date": today + timedelta(days=REVIEW_CYCLES[0]),
                "cycle_index": 0
            })
        self.save_word_review_records()
        self.update_word_review_tip()
        QMessageBox.information(self, "提示", f"{word} 已加入学习队列!")
        self.next_word_dictation()
    def setup_word_review_tab(self):
        layout = QVBoxLayout(self.word_review)
        layout.setContentsMargins(30, 20, 30, 20)
        self.word_review_tip = QLabel()
        self.word_review_tip.setFont(self.font)
        self.word_review_tip.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.word_review_tip)
        self.word_review_card = QLabel("点击开始复习")
        self.word_review_card.setFont(QFont("微软雅黑", 24, QFont.Bold))
        self.word_review_card.setAlignment(Qt.AlignCenter)
        self.word_review_card.setStyleSheet("background-color: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 10px; padding: 30px;")
        layout.addWidget(self.word_review_card)
        self.word_review_meaning = QLabel()
        self.word_review_meaning.setFont(QFont("微软雅黑", 16))
        self.word_review_meaning.setAlignment(Qt.AlignCenter)
        self.word_review_meaning.setVisible(False)
        layout.addWidget(self.word_review_meaning)
        # 记忆曲线听写输入区
        self.review_dict_title = QLabel("\U0001f4dd 输入答案后点击验证")
        self.review_dict_title.setFont(self.font)
        self.review_dict_title.setAlignment(Qt.AlignCenter)
        self.review_dict_title.setVisible(False)
        layout.addWidget(self.review_dict_title)
        review_input_row = QHBoxLayout()
        self.word_review_input = QLineEdit()
        self.word_review_input.setPlaceholderText("请输入答案...")
        self.word_review_input.setStyleSheet("padding: 10px; border: 1px solid #e0e0e0; border-radius: 6px; font-size: 14px;")
        self.word_review_input.setVisible(False)
        self.word_review_input.returnPressed.connect(self.check_review_answer)
        self.word_review_check = QPushButton("验证答案")
        self.word_review_next = QPushButton("下一个单词")
        for btn in (self.word_review_check, self.word_review_next):
            btn.setStyleSheet("""
                QPushButton { background-color: #4a90e2; color: white; font-size: 14px;
                              padding: 10px 20px; min-width: 80px;
                              border-radius: 6px; border: none; }
                QPushButton:hover { background-color: #357abd; }
            """)
            btn.setVisible(False)
        self.word_review_next.setStyleSheet("background-color: #6c757d;")
        review_input_row.addWidget(self.word_review_input)
        review_input_row.addWidget(self.word_review_check)
        review_input_row.addWidget(self.word_review_next)
        layout.addLayout(review_input_row)
        self.word_review_result = QLabel()
        self.word_review_result.setAlignment(Qt.AlignCenter)
        self.word_review_result.setStyleSheet("font-size: 14px;")
        self.word_review_result.setVisible(False)
        layout.addWidget(self.word_review_result)
        btn_layout = QHBoxLayout()
        self.word_review_start_btn = QPushButton("开始练习")
        self.word_review_show_btn = QPushButton("查看范文")
        self.word_review_speak_btn = QPushButton("\U0001f50a 播报单词")
        self.word_review_mastered_btn = QPushButton("已掌握")
        self.word_review_unmastered_btn = QPushButton("未掌握")
        for btn in (self.word_review_start_btn, self.word_review_show_btn, self.word_review_speak_btn,
                    self.word_review_mastered_btn, self.word_review_unmastered_btn):
            btn.setStyleSheet("""
                QPushButton { background-color: #4a90e2; color: white; font-size: 14px;
                              padding: 10px 25px; min-width: 100px;
                              border-radius: 8px; border: none; }
                QPushButton:hover { background-color: #357abd; }
            """)
            btn.setMinimumWidth(100)
        self.word_review_show_btn.setEnabled(False)
        self.word_review_speak_btn.setEnabled(False)
        self.word_review_mastered_btn.setEnabled(False)
        self.word_review_unmastered_btn.setEnabled(False)
        btn_layout.addWidget(self.word_review_start_btn)
        btn_layout.addWidget(self.word_review_show_btn)
        btn_layout.addWidget(self.word_review_speak_btn)
        btn_layout.addWidget(self.word_review_mastered_btn)
        btn_layout.addWidget(self.word_review_unmastered_btn)
        layout.addLayout(btn_layout)
        self.word_review_start_btn.clicked.connect(self.start_word_review)
        self.word_review_show_btn.clicked.connect(self.show_word_review_meaning)
        self.word_review_speak_btn.clicked.connect(lambda: self.speak(self.current_review_word["word"]) if self.current_review_word else None)
        self.word_review_mastered_btn.clicked.connect(self.word_review_mastered)
        self.word_review_unmastered_btn.clicked.connect(self.word_review_unmastered)
        self.word_review_check.clicked.connect(self.check_review_answer)
        self.word_review_next.clicked.connect(self.next_review_word)
        self.current_review_word = None
    # ---------- 单词补全新功能(内置填空，间距优化)----------
    def setup_word_completion_tab(self):
        main_layout = QVBoxLayout(self.word_completion)
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(20)
        self.title = QLabel("单词补全练习")
        self.title.setFont(self.title_font)
        self.title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.title)
        # 单词卡片容器
        self.word_completion_container = QWidget()
        self.word_completion_container.setStyleSheet("background-color: transparent; border: none;")
        self.word_completion_layout = QHBoxLayout(self.word_completion_container)
        self.word_completion_layout.setAlignment(Qt.AlignCenter)
        self.word_completion_layout.setSpacing(0)    # 鍏抽敭锛氬幓鎺夐棿璺濓紝璁瓧姣嶇揣鍑衣
        self.word_completion_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.word_completion_container)
        # 中文释义
        self.word_completion_meaning_label = QLabel()
        self.word_completion_meaning_label.setFont(QFont("微软雅黑", 14))
        self.word_completion_meaning_label.setAlignment(Qt.AlignCenter)
        self.word_completion_meaning_label.setStyleSheet("color: #555;")
        main_layout.addWidget(self.word_completion_meaning_label)
        # 按钮
        btn_layout = QHBoxLayout()
        self.word_completion_check_btn = QPushButton("验证答案")
        self.word_completion_next_btn = QPushButton("下一题")
        for btn in (self.word_completion_check_btn, self.word_completion_next_btn):
            btn.setStyleSheet("""
                QPushButton { background-color: #4a90e2; color: white; font-size: 14px;
                              padding: 10px 20px; min-width: 100px;
                              border-radius: 6px; border: none; }
                QPushButton:hover { background-color: #357abd; }
            """)
        self.word_completion_next_btn.setStyleSheet("background-color: #6c757d;")
        btn_layout.addStretch()
        btn_layout.addWidget(self.word_completion_check_btn)
        btn_layout.addWidget(self.word_completion_next_btn)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)
        self.word_completion_result = QLabel()
        self.word_completion_result.setAlignment(Qt.AlignCenter)
        self.word_completion_result.setStyleSheet("font-size: 14px;")
        main_layout.addWidget(self.word_completion_result)
        main_layout.addStretch()
        self.word_completion_check_btn.clicked.connect(self.check_word_completion)
        self.word_completion_next_btn.clicked.connect(self.next_word_completion)
        self.current_word_obj = None
        self.current_word_missing = ""
        self.current_word_input_box = None
        self.show_word_completion_placeholder()
    def show_word_completion_placeholder(self):
        self.clear_word_completion_layout()
        label = QLabel("")
        label.setFont(QFont("微软雅黑", 20))
        label.setAlignment(Qt.AlignCenter)
        self.word_completion_layout.addWidget(label)
        self.word_completion_meaning_label.setText("")
    def clear_word_completion_layout(self):
        while self.word_completion_layout.count():
            item = self.word_completion_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    def next_word_completion(self):
        if not self.word_lib:
            QMessageBox.warning(self, "提示")
            self.show_word_completion_placeholder()
            return
        # 随机选一个单词(长度至少2，否则跳过)
        valid_words = [w for w in self.word_lib.keys() if len(w) >= 2]
        if not valid_words:
            QMessageBox.warning(self, "提示", "词库中没有长度>=2的单词，无法进行补全练习")
            self.show_word_completion_placeholder()
            return
        word = random.choice(valid_words)
        # 随机选择填空位置
        valid_pos = [i for i in range(len(word))]
        pos = random.choice(valid_pos)
        missing_char = word[pos]
        self.clear_word_completion_layout()
        # 使用自定义国家风格控件
        fill_widget = WordFillWidget(word, pos)
        self.word_completion_layout.addWidget(fill_widget)
        self.current_word_fill_widget = fill_widget
        self.current_word_obj = word
        self.current_word_missing = missing_char
        ph = phonetic_dict.get(word, "")
        if ph:
            self.word_completion_meaning_label.setText(f"[{ph}]\n释义：{self.word_lib[word]}")
        else:
            self.word_completion_meaning_label.setText(f"释义：{self.word_lib[word]}")
        self.word_completion_result.setText("")
        if self.current_word_fill_widget:
            self.current_word_fill_widget.input_label.setFocus()
    def check_word_completion(self):
        if self.current_word_obj is None:
            QMessageBox.warning(self, "请先开始练习")
            return
        if self.current_word_fill_widget is None:
            return
        user = self.current_word_fill_widget.user_input.strip()
        if not user:
            self.word_completion_result.setText("...")
            self.word_completion_result.setStyleSheet("color: orange;")
            return
        # 获取褰撳墠单词鐨勫勾绾俊鎭衣
        full_word = str(self.current_word_obj) if hasattr(self.current_word_obj, '__str__') else str(self.current_word_obj)
        current_grade = getattr(self, 'word_to_grade', {}).get(full_word, None)
        if user.lower() == self.current_word_missing.lower():
            self.word_completion_result.setText("✅ 回答正确！")
            self.word_completion_result.setStyleSheet("color: green; font-size: 14px;")
            # 播放完整单词 + 播报发音
            self.speak(f"{full_word}. Correct! Very good!")
            self._check_star_award("word", word_grade=current_grade)
        else:
            self.word_completion_result.setText(f"❌ 错误，正确答案：{self.current_word_missing}")
            self.word_completion_result.setStyleSheet("color: red; font-size: 14px;")
            # 朗读正确答案 + 鼓励语
            full_word = str(self.current_word_obj) if hasattr(self.current_word_obj, '__str__') else str(self.current_word_obj)
            self.speak(f"Wrong! The answer is {full_word}. Keep trying, you can do it!")
            self._reward_wrong_answer()
    # ---------- 单词数据点击綔 ----------
    def save_word_lib(self):
        with open(self.word_lib_path, "w", encoding="utf-8") as f:
            for w, m in self.word_lib.items():
                f.write(f"{w}|{m}\n")
    def save_word_review_records(self):
        with open(self.word_review_path, "wb") as f:
            pickle.dump(self.word_review_records, f)
    def update_word_list(self):
        self.word_list.clear()
        grade = self.word_grade_combo.currentText()
        for w, m in self.word_lib.items():
            if grade != '全部':
                item_grade = self.word_to_grade.get(w, '')
                if grade not in item_grade:
                    continue
            ph = phonetic_dict.get(w, ""); self.word_list.addItem(f"{w} {ph} - {m}")
    def update_word_review_tip(self):
        today = datetime.now().date()
        need = sum(1 for r in self.word_review_records if r["next_review_date"] <= today)
        self.word_review_tip.setText("...")
    def import_word_lib(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择单词文件", "", "TXT (*.txt)")
        if path:
            with open(path, "r", encoding="utf-8") as f:
                cnt = 0
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    if '|' in line:
                        parts = line.split('|', 1)
                    elif ' ' in line:
                        parts = line.split(' ', 1)
                    else:
                        continue
                    if len(parts) < 2:
                        continue
                    w, m = parts[0].strip(), parts[1].strip()
                    if w and w not in self.word_lib:
                        self.word_lib[w] = m
                        cnt += 1
            self.save_word_lib()
            self.update_word_list()
            QMessageBox.information(self, "提示")
    def export_word_lib(self):
        if not self.word_lib:
            QMessageBox.warning(self, "错误", "词库为空")
            return
        path, _ = QFileDialog.getSaveFileName(self, "保存词库", "word_lib", "TXT (*.txt)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                for w, m in self.word_lib.items():
                    f.write(f"{w}|{m}\n")
            QMessageBox.information(self, "成功", "导出完成")
    def add_word(self):
        w = self.word_input.text().strip()
        m = self.meaning_input.text().strip()
        if not w or not m:
            QMessageBox.warning(self, "提示", "请填写完整内容")
            return
        if w in self.word_lib:
            QMessageBox.warning(self, "提示", "单词已存在")
            return
        self.word_lib[w] = m
        self.save_word_lib()
        self.update_word_list()
        self.word_input.clear()
        self.meaning_input.clear()
    def delete_word(self):
        cur = self.word_list.currentItem()
        if not cur:
            return
        # 列表项格式为 "word [音标] - 释义" 或 "word - 释义"
        # 鍏堝彇 " - " 鍓嶅崐閮题垎锛屽啀鍘绘帀可以判兘鐨勯煶鏍囷紙鍘婚櫎方法嫭可以峰唴瀹瑰強灏鹃殢绌烘牸锛衣
        raw = cur.text().split(" - ")[0]
        w = re.sub(r'\s*\[.*?\]\s*$', '', raw).strip()
        # 检查槸鍚-负鍐呯疆璇嶆眹
        builtin_words = {item[0] for item in BUILTIN_WORD_LIST}
        if w in builtin_words:
            QMessageBox.warning(self, "确认删除", f"{w} 是内置单词，不能删除")
            return
        if QMessageBox.question(self, "确认", f"确定删除 {w} ?") == QMessageBox.Yes:
            del self.word_lib[w]
            self.word_review_records = [r for r in self.word_review_records if r["word"] != w]
            self.save_word_lib()
            self.save_word_review_records()
            self.update_word_list()
            self.update_word_review_tip()
    def get_next_word_review(self):
        today = datetime.now().date()
        due = [r for r in self.word_review_records if r["next_review_date"] <= today]
        if due:
            due.sort(key=lambda x: x["next_review_date"])
            return due[0]
        return None
    def start_word_review(self):
        rec = self.get_next_word_review()
        if not rec:
            QMessageBox.information(self, "复习", "无待复习单词")
            return
        self.current_review_word = rec
        self.word_review_card.setText(rec["word"])
        self.word_review_meaning.setVisible(False)
        self.word_review_show_btn.setEnabled(True)
        self.word_review_speak_btn.setEnabled(True)
        self.word_review_mastered_btn.setEnabled(True)
        self.word_review_unmastered_btn.setEnabled(True)
        # 显示输入区域
        self.review_dict_title.setVisible(True)
        self.word_review_input.setVisible(True)
        self.word_review_input.clear()
        self.word_review_input.setFocus()
        self.word_review_check.setVisible(True)
        self.word_review_next.setVisible(True)
        self.word_review_result.setVisible(True)
        self.word_review_result.setText("")
    def show_word_review_meaning(self):
        if self.current_review_word:
            self.word_review_meaning.setText(self.current_review_word["meaning"])
            self.word_review_meaning.setVisible(True)
    def word_review_mastered(self):
        if self.current_review_word:
            self.word_review_records = [r for r in self.word_review_records if r["word"] != self.current_review_word["word"]]
            self.save_word_review_records()
            self.update_word_review_tip()
            self.start_word_review()
    def word_review_unmastered(self):
        if not self.current_review_word:
            return
        idx = self.current_review_word["cycle_index"]
        if idx + 1 < len(REVIEW_CYCLES):
            self.current_review_word["cycle_index"] = idx + 1
            self.current_review_word["next_review_date"] = datetime.now().date() + timedelta(days=REVIEW_CYCLES[idx+1])
        else:
            self.word_review_records = [r for r in self.word_review_records if r["word"] != self.current_review_word["word"]]
            QMessageBox.information(self, "完成", f"{self.current_review_word['word']} 已完成复习")
            self.save_word_review_records()
            self.update_word_review_tip()
            self.start_word_review()
            return
        self.save_word_review_records()
        self.update_word_review_tip()
        QMessageBox.information(self, "复习", f"{self.current_review_word['word']} 已掌握！，{REVIEW_CYCLES[idx+1]} 天后再复习")
        self.start_word_review()
    def check_review_answer(self):
        """检查记忆曲线复习中的输入答案"""
        if not self.current_review_word:
            return
        answer = self.word_review_input.text().strip()
        if not answer:
            self.word_review_result.setText("⚠️ 请输入答案")
            self.word_review_result.setStyleSheet("font-size: 14px; color: orange;")
            return
        correct = self.current_review_word["word"].strip().lower()
        if answer.lower() == correct:
            self.word_review_result.setText("✅ 正确！")
            self.word_review_result.setStyleSheet("font-size: 14px; color: green;")
            # 自动进入下一题
            self.word_review_mastered()
        else:
            self.word_review_result.setText(f"❌ 错误，正确答案：{self.current_review_word['word']}")
            self.word_review_result.setStyleSheet("font-size: 14px; color: red;")
    def next_review_word(self):
        """记忆曲线复习中跳过当前单词"""
        if not self.current_review_word:
            return
        self.word_review_unmastered()
    # ---------- 短语模块 ----------
    def setup_phrase_module(self):
        self.phrase_sub_tabs = QTabWidget()
        layout = QVBoxLayout(self.phrase_tab)
        # 年级筛选工具栏
        grade_layout = QHBoxLayout()
        grade_label = QLabel('选择年级：')
        grade_label.setFont(QFont('微软雅黑', 12))
        self.phrase_grade_combo = QComboBox()
        self.phrase_grade_combo.addItems(['全部', '七年级上册', '七年级下册', '八年级上册', '八年级下册', '九年级'])
        self.phrase_grade_combo.setFont(QFont('微软雅黑', 12))
        self.phrase_grade_combo.currentTextChanged.connect(self._on_phrase_grade_changed)
        grade_layout.addWidget(grade_label)
        grade_layout.addWidget(self.phrase_grade_combo)
        grade_layout.addStretch()
        layout.addLayout(grade_layout)
        layout.addWidget(self.phrase_sub_tabs)
        self.phrase_manage = QWidget()
        self.phrase_random = QWidget()
        self.phrase_review = QWidget()
        self.phrase_completion = QWidget()
        self.phrase_sub_tabs.addTab(self.phrase_manage, "📑 短语管理")
        self.phrase_sub_tabs.addTab(self.phrase_random, "🎲 随机练习 + 默认模式")
        self.phrase_sub_tabs.addTab(self.phrase_review, "📝 短语复习")
        self.phrase_sub_tabs.addTab(self.phrase_completion, "✍️ 短语补全 (自由模式)")
        self.setup_phrase_manage_tab()
        self.setup_phrase_random_tab()
        self.setup_phrase_review_tab()
        self.setup_phrase_completion_tab()
    def setup_phrase_manage_tab(self):
        layout = QVBoxLayout(self.phrase_manage)
        layout.setContentsMargins(30, 20, 30, 20)
        btn_layout = QHBoxLayout()
        self.phrase_import_btn = QPushButton("按钮")
        self.phrase_export_btn = QPushButton("导出短语(TXT)")
        self.phrase_add_btn = QPushButton("添加短语")
        self.phrase_del_btn = QPushButton("删除选中")
        for btn in (self.phrase_import_btn, self.phrase_export_btn, self.phrase_add_btn, self.phrase_del_btn):
            btn.setStyleSheet("""
                QPushButton { background-color: #4a90e2; color: white; font-family: 微软雅黑;
                              font-size: 12px; padding: 8px 15px; border: none; border-radius: 6px; }
                QPushButton:hover { background-color: #357abd; }
            """)
        btn_layout.addWidget(self.phrase_import_btn)
        btn_layout.addWidget(self.phrase_export_btn)
        btn_layout.addWidget(self.phrase_add_btn)
        btn_layout.addWidget(self.phrase_del_btn)
        layout.addLayout(btn_layout)
        layout.addSpacing(15)
        input_layout = QHBoxLayout()
        self.phrase_input = QLineEdit()
        self.phrase_input.setPlaceholderText("请输入答案...")
        self.phrase_meaning_input = QLineEdit()
        self.phrase_meaning_input.setPlaceholderText("请输入答案...")
        for inp in (self.phrase_input, self.phrase_meaning_input):
            inp.setStyleSheet("padding: 8px 10px; border: 1px solid #e0e0e0; border-radius: 6px;")
        input_layout.addWidget(self.phrase_input)
        input_layout.addWidget(self.phrase_meaning_input)
        layout.addLayout(input_layout)
        layout.addSpacing(15)
        self.phrase_list = QListWidget()
        self.phrase_list.setFont(self.font)
        self.phrase_list.setStyleSheet("border: 1px solid #e0e0e0; border-radius: 6px;")
        self.phrase_list.itemDoubleClicked.connect(self.on_phrase_list_double_click)
        layout.addWidget(self.phrase_list)
        self.phrase_import_btn.clicked.connect(self.import_phrase_lib)
        self.phrase_export_btn.clicked.connect(self.export_phrase_lib)
        self.phrase_add_btn.clicked.connect(self.add_phrase)
        self.phrase_del_btn.clicked.connect(self.delete_phrase)
    def on_phrase_list_double_click(self, item):
        phrase = re.sub(r'\s*\[.*?\]\s*$', '', item.text().split(" - ")[0]).strip()
        self.speak(phrase)
    def setup_phrase_random_tab(self):
        layout = QVBoxLayout(self.phrase_random)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)
        mode_layout = QHBoxLayout()
        mode_layout.addStretch()
        mode_label = QLabel("")
        mode_label.setFont(self.font)
        self.phrase_mode_en2zh = QRadioButton("英译中(显示英文,输入中文)")
        self.phrase_mode_zh2en = QRadioButton("中译英(显示中文,输入英文)")
        self.phrase_mode_en2zh.setChecked(True)
        self.phrase_mode_group = QButtonGroup()
        self.phrase_mode_group.addButton(self.phrase_mode_en2zh)
        self.phrase_mode_group.addButton(self.phrase_mode_zh2en)
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.phrase_mode_en2zh)
        mode_layout.addWidget(self.phrase_mode_zh2en)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        layout.addSpacing(10)
        self.phrase_card = QLabel("")
        self.phrase_card.setFont(QFont("微软雅黑", 24, QFont.Bold))
        self.phrase_card.setAlignment(Qt.AlignCenter)
        self.phrase_card.setWordWrap(True)
        self.phrase_card.setStyleSheet("background-color: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 10px; padding: 30px;")
        layout.addWidget(self.phrase_card)
        layout.addSpacing(15)
        self.phrase_meaning_label = QLabel()
        self.phrase_meaning_label.setFont(QFont("微软雅黑", 16))
        self.phrase_meaning_label.setAlignment(Qt.AlignCenter)
        self.phrase_meaning_label.setWordWrap(True)
        self.phrase_meaning_label.setVisible(False)
        layout.addWidget(self.phrase_meaning_label)
        layout.addSpacing(15)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        self.phrase_start_btn = QPushButton("开始练习")
        self.phrase_show_btn = QPushButton("查看答案")
        self.phrase_speak_btn = QPushButton("\U0001f50a 播报完整短语")
        self.phrase_mastered_btn = QPushButton("已掌握")
        self.phrase_unmastered_btn = QPushButton("已掌握")
        for btn in (self.phrase_start_btn, self.phrase_show_btn, self.phrase_speak_btn, self.phrase_mastered_btn, self.phrase_unmastered_btn):
            btn.setStyleSheet("""
                QPushButton { background-color: #4a90e2; color: white; font-size: 14px;
                              padding: 10px 25px; min-width: 100px;
                              border-radius: 8px; border: none; }
                QPushButton:hover { background-color: #357abd; }
            """)
            btn.setMinimumWidth(100)
        self.phrase_show_btn.setEnabled(False)
        self.phrase_speak_btn.setEnabled(False)
        self.phrase_mastered_btn.setEnabled(False)
        self.phrase_unmastered_btn.setEnabled(False)
        btn_layout.addWidget(self.phrase_start_btn)
        btn_layout.addWidget(self.phrase_show_btn)
        btn_layout.addWidget(self.phrase_speak_btn)
        btn_layout.addWidget(self.phrase_mastered_btn)
        btn_layout.addWidget(self.phrase_unmastered_btn)
        layout.addLayout(btn_layout)
        layout.addSpacing(20)
        line = QLabel("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        line.setAlignment(Qt.AlignCenter)
        line.setStyleSheet("color: #cccccc;")
        layout.addWidget(line)
        layout.addSpacing(15)
        dict_title = QLabel("\U0001f4dd 听写模式：根据上方内容输入答案，系统自动验证")
        dict_title.setFont(self.font)
        dict_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(dict_title)
        layout.addSpacing(10)
        input_row = QHBoxLayout()
        input_row.setSpacing(15)
        self.phrase_dict_input = QLineEdit()
        self.phrase_dict_input.setPlaceholderText("请输入答案...")
        self.phrase_dict_input.returnPressed.connect(self.check_phrase_dictation)
        self.phrase_dict_input.setStyleSheet("padding: 10px; border: 1px solid #e0e0e0; border-radius: 6px; font-size: 14px;")
        self.phrase_dict_check = QPushButton("验证答案")
        self.phrase_dict_next = QPushButton("下一题")
        for btn in (self.phrase_dict_check, self.phrase_dict_next):
            btn.setStyleSheet("""
                QPushButton { background-color: #4a90e2; color: white; font-size: 14px;
                              padding: 10px 20px; min-width: 80px;
                              border-radius: 6px; border: none; }
                QPushButton:hover { background-color: #357abd; }
            """)
        self.phrase_dict_next.setStyleSheet("background-color: #6c757d;")
        input_row.addWidget(self.phrase_dict_input)
        input_row.addWidget(self.phrase_dict_check)
        input_row.addWidget(self.phrase_dict_next)
        layout.addLayout(input_row)
        layout.addSpacing(10)
        self.phrase_dict_result = QLabel()
        self.phrase_dict_result.setAlignment(Qt.AlignCenter)
        self.phrase_dict_result.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.phrase_dict_result)
        layout.addStretch()
        self.phrase_start_btn.clicked.connect(self.start_phrase_random)
        self.phrase_show_btn.clicked.connect(self.show_phrase_meaning)
        self.phrase_speak_btn.clicked.connect(self.speak_phrase_card)
        self.phrase_mastered_btn.clicked.connect(self.phrase_mark_mastered)
        self.phrase_unmastered_btn.clicked.connect(self.phrase_mark_unmastered)
        self.phrase_dict_check.clicked.connect(self.check_phrase_dictation)
        self.phrase_dict_next.clicked.connect(self.next_phrase_dictation)
        self.phrase_mode_en2zh.toggled.connect(self.refresh_phrase_display)
        self.phrase_mode_zh2en.toggled.connect(self.refresh_phrase_display)
        self.current_phrase = None
    def _on_phrase_grade_changed(self, grade_text):
        """年级筛选变化时刷新短语列表"""
        self.update_phrase_list()
    def _get_phrase_display_text(self):
        if self.current_phrase is None:
            return ""
        if self.phrase_mode_en2zh.isChecked():
            return self.current_phrase
        else:
            meaning = self.phrase_lib.get(self.current_phrase, "")
            chinese = re.sub(r'[a-zA-Z\s]', '', meaning)
            if chinese:
                return chinese
            return meaning
    def refresh_phrase_display(self):
        if self.current_phrase:
            self.phrase_card.setText(self._get_phrase_display_text())
            self.phrase_meaning_label.setVisible(False)
            self.phrase_meaning_label.setText("")
            self.phrase_dict_input.clear()
            self.phrase_dict_result.setText("")
            if self.phrase_mode_en2zh.isChecked():
                self.phrase_dict_input.setPlaceholderText("请输入答案...")
            else:
                self.phrase_dict_input.setPlaceholderText("请输入答案...")
    def start_phrase_random(self):
        if not self.phrase_lib:
            QMessageBox.warning(self, "提示", "短语库为空，请先通过「短语管理」导入或添加短语")
            return
        multi_word_phrases = [p for p in self.phrase_lib.keys() if " " in p]
        if not multi_word_phrases:
            reply = QMessageBox.question(self, "填充短语", "当前短语库中没有完整的短语（包含空格）。是否从系统内置短语库中填充？（这会添加约20道练习短语，不会删除已有的单词）",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                added = 0
                for phrase, meaning, *_ in BUILTIN_PHRASE_LIST:
                    if phrase not in self.phrase_lib:
                        self.phrase_lib[phrase] = meaning
                        added += 1
                self.save_phrase_lib()
                self.update_phrase_list()
                QMessageBox.information(self, "成功", f"已添加 {added} 个短语")
                multi_word_phrases = [p for p in self.phrase_lib.keys() if " " in p]
                if not multi_word_phrases:
                    QMessageBox.warning(self, "提示", "自定义短语不能为空")
                    return
            else:
                QMessageBox.warning(self, "提示", "没有可用的多单词短语")
        self.current_phrase = random.choice(multi_word_phrases)
        self.phrase_card.setText(self._get_phrase_display_text())
        self.phrase_meaning_label.setVisible(False)
        self.phrase_meaning_label.setText("")
        self.phrase_dict_input.clear()
        self.phrase_dict_result.setText("")
        self.phrase_show_btn.setEnabled(True)
        self.phrase_speak_btn.setEnabled(True)
        self.phrase_mastered_btn.setEnabled(True)
        self.phrase_unmastered_btn.setEnabled(True)
        if self.phrase_mode_en2zh.isChecked():
            self.phrase_dict_input.setPlaceholderText("请输入答案...")
        else:
            self.phrase_dict_input.setPlaceholderText("请输入答案...")
    def show_phrase_meaning(self):
        if self.current_phrase:
            meaning = self.phrase_lib[self.current_phrase]
            chinese = re.sub(r'[a-zA-Z\s]', '', meaning)
            if chinese:
                meaning = chinese
            self.phrase_meaning_label.setText(meaning)
            self.phrase_meaning_label.setVisible(True)
    def speak_phrase_card(self):
        text = self._get_phrase_display_text()
        if text:
            self.speak(text)
    def check_phrase_dictation(self):
        if self.current_phrase is None:
            QMessageBox.warning(self, "请先开始练习")
            return
        user = self.phrase_dict_input.text().strip()
        if not user:
            self.phrase_dict_result.setText("请输入答案...")
            self.phrase_dict_result.setStyleSheet("color: orange;")
            return
        if self.phrase_mode_en2zh.isChecked():
            correct = self.phrase_lib[self.current_phrase]
            correct = re.sub(r'[a-zA-Z\s]', '', correct)
            if self._clean(user) == self._clean(correct):
                self.phrase_dict_result.setText("✅ 回答正确！")
                self.phrase_dict_result.setStyleSheet("color: green; font-size: 14px;")
                self._check_star_award("phrase")
            else:
                self.phrase_dict_result.setText(f"❌ 错误，正确答案：{correct}")
                self.phrase_dict_result.setStyleSheet("color: red; font-size: 14px;")
                self._reward_wrong_answer()
        else:
            correct = self.current_phrase
            if self._clean(user) == self._clean(correct):
                self.phrase_dict_result.setText("✅ 回答正确！")
                self.phrase_dict_result.setStyleSheet("color: green; font-size: 14px;")
                self._check_star_award("phrase")
            else:
                self.phrase_dict_result.setText(f"❌ 错误，正确答案：{correct}")
                self.phrase_dict_result.setStyleSheet("color: red; font-size: 14px;")
                self._reward_wrong_answer()
    def next_phrase_dictation(self):
        self.start_phrase_random()
    def phrase_mark_mastered(self):
        self.next_phrase_dictation()
    def phrase_mark_unmastered(self):
        if self.current_phrase is None:
            return
        phrase = self.current_phrase
        meaning = self.phrase_lib[phrase]
        meaning = re.sub(r'[a-zA-Z\s]', '', meaning)
        existing = next((r for r in self.phrase_review_records if r["word"] == phrase), None)
        today = datetime.now().date()
        if existing:
            existing["next_review_date"] = today + timedelta(days=REVIEW_CYCLES[0])
            existing["cycle_index"] = 0
        else:
            self.phrase_review_records.append({
                "word": phrase, "meaning": meaning,
                "next_review_date": today + timedelta(days=REVIEW_CYCLES[0]),
                "cycle_index": 0
            })
        self.save_phrase_review_records()
        self.update_phrase_review_tip()
        QMessageBox.information(self, "提示", f"{phrase} 已加入学习队列")
        self.next_phrase_dictation()
    def setup_phrase_review_tab(self):
        layout = QVBoxLayout(self.phrase_review)
        layout.setContentsMargins(30, 20, 30, 20)
        self.phrase_review_tip = QLabel()
        self.phrase_review_tip.setFont(self.font)
        self.phrase_review_tip.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.phrase_review_tip)
        self.phrase_review_card = QLabel("")
        self.phrase_review_card.setFont(QFont("微软雅黑", 24, QFont.Bold))
        self.phrase_review_card.setAlignment(Qt.AlignCenter)
        self.phrase_review_card.setWordWrap(True)
        self.phrase_review_card.setStyleSheet("background-color: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 10px; padding: 30px;")
        layout.addWidget(self.phrase_review_card)
        self.phrase_review_meaning = QLabel()
        self.phrase_review_meaning.setFont(QFont("微软雅黑", 16))
        self.phrase_review_meaning.setAlignment(Qt.AlignCenter)
        self.phrase_review_meaning.setWordWrap(True)
        self.phrase_review_meaning.setVisible(False)
        layout.addWidget(self.phrase_review_meaning)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        self.phrase_review_start_btn = QPushButton("开始练习")
        self.phrase_review_show_btn = QPushButton("查看答案")
        self.phrase_review_speak_btn = QPushButton("\U0001f50a 播报完整短语")
        self.phrase_review_mastered_btn = QPushButton("已掌握")
        self.phrase_review_unmastered_btn = QPushButton("已掌握")
        for btn in (self.phrase_review_start_btn, self.phrase_review_show_btn, self.phrase_review_speak_btn,
                    self.phrase_review_mastered_btn, self.phrase_review_unmastered_btn):
            btn.setStyleSheet("""
                QPushButton { background-color: #4a90e2; color: white; font-size: 14px;
                              padding: 10px 25px; min-width: 100px;
                              border-radius: 8px; border: none; }
                QPushButton:hover { background-color: #357abd; }
            """)
            btn.setMinimumWidth(100)
        self.phrase_review_show_btn.setEnabled(False)
        self.phrase_review_speak_btn.setEnabled(False)
        self.phrase_review_mastered_btn.setEnabled(False)
        self.phrase_review_unmastered_btn.setEnabled(False)
        btn_layout.addWidget(self.phrase_review_start_btn)
        btn_layout.addWidget(self.phrase_review_show_btn)
        btn_layout.addWidget(self.phrase_review_speak_btn)
        btn_layout.addWidget(self.phrase_review_mastered_btn)
        btn_layout.addWidget(self.phrase_review_unmastered_btn)
        layout.addLayout(btn_layout)
        self.phrase_review_start_btn.clicked.connect(self.start_phrase_review)
        self.phrase_review_show_btn.clicked.connect(self.show_phrase_review_meaning)
        self.phrase_review_speak_btn.clicked.connect(lambda: self.speak(self.current_review_phrase["word"]) if self.current_review_phrase else None)
        self.phrase_review_mastered_btn.clicked.connect(self.phrase_review_mastered)
        self.phrase_review_unmastered_btn.clicked.connect(self.phrase_review_unmastered)
        self.current_review_phrase = None
    # ---------- 短语补全新功能(内置填空，间距优化)----------
    def setup_phrase_completion_tab(self):
        main_layout = QVBoxLayout(self.phrase_completion)
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(20)
        self.phrase_completion_title = QLabel("短语补全练习")
        self.phrase_completion_title.setFont(self.title_font)
        self.phrase_completion_title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.phrase_completion_title)
        self.phrase_completion_container = QWidget()
        self.phrase_completion_container.setStyleSheet("background-color: transparent; border: none;")
        self.phrase_completion_layout = QHBoxLayout(self.phrase_completion_container)
        self.phrase_completion_layout.setAlignment(Qt.AlignCenter)
        self.phrase_completion_layout.setSpacing(10)   # 单词之间适当间距
        main_layout.addWidget(self.phrase_completion_container)
        self.phrase_completion_meaning_label = QLabel()
        self.phrase_completion_meaning_label.setFont(QFont("微软雅黑", 14))
        self.phrase_completion_meaning_label.setAlignment(Qt.AlignCenter)
        self.phrase_completion_meaning_label.setStyleSheet("color: #555;")
        main_layout.addWidget(self.phrase_completion_meaning_label)
        btn_layout = QHBoxLayout()
        self.phrase_completion_check_btn = QPushButton("验证答案")
        self.phrase_completion_next_btn = QPushButton("下一题")
        for btn in (self.phrase_completion_check_btn, self.phrase_completion_next_btn):
            btn.setStyleSheet("""
                QPushButton { background-color: #4a90e2; color: white; font-size: 14px;
                              padding: 10px 20px; min-width: 100px;
                              border-radius: 6px; border: none; }
                QPushButton:hover { background-color: #357abd; }
            """)
        self.phrase_completion_next_btn.setStyleSheet("background-color: #6c757d;")
        btn_layout.addStretch()
        btn_layout.addWidget(self.phrase_completion_check_btn)
        btn_layout.addWidget(self.phrase_completion_next_btn)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)
        self.phrase_completion_result = QLabel()
        self.phrase_completion_result.setAlignment(Qt.AlignCenter)
        self.phrase_completion_result.setStyleSheet("font-size: 14px;")
        main_layout.addWidget(self.phrase_completion_result)
        main_layout.addStretch()
        self.phrase_completion_check_btn.clicked.connect(self.check_phrase_completion)
        self.phrase_completion_next_btn.clicked.connect(self.next_phrase_completion)
        self.current_phrase_obj = None
        self.current_phrase_missing = ""
        self.current_phrase_fill_widget = None
        self.show_phrase_completion_placeholder()
    def show_phrase_completion_placeholder(self):
        self.clear_phrase_completion_layout()
        label = QLabel("")
        label.setFont(QFont("微软雅黑", 20))
        label.setAlignment(Qt.AlignCenter)
        self.phrase_completion_layout.addWidget(label)
        self.phrase_completion_meaning_label.setText("")
    def clear_phrase_completion_layout(self):
        while self.phrase_completion_layout.count():
            item = self.phrase_completion_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    def next_phrase_completion(self):
        if not self.phrase_lib:
            QMessageBox.warning(self, "提示")
            self.show_phrase_completion_placeholder()
            return
        multi_word_phrases = [p for p in self.phrase_lib.keys() if " " in p]
        if not multi_word_phrases:
            QMessageBox.warning(self, "提示")
            self.show_phrase_completion_placeholder()
            return
        # 杩囨护鎺夊彧鍚知竴涓复瘝鐨勭煭璇衣
        valid_phrases = [p for p in multi_word_phrases if len(p.split()) > 1]
        if not valid_phrases:
            QMessageBox.warning(self, "提示")
            self.show_phrase_completion_placeholder()
            return
        phrase = random.choice(valid_phrases)
        words = phrase.split()
        pos = random.randint(0, len(words)-1)
        missing_word = words[pos]
        self.clear_phrase_completion_layout()
        # 使用自定义字体风格控件(字号填空)
        fill_widget = PhraseFillWidget(phrase, pos, words, missing_word)
        self.phrase_completion_layout.addWidget(fill_widget)
        self.current_phrase_fill_widget = fill_widget
        self.current_phrase_obj = phrase
        self.current_phrase_missing = missing_word  # 鏁翠釜缂哄单词锛堜繚鐣欑敤浜庢樉绀猴級
        self.phrase_completion_meaning_label.setText(f"释义：{self.phrase_lib[phrase]}")
        self.phrase_completion_result.setText("")
        if hasattr(fill_widget, 'input_label'):
            fill_widget.input_label.setFocus()
    def check_phrase_completion(self):
        if self.current_phrase_obj is None:
            QMessageBox.warning(self, "请先开始练习")
            return
        if self.current_phrase_fill_widget is None:
            return
        user = self.current_phrase_fill_widget.user_input.strip()
        if not user:
            self.phrase_completion_result.setText("...")
            self.phrase_completion_result.setStyleSheet("color: orange;")
            return
        if user.lower() == getattr(self, 'current_phrase_missing', '').lower():
            self.phrase_completion_result.setText("✅ 回答正确！")
            self.phrase_completion_result.setStyleSheet("color: green; font-size: 14px;")
            # 播放完整短语 + 播报发音
            phrase = str(self.current_phrase_obj) if self.current_phrase_obj else ""
            self.speak(f"{phrase}. Correct! Very good!")
            self._check_star_award("phrase")
        else:
            correct = getattr(self, 'current_phrase_missing', self.current_phrase_missing)
            self.phrase_completion_result.setText(f"❌ 错误，正确答案：{correct}")
            self.phrase_completion_result.setStyleSheet("color: red; font-size: 14px;")
            # 播放完整短语 + 播报发音
            phrase = str(self.current_phrase_obj) if self.current_phrase_obj else ""
            self.speak(f"Wrong! The answer is {phrase}. Keep trying, you can do it!")
            self._reward_wrong_answer()
    # ---------- 短语数据操作 ----------
    def import_phrase_lib(self):
        path, _ = QFileDialog.getOpenFileName(self, "导入短语", "", "TXT (*.txt)")
        if path:
            with open(path, "r", encoding="utf-8") as f:
                cnt = 0
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    if '|' in line:
                        parts = line.split('|', 1)
                    elif ' ' in line:
                        parts = line.split(' ', 1)
                    else:
                        continue
                    if len(parts) < 2:
                        continue
                    p, m = parts[0].strip(), parts[1].strip()
                    if p and p not in self.phrase_lib:
                        self.phrase_lib[p] = m
                        cnt += 1
            self.save_phrase_lib()
            self.update_phrase_list()
            QMessageBox.information(self, "成功", f"已导入 {cnt} 个短语")
    def export_phrase_lib(self):
        if not self.phrase_lib:
            QMessageBox.warning(self, "提示", "短语库为空")
            return
        path, _ = QFileDialog.getSaveFileName(self, "导出短语", "phrase_lib", "TXT (*.txt)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                for p, m in self.phrase_lib.items():
                    f.write(f"{p}|{m}\n")
            QMessageBox.information(self, "成功", "导出完成")
    def add_phrase(self):
        p = self.phrase_input.text().strip()
        m = self.phrase_meaning_input.text().strip()
        if not p or not m:
            QMessageBox.warning(self, "提示", "请填写短语和含义")
            return
        if p in self.phrase_lib:
            QMessageBox.warning(self, "提示", "短语已存在")
            return
        self.phrase_lib[p] = m
        self.save_phrase_lib()
        self.update_phrase_list()
        self.phrase_input.clear()
        self.phrase_meaning_input.clear()
    def delete_phrase(self):
        cur = self.phrase_list.currentItem()
        if not cur:
            return
        p = cur.text().split(" - ")[0]
        # 检查是否为内置短语
        builtin_phrases = {item[0] for item in BUILTIN_PHRASE_LIST}
        if p in builtin_phrases:
            QMessageBox.warning(self, "禁止删除", f"【{p}】是系统内置短语，不能删除！如需练习请使用随机抽测或短语听写。")
            return
        if QMessageBox.question(self, "确认选择", f"删除短语 {p} ？") == QMessageBox.Yes:
            del self.phrase_lib[p]
            self.phrase_review_records = [r for r in self.phrase_review_records if r["word"] != p]
            self.save_phrase_lib()
            self.save_phrase_review_records()
            self.update_phrase_list()
            self.update_phrase_review_tip()
    def get_next_phrase_review(self):
        today = datetime.now().date()
        due = [r for r in self.phrase_review_records if r["next_review_date"] <= today]
        if due:
            due.sort(key=lambda x: x["next_review_date"])
            return due[0]
        return None
    def start_phrase_review(self):
        rec = self.get_next_phrase_review()
        if not rec:
            QMessageBox.information(self, "复习", "无待复习短语")
            return
        self.current_review_phrase = rec
        self.phrase_review_card.setText(rec["word"])
        self.phrase_review_meaning.setVisible(False)
        self.phrase_review_show_btn.setEnabled(True)
        self.phrase_review_speak_btn.setEnabled(True)
        self.phrase_review_mastered_btn.setEnabled(True)
        self.phrase_review_unmastered_btn.setEnabled(True)
    def show_phrase_review_meaning(self):
        if self.current_review_phrase:
            meaning = self.current_review_phrase["meaning"]
            meaning = re.sub(r'[a-zA-Z\s]', '', meaning)
            self.phrase_review_meaning.setText(meaning)
            self.phrase_review_meaning.setVisible(True)
    def phrase_review_mastered(self):
        if self.current_review_phrase:
            self.phrase_review_records = [r for r in self.phrase_review_records if r["word"] != self.current_review_phrase["word"]]
            self.save_phrase_review_records()
            self.update_phrase_review_tip()
            self.start_phrase_review()
    def phrase_review_unmastered(self):
        if not self.current_review_phrase:
            return
        idx = self.current_review_phrase["cycle_index"]
        if idx + 1 < len(REVIEW_CYCLES):
            self.current_review_phrase["cycle_index"] = idx + 1
            self.current_review_phrase["next_review_date"] = datetime.now().date() + timedelta(days=REVIEW_CYCLES[idx+1])
        else:
            self.phrase_review_records = [r for r in self.phrase_review_records if r["word"] != self.current_review_phrase["word"]]
            QMessageBox.information(self, "提示")
            self.save_phrase_review_records()
            self.update_phrase_review_tip()
            self.start_phrase_review()
            return
        self.save_phrase_review_records()
        self.update_phrase_review_tip()
        QMessageBox.information(self, "复习", f"{self.current_review_phrase['word']} 已掌握！，{REVIEW_CYCLES[idx+1]} 天后再复习")
        self.start_phrase_review()
    def save_phrase_lib(self):
        with open(self.phrase_lib_path, "w", encoding="utf-8") as f:
            for p, m in self.phrase_lib.items():
                f.write(f"{p}|{m}\n")
    def save_phrase_review_records(self):
        with open(self.phrase_review_path, "wb") as f:
            pickle.dump(self.phrase_review_records, f)
    def update_phrase_list(self):
        self.phrase_list.clear()
        grade = self.phrase_grade_combo.currentText()
        for p, m in self.phrase_lib.items():
            if grade != '全部':
                item_grade = self.phrase_to_grade.get(p, '')
                if grade not in item_grade:
                    continue
            self.phrase_list.addItem(f"{p} - {m}")
    def update_phrase_review_tip(self):
        today = datetime.now().date()
        need = sum(1 for r in self.phrase_review_records if r["next_review_date"] <= today)
        self.phrase_review_tip.setText("...")
    # ---------- 英语对话模块 ----------
    def setup_dialogue_module(self):
        # 浣跨敤瀛愭爣绛剧粨鏋勶紙涓庡崟璇嶃佺煭璇解鍧椾竴鑷达級
        self.dialogue_sub_tabs = QTabWidget()
        layout = QVBoxLayout(self.dialogue_tab)
        layout.addWidget(self.dialogue_sub_tabs)
        self.dialogue_manage = QWidget()
        self.dialogue_random = QWidget()
        self.dialogue_completion = QWidget()
        self.dialogue_sub_tabs.addTab(self.dialogue_manage, "对话管理")
        self.dialogue_sub_tabs.addTab(self.dialogue_random, "随机学习")
        self.dialogue_sub_tabs.addTab(self.dialogue_completion, "✍️ 对话补全练习")
        self.dialogue_sub_tabs.setStyleSheet("""
            QTabWidget::tab-bar {alignment: center;}
            QTabBar::tab {
                background-color: #e0e0e0; color: #333; font-size: 13px;
                font-family: 微软雅黑; padding: 8px 20px; margin-right: 5px;
                border-radius: 6px 6px 0 0; border: none;
            }
            QTabBar::tab:selected, QTabBar::tab:hover {
                background-color: #4a90e2; color: white;
            }
            QTabWidget::pane {
                border: 1px solid #e0e0e0; border-radius: 0 0 8px 8px;
                background-color: white;
            }
        """)
        self._setup_dialogue_manage_tab()
        self._setup_dialogue_random_tab()
        self._setup_dialogue_completion_tab()
    def _setup_dialogue_manage_tab(self):
        """功能方法"""
        layout = QVBoxLayout(self.dialogue_manage)
        layout.setContentsMargins(30, 20, 30, 20)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        self.dialogue_import_btn = QPushButton("按钮")
        self.dialogue_export_btn = QPushButton("导出对话")
        self.dialogue_add_btn = QPushButton("添加对话")
        self.dialogue_del_btn = QPushButton("删除选中")
        self.dialogue_speak_btn = QPushButton("\U0001f50a 播报英语对话")
        for btn in (self.dialogue_import_btn, self.dialogue_export_btn, self.dialogue_add_btn,
                    self.dialogue_del_btn, self.dialogue_speak_btn):
            btn.setStyleSheet("""
                QPushButton { background-color: #4a90e2; color: white; padding: 8px 15px;
                              min-width: 100px;
                              border-radius: 6px; border: none; font-size: 12px; }
                QPushButton:hover { background-color: #357abd; }
            """)
            btn.setMinimumWidth(100)
        btn_layout.addWidget(self.dialogue_import_btn)
        btn_layout.addWidget(self.dialogue_export_btn)
        btn_layout.addWidget(self.dialogue_add_btn)
        btn_layout.addWidget(self.dialogue_del_btn)
        btn_layout.addWidget(self.dialogue_speak_btn)
        self.dialogue_speak_btn.clicked.connect(self.speak_dialogue)
        layout.addLayout(btn_layout)
        layout.addSpacing(20)
        splitter = QSplitter(Qt.Horizontal)
        # 对话列表(ListWidget，显示英文标题)
        self.dialogue_list = QListWidget()
        self.dialogue_list.setFont(self.font)
        self.dialogue_list.setMinimumWidth(280)
        self.dialogue_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 6px;
                background: white;
                alternate-background-color: #f8f9fa;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background: #e3f2fd;
                color: #1a73e8;
            }
        """)
        self.dialogue_list.currentRowChanged.connect(self.display_dialogue)
        splitter.addWidget(self.dialogue_list)
        # 可以充晶闈程澘锛氳嫳鏂衣| 涓解枃 宸彸鍒嗘爮
        right_widget = QWidget()
        right_layout = QHBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(10)
        en_widget = QWidget()
        en_layout = QVBoxLayout(en_widget)
        en_layout.setContentsMargins(0, 0, 0, 0)
        self.dialogue_en_text = QTextEdit()
        self.dialogue_en_text.setReadOnly(True)
        self.dialogue_en_text.setTextInteractionFlags(Qt.NoTextInteraction)  # 禁止选择复制
        self.dialogue_en_text.setFont(QFont("微软雅黑", 12))
        self.dialogue_en_text.setStyleSheet("border: 1px solid #ddd; border-radius: 6px; padding: 8px;")
        en_layout.addWidget(QLabel("English:"))
        en_layout.addWidget(self.dialogue_en_text)
        right_layout.addWidget(en_widget)
        zh_widget = QWidget()
        zh_layout = QVBoxLayout(zh_widget)
        zh_layout.setContentsMargins(0, 0, 0, 0)
        self.dialogue_zh_text = QTextEdit()
        self.dialogue_zh_text.setReadOnly(True)
        self.dialogue_zh_text.setTextInteractionFlags(Qt.NoTextInteraction)  # 禁止选择复制
        self.dialogue_zh_text.setFont(QFont("微软雅黑", 12))
        self.dialogue_zh_text.setStyleSheet("border: 1px solid #ddd; border-radius: 6px; padding: 8px;")
        zh_layout.addWidget(QLabel("中文:"))
        zh_layout.addWidget(self.dialogue_zh_text)
        right_layout.addWidget(zh_widget)
        splitter.addWidget(right_widget)
        layout.addWidget(splitter, 1)
        # 底部按钮区（已在上面创建）
        # btn_layout 已在上面定义
    def _setup_dialogue_random_tab(self):
        """随机学习标签ab锛氬乏渚夊満鏅紝可以充晶显示鑻辨枃+涓解枃"""
        layout = QVBoxLayout(self.dialogue_random)
        layout.setContentsMargins(10, 10, 10, 10)
        
        splitter = QSplitter(Qt.Horizontal)
        
        # 宸-晶锛氬満鏅量垪琛衣
        self.dlg_random_list = QListWidget()
        self.dlg_random_list.setFont(self.font)
        self.dlg_random_list.currentRowChanged.connect(self._show_random_dialogue)
        splitter.addWidget(self.dlg_random_list)
        
        # 可以充晶锛氳嫳鏂衣涓解枃显示
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        self.dlg_random_en = QTextEdit()
        self.dlg_random_en.setReadOnly(True)
        self.dlg_random_en.setTextInteractionFlags(Qt.NoTextInteraction)  # 禁止选择复制
        self.dlg_random_en.setFont(QFont("微软雅黑", 14))
        right_layout.addWidget(self.dlg_random_en)
        
        self.dlg_random_zh = QTextEdit()
        self.dlg_random_zh.setReadOnly(True)
        self.dlg_random_zh.setTextInteractionFlags(Qt.NoTextInteraction)  # 禁止选择复制
        self.dlg_random_zh.setFont(QFont("微软雅黑", 14))
        right_layout.addWidget(self.dlg_random_zh)
        
        splitter.addWidget(right_widget)
        layout.addWidget(splitter, 1)
        # 随机学习Tab播报按钮
        speak_btn_row = QHBoxLayout()
        speak_btn_row.addStretch()
        self.dlg_random_speak_btn = QPushButton("\U0001f50a 播报英语")
        self.dlg_random_speak_btn.setFont(QFont("微软雅黑", 12))
        self.dlg_random_speak_btn.setStyleSheet("""
            QPushButton { background-color: #5cb85c; color: white; padding: 8px 20px;
                          border-radius: 6px; border: none; }
            QPushButton:hover { background-color: #449d44; }
        """)
        self.dlg_random_speak_btn.clicked.connect(self._speak_random_dialogue)
        speak_btn_row.addWidget(self.dlg_random_speak_btn)
        layout.addLayout(speak_btn_row)
        # 濉识厖鍒楄
        for d in self.dialogues:
            self.dlg_random_list.addItem(d.get('title', ''))
    def _show_random_dialogue(self, idx):
        """显示选中场景的内容"""
        if 0 <= idx < len(self.dialogues):
            d = self.dialogues[idx]
            self.dlg_random_en.setText(d.get('en', ''))
            self.dlg_random_zh.setText(d.get('zh', ''))
    def _setup_dialogue_completion_tab(self):
        """对话补全练习Tab"""
        layout = QVBoxLayout(self.dialogue_completion)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 椤堕儴标题理琛衣
        header = QHBoxLayout()
        self.dlg_comp_title = QLabel("✍️ 对话补全")
        self.dlg_comp_title.setFont(QFont("微软雅黑", 14, QFont.Bold))
        header.addWidget(self.dlg_comp_title)
        self.dlg_comp_scenario = QLabel("")
        self.dlg_comp_scenario.setFont(QFont("微软雅黑", 11))
        header.addWidget(self.dlg_comp_scenario)
        header.addStretch()
        layout.addLayout(header)
        
        # 涓答嫳文本樉绀哄尯
        comp_splitter = QSplitter(Qt.Horizontal)
        
        # 鑻辨枃鍖衣
        en_container = QWidget()
        en_layout = QVBoxLayout(en_container)
        en_layout.setContentsMargins(8, 4, 8, 4)
        en_label = QLabel("English:")
        en_label.setFont(QFont("微软雅黑", 14, QFont.Bold))
        en_layout.addWidget(en_label)
        self.dlg_comp_en_area = QScrollArea()
        self.dlg_comp_en_area.setWidgetResizable(True)
        self.dlg_comp_en_area.setStyleSheet("QScrollArea { border: 1px solid #ddd; border-radius: 6px; }")
        self.dlg_comp_widget = QWidget()
        self.dlg_comp_en_layout = QVBoxLayout(self.dlg_comp_widget)
        self.dlg_comp_en_layout.setContentsMargins(8, 4, 8, 4)
        self.dlg_comp_en_area.setWidget(self.dlg_comp_widget)
        en_layout.addWidget(self.dlg_comp_en_area)
        comp_splitter.addWidget(en_container)
        
        # 涓解枃鍖衣
        zh_container = QWidget()
        zh_layout = QVBoxLayout(zh_container)
        zh_layout.setContentsMargins(8, 4, 8, 4)
        zh_label = QLabel("中文:")
        zh_label.setFont(QFont("微软雅黑", 14, QFont.Bold))
        zh_layout.addWidget(zh_label)
        self.dlg_comp_zh_area = QScrollArea()
        self.dlg_comp_zh_area.setWidgetResizable(True)
        self.dlg_comp_zh_area.setStyleSheet("QScrollArea { border: 1px solid #ddd; border-radius: 6px; }")
        self.dlg_comp_zh_panel = QLabel()
        self.dlg_comp_zh_panel.setTextInteractionFlags(Qt.NoTextInteraction)  # 禁止选择复制
        self.dlg_comp_zh_panel.setFont(QFont("微软雅黑", 15))
        self.dlg_comp_zh_panel.setWordWrap(True)
        self.dlg_comp_zh_panel.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.dlg_comp_zh_panel.setStyleSheet("padding: 8px;")
        self.dlg_comp_zh_area.setWidget(self.dlg_comp_zh_panel)
        zh_layout.addWidget(self.dlg_comp_zh_area)
        comp_splitter.addWidget(zh_container)
        
        layout.addWidget(comp_splitter, 1)
        
        # 底部：结构按钮
        bottom = QHBoxLayout()
        self.dlg_comp_result = QLabel("")
        self.dlg_comp_result.setFont(QFont("微软雅黑", 11))
        self.dlg_comp_result.setStyleSheet("color: #666;")
        bottom.addWidget(self.dlg_comp_result)
        bottom.addStretch()
        
        hint = QLabel("")
        hint.setFont(QFont("微软雅黑", 10))
        hint.setStyleSheet("color: #999;")
        bottom.addWidget(hint)
        
        self.dlg_comp_check_btn = QPushButton("检查答案")
        self.dlg_comp_check_btn.setFont(QFont("微软雅黑", 11))
        self.dlg_comp_check_btn.clicked.connect(self._check_dialogue_completion)
        bottom.addWidget(self.dlg_comp_check_btn)
        
        self.dlg_comp_next_btn = QPushButton("下一题")
        self.dlg_comp_next_btn.setFont(QFont("微软雅黑", 11))
        self.dlg_comp_next_btn.clicked.connect(self._next_dialogue_completion)
        bottom.addWidget(self.dlg_comp_next_btn)
        self.dlg_comp_speak_btn = QPushButton("\U0001f50a 播报")
        self.dlg_comp_speak_btn.setFont(QFont("微软雅黑", 11))
        self.dlg_comp_speak_btn.setStyleSheet("""
            QPushButton { background-color: #5cb85c; color: white; padding: 6px 15px;
                          border-radius: 6px; border: none; }
            QPushButton:hover { background-color: #449d44; }
        """)
        self.dlg_comp_speak_btn.clicked.connect(self._speak_comp_dialogue)
        bottom.addWidget(self.dlg_comp_speak_btn)
        
        layout.addLayout(bottom)
        
        # 初始化鍖衣
        self._current_dlg_idx = 0
        self._current_dlg_missing_idx = 0
        self._next_dialogue_completion()
    def _next_dialogue_completion(self):
        """鐢熸垚涓嬩竴涓试批璇濊鍏录粌涔衣- 鏍规嵁绡囧箙鎸栫澶氬彞"""
        import random
        if not self.dialogues:
            return
        
        # 随机选一个场景
        self._current_dlg_idx = random.randint(0, len(self.dialogues) - 1)
        dlg = self.dialogues[self._current_dlg_idx]
        
        # 更新标题
        self.dlg_comp_scenario.setText(dlg.get('title', ''))
        
        # 清空内容
        while self.dlg_comp_en_layout.count():
            item = self.dlg_comp_en_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 解析对话内容
        en_text = dlg.get('en', '')
        lines = en_text.splitlines()
        
        # 获取闈炵琛衣
        non_empty_lines = [i for i, l in enumerate(lines) if l.strip()]
        if not non_empty_lines:
            return
        
        # 鏍规嵁绡囧箙冠词畾鎸栫鏁伴噺
        total_lines = len(non_empty_lines)
        if total_lines <= 3:
            blank_count = 1  # 鐭组批璇濇寲1可以衣
        elif total_lines <= 6:
            blank_count = random.choice([1, 2])  # 涓释瓑鎸衣-2可以衣
        elif total_lines <= 10:
            blank_count = random.choice([2, 3])  # 杈冮暱鎸衣-3可以衣
        else:
            blank_count = random.choice([3, 4])  # 闀垮批璇濇寲3-4可以衣
        
        # 随机选择要填空的行（不重复）
        blank_indices = sorted(random.sample(non_empty_lines, min(blank_count, total_lines)))
        
        # 存储答案: {行号: 完整句子}
        self._missing_sentences = {}
        for idx in blank_indices:
            self._missing_sentences[idx] = lines[idx].strip()
        
        # 显示所有输格
        font_size = 15
        line_font = QFont("微软雅黑", font_size)
        self.dlg_comp_inputs = []  # 瀛樺偍所有输入框待验证
        
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            
            if i in self._missing_sentences:
                # 鎸栫琛衣- 显示输入妗衣
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(4, 8, 4, 8)
                
                # 琛屽墠缂鏍囩 (濡衣"Tom:" 鎴衣"Lucy:")
                stripped = line.strip()
                prefix = ""
                for p in ["Tom:", "Lucy:", "C:", "D:", "A:", "B:", "C:", "D:"]:
                    if stripped.startswith(p):
                        prefix = p
                        break
                
                if prefix:
                    pref_lbl = QLabel(prefix)
                    pref_lbl.setFont(line_font)
                    pref_lbl.setStyleSheet("color: #333; padding-right: 6px;")
                    row_layout.addWidget(pref_lbl)
                
                # 输入妗衣- 濉识畬鏁村彞
                self.inp = QLineEdit()
                self.inp.setFont(line_font)
                self.inp.setPlaceholderText("请输入答案...")
                self.inp.setMinimumHeight(40)
                self.inp.setStyleSheet("""
                    QLineEdit {
                        color: #1cb0f6;
                        background: transparent;
                        border: none;
                        border-bottom: 3px solid #1cb0f6;
                        padding: 4px 8px;
                    }
                """)
                row_layout.addWidget(self.inp, 1)
                self.dlg_comp_inputs.append(self.inp)
                
                self.dlg_comp_en_layout.addWidget(row_widget)
            else:
                # 鏅证氳格 - 姝E父显示
                lbl = QLabel(line)
                lbl.setFont(line_font)
                lbl.setWordWrap(True)
                lbl.setStyleSheet("padding: 6px 4px; color: #333;")
                self.dlg_comp_en_layout.addWidget(lbl)
        
        self.dlg_comp_en_layout.addStretch()
        
        # 显示涓解枃
        self.dlg_comp_zh_panel.setText(dlg.get('zh', ''))
        self.dlg_comp_result.setText("")
        # 鑱氱劍鍒扮单涓涓复緭鍏
        if self.dlg_comp_inputs:
            self.dlg_comp_inputs[0].setFocus()
    def _check_dialogue_completion(self):
        """验证答案 - 检查墍鏈夋寲绌哄彞瀛衣"""
        import re
        
        if not hasattr(self, '_missing_sentences') or not hasattr(self, 'dlg_comp_inputs'):
            return
        
        # 鏍囧噯鍖栨瘮杈冿細蹇界暐大小鍐欍佹爣鐐广佸套浣欑鏍衣
        def normalize(s):
            s = s.lower()
            s = re.sub(r'[^\w\s]', '', s)  # 鍘绘爣点
            s = re.sub(r'\s+', ' ', s).strip()  # 鍚堝苟绌烘牸
            return s
        
        # 鏀堕泦鎵鏈夌瓟妗衣
        results = []
        blank_indices = sorted(self._missing_sentences.keys())
        
        for i, idx in enumerate(blank_indices):
            if i >= len(self.dlg_comp_inputs):
                break
            user_ans = self.dlg_comp_inputs[i].text().strip()
            correct = self._missing_sentences[idx].strip()
            
            norm_user = normalize(user_ans)
            norm_correct = normalize(correct)
            
            if norm_user and norm_user == norm_correct:
                results.append(True)
            else:
                results.append(False)
        
        # 显示结构灉
        total = len(results)
        correct_count = sum(results)
        
        if correct_count == total:
            self.dlg_comp_result.setText("回答正确!")
            self.dlg_comp_result.setStyleSheet("color: green; font-size: 14px; font-weight: bold;")
            self.dialogue_streak += 1
            self.total_dialogue_correct += 1
            self._check_star_award("dialogue")
            self._update_reward_display()
        else:
            # 显示正确答案
            correct_texts = list(self._missing_sentences.values())
            answers_display = " | ".join(correct_texts[:3])
            hint = "..." if len(correct_texts) > 3 else ""
            self.dlg_comp_result.setText(f"❌ 错误！正确答案：{answers_display}{hint}")
            self.dlg_comp_result.setStyleSheet("color: red; font-size: 13px;")
            self.dialogue_streak = 0
            self._update_reward_display()
            self.speak("Try again. Keep practicing!")
    def closeEvent(self, event):
        """窗口关闭时停止计时并保存数据"""
        # 停止学习计时器
        if hasattr(self, 'study_timer'):
            self.study_timer.stop()
        # 停止滚动字幕
        if hasattr(self, '_ticker_timer'):
            self._ticker_timer.stop()
        # 保存奖励数据
        if hasattr(self, 'reward'):
            self.reward.save_data()
        event.accept()
    def display_dialogue(self):
        """功能方法"""
        idx = self.dialogue_list.currentRow()
        if 0 <= idx < len(self.dialogues):
            d = self.dialogues[idx]
            self.dialogue_en_text.setText(d.get('en', ''))
            self.dialogue_zh_text.setText(d.get('zh', ''))
    def add_dialogue(self):
        """添加对话"""
        QMessageBox.information(self, "提示", "添加对话功能尚未开启")
    def delete_dialogue(self):
        """删除对话框(确认)"""
        QMessageBox.information(self, "提示", "内置对话只能查看，不能删除")
    def import_dialogues(self):
        """导入对话"""
        QMessageBox.information(self, "提示", "导入功能尚未开启")
    def export_dialogues(self):
        """导出对话"""
        QMessageBox.information(self, "提示", "导出功能尚未开启")
    def speak_dialogue(self):
        """鏈楄备对话锛堢填鐞員ab锛衣"""
        idx = self.dialogue_list.currentRow()
        if 0 <= idx < len(self.dialogues):
            d = self.dialogues[idx]
            self.speak(d.get('en', ''))
    def _speak_random_dialogue(self):
        """鏈楄备随机学习Tab鐨勫綋鍓嶅批璇衣"""
        idx = getattr(self, 'dlg_random_list', None)
        if idx is not None:
            idx = idx.currentRow()
        if idx is not None and 0 <= idx < len(self.dialogues):
            d = self.dialogues[idx]
            self.speak(d.get('en', ''))
    def _speak_comp_dialogue(self):
        """鏈楄备补全练习Tab鐨勮嫳鏂囧唴瀹癸紙浠庡綋鍓嶅批璇濇暟鎹题备可以栵級"""
        idx = getattr(self, '_current_dlg_idx', None)
        if idx is not None and 0 <= idx < len(self.dialogues):
            d = self.dialogues[idx]
            self.speak(d.get('en', ''))
    def update_dialogue_list(self):
        """更新对话列表"""
        self.dialogue_list.clear()
        for d in self.dialogues:
            self.dialogue_list.addItem(d.get('title', ''))
    def _setup_grammar_tab(self):
        """设置语法Tab(含知识查看和语法练习)"""
        # 使用tab结构
        self.grammar_sub_tabs = QTabWidget()
        layout = QVBoxLayout(self.grammar_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.grammar_sub_tabs)
        self.grammar_sub_tabs.setStyleSheet("""
            QTabWidget::tab-bar {alignment: left;}
            QTabBar::tab {
                background-color: #e8e8e8; color: #333; font-size: 14px;
                font-family: 微软雅黑; padding: 8px 28px;
                border-radius: 6px 6px 0 0;
            }
            QTabBar::tab:selected { background-color: #4a90e2; color: white; }
        """)
        # Tab1: 语法知识锛堝師鍐呭确锛衣
        self.grammar_knowledge = QWidget()
        self._setup_grammar_knowledge_tab()
        self.grammar_sub_tabs.addTab(self.grammar_knowledge, "\U0001f4d6 语法知识")
        # Tab2: 语法练习(新内容)
        self.grammar_exercise = QWidget()
        self._setup_grammar_exercise_tab()
        self.grammar_sub_tabs.addTab(self.grammar_exercise, "✍️ 语法练习")
    def _setup_grammar_knowledge_tab(self):
        """语法知识Tab锛堝師_setup_grammar_tab鍐呭确锛衣"""
        layout = QVBoxLayout(self.grammar_knowledge)
        layout.setContentsMargins(10, 10, 10, 10)
        # 年级选择下拉框
        grade_layout = QHBoxLayout()
        grade_label = QLabel('选择年级')
        grade_label.setFont(QFont('微软雅黑', 12))
        self.grade_combo = QComboBox()
        self.grade_combo.addItems(['七年级上学期', '七年级下学期', '八年级上学期', '八年级下学期', '九年级'])
        self.grade_combo.setFont(QFont('微软雅黑', 12))
        self.grade_combo.currentTextChanged.connect(self._load_grammar_list)
        grade_layout.addWidget(grade_label)
        grade_layout.addWidget(self.grade_combo)
        grade_layout.addStretch()
        layout.addLayout(grade_layout)
        # 宸-晶语法鐐瑰垪琛衣
        self.grammar_list = QListWidget()
        self.grammar_list.setFont(QFont('微软雅黑', 13))
        self.grammar_list.itemClicked.connect(self._show_grammar_detail)
        # 可以充晶语法璇】儏显示鍖衣
        self.grammar_detail = QTextEdit()
        self.grammar_detail.setReadOnly(True)
        self.grammar_detail.setFont(QFont('微软雅黑', 14))
        self.grammar_detail.setStyleSheet(
            "QTextEdit {"
            "    background-color: white;"
            "    border: 1px solid #ddd;"
            "    border-radius: 5px;"
            "    padding: 10px;"
            "}"
        )
        # 使用splitter分割
        splitter = QSplitter(Qt.Horizontal)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.grammar_list)
        splitter.addWidget(left_widget)
        
        # 显示学习方法+ 播报按钮
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self.grammar_detail)
        
        # 播报按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        # 练习按钮
        start_btn = QPushButton("开始练习")
        start_btn.setStyleSheet("""
            QPushButton { background-color: #4a90e2; color: white; padding: 8px 20px;
                         border-radius: 5px; border: none; font-size: 13px; font-weight: bold; }
            QPushButton:hover { background-color: #357abd; }
        """)
        start_btn.setFixedWidth(120)
        btn_layout.addWidget(start_btn)
        btn_layout.addStretch()
        right_layout.addLayout(btn_layout)
        splitter.addWidget(right_widget)
        layout.addWidget(splitter)
        start_btn.clicked.connect(self._start_grammar_exercise)
    def _load_grammar_list(self, grade_text):
        """根据年级加载语法知识点列表"""
        self.grammar_list.clear()
        grade_map = {
            "七年级上学期": "七年级",
            "七年级下学期": "七年级",
            "八年级上学期": "八年级",
            "八年级下学期": "八年级",
            "九年级": "九年级",
        }
        grade_key = grade_map.get(grade_text, "七年级")
        if grade_key in BUILTIN_GRAMMAR_EXERCISES:
            for unit in BUILTIN_GRAMMAR_EXERCISES[grade_key]:
                item = QListWidgetItem(unit["title"])
                item.setData(32, unit)  # UserRole
                self.grammar_list.addItem(item)
        if self.grammar_list.count() > 0:
            self.grammar_list.setCurrentRow(0)
    def _show_grammar_detail(self, item):
        """显示语法知识点详情"""
        unit = item.data(32)
        if not unit:
            return
        html = "<h2 style='color:#4a90e2;'>{title}</h2>".format(title=unit.get("title", ""))
        if "explanation" in unit:
            html += "<p style='font-size:14px;line-height:1.8'>{}</p>".format(unit["explanation"])
        if "examples" in unit:
            html += "<h3>例句</h3><ul>"
            for ex in unit["examples"]:
                html += "<li>{}</li>".format(ex)
            html += "</ul>"
        if "questions" in unit:
            html += "<h3>练习题 ({count}道)</h3>".format(count=len(unit["questions"]))
        self.grammar_detail.setHtml(html)
    def _setup_grammar_exercise_tab(self):
        """语法练习Tab（填空题）"""
        layout = QVBoxLayout(self.grammar_exercise)
        layout.setContentsMargins(15, 15, 15, 15)
        # 题目显示区
        from PyQt5.QtWidgets import QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit, QProgressBar, QGroupBox, QFormLayout
        self.gr_title_label = QLabel("语法填空练习")
        self.gr_title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        self.gr_title_label.setStyleSheet("color: #333; padding: 10px;")
        layout.addWidget(self.gr_title_label)
        # 进度条
        self.gr_progress = QProgressBar()
        self.gr_progress.setVisible(False)
        layout.addWidget(self.gr_progress)
        # 题目区域
        gr_group = QGroupBox("题目")
        gr_group.setFont(QFont("Microsoft YaHei", 12))
        gr_layout = QVBoxLayout(gr_group)
        self.gr_question_label = QLabel("...")
        self.gr_question_label.setFont(QFont("Microsoft YaHei", 14))
        self.gr_question_label.setWordWrap(True)
        self.gr_question_label.setStyleSheet("padding: 15px; font-size: 15px;")
        gr_layout.addWidget(self.gr_question_label)
        self.gr_answer_input = QLineEdit()
        self.gr_answer_input.setPlaceholderText("请输入答案...")
        self.gr_answer_input.setFont(QFont("Microsoft YaHei", 13))
        self.gr_answer_input.setFixedHeight(40)
        gr_layout.addWidget(self.gr_answer_input)
        # 按钮行
        btn_row = QHBoxLayout()
        self.gr_submit_btn = QPushButton("提交答案")
        self.gr_submit_btn.setFixedWidth(100)
        self.gr_next_btn = QPushButton("下一题")
        self.gr_next_btn.setFixedWidth(100)
        self.gr_next_btn.setEnabled(False)
        for btn in [self.gr_submit_btn, self.gr_next_btn]:
            btn.setStyleSheet("""
                QPushButton { padding: 8px 16px; border-radius: 5px; border: none;
                             font-size: 13px; background-color: #4a90e2; color: white; }
                QPushButton:hover { background-color: #357abd; }
                QPushButton:disabled { background-color: #ccc; color: #888; }
            """)
        btn_row.addWidget(self.gr_submit_btn)
        btn_row.addWidget(self.gr_next_btn)
        btn_row.addStretch()
        gr_layout.addLayout(btn_row)
        # 结果反馈
        self.gr_result_label = QLabel("")
        self.gr_result_label.setFont(QFont("Microsoft YaHei", 12))
        gr_layout.addWidget(self.gr_result_label)
        layout.addWidget(gr_group)
        # 统计信息
        self.gr_stats_label = QLabel("")
        self.gr_stats_label.setFont(QFont("Microsoft YaHei", 11))
        self.gr_stats_label.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(self.gr_stats_label)
        layout.addStretch()
        # 状态变量
        self._gr_current_questions = []
        self._gr_current_idx = 0
        self._gr_correct_count = 0
        self._gr_total_count = 0
        # 连接信号
        self.gr_submit_btn.clicked.connect(self._check_grammar_answer)
        self.gr_next_btn.clicked.connect(self._next_grammar_question)
        self.gr_answer_input.returnPressed.connect(self._check_grammar_answer)
    def _start_grammar_exercise(self):
        """开始语法练习"""
        current_item = self.grammar_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择一个语法知识点")
            return
        unit = current_item.data(32)
        if not unit or "questions" not in unit:
            QMessageBox.warning(self, "提示", "该语法点暂无练习题")
            return
        self._gr_current_questions = list(unit["questions"])
        random.shuffle(self._gr_current_questions)
        self._gr_current_idx = 0
        self._gr_correct_count = 0
        self._gr_total_count = len(self._gr_current_questions)
        self.gr_progress.setMaximum(self._gr_total_count)
        self.gr_progress.setValue(0)
        self.gr_progress.setVisible(True)
        self.gr_stats_label.setText("进度: 0/{}".format(self._gr_total_count))
        self.grammar_sub_tabs.setCurrentWidget(self.grammar_exercise)
        self._show_grammar_question()
    def _show_grammar_question(self):
        """显示当前语法题"""
        if self._gr_current_idx >= len(self._gr_current_questions):
            self._finish_grammar_exercise()
            return
        q = self._gr_current_questions[self._gr_current_idx]
        self.gr_question_label.setText("【第{}/{}题】{}".format(
            self._gr_current_idx + 1, self._gr_total_count, q["q"]))
        self.gr_answer_input.clear()
        self.gr_result_label.setText("")
        self.gr_submit_btn.setEnabled(True)
        self.gr_next_btn.setEnabled(False)
        self.gr_answer_input.setFocus()
    def _check_grammar_answer(self):
        """检查语法练习答案"""
        ans = self.gr_answer_input.text().strip()
        if not ans:
            return
        q = self._gr_current_questions[self._gr_current_idx]
        correct = q["a"]
        # 标准化比较：忽略大小写、空格
        ans_norm = re.sub(r'\s+', '', ans.lower())
        corr_norm = re.sub(r'\s+', '', correct.lower())
        if ans_norm == corr_norm:
            self._gr_correct_count += 1
            self.gr_result_label.setText("<span style='color:green;font-size:14px;font-weight:bold;'>✓ 正确！</span>")
            self.gr_result_label.setStyleSheet("padding:10px;background:#e8f5e9;border-radius:5px;")
            self._check_star_award(mode="grammar")  # 语法练习正确，给星
        else:
            self.gr_result_label.setText("<span style='color:red;font-size:14px;font-weight:bold;'>✗ 错误。正确答案：{}</span>".format(correct))
            self.gr_result_label.setStyleSheet("padding:10px;background:#ffebee;border-radius:5px;")
            self._reward_wrong_answer()
        self.gr_progress.setValue(self._gr_current_idx + 1)
        self.gr_stats_label.setText("进度: {}/{} | 正确: {}".format(
            self._gr_current_idx + 1, self._gr_total_count, self._gr_correct_count))
        self.gr_submit_btn.setEnabled(False)
        self.gr_next_btn.setEnabled(True)
        self.gr_next_btn.setFocus()
    def _next_grammar_question(self):
        """下一道语法题"""
        self._gr_current_idx += 1
        self._show_grammar_question()
    def _finish_grammar_exercise(self):
        """完成语法练习"""
        accuracy = self._gr_correct_count / max(self._gr_total_count, 1) * 100
        msg = "练习完成！\n\n总题数：{}\n答对：{}\n正确率：{:.1f}%".format(
            self._gr_total_count, self._gr_correct_count, accuracy)
        self.gr_question_label.setText(msg)
        self.gr_answer_input.setVisible(False)
        self.gr_submit_btn.setVisible(False)
        self.gr_next_btn.setVisible(False)
        self.gr_result_label.setText("")
        self.gr_progress.setValue(self._gr_total_count)
    def _setup_plan_tab(self):
        """设置学习计划 Tab"""
        from PyQt5.QtWidgets import QTextBrowser
        layout = QVBoxLayout(self.plan_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setFont(QFont("Microsoft YaHei", 12))
        plan_html = """
        <h2 style="color:#4a90e2;">📋 初中英语三阶段复习计划</h2>
        
        <h3>第一阶段：打基础（当前阶段）</h3>
        <p>📌 目标时间：至2026年6月</p>
        <ul>
            <li>✅ 单词：每天背诵30-50个，重点突破核心词汇</li>
            <li>✅ 语法：系统梳理基础时态、从句等</li>
            <li>✅ 听力：每天听15-20分钟英语材料</li>
        </ul>
        <h3>第二阶段：提分冲刺</h3>
        <p>📌 目标时间：2026年9月至2027年1月</p>
        <p>🎯 目标分数：360-380分</p>
        <ul>
            <li>📝 完形填空与阅读理解专项训练</li>
            <li>📝 作文模板积累与写作练习</li>
            <li>📝 错题本整理与定期回顾</li>
        </ul>
        <h3>第三阶段：模考冲刺</h3>
        <p>📌 目标时间：2027年2月至5月</p>
        <ul>
            <li>🏆 真题模拟训练（每周1-2套）</li>
            <li>🏆 时间管理与答题策略优化</li>
            <li>🏆 心态调整与考前准备</li>
        </ul>
        <hr>
        <p style="color:#666;">💡 提示：按照关卡解锁顺序学习效果最佳！</p>
        """
        browser.setHtml(plan_html)
        layout.addWidget(browser)
    def _setup_essay_tab(self):
        """设置英语作文 Tab"""
        from PyQt5.QtWidgets import QTextEdit, QComboBox, QLabel, QPushButton, QGroupBox, QHBoxLayout
        layout = QVBoxLayout(self.essay_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        # 作文类型选择
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("作文类型："))
        self.essay_type_combo = QComboBox()
        self.essay_type_combo.addItems([
            "记叙文", "说明文", "议论文", "应用文（书信/邮件/通知）",
            "看图作文", "话题作文"
        ])
        self.essay_type_combo.setFont(QFont("Microsoft YaHei", 11))
        type_layout.addWidget(self.essay_type_combo)
        type_layout.addStretch()
        layout.addLayout(type_layout)
        # 写作指导区域
        guide_group = QGroupBox("写作指导")
        guide_layout = QVBoxLayout(guide_group)
        self.essay_guide = QTextEdit()
        self.essay_guide.setReadOnly(True)
        self.essay_guide.setTextInteractionFlags(Qt.NoTextInteraction)  # 禁止选择复制
        self.essay_guide.setFont(QFont("Microsoft YaHei", 11))
        self.essay_guide.setMaximumHeight(200)
        guide_layout.addWidget(self.essay_guide)
        layout.addWidget(guide_group)
        # 写作区域
        write_group = QGroupBox("作文编辑区")
        write_layout = QVBoxLayout(write_group)
        self.essay_editor = QTextEdit()
        self.essay_editor.setPlaceholderText("在此编写你的作文...")
        self.essay_editor.setFont(QFont("Microsoft YaHei", 12))
        self.essay_editor.setMinimumHeight(300)
        write_layout.addWidget(self.essay_editor)
        # 字数统计 + 按钮
        editor_bar = QHBoxLayout()
        self.essay_word_count = QLabel("字数：0")
        self.essay_word_count.setStyleSheet("color:#666;")
        editor_bar.addWidget(self.essay_word_count)
        editor_bar.addStretch()
        save_essay_btn = QPushButton("保存作文")
        save_essay_btn.setFixedWidth(100)
        save_essay_btn.setStyleSheet("""
            QPushButton { background-color: #4a90e2; color: white; padding: 6px 16px;
                         border-radius: 4px; border: none; font-size: 12px; }
            QPushButton:hover { background-color: #357abd; }
        """)
        editor_bar.addWidget(save_essay_btn)
        write_layout.addLayout(editor_bar)
        layout.addWidget(write_group)
        # 初始化指导内容
        self._update_essay_guide()
        self.essay_type_combo.currentTextChanged.connect(self._update_essay_guide)
        self.essay_editor.textChanged.connect(self._update_essay_word_count)
        save_essay_btn.clicked.connect(self._save_essay)
    def _update_essay_guide(self):
        """更新作文指导内容"""
        guides = {
            "记叙文": "<b>记叙文写作要点：</b><br>1. 明确六要素（时间、地点、人物、起因、经过、结果）<br>2. 按时间顺序或事件发展顺序组织<br>3. 使用过去时态为主<br>4. 注意描写细节和人物情感<br><br><b>常用句型：</b><br>• One day... / Last Sunday...<br>• When I arrived...<br>• At first..., but then...",
            "说明文": "<b>说明文写作要点：</b><br>1. 开头引入主题<br>2. 分点说明特征或步骤<br>3. 使用一般现在时<br>4. 语言简洁客观<br><br><b>常用表达：</b><br>• It is made of...<br>• There are several reasons...<br>• First..., Second..., Finally...",
            "议论文": "<b>议论文写作要点：</b><br>1. 开门见山提出观点<br>2. 分论点支撑（2-3个）<br>3. 论据具体有说服力<br>4. 总结重申观点<br><br><b>常用结构：</b><br>• Some people think..., but I believe...<br>• First of all... In addition...<br>• In a word / All in all...",
            "应用文（书信/邮件/通知）": "<b>应用文格式要点：</b><br><b>书信/邮件：</b><br>1. 称呼（Dear Sir/Madam,）<br>2. 开头说明写信目的<br>3. 正文分段阐述<br>4. 结尾礼貌用语<br>5. 落款<br><br><b>通知：</b><br>1. 标题（Notice）<br>2. 时间地点活动内容<br>3. 要求/注意事项<br>4. 发布单位和日期",
            "看图作文": "<b>看图作文要点：</b><br>1. 仔细观察图片，抓住关键信息<br>2. 描述图片内容（what/who/where/when）<br>3. 发挥合理想象，补充细节<br>4. 适当发表个人看法<br>5. 注意时态转换（描述用现在时，叙述用过去时）<br><br><b>常用开头：</b><br>• As we can see from the picture...<br>• The picture shows us that...",
            "话题作文": "<b>话题作文要点：</b><br>1. 审题明确话题关键词<br>2. 围绕话题展开，不偏题<br>3. 结构清晰（引言-正文-结尾）<br>4. 使用高级词汇和句型加分<br>5. 检查语法和拼写错误<br><br><b>加分句型：</b><br>• It is widely believed that...<br>• There is no doubt that...<br>• Not only... but also...",
        }
        essay_type = self.essay_type_combo.currentText()
        guide = guides.get(essay_type, guides["记叙文"])
        self.essay_guide.setHtml(guide)
    def _update_essay_word_count(self):
        """更新作文字数统计"""
        text = self.essay_editor.toPlainText()
        count = len(text.replace(" ", "").replace("\n", ""))
        self.essay_word_count.setText("字数：{}".format(count))
    def _save_essay(self):
        """保存作文到文件"""
        text = self.essay_editor.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "提示", "作文内容为空，无需保存")
            return
        essay_type = self.essay_type_combo.currentText()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = "essay_{}_{}.txt".format(essay_type, timestamp)
        filepath = os.path.join(BASE_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("【类型】{}\n".format(essay_type))
            f.write("【时间】{}\n".format(datetime.now().strftime("%Y-%m-%d %H:%M")))
            f.write("\n{}\n".format(text))
        QMessageBox.information(self, "保存成功", "作文已保存到：\n{}".format(filepath))
    def _update_tab_access(self):
        """根据学习进度更新Tab访问权限（八关卡体系）
        Stage 0: 仅单词
        Stage 1: 解锁短语
        Stage 2: 解锁语法
        Stage 3: 解锁对话
        Stage 4: 解锁作文
        """
        stats = self.reward.stats
        stage = stats.get('current_stage', 0)
        required_stages = {
            "单词": 0,
            "短语": 1,
            "语法": 2,
            "对话": 3,
            "英语作文": 4,
            "学习计划": 0,
        }
        for i in range(self.main_tabs.count()):
            name = self.main_tabs.tabText(i)
            needed = 6  # default locked
            for key, val in required_stages.items():
                if key in name:
                    needed = val
                    break
            self.main_tabs.setTabEnabled(i, stage >= needed)
def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    # 全局字体设置
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    window = EnglishLearningTool()
    window.show()
    # 启动后更新一次Tab权限
    window._update_tab_access()
    sys.exit(app.exec())
if __name__ == '__main__':
    main()