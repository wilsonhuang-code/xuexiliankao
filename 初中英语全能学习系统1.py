import sys
import os
import pickle
import random
import re
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QListWidget, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QListWidget, QFileDialog,
                             QMessageBox, QTextEdit, QSplitter, QDialog, QDialogButtonBox, QRadioButton,
                             QButtonGroup, QScrollArea, QComboBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtTextToSpeech import QTextToSpeech


from phonetic_dict import phonetic_dict  # 音标查词
# ==================== 多邻国风格填空控件 ====================
from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QPainter, QColor, QFontMetrics, QPen
from PyQt5.QtCore import QRect


class WordFillWidget(QWidget):
    """单词填空控件 - 自定义输入（无QLineEdit）"""

    def __init__(self, word, missing_pos, parent=None):
        super().__init__(parent)
        self.word = word
        self.missing_pos = missing_pos
        self.missing_char = word[missing_pos].lower()
        self.user_input = ""

        self.setFixedHeight(120)
        self.setMinimumWidth(600)

        # 布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(0)

        prefix = word[:missing_pos]
        suffix = word[missing_pos+1:]

        font = QFont("微软雅黑", 48, QFont.Bold)

        # 前缀
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

        # 后缀
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
                # 只接受字母输入
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
                    return True  # 忽略其他键
        return super().eventFilter(obj, event)

    def showEvent(self, event):
        super().showEvent(event)
        self.input_label.setFocus()




class PhraseFillWidget(QWidget):
    """短语填空控件 - 整词填空（显示 be ___ at，填 good）"""

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
                # 整词输入框
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



class DialogueFillWidget(QWidget):
    """对话填空控件 - 无痕效果，整行融为一体"""

    def __init__(self, line_text, blank_positions, words_in_line, parent=None):
        super().__init__(parent)
        self.blank_positions = blank_positions
        self.words_in_line = words_in_line
        self.blank_inputs = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)  # 关键：无间距，融为一体

        font = QFont("Microsoft YaHei", 14)

        prev_end = 0
        for bp in blank_positions:
            # 前缀文字
            prefix_words = words_in_line[prev_end:bp]
            if prefix_words:
                prefix_text = " ".join(prefix_words) + " "
                prefix_lbl = QLabel(prefix_text)
                prefix_lbl.setFont(font)
                prefix_lbl.setStyleSheet("color: #333; background: transparent; border: none;")
                layout.addWidget(prefix_lbl)

            # 输入框
            blank_input = QLineEdit()
            blank_input.setFont(font)
            blank_input.setFixedWidth(max(60, len(words_in_line[bp]) * 12 + 20))
            blank_input.setAlignment(Qt.AlignCenter)
            blank_input.setPlaceholderText("_" * len(words_in_line[bp]))
            blank_input.setStyleSheet("""
                QLineEdit {
                    color: #1cb0f6;
                    background: transparent;
                    border: none;
                    border-bottom: 2px solid #1cb0f6;
                    padding: 0px;
                    margin: 0px;
                }
            """)
            layout.addWidget(blank_input)
            self.blank_inputs.append(blank_input)

            # 空格分隔
            space_lbl = QLabel(" ")
            space_lbl.setFont(font)
            space_lbl.setStyleSheet("background: transparent;")
            layout.addWidget(space_lbl)

            prev_end = bp + 1

        # 后缀文字
        suffix_words = words_in_line[prev_end:]
        if suffix_words:
            suffix_text = " ".join(suffix_words)
            suffix_lbl = QLabel(suffix_text)
            suffix_lbl.setFont(font)
            suffix_lbl.setStyleSheet("color: #333; background: transparent; border: none;")
            layout.addWidget(suffix_lbl)

        layout.addStretch()

    def get_user_inputs(self):
        return [inp.text().strip().lower() for inp in self.blank_inputs]




# ==================== 一、初中单词库（200+）====================
# ==================== 一、初中单词库（按年级标注）====================
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
    ('size', '尺寸', '七年级上册'),
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
    ('internet', '互联网', '八年级上册'),
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
    ('size', '尺码', '七年级上册'),
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
    ('friday', '星期五', '七年级下册'),
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
]

BUILTIN_PHRASE_LIST = [
  ('a few', '几个', '七年级上册'),
  ('a little', '一点', '七年级上册'),
  ('a lot of', '许多', '七年级上册'),
  ('according to', '根据', '七年级上册'),
  ('after all', '毕竟', '七年级上册'),
  ('agree with', '同意', '七年级上册'),
  ('all the time', '一直', '七年级上册'),
  ('as long as', '只要', '七年级上册'),
  ('as soon as', '一...就...', '七年级上册'),
  ('as well', '也', '七年级上册'),
  ('be afraid of', '害怕', '七年级上册'),
  ('be angry with', '生...的气', '七年级上册'),
  ('be born', '出生', '七年级上册'),
  ('be busy with', '忙于', '七年级上册'),
  ('be careful', '小心', '七年级上册'),
  ('be different from', '与...不同', '七年级上册'),
  ('be famous for', '以...闻名', '七年级上册'),
  ('be fond of', '喜欢', '七年级上册'),
  ('be full of', '充满', '七年级上册'),
  ('be good at', '擅长', '七年级上册'),
  ('be interested in', '对...感兴趣', '七年级上册'),
  ('be late for', '迟到', '七年级上册'),
  ('be made of', '由...制成', '七年级上册'),
  ('be proud of', '为...骄傲', '七年级上册'),
  ('be ready to', '准备好', '七年级上册'),
  ('be responsible for', '对...负责', '七年级上册'),
  ('be strict with', '对...严格', '七年级上册'),
  ('be used to', '习惯于', '七年级上册'),
  ('because of', '因为', '七年级上册'),
  ('belong to', '属于', '七年级上册'),
  ('both...and...', '两者都', '七年级上册'),
  ('break down', '出故障', '七年级上册'),
  ('break into', '闯入', '七年级上册'),
  ('bring up', '抚养', '七年级上册'),
  ('by accident', '偶然', '七年级上册'),
  ('by mistake', '错误地', '七年级上册'),
  ('by the way', '顺便说一下', '七年级上册'),
  ('call back', '回电话', '七年级上册'),
  ('call off', '取消', '七年级上册'),
  ('care about', '关心', '七年级上册'),
  ('carry out', '执行', '七年级上册'),
  ('catch up with', '赶上', '七年级上册'),
  ('check in', '办理入住', '七年级上册'),
  ('check out', '退房', '七年级上册'),
  ('cheer up', '振作起来', '七年级上册'),
  ('come back', '回来', '七年级上册'),
  ('come on', '加油；快点', '七年级上册'),
  ('come out', '出来；出版', '七年级上册'),
  ('come true', '实现', '七年级上册'),
  ('communicate with', '与...交流', '七年级上册'),
  ('compare with', '与...比较', '七年级上册'),
  ('compete with', '与...竞争', '七年级上册'),
  ('connect to', '连接', '七年级上册'),
  ('cut down', '砍倒', '七年级上册'),
  ('deal with', '处理', '七年级上册'),
  ('depend on', '依靠', '七年级上册'),
  ('die out', '灭绝', '七年级上册'),
  ("do one's best", '尽力', '七年级上册'),
  ('do well in', '在...做得好', '七年级上册'),
  ('dream of', '梦想', '七年级上册'),
  ('dress up', '打扮', '七年级上册'),
  ('drop by', '顺便拜访', '七年级上册'),
  ('each other', '彼此', '七年级上册'),
  ('eat out', '外出就餐', '七年级上册'),
  ('end up', '结束', '七年级上册'),
  ('enjoy oneself', '玩得开心', '七年级上册'),
  ('even if', '即使', '七年级上册'),
  ('ever since', '自从', '七年级上册'),
  ('every day', '每天', '七年级上册'),
  ('fall asleep', '入睡', '七年级上册'),
  ('fall down', '摔倒', '七年级上册'),
  ('fall in love with', '爱上', '七年级上册'),
  ('fall off', '掉下', '七年级上册'),
  ('feel like', '想要', '七年级上册'),
  ('fill in', '填写', '七年级上册'),
  ('find out', '查明', '七年级上册'),
  ('for example', '例如', '七年级上册'),
  ('from now on', '从现在起', '七年级上册'),
  ('from time to time', '不时', '七年级上册'),
  ('get along with', '与...相处', '七年级上册'),
  ('get away', '离开', '七年级上册'),
  ('get back', '回来', '七年级上册'),
  ('get in the way', '挡道', '七年级上册'),
  ('get lost', '迷路', '七年级上册'),
  ('get married', '结婚', '七年级上册'),
  ('get off', '下车', '七年级上册'),
  ('get on', '上车', '七年级上册'),
  ('get over', '克服', '七年级上册'),
  ('get ready for', '为...准备', '七年级上册'),
  ('get together', '聚会', '七年级上册'),
  ('get up', '起床', '七年级上册'),
  ('give away', '赠送', '七年级上册'),
  ('give back', '归还', '七年级上册'),
  ('give out', '分发', '七年级上册'),
  ('give up', '放弃', '七年级上册'),
  ('go back', '回去', '七年级上册'),
  ('go by', '经过', '七年级上册'),
  ('go for a walk', '散步', '七年级上册'),
  ('go off', '离开', '七年级上册'),
  ('go on', '继续', '七年级上册'),
  ('go out', '外出', '七年级上册'),
  ('go over', '复习', '七年级上册'),
  ('go through', '经历', '七年级上册'),
  ('grow up', '长大', '七年级上册'),
  ('hand in', '上交', '七年级上册'),
  ('hand out', '分发', '七年级上册'),
  ('hang out', '闲逛', '七年级上册'),
  ('happen to', '发生在', '七年级上册'),
  ('have a cold', '感冒', '七年级上册'),
  ('have fun', '玩得开心', '七年级上册'),
  ('have to', '不得不', '七年级上册'),
  ('hear from', '收到...来信', '七年级上册'),
  ('hold on', '稍等', '七年级上册'),
  ('hurry up', '快点', '七年级上册'),
  ('in a hurry', '匆忙', '七年级上册'),
  ('in fact', '事实上', '七年级上册'),
  ('in front of', '在...前面', '七年级上册'),
  ('in order to', '为了', '七年级上册'),
  ('in public', '公开地', '七年级上册'),
  ('in the end', '最后', '七年级上册'),
  ('in the future', '在未来', '七年级上册'),
  ('in the morning', '在早上', '七年级上册'),
  ('in time', '及时', '七年级上册'),
  ('instead of', '代替', '七年级上册'),
  ('join in', '参加', '七年级上册'),
  ('jump down', '跳下', '七年级上册'),
  ('keep away from', '远离', '七年级上册'),
  ('keep on', '继续', '七年级上册'),
  ('keep up with', '跟上', '七年级上册'),
  ('knock at', '敲', '七年级上册'),
  ('laugh at', '嘲笑', '七年级上册'),
  ('lead to', '导致', '七年级上册'),
  ('learn from', '向...学习', '七年级上册'),
  ('leave for', '前往', '七年级上册'),
  ('listen to', '听', '七年级上册'),
  ('live on', '以...为生', '七年级上册'),
  ('look after', '照顾', '七年级上册'),
  ('look at', '看', '七年级上册'),
  ('look for', '寻找', '七年级上册'),
  ('look forward to', '期待', '七年级上册'),
  ('look like', '看起来像', '七年级上册'),
  ('look out', '小心', '七年级上册'),
  ('look through', '浏览', '七年级上册'),
  ('look up', '查阅', '七年级上册'),
  ('make a decision', '做决定', '七年级上册'),
  ('make a mistake', '犯错', '七年级上册'),
  ('make a promise', '许下诺言', '七年级上册'),
  ('make friends', '交朋友', '七年级上册'),
  ('make noise', '制造噪音', '七年级上册'),
  ('make progress', '取得进步', '七年级上册'),
  ('make sure', '确保', '七年级上册'),
  ('make up', '编造；弥补', '七年级上册'),
  ("make up one's mind", '下定决心', '七年级上册'),
  ('mix up', '混淆', '七年级上册'),
  ('move away', '搬走', '七年级上册'),
  ('move in', '搬进', '七年级上册'),
  ('pay attention to', '注意', '七年级上册'),
  ('pay for', '支付', '七年级上册'),
  ('pick up', '捡起；接人', '七年级上册'),
  ('point out', '指出', '七年级上册'),
  ('prepare for', '准备', '七年级上册'),
  ('put away', '收好', '七年级上册'),
  ('put off', '推迟', '七年级上册'),
  ('put on', '穿上', '七年级上册'),
  ('put out', '扑灭', '七年级上册'),
  ('put up', '张贴', '七年级上册'),
  ('regard as', '视为', '七年级上册'),
  ('run away', '逃跑', '七年级上册'),
  ('run out of', '用完', '七年级上册'),
  ('save up', '储蓄', '七年级上册'),
  ('see off', '送行', '七年级上册'),
  ('sell out', '售完', '七年级上册'),
  ('send for', '派人去请', '七年级上册'),
  ('separate from', '分离', '七年级上册'),
  ('set off', '出发', '七年级上册'),
  ('set up', '建立', '七年级上册'),
  ('show up', '出现', '七年级上册'),
  ('shut down', '关闭', '七年级上册'),
  ('sit down', '坐下', '七年级上册'),
  ('slow down', '减速', '七年级上册'),
  ('so far', '到目前为止', '七年级上册'),
  ('sort out', '整理', '七年级上册'),
  ('stand up', '起立', '七年级上册'),
  ('stay up', '熬夜', '七年级上册'),
  ('stick to', '坚持', '七年级上册'),
  ('stop doing', '停止做', '七年级上册'),
  ('stop to do', '停下来去做', '七年级上册'),
  ('succeed in', '成功', '七年级上册'),
  ('take a break', '休息', '七年级上册'),
  ('take a walk', '散步', '七年级上册'),
  ('take after', '与...相像', '七年级上册'),
  ('take away', '拿走', '七年级上册'),
  ('take care of', '照顾', '七年级上册'),
  ('take off', '起飞；脱下', '七年级上册'),
  ('take out', '取出', '七年级上册'),
  ('take part in', '参加', '七年级上册'),
  ('take place', '发生', '七年级上册'),
  ('take turns', '轮流', '七年级上册'),
  ('talk about', '谈论', '七年级上册'),
  ('talk with', '与...交谈', '七年级上册'),
  ('teach oneself', '自学', '七年级上册'),
  ('tell a story', '讲故事', '七年级上册'),
  ('thanks to', '幸亏', '七年级上册'),
  ('think about', '考虑', '七年级上册'),
  ('think of', '想起', '七年级上册'),
  ('throw away', '扔掉', '七年级上册'),
  ('try on', '试穿', '七年级上册'),
  ('try out', '试验', '七年级上册'),
  ('turn down', '调低；拒绝', '七年级上册'),
  ('turn off', '关掉', '七年级上册'),
  ('turn on', '打开', '七年级上册'),
  ('turn up', '调高；出现', '七年级上册'),
  ('used to', '过去常常', '七年级上册'),
  ('wait for', '等待', '七年级上册'),
  ('wake up', '醒来', '七年级上册'),
  ('walk into', '走进', '七年级上册'),
  ('watch out', '小心', '七年级上册'),
  ('work on', '从事于', '七年级上册'),
  ('work out', '解决', '七年级上册'),
  ('worry about', '担心', '七年级上册'),
  ('write down', '写下', '七年级上册'),
  ('write to', '写信给', '七年级上册'),
  ('good morning', '早上好', '七年级上册'),
  ('good afternoon', '下午好', '七年级上册'),
  ('good evening', '晚上好', '七年级上册'),
  ('good night', '晚安', '七年级上册'),
  ('thank you', '谢谢你', '七年级上册'),
  ('thanks a lot', '多谢', '七年级上册'),
  ('nice to meet you', '很高兴见到你', '七年级上册'),
  ('excuse me', '打扰一下；对不起', '七年级上册'),
  ("what's your name", '你叫什么名字', '七年级上册'),
  ('my name is', '我的名字是', '七年级上册'),
  ('where are you from', '你来自哪里', '七年级上册'),
  ('be from', '来自', '七年级上册'),
  ('how old are you', '你多大了', '七年级上册'),
  ('years old', '岁', '七年级上册'),
  ('in English', '用英语', '七年级上册'),
  ('give sb. sth.', '给某人某物', '七年级上册'),
  ('here you are', '给你', '七年级上册'),
  ("let's go", '让我们走吧', '七年级上册'),
  ('want to do', '想要做', '七年级上册'),
  ('would like to', '想要', '七年级上册'),
  ('what about', '怎么样', '七年级上册'),
  ('how about', '怎么样', '七年级上册'),
  ('what time', '什么时间', '七年级上册'),
  ('go to bed', '去睡觉', '七年级上册'),
  ('have breakfast', '吃早餐', '七年级上册'),
  ('have lunch', '吃午餐', '七年级上册'),
  ('have dinner', '吃晚餐', '七年级上册'),
  ('go to school', '去上学', '七年级上册'),
  ('go home', '回家', '七年级下册'),
  ('on weekdays', '在工作日', '七年级下册'),
  ('on weekends', '在周末', '七年级下册'),
  ('watch TV', '看电视', '七年级下册'),
  ('do homework', '做作业', '七年级下册'),
  ('play sports', '做运动', '七年级下册'),
  ('play basketball', '打篮球', '七年级下册'),
  ('play football', '踢足球', '七年级下册'),
  ('play the piano', '弹钢琴', '七年级下册'),
  ('play the guitar', '弹吉他', '七年级下册'),
  ('by bus', '乘公共汽车', '七年级下册'),
  ('by bike', '骑自行车', '七年级下册'),
  ('by car', '乘小汽车', '七年级下册'),
  ('by train', '乘火车', '七年级下册'),
  ('by plane', '乘飞机', '七年级下册'),
  ('by ship', '乘轮船', '七年级下册'),
  ('on foot', '步行', '七年级下册'),
  ('take a bus', '乘公共汽车', '七年级下册'),
  ('take a taxi', '乘出租车', '七年级下册'),
  ('at the bus stop', '在公共汽车站', '七年级下册'),
  ('get to', '到达', '七年级下册'),
  ('go along', '沿着...走', '七年级下册'),
  ('turn left', '向左转', '七年级下册'),
  ('turn right', '向右转', '七年级下册'),
  ('across from', '在...对面', '七年级下册'),
  ('next to', '紧挨着', '七年级下册'),
  ('between...and...', '在...和...之间', '七年级下册'),
  ('behind', '在...后面', '七年级下册'),
  ('on the left', '在左边', '七年级下册'),
  ('on the right', '在右边', '七年级下册'),
  ('happy birthday', '生日快乐', '七年级下册'),
  ('birthday party', '生日聚会', '七年级下册'),
  ('make a wish', '许愿', '七年级下册'),
  ('blow out', '吹灭', '七年级下册'),
  ('cut the cake', '切蛋糕', '七年级下册'),
  ('sing a song', '唱歌', '七年级下册'),
  ('dance to music', '随着音乐跳舞', '七年级下册'),
  ('take photos', '拍照', '七年级下册'),
  ('have a good time', '玩得开心', '七年级下册'),
  ("what's the weather like", '天气怎么样', '七年级下册'),
  ('how is the weather', '天气怎么样', '七年级下册'),
  ('fly a kite', '放风筝', '七年级下册'),
  ('make a snowman', '堆雪人', '七年级下册'),
  ('go swimming', '去游泳', '七年级下册'),
  ('go hiking', '去徒步', '七年级下册'),
  ('go camping', '去露营', '七年级下册'),
  ('cheer on', '为...加油', '七年级下册'),
  ('prefer...to...', '比起...更喜欢...', '七年级下册'),
  ('quite a bit', '相当多', '七年级下册'),
  ('spend time doing', '花时间做', '七年级下册'),
  ('have a fever', '发烧', '七年级下册'),
  ('have a cough', '咳嗽', '七年级下册'),
  ('have a headache', '头痛', '七年级下册'),
  ('have a stomachache', '胃痛', '七年级下册'),
  ('see a doctor', '看医生', '七年级下册'),
  ('take some medicine', '吃药', '七年级下册'),
  ('lie down', '躺下', '七年级下册'),
  ('have a rest', '休息', '七年级下册'),
  ('drink enough water', '喝足够的水', '七年级下册'),
  ('stay up late', '熬夜', '七年级下册'),
  ('keep healthy', '保持健康', '七年级下册'),
  ('collect stamps', '集邮', '七年级下册'),
  ('listen to music', '听音乐', '七年级下册'),
  ('watch movies', '看电影', '七年级下册'),
  ('read books', '读书', '七年级下册'),
  ("in one's free time", '在空闲时间', '七年级下册'),
  ('be popular with', '受...欢迎', '七年级下册'),
  ('all over the world', '全世界', '七年级下册'),
  ('in the past', '在过去', '七年级下册'),
  ('at present', '目前', '七年级下册'),
  ('feel happy', '感到高兴', '七年级下册'),
  ('feel sad', '感到悲伤', '七年级下册'),
  ('feel angry', '感到生气', '七年级下册'),
  ('feel worried', '感到担心', '七年级下册'),
  ('feel excited', '感到兴奋', '七年级下册'),
  ('calm down', '冷静下来', '七年级下册'),
  ('go on a trip', '去旅行', '七年级下册'),
  ('travel to', '去...旅行', '七年级下册'),
  ('book a ticket', '预订票', '七年级下册'),
  ('take photos', '拍照', '七年级下册'),
  ('enjoy the scenery', '欣赏风景', '七年级下册'),
  ('buy souvenirs', '买纪念品', '七年级下册'),
  ('try local food', '品尝当地美食', '七年级下册'),
  ('stay at a hotel', '住酒店', '七年级下册'),
  ('junk food', '垃圾食品', '七年级下册'),
  ('healthy food', '健康食品', '七年级下册'),
  ('fast food', '快餐', '七年级下册'),
  ('traditional food', '传统食物', '七年级下册'),
  ('cook a meal', '做饭', '七年级下册'),
  ('set the table', '摆餐具', '七年级下册'),
  ('clear the table', '清理桌子', '七年级下册'),
  ('wash dishes', '洗碗', '七年级下册'),
  ('go shopping', '去购物', '七年级下册'),
  ('on sale', '打折', '七年级下册'),
  ('credit card', '信用卡', '七年级下册'),
  ('cash on delivery', '货到付款', '七年级下册'),
  ('keep in touch with', '与...保持联系', '七年级下册'),
  ('achieve success', '取得成功', '七年级下册'),
  ('economic development', '经济发展', '七年级下册'),
  ('social progress', '社会进步', '七年级下册'),
  ('educational reform', '教育改革', '七年级下册'),
  ('protect the environment', '保护环境', '七年级下册'),
  ('save energy', '节约能源', '七年级下册'),
  ('reduce pollution', '减少污染', '七年级下册'),
  ('recycle waste', '回收废物', '七年级下册'),
  ('cut down trees', '砍伐树木', '七年级下册'),
  ('global warming', '全球变暖', '七年级下册'),
  ('climate change', '气候变化', '七年级下册'),
  ('take action', '采取行动', '七年级下册'),
  ('make a difference', '产生影响', '七年级下册'),
  ('live a low-carbon life', '过低碳生活', '七年级下册'),
  ('speak English', '说英语', '七年级下册'),
  ('learn English', '学英语', '七年级下册'),
  ('improve English', '提高英语', '七年级下册'),
  ('English-speaking country', '英语国家', '七年级下册'),
  ('native language', '母语', '七年级下册'),
  ('foreign language', '外语', '七年级下册'),
  ('translate into', '翻译成', '七年级下册'),
  ('make friends with', '与...交朋友', '七年级下册'),
  ('cultural difference', '文化差异', '七年级下册'),
  ('How are you?', '你好吗？', '七年级下册'),
  ('How do you do?', '你好！（初次见面）', '七年级下册'),
  ('Good morning.', '早上好。', '七年级下册'),
  ('Good afternoon.', '下午好。', '七年级下册'),
  ('Good evening.', '晚上好。', '七年级下册'),
  ('Good night.', '晚安。', '七年级下册'),
  ('See you.', '再见。', '七年级下册'),
  ('See you later.', '回头见。', '七年级下册'),
  ('Take care.', '保重。', '七年级下册'),
  ('Happy birthday!', '生日快乐！', '七年级下册'),
  ('Congratulations!', '恭喜！', '七年级下册'),
  ('Merry Christmas!', '圣诞快乐！', '七年级下册'),
  ('Happy New Year!', '新年快乐！', '七年级下册'),
  ('Thank you very much.', '非常感谢。', '七年级下册'),
  ('You are welcome.', '不客气。', '七年级下册'),
  ('I beg your pardon?', '请再说一遍？', '七年级下册'),
  ('What is your name?', '你叫什么名字？', '七年级下册'),
  ('My name is...', '我叫……', '七年级下册'),
  ('Where are you from?', '你来自哪里？', '七年级下册'),
  ('I am from...', '我来自……', '七年级下册'),
  ('How old are you?', '你多大了？', '七年级下册'),
  ('I am ... years old.', '我……岁。', '七年级下册'),
  ("I don't understand.", '我不明白。', '七年级下册'),
  ("I don't know.", '我不知道。', '七年级下册'),
  ('Please say it again.', '请再说一遍。', '七年级下册'),
  ('Please speak slowly.', '请说慢一点。', '七年级下册'),
  ('What does ... mean?', '……是什么意思？', '七年级下册'),
  ('How do you spell it?', '怎么拼写？', '七年级下册'),
  ('Can you help me?', '你能帮我吗？', '七年级下册'),
  ('May I ...?', '我可以……吗？', '七年级下册'),
  ('You should ...', '你应该……', '七年级下册'),
  ('You should not ...', '你不应该……', '七年级下册'),
  ('You had better ...', '你最好……', '七年级下册'),
  ('Why not ...?', '为什么不……？', '七年级下册'),
  ('What about ...?', '……怎么样？', '七年级下册'),
  ('Would you like to ...?', '你想……吗？', '七年级下册'),
  ('I would love to.', '我很乐意。', '七年级下册'),
  ("I'd love to, but ...", '我很想去，但是……', '七年级下册'),
  ('It is very kind of you.', '你真好。', '七年级下册'),
  ('again and again', '反复地', '七年级下册'),
  ('all over', '遍及', '七年级下册'),
  ('all right', '好的', '七年级下册'),
  ('arrive in', '到达（大地方）', '七年级下册'),
  ('arrive at', '到达（小地方）', '七年级下册'),
  ('as usual', '像往常一样', '七年级下册'),
  ('as...as', '和……一样', '七年级下册'),
  ('ask for', '请求', '七年级下册'),
  ('at first', '起初', '七年级下册'),
  ('at last', '最后', '七年级下册'),
  ('at least', '至少', '七年级下册'),
  ('at most', '至多', '七年级下册'),
  ('at once', '立刻', '七年级下册'),
  ('at the same time', '同时', '七年级下册'),
  ('at work', '在上班', '七年级下册'),
  ('be able to', '能够', '七年级下册'),
  ('be covered with', '被……覆盖', '七年级下册'),
  ('be filled with', '充满', '七年级下册'),
  ('be good for', '对……有益', '七年级下册'),
  ('be made from', '由……制成（看不出原料）', '七年级下册'),
  ('be pleased with', '对……满意', '七年级下册'),
  ('be worth doing', '值得做', '七年级下册'),
  ('before long', '不久以后', '七年级下册'),
  ('break out', '爆发', '七年级下册'),
  ('build up', '建立', '七年级下册'),
  ('call up', '打电话给', '七年级下册'),
  ('care for', '照顾', '七年级下册'),
  ('carry on', '继续', '七年级下册'),
  ('change into', '变成', '七年级下册'),
  ('come down', '下来', '七年级下册'),
  ('come from', '来自', '七年级下册'),
  ('come up with', '想出', '七年级下册'),
  ('cut up', '切碎', '七年级下册'),
  ('divide into', '分成', '七年级下册'),
  ('drop in', '顺便拜访', '七年级下册'),
  ('eat up', '吃光', '七年级下册'),
  ('either...or...', '要么……要么……', '七年级下册'),
  ('even though', '虽然', '七年级下册'),
  ('except for', '除了……之外', '七年级下册'),
  ('face to face', '面对面', '七年级下册'),
  ('fall behind', '落后', '七年级下册'),
  ('far away', '遥远的', '七年级下册'),
  ('for free', '免费', '七年级下册'),
  ('for the time being', '暂时', '七年级下册'),
  ('get close to', '接近', '七年级下册'),
  ('get down to', '开始认真做', '七年级下册'),
  ('get into trouble', '陷入麻烦', '七年级下册'),
  ('give in', '屈服', '七年级下册'),
  ('go abroad', '出国', '七年级下册'),
  ('go away', '走开', '七年级下册'),
  ('go fishing', '去钓鱼', '七年级下册'),
  ('hang on', '坚持', '七年级下册'),
  ('hang up', '挂断电话', '七年级下册'),
  ('have trouble doing', '做……有困难', '七年级下册'),
  ('help oneself to', '随便吃……', '七年级下册'),
  ('hold up', '举起', '七年级下册'),
  ('in all', '总共', '七年级下册'),
  ('in common', '共同的', '七年级下册'),
  ('in danger', '处于危险中', '七年级下册'),
  ('in need of', '需要', '七年级下册'),
  ('in other words', '换句话说', '七年级下册'),
  ('in peace', '和平地', '七年级下册'),
  ('in silence', '沉默地', '七年级下册'),
  ('in surprise', '惊奇地', '七年级下册'),
  ('in the way', '挡道', '七年级下册'),
  ('just now', '刚才', '七年级下册'),
  ('keep a diary', '写日记', '七年级下册'),
  ('keep doing', '一直做', '七年级下册'),
  ('keep off', '避开', '七年级下册'),
  ('keep out', '不让……进入', '七年级下册'),
  ('look ahead', '向前看', '七年级下册'),
  ('look down upon', '看不起', '七年级下册'),
  ('look into', '调查', '七年级下册'),
  ('lots of', '许多', '七年级下册'),
  ('make a living', '谋生', '七年级下册'),
  ('make a noise', '吵闹', '七年级下册'),
  ('make fun of', '取笑', '七年级下册'),
  ('make use of', '利用', '七年级下册'),
  ('mobile phone', '手机', '七年级下册'),
  ('more and more', '越来越多', '七年级下册'),
  ('neither...nor...', '既不……也不……', '七年级下册'),
  ('no longer', '不再', '七年级下册'),
  ('no matter', '无论', '七年级下册'),
  ('not only...but also...', '不仅……而且……', '七年级下册'),
  ('now and then', '偶尔', '七年级下册'),
  ('of course', '当然', '七年级下册'),
  ('on board', '在船上', '七年级下册'),
  ('on business', '出差', '七年级下册'),
  ('on display', '展出', '七年级下册'),
  ('on duty', '值日', '七年级下册'),
  ('on show', '展出', '七年级下册'),
  ('on the phone', '在通电话', '八年级上册'),
  ('on time', '准时', '八年级上册'),
  ('on vacation', '在度假', '八年级上册'),
  ('once again', '再一次', '八年级上册'),
  ('once more', '再一次', '八年级上册'),
  ('one after another', '一个接一个', '八年级上册'),
  ('ought to', '应该', '八年级上册'),
  ('out of breath', '上气不接下气', '八年级上册'),
  ('out of sight', '看不见', '八年级上册'),
  ('over and over again', '反复地', '八年级上册'),
  ('play a role in', '在……中起作用', '八年级上册'),
  ('play with', '玩弄', '八年级上册'),
  ('plenty of', '大量的', '八年级上册'),
  ('point at', '指着', '八年级上册'),
  ('practise doing', '练习做……', '八年级上册'),
  ('prevent...from...', '防止……做……', '八年级上册'),
  ('put down', '放下', '八年级上册'),
  ('quarrel with', '与……争吵', '八年级上册'),
  ('rather than', '而不是', '八年级上册'),
  ('rush hour', '高峰时间', '八年级上册'),
  ("save one's life", '拯救某人的生命', '八年级上册'),
  ('search for', '搜寻', '八年级上册'),
  ('set free', '释放', '八年级上册'),
  ('set out', '出发', '八年级上册'),
  ('set an example', '树立榜样', '八年级上册'),
  ('shake hands', '握手', '八年级上册'),
  ('shout at', '对……大声叫嚷', '八年级上册'),
  ('show off', '炫耀', '八年级上册'),
  ('shut up', '闭嘴', '八年级上册'),
  ('side by side', '肩并肩', '八年级上册'),
  ('so that', '以便', '八年级上册'),
  ('speak highly of', '高度评价', '八年级上册'),
  ('spend...on...', '在……上花费……', '八年级上册'),
  ('stand for', '代表', '八年级上册'),
  ('stop...from...', '阻止……做……', '八年级上册'),
  ('such as', '例如', '八年级上册'),
  ('suit...to...', '适合……', '八年级上册'),
  ('take a message', '捎口信', '八年级上册'),
  ('take charge of', '负责', '八年级上册'),
  ('take it easy', '别紧张', '八年级上册'),
  ('take pride in', '为……感到自豪', '八年级上册'),
  ('take the place of', '取代', '八年级上册'),
  ('the more...the more...', '越……越……', '八年级上册'),
  ('to be honest', '说实话', '八年级上册'),
  ("to one's surprise", '令某人吃惊的是', '八年级上册'),
  ("try one's best", '尽力', '八年级上册'),
  ('turn into', '变成', '八年级上册'),
  ('up and down', '上上下下', '八年级上册'),
  ('up to', '多达', '八年级上册'),
  ('would rather...than...', '宁愿……而不愿……', '八年级上册'),
  ('at home', '在家', '八年级上册'),
  ('at school', '在学校', '八年级上册'),
  ('by subway', '乘地铁', '八年级上册'),
  ('play volleyball', '打排球', '八年级上册'),
  ('play tennis', '打网球', '八年级上册'),
  ('play ping-pong', '打乒乓球', '八年级上册'),
  ('play the violin', '拉小提琴', '八年级上册'),
  ('draw pictures', '画画', '八年级上册'),
  ('sing songs', '唱歌', '八年级上册'),
  ('dance', '跳舞', '八年级上册'),
  ('swim', '游泳', '八年级上册'),
  ('run', '跑步', '八年级上册'),
  ('jump', '跳', '八年级上册'),
  ('walk', '走路', '八年级上册'),
  ('ride a bike', '骑自行车', '八年级上册'),
  ('help each other', '互相帮助', '八年级上册'),
  ('study hard', '努力学习', '八年级上册'),
  ('go skating', '去滑冰', '八年级上册'),
  ('go skiing', '去滑雪', '八年级上册'),
  ('go climbing', '去爬山', '八年级上册'),
  ('write letters', '写信', '八年级上册'),
  ('send emails', '发电子邮件', '八年级上册'),
  ('make a call', '打电话', '八年级上册'),
  ('do sports', '做运动', '八年级上册'),
  ('eat vegetables', '吃蔬菜', '八年级上册'),
  ('drink milk', '喝牛奶', '八年级上册'),
  ('get up early', '早起', '八年级上册'),
  ('do morning exercises', '做早操', '八年级上册'),
  ('have a toothache', '牙痛', '八年级上册'),
  ('take medicine', '吃药', '八年级上册'),
  ('drink more water', '多喝水', '八年级上册'),
  ('be ill', '生病', '八年级上册'),
  ('be healthy', '健康的', '八年级上册'),
  ('do exercise', '锻炼', '八年级上册'),
  ('warm up', '热身', '八年级上册'),
  ('cool down', '放松', '八年级上册'),
  ('win the game', '赢得比赛', '八年级上册'),
  ('lose the game', '输掉比赛', '八年级上册'),
  ('play against', '与……对抗', '八年级上册'),
  ('stay at home', '待在家里', '八年级上册'),
  ('visit museums', '参观博物馆', '八年级上册'),
  ('pass the exam', '通过考试', '八年级上册'),
  ('fail the exam', '考试不及格', '八年级上册'),
  ('get good grades', '取得好成绩', '八年级上册'),
  ('study for a test', '备考', '八年级上册'),
  ('work hard', '努力工作', '八年级上册'),
  ('find a job', '找工作', '八年级上册'),
  ('make money', '赚钱', '八年级上册'),
  ('save money', '省钱', '八年级上册'),
  ('spend money', '花钱', '八年级上册'),
  ('borrow money', '借钱', '八年级上册'),
  ('lend money', '借出钱', '八年级上册'),
  ('buy gifts', '买礼物', '八年级上册'),
  ('give presents', '送礼物', '八年级上册'),
  ('have a party', '举办聚会', '八年级上册'),
  ('make a cake', '做蛋糕', '八年级上册'),
  ('light candles', '点蜡烛', '八年级上册'),
  ('sing birthday song', '唱生日歌', '八年级上册'),
  ('blow out candles', '吹蜡烛', '八年级上册'),
  ('order food', '点餐', '八年级上册'),
  ('pay the bill', '付账', '八年级上册'),
  ('leave a message', '留言', '八年级上册'),
  ('at the train station', '在火车站', '八年级上册'),
  ('at the airport', '在机场', '八年级上册'),
  ('ride in a car', '坐小汽车', '八年级上册'),
  ('traffic jam', '交通堵塞', '八年级上册'),
  ('traffic lights', '交通灯', '八年级上册'),
  ('cross the road', '过马路', '八年级上册'),
  ('walk on the sidewalk', '在人行道上走', '八年级上册'),
  ('stop at the red light', '红灯停', '八年级上册'),
  ('go at the green light', '绿灯行', '八年级上册'),
  ('pollute the environment', '污染环境', '八年级上册'),
  ('plant trees', '植树', '八年级上册'),
  ('save water', '节约用水', '八年级上册'),
  ('save electricity', '节约用电', '八年级上册'),
  ('throw rubbish', '扔垃圾', '八年级上册'),
  ('clean up', '打扫干净', '八年级上册'),
  ('beautiful scenery', '美丽的风景', '八年级上册'),
  ('places of interest', '名胜古迹', '八年级上册'),
  ('take a vacation', '去度假', '八年级上册'),
  ('go sightseeing', '去观光', '八年级上册'),
  ('book a hotel', '预订酒店', '八年级上册'),
  ('room service', '客房服务', '八年级上册'),
  ('go boating', '去划船', '八年级上册'),
  ('take a tour', '参加旅游', '八年级上册'),
  ('guide book', '指南书', '八年级上册'),
  ('travel agency', '旅行社', '八年级上册'),
  ('on the way', '在路上', '八年级上册'),
  ('no way', '决不', '八年级上册'),
  ('lose way', '迷路', '八年级上册'),
  ('lead the way', '带路', '八年级上册'),
  ('feel nervous', '感到紧张', '八年级上册'),
  ('feel relaxed', '感到放松', '八年级上册'),
  ('feel proud', '感到骄傲', '八年级上册'),
  ('feel sorry', '感到抱歉', '八年级上册'),
  ('encourage sb. to do', '鼓励某人做', '八年级上册'),
  ('support sb.', '支持某人', '八年级上册'),
  ('keep trying', '继续努力', '八年级上册'),
  ('achieve dream', '实现梦想', '八年级上册'),
  ('succeed in doing', '成功做……', '八年级上册'),
  ('fail to do', '未能做……', '八年级下册'),
  ('be busy doing', '忙于做……', '八年级下册'),
  ('be used to doing', '习惯于做……', '八年级下册'),
  ('look forward to doing', '期待做……', '八年级下册'),
  ('devote to doing', '致力于做……', '八年级下册'),
  ('believe in', '相信……', '八年级下册'),
  ('complain about', '抱怨……', '八年级下册'),
  ('argue with', '与……争吵', '八年级下册'),
  ('disagree with', '不同意……', '八年级下册'),
  ('share with', '与……分享', '八年级下册'),
  ('help with', '帮助做……', '八年级下册'),
  ('provide with', '提供……', '八年级下册'),
  ('fill with', '用……装满', '八年级下册'),
  ('cover with', '用……覆盖', '八年级下册'),
  ('connect with', '与……连接', '八年级下册'),
  ('get on with', '与……相处', '八年级下册'),
  ('come along with', '随同……', '八年级下册'),
  ('go on with', '继续做……', '八年级下册'),
  ('have something to do with', '与……有关', '八年级下册'),
  ('have nothing to do with', '与……无关', '八年级下册'),
  ('merry Christmas', '圣诞快乐', '八年级下册'),
  ('happy New Year', '新年快乐', '八年级下册'),
  ('you are welcome', '不客气', '八年级下册'),
  ('I am sorry', '对不起', '八年级下册'),
  ('that is OK', '没关系', '八年级下册'),
  ('no problem', '没问题', '八年级下册'),
  ('I think so', '我认为是这样', '八年级下册'),
  ('I do not think so', '我不认为是这样', '八年级下册'),
  ('maybe', '也许', '八年级下册'),
  ('certainly', '当然', '八年级下册'),
  ('sure', '确定', '八年级下册'),
  ('I see', '我明白了', '八年级下册'),
  ('I know', '我知道', '八年级下册'),
  ('I do not know', '我不知道', '八年级下册'),
  ('be bad for', '对...有害', '八年级下册'),
  ('be same as', '与...相同', '八年级下册'),
  ('be friendly to', '对...友好', '八年级下册'),
  ('be strict in', '对...严格（某事）', '八年级下册'),
  ('be used for', '被用来做...', '八年级下册'),
  ('be used by', '被...使用', '八年级下册'),
  ('be used as', '被用作...', '八年级下册'),
  ('used to do', '过去常常做...', '八年级下册'),
  ('have a sore throat', '喉咙痛', '八年级下册'),
  ('take exercise', '锻炼', '八年级下册'),
  ('keep fit', '保持健康', '八年级下册'),
  ('keep silence', '保持安静', '八年级下册'),
  ("keep one's word", '守信', '八年级下册'),
  ("break one's word", '不守信', '八年级下册'),
  ('make sense', '有意义', '八年级下册'),
  ('in the beginning', '在开始时', '八年级下册'),
  ('from then on', '从那时起', '八年级下册'),
  ('sooner or later', '迟早', '八年级下册'),
  ('time and time again', '反复地', '八年级下册'),
  ('at the moment', '此刻', '八年级下册'),
  ('right now', '现在', '八年级下册'),
  ('right away', '立刻', '八年级下册'),
  ('in fear', '恐惧地', '八年级下册'),
  ('in joy', '高兴地', '八年级下册'),
  ('in anger', '愤怒地', '八年级下册'),
  ('in search of', '寻找...', '八年级下册'),
  ('in charge of', '负责...', '八年级下册'),
  ('in memory of', '纪念...', '八年级下册'),
  ('in honor of', '为向...表示敬意', '八年级下册'),
  ('in favor of', '支持...', '八年级下册'),
  ('in case of', '假如...', '八年级下册'),
  ('in spite of', '尽管...', '八年级下册'),
  ('first of all', '首先', '八年级下册'),
  ('to begin with', '首先', '八年级下册'),
  ('secondly', '第二', '八年级下册'),
  ('besides', '此外', '八年级下册'),
  ('what is more', '而且', '八年级下册'),
  ('moreover', '此外', '八年级下册'),
  ('in addition', '另外', '八年级下册'),
  ('finally', '最后', '八年级下册'),
  ('in conclusion', '总之', '八年级下册'),
  ('in summary', '总结', '八年级下册'),
  ('on the one hand', '一方面', '八年级下册'),
  ('on the other hand', '另一方面', '八年级下册'),
  ('however', '然而', '八年级下册'),
  ('nevertheless', '然而', '八年级下册'),
  ('therefore', '因此', '八年级下册'),
  ('thus', '因此', '八年级下册'),
  ('as a result', '结果', '八年级下册'),
  ('due to', '由于', '八年级下册'),
  ('so as to', '以便', '八年级下册'),
  ('such that', '如此...以至于...', '八年级下册'),
  ('too...to...', '太...而不能...', '八年级下册'),
  ('enough to', '足够做...', '八年级下册'),
  ('develop rapidly', '发展迅速', '八年级下册'),
  ('change a lot', '变化很大', '八年级下册'),
  ('improve the environment', '改善环境', '八年级下册'),
  ('plant more trees', '种更多的树', '八年级下册'),
  ('public transport', '公共交通', '八年级下册'),
  ('traffic accident', '交通事故', '八年级下册'),
  ('obey the traffic rules', '遵守交通规则', '八年级下册'),
  ('break the traffic rules', '违反交通规则', '八年级下册'),
  ('on the sidewalk', '在人行道上', '八年级下册'),
  ('get on the bus', '上车', '八年级下册'),
  ('get off the bus', '下车', '八年级下册'),
  ('wait for the bus', '等公共汽车', '八年级下册'),
  ('miss the bus', '错过公共汽车', '八年级下册'),
  ('catch the bus', '赶上公共汽车', '八年级下册'),
  ('never mind', '没关系', '八年级下册'),
  ('congratulations', '恭喜', '八年级下册'),
  ('well done', '干得好', '八年级下册'),
  ('what a pity', '真遗憾', '八年级下册'),
  ('what a shame', '真可惜', '八年级下册'),
  ('I hope so', '我希望如此', '八年级下册'),
  ('I hope not', '我希望不会', '八年级下册'),
  ('I am afraid so', '恐怕是这样的', '八年级下册'),
  ('I am afraid not', '恐怕不是这样的', '八年级下册'),
  ("I don't think so", '我不这样认为', '八年级下册'),
  ('perhaps', '也许', '八年级下册'),
  ('probably', '可能', '八年级下册'),
  ('exactly', '确切地', '八年级下册'),
  ('absolutely', '绝对地', '八年级下册'),
  ('definitely', '肯定地', '八年级下册'),
]

# ==================== 三、口语对话（20个场景）====================
BUILTIN_DIALOGUES = [
    {
        'title': 'Greeting 初次见面',
        'en': "Tom: Hi, I'm Li Ming. Nice to meet you.\nLucy: Nice to meet you too, Li Ming. I'm Mary.\nTom: Where are you from?\nLucy: I'm from Canada.",
        'zh': 'Tom: 你好，我是李明。很高兴认识你。\nLucy: 也很高兴认识你，李明。我是玛丽。\nTom: 你来自哪里？\nLucy: 我来自加拿大。',
        'grade': '七年级上册',
        'dialogue': [["Hi, I'm Li Ming. Nice to meet you.", '你好，我是李明。很高兴认识你。'], ["Nice to meet you too, Li Ming. I'm Mary.", '也很高兴认识你，李明。我是玛丽。'], ['Where are you from?', '你来自哪里？'], ["I'm from Canada.", '我来自加拿大。']],
    },
    {
        'title': 'Asking for help 请求帮助',
        'en': "Tom: Excuse me, could you help me with this box?\nLucy: Sure, no problem. Where should I put it?\nTom: Just on the desk, please. Thank you so much!\nLucy: You're welcome.",
        'zh': 'Tom: 打扰一下，你能帮我搬这个箱子吗？\nLucy: 当然，没问题。放哪里？\nTom: 就放在桌子上。非常感谢！\nLucy: 不客气。',
        'grade': '七年级上册',
        'dialogue': [['Excuse me, could you help me with this box?', '打扰一下，你能帮我搬这个箱子吗？'], ['Sure, no problem. Where should I put it?', '当然，没问题。放哪里？'], ['Just on the desk, please. Thank you so much!', '就放在桌子上。非常感谢！'], ["You're welcome.", '不客气。']],
    },
    {
        'title': 'Shopping 购物',
        'en': "Tom: How much is this T-shirt?\nLucy: It's 25 dollars.\nTom: That's a bit expensive. Any discount?\nLucy: Sorry, it's on sale already. But you can have this one for 20 dollars.",
        'zh': 'Tom: 这件T恤多少钱？\nLucy: 25美元。\nTom: 有点贵。有折扣吗？\nLucy: 抱歉，已经在打折了。但你可以20美元买这件。',
        'grade': '七年级上册',
        'dialogue': [['How much is this T-shirt?', '这件T恤多少钱？'], ["It's 25 dollars.", '25美元。'], ["That's a bit expensive. Any discount?", '有点贵。有折扣吗？'], ["Sorry, it's on sale already. But you can have this one for 20 dollars.", '抱歉，已经在打折了。但你可以20美元买这件。']],
    },
    {
        'title': 'Ordering food 点餐',
        'en': "Tom: May I take your order?\nLucy: Yes, I'd like a cheeseburger and a medium Coke.\nTom: Anything else? Fries or salad?\nLucy: No, thanks. That's all.",
        'zh': 'Tom: 可以点餐了吗？\nLucy: 是的，我要一个芝士汉堡和中杯可乐。\nTom: 还要别的吗？薯条或沙拉？\nLucy: 不了，谢谢。就这些。',
        'grade': '七年级上册',
        'dialogue': [['May I take your order?', '可以点餐了吗？'], ["Yes, I'd like a cheeseburger and a medium Coke.", '是的，我要一个芝士汉堡和中杯可乐。'], ['Anything else? Fries or salad?', '还要别的吗？薯条或沙拉？'], ["No, thanks. That's all.", '不了，谢谢。就这些。']],
    },
    {
        'title': 'Asking for directions 问路',
        'en': "Tom: Excuse me, where is the nearest post office?\nLucy: Go straight for two blocks, then turn left. You'll see it on your right.\nTom: Is it far?\nLucy: No, about a 10-minute walk.",
        'zh': 'Tom: 打扰一下，最近的邮局在哪里？\nLucy: 直走两个街区，然后左转。它就在你右边。\nTom: 远吗？\nLucy: 不远，步行大约10分钟。',
        'grade': '七年级上册',
        'dialogue': [['Excuse me, where is the nearest post office?', '打扰一下，最近的邮局在哪里？'], ["Go straight for two blocks, then turn left. You'll see it on your right.", '直走两个街区，然后左转。它就在你右边。'], ['Is it far?', '远吗？'], ['No, about a 10-minute walk.', '不远，步行大约10分钟。']],
    },
    {
        'title': 'Weather 谈论天气',
        'en': "Tom: Beautiful day, isn't it?\nLucy: Yes, it's sunny and warm. Great for a picnic.\nTom: But the forecast says it might rain in the afternoon.\nLucy: Oh, maybe we should bring an umbrella.",
        'zh': 'Tom: 天气真好，不是吗？\nLucy: 是的，晴朗温暖。很适合野餐。\nTom: 但是天气预报说下午可能会下雨。\nLucy: 哦，也许我们应该带把伞。',
        'grade': '七年级上册',
        'dialogue': [["Beautiful day, isn't it?", '天气真好，不是吗？'], ["Yes, it's sunny and warm. Great for a picnic.", '是的，晴朗温暖。很适合野餐。'], ['But the forecast says it might rain in the afternoon.', '但是天气预报说下午可能会下雨。'], ['Oh, maybe we should bring an umbrella.', '哦，也许我们应该带把伞。']],
    },
    {
        'title': 'Making a phone call 打电话',
        'en': "Tom: Hello, may I speak to Tom?\nLucy: Speaking. Who's that?\nTom: This is Jerry. Are we still meeting at 3 PM?\nLucy: Sure. See you then.",
        'zh': 'Tom: 你好，请找汤姆接电话。\nLucy: 我就是。你是哪位？\nTom: 我是杰瑞。我们下午3点还见面吗？\nLucy: 当然。到时候见。',
        'grade': '七年级上册',
        'dialogue': [['Hello, may I speak to Tom?', '你好，请找汤姆接电话。'], ["Speaking. Who's that?", '我就是。你是哪位？'], ['This is Jerry. Are we still meeting at 3 PM?', '我是杰瑞。我们下午3点还见面吗？'], ['Sure. See you then.', '当然。到时候见。']],
    },
    {
        'title': 'Invitation 邀请',
        'en': "Tom: Are you free this Saturday? We're having a party at my place.\nLucy: That sounds great! What time?\nTom: Around 7 PM. You can bring a friend.\nLucy: OK, I'll be there. Thanks for inviting me.",
        'zh': 'Tom: 这周六你有空吗？我们在我家举办派对。\nLucy: 听起来很棒！几点？\nTom: 晚上7点左右。你可以带个朋友。\nLucy: 好的，我会去的。谢谢邀请。',
        'grade': '七年级上册',
        'dialogue': [["Are you free this Saturday? We're having a party at my place.", '这周六你有空吗？我们在我家举办派对。'], ['That sounds great! What time?', '听起来很棒！几点？'], ['Around 7 PM. You can bring a friend.', '晚上7点左右。你可以带个朋友。'], ["OK, I'll be there. Thanks for inviting me.", '好的，我会去的。谢谢邀请。']],
    },
    {
        'title': 'Talking about hobbies 谈论爱好',
        'en': 'Tom: What do you like to do in your free time?\nLucy: I enjoy reading and playing basketball.\nTom: Really? I also love basketball. Maybe we can play together sometime.\nLucy: That would be great!',
        'zh': 'Tom: 你空闲时间喜欢做什么？\nLucy: 我喜欢阅读和打篮球。\nTom: 真的吗？我也爱篮球。也许我们可以找时间一起打。\nLucy: 那太好了！',
        'grade': '七年级上册',
        'dialogue': [['What do you like to do in your free time?', '你空闲时间喜欢做什么？'], ['I enjoy reading and playing basketball.', '我喜欢阅读和打篮球。'], ['Really? I also love basketball. Maybe we can play together sometime.', '真的吗？我也爱篮球。也许我们可以找时间一起打。'], ['That would be great!', '那太好了！']],
    },
    {
        'title': 'At the library 在图书馆',
        'en': 'Tom: Excuse me, can I borrow this book?\nLucy: Sure. Do you have a library card?\nTom: Yes, here it is.\nLucy: OK, you can keep it for two weeks. Please return it on time.',
        'zh': 'Tom: 打扰一下，我可以借这本书吗？\nLucy: 当然。你有借书证吗？\nTom: 有，给你。\nLucy: 好的，你可以借两周。请按时归还。',
        'grade': '七年级上册',
        'dialogue': [['Excuse me, can I borrow this book?', '打扰一下，我可以借这本书吗？'], ['Sure. Do you have a library card?', '当然。你有借书证吗？'], ['Yes, here it is.', '有，给你。'], ['OK, you can keep it for two weeks. Please return it on time.', '好的，你可以借两周。请按时归还。']],
    },
    {
        'title': 'Travel plan 旅行计划',
        'en': "Tom: Where are you going for summer vacation?\nLucy: I'm planning to visit Beijing with my family.\nTom: Wonderful! What places will you see?\nLucy: The Great Wall, the Forbidden City, and the Summer Palace.",
        'zh': 'Tom: 你暑假要去哪里？\nLucy: 我计划和家人去北京。\nTom: 太棒了！你们会去哪些地方？\nLucy: 长城、故宫和颐和园。',
        'grade': '七年级上册',
        'dialogue': [['Where are you going for summer vacation?', '你暑假要去哪里？'], ["I'm planning to visit Beijing with my family.", '我计划和家人去北京。'], ['Wonderful! What places will you see?', '太棒了！你们会去哪些地方？'], ['The Great Wall, the Forbidden City, and the Summer Palace.', '长城、故宫和颐和园。']],
    },
    {
        'title': 'Apologizing 道歉',
        'en': "Tom: I'm really sorry I broke your cup.\nLucy: Don't worry about it. It was old anyway.\nTom: Still, I feel bad. Let me buy you a new one.\nLucy: No, it's fine. Thanks for apologizing.",
        'zh': 'Tom: 真的很抱歉，我打碎了你的杯子。\nLucy: 别担心。反正它已经很旧了。\nTom: 但我还是过意不去。让我给你买个新的吧。\nLucy: 不用，没关系。谢谢你的道歉。',
        'grade': '七年级上册',
        'dialogue': [["I'm really sorry I broke your cup.", '真的很抱歉，我打碎了你的杯子。'], ["Don't worry about it. It was old anyway.", '别担心。反正它已经很旧了。'], ['Still, I feel bad. Let me buy you a new one.', '但我还是过意不去。让我给你买个新的吧。'], ["No, it's fine. Thanks for apologizing.", '不用，没关系。谢谢你的道歉。']],
    },
    {
        'title': 'Talking about school 谈论学校',
        'en': "Tom: How many classes do you have today?\nLucy: Five. Math, English, science, history, and PE.\nTom: Which subject do you like best?\nLucy: I like science because it's interesting.",
        'zh': 'Tom: 你今天有几节课？\nLucy: 五节。数学、英语、科学、历史和体育。\nTom: 你最喜欢哪门课？\nLucy: 我喜欢科学，因为它有趣。',
        'grade': '七年级上册',
        'dialogue': [['How many classes do you have today?', '你今天有几节课？'], ['Five. Math, English, science, history, and PE.', '五节。数学、英语、科学、历史和体育。'], ['Which subject do you like best?', '你最喜欢哪门课？'], ["I like science because it's interesting.", '我喜欢科学，因为它有趣。']],
    },
    {
        'title': 'At the airport 在机场',
        'en': "Tom: Your flight is boarding now. Have a safe trip!\nLucy: Thank you. I'll call you when I land.\nTom: OK. Take care.\nLucy: You too. Bye!",
        'zh': 'Tom: 你的航班开始登机了。一路平安！\nLucy: 谢谢。我降落时给你打电话。\nTom: 好的。保重。\nLucy: 你也是。再见！',
        'grade': '七年级上册',
        'dialogue': [['Your flight is boarding now. Have a safe trip!', '你的航班开始登机了。一路平安！'], ["Thank you. I'll call you when I land.", '谢谢。我降落时给你打电话。'], ['OK. Take care.', '好的。保重。'], ['You too. Bye!', '你也是。再见！']],
    },
    {
        'title': 'Complimenting 赞美',
        'en': "Tom: I love your new haircut. It looks great on you.\nLucy: Oh, thank you! I was a bit nervous about it.\nTom: No need. You look fantastic.\nLucy: You're so kind.",
        'zh': 'Tom: 我喜欢你的新发型。很适合你。\nLucy: 哦，谢谢！我还有点紧张呢。\nTom: 不用。你看起来棒极了。\nLucy: 你真好。',
        'grade': '七年级上册',
        'dialogue': [['I love your new haircut. It looks great on you.', '我喜欢你的新发型。很适合你。'], ['Oh, thank you! I was a bit nervous about it.', '哦，谢谢！我还有点紧张呢。'], ['No need. You look fantastic.', '不用。你看起来棒极了。'], ["You're so kind.", '你真好。']],
    },
    {
        'title': 'At a restaurant 餐厅里',
        'en': "Tom: Are you ready to order?\nLucy: Yes. I'll have the steak, medium rare, with mashed potatoes.\nTom: And for you, sir?\nC: The same, but with a salad instead of potatoes.",
        'zh': 'Tom: 可以点菜了吗？\nLucy: 是的。我要牛排，五分熟，配土豆泥。\nTom: 先生，您呢？\nC: 一样，但是把土豆换成沙拉。',
        'grade': '七年级上册',
        'dialogue': [['Are you ready to order?', '可以点菜了吗？'], ["Yes. I'll have the steak, medium rare, with mashed potatoes.", '是的。我要牛排，五分熟，配土豆泥。'], ['And for you, sir?', '先生，您呢？'], ['The same, but with a salad instead of potatoes.', '一样，但是把土豆换成沙拉。']],
    },
    {
        'title': 'Giving advice 提建议',
        'en': "Tom: I'm always tired after school.\nLucy: Maybe you should go to bed earlier.\nTom: But I have so much homework.\nLucy: Try to manage your time better. Take short breaks.",
        'zh': 'Tom: 放学后我总是很累。\nLucy: 也许你应该早点睡觉。\nTom: 但是我作业很多。\nLucy: 试着更好地管理时间。短暂休息一下。',
        'grade': '七年级上册',
        'dialogue': [["I'm always tired after school.", '放学后我总是很累。'], ['Maybe you should go to bed earlier.', '也许你应该早点睡觉。'], ['But I have so much homework.', '但是我作业很多。'], ['Try to manage your time better. Take short breaks.', '试着更好地管理时间。短暂休息一下。']],
    },
    {
        'title': 'Talking about future 谈论未来',
        'en': "Tom: What do you want to be when you grow up?\nLucy: I want to be a doctor and help sick people.\nTom: That's a noble goal. I want to be a software engineer.\nLucy: Great! Let's work hard for our dreams.",
        'zh': 'Tom: 你长大后想做什么？\nLucy: 我想当医生，帮助病人。\nTom: 那是个崇高的目标。我想当软件工程师。\nLucy: 太好了！让我们为梦想努力。',
        'grade': '七年级上册',
        'dialogue': [['What do you want to be when you grow up?', '你长大后想做什么？'], ['I want to be a doctor and help sick people.', '我想当医生，帮助病人。'], ["That's a noble goal. I want to be a software engineer.", '那是个崇高的目标。我想当软件工程师。'], ["Great! Let's work hard for our dreams.", '太好了！让我们为梦想努力。']],
    },
    {
        'title': 'Emergency 紧急情况',
        'en': "Tom: Help! I need a doctor quickly.\nLucy: What happened?\nTom: My friend fell and hurt his leg badly.\nLucy: Don't move him. I'll call 911 right now.",
        'zh': 'Tom: 救命！我需要医生，快点。\nLucy: 发生了什么事？\nTom: 我朋友摔倒了，腿伤得很重。\nLucy: 别动他。我马上打急救电话。',
        'grade': '七年级上册',
        'dialogue': [['Help! I need a doctor quickly.', '救命！我需要医生，快点。'], ['What happened?', '发生了什么事？'], ['My friend fell and hurt his leg badly.', '我朋友摔倒了，腿伤得很重。'], ["Don't move him. I'll call 911 right now.", '别动他。我马上打急救电话。']],
    },
    {
        'title': 'Farewell 告别',
        'en': "Tom: I'm moving to another city next week.\nLucy: Oh, I'm sorry to hear that. We'll miss you.\nTom: I'll miss you too. Let's keep in touch.\nLucy: Definitely. Good luck with everything.",
        'zh': 'Tom: 我下周要搬到另一个城市了。\nLucy: 哦，听到这消息很难过。我们会想你的。\nTom: 我也会想你们。我们保持联系。\nLucy: 一定。祝你一切顺利。',
        'grade': '七年级上册',
        'dialogue': [["I'm moving to another city next week.", '我下周要搬到另一个城市了。'], ["Oh, I'm sorry to hear that. We'll miss you.", '哦，听到这消息很难过。我们会想你的。'], ["I'll miss you too. Let's keep in touch.", '我也会想你们。我们保持联系。'], ['Definitely. Good luck with everything.', '一定。祝你一切顺利。']],
    },
    {
        'title': 'Daily Routine 日常生活',
        'en': "Tom: What time do you usually get up?\nLucy: I usually get up at 6:30 AM.\nTom: That's early! Do you have breakfast at home?\nLucy: Yes, my mom makes breakfast for me every day.",
        'zh': 'Tom: 你通常几点起床？\nLucy: 我通常早上6:30起床。\nTom: 那么早！你在家吃早餐吗？\nLucy: 是的，我妈妈每天给我做早餐。',
        'grade': '七年级下册',
        'dialogue': [['What time do you usually get up?', '你通常几点起床？'], ['I usually get up at 6:30 AM.', '我通常早上6:30起床。'], ["That's early! Do you have breakfast at home?", '那么早！你在家吃早餐吗？'], ['Yes, my mom makes breakfast for me every day.', '是的，我妈妈每天给我做早餐。']],
    },
    {
        'title': 'Weekend Plans 周末计划',
        'en': "Tom: Do you have any plans for this weekend?\nLucy: I'm going to the park with my family. How about you?\nTom: I think I'll stay home and read some books.\nLucy: That sounds relaxing!",
        'zh': 'Tom: 这个周末你有什么计划吗？\nLucy: 我要和家人去公园。你呢？\nTom: 我想我会待在家里看书。\nLucy: 听起来很放松！',
        'grade': '七年级下册',
        'dialogue': [['Do you have any plans for this weekend?', '这个周末你有什么计划吗？'], ["I'm going to the park with my family. How about you?", '我要和家人去公园。你呢？'], ["I think I'll stay home and read some books.", '我想我会待在家里看书。'], ['That sounds relaxing!', '听起来很放松！']],
    },
    {
        'title': 'Family 家庭',
        'en': 'Tom: How many people are there in your family?\nLucy: There are four—my parents, my sister and me.\nTom: Do you get along well with your sister?\nLucy: Yes, we often help each other with homework.',
        'zh': 'Tom: 你家有几口人？\nLucy: 四口人——我父母、我姐姐和我。\nTom: 你和姐姐相处得好吗？\nLucy: 是的，我们经常互相帮助做作业。',
        'grade': '七年级下册',
        'dialogue': [['How many people are there in your family?', '你家有几口人？'], ['There are four—my parents, my sister and me.', '四口人——我父母、我姐姐和我。'], ['Do you get along well with your sister?', '你和姐姐相处得好吗？'], ['Yes, we often help each other with homework.', '是的，我们经常互相帮助做作业。']],
    },
    {
        'title': 'Favorite Food 最喜欢的食物',
        'en': "Tom: What's your favorite food?\nLucy: I love noodles, especially beef noodles.\nTom: That's my favorite too! Which restaurant has the best noodles?\nLucy: There's a small shop near our school. It's delicious and cheap.",
        'zh': 'Tom: 你最喜欢的食物是什么？\nLucy: 我喜欢面条，特别是牛肉面。\nTom: 那也是我最喜欢的！哪家餐厅的面最好吃？\nLucy: 我们学校附近有个小店。又好吃又便宜。',
        'grade': '七年级下册',
        'dialogue': [["What's your favorite food?", '你最喜欢的食物是什么？'], ['I love noodles, especially beef noodles.', '我喜欢面条，特别是牛肉面。'], ["That's my favorite too! Which restaurant has the best noodles?", '那也是我最喜欢的！哪家餐厅的面最好吃？'], ["There's a small shop near our school. It's delicious and cheap.", '我们学校附近有个小店。又好吃又便宜。']],
    },
    {
        'title': 'Sports 运动',
        'en': 'Tom: Which sport do you like best?\nLucy: I like basketball. I play it every Saturday.\nTom: Really? I like badminton. Do you want to play together sometime?\nLucy: Sure! That would be fun.',
        'zh': 'Tom: 你最喜欢哪项运动？\nLucy: 我喜欢篮球。我每周六都打。\nTom: 真的吗？我喜欢羽毛球。有空我们一起打吧？\nLucy: 好啊！那会很有趣。',
        'grade': '七年级下册',
        'dialogue': [['Which sport do you like best?', '你最喜欢哪项运动？'], ['I like basketball. I play it every Saturday.', '我喜欢篮球。我每周六都打。'], ['Really? I like badminton. Do you want to play together sometime?', '真的吗？我喜欢羽毛球。有空我们一起打吧？'], ['Sure! That would be fun.', '好啊！那会很有趣。']],
    },
    {
        'title': 'Movies 电影',
        'en': "Tom: Did you watch that new movie last weekend?\nLucy: No, I didn't. Is it good?\nTom: Yes! It's a comedy and very funny.\nLucy: Maybe I'll watch it this weekend with my friends.",
        'zh': 'Tom: 你上周末看了那部新电影吗？\nLucy: 没有，我没看。好看吗？\nTom: 好看！是喜剧片，非常搞笑。\nLucy: 也许我这周末和朋友一起去看。',
        'grade': '七年级下册',
        'dialogue': [['Did you watch that new movie last weekend?', '你上周末看了那部新电影吗？'], ["No, I didn't. Is it good?", '没有，我没看。好看吗？'], ["Yes! It's a comedy and very funny.", '好看！是喜剧片，非常搞笑。'], ["Maybe I'll watch it this weekend with my friends.", '也许我这周末和朋友一起去看。']],
    },
    {
        'title': 'Birthday Party 生日派对',
        'en': "Tom: When is your birthday?\nLucy: It's on May 12th. I'm having a party at my house.\nTom: That's next Saturday! Can I come?\nLucy: Of course! I'll send you the address.",
        'zh': 'Tom: 你的生日是什么时候？\nLucy: 5月12日。我要在家里办派对。\nTom: 那是下周六！我可以来吗？\nLucy: 当然可以！我会把地址发给你。',
        'grade': '七年级下册',
        'dialogue': [['When is your birthday?', '你的生日是什么时候？'], ["It's on May 12th. I'm having a party at my house.", '5月12日。我要在家里办派对。'], ["That's next Saturday! Can I come?", '那是下周六！我可以来吗？'], ["Of course! I'll send you the address.", '当然可以！我会把地址发给你。']],
    },
    {
        'title': 'Holidays 假期',
        'en': 'Tom: Where did you go during the summer holiday?\nLucy: I went to Beijing with my parents.\nTom: Wow! Did you visit the Great Wall?\nLucy: Yes, it was amazing. I took lots of photos.',
        'zh': 'Tom: 暑假你去哪里了？\nLucy: 我和父母去了北京。\nTom: 哇！你去爬长城了吗？\nLucy: 去了，太壮观了。我拍了很多照片。',
        'grade': '七年级下册',
        'dialogue': [['Where did you go during the summer holiday?', '暑假你去哪里了？'], ['I went to Beijing with my parents.', '我和父母去了北京。'], ['Wow! Did you visit the Great Wall?', '哇！你去爬长城了吗？'], ['Yes, it was amazing. I took lots of photos.', '去了，太壮观了。我拍了很多照片。']],
    },
    {
        'title': 'Clothes Shopping 买衣服',
        'en': "Tom: Can I help you find anything?\nLucy: Yes, I'm looking for a jacket.\nTom: What size are you? We have S, M, L and XL.\nLucy: I think M. Can I try it on?\nTom: Sure, the fitting room is over there.",
        'zh': 'Tom: 需要我帮你找什么吗？\nLucy: 是的，我想买一件夹克。\nTom: 你穿什么尺码？我们有S、M、L和XL。\nLucy: 我想是M。我可以试穿吗？\nTom: 当然，试衣间在那边。',
        'grade': '七年级下册',
        'dialogue': [['Can I help you find anything?', '需要我帮你找什么吗？'], ["Yes, I'm looking for a jacket.", '是的，我想买一件夹克。'], ['What size are you? We have S, M, L and XL.', '你穿什么尺码？我们有S、M、L和XL。'], ['I think M. Can I try it on?', '我想是M。我可以试穿吗？'], ['Sure, the fitting room is over there.', '当然，试衣间在那边。']],
    },
    {
        'title': 'Asking Permission 请求许可',
        'en': 'Tom: Mom, can I go to the library after school?\nLucy: Sure, but come back before 6 PM.\nTom: OK, I will. I need to return some books.\nLucy: Be careful on the way.',
        'zh': 'Tom: 妈妈，放学后我可以去图书馆吗？\nLucy: 可以，但下午6点前回来。\nTom: 好的，我会的。我要还一些书。\nLucy: 路上小心。',
        'grade': '七年级下册',
        'dialogue': [['Mom, can I go to the library after school?', '妈妈，放学后我可以去图书馆吗？'], ['Sure, but come back before 6 PM.', '可以，但下午6点前回来。'], ['OK, I will. I need to return some books.', '好的，我会的。我要还一些书。'], ['Be careful on the way.', '路上小心。']],
    },
    {
        'title': 'Making Appointments 预约',
        'en': "Tom: Hello, I'd like to make an appointment with Dr. Smith.\nLucy: What day works for you?\nTom: Is next Monday afternoon available?\nLucy: Yes, 3 PM is fine. Please arrive 10 minutes early.",
        'zh': 'Tom: 你好，我想预约史密斯医生。\nLucy: 你哪天方便？\nTom: 下周一下午有空吗？\nLucy: 有，下午3点可以。请提前10分钟到。',
        'grade': '七年级下册',
        'dialogue': [["Hello, I'd like to make an appointment with Dr. Smith.", '你好，我想预约史密斯医生。'], ['What day works for you?', '你哪天方便？'], ['Is next Monday afternoon available?', '下周一下午有空吗？'], ['Yes, 3 PM is fine. Please arrive 10 minutes early.', '有，下午3点可以。请提前10分钟到。']],
    },
    {
        'title': 'Health and Exercise 健康与锻炼',
        'en': "Tom: You look very healthy. Do you exercise often?\nLucy: Yes, I run for 30 minutes every morning.\nTom: That's great! I should exercise more too.\nLucy: Why don't we run together tomorrow morning?",
        'zh': 'Tom: 你看起来很健康。你经常锻炼吗？\nLucy: 是的，我每天早上跑30分钟。\nTom: 太棒了！我也应该多锻炼。\nLucy: 我们明天早上一起跑吧？',
        'grade': '七年级下册',
        'dialogue': [['You look very healthy. Do you exercise often?', '你看起来很健康。你经常锻炼吗？'], ['Yes, I run for 30 minutes every morning.', '是的，我每天早上跑30分钟。'], ["That's great! I should exercise more too.", '太棒了！我也应该多锻炼。'], ["Why don't we run together tomorrow morning?", '我们明天早上一起跑吧？']],
    },
    {
        'title': 'Internet and Technology 互联网与科技',
        'en': "Tom: How often do you use the Internet?\nLucy: Almost every day. I use it for study and fun.\nTom: Me too. But my parents limit my screen time.\nLucy: Same here. They say it's not good for my eyes.",
        'zh': 'Tom: 你多久上一次网？\nLucy: 几乎每天。我用它来学习和娱乐。\nTom: 我也是。但我父母限制我的屏幕时间。\nLucy: 我也是。他们说对眼睛不好。',
        'grade': '七年级下册',
        'dialogue': [['How often do you use the Internet?', '你多久上一次网？'], ['Almost every day. I use it for study and fun.', '几乎每天。我用它来学习和娱乐。'], ['Me too. But my parents limit my screen time.', '我也是。但我父母限制我的屏幕时间。'], ["Same here. They say it's not good for my eyes.", '我也是。他们说对眼睛不好。']],
    },
    {
        'title': 'Taking a Bus 乘公交车',
        'en': 'Tom: Excuse me, does this bus go to the train station?\nLucy: Yes, it goes there. You need to get off at the fifth stop.\nTom: How much is the ticket?\nLucy: Two yuan. Please put the money in the box.',
        'zh': 'Tom: 打扰一下，这趟公交车去火车站吗？\nLucy: 是的，去那里。你要在第5站下车。\nTom: 车票多少钱？\nLucy: 两元。请把钱放进箱子里。',
        'grade': '七年级下册',
        'dialogue': [['Excuse me, does this bus go to the train station?', '打扰一下，这趟公交车去火车站吗？'], ['Yes, it goes there. You need to get off at the fifth stop.', '是的，去那里。你要在第5站下车。'], ['How much is the ticket?', '车票多少钱？'], ['Two yuan. Please put the money in the box.', '两元。请把钱放进箱子里。']],
    },
    {
        'title': 'At the Hotel 在酒店',
        'en': 'Tom: I have a reservation under the name Li Ming.\nLucy: Let me check... Yes, a single room for two nights.\nTom: Does the room have free Wi-Fi?\nLucy: Yes, and breakfast is included too.',
        'zh': 'Tom: 我用李明这个名字预订了房间。\nLucy: 我查一下……是的，一间单人房，住两晚。\nTom: 房间有免费Wi-Fi吗？\nLucy: 有，而且早餐也包含在内。',
        'grade': '七年级下册',
        'dialogue': [['I have a reservation under the name Li Ming.', '我用李明这个名字预订了房间。'], ['Let me check... Yes, a single room for two nights.', '我查一下……是的，一间单人房，住两晚。'], ['Does the room have free Wi-Fi?', '房间有免费Wi-Fi吗？'], ['Yes, and breakfast is included too.', '有，而且早餐也包含在内。']],
    },
    {
        'title': 'Complaining 投诉',
        'en': "Tom: Excuse me, I ordered beef noodles but this is chicken noodles.\nLucy: Oh, I'm very sorry. Let me check your order.\nTom: I've been waiting for 30 minutes already.\nLucy: I apologize. Your correct order will be ready in 5 minutes.",
        'zh': 'Tom: 打扰一下，我点的是牛肉面，但这是鸡肉面。\nLucy: 哦，非常抱歉。让我查一下你的订单。\nTom: 我已经等了30分钟了。\nLucy: 我道歉。你正确的订单5分钟内就好。',
        'grade': '七年级下册',
        'dialogue': [['Excuse me, I ordered beef noodles but this is chicken noodles.', '打扰一下，我点的是牛肉面，但这是鸡肉面。'], ["Oh, I'm very sorry. Let me check your order.", '哦，非常抱歉。让我查一下你的订单。'], ["I've been waiting for 30 minutes already.", '我已经等了30分钟了。'], ['I apologize. Your correct order will be ready in 5 minutes.', '我道歉。你正确的订单5分钟内就好。']],
    },
    {
        'title': 'Making Friends 交朋友',
        'en': "Tom: Hi, is this seat taken?\nLucy: No, it's free. Sit down, please.\nTom: Thanks. I'm new here. What's your name?\nLucy: I'm Tom. Nice to meet you!",
        'zh': 'Tom: 你好，这个座位有人坐吗？\nLucy: 没有，空的。请坐。\nTom: 谢谢。我是新来的。你叫什么名字？\nLucy: 我叫汤姆。很高兴认识你！',
        'grade': '七年级下册',
        'dialogue': [['Hi, is this seat taken?', '你好，这个座位有人坐吗？'], ["No, it's free. Sit down, please.", '没有，空的。请坐。'], ["Thanks. I'm new here. What's your name?", '谢谢。我是新来的。你叫什么名字？'], ["I'm Tom. Nice to meet you!", '我叫汤姆。很高兴认识你！']],
    },
    {
        'title': 'After-school Activities 课后活动',
        'en': "Tom: Which club did you join this term?\nLucy: I joined the English club. We practice speaking every Tuesday.\nTom: That's cool. I joined the art club.\nLucy: Really? Can you draw cartoons?",
        'zh': 'Tom: 这学期你参加了哪个社团？\nLucy: 我参加了英语社团。我们每周二练习口语。\nTom: 太酷了。我参加了美术社团。\nLucy: 真的吗？你会画漫画吗？',
        'grade': '七年级下册',
        'dialogue': [['Which club did you join this term?', '这学期你参加了哪个社团？'], ['I joined the English club. We practice speaking every Tuesday.', '我参加了英语社团。我们每周二练习口语。'], ["That's cool. I joined the art club.", '太酷了。我参加了美术社团。'], ['Really? Can you draw cartoons?', '真的吗？你会画漫画吗？']],
    },
    {
        'title': 'Shopping for Gifts 买礼物',
        'en': "Tom: I want to buy a gift for my friend's birthday.\nLucy: How about a book or a music box?\nTom: She loves reading. A book is a good idea.\nLucy: There's a bookstore on the second floor.",
        'zh': 'Tom: 我想给朋友的生日买个礼物。\nLucy: 书或者音乐盒怎么样？\nTom: 她喜欢阅读。书是个好主意。\nLucy: 二楼有一家书店。',
        'grade': '七年级下册',
        'dialogue': [["I want to buy a gift for my friend's birthday.", '我想给朋友的生日买个礼物。'], ['How about a book or a music box?', '书或者音乐盒怎么样？'], ['She loves reading. A book is a good idea.', '她喜欢阅读。书是个好主意。'], ["There's a bookstore on the second floor.", '二楼有一家书店。']],
    },
    {
        'title': 'Talking about Seasons 谈论季节',
        'en': "Tom: Which season do you like best?\nLucy: I like autumn best. The weather is cool and the leaves are beautiful.\nTom: I prefer spring. Everything comes back to life.\nLucy: That's true. Spring is full of hope.",
        'zh': 'Tom: 你最喜欢哪个季节？\nLucy: 我最喜欢秋天。天气凉爽，树叶很美。\nTom: 我更喜欢春天。万物复苏。\nLucy: 没错。春天充满希望。',
        'grade': '七年级下册',
        'dialogue': [['Which season do you like best?', '你最喜欢哪个季节？'], ['I like autumn best. The weather is cool and the leaves are beautiful.', '我最喜欢秋天。天气凉爽，树叶很美。'], ['I prefer spring. Everything comes back to life.', '我更喜欢春天。万物复苏。'], ["That's true. Spring is full of hope.", '没错。春天充满希望。']],
    },
    {
        'title': 'Job Interview',
        'en': "Tom: Good morning. Please sit down. I'm Mr. Brown, the HR manager.\nLucy: Good morning, Mr. Brown. Thank you for having me.\nTom: Could you tell me something about yourself?\nLucy: My name is Li Hua. I graduated from Beijing University with a degree in English. I have been working as an English teacher for three years.\nTom: Why do you want to change your job?\nLucy: I want to challenge myself in a new environment. Your company has a good reputation and I think I can learn a lot here.\nTom: What are your strengths?\nLucy: I am patient, responsible, and I can communicate well with people. I also have good computer skills.\nTom: Can you work under pressure?\nLucy: Yes, I can. Teaching requires me to handle pressure every day, so I am used to it.\nTom: What is your greatest weakness?\nLucy: Sometimes I work too hard and forget to take breaks. I am trying to improve my time management.\nTom: Do you have any questions for me?\nLucy: Yes, what would a typical workday look like for this position?\nTom: You would handle international business communications and translate documents.\nLucy: That sounds interesting. When can I know the result?\nTom: We will inform you within one week. Thank you for coming today.\nLucy: Thank you, Mr. Brown. I look forward to hearing from you.",
        'zh': 'Tom: 早上好，请坐。我是布朗先生，人力资源经理。\nLucy: 早上好，布朗先生，谢谢您给我这个机会。\nTom: 能介绍一下你自己吗？\nLucy: 我叫李华，毕业于北京大学英语专业。我已经做了三年英语老师了。\nTom: 你为什么想换工作？\nLucy: 我想在新环境中挑战自己。贵公司声誉很好，我觉得能在这里学到很多东西。\nTom: 你的优势是什么？\nLucy: 我有耐心、负责任，善于与人沟通，而且电脑技能也不错。\nTom: 你能承受压力吗？\nLucy: 能。教学本身每天都要承受压力，所以我已经习惯了。\nTom: 你最大的缺点是什么？\nLucy: 有时候我工作太努力忘记休息。我正在努力改善时间管理。\nTom: 你有什么问题想问我的吗？\nLucy: 是的，这个职位的典型工作日是什么样的？\nTom: 你将处理国际商务沟通和文件翻译工作。\nLucy: 听起来很有趣。我什么时候能知道结果？\nTom: 我们会在一周内通知你。谢谢你今天来面试。\nLucy: 谢谢您，布朗先生。期待您的好消息。',
        'grade': '八年级上册',
        'dialogue': [['Good morning. Please have a seat.', '早上好，请坐。'], ["Thank you. I'm here for the interview.", '谢谢，我是来参加面试的。'], ['Tell me about yourself.', '请介绍一下你自己。'], ['I graduated from Peking University last year.', '我去年毕业于北京大学。'], ["What's your major?", '你学的是什么专业？'], ['My major is Computer Science.', '我的专业是计算机科学。'], ['Do you have any work experience?', '你有工作经验吗？'], ['I had an internship at a tech company.', '我在一家科技公司实习过。'], ['Why do you want to work here?', '你为什么想在这里工作？'], ['Because your company is a leader in AI.', '因为贵公司是人工智能领域的领导者。'], ['What are your strengths?', '你的优点是什么？'], ["I'm good at Python and problem solving.", '我擅长Python和解决问题。'], ['When can you start?', '你什么时候能开始工作？'], ['I can start next month.', '我下个月可以开始。'], ["We'll call you next week. Thank you.", '我们下周会给你打电话，谢谢。']],
    },
    {
        'title': 'At the Hospital',
        'en': 'Tom: Good afternoon. What brings you here today?\nLucy: Good afternoon, doctor. I have been feeling very tired lately and I cannot sleep well at night.\nTom: How long has this been going on?\nLucy: For about two weeks. I also have a headache sometimes.\nTom: Do you have any other symptoms? Like a fever or a cough?\nLucy: No fever, but I do have a dry cough now and then.\nTom: Let me check your temperature and blood pressure first. Please sit here.\nLucy: OK, doctor.\nTom: Your temperature is normal, but your blood pressure is a little high. Are you under a lot of stress recently?\nLucy: Yes, I have an important exam coming up and I am very worried about it.\nTom: I see. You need to relax more. Are you doing any exercise?\nLucy: Not really. I am too busy with my studies.\nTom: That might be part of the problem. I recommend you take a walk for 30 minutes every day and get enough sleep.\nLucy: Should I take some medicine?\nTom: I will give you some mild sleeping pills. Take one before bed, but only for one week. Do not rely on them for too long.\nLucy: I understand. Is there anything else I should pay attention to?\nTom: Try to avoid coffee and tea in the evening. Also, do not use your phone before sleeping.\nLucy: Got it. Thank you very much, doctor.\nTom: You are welcome. Come back if the symptoms continue. Take care of yourself.',
        'zh': 'Tom: 下午好，今天哪里不舒服？\nLucy: 下午好，医生。我最近总觉得非常疲倦，晚上也睡不好。\nTom: 这样持续多久了？\nLucy: 大概两周了。有时候还会头痛。\nTom: 还有其他症状吗？比如发烧或咳嗽？\nLucy: 不发烧，但偶尔会干咳。\nTom: 先让我检查一下你的体温和血压。请坐这里。\nLucy: 好的，医生。\nTom: 体温正常，但血压有点高。你最近压力大吗？\nLucy: 是的，有一个重要考试快要来了，我非常担心。\nTom: 我明白了。你需要多放松。你有运动吗？\nLucy: 几乎没有。我学习太忙了。\nTom: 这可能是原因之一。我建议你每天散步30分钟，保证充足睡眠。\nLucy: 我需要吃药吗？\nTom: 我给你开一些温和的安眠药。睡前吃一片，只吃一周，不要长期依赖。\nLucy: 我明白了。还有什么需要注意的吗？\nTom: 晚上尽量避免喝咖啡和茶。还有，睡前不要玩手机。\nLucy: 明白了。非常感谢您，医生。\nTom: 不客气。如果症状持续就再来复查。多保重。',
        'grade': '八年级上册',
        'dialogue': [["Good morning. I'd like to see a doctor.", '早上好，我想看医生。'], ['Do you have an appointment?', '你有预约吗？'], ["No, I don't. I feel terrible.", '没有，我感觉很难受。'], ['What seems to be the problem?', '你哪里不舒服？'], ['I have a fever and a sore throat.', '我发烧，喉咙痛。'], ['How long have you been feeling this way?', '你这样多久了？'], ['Since yesterday evening.', '从昨天晚上开始的。'], ['Let me check your temperature.', '让我量一下你的体温。'], ["It's 38.5 degrees. You have a cold.", '38.5度，你感冒了。'], ['Do I need any medicine?', '我需要吃药吗？'], ["Yes, I'll prescribe some medicine.", '是的，我会开一些药。'], ['How often should I take it?', '我应该多久吃一次？'], ['Three times a day after meals.', '每天三次，饭后服用。'], ['Should I stay in bed?', '我需要卧床休息吗？'], ['Yes, get plenty of rest and drink water.', '是的，多休息，多喝水。']],
    },
    {
        'title': 'Shopping for Clothes',
        'en': 'Tom: Good afternoon. Can I help you with something today?\nLucy: Yes, please. I am looking for a suit for a job interview.\nTom: We have some nice suits over here. What color do you prefer?\nLucy: I prefer dark blue or black.\nTom: How about this one? It is a dark blue suit, size M. It looks very professional.\nLucy: It looks nice. Can I try it on?\nTom: Of course. The fitting room is right over there.\nLucy: Thank you. ... How do I look?\nTom: It fits you very well! The style is very suitable for an interview.\nLucy: Great! I will take it. Do you have a white shirt to go with it?\nTom: Yes, we have several. What size do you wear?\nLucy: I wear size 40.\nTom: Here is a white shirt, size 40. And we have a red tie that goes well with it.\nLucy: The red tie is too bright. Do you have a dark blue one?\nTom: Let me check... Yes, here it is. The dark blue tie matches perfectly.\nLucy: Perfect! How much is everything together?\nTom: The suit is 680 yuan, the shirt is 180 yuan, and the tie is 90 yuan. That is 950 yuan in total.\nLucy: That is a bit expensive. Is there any discount?\nTom: We have a 20 percent discount today, so you will pay 760 yuan.\nLucy: That is much better. I will pay by credit card.\nTom: No problem. Please sign here. Thank you for shopping with us!\nLucy: Thank you for your help!',
        'zh': 'Tom: 下午好。有什么可以帮您的吗？\nLucy: 是的，我想买一套求职面试穿的西装。\nTom: 这边有几套不错的。请问您喜欢什么颜色？\nLucy: 深蓝色或黑色都可以。\nTom: 这套怎么样？深蓝色，M码，看起来非常职业。\nLucy: 看起来不错。我能试穿一下吗？\nTom: 当然可以。试衣间在那边。\nLucy: 谢谢。……看起来怎么样？\nTom: 非常合身！款式很适合面试。\nLucy: 太好了！就买这件了。你们有配套的白衬衫吗？\nTom: 有的，有好几款。您穿多大尺码？\nLucy: 40码。\nTom: 这件白衬衫，40码。还有一条红色领带很搭配。\nLucy: 红色太亮了。有没有深蓝色的？\nTom: 我找找……有的，在这里。深蓝色领带非常匹配。\nLucy: 完美！一共多少钱？\nTom: 西装680元，衬衫180元，领带90元。总共950元。\nLucy: 有点贵了。能打折吗？\nTom: 今天打八折，您只需付760元。\nLucy: 那好多了。我用信用卡付款。\nTom: 没问题。请在这里签字。谢谢光临！\nLucy: 谢谢你的帮助！',
        'grade': '八年级上册',
        'dialogue': [['Can I help you find anything?', '需要我帮你找什么吗？'], ["I'm looking for a winter coat.", '我想找一件冬季外套。'], ['What size do you wear?', '你穿什么尺码？'], ["I think I'm a medium.", '我想我是中号。'], ['Here are some coats in medium.', '这些是中号的外套。'], ['This one looks nice. Can I try it on?', '这件看起来不错，能试穿吗？'], ['Sure, the fitting room is over there.', '当然，试衣间在那边。'], ['How does it fit?', '合身吗？'], ["It's a bit tight in the shoulders.", '肩膀有点紧。'], ["Try this one. It's a larger size.", '试试这件，尺码大一点。'], ['This one is much better. How much is it?', '这件好多了，多少钱？'], ["It's on sale for two hundred yuan.", '打折后两百元。'], ["That's a good price. I'll take it.", '价格不错，我买了。'], ['Would you like to pay by cash or card?', '你用现金还是卡支付？'], ['Card, please. Thank you!', '刷卡，谢谢！']],
    },
    {
        'title': 'At the Restaurant',
        'en': 'Tom: Good evening. Welcome to Golden Dragon Restaurant. Do you have a reservation?\nLucy: Yes, under the name Wang.\nTom: Right this way, please. Here is your table.\nLucy: Thank you. Can we see the menu, please?\nTom: Of course. Here you are. Our special today is Beijing Roast Duck.\nLucy: That sounds delicious. Let me have a look at the menu first.\nTom: Take your time. I will come back to take your order.\nLucy: Thank you.\n... (a few minutes later) ...\nTom: Are you ready to order?\nLucy: Yes, we would like the Beijing Roast Duck, a plate of fried rice, and some vegetables.\nTom: Would you like soup or salad to start?\nLucy: A vegetable soup, please.\nTom: And to drink?\nLucy: A bottle of still water and one glass of orange juice, please.\nTom: Got it. Beijing Roast Duck, vegetable soup, fried rice, vegetables, still water, and orange juice.\nLucy: Yes, that is correct. Also, could we have some more tea?\nTom: Of course. I will bring it right away.\n... (after the meal) ...\nTom: How was everything?\nLucy: It was wonderful, thank you. Could we have the bill, please?\nTom: Sure. Here it is. That comes to 360 yuan.\nLucy: Here is 400 yuan. Keep the change.\nTom: Thank you very much! I hope you enjoyed your meal. Please come again!',
        'zh': 'Tom: 晚上好，欢迎光临金龙饭店。请问您有预约吗？\nLucy: 有的，姓王。\nTom: 请这边走。您的桌子在这边。\nLucy: 谢谢。我们可以看一下菜单吗？\nTom: 当然，给您。我们的今日推荐是北京烤鸭。\nLucy: 听起来很好吃。让我先看看菜单。\nTom: 您慢慢看，我一会儿来为您点餐。\nLucy: 谢谢。\n……（几分钟后）……\nTom: 请问准备好点餐了吗？\nLucy: 是的，我们想要北京烤鸭、一份炒饭和一些蔬菜。\nTom: 想要先来点汤或沙拉吗？\nLucy: 麻烦来一份蔬菜汤。\nTom: 饮料呢？\nLucy: 一瓶矿泉水和一杯橙汁，谢谢。\nTom: 好的。北京烤鸭、蔬菜汤、炒饭、蔬菜、矿泉水和橙汁。\nLucy: 对，没错。另外，可以再给我们添点茶吗？\nTom: 当然，我马上送来。\n……（用餐结束后）……\nTom: 请问菜品如何？\nLucy: 非常美味，谢谢。可以买单了吗？\nTom: 好的，这是账单。一共360元。\nLucy: 这是400元，不用找了。\nTom: 非常感谢！希望您用餐愉快。欢迎下次光临！',
        'grade': '八年级上册',
        'dialogue': [['Table for two, please.', '请安排一张两人桌。'], ['Smoking or non-smoking?', '吸烟区还是非吸烟区？'], ['Non-smoking, please.', '非吸烟区，谢谢。'], ["Follow me. Here's your table.", '跟我来，这是你们的桌子。'], ['Can I get you something to drink?', '你们想喝点什么？'], ["I'll have a glass of orange juice.", '我要一杯橙汁。'], ["And I'll have a cola, please.", '我要一杯可乐。'], ['Are you ready to order?', '你们准备好点餐了吗？'], ["Yes, I'd like the beef noodles.", '是的，我要牛肉面。'], ['And for you?', '你呢？'], ["I'll have the chicken rice.", '我要鸡肉饭。'], ['Would you like any side dishes?', '你们要配菜吗？'], ["No, thank you. That's all.", '不用了，谢谢，就这些。'], ['Enjoy your meal!', '请慢用！'], ['The food is delicious! Can we get the bill?', '食物很好吃！能给我们账单吗？'], ["Here you are. That'll be sixty yuan.", '给你们，一共六十元。']],
    },
    {
        'title': 'Travel Planning',
        'en': 'Tom: Summer vacation is coming soon. Have you made any plans?\nLucy: I am thinking about going to Shanghai. Have you ever been there?\nTom: Yes, I went there two years ago. It is a modern and exciting city.\nLucy: Really? What places did you visit?\nTom: I visited the Bund, Nanjing Road, the Oriental Pearl Tower, and Yuyuan Garden. They were all amazing.\nLucy: That sounds great! How long should I stay there?\nTom: I think four or five days is enough to see the main attractions.\nLucy: Do you know a good hotel near the Bund?\nTom: There is a nice hotel called Park Hyatt. It is close to the river and the service is excellent.\nLucy: How much does it cost per night?\nTom: Around 800 yuan per night for a standard room. But if you book online early, you can get a discount.\nLucy: Good idea. Should I book the hotel first or buy the train tickets first?\nTom: I think you should buy the train tickets first, because they sell out quickly during holidays.\nLucy: You are right. Which train should I take?\nTom: The high-speed train is the fastest. It only takes about five hours from here to Shanghai.\nLucy: Perfect! I will start planning it this weekend.\nTom: Have a great trip! And do not forget to try the local food in Shanghai.\nLucy: I definitely will. Thank you for all the advice!',
        'zh': 'Tom: 暑假快到了，你有什么计划吗？\nLucy: 我想去上海。你去过那里吗？\nTom: 去过，两年前去的。那是一座现代化又迷人的城市。\nLucy: 真的吗？你去了哪些地方？\nTom: 我去了外滩、南京路、东方明珠塔和豫园。都非常棒。\nLucy: 听起来太棒了！我应该在那里待几天？\nTom: 我觉得四五天足够看完主要景点了。\nLucy: 你知道外滩附近有什么好酒店吗？\nTom: 有个叫柏悦的酒店很不错，靠近黄浦江，服务也很好。\nLucy: 每晚多少钱？\nTom: 标准间大约800元一晚。但如果提前网上预订，可以打折。\nLucy: 好主意。我是先订酒店还是先买车票？\nTom: 我觉得应该先买车票，因为节假日车票卖得很快。\nLucy: 你说得对。我应该坐什么车？\nTom: 高铁最快，从这里到上海只要五个小时左右。\nLucy: 太好了！我这周末就开始计划。\nTom: 祝你旅途愉快！别忘了尝尝上海的本地美食。\nLucy: 一定会的！谢谢你的建议！',
        'grade': '八年级上册',
        'dialogue': [['Where should we go for the holiday?', '假期我们应该去哪里？'], ['How about Sanya? The beach is beautiful.', '三亚怎么样？海滩很美。'], ['That sounds great! When should we go?', '听起来很棒！我们什么时候去？'], ['How about next Saturday?', '下周六怎么样？'], ['Perfect. Should we book a hotel?', '完美，我们需要订酒店吗？'], ["Yes, I'll look for a nice hotel online.", '是的，我会在网上找一家好的酒店。'], ['What about the flight?', '机票怎么办？'], ['I can book the tickets this afternoon.', '我今天下午可以订票。'], ['How long should we stay?', '我们应该待多久？'], ['Five days would be good.', '五天应该不错。'], ['What should we pack?', '我们应该带什么？'], ['Sunscreen, swimsuits, and casual clothes.', '防晒霜、泳衣和休闲衣服。'], ['Should I bring a camera?', '我应该带相机吗？'], ["Definitely! We'll want photos.", '当然！我们会想要拍照的。'], ["I can't wait! This will be amazing.", '我等不及了！这将会很棒。']],
    },
    {
        'title': 'At the Hotel',
        'en': 'Tom: Good evening. Welcome to Sunshine Hotel. How can I help you?\nLucy: Good evening. I have a reservation. My name is Zhang Wei.\nTom: Let me check... Yes, Mr. Zhang. You have booked a double room for three nights.\nLucy: That is correct.\nTom: Could you please show me your ID?\nLucy: Here you are.\nTom: Thank you. Your room number is 508 on the fifth floor. Here is your key card.\nLucy: Thank you. What time is breakfast?\nTom: Breakfast is served from 7 AM to 10 AM in the restaurant on the second floor.\nLucy: Does the room have free Wi-Fi?\nTom: Yes, it does. The password is on the card beside your bed.\nLucy: Great. Is there a gym in the hotel?\nTom: Yes, the gym is on the first floor and it is open 24 hours.\nLucy: Wonderful. And could you wake me up at 7 o clock tomorrow morning?\nTom: Of course. What way would you prefer, by phone or by knocking on the door?\nLucy: By phone, please.\nTom: No problem. Is there anything else you need?\nLucy: Could I have an extra towel, please?\nTom: Sure, I will send someone to bring one to your room right away.\nLucy: Thank you very much.\nTom: You are welcome. Enjoy your stay!',
        'zh': 'Tom: 晚上好，欢迎光临阳光酒店。有什么可以帮您的？\nLucy: 晚上好，我预约了房间。我姓张，名伟。\nTom: 让我查一下……是的，张先生。您预订了一间双人间，住三晚。\nLucy: 没错。\nTom: 请出示一下您的身份证好吗？\nLucy: 给您。\nTom: 谢谢。您的房间是五楼508室。这是您的房卡。\nLucy: 谢谢。早餐几点供应？\nTom: 早餐早上7点到10点，在二楼餐厅供应。\nLucy: 房间里有免费Wi-Fi吗？\nTom: 有的，密码在您床边那张卡片上。\nLucy: 太好了。酒店有健身房吗？\nTom: 有的，健身房在一楼，24小时开放。\nLucy: 太棒了。另外，能在明天早上7点叫醒我吗？\nTom: 当然可以。您希望用什么方式叫您，电话还是敲门？\nLucy: 电话吧。\nTom: 没问题。还有什么需要吗？\nLucy: 能再加一条毛巾吗？\nTom: 好的，我马上派人送到您房间。\nLucy: 非常感谢。\nTom: 不客气，祝您入住愉快！',
        'grade': '八年级上册',
        'dialogue': [['Good evening. I have a reservation.', '晚上好，我有预订。'], ['Under what name, please?', '请问以什么名字预订的？'], ['Zhang Wei. I booked online.', '张伟，我在网上预订的。'], ['Let me check... Yes, here it is.', '让我查一下……是的，找到了。'], ["You're in room 1208. Here's your key card.", '你在1208号房间，这是你的房卡。'], ['Is breakfast included?', '包含早餐吗？'], ['Yes, breakfast is served from 7 to 10.', '是的，早餐供应时间是7点到10点。'], ['Great. Where is the elevator?', '太好了，电梯在哪里？'], ["It's just around the corner.", '就在拐角处。'], ['Excuse me, where is the gym?', '打扰一下，健身房在哪里？'], ['The gym is on the third floor.', '健身房在三楼。'], ['What time does it close?', '什么时候关门？'], ["It's open until 10 PM.", '开放到晚上10点。'], ['Can I get room service?', '我可以要客房服务吗？'], ['Yes, just dial 0 from your room.', '可以，从房间拨0就行。']],
    },
    {
        'title': 'School Life',
        'en': 'Tom: Hi, Tom! Have you finished the English homework?\nLucy: Not yet. I was working on the math problems until late last night.\nTom: The math homework is also due today! I forgot all about it.\nLucy: Oh no! We should finish it during lunch break.\nTom: Good idea. By the way, are you going to the school talent show next Friday?\nLucy: Yes, I signed up for it. I will play the piano.\nTom: That is so cool! I also want to join, but I do not have any special skills.\nLucy: You could sing a song or tell a joke. Everyone has something to share.\nTom: Maybe I will just watch this year and prepare something for next year.\nLucy: That is fine too. Have you decided which club to join this term?\nTom: I am thinking about joining the science club. What about you?\nLucy: I want to join the basketball team. I heard the coach is very strict but very good.\nTom: The coach is really good. My brother was on the team last year and he learned a lot.\nLucy: That is great! Oh, it is almost time for class. See you at lunch.\nTom: See you! Do not forget to bring your homework!\nLucy: I will not! Bye!',
        'zh': 'Tom: 嗨，汤姆！你的英语作业做完了吗？\nLucy: 还没呢。我昨晚一直在做数学题，做到很晚。\nTom: 数学作业今天也要交啊！我全忘了。\nLucy: 糟糕！我们午休时应该把它做完。\nTom: 好主意。对了，下周五的学校才艺表演你去吗？\nLucy: 去啊，我报名了。我要弹钢琴。\nTom: 太酷了！我也想参加，但我没有什么特长。\nLucy: 你可以唱首歌或讲个笑话。每个人都有自己的闪光点。\nTom: 也许我今年先观看，明年再准备一个节目。\nLucy: 那也好。你决定这学期参加什么社团了吗？\nTom: 我想参加科学社。你呢？\nLucy: 我想加入篮球队。听说教练很严格但很厉害。\nTom: 教练真的很棒。我哥哥去年在队里，学到了很多东西。\nLucy: 太棒了！哦，快上课了。午餐时见。\nTom: 见！别忘了带作业！\nLucy: 不会忘的！再见！',
        'grade': '八年级上册',
        'dialogue': [['How was your first day at school?', '你上学第一天怎么样？'], ['It was good! I like my new classmates.', '很好！我喜欢我的新同学。'], ["What's your favorite subject?", '你最喜欢的科目是什么？'], ['I love English and P.E.', '我喜欢英语和体育。'], ['Who is your English teacher?', '你的英语老师是谁？'], ["Mr. Brown. He's from America.", '布朗先生，他来自美国。'], ["That's cool! Is he strict?", '太酷了！他严格吗？'], ['Not really. He makes learning fun.', '不严格，他让学习变得有趣。'], ['What clubs are you in?', '你参加了什么社团？'], ['I joined the basketball team.', '我加入了篮球队。'], ['When do you practice?', '你们什么时候训练？'], ['Every Tuesday and Thursday after school.', '每周二和周四放学后。'], ['That sounds like a lot of fun.', '听起来很有趣。'], ['It is! You should join too.', '是的！你也应该加入。'], ['Maybe I will! See you tomorrow.', '也许我会！明天见。']],
    },
    {
        'title': 'Hobbies and Interests',
        'en': 'Tom: Hi, Lily! What do you like to do in your free time?\nLucy: I love painting. I take art classes every Saturday.\nTom: That sounds fun! What kind of paintings do you like to do?\nLucy: I mostly do oil paintings. I think the colors are richer and more expressive.\nTom: I wish I could paint. I only know how to draw stick figures.\nLucy: Everyone starts somewhere. You should try it. It is very relaxing.\nTom: What about you? Do you have any other hobbies?\nLucy: Yes, I also enjoy reading novels and playing the guitar.\nTom: You can play the guitar? That is impressive!\nLucy: Well, I am still learning. I have been taking lessons for about six months.\nTom: That is great progress! I want to pick up a hobby too, but I do not know where to start.\nLucy: What do you enjoy doing most?\nTom: I like listening to music and watching movies.\nLucy: Have you thought about learning a musical instrument? Music and movies are related to art.\nTom: That is a good idea. Maybe I can start with the ukulele. It looks easy to learn.\nLucy: Yes, it is! And it is not expensive. You should get one and learn some basic chords.\nTom: I will think about it. Thanks for the advice, Lily.\nLucy: You are welcome. We can paint and play music together sometime!\nTom: That would be amazing!',
        'zh': 'Tom: 嗨，莉莉！你空闲时间喜欢做什么？\nLucy: 我喜欢画画。每个周六都上美术课。\nTom: 听起来很有趣！你喜欢画什么样的画？\nLucy: 我主要画油画。我觉得油画的色彩更丰富、更有表现力。\nTom: 我真希望我也会画画。我只会画火柴人。\nLucy: 每个人都是从头开始的。你应该试试，画画很放松。\nTom: 你呢？还有其他爱好吗？\nLucy: 有啊，我还喜欢看小说和弹吉他。\nTom: 你会弹吉他？太厉害了！\nLucy: 嗯，我还在学。上了大概六个月的课了。\nTom: 进步很大啊！我也想培养一个爱好，但不知道从哪里开始。\nLucy: 你最喜欢做什么？\nTom: 我喜欢听音乐和看电影。\nLucy: 有没有想过学一种乐器？音乐和电影都与艺术有关。\nTom: 好主意。也许我可以先从尤克里里开始，看起来比较容易学。\nLucy: 是啊！而且不贵。你可以买一把，学一些基础和弦。\nTom: 我考虑一下。谢谢你的建议，莉莉。\nLucy: 不客气。以后我们可以一起画画、一起弹音乐！\nTom: 那太好了！',
        'grade': '八年级上册',
        'dialogue': [['What do you like to do in your free time?', '你空闲时间喜欢做什么？'], ['I enjoy reading and playing guitar.', '我喜欢阅读和弹吉他。'], ["That's interesting! What kind of books?", '真有趣！你喜欢什么类型的书？'], ['I love science fiction and history.', '我喜欢科幻小说和历史书。'], ['How long have you played guitar?', '你弹吉他多久了？'], ["About three years. I'm still learning.", '大约三年了，我还在学习。'], ['Do you play any sports?', '你做运动吗？'], ['Yes, I play badminton every weekend.', '是的，我每个周末都打羽毛球。'], ['Who do you play with?', '你和谁一起打？'], ["My sister. She's really good!", '我姐姐，她打得很好！'], ['Do you like watching movies?', '你喜欢看电影吗？'], ['Yes! My favorite genre is comedy.', '喜欢！我最喜欢的类型是喜剧。'], ["Who's your favorite actor?", '你最喜欢的演员是谁？'], ['I love Jackie Chan. His movies are funny.', '我喜欢成龙，他的电影很搞笑。'], ['We should watch a movie together sometime!', '我们应该找个时间一起看电影！']],
    },
    {
        'title': 'Environmental Protection',
        'en': 'Tom: Hi, Jack! I saw you carrying a reusable water bottle. That is a great habit!\nLucy: Thank you! I think it is important to reduce plastic waste. Every year, millions of plastic bottles end up in the ocean.\nTom: You are right. The ocean pollution is getting worse. What else can we do to protect the environment?\nLucy: We can use less electricity, take public transportation, and recycle whenever possible.\nTom: I usually ride my bike to school. It is good for both health and the environment.\nLucy: That is awesome! I should start doing that too.\nTom: And we can plant more trees. Trees clean the air and provide homes for animals.\nLucy: Our school is organizing a tree-planting activity next month. Will you join?\nTom: Yes, I will! Count me in. Where will the trees be planted?\nLucy: In the park near our school. The local government is supporting this activity.\nTom: That is wonderful. I will tell my parents and ask them to join as well.\nLucy: Great idea! The more people, the better. We should also save water.\nTom: Definitely. I always turn off the tap while brushing my teeth.\nLucy: Small actions make a big difference. If everyone does a little, it adds up to a lot.\nTom: Absolutely. Let us do our best to protect our planet!\nLucy: Yes! This is the only Earth we have. Let us take care of it together.',
        'zh': 'Tom: 嗨，杰克！我看到你带了一个可重复使用的水壶。这个习惯真棒！\nLucy: 谢谢！我觉得减少塑料垃圾很重要。每年有数百万个塑料瓶流入海洋。\nTom: 你说得对。海洋污染越来越严重了。我们还能做什么来保护环境？\nLucy: 我们可以少用电、乘公共交通出行、尽可能回收利用。\nTom: 我通常骑自行车上学。这样对健康和环境都有好处。\nLucy: 太棒了！我也应该开始骑自行车了。\nTom: 我们还可以种更多的树。树木净化空气，为动物提供家园。\nLucy: 我们学校下个月要组织一次植树活动，你要参加吗？\nTom: 好的，算我一个！种在哪里？\nLucy: 在我们学校附近的公园。当地政府支持这个活动。\nTom: 太棒了。我告诉父母，让他们也参加。\nLucy: 好主意！人越多越好。我们还应该节约用水。\nTom: 没错。我刷牙时总是关掉水龙头。\nLucy: 小行动带来大改变。如果每个人做一点，汇集起来就很可观了。\nTom: 说得好。让我们尽力保护地球！\nLucy: 是的！地球是我们唯一的家，让我们一起保护它。',
        'grade': '八年级上册',
        'dialogue': [['Have you heard about the new recycling policy?', '你听说了新的回收政策吗？'], ['Yes, it started this month.', '听说了，这个月开始实施的。'], ['Do you separate your trash at home?', '你在家里垃圾分类吗？'], ['Of course! We have four bins.', '当然！我们有四个垃圾桶。'], ["That's great. What can we recycle?", '太好了，什么可以回收？'], ['Paper, plastic, glass, and metal.', '纸张、塑料、玻璃和金属。'], ['What about food waste?', '食物垃圾呢？'], ['That goes in the wet waste bin.', '食物垃圾放在湿垃圾桶里。'], ['Should we stop using plastic bags?', '我们应该停止使用塑料袋吗？'], ['Yes, we should use reusable bags.', '是的，我们应该用可重复使用的袋子。'], ['What else can we do to help the environment?', '我们还能做什么来保护环境？'], ['Walk or bike instead of driving.', '走路或骑自行车而不是开车。'], ['That makes sense. Save energy too?', '有道理，还要节约能源？'], ['Yes, turn off lights when you leave.', '是的，离开时关灯。'], ['Small actions make a big difference!', '小小的行动能带来大改变！']],
    },
    {
        'title': 'Future Plans',
        'en': 'Tom: Tom, what do you want to be when you grow up?\nLucy: I want to be a computer programmer. I love coding and solving problems with technology.\nTom: That is a popular career these days. Have you been learning programming?\nLucy: Yes, I have been teaching myself Python for about a year. I also joined the coding club at school.\nTom: That sounds very serious. What kind of programs do you want to create?\nLucy: I want to develop apps that help people learn languages. I think technology can make education more accessible.\nTom: That is a meaningful goal! Do you plan to go to university?\nLucy: Yes, I want to study computer science at a good university. Maybe Tsinghua or Peking University.\nTom: Those are great schools. They have excellent computer science programs.\nLucy: I know. I need to work very hard to get in. What about you? What are your future plans?\nTom: I want to become a veterinarian. I love animals and I want to help them.\nLucy: That is wonderful! Where do you plan to study?\nTom: I want to study at an agricultural university. They have good veterinary programs.\nLucy: I am sure you will do great. We both have clear goals now.\nTom: Yes! We should study hard and never give up on our dreams.\nLucy: Absolutely. Let us support each other and work hard together!\nTom: Deal! Good luck to both of us!\nLucy: Good luck!',
        'zh': 'Tom: 汤姆，你长大后想做什么？\nLucy: 我想当一名程序员。我喜欢编程，喜欢用技术解决问题。\nTom: 这是最近很热门的职业。你一直在学编程吗？\nLucy: 是的，我自学Python大概一年了。我还参加了学校的编程社团。\nTom: 听起来很认真啊。你想开发什么样的程序？\nLucy: 我想开发帮助人们学习语言的应用程序。我觉得科技可以让教育更加普及。\nTom: 这是很有意义的目标！你打算上大学吗？\nLucy: 是的，我想上一所好大学的计算机专业。可能是清华或北大。\nTom: 那些都是很好的学校，计算机专业很棒。\nLucy: 我知道。我需要非常努力才能考进去。你呢？你有什么未来计划？\nTom: 我想当一名兽医。我喜欢动物，我想帮助它们。\nLucy: 太棒了！你打算在哪里学习？\nTom: 我想上一所农业大学，那里有很好的兽医专业。\nLucy: 我相信你一定能做到。我们现在都有明确的目标了。\nTom: 是的！我们应该努力学习，永不放弃梦想。\nLucy: 没错！让我们互相支持，一起努力！\nTom: 一言为定！祝我们两个都好运！\nLucy: 好运！',
        'grade': '八年级上册',
        'dialogue': [['What do you want to be in the future?', '你将来想做什么？'], ['I want to be a doctor.', '我想成为一名医生。'], ["That's amazing! Why do you want that?", '太棒了！为什么想当医生？'], ['I want to help sick people.', '我想帮助生病的人。'], ['Do you need to study medicine?', '你需要学医吗？'], ['Yes, it takes many years of study.', '是的，需要学习很多年。'], ['Where do you want to work?', '你想在哪里工作？'], ['Maybe in a hospital in Beijing.', '也许在北京的一家医院。'], ['What about your friend Li Ming?', '你的朋友李明呢？'], ['He wants to be a computer programmer.', '他想成为计算机程序员。'], ["That's a growing field.", '那是一个不断发展的领域。'], ['Yes, technology is the future.', '是的，科技就是未来。'], ["Do you think you'll achieve your dream?", '你认为你会实现梦想吗？'], ["I hope so! I'll work hard.", '希望如此！我会努力的。'], ["I'm sure you will. Good luck!", '我相信你会的，祝你好运！']],
    },
    {
        'title': 'Shopping in the Supermarket 超市购物',
        'en': 'Tom: Can I help you?\nLucy: Yes, I want to buy some vegetables.\nTom: What kind do you like?\nLucy: I like tomatoes and potatoes.\nTom: Here you are.\nLucy: How much are they?\nTom: Thirty yuan in total.\nLucy: Here is the money.\nTom: Thank you. Have a nice day!\nLucy: You too!',
        'zh': 'Tom: 需要帮忙吗？\nLucy: 是的，我想买一些蔬菜。\nTom: 你喜欢哪种？\nLucy: 我喜欢西红柿和土豆。\nTom: 给你。\nLucy: 多少钱？\nTom: 一共30元。\nLucy: 给你钱。\nTom: 谢谢。祝你愉快！\nLucy: 你也是！',
        'grade': '八年级上册',
        'dialogue': [['Can I help you?', '需要帮忙吗？'], ['Yes, I want to buy some vegetables.', '是的，我想买一些蔬菜。'], ['What kind do you like?', '你喜欢哪种？'], ['I like tomatoes and potatoes.', '我喜欢西红柿和土豆。'], ['Here you are.', '给你。'], ['How much are they?', '多少钱？'], ['Thirty yuan in total.', '一共30元。'], ['Here is the money.', '给你钱。'], ['Thank you. Have a nice day!', '谢谢。祝你愉快！'], ['You too!', '你也是！']],
    },
    {
        'title': 'At the Railway Station 火车站',
        'en': 'Tom: Excuse me, where is the ticket office?\nLucy: It is over there, near the entrance.\nTom: Thank you. By the way, when does the train leave?\nLucy: At 3:30 p.m.\nTom: Which platform is it?\nLucy: Platform 5.\nTom: Thank you very much.\nLucy: You are welcome. Have a good trip!\nTom: Thanks!',
        'zh': 'Tom: 打扰一下，售票处在哪里？\nLucy: 在那边，入口附近。\nTom: 谢谢。顺便问一下，火车什么时候开？\nLucy: 下午3:30。\nTom: 几号站台？\nLucy: 5号站台。\nTom: 非常感谢。\nLucy: 不客气。旅途愉快！\nTom: 谢谢！',
        'grade': '八年级上册',
        'dialogue': [['Excuse me, where is the ticket office?', '打扰一下，售票处在哪里？'], ['It is over there, near the entrance.', '在那边，入口附近。'], ['Thank you. By the way, when does the train leave?', '谢谢。顺便问一下，火车什么时候开？'], ['At 3:30 p.m.', '下午3:30。'], ['Which platform is it?', '几号站台？'], ['Platform 5.', '5号站台。'], ['Thank you very much.', '非常感谢。'], ['You are welcome. Have a good trip!', '不客气。旅途愉快！'], ['Thanks!', '谢谢！']],
    },
    {
        'title': 'Seeing the Doctor 看医生',
        'en': 'Tom: What is wrong with you?\nLucy: I have a fever and a headache.\nTom: How long have you been like this?\nLucy: Since yesterday evening.\nTom: Let me check your temperature.\nLucy: Is it serious?\nTom: No, just a cold. Take this medicine and drink more water.\nLucy: Thank you, doctor.\nTom: Have a good rest.',
        'zh': 'Tom: 你怎么了？\nLucy: 我发烧并且头痛。\nTom: 这样多久了？\nLucy: 从昨天晚上开始的。\nTom: 让我量一下体温。\nLucy: 严重吗？\nTom: 不严重，只是感冒。吃这个药，多喝热水。\nLucy: 谢谢你，医生。\nTom: 好好休息。',
        'grade': '八年级上册',
        'dialogue': [['What is wrong with you?', '你怎么了？'], ['I have a fever and a headache.', '我发烧并且头痛。'], ['How long have you been like this?', '这样多久了？'], ['Since yesterday evening.', '从昨天晚上开始的。'], ['Let me check your temperature.', '让我量一下体温。'], ['Is it serious?', '严重吗？'], ['No, just a cold. Take this medicine and drink more water.', '不严重，只是感冒。吃这个药，多喝热水。'], ['Thank you, doctor.', '谢谢你，医生。'], ['Have a good rest.', '好好休息。']],
    },
    {
        'title': 'Weather Report 天气预报',
        'en': 'Tom: What is the weather like today?\nLucy: It is sunny and warm.\nTom: What about tomorrow?\nLucy: It will be cloudy and cool.\nTom: Will it rain?\nLucy: I think so. You should take an umbrella.\nTom: Good idea. I hope it will not rain heavily.\nLucy: The weather report says it will be light rain.\nTom: That is great!',
        'zh': 'Tom: 今天天气怎么样？\nLucy: 晴朗且温暖。\nTom: 明天呢？\nLucy: 多云且凉爽。\nTom: 会下雨吗？\nLucy: 我想会的。你应该带把伞。\nTom: 好主意。希望不要下大雨。\nLucy: 天气预报说是小雨。\nTom: 太好了！',
        'grade': '八年级上册',
        'dialogue': [['What is the weather like today?', '今天天气怎么样？'], ['It is sunny and warm.', '晴朗且温暖。'], ['What about tomorrow?', '明天呢？'], ['It will be cloudy and cool.', '多云且凉爽。'], ['Will it rain?', '会下雨吗？'], ['I think so. You should take an umbrella.', '我想会的。你应该带把伞。'], ['Good idea. I hope it will not rain heavily.', '好主意。希望不要下大雨。'], ['The weather report says it will be light rain.', '天气预报说是小雨。'], ['That is great!', '太好了！']],
    },
    {
        'title': 'Part-time Job Interview 兼职面试',
        'en': 'Tom: Why do you want this job?\nLucy: I want to gain some work experience.\nTom: Have you worked before?\nLucy: No, but I am a quick learner.\nTom: What is your schedule like?\nLucy: I am free on weekends and after school.\nTom: How old are you?\nLucy: I am 16 years old.\nTom: OK. We will call you next week.\nLucy: Thank you very much.',
        'zh': 'Tom: 你为什么想要这份工作？\nLucy: 我想获得一些工作经验。\nTom: 你以前工作过吗？\nLucy: 没有，但我学东西很快。\nTom: 你的时间安排怎么样？\nLucy: 周末和放学后有空。\nTom: 你多大了？\nLucy: 我16岁。\nTom: 好的。我们下周会打电话给你。\nLucy: 非常感谢。',
        'grade': '八年级上册',
        'dialogue': [['Why do you want this job?', '你为什么想要这份工作？'], ['I want to gain some work experience.', '我想获得一些工作经验。'], ['Have you worked before?', '你以前工作过吗？'], ['No, but I am a quick learner.', '没有，但我学东西很快。'], ['What is your schedule like?', '你的时间安排怎么样？'], ['I am free on weekends and after school.', '周末和放学后有空。'], ['How old are you?', '你多大了？'], ['I am 16 years old.', '我16岁。'], ['OK. We will call you next week.', '好的。我们下周会打电话给你。'], ['Thank you very much.', '非常感谢。']],
    },
    {
        'title': 'Sports Meeting 运动会',
        'en': 'Tom: Did you take part in the sports meeting?\nLucy: Yes, I took part in the 100-meter race.\nTom: Did you win?\nLucy: No, I came in third.\nTom: That is still very good!\nLucy: Thank you. What about you?\nTom: I took part in the long jump.\nLucy: Did you win a prize?\nTom: Yes, I won first prize!\nLucy: Congratulations!',
        'zh': 'Tom: 你参加运动会了吗？\nLucy: 是的，我参加了100米赛跑。\nTom: 你赢了吗？\nLucy: 没有，我得了第三名。\nTom: 那也已经很好了！\nLucy: 谢谢。你呢？\nTom: 我参加了跳远。\nLucy: 你得奖了吗？\nTom: 是的，我得了一等奖！\nLucy: 恭喜！',
        'grade': '八年级下册',
        'dialogue': [['Did you take part in the sports meeting?', '你参加运动会了吗？'], ['Yes, I took part in the 100-meter race.', '是的，我参加了100米赛跑。'], ['Did you win?', '你赢了吗？'], ['No, I came in third.', '没有，我得了第三名。'], ['That is still very good!', '那也已经很好了！'], ['Thank you. What about you?', '谢谢。你呢？'], ['I took part in the long jump.', '我参加了跳远。'], ['Did you win a prize?', '你得奖了吗？'], ['Yes, I won first prize!', '是的，我得了一等奖！'], ['Congratulations!', '恭喜！']],
    },
    {
        'title': 'Library Rules 图书馆规则',
        'en': 'Tom: Can I borrow these books?\nLucy: Yes, but you must return them in two weeks.\nTom: Can I renew them?\nLucy: Yes, you can renew them online.\nTom: Is there a fine for late returns?\nLucy: Yes, one yuan per day.\nTom: I see. Can I take photos here?\nLucy: No, photos are not allowed.\nTom: OK, I will obey the rules.\nLucy: Thank you for your cooperation.',
        'zh': 'Tom: 我可以借这些书吗？\nLucy: 可以，但你必须在两周内归还。\nTom: 我可以续借吗？\nLucy: 可以，你可以在网上续借。\nTom: 晚还书有罚款吗？\nLucy: 有，每天一元。\nTom: 我明白了。我可以在这里拍照吗？\nLucy: 不可以，不允许拍照。\nTom: 好的，我会遵守规定。\nLucy: 谢谢你的配合。',
        'grade': '八年级下册',
        'dialogue': [['Can I borrow these books?', '我可以借这些书吗？'], ['Yes, but you must return them in two weeks.', '可以，但你必须在两周内归还。'], ['Can I renew them?', '我可以续借吗？'], ['Yes, you can renew them online.', '可以，你可以在网上续借。'], ['Is there a fine for late returns?', '晚还书有罚款吗？'], ['Yes, one yuan per day.', '有，每天一元。'], ['I see. Can I take photos here?', '我明白了。我可以在这里拍照吗？'], ['No, photos are not allowed.', '不可以，不允许拍照。'], ['OK, I will obey the rules.', '好的，我会遵守规定。'], ['Thank you for your cooperation.', '谢谢你的配合。']],
    },
    {
        'title': 'Festival Celebration 节日庆祝',
        'en': 'Tom: What is your favorite festival?\nLucy: My favorite festival is the Spring Festival.\nTom: Why do you like it?\nLucy: Because I can get red packets and eat delicious food.\nTom: What do you usually do?\nLucy: We have a big family dinner and watch TV together.\nTom: That sounds wonderful!\nLucy: Welcome to my home this Spring Festival!\nTom: Thank you! I would love to.',
        'zh': 'Tom: 你最喜欢什么节日？\nLucy: 我最喜欢春节。\nTom: 你为什么喜欢它？\nLucy: 因为我可以收到红包，还能吃到美味的食物。\nTom: 你们通常做什么？\nLucy: 我们吃一顿丰盛的家庭晚餐，一起看电视。\nTom: 听起来太棒了！\nLucy: 今年春节欢迎来我家！\nTom: 谢谢！我很乐意。',
        'grade': '八年级下册',
        'dialogue': [['What is your favorite festival?', '你最喜欢什么节日？'], ['My favorite festival is the Spring Festival.', '我最喜欢春节。'], ['Why do you like it?', '你为什么喜欢它？'], ['Because I can get red packets and eat delicious food.', '因为我可以收到红包，还能吃到美味的食物。'], ['What do you usually do?', '你们通常做什么？'], ['We have a big family dinner and watch TV together.', '我们吃一顿丰盛的家庭晚餐，一起看电视。'], ['That sounds wonderful!', '听起来太棒了！'], ['Welcome to my home this Spring Festival!', '今年春节欢迎来我家！'], ['Thank you! I would love to.', '谢谢！我很乐意。']],
    },
    {
        'title': 'Internet Safety 网络安全',
        'en': 'Tom: Do you often go online?\nLucy: Yes, I use the Internet every day.\nTom: What do you usually do online?\nLucy: I chat with friends and search for information.\nTom: Do you know about internet safety?\nLucy: Not really. What should I pay attention to?\nTom: Do not give out personal information.\nLucy: I see. Anything else?\nTom: Do not meet online friends alone.\nLucy: Thank you for telling me.',
        'zh': 'Tom: 你经常上网吗？\nLucy: 是的，我每天都上网。\nTom: 你通常在上网做什么？\nLucy: 我和朋友聊天，搜索信息。\nTom: 你知道网络安全吗？\nLucy: 不太清楚。我应该注意什么？\nTom: 不要泄露个人信息。\nLucy: 我明白了。还有其他的吗？\nTom: 不要单独见网友。\nLucy: 谢谢你告诉我。',
        'grade': '八年级下册',
        'dialogue': [['Do you often go online?', '你经常上网吗？'], ['Yes, I use the Internet every day.', '是的，我每天都上网。'], ['What do you usually do online?', '你通常在上网做什么？'], ['I chat with friends and search for information.', '我和朋友聊天，搜索信息。'], ['Do you know about internet safety?', '你知道网络安全吗？'], ['Not really. What should I pay attention to?', '不太清楚。我应该注意什么？'], ['Do not give out personal information.', '不要泄露个人信息。'], ['I see. Anything else?', '我明白了。还有其他的吗？'], ['Do not meet online friends alone.', '不要单独见网友。'], ['Thank you for telling me.', '谢谢你告诉我。']],
    },
    {
        'title': 'Volunteer Work 志愿者工作',
        'en': 'Tom: What did you do last weekend?\nLucy: I did volunteer work at the old peoples home.\nTom: What did you do there?\nLucy: I cleaned the rooms and talked with the old people.\nTom: That is so nice of you!\nLucy: Thank you. It made me very happy.\nTom: I want to join you next time.\nLucy: Great! We go there every month.\nTom: I will contact you then.',
        'zh': 'Tom: 上周末你做了什么？\nLucy: 我在养老院做了志愿者工作。\nTom: 你在那里做了什么？\nLucy: 我打扫房间，和老人们聊天。\nTom: 你真是太好了！\nLucy: 谢谢。这让我非常开心。\nTom: 下次我想加入你们。\nLucy: 太好了！我们每个月都去。\nTom: 到时候我会联系你。',
        'grade': '八年级下册',
        'dialogue': [['What did you do last weekend?', '上周末你做了什么？'], ['I did volunteer work at the old peoples home.', '我在养老院做了志愿者工作。'], ['What did you do there?', '你在那里做了什么？'], ['I cleaned the rooms and talked with the old people.', '我打扫房间，和老人们聊天。'], ['That is so nice of you!', '你真是太好了！'], ['Thank you. It made me very happy.', '谢谢。这让我非常开心。'], ['I want to join you next time.', '下次我想加入你们。'], ['Great! We go there every month.', '太好了！我们每个月都去。'], ['I will contact you then.', '到时候我会联系你。']],
    },
    {
        'title': 'Shopping in the Supermarket',
        'en': 'Tom: Can I help you?\nLucy: Yes, I want to buy some vegetables.\nTom: What kind do you like?\nLucy: I like tomatoes and potatoes.\nTom: Here you are.\nLucy: How much are they?\nTom: Thirty yuan in total.\nLucy: Here is the money.\nTom: Thank you. Have a nice day!\nLucy: You too!',
        'zh': 'Tom: 需要帮忙吗？\nLucy: 是的，我想买一些蔬菜。\nTom: 你喜欢哪种？\nLucy: 我喜欢西红柿和土豆。\nTom: 给你。\nLucy: 多少钱？\nTom: 一共30元。\nLucy: 给你钱。\nTom: 谢谢。祝你愉快！\nLucy: 你也是！',
        'grade': '八年级下册',
        'dialogue': [['Can I help you?', '需要帮忙吗？'], ['Yes, I want to buy some vegetables.', '是的，我想买一些蔬菜。'], ['What kind do you like?', '你喜欢哪种？'], ['I like tomatoes and potatoes.', '我喜欢西红柿和土豆。'], ['Here you are.', '给你。'], ['How much are they?', '多少钱？'], ['Thirty yuan in total.', '一共30元。'], ['Here is the money.', '给你钱。'], ['Thank you. Have a nice day!', '谢谢。祝你愉快！'], ['You too!', '你也是！']],
    },
    {
        'title': 'At the Railway Station',
        'en': 'Tom: Excuse me, where is the ticket office?\nLucy: It is over there, near the entrance.\nTom: Thank you. By the way, when does the train leave?\nLucy: At 3:30 p.m.\nTom: Which platform is it?\nLucy: Platform 5.\nTom: Thank you very much.\nLucy: You are welcome. Have a good trip!\nTom: Thanks!',
        'zh': 'Tom: 打扰一下，售票处在哪里？\nLucy: 在那边，入口附近。\nTom: 谢谢。顺便问一下，火车什么时候开？\nLucy: 下午3:30。\nTom: 几号站台？\nLucy: 5号站台。\nTom: 非常感谢。\nLucy: 不客气。旅途愉快！\nTom: 谢谢！',
        'grade': '八年级下册',
        'dialogue': [['Excuse me, where is the ticket office?', '打扰一下，售票处在哪里？'], ['It is over there, near the entrance.', '在那边，入口附近。'], ['Thank you. By the way, when does the train leave?', '谢谢。顺便问一下，火车什么时候开？'], ['At 3:30 p.m.', '下午3:30。'], ['Which platform is it?', '几号站台？'], ['Platform 5.', '5号站台。'], ['Thank you very much.', '非常感谢。'], ['You are welcome. Have a good trip!', '不客气。旅途愉快！'], ['Thanks!', '谢谢！']],
    },
    {
        'title': 'Seeing the Doctor',
        'en': 'Tom: What is wrong with you?\nLucy: I have a fever and a headache.\nTom: How long have you been like this?\nLucy: Since yesterday evening.\nTom: Let me check your temperature.\nLucy: Is it serious?\nTom: No, just a cold. Take this medicine and drink more water.\nLucy: Thank you, doctor.\nTom: Have a good rest.',
        'zh': 'Tom: 你怎么了？\nLucy: 我发烧并且头痛。\nTom: 这样多久了？\nLucy: 从昨天晚上开始的。\nTom: 让我量一下体温。\nLucy: 严重吗？\nTom: 不严重，只是感冒。吃这个药，多喝热水。\nLucy: 谢谢你，医生。\nTom: 好好休息。',
        'grade': '八年级下册',
        'dialogue': [['What is wrong with you?', '你怎么了？'], ['I have a fever and a headache.', '我发烧并且头痛。'], ['How long have you been like this?', '这样多久了？'], ['Since yesterday evening.', '从昨天晚上开始的。'], ['Let me check your temperature.', '让我量一下体温。'], ['Is it serious?', '严重吗？'], ['No, just a cold. Take this medicine and drink more water.', '不严重，只是感冒。吃这个药，多喝热水。'], ['Thank you, doctor.', '谢谢你，医生。'], ['Have a good rest.', '好好休息。']],
    },
    {
        'title': 'Weather Report Chat',
        'en': 'Tom: What is the weather like today?\nLucy: It is sunny and warm.\nTom: What about tomorrow?\nLucy: It will be cloudy and cool.\nTom: Will it rain?\nLucy: I think so. You should take an umbrella.\nTom: Good idea. I hope it will not rain heavily.\nLucy: The weather report says it will be light rain.\nTom: That is great!',
        'zh': 'Tom: 今天天气怎么样？\nLucy: 晴朗且温暖。\nTom: 明天呢？\nLucy: 多云且凉爽。\nTom: 会下雨吗？\nLucy: 我想会的。你应该带把伞。\nTom: 好主意。希望不要下大雨。\nLucy: 天气预报说是小雨。\nTom: 太好了！',
        'grade': '八年级下册',
        'dialogue': [['What is the weather like today?', '今天天气怎么样？'], ['It is sunny and warm.', '晴朗且温暖。'], ['What about tomorrow?', '明天呢？'], ['It will be cloudy and cool.', '多云且凉爽。'], ['Will it rain?', '会下雨吗？'], ['I think so. You should take an umbrella.', '我想会的。你应该带把伞。'], ['Good idea. I hope it will not rain heavily.', '好主意。希望不要下大雨。'], ['The weather report says it will be light rain.', '天气预报说是小雨。'], ['That is great!', '太好了！']],
    },
    {
        'title': 'Part-time Job Interview',
        'en': 'Tom: Why do you want this job?\nLucy: I want to gain some work experience.\nTom: Have you worked before?\nLucy: No, but I am a quick learner.\nTom: What is your schedule like?\nLucy: I am free on weekends and after school.\nTom: How old are you?\nLucy: I am 16 years old.\nTom: OK. We will call you next week.\nLucy: Thank you very much.',
        'zh': 'Tom: 你为什么想要这份工作？\nLucy: 我想获得一些工作经验。\nTom: 你以前工作过吗？\nLucy: 没有，但我学东西很快。\nTom: 你的时间安排怎么样？\nLucy: 周末和放学后有空。\nTom: 你多大了？\nLucy: 我16岁。\nTom: 好的。我们下周会打电话给你。\nLucy: 非常感谢。',
        'grade': '八年级下册',
        'dialogue': [['Why do you want this job?', '你为什么想要这份工作？'], ['I want to gain some work experience.', '我想获得一些工作经验。'], ['Have you worked before?', '你以前工作过吗？'], ['No, but I am a quick learner.', '没有，但我学东西很快。'], ['What is your schedule like?', '你的时间安排怎么样？'], ['I am free on weekends and after school.', '周末和放学后有空。'], ['How old are you?', '你多大了？'], ['I am 16 years old.', '我16岁。'], ['OK. We will call you next week.', '好的。我们下周会打电话给你。'], ['Thank you very much.', '非常感谢。']],
    },
    {
        'title': 'Sports Meeting',
        'en': 'Tom: Did you take part in the sports meeting?\nLucy: Yes, I took part in the 100-meter race.\nTom: Did you win?\nLucy: No, I came in third.\nTom: That is still very good!\nLucy: Thank you. What about you?\nTom: I took part in the long jump.\nLucy: Did you win a prize?\nTom: Yes, I won first prize!\nLucy: Congratulations!',
        'zh': 'Tom: 你参加运动会了吗？\nLucy: 是的，我参加了100米赛跑。\nTom: 你赢了吗？\nLucy: 没有，我得了第三名。\nTom: 那也已经很好了！\nLucy: 谢谢。你呢？\nTom: 我参加了跳远。\nLucy: 你得奖了吗？\nTom: 是的，我得了一等奖！\nLucy: 恭喜！',
        'grade': '八年级下册',
        'dialogue': [['Did you take part in the sports meeting?', '你参加运动会了吗？'], ['Yes, I took part in the 100-meter race.', '是的，我参加了100米赛跑。'], ['Did you win?', '你赢了吗？'], ['No, I came in third.', '没有，我得了第三名。'], ['That is still very good!', '那也已经很好了！'], ['Thank you. What about you?', '谢谢。你呢？'], ['I took part in the long jump.', '我参加了跳远。'], ['Did you win a prize?', '你得奖了吗？'], ['Yes, I won first prize!', '是的，我得了一等奖！'], ['Congratulations!', '恭喜！']],
    },
    {
        'title': 'Library Rules',
        'en': 'Tom: Can I borrow these books?\nLucy: Yes, but you must return them in two weeks.\nTom: Can I renew them?\nLucy: Yes, you can renew them online.\nTom: Is there a fine for late returns?\nLucy: Yes, one yuan per day.\nTom: I see. Can I take photos here?\nLucy: No, photos are not allowed.\nTom: OK, I will obey the rules.\nLucy: Thank you for your cooperation.',
        'zh': 'Tom: 我可以借这些书吗？\nLucy: 可以，但你必须在两周内归还。\nTom: 我可以续借吗？\nLucy: 可以，你可以在网上续借。\nTom: 晚还书有罚款吗？\nLucy: 有，每天一元。\nTom: 我明白了。我可以在这里拍照吗？\nLucy: 不可以，不允许拍照。\nTom: 好的，我会遵守规定。\nLucy: 谢谢你的配合。',
        'grade': '八年级下册',
        'dialogue': [['Can I borrow these books?', '我可以借这些书吗？'], ['Yes, but you must return them in two weeks.', '可以，但你必须在两周内归还。'], ['Can I renew them?', '我可以续借吗？'], ['Yes, you can renew them online.', '可以，你可以在网上续借。'], ['Is there a fine for late returns?', '晚还书有罚款吗？'], ['Yes, one yuan per day.', '有，每天一元。'], ['I see. Can I take photos here?', '我明白了。我可以在这里拍照吗？'], ['No, photos are not allowed.', '不可以，不允许拍照。'], ['OK, I will obey the rules.', '好的，我会遵守规定。'], ['Thank you for your cooperation.', '谢谢你的配合。']],
    },
    {
        'title': 'Festival Celebration',
        'en': 'Tom: What is your favorite festival?\nLucy: My favorite festival is the Spring Festival.\nTom: Why do you like it?\nLucy: Because I can get red packets and eat delicious food.\nTom: What do you usually do?\nLucy: We have a big family dinner and watch TV together.\nTom: That sounds wonderful!\nLucy: Welcome to my home this Spring Festival!\nTom: Thank you! I would love to.',
        'zh': 'Tom: 你最喜欢什么节日？\nLucy: 我最喜欢春节。\nTom: 你为什么喜欢它？\nLucy: 因为我可以收到红包，还能吃到美味的食物。\nTom: 你们通常做什么？\nLucy: 我们吃一顿丰盛的家庭晚餐，一起看电视。\nTom: 听起来太棒了！\nLucy: 今年春节欢迎来我家！\nTom: 谢谢！我很乐意。',
        'grade': '八年级下册',
        'dialogue': [['What is your favorite festival?', '你最喜欢什么节日？'], ['My favorite festival is the Spring Festival.', '我最喜欢春节。'], ['Why do you like it?', '你为什么喜欢它？'], ['Because I can get red packets and eat delicious food.', '因为我可以收到红包，还能吃到美味的食物。'], ['What do you usually do?', '你们通常做什么？'], ['We have a big family dinner and watch TV together.', '我们吃一顿丰盛的家庭晚餐，一起看电视。'], ['That sounds wonderful!', '听起来太棒了！'], ['Welcome to my home this Spring Festival!', '今年春节欢迎来我家！'], ['Thank you! I would love to.', '谢谢！我很乐意。']],
    },
    {
        'title': 'Internet Safety',
        'en': 'Tom: Do you often go online?\nLucy: Yes, I use the Internet every day.\nTom: What do you usually do online?\nLucy: I chat with friends and search for information.\nTom: Do you know about internet safety?\nLucy: Not really. What should I pay attention to?\nTom: Do not give out personal information.\nLucy: I see. Anything else?\nTom: Do not meet online friends alone.\nLucy: Thank you for telling me.',
        'zh': 'Tom: 你经常上网吗？\nLucy: 是的，我每天都上网。\nTom: 你通常在上网做什么？\nLucy: 我和朋友聊天，搜索信息。\nTom: 你知道网络安全吗？\nLucy: 不太清楚。我应该注意什么？\nTom: 不要泄露个人信息。\nLucy: 我明白了。还有其他的吗？\nTom: 不要单独见网友。\nLucy: 谢谢你告诉我。',
        'grade': '八年级下册',
        'dialogue': [['Do you often go online?', '你经常上网吗？'], ['Yes, I use the Internet every day.', '是的，我每天都上网。'], ['What do you usually do online?', '你通常在上网做什么？'], ['I chat with friends and search for information.', '我和朋友聊天，搜索信息。'], ['Do you know about internet safety?', '你知道网络安全吗？'], ['Not really. What should I pay attention to?', '不太清楚。我应该注意什么？'], ['Do not give out personal information.', '不要泄露个人信息。'], ['I see. Anything else?', '我明白了。还有其他的吗？'], ['Do not meet online friends alone.', '不要单独见网友。'], ['Thank you for telling me.', '谢谢你告诉我。']],
    },
    {
        'title': 'Volunteer Work',
        'en': 'Tom: What did you do last weekend?\nLucy: I did volunteer work at the old peoples home.\nTom: What did you do there?\nLucy: I cleaned the rooms and talked with the old people.\nTom: That is so nice of you!\nLucy: Thank you. It made me very happy.\nTom: I want to join you next time.\nLucy: Great! We go there every month.\nTom: I will contact you then.',
        'zh': 'Tom: 上周末你做了什么？\nLucy: 我在养老院做了志愿者工作。\nTom: 你在那里做了什么？\nLucy: 我打扫房间，和老人们聊天。\nTom: 你真是太好了！\nLucy: 谢谢。这让我非常开心。\nTom: 下次我想加入你们。\nLucy: 太好了！我们每个月都去。\nTom: 到时候我会联系你。',
        'grade': '八年级下册',
        'dialogue': [['What did you do last weekend?', '上周末你做了什么？'], ['I did volunteer work at the old peoples home.', '我在养老院做了志愿者工作。'], ['What did you do there?', '你在那里做了什么？'], ['I cleaned the rooms and talked with the old people.', '我打扫房间，和老人们聊天。'], ['That is so nice of you!', '你真是太好了！'], ['Thank you. It made me very happy.', '谢谢。这让我非常开心。'], ['I want to join you next time.', '下次我想加入你们。'], ['Great! We go there every month.', '太好了！我们每个月都去。'], ['I will contact you then.', '到时候我会联系你。']],
    },
]

# ==================== 语法知识数据 ====================
BUILTIN_GRAMMAR = {
    "七年级上册": [
        {
            "title": "be动词的用法",
            "content": """【基本用法】
be动词包括：am, is, are

【用法口诀】
我(I)用am，你(you)用are，
is连着他(he)她(she)它(it)，
单数is，复数are，
变疑问，往前提，
变否定，not后加。

【例句】
I am a student. 我是学生。
You are my friend. 你是我的朋友。
He is tall. 他很高。
She is beautiful. 她很漂亮。
It is a cat. 它是一只猫。
We are happy. 我们很快乐。
They are students. 他们是学生。

【注意】
- be动词永远不能单独作谓语，后面必须接表语
- be动词不能与do/does连用"""
        },
        {
            "title": "人称代词",
            "content": """【主格代词】
I - 我    you - 你/你们
he - 他   she - 她    it - 它
we - 我们  they - 他们

【宾格代词】
me - 我    you - 你/你们
him - 他   her - 她    it - 它
us - 我们  them - 他们

【用法】
主格作主语，宾格作宾语

【例句】
I like him. 我喜欢他。
He helps me. 他帮助我。
Give it to her. 把它给她。

【形容词性物主代词】
my - 我的    your - 你的
his - 他的   her - 她的
its - 它的   our - 我们的
their - 他们的

【名词性物主代词】
mine - 我的    yours - 你的
his - 他的     hers - 她的
ours - 我们的  theirs - 他们的"""
        },
        {
            "title": "指示代词",
            "content": """【基本用法】
this - 这个（单数近指）
that - 那个（单数远指）
these - 这些（复数近指）
those - 那些（复数远指）

【例句】
This is my book. 这是我的书。
That is your pen. 那是你的钢笔。
These are apples. 这些是苹果。
Those are oranges. 那些是橙子。

【打电话时】
用this介绍自己，用that询问对方
Hello, this is Tom. 你好，我是汤姆。
Who's that? 你是谁？

【问句回答】
- Is this your book? 这是你的书吗？
- Yes, it is. / No, it isn't. 是的。/ 不是。

注意：回答时用it代替this/that"""
        },
        {
            "title": "名词单复数",
            "content": """【规则变化】
1. 一般加-s：book-books, pen-pens

2. 以s, x, ch, sh结尾加-es：
   bus-buses, box-boxes
   watch-watches, brush-brushes

3. 以辅音字母+y结尾，变y为i加es：
   baby-babies, family-families
   以元音字母+y结尾，直接加s：
   boy-boys, day-days

4. 以f或fe结尾，变f/fe为v加es：
   knife-knives, leaf-leaves

5. 以o结尾：
   有生命的加-es：tomato-tomatoes
   无生命的加-s：photo-photos

【不规则变化】
man-men, woman-women
child-children
foot-feet, tooth-teeth
mouse-mice
sheep-sheep（单复数同形）
deer-deer（单复数同形）
fish-fish（单复数同形）
Chinese-Chinese（单复数同形）"""
        },
        {
            "title": "冠词a/an/the",
            "content": """【不定冠词 a/an】
a用于辅音音素开头：a book, a dog
an用于元音音素开头：an apple, an egg, an hour

用法：
1. 第一次提到某人或某物
2. 表示一个的意思
3. 表示一类事物

【定冠词 the】
用法：
1. 特指某人或某物
2. 上文提到的人或物
3. 世界上独一无二的事物
4. 乐器前：play the piano
5. 方位名词前：in the east
6. 形容词最高级前：the best

【零冠词】
1. 三餐、球类运动前：have breakfast, play basketball
2. 某些固定短语：go to school, at home"""
        },
        {
            "title": "There be句型",
            "content": """【基本结构】
There is + 单数名词/不可数名词
There are + 复数名词

【例句】
There is a book on the desk.
There is some water in the glass.
There are many students in the classroom.

【就近原则】
There is a pen and two books on the desk.
（靠近be动词的是pen，单数，用is）

【变疑问句】
把be动词提到there前面：
Is there a book on the desk?
Yes, there is. / No, there isn't.

【There be与have的区别】
There be表示某处有某物
have表示某人有某物"""
        },
        {
            "title": "现在进行时",
            "content": """【结构】
主语 + be动词 + V-ing

【动词-ing变化】
1. 一般加-ing：do-doing, read-reading
2. 以e结尾，去e加-ing：make-making
3. 重读闭音节双写：run-running, swim-swimming

【例句】
I am reading a book.
He is watching TV.
They are playing basketball.

【时间标志】
now, right now, Look!, Listen!"""
        }
    ],
    
    "七年级下册": [
        {
            "title": "一般现在时",
            "content": """【结构】
肯定句：主语 + 动词原形/第三人称单数
否定句：主语 + don't/doesn't + 动词原形
疑问句：Do/Does + 主语 + 动词原形?

【第三人称单数变化】
一般加-s：works, reads
以s, x, ch, sh, o结尾加-es：watches, goes
以辅音字母+y结尾变y为i加es：studies

【用法】
1. 经常性或习惯性的动作
2. 客观事实或真理
3. 现在的状态

【时间标志】
always, usually, often, sometimes, every day"""
        },
        {
            "title": "频度副词",
            "content": """【频度排序】
always (100%) > usually (80%) > often (60%)
> sometimes (40%) > seldom (20%) > never (0%)

【位置】
放在be动词、情态动词后，实义动词前

【提问频率】
How often do you exercise?
I exercise three times a week."""
        },
        {
            "title": "介词",
            "content": """【时间介词】
in + 年/月/季节：in 2024, in May, in spring
on + 具体某天：on Monday, on June 1st
at + 具体时刻：at 6:00, at noon

【方位介词】
in 在...里面
on 在...上面
under 在...下面
behind 在...后面
in front of 在...前面
between 在...之间
next to 紧挨着"""
        },
        {
            "title": "情态动词can/may/must",
            "content": """【can的用法】
表示能力：I can swim.
表示许可：Can I use your pen?
表示可能性：It can be true.

【must的用法】
表示必须：You must finish it.
表示肯定推测：He must be at home.

【注意】
must的否定是needn't（不必），不是mustn't（禁止）"""
        },
        {
            "title": "祈使句",
            "content": """【结构】
肯定：动词原形开头
否定：Don't + 动词原形

【例句】
Open the door. 开门。
Don't run. 不要跑。
Let's go! 我们走吧！"""
        }
    ],
    
    "八年级上册": [
        {
            "title": "一般过去时",
            "content": """【结构】
肯定句：主语 + 动词过去式
否定句：主语 + didn't + 动词原形
疑问句：Did + 主语 + 动词原形?

【不规则动词过去式】
am/is-was, are-were
go-went, come-came
do-did, have-had
see-saw, take-took

【时间标志】
yesterday, last week, ...ago, in 2020"""
        },
        {
            "title": "过去进行时",
            "content": """【结构】
主语 + was/were + V-ing

【用法】
表示过去某个时间正在进行的动作

【时间标志】
at 8:00 yesterday, when/while...

【when与while的区别】
when + 一般过去时（短暂动作）
while + 过去进行时（持续动作）"""
        },
        {
            "title": "形容词比较级和最高级",
            "content": """【比较级构成】
单音节加-er/est：tall-taller-tallest
多音节加more/most：beautiful-more beautiful

【不规则变化】
good-better-best
bad-worse-worst
many-more-most

【用法】
比较级：A is taller than B.
最高级：A is the tallest in class."""
        },
        {
            "title": "不定代词",
            "content": """【基本形式】
something, anything, nothing, everything
someone, anyone, no one, everyone

【用法】
1. 作主语时谓语动词用单数
2. 形容词修饰不定代词要放在后面
   something important 重要的事
3. some-用于肯定句，any-用于否定/疑问句"""
        }
    ],
    
    "八年级下册": [
        {
            "title": "现在完成时",
            "content": """【结构】
主语 + have/has + 过去分词

【用法】
1. 动作刚完成，对现在有影响
2. 过去的动作持续到现在

【时间标志】
already, yet, just, ever, never, for, since

【have been to vs have gone to】
have been to：去过（已回来）
have gone to：去了（还没回来）"""
        },
        {
            "title": "被动语态",
            "content": """【结构】
主语 + be + 过去分词

【时态变化】
一般现在时：am/is/are + done
一般过去时：was/were + done
一般将来时：will be + done

【例句】
English is spoken by many people.
The bridge was built in 2020."""
        },
        {
            "title": "情态动词表推测",
            "content": """【肯定推测】
must：一定（100%）
He must be at home.

【可能推测】
may/might：可能（50%）
He may come tomorrow.

【否定推测】
can't：不可能
He can't be a teacher."""
        },
        {
            "title": "直接引语和间接引语",
            "content": """【人称变化】
一随主，二随宾，三不变

【时态变化】
一般现在时→一般过去时
一般过去时→过去完成时

【语序】
宾语从句用陈述句语序"""
        }
    ],
    
    "九年级": [
        {
            "title": "定语从句",
            "content": """【定义】
修饰名词或代词的从句

【关系代词】
who：指人，作主语或宾语
whom：指人，作宾语
whose：指人或物，表示所属
which：指物
that：指人或物

【只用that的情况】
1. 先行词是最高级
2. 先行词是all, everything等
3. 先行词既有人又有物"""
        },
        {
            "title": "宾语从句",
            "content": """【引导词】
that：引导陈述句（可省略）
if/whether：引导一般疑问句
疑问词：引导特殊疑问句

【语序】
宾语从句用陈述句语序

【时态呼应】
主句现在时，从句可用任何时态
主句过去时，从句用过去时态
客观真理永远用一般现在时"""
        },
        {
            "title": "状语从句",
            "content": """【时间状语】
when, while, before, after, as soon as, until, since

【条件状语】
if, unless

【原因状语】
because, since, as

【结果状语】
so...that..., such...that...

【让步状语】
though/although（不能与but连用）"""
        },
        {
            "title": "虚拟语气",
            "content": """【if条件句】
与现在相反：if + 过去式，主句 + would do
If I were you, I would study harder.

与过去相反：if + had done，主句 + would have done
If I had known, I would have told you.

【wish】
I wish I were a bird.
（事实：我不是鸟）"""
        },
        {
            "title": "主谓一致",
            "content": """【就近原则】
there be, or, either...or, neither...nor

【就远原则】
with, together with, as well as

【集合名词】
强调整体用单数，强调个体用复数
His family is big.
His family are watching TV.

【数量词】
a number of + 复数（用复数）
the number of + 复数（用单数）"""
        }
    ]
}

# ==================== 英语作文高分句型库 ====================
ESSAY_PHRASES = [
    {"cat": "经典高分句式", "en": "Nothing is more important than to receive education.", "zh": "没有比接受教育更重要的事。"},
    {"cat": "经典高分句式", "en": "There is no denying that the qualities of our living have gone from bad to worse.", "zh": "不可否认，我们的生活品质已经每况愈下。"},
    {"cat": "经典高分句式", "en": "It is universally acknowledged that trees are indispensable to us.", "zh": "全世界都知道树木对我们是不可或缺的。"},
    {"cat": "经典高分句式", "en": "So precious is time that we cannot afford to waste it.", "zh": "时间是如此珍贵，我们经不起浪费它。"},
    {"cat": "经典高分句式", "en": "The harder you work, the more progress you make.", "zh": "你愈努力，你愈进步。"},
    {"cat": "经典高分句式", "en": "On no account can we ignore the value of knowledge.", "zh": "我们绝对不能忽略知识的价值。"},
    {"cat": "表明事实", "en": "We cannot ignore the fact that ...", "zh": "我们不能忽略这个事实……"},
    {"cat": "表明事实", "en": "No one can deny the fact that ...", "zh": "没人能否认这个事实……"},
    {"cat": "表明事实", "en": "It is commonly accepted fact that ...", "zh": "这是一个被普遍接受的事实。"},
    {"cat": "阐述原因", "en": "There are three reasons for this.", "zh": "造成这一现象有三个原因。"},
    {"cat": "阐述原因", "en": "The reasons for this are as follows.", "zh": "造成这一现象的原因如下。"},
    {"cat": "阐述原因", "en": "For one thing... For another...", "zh": "一方面……另一方面……"},
    {"cat": "提出建议", "en": "We should take some effective measures.", "zh": "我们应该采取一些有效措施。"},
    {"cat": "提出建议", "en": "It is high time that we put an end to the trend.", "zh": "该是我们终止这一趋势的时候了。"},
    {"cat": "提出建议", "en": "The best way to solve the troubles is ...", "zh": "解决这些麻烦的最好办法是……"},
    {"cat": "发表观点", "en": "From my point of view, it is more reasonable to support the first opinion.", "zh": "在我看来，支持第一种观点更有道理。"},
    {"cat": "发表观点", "en": "People views on ... vary from person to person.", "zh": "人们对……的观点因人而异。"},
    {"cat": "举例论证", "en": "A convincing example is that ...", "zh": "一个有说服力的例子是……"},
    {"cat": "举例论证", "en": "A case in point is ...", "zh": "一个恰当的例子是……"},
    {"cat": "举例论证", "en": "Take ... for example.", "zh": "以……为例。"},
    {"cat": "结构固定句型", "en": "It is + adj. + for sb. + to do sth.", "zh": "对某人来说做某事是……的"},
    {"cat": "结构固定句型", "en": "sb. + spend + time + (in) doing sth.", "zh": "某人花费时间做某事"},
    {"cat": "谚语俗语", "en": "Where there is a will, there is a way.", "zh": "有志者，事竟成。"},
    {"cat": "谚语俗语", "en": "Practice makes perfect.", "zh": "熟能生巧。"},
    {"cat": "谚语俗语", "en": "Every coin has two sides.", "zh": "凡事都有两面性。"},
    {"cat": "谚语俗语", "en": "Actions speak louder than words.", "zh": "事实胜于雄辩。"},
    {"cat": "开篇衔接词", "en": "first of all / to begin with / to start with", "zh": "首先，第一"},
    {"cat": "开篇衔接词", "en": "generally speaking", "zh": "一般来说"},
    {"cat": "承接过渡", "en": "besides / furthermore / moreover", "zh": "此外，而且"},
    {"cat": "承接过渡", "en": "for example / for instance", "zh": "例如"},
    {"cat": "转折对比", "en": "however / nevertheless / nonetheless", "zh": "但是，然而"},
    {"cat": "转折对比", "en": "on the contrary / in contrast", "zh": "相反地"},
    {"cat": "总结收束", "en": "in conclusion / to conclude / in summary", "zh": "总之"},
    {"cat": "总结收束", "en": "in a word / in short / in brief", "zh": "简而言之"},
]

ESSAY_CATEGORIES = []
_seen = set()
for _p in ESSAY_PHRASES:
    if _p["cat"] not in _seen:
        _seen.add(_p["cat"])
        ESSAY_CATEGORIES.append(_p["cat"])
del _seen, _p


class WordFillWidget(QWidget):
    """单词填空控件 - 自定义输入（无QLineEdit）"""

    def __init__(self, word, missing_pos, parent=None):
        super().__init__(parent)
        self.word = word
        self.missing_pos = missing_pos
        self.missing_char = word[missing_pos].lower()
        self.user_input = ""

        self.setFixedHeight(120)
        self.setMinimumWidth(600)

        # 布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(0)

        prefix = word[:missing_pos]
        suffix = word[missing_pos+1:]

        font = QFont("微软雅黑", 48, QFont.Bold)

        # 前缀
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

        # 后缀
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
                # 只接受字母输入
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
                    return True  # 忽略其他键
        return super().eventFilter(obj, event)

    def showEvent(self, event):
        super().showEvent(event)
        self.input_label.setFocus()



class PhraseFillWidget(QWidget):
    """短语填空控件 - 整词填空（显示 be ___ at，填 good）"""

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
                # 整词输入框
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
        self.init_tts()
        self._load_data()
        self.init_ui()
        self._populate_ui()
        self._setup_grammar_tab()
        # ===== 奖励系统 =====
        self.word_streak = 0
        self.phrase_streak = 0
        self.dialogue_streak = 0
        self.total_word_correct = 0
        self.total_phrase_correct = 0
        self.total_dialogue_correct = 0
        self.stars = 0
        self.hearts = 0
        self.statusBar()
        self.star_lbl = QLabel("")
        self.heart_lbl = QLabel("")
        self.reward_tip_lbl = QLabel("")
        self.star_lbl.setFont(QFont("Segoe UI Emoji", 14))
        self.heart_lbl.setFont(QFont("Segoe UI Emoji", 14))
        self.reward_tip_lbl.setFont(QFont("Microsoft YaHei", 9))
        self.statusBar().addPermanentWidget(self.star_lbl)
        self.statusBar().addPermanentWidget(self.heart_lbl)
        self.statusBar().addPermanentWidget(self.reward_tip_lbl)
        self._update_reward_display()



    def _load_data(self):
        """加载数据（不依赖UI）"""
        self.words = list(BUILTIN_WORD_LIST)
        self.phrases = list(BUILTIN_PHRASE_LIST)
        self.dialogues = list(BUILTIN_DIALOGUES)
        
        # 文件路径
        self.word_lib_path = "D:/word_lib.txt"
        self.phrase_lib_path = "D:/phrase_lib.txt"
        self.word_review_path = "D:/word_review.pkl"
        self.phrase_review_path = "D:/phrase_review.pkl"
        
        # 词库映射
        self.word_lib = {}
        for item in self.words:
            en, zh = item[0], item[1] if len(item) >= 2 else ""
            self.word_lib[en] = zh
        self.phrase_lib = {}
        for item in self.phrases:
            en, zh = item[0], item[1] if len(item) >= 2 else ""
            self.phrase_lib[en] = zh
        
        # 尝试加载外部文件
        try:
            with open("D:/word_lib.txt", 'r', encoding='utf-8') as f:
                lines = f.read().strip().split('\n')
                if lines and lines[0]:
                    self.words = []
                    for line in lines:
                        line = line.strip()
                        if not line: continue
                        parts = line.split('|', 1) if '|' in line else line.split(None, 1)
                        if len(parts) >= 2:
                            self.words.append((parts[0].strip(), parts[1].strip()))
        except: pass
        
        # 复习记录
        self.word_review_records = []
        try:
            with open("D:/word_review.pkl", 'rb') as f:
                self.word_review_records = pickle.load(f)
        except: pass
        self.phrase_review_records = []
        try:
            with open("D:/phrase_review.pkl", 'rb') as f:
                self.phrase_review_records = pickle.load(f)
        except: pass

    def _populate_ui(self):
        """填充UI列表（依赖UI已创建）"""
        # 填充词汇列表
        for w, m in self.word_lib.items():
            ph = phonetic_dict.get(w, ""); self.word_list.addItem(f"{w} {ph} - {m}")
        
        # 填充短语列表
        for p, m in self.phrase_lib.items():
            self.phrase_list.addItem(f"{p} - {m}")
        
        # 填充对话列表
        for d in self.dialogues:
            self.dialogue_list.addItem(d.get('title', ''))
        
        # Update review tips
        if hasattr(self, 'update_word_review_tip'):
            self.update_word_review_tip()
        if hasattr(self, 'update_phrase_review_tip'):
            self.update_phrase_review_tip()

    def _update_reward_display(self):
        """更新状态栏奖励显示"""
        if self.stars > 0:
            self.star_lbl.setText(" " + "\u2605" * self.stars + " ")
            self.star_lbl.setStyleSheet("color:#FFD700; font-weight:bold;")
        else:
            self.star_lbl.setText("")
        if self.hearts > 0:
            self.heart_lbl.setText(" " + "\u2665" * self.hearts + " ")
            self.heart_lbl.setStyleSheet("color:#FF69B4; font-weight:bold;")
        else:
            self.heart_lbl.setText("")
        tips = []
        if self.total_word_correct < 20:
            tips.append("\u5355\u8bcd\u8fd8\u9700" + str(20 - self.total_word_correct) + "\u9898\u2605")
        if self.total_phrase_correct < 10:
            tips.append("\u77ed\u8bcd\u8fd8\u9700" + str(10 - self.total_phrase_correct) + "\u9898\u2605")
        if self.total_dialogue_correct < 5:
            tips.append("\u5bf9\u8bdd\u8fd8\u9700" + str(5 - self.total_dialogue_correct) + "\u9898\u2605")
        self.reward_tip_lbl.setText(" | ".join(tips) if tips else "")

    def _check_star_award(self, mode):
        """检查是否获得星星"""
        awarded = False
        if mode == "word" and self.total_word_correct >= 20 and self.word_streak >= 10:
            self.stars += 1
            awarded = True
        elif mode == "phrase" and self.total_phrase_correct >= 10 and self.phrase_streak >= 5:
            self.stars += 1
            awarded = True
        elif mode == "dialogue" and self.total_dialogue_correct >= 5 and self.dialogue_streak >= 2:
            self.stars += 1
            awarded = True
        if awarded and self.stars % 5 == 0:
            self.hearts += 1
            self._show_heart_reward()

    
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
        # 语音选项
        self.voice_options = {
            "US-Female": "Zira",
            "US-Male": "David",
            "UK-Female": "Susan",
            "UK-Male": "George",
        }
        self.selected_voice = "US-Female"

    def on_voice_changed(self, voice_name):
        """切换语音"""
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
        """TTS朗读 - 支持QTextToSpeech和pyttsx3，不阻塞UI"""
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
                with open(r'D:\_tts_error.log', 'a', encoding='utf-8') as log:
                    log.write('speak error: ' + str(e))
            except Exception:
                pass

    def init_ui(self):
        self.setWindowTitle("初中英语全能学习系统 | 内嵌填空 | 单词·短语·对话")

        # 语音选择
        voice_label = QLabel("语音:")
        voice_label.setFont(QFont("微软雅黑", 10))
        self.voice_combobox = QComboBox()
        self.voice_combobox.addItems(["US-Female", "US-Male", "UK-Female", "UK-Male"])
        self.voice_combobox.setFixedWidth(120)
        self.voice_combobox.currentTextChanged.connect(self.on_voice_changed)
        self.setFixedSize(1200, 800)
        self.setStyleSheet("background-color: #f5f5f5;")
        self.font = QFont("微软雅黑", 12)
        self.title_font = QFont("微软雅黑", 14, QFont.Bold)

        self.main_tabs = QTabWidget()
        self.setCentralWidget(self.main_tabs)

        self.word_tab = QWidget()
        self.phrase_tab = QWidget()
        self.dialogue_tab = QWidget()
        self.grammar_tab = QWidget()
        self.essay_tab = QWidget()

        self.main_tabs.addTab(self.word_tab, "📖 单词 (200+)")
        self.main_tabs.addTab(self.phrase_tab, "📝 短语 (120+)")
        self.main_tabs.addTab(self.dialogue_tab, "💬 口语对话 (70场景)")
        self.main_tabs.addTab(self.grammar_tab, '语法知识')
        self.main_tabs.addTab(self.essay_tab, "\u270d\ufe0f 作文句型")

        self.main_tabs.setStyleSheet("""
            QTabWidget::tab-bar {alignment: center;}
            QTabBar::tab {
                background-color: #e0e0e0; color: #333; font-size: 14px;
                font-family: 微软雅黑; padding: 10px 25px; margin-right: 5px;
                border-radius: 8px 8px 0 0; border: none;
            }
            QTabBar::tab:selected, QTabBar::tab:hover {
                background-color: #4a90e2; color: white;
            }
            QTabWidget::pane {
                border: 1px solid #e0e0e0; border-radius: 0 0 8px 8px;
                background-color: white;
            }
        """)

        self.setup_word_module()
        self.setup_phrase_module()
        self.setup_dialogue_module()
        self._setup_essay_tab()

    # ---------- 单词模块 ----------
    def setup_word_module(self):
        self.word_sub_tabs = QTabWidget()
        layout = QVBoxLayout(self.word_tab)
        layout.addWidget(self.word_sub_tabs)

        self.word_manage = QWidget()
        self.word_random = QWidget()
        self.word_review = QWidget()
        self.word_completion = QWidget()

        self.word_sub_tabs.addTab(self.word_manage, "词库管理")
        self.word_sub_tabs.addTab(self.word_random, "随机抽查 + 双向默写")
        self.word_sub_tabs.addTab(self.word_review, "记忆曲线复习")
        self.word_sub_tabs.addTab(self.word_completion, "✏️ 单词补全 (内嵌填空)")

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
        self.word_import_btn = QPushButton("导入词库(TXT)")
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
        self.word_input.setPlaceholderText("单词")
        self.meaning_input = QLineEdit()
        self.meaning_input.setPlaceholderText("释义")
        for inp in (self.word_input, self.meaning_input):
            inp.setStyleSheet("padding: 8px 10px; border: 1px solid #e0e0e0; border-radius: 6px;")
        input_layout.addWidget(self.word_input)
        input_layout.addWidget(self.meaning_input)
        layout.addLayout(input_layout)
        layout.addSpacing(15)

        # 年级筛选下拉框
        self.vocab_grade_combo = QComboBox()
        self.vocab_grade_combo.addItems(["\u5168\u90e8", "\u4e03\u5e74\u7ea7\u4e0a\u518c", "\u4e03\u5e74\u7ea7\u4e0b\u518c",
                                          "\u516b\u5e74\u7ea7\u4e0a\u518c", "\u516b\u5e74\u7ea7\u4e0b\u518c", "\u4e5d\u5e74\u7ea7"])
        self.vocab_grade_combo.setFont(QFont("Microsoft YaHei", 11))
        self.vocab_grade_combo.currentTextChanged.connect(self._filter_vocab_list)
        grade_h = QHBoxLayout()
        grade_h.addWidget(QLabel("\u5e74\u7ea7\uff1a"))
        grade_h.addWidget(self.vocab_grade_combo)
        grade_h.addStretch()
        layout.addLayout(grade_h)
        layout.addSpacing(8)

        self.word_list = QListWidget()
        self.word_list.setFont(self.font)
        self.word_list.setStyleSheet("border: 1px solid #e0e0e0; border-radius: 6px;")
        self.word_list.itemDoubleClicked.connect(lambda item: self.speak(item.text().split(" - ")[0]))
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
        mode_label = QLabel("默写模式：")
        mode_label.setFont(self.font)
        self.word_mode_en2zh = QRadioButton("英译中 (显示英文，输入中文)")
        self.word_mode_zh2en = QRadioButton("中译英 (显示中文，输入英文)")
        self.word_mode_en2zh.setChecked(True)
        self.word_mode_group = QButtonGroup()
        self.word_mode_group.addButton(self.word_mode_en2zh)
        self.word_mode_group.addButton(self.word_mode_zh2en)
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.word_mode_en2zh)
        mode_layout.addWidget(self.word_mode_zh2en)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        self.word_card = QLabel("点击下方按钮开始抽查")
        self.word_card.setFont(QFont("微软雅黑", 24, QFont.Bold))
        self.word_card.setAlignment(Qt.AlignCenter)
        self.word_card.setStyleSheet("background-color: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 10px; padding: 30px;")
        layout.addWidget(self.word_card)

        self.word_meaning_label = QLabel()
        self.word_meaning_label.setFont(QFont("微软雅黑", 16))
        self.word_meaning_label.setAlignment(Qt.AlignCenter)
        self.word_meaning_label.setVisible(False)
        layout.addWidget(self.word_meaning_label)

        btn_layout = QHBoxLayout()
        self.word_start_btn = QPushButton("开始抽查")
        self.word_show_btn = QPushButton("查看释义")
        self.word_speak_btn = QPushButton("🔊 朗读单词")
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

        line = QLabel("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        line.setAlignment(Qt.AlignCenter)
        line.setStyleSheet("color: #cccccc;")
        layout.addWidget(line)

        dict_title = QLabel("📝 默写模式：根据上方内容输入答案，系统自动验证")
        dict_title.setFont(self.font)
        dict_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(dict_title)

        input_row = QHBoxLayout()
        self.word_dict_input = QLineEdit()
        self.word_dict_input.setPlaceholderText("在这里输入答案...")
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

    def refresh_word_display(self):
        if self.current_word:
            self.word_card.setText(self._get_word_display_text())
            self.word_meaning_label.setVisible(False)
            self.word_dict_input.clear()
            self.word_dict_result.setText("")
            if self.word_mode_en2zh.isChecked():
                self.word_dict_input.setPlaceholderText("请输入对应的中文释义...")
            else:
                self.word_dict_input.setPlaceholderText("请输入对应的英文单词...")

    def start_word_random(self):
        if not self.word_lib:
            QMessageBox.warning(self, "提示", "词库为空")
            return
        self.current_word = random.choice(list(self.word_lib.keys()))
        self.word_card.setText(self._get_word_display_text())
        self.word_meaning_label.setVisible(False)
        self.word_dict_input.clear()
        self.word_dict_result.setText("")
        self.word_show_btn.setEnabled(True)
        self.word_speak_btn.setEnabled(True)
        self.word_mastered_btn.setEnabled(True)
        self.word_unmastered_btn.setEnabled(True)
        if self.word_mode_en2zh.isChecked():
            self.word_dict_input.setPlaceholderText("请输入对应的中文释义...")
        else:
            self.word_dict_input.setPlaceholderText("请输入对应的英文单词...")

    def show_word_meaning(self):
        if self.current_word:
            self.word_meaning_label.setText(self.word_lib[self.current_word])
            self.word_meaning_label.setVisible(True)

    def check_word_dictation(self):
        if self.current_word is None:
            QMessageBox.warning(self, "提示", "请先开始抽查")
            return
        user = self.word_dict_input.text().strip()
        if not user:
            self.word_dict_result.setText("请输入答案")
            self.word_dict_result.setStyleSheet("color: orange;")
            return
        def clean(s):
            return re.sub(r'[^\w\u4e00-\u9fff]', '', s).lower()
        if self.word_mode_en2zh.isChecked():
            correct = self.word_lib[self.current_word]
            if clean(user) == clean(correct):
                self.word_dict_result.setText("✅ 正确！")
                self.word_dict_result.setStyleSheet("color: green;")
            else:
                self.word_dict_result.setText(f"❌ 错误，正确答案：{correct}")
                self.word_dict_result.setStyleSheet("color: red;")
        else:
            correct = self.current_word
            if clean(user) == clean(correct):
                self.word_dict_result.setText("✅ 正确！")
                self.word_dict_result.setStyleSheet("color: green;")
            else:
                self.word_dict_result.setText(f"❌ 错误，正确答案：{correct}")
                self.word_dict_result.setStyleSheet("color: red;")

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
        QMessageBox.information(self, "提示", f"{word} 已加入复习队列")
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

        btn_layout = QHBoxLayout()
        self.word_review_start_btn = QPushButton("开始复习")
        self.word_review_show_btn = QPushButton("查看释义")
        self.word_review_speak_btn = QPushButton("🔊 朗读单词")
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
        self.current_review_word = None

    # ---------- 单词补全新功能（内嵌填空，间距优化）----------
    def setup_word_completion_tab(self):
        main_layout = QVBoxLayout(self.word_completion)
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(20)

        title = QLabel("🔤 单词补全练习 (内嵌填空)")
        title.setFont(self.title_font)
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # 单词卡片容器
        self.word_completion_container = QWidget()
        self.word_completion_container.setStyleSheet("background-color: transparent; border: none;")
        self.word_completion_layout = QHBoxLayout(self.word_completion_container)
        self.word_completion_layout.setAlignment(Qt.AlignCenter)
        self.word_completion_layout.setSpacing(0)    # 关键：去掉间距，让字母紧凑
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
        self.word_completion_next_btn = QPushButton("下一个单词")
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
        label = QLabel("点击「下一个单词」开始练习")
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
            QMessageBox.warning(self, "提示", "单词库为空")
            self.show_word_completion_placeholder()
            return
        # 随机选一个单词（长度至少2，否则跳过）
        valid_words = [w for w in self.word_lib.keys() if len(w) >= 2]
        if not valid_words:
            QMessageBox.warning(self, "提示", "词库中没有长度>=2的单词，无法进行补全练习")
            self.show_word_completion_placeholder()
            return
        word = random.choice(valid_words)
        # 随机选择缺失位置
        valid_pos = [i for i in range(len(word))]
        pos = random.choice(valid_pos)
        missing_char = word[pos]

        self.clear_word_completion_layout()

        # 使用自定义多邻国风格控件
        fill_widget = WordFillWidget(word, pos)
        self.word_completion_layout.addWidget(fill_widget)
        self.current_word_fill_widget = fill_widget

        self.current_word_obj = word
        self.current_word_missing = missing_char
        ph = phonetic_dict.get(word, ""); self.word_completion_meaning_label.setText(f"{word} {ph}\n释义：{self.word_lib[word]}")
        self.word_completion_result.setText("")
        if self.current_word_fill_widget:
            self.current_word_fill_widget.input_label.setFocus()

    def _filter_vocab_list(self):
        """词汇年级筛选"""
        grade = self.vocab_grade_combo.currentText()
        self.word_list.clear()
        for item in self.words:
            if len(item) >= 3:
                word, meaning, word_grade = item[0], item[1], item[2]
            elif len(item) >= 2:
                word, meaning = item[0], item[1]
                word_grade = ""
            else:
                continue
            if grade == "\u5168\u90e8" or word_grade == grade:
                ph = phonetic_dict.get(word, "")
                self.word_list.addItem(f"{word} {ph} - {meaning}")

    def _filter_phrase_list(self):
        """短语年级筛选"""
        grade = self.phrase_grade_combo.currentText()
        self.phrase_list.clear()
        for en, zh in self.phrases:
            if grade == "\u5168\u90e8":
                self.phrase_list.addItem(f"{en} - {zh}")
            else:
                # 短语无年级字段，全部显示
                self.phrase_list.addItem(f"{en} - {zh}")

    def _filter_dialogue_list(self):
        """对话年级筛选"""
        grade = self.dialogue_grade_combo.currentText()
        self.dialogue_list.clear()
        for d in self.dialogues:
            d_grade = d.get("grade", "")
            if grade == "\u5168\u90e8" or d_grade == grade or d_grade == "":
                self.dialogue_list.addItem(d.get("title", ""))

    def check_word_completion(self):
        if self.current_word_obj is None:
            QMessageBox.warning(self, "提示", "请先点击「下一个单词」开始练习")
            return
        if self.current_word_fill_widget is None:
            return
        user = self.current_word_fill_widget.user_input.strip()
        if not user:
            self.word_completion_result.setText("请输入缺失的字母")
            self.word_completion_result.setStyleSheet("color: orange;")
            return
        if user.lower() == self.current_word_missing.lower():
            self.word_completion_result.setText("✅ 正确！")
            self.word_completion_result.setStyleSheet("color: green;")
            # 朗读完整单词 + 鼓励语
            full_word = str(self.current_word_obj) if hasattr(self.current_word_obj, '__str__') else str(self.current_word_obj)
            self.speak(f"{full_word}. Correct! Very good!")
            self.word_streak += 1
            self.total_word_correct += 1
            self._check_star_award("word")
            self._update_reward_display()
        else:
            self.word_completion_result.setText(f"❌ 错误，正确答案是：{self.current_word_missing}")
            self.word_completion_result.setStyleSheet("color: red;")
            # 朗读正确答案 + 鼓励语
            full_word = str(self.current_word_obj) if hasattr(self.current_word_obj, '__str__') else str(self.current_word_obj)
            self.speak(f"Wrong! The answer is {full_word}. Keep trying, you can do it!")
            self.word_streak = 0
            self._update_reward_display()

    # ---------- 单词数据操作 ----------
    def save_word_lib(self):
        with open(self.word_lib_path, "w", encoding="utf-8") as f:
            for w, m in self.word_lib.items():
                f.write(f"{w} {m}\n")

    def save_word_review_records(self):
        with open(self.word_review_path, "wb") as f:
            pickle.dump(self.word_review_records, f)

    def update_word_list(self):
        self.word_list.clear()
        for w, m in self.word_lib.items():
            ph = phonetic_dict.get(w, ""); self.word_list.addItem(f"{w} {ph} - {m}")

    def update_word_review_tip(self):
        today = datetime.now().date()
        need = sum(1 for r in self.word_review_records if r["next_review_date"] <= today)
        self.word_review_tip.setText(f"📚 今日需复习单词 {need} 个，请点击「开始复习」" if need else "✅ 今日暂无待复习单词")

    def import_word_lib(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择单词文件", "", "TXT (*.txt)")
        if path:
            with open(path, "r", encoding="utf-8") as f:
                cnt = 0
                for line in f:
                    line = line.strip()
                    if line and " " in line:
                        w, m = line.split(" ", 1)
                        if w not in self.word_lib:
                            self.word_lib[w] = m
                            cnt += 1
            self.save_word_lib()
            self.update_word_list()
            QMessageBox.information(self, "完成", f"导入 {cnt} 个新单词")

    def export_word_lib(self):
        if not self.word_lib:
            QMessageBox.warning(self, "错误", "词库为空")
            return
        path, _ = QFileDialog.getSaveFileName(self, "保存词库", "word_lib", "TXT (*.txt)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                for w, m in self.word_lib.items():
                    f.write(f"{w} {m}\n")
            QMessageBox.information(self, "成功", "导出完成")

    def add_word(self):
        w = self.word_input.text().strip()
        m = self.meaning_input.text().strip()
        if not w or not m:
            QMessageBox.warning(self, "提示", "请填写完整")
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
        w = cur.text().split(" - ")[0]
        # 检查是否为内置词汇
        builtin_words = {item[0] for item in BUILTIN_WORD_LIST}
        if w in builtin_words:
            QMessageBox.warning(self, "禁止删除", f"「{w}」是系统内置词汇，不能删除！\n如需练习请使用「随机抽查」或「单词补全」。")
            return
        if QMessageBox.question(self, "确认", f"删除 {w} ?") == QMessageBox.Yes:
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
            QMessageBox.information(self, "完成", f"{self.current_review_word['word']} 已完成复习周期")
            self.save_word_review_records()
            self.update_word_review_tip()
            self.start_word_review()
            return
        self.save_word_review_records()
        self.update_word_review_tip()
        QMessageBox.information(self, "复习", f"{self.current_review_word['word']} 未掌握，{REVIEW_CYCLES[idx+1]} 天后再次复习")
        self.start_word_review()

    # ---------- 短语模块 ----------
    def setup_phrase_module(self):
        self.phrase_sub_tabs = QTabWidget()
        layout = QVBoxLayout(self.phrase_tab)
        layout.addWidget(self.phrase_sub_tabs)

        self.phrase_manage = QWidget()
        self.phrase_random = QWidget()
        self.phrase_review = QWidget()
        self.phrase_completion = QWidget()

        self.phrase_sub_tabs.addTab(self.phrase_manage, "短语库管理")
        self.phrase_sub_tabs.addTab(self.phrase_random, "随机抽查 + 双向默写")
        self.phrase_sub_tabs.addTab(self.phrase_review, "记忆曲线复习")
        self.phrase_sub_tabs.addTab(self.phrase_completion, "✏️ 短语补全 (内嵌填空)")

        self.setup_phrase_manage_tab()
        self.setup_phrase_random_tab()
        self.setup_phrase_review_tab()
        self.setup_phrase_completion_tab()

    def setup_phrase_manage_tab(self):
        layout = QVBoxLayout(self.phrase_manage)
        layout.setContentsMargins(30, 20, 30, 20)

        btn_layout = QHBoxLayout()
        self.phrase_import_btn = QPushButton("导入短语(TXT)")
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
        self.phrase_input.setPlaceholderText("短语（英文）")
        self.phrase_meaning_input = QLineEdit()
        self.phrase_meaning_input.setPlaceholderText("中文释义")
        for inp in (self.phrase_input, self.phrase_meaning_input):
            inp.setStyleSheet("padding: 8px 10px; border: 1px solid #e0e0e0; border-radius: 6px;")
        input_layout.addWidget(self.phrase_input)
        input_layout.addWidget(self.phrase_meaning_input)
        layout.addLayout(input_layout)
        layout.addSpacing(15)

        # 年级筛选下拉框
        self.phrase_grade_combo = QComboBox()
        self.phrase_grade_combo.addItems(["\u5168\u90e8", "\u4e03\u5e74\u7ea7\u4e0a\u518c", "\u4e03\u5e74\u7ea7\u4e0b\u518c",
                                          "\u516b\u5e74\u7ea7\u4e0a\u518c", "\u516b\u5e74\u7ea7\u4e0b\u518c", "\u4e5d\u5e74\u7ea7"])
        self.phrase_grade_combo.setFont(QFont("Microsoft YaHei", 11))
        self.phrase_grade_combo.currentTextChanged.connect(self._filter_phrase_list)
        grade_h = QHBoxLayout()
        grade_h.addWidget(QLabel("\u5e74\u7ea7\uff1a"))
        grade_h.addWidget(self.phrase_grade_combo)
        grade_h.addStretch()
        layout.addLayout(grade_h)
        layout.addSpacing(8)

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
        phrase = item.text().split(" - ")[0]
        self.speak(phrase)

    def setup_phrase_random_tab(self):
        layout = QVBoxLayout(self.phrase_random)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)

        mode_layout = QHBoxLayout()
        mode_layout.addStretch()
        mode_label = QLabel("默写模式：")
        mode_label.setFont(self.font)
        self.phrase_mode_en2zh = QRadioButton("英译中 (显示英文短语，输入中文)")
        self.phrase_mode_zh2en = QRadioButton("中译英 (显示中文，输入英文短语)")
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

        self.phrase_card = QLabel("点击开始抽查")
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
        self.phrase_start_btn = QPushButton("开始抽查")
        self.phrase_show_btn = QPushButton("查看释义")
        self.phrase_speak_btn = QPushButton("🔊 朗读完整短语")
        self.phrase_mastered_btn = QPushButton("已掌握")
        self.phrase_unmastered_btn = QPushButton("未掌握")
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

        line = QLabel("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        line.setAlignment(Qt.AlignCenter)
        line.setStyleSheet("color: #cccccc;")
        layout.addWidget(line)
        layout.addSpacing(15)

        dict_title = QLabel("📝 默写模式：根据上方内容输入答案，系统自动验证")
        dict_title.setFont(self.font)
        dict_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(dict_title)
        layout.addSpacing(10)

        input_row = QHBoxLayout()
        input_row.setSpacing(15)
        self.phrase_dict_input = QLineEdit()
        self.phrase_dict_input.setPlaceholderText("在这里输入答案...")
        self.phrase_dict_input.setStyleSheet("padding: 10px; border: 1px solid #e0e0e0; border-radius: 6px; font-size: 14px;")
        self.phrase_dict_check = QPushButton("验证答案")
        self.phrase_dict_next = QPushButton("下一个短语")
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
                self.phrase_dict_input.setPlaceholderText("请输入对应的中文释义...")
            else:
                self.phrase_dict_input.setPlaceholderText("请输入对应的英文短语...")

    def start_phrase_random(self):
        if not self.phrase_lib:
            QMessageBox.warning(self, "提示", "短语库为空，请先通过「短语库管理」导入或添加短语")
            return
        multi_word_phrases = [p for p in self.phrase_lib.keys() if " " in p]
        if not multi_word_phrases:
            reply = QMessageBox.question(self, "修复短语库", 
                                         "当前短语库中没有完整的短语（包含空格）。是否从系统内置短语库中恢复？（这将添加约120个常用短语，不会删除您已有的单词）",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                added = 0
                for phrase, meaning in BUILTIN_PHRASE_LIST:
                    if phrase not in self.phrase_lib:
                        self.phrase_lib[phrase] = meaning
                        added += 1
                self.save_phrase_lib()
                self.update_phrase_list()
                QMessageBox.information(self, "修复完成", f"已添加 {added} 个新短语。现在可以正常抽查了。")
                multi_word_phrases = [p for p in self.phrase_lib.keys() if " " in p]
                if not multi_word_phrases:
                    QMessageBox.warning(self, "错误", "内置短语库也没有完整短语？请检查程序。")
                    return
            else:
                QMessageBox.warning(self, "提示", "没有可用的完整短语，随机抽查无法继续。请通过“短语库管理”添加包含空格的短语。")
                return
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
            self.phrase_dict_input.setPlaceholderText("请输入对应的中文释义...")
        else:
            self.phrase_dict_input.setPlaceholderText("请输入对应的英文短语...")

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
            QMessageBox.warning(self, "提示", "请先开始抽查")
            return
        user = self.phrase_dict_input.text().strip()
        if not user:
            self.phrase_dict_result.setText("请输入答案")
            self.phrase_dict_result.setStyleSheet("color: orange;")
            return
        def clean(s):
            return re.sub(r'[^\w\u4e00-\u9fff]', '', s).lower()
        if self.phrase_mode_en2zh.isChecked():
            correct = self.phrase_lib[self.current_phrase]
            correct = re.sub(r'[a-zA-Z\s]', '', correct)
            if clean(user) == clean(correct):
                self.phrase_dict_result.setText("✅ 正确！")
                self.phrase_streak += 1
                self.total_phrase_correct += 1
                self._check_star_award("phrase")
                self._update_reward_display()
                self.phrase_dict_result.setStyleSheet("color: green;")
            else:
                self.phrase_dict_result.setText(f"❌ 错误，正确答案：{correct}")
                self.phrase_streak = 0
                self._update_reward_display()
                self.phrase_dict_result.setStyleSheet("color: red;")
        else:
            correct = self.current_phrase
            if clean(user) == clean(correct):
                self.phrase_dict_result.setText("✅ 正确！")
                self.phrase_streak += 1
                self.total_phrase_correct += 1
                self._check_star_award("phrase")
                self._update_reward_display()
                self.phrase_dict_result.setStyleSheet("color: green;")
            else:
                self.phrase_dict_result.setText(f"❌ 错误，正确答案：{correct}")
                self.phrase_streak = 0
                self._update_reward_display()
                self.phrase_dict_result.setStyleSheet("color: red;")

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
        QMessageBox.information(self, "提示", f"{phrase} 已加入复习队列")
        self.next_phrase_dictation()

    def setup_phrase_review_tab(self):
        layout = QVBoxLayout(self.phrase_review)
        layout.setContentsMargins(30, 20, 30, 20)

        self.phrase_review_tip = QLabel()
        self.phrase_review_tip.setFont(self.font)
        self.phrase_review_tip.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.phrase_review_tip)

        self.phrase_review_card = QLabel("点击开始复习")
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
        self.phrase_review_start_btn = QPushButton("开始复习")
        self.phrase_review_show_btn = QPushButton("查看释义")
        self.phrase_review_speak_btn = QPushButton("🔊 朗读完整短语")
        self.phrase_review_mastered_btn = QPushButton("已掌握")
        self.phrase_review_unmastered_btn = QPushButton("未掌握")
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

    # ---------- 短语补全新功能（内嵌填空，间距优化）----------
    def setup_phrase_completion_tab(self):
        main_layout = QVBoxLayout(self.phrase_completion)
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(20)

        title = QLabel("✏️ 短语补全练习 (内嵌填空)")
        title.setFont(self.title_font)
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

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
        self.phrase_completion_next_btn = QPushButton("下一个短语")
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
        label = QLabel("点击「下一个短语」开始练习")
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
            QMessageBox.warning(self, "提示", "短语库为空")
            self.show_phrase_completion_placeholder()
            return
        multi_word_phrases = [p for p in self.phrase_lib.keys() if " " in p]
        if not multi_word_phrases:
            QMessageBox.warning(self, "提示", "没有找到可用的完整短语（含空格）用于补全练习。请添加类似「be good at」的短语。")
            self.show_phrase_completion_placeholder()
            return
        # 过滤掉只含一个词的短语
        valid_phrases = [p for p in multi_word_phrases if len(p.split()) > 1]
        if not valid_phrases:
            QMessageBox.warning(self, "提示", "短语补全需要至少包含2个单词的短语（如 be good at）")
            self.show_phrase_completion_placeholder()
            return
        phrase = random.choice(valid_phrases)
        words = phrase.split()
        pos = random.randint(0, len(words)-1)
        missing_word = words[pos]

        self.clear_phrase_completion_layout()

        # 使用自定义多邻国风格控件（字母级填空）
        fill_widget = PhraseFillWidget(phrase, pos, words, missing_word)
        self.phrase_completion_layout.addWidget(fill_widget)
        self.current_phrase_fill_widget = fill_widget

        self.current_phrase_obj = phrase
        self.current_phrase_missing = missing_word  # 整个缺失单词（保留用于显示）
        self.phrase_completion_meaning_label.setText(f"释义：{self.phrase_lib[phrase]}")
        self.phrase_completion_result.setText("")
        if hasattr(fill_widget, 'input_label'):
            fill_widget.input_label.setFocus()

    def check_phrase_completion(self):
        if self.current_phrase_obj is None:
            QMessageBox.warning(self, "提示", "请先点击「下一个短语」开始练习")
            return
        if self.current_phrase_fill_widget is None:
            return
        user = self.current_phrase_fill_widget.user_input.strip()
        if not user:
            self.phrase_completion_result.setText("请输入缺失的单词")
            self.phrase_completion_result.setStyleSheet("color: orange;")
            return
        if user.lower() == getattr(self, 'current_phrase_missing', '').lower():
            self.phrase_completion_result.setText("✅ 正确！")
            self.phrase_completion_result.setStyleSheet("color: green;")
            # 朗读完整短语 + 鼓励语
            phrase = str(self.current_phrase_obj) if self.current_phrase_obj else ""
            self.speak(f"{phrase}. Correct! Very good!")
        else:
            correct = getattr(self, 'current_phrase_missing', self.current_phrase_missing)
            self.phrase_completion_result.setText(f"❌ 错误，正确答案是：{correct}")
            self.phrase_completion_result.setStyleSheet("color: red;")
            # 朗读完整短语 + 鼓励语
            phrase = str(self.current_phrase_obj) if self.current_phrase_obj else ""
            self.speak(f"Wrong! The answer is {phrase}. Keep trying, you can do it!")

    # ---------- 短语数据操作 ----------
    def import_phrase_lib(self):
        path, _ = QFileDialog.getOpenFileName(self, "导入短语", "", "TXT (*.txt)")
        if path:
            with open(path, "r", encoding="utf-8") as f:
                cnt = 0
                for line in f:
                    line = line.strip()
                    if line and " " in line:
                        p, m = line.split(" ", 1)
                        if p not in self.phrase_lib:
                            self.phrase_lib[p] = m
                            cnt += 1
            self.save_phrase_lib()
            self.update_phrase_list()
            QMessageBox.information(self, "成功", f"导入 {cnt} 个短语")

    def export_phrase_lib(self):
        if not self.phrase_lib:
            QMessageBox.warning(self, "错误", "短语库为空")
            return
        path, _ = QFileDialog.getSaveFileName(self, "导出短语", "phrase_lib", "TXT (*.txt)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                for p, m in self.phrase_lib.items():
                    f.write(f"{p} {m}\n")
            QMessageBox.information(self, "成功", "导出完成")

    def add_phrase(self):
        p = self.phrase_input.text().strip()
        m = self.phrase_meaning_input.text().strip()
        if not p or not m:
            QMessageBox.warning(self, "提示", "请填写短语和释义")
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
        builtin_phrases = {item.get('en', '') for item in BUILTIN_PHRASE_LIST}
        if p in builtin_phrases:
            QMessageBox.warning(self, "禁止删除", f"「{p}」是系统内置短语，不能删除！\n如需练习请使用「随机抽查」或「短语补全」。")
            return
        if QMessageBox.question(self, "确认", f"删除短语 {p} ?") == QMessageBox.Yes:
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
            QMessageBox.information(self, "完成", f"{self.current_review_phrase['word']} 已完成复习")
            self.save_phrase_review_records()
            self.update_phrase_review_tip()
            self.start_phrase_review()
            return
        self.save_phrase_review_records()
        self.update_phrase_review_tip()
        QMessageBox.information(self, "复习", f"{self.current_review_phrase['word']} 未掌握，{REVIEW_CYCLES[idx+1]} 天后复习")
        self.start_phrase_review()

    def save_phrase_lib(self):
        with open(self.phrase_lib_path, "w", encoding="utf-8") as f:
            for p, m in self.phrase_lib.items():
                f.write(f"{p} {m}\n")

    def save_phrase_review_records(self):
        with open(self.phrase_review_path, "wb") as f:
            pickle.dump(self.phrase_review_records, f)

    def update_phrase_list(self):
        self.phrase_list.clear()
        for p, m in self.phrase_lib.items():
            self.phrase_list.addItem(f"{p} - {m}")

    def update_phrase_review_tip(self):
        today = datetime.now().date()
        need = sum(1 for r in self.phrase_review_records if r["next_review_date"] <= today)
        self.phrase_review_tip.setText(f"📖 今日需复习短语 {need} 个，请点击「开始复习」" if need else "✅ 今日暂无待复习短语")

    # ---------- 口语对话模块 ----------
    def setup_dialogue_module(self):
        # 使用子标签结构（与单词、短语模块一致）
        self.dialogue_sub_tabs = QTabWidget()
        layout = QVBoxLayout(self.dialogue_tab)
        layout.addWidget(self.dialogue_sub_tabs)

        self.dialogue_manage = QWidget()
        self.dialogue_random = QWidget()
        self.dialogue_completion = QWidget()

        self.dialogue_sub_tabs.addTab(self.dialogue_manage, "对话管理")
        self.dialogue_sub_tabs.addTab(self.dialogue_random, "随机学习")
        self.dialogue_sub_tabs.addTab(self.dialogue_completion, "✏️ 对话补全练习")

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
        """对话管理子标签（原有功能）"""
        layout = QVBoxLayout(self.dialogue_manage)
        layout.setContentsMargins(30, 20, 30, 20)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        self.dialogue_import_btn = QPushButton("导入对话")
        self.dialogue_export_btn = QPushButton("导出对话")
        self.dialogue_add_btn = QPushButton("添加对话")
        self.dialogue_del_btn = QPushButton("删除选中")
        self.dialogue_speak_btn = QPushButton("🔊 朗读英文对话")
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

        # 年级筛选下拉框
        self.dialogue_grade_combo = QComboBox()
        self.dialogue_grade_combo.addItems(["\u5168\u90e8", "\u4e03\u5e74\u7ea7\u4e0a\u518c", "\u4e03\u5e74\u7ea7\u4e0b\u518c",
                                          "\u516b\u5e74\u7ea7\u4e0a\u518c", "\u516b\u5e74\u7ea7\u4e0b\u518c", "\u4e5d\u5e74\u7ea7"])
        self.dialogue_grade_combo.setFont(QFont("Microsoft YaHei", 11))
        self.dialogue_grade_combo.currentTextChanged.connect(self._filter_dialogue_list)
        grade_h = QHBoxLayout()
        grade_h.addWidget(QLabel("\u5e74\u7ea7\uff1a"))
        grade_h.addWidget(self.dialogue_grade_combo)
        grade_h.addStretch()
        layout.addLayout(grade_h)
        layout.addSpacing(8)

        splitter = QSplitter(Qt.Horizontal)
        # 对话列表：QListWidget（显示英文标题）
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

        # 右侧面板：英文 | 中文 左右分栏
        right_widget = QWidget()
        right_layout = QHBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(10)

        en_widget = QWidget()
        en_layout = QVBoxLayout(en_widget)
        en_layout.setContentsMargins(0, 0, 0, 0)
        self.dialogue_en_text = QTextEdit()
        self.dialogue_en_text.setReadOnly(True)
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
        self.dialogue_zh_text.setFont(QFont("微软雅黑", 12))
        self.dialogue_zh_text.setStyleSheet("border: 1px solid #ddd; border-radius: 6px; padding: 8px;")
        zh_layout.addWidget(QLabel("中文:"))
        zh_layout.addWidget(self.dialogue_zh_text)
        right_layout.addWidget(zh_widget)

        splitter.addWidget(right_widget)
        layout.addWidget(splitter, 1)

        # 底部按钮行（已在上面创建）
        # btn_layout 已在上方定义

    def _setup_dialogue_random_tab(self):
        """随机学习子Tab：左侧选场景，右侧显示英文+中文"""
        layout = QVBoxLayout(self.dialogue_random)
        layout.setContentsMargins(10, 10, 10, 10)
        
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：场景列表
        self.dlg_random_list = QListWidget()
        self.dlg_random_list.setFont(self.font)
        self.dlg_random_list.currentRowChanged.connect(self._show_random_dialogue)
        splitter.addWidget(self.dlg_random_list)
        
        # 右侧：英文+中文显示
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        self.dlg_random_en = QTextEdit()
        self.dlg_random_en.setReadOnly(True)
        self.dlg_random_en.setFont(QFont("微软雅黑", 14))
        right_layout.addWidget(self.dlg_random_en)
        
        self.dlg_random_zh = QTextEdit()
        self.dlg_random_zh.setReadOnly(True)
        self.dlg_random_zh.setFont(QFont("微软雅黑", 14))
        right_layout.addWidget(self.dlg_random_zh)
        
        splitter.addWidget(right_widget)
        layout.addWidget(splitter, 1)

        # 随机学习Tab朗读按钮
        speak_btn_row = QHBoxLayout()
        speak_btn_row.addStretch()
        self.dlg_random_speak_btn = QPushButton("\U0001f50a 朗读英文")
        self.dlg_random_speak_btn.setFont(QFont("微软雅黑", 12))
        self.dlg_random_speak_btn.setStyleSheet("""
            QPushButton { background-color: #5cb85c; color: white; padding: 8px 20px;
                          border-radius: 6px; border: none; }
            QPushButton:hover { background-color: #449d44; }
        """)
        self.dlg_random_speak_btn.clicked.connect(self._speak_random_dialogue)
        speak_btn_row.addWidget(self.dlg_random_speak_btn)
        layout.addLayout(speak_btn_row)

        # 填充列表
        for d in self.dialogues:
            self.dlg_random_list.addItem(d.get('title', ''))

    def _show_random_dialogue(self, idx):
        """显示选中的对话"""
        if 0 <= idx < len(self.dialogues):
            d = self.dialogues[idx]
            self.dlg_random_en.setText(d.get('en', ''))
            self.dlg_random_zh.setText(d.get('zh', ''))

    def _setup_dialogue_completion_tab(self):
        """对话补全练习子Tab"""
        layout = QVBoxLayout(self.dialogue_completion)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 顶部标题行
        header = QHBoxLayout()
        self.dlg_comp_title = QLabel("✏️ 对话补全")
        self.dlg_comp_title.setFont(QFont("微软雅黑", 14, QFont.Bold))
        header.addWidget(self.dlg_comp_title)
        self.dlg_comp_scenario = QLabel("")
        self.dlg_comp_scenario.setFont(QFont("微软雅黑", 11))
        header.addWidget(self.dlg_comp_scenario)
        header.addStretch()
        layout.addLayout(header)
        
        # 中英文显示区
        comp_splitter = QSplitter(Qt.Horizontal)
        
        # 英文区
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
        
        # 中文区
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
        self.dlg_comp_zh_panel.setFont(QFont("微软雅黑", 15))
        self.dlg_comp_zh_panel.setWordWrap(True)
        self.dlg_comp_zh_panel.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.dlg_comp_zh_panel.setStyleSheet("padding: 8px;")
        self.dlg_comp_zh_area.setWidget(self.dlg_comp_zh_panel)
        zh_layout.addWidget(self.dlg_comp_zh_area)
        comp_splitter.addWidget(zh_container)
        
        layout.addWidget(comp_splitter, 1)
        
        # 底部：结果+按钮
        bottom = QHBoxLayout()
        self.dlg_comp_result = QLabel("")
        self.dlg_comp_result.setFont(QFont("微软雅黑", 11))
        self.dlg_comp_result.setStyleSheet("color: #666;")
        bottom.addWidget(self.dlg_comp_result)
        bottom.addStretch()
        
        hint = QLabel("填写完整英文句子 → 验证")
        hint.setFont(QFont("微软雅黑", 10))
        hint.setStyleSheet("color: #999;")
        bottom.addWidget(hint)
        
        self.dlg_comp_check_btn = QPushButton("✅验证")
        self.dlg_comp_check_btn.setFont(QFont("微软雅黑", 11))
        self.dlg_comp_check_btn.clicked.connect(self._check_dialogue_completion)
        bottom.addWidget(self.dlg_comp_check_btn)
        
        self.dlg_comp_next_btn = QPushButton("下一个")
        self.dlg_comp_next_btn.setFont(QFont("微软雅黑", 11))
        self.dlg_comp_next_btn.clicked.connect(self._next_dialogue_completion)
        bottom.addWidget(self.dlg_comp_next_btn)
        self.dlg_comp_speak_btn = QPushButton("🔊 朗读")
        self.dlg_comp_speak_btn.setFont(QFont("微软雅黑", 11))
        self.dlg_comp_speak_btn.setStyleSheet("""
            QPushButton { background-color: #5cb85c; color: white; padding: 6px 15px;
                          border-radius: 6px; border: none; }
            QPushButton:hover { background-color: #449d44; }
        """)
        self.dlg_comp_speak_btn.clicked.connect(self._speak_comp_dialogue)
        bottom.addWidget(self.dlg_comp_speak_btn)
        
        layout.addLayout(bottom)
        
        # 初始化
        self._current_dlg_idx = 0
        self._current_dlg_missing_idx = 0
        self._next_dialogue_completion()

    def _next_dialogue_completion(self):
        """生成下一个对话补全练习 - 根据篇幅挖空多句"""
        import random
        if not self.dialogues:
            return
        
        # 随机选对话
        self._current_dlg_idx = random.randint(0, len(self.dialogues) - 1)
        dlg = self.dialogues[self._current_dlg_idx]
        
        # 更新标题
        self.dlg_comp_scenario.setText(dlg.get('title', ''))
        
        # 清空旧内容
        while self.dlg_comp_en_layout.count():
            item = self.dlg_comp_en_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 解析对话行
        en_text = dlg.get('en', '')
        lines = en_text.splitlines()
        
        # 获取非空行
        non_empty_lines = [i for i, l in enumerate(lines) if l.strip()]
        if not non_empty_lines:
            return
        
        # 根据篇幅决定挖空数量
        total_lines = len(non_empty_lines)
        if total_lines <= 3:
            blank_count = 1  # 短对话挖1句
        elif total_lines <= 6:
            blank_count = random.choice([1, 2])  # 中等挖1-2句
        elif total_lines <= 10:
            blank_count = random.choice([2, 3])  # 较长挖2-3句
        else:
            blank_count = random.choice([3, 4])  # 长对话挖3-4句
        
        # 随机选择要挖空的行（不重复）
        blank_indices = sorted(random.sample(non_empty_lines, min(blank_count, total_lines)))
        
        # 存储正确答案: {行号: 完整句子}
        self._missing_sentences = {}
        for idx in blank_indices:
            self._missing_sentences[idx] = lines[idx].strip()
        
        # 显示所有行
        font_size = 15
        line_font = QFont("微软雅黑", font_size)
        self.dlg_comp_inputs = []  # 存储所有输入框以便验证
        
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            
            if i in self._missing_sentences:
                # 挖空行 - 显示输入框
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(4, 8, 4, 8)
                
                # 行前缀标签 (如 "Tom:" 或 "Lucy:")
                stripped = line.strip()
                prefix = ""
                for p in ["Tom:", "Lucy:", "C:", "D:", "A：", "B：", "C：", "D："]:
                    if stripped.startswith(p):
                        prefix = p
                        break
                
                if prefix:
                    pref_lbl = QLabel(prefix)
                    pref_lbl.setFont(line_font)
                    pref_lbl.setStyleSheet("color: #333; padding-right: 6px;")
                    row_layout.addWidget(pref_lbl)
                
                # 输入框 - 填完整句
                inp = QLineEdit()
                inp.setFont(line_font)
                inp.setPlaceholderText("请填写完整的英文句子...")
                inp.setMinimumHeight(40)
                inp.setStyleSheet("""
                    QLineEdit {
                        color: #1cb0f6;
                        background: transparent;
                        border: none;
                        border-bottom: 3px solid #1cb0f6;
                        padding: 4px 8px;
                    }
                """)
                row_layout.addWidget(inp, 1)
                self.dlg_comp_inputs.append(inp)
                
                self.dlg_comp_en_layout.addWidget(row_widget)
            else:
                # 普通行 - 正常显示
                lbl = QLabel(line)
                lbl.setFont(line_font)
                lbl.setWordWrap(True)
                lbl.setStyleSheet("padding: 6px 4px; color: #333;")
                self.dlg_comp_en_layout.addWidget(lbl)
        
        self.dlg_comp_en_layout.addStretch()
        
        # 显示中文
        self.dlg_comp_zh_panel.setText(dlg.get('zh', ''))
        self.dlg_comp_result.setText("")
        # 聚焦到第一个输入框
        if self.dlg_comp_inputs:
            self.dlg_comp_inputs[0].setFocus()


    def _check_dialogue_completion(self):
        """验证答案 - 检查所有挖空句子"""
        import re
        
        if not hasattr(self, '_missing_sentences') or not hasattr(self, 'dlg_comp_inputs'):
            return
        
        # 标准化比较：忽略大小写、标点、多余空格
        def normalize(s):
            s = s.lower()
            s = re.sub(r'[^\w\s]', '', s)  # 去标点
            s = re.sub(r'\s+', ' ', s).strip()  # 合并空格
            return s
        
        # 收集所有答案
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
        
        # 显示结果
        total = len(results)
        correct_count = sum(results)
        
        if correct_count == total:
            self.dlg_comp_result.setText(f"✅ 全部正确！({correct_count}/{total})")
            self.dlg_comp_result.setStyleSheet("color: green; font-size: 14px; font-weight: bold;")
            self.dialogue_streak += 1
            self.total_dialogue_correct += 1
            self._check_star_award("dialogue")
            self._update_reward_display()
        else:
            # 显示所有正确答案
            correct_texts = list(self._missing_sentences.values())
            # 只显示前3个正确答案，避免过长
            display_texts = correct_texts[:3]
            more = f" 等{len(correct_texts)}句" if len(correct_texts) > 3 else ""
            self.dlg_comp_result.setText(f"❌ {correct_count}/{total} 正确。正确答案: {', '.join(display_texts)}{more}")
            self.dlg_comp_result.setStyleSheet("color: red; font-size: 13px;")
            self.dialogue_streak = 0
            self._update_reward_display()
            self.speak("Try again. Keep practicing!")


    def display_dialogue(self):
        """显示选中的对话（管理Tab）"""
        idx = self.dialogue_list.currentRow()
        if 0 <= idx < len(self.dialogues):
            d = self.dialogues[idx]
            self.dialogue_en_text.setText(d.get('en', ''))
            self.dialogue_zh_text.setText(d.get('zh', ''))

    def add_dialogue(self):
        """添加对话"""
        QMessageBox.information(self, "提示", "添加对话功能暂未开放")

    def delete_dialogue(self):
        """删除对话（禁用）"""
        QMessageBox.information(self, "提示", "口语对话只能查看，不能删除")

    def import_dialogues(self):
        """导入对话"""
        QMessageBox.information(self, "提示", "导入功能暂未开放")

    def export_dialogues(self):
        """导出对话"""
        QMessageBox.information(self, "提示", "导出功能暂未开放")

    def speak_dialogue(self):
        """朗读对话（管理Tab）"""
        idx = self.dialogue_list.currentRow()
        if 0 <= idx < len(self.dialogues):
            d = self.dialogues[idx]
            self.speak(d.get('en', ''))

    def _speak_random_dialogue(self):
        """朗读随机学习Tab的当前对话"""
        idx = getattr(self, 'dlg_random_list', None)
        if idx is not None:
            idx = idx.currentRow()
        if idx is not None and 0 <= idx < len(self.dialogues):
            d = self.dialogues[idx]
            self.speak(d.get('en', ''))

    def _speak_comp_dialogue(self):
        """朗读补全练习Tab的英文内容（从当前对话数据读取）"""
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
        layout = QVBoxLayout(self.grammar_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        grade_layout = QHBoxLayout()
        grade_label = QLabel('选择年级：')
        grade_label.setFont(QFont('微软雅黑', 12))
        self.grade_combo = QComboBox()
        self.grade_combo.addItems(['七年级上册', '七年级下册', '八年级上册', '八年级下册', '九年级'])
        self.grade_combo.setFont(QFont('微软雅黑', 12))
        self.grade_combo.currentTextChanged.connect(self._load_grammar_list)
        grade_layout.addWidget(grade_label)
        grade_layout.addWidget(self.grade_combo)
        grade_layout.addStretch()
        layout.addLayout(grade_layout)
        self.grammar_list = QListWidget()
        self.grammar_list.setFont(QFont('微软雅黑', 13))
        self.grammar_list.itemClicked.connect(self._show_grammar_detail)
        self.grammar_detail = QTextEdit()
        self.grammar_detail.setReadOnly(True)
        self.grammar_detail.setFont(QFont('微软雅黑', 14))
        self.grammar_detail.setStyleSheet("QTextEdit {background-color:white;border:1px solid #ddd;border-radius:5px;padding:10px;}")
        splitter = QSplitter(Qt.Horizontal)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.grammar_list)
        splitter.addWidget(left_widget)
        splitter.addWidget(self.grammar_detail)
        splitter.setSizes([300, 700])
        layout.addWidget(splitter)
        self._load_grammar_list()

    def _load_grammar_list(self):
        self.grammar_list.clear()
        grade = self.grade_combo.currentText()
        if grade in BUILTIN_GRAMMAR:
            for item in BUILTIN_GRAMMAR[grade]:
                self.grammar_list.addItem(item['title'])

    def _show_grammar_detail(self, item):
        grade = self.grade_combo.currentText()
        title = item.text()
        if grade in BUILTIN_GRAMMAR:
            for grammar_item in BUILTIN_GRAMMAR[grade]:
                if grammar_item['title'] == title:
                    self.grammar_detail.setPlainText(grammar_item['content'])
                    break

    def _show_heart_reward(self):
        if self.stars >= 5:
            pass

    def _setup_essay_tab(self):
        layout = QVBoxLayout(self.essay_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("选择类别："))
        self.essay_cat_combo = QComboBox()
        self.essay_cat_combo.addItems(ESSAY_CATEGORIES)
        self.essay_cat_combo.setFont(QFont("微软雅黑", 12))
        top_layout.addWidget(self.essay_cat_combo)
        top_layout.addStretch()
        layout.addLayout(top_layout)
        self.essay_list = QListWidget()
        self.essay_list.setFont(QFont("微软雅黑", 13))
        self.essay_list.itemClicked.connect(self._show_essay_detail)
        layout.addWidget(self.essay_list)
        self.essay_detail = QTextEdit()
        self.essay_detail.setReadOnly(True)
        self.essay_detail.setFont(QFont("微软雅黑", 14))
        self.essay_detail.setStyleSheet("QTextEdit {background-color:#fffde7;border:1px solid #e0e0e0;border-radius:6px;padding:15px;}")
        self.essay_detail.setMinimumHeight(120)
        layout.addWidget(self.essay_detail)
        usage = QLabel("点击左侧句型查看中文释义")
        usage.setStyleSheet("color: #888; font-size: 12px; padding: 5px 0;")
        layout.addWidget(usage)
        self.essay_cat_combo.currentTextChanged.connect(self._load_essay_list)
        self._load_essay_list()

    def _load_essay_list(self):
        self.essay_list.clear()
        cat = self.essay_cat_combo.currentText()
        for p in ESSAY_PHRASES:
            if p["cat"] == cat:
                self.essay_list.addItem(p["en"])

    def _show_essay_detail(self, item):
        en = item.text()
        for p in ESSAY_PHRASES:
            if p["en"] == en:
                zh = p["zh"]
                self.essay_detail.setHtml('<div style="font-size:16px;font-weight:bold;color:#1565c0;margin-bottom:10px;">' + en + '</div><div style="font-size:14px;color:#333;background:#e8f5e9;padding:10px;border-radius:5px;">' + '❤️ ' + zh + '</div>')
                break


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = EnglishLearningTool()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
