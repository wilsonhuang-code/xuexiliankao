#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学练考系统 - Kivy手机APP版
整合自适应训练(数学/物理) + 英语全能学习
"""

import os
import sys
import json
import random
from datetime import datetime, timedelta

# ====== 中文字体注册（必须在kivy import之前） ======
from kivy.core.text import LabelBase
_FONT_DIR = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
_CN_FONT = os.path.join(_FONT_DIR, 'msyh.ttc')
_CN_FONT_BOLD = os.path.join(_FONT_DIR, 'msyhbd.ttc')
if os.path.exists(_CN_FONT):
    LabelBase.register(name='Roboto', fn_regular=_CN_FONT,
                       fn_bold=_CN_FONT_BOLD if os.path.exists(_CN_FONT_BOLD) else _CN_FONT)

import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.uix.switch import Switch
from kivy.uix.checkbox import CheckBox
from kivy.uix.widget import Widget
from kivy.uix.stacklayout import StackLayout
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform
from kivy.properties import StringProperty, NumericProperty, ListProperty

# Window size for mobile
Window.size = (400, 700)

# ==================== 数据目录 ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ==================== 题库 ====================
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

ALL_SUBJECTS = {
    "math": MATH_QUESTIONS,
    "physics": PHYSICS_QUESTIONS,
}

# ==================== 英语词库（精简核心词约2000+） ====================
WORD_LIST = [
    ('able','能够；有能力的','九年级'),('about','关于；大约','七上'),('above','在…上方','七下'),
    ('accept','接受','七上'),('accident','事故','七上'),('achieve','取得；实现','八上'),
    ('across','横过','七上'),('act','行动','七上'),('active','活跃的','七下'),
    ('activity','活动','八上'),('actor','演员','七上'),('actually','实际上','七下'),
    ('add','增加','八下'),('address','地址','七上'),('advice','建议','七上'),
    ('advise','劝告','七上'),('afford','负担得起','七下'),('afraid','害怕的','八下'),
    ('after','在…之后','七下'),('afternoon','下午','七上'),('again','又','七上'),
    ('against','反对','七上'),('age','年龄','七上'),('ago','以前','七上'),
    ('agree','同意','八上'),('air','空气','七上'),('all','全部','七上'),
    ('allow','允许','七上'),('almost','几乎','八上'),('alone','单独的','七下'),
    ('along','沿着','七上'),('already','已经','七上'),('also','也','七上'),
    ('although','虽然','八上'),('always','总是','七上'),('amazing','令人惊异的','八上'),
    ('among','在…之中','七下'),('and','和','七上'),('angry','生气的','七下'),
    ('animal','动物','七上'),('another','另一个','七上'),('answer','回答','七上'),
    ('appear','出现','八上'),('apple','苹果','七上'),('area','区域','七上'),
    ('arm','手臂','七上'),('around','围绕','七上'),('arrive','到达','七上'),
    ('art','艺术','七上'),('article','文章','八上'),('as','作为','七上'),
    ('ask','问','七上'),('asleep','睡着的','七下'),('at','在','七上'),
    ('attend','参加','七上'),('attention','注意力','八下'),('August','八月','七下'),
    ('aunt','伯母','八上'),('autumn','秋天','七下'),('avoid','避免','七上'),
    ('awake','醒来的','七下'),('away','离开','七下'),('baby','婴儿','七上'),
    ('back','后面','七上'),('bad','坏的','七上'),('bag','包','七上'),
    ('ball','球','七下'),('banana','香蕉','七上'),('bank','银行','七下'),
    ('base','基础','七上'),('basic','基本的','七下'),('basket','篮子','七上'),
    ('basketball','篮球','七下'),('bathroom','浴室','七下'),('be','是','七上'),
    ('beach','海滩','七上'),('bear','熊；忍受','八上'),('beautiful','美丽的','七下'),
    ('because','因为','七上'),('become','变成','七上'),('bed','床','七上'),
    ('bedroom','卧室','七下'),('bee','蜜蜂','七上'),('beef','牛肉','七上'),
    ('before','在…之前','七下'),('begin','开始','七下'),('behind','在…后面','七下'),
    ('believe','相信','七上'),('bell','铃','七上'),('belong','属于','七上'),
    ('below','在…下面','七下'),('beside','在…旁边','七下'),('best','最好的','七下'),
    ('better','更好的','七下'),('between','在…之间','七下'),('big','大的','七上'),
    ('bike','自行车','七下'),('bill','账单','七上'),('bird','鸟','七上'),
    ('birth','出生','七上'),('birthday','生日','七上'),('bit','一点','七下'),
    ('black','黑色的','七上'),('blind','盲的','七上'),('block','街区','七上'),
    ('blood','血','七上'),('blow','吹','七上'),('blue','蓝色的','七上'),
    ('board','木板','七上'),('boat','船','七下'),('body','身体','七上'),
    ('book','书','七上'),('boring','无聊的','七下'),('born','出生的','七下'),
    ('borrow','借入','七上'),('boss','老板','七上'),('both','两者都','七下'),
    ('bottle','瓶子','七上'),('bottom','底部','七上'),('bowl','碗','七上'),
    ('box','盒子','七上'),('boy','男孩','七上'),('brain','大脑','七上'),
    ('brave','勇敢的','八下'),('bread','面包','七上'),('break','打破','七上'),
    ('breakfast','早餐','七下'),('bridge','桥','七上'),('bright','明亮的','七下'),
    ('bring','带来','七下'),('brother','兄弟','七上'),('brown','棕色的','七下'),
    ('brush','刷子','七上'),('build','建造','七上'),('building','建筑物','七下'),
    ('burn','燃烧','七上'),('bus','公共汽车','八下'),('business','生意','七上'),
    ('busy','忙碌的','七下'),('but','但是','七上'),('buy','购买','七上'),
    ('by','通过；靠','七下'),('cake','蛋糕','七上'),('call','打电话；称呼','七上'),
    ('camera','照相机','七下'),('camp','营地','七上'),('can','能；罐头','七上'),
    ('candle','蜡烛','七上'),('cap','帽子','七上'),('car','汽车','七上'),
    ('card','卡片','七上'),('care','关心','七上'),('careful','小心的','七上'),
    ('carry','搬运','七上'),('cat','猫','七上'),('catch','抓住','七上'),
    ('cause','原因；引起','八上'),('celebrate','庆祝','八上'),('center','中心','七上'),
    ('century','世纪','七上'),('certain','确定的','七下'),('chair','椅子','七上'),
    ('chance','机会','九年级'),('change','改变','七上'),('character','性格；角色','八上'),
    ('cheap','便宜的','七下'),('check','检查','九年级'),('cheer','欢呼','七上'),
    ('chemistry','化学','七上'),('chess','国际象棋','七下'),('chicken','鸡肉；小鸡','七上'),
    ('child','孩子','七上'),('China','中国','七上'),('Chinese','中国人；汉语','七上'),
    ('choice','选择','七上'),('choose','选择','七上'),('Christmas','圣诞节','七下'),
    ('church','教堂','七上'),('cinema','电影院','七下'),('circle','圆','七上'),
    ('city','城市','七上'),('class','班级；课','七上'),('classmate','同班同学','七下'),
    ('classroom','教室','七上'),('clean','干净的；打扫','七下'),('clear','清晰的；清理','八上'),
    ('clever','聪明的','七下'),('climb','爬','七上'),('clock','时钟','七上'),
    ('close','关闭；接近的','八上'),('clothes','衣服','七上'),('cloud','云','七上'),
    ('club','俱乐部','七下'),('coach','教练','七上'),('coast','海岸','七上'),
    ('coat','外套','七上'),('coffee','咖啡','七上'),('coin','硬币','七上'),
    ('cold','冷的；感冒','七下'),('collect','收集','七上'),('college','大学','七上'),
    ('color','颜色','七上'),('come','来','七上'),('comfortable','舒适的','七下'),
    ('common','普通的','九年级'),('communicate','沟通','七上'),('community','社区','七上'),
    ('company','公司','七上'),('compare','比较','七上'),('competition','比赛','八上'),
    ('complete','完成；完整的','八上'),('computer','电脑','七上'),('concert','音乐会','七下'),
    ('condition','条件','七上'),('confident','自信的','七下'),('connect','连接','七上'),
    ('consider','考虑','八下'),('continue','继续','七上'),('control','控制','七上'),
    ('cook','烹饪；厨师','八上'),('cool','凉爽的；酷','七下'),('copy','复制','七上'),
    ('corner','角落','七上'),('correct','正确的','九年级'),('cost','花费','七上'),
    ('cotton','棉花','七上'),('cough','咳嗽','七上'),('could','可以','七上'),
    ('count','数数','七上'),('country','国家；乡村','七下'),('courage','勇气','七上'),
    ('course','课程；当然','八上'),('cousin','表兄妹','七下'),('cover','覆盖','七上'),
    ('cow','奶牛','七上'),('crazy','疯狂的','七下'),('create','创造','七上'),
    ('cross','穿过','七下'),('cruel','残酷的','七下'),('cry','哭','七上'),
    ('culture','文化','八上'),('cup','杯子','七上'),('cute','可爱的','七下'),
    ('dad','爸爸','七上'),('daily','每日的','七下'),('dance','跳舞','七下'),
    ('danger','危险','八下'),('dangerous','危险的','八下'),('dark','黑暗的','七下'),
    ('date','日期；约会','八上'),('daughter','女儿','七上'),('day','一天','七上'),
    ('dead','死的','七上'),('deaf','聋的','七上'),('deal','处理；交易','八上'),
    ('dear','亲爱的；昂贵的','八下'),('death','死亡','七上'),('decide','决定','八上'),
    ('deep','深的','七上'),('deer','鹿','七上'),('degree','度数；学位','八上'),
    ('good','好的','七上'),('morning','早晨；上午','七下'),('welcome','欢迎','七上'),
    ('to','向；到','七下'),('thank','谢谢','七上'),('you','你；你们','七下'),
    ('hello','你好','七上'),('hi','嗨','七上'),('I','我','七上'),
    ('am','是','七上'),('name','名字','七上'),('what','什么','七上'),
    ('your','你的','七上'),('my','我的','七上'),('nice','令人愉快的','七下'),
    ('meet','遇见','七上'),('too','也；太','七下'),('please','请','七上'),
    ('excuse','原谅','七上'),('me','我（宾格）','八上'),('are','是','七上'),
    ('yes','是的','七上'),('no','不','七上'),('it','它','七上'),
    ('is','是','七上'),('not','不','七上'),('from','来自','七上'),
    ('where','哪里','七上'),('Canada','加拿大','七下'),('the','这/那','七上'),
    ('they','他们','七上'),('he','他','七上'),('she','她','七上'),
    ('who','谁','七上'),('student','学生','七上'),('teacher','老师','七上'),
    ('friend','朋友','七上'),('how','怎样','七上'),('old','老的；...岁','七上'),
    ('number','数字','七上'),('one','一','七上'),('two','二','七上'),
    ('three','三','七上'),('four','四','七上'),('five','五','七上'),
    ('six','六','七上'),('seven','七','七上'),('eight','八','七上'),
    ('nine','九','七上'),('ten','十','七上'),('year','年','七上'),
    ('grade','年级','七上'),('in','在...里面','八上'),('map','地图','七上'),
    ('pen','钢笔','七上'),('pencil','铅笔','七上'),('ruler','尺子','七上'),
    ('desk','书桌','七上'),('school','学校','七上'),('have','有','七上'),
    ('small','小的','七上'),('long','长的','七上'),('short','短的；矮的','七上'),
    ('hair','头发','七上'),('face','脸','七上'),('eye','眼睛','七上'),
    ('ear','耳朵','七上'),('nose','鼻子','七上'),('mouth','嘴巴','七上'),
    ('head','头','七上'),('neck','脖子','七上'),('hand','手','七上'),
    ('leg','腿','七上'),('foot','脚','七上'),('finger','手指','七上'),
    ('favorite','最喜欢的','七下'),('English','英语','七上'),('white','白色','七上'),
    ('pink','粉色','七上'),('red','红色','七上'),('purple','紫色','七上'),
    ('orange','橙色','七上'),('yellow','黄色','七上'),('green','绿色','七上'),
    ('gray','灰色','七上'),('give','给','七上'),('letter','信；字母','七下'),
    ('sorry','抱歉','七上'),('like','喜欢','七上'),('look','看','七下'),
    ('same','相同的','七下'),('tall','高的','七上'),('know','知道','七上'),
    ('new','新的','七上'),('parent','父/母亲','七上'),('mother','母亲','七上'),
    ('father','父亲','七上'),('sister','姐妹','七上'),('grandmother','祖母','七上'),
    ('grandfather','祖父','七上'),('son','儿子','七上'),('uncle','叔叔；舅舅','八上'),
    ('wife','妻子','七上'),('husband','丈夫','七上'),('family','家庭','七下'),
    ('home','家','七下'),('photo','照片','七上'),('picture','图片','七上'),
    ('happy','快乐的','七下'),('sad','悲伤的','七下'),('only','仅仅','七上'),
    ('young','年轻的','七上'),('right','正确的；右边','九年级'),('then','那么；然后','七下'),
    ('work','工作','七上'),('hospital','医院','七下'),('restaurant','餐馆','七上'),
    ('shop','商店','七下'),('office','办公室','七下'),('farm','农场','七上'),
    ('driver','司机','七上'),('farmer','农民','七上'),('nurse','护士','七上'),
    ('doctor','医生','七上'),('worker','工人','七上'),('teach','教','七上'),
    ('drive','驾驶','七上'),('job','工作','七上'),('time','时间','七下'),
    ('half','一半','七下'),('now','现在','七下'),('early','早的','七下'),
    ('late','迟的','七上'),('watch','手表；观看','七下'),('TV','电视','七下'),
    ('kitchen','厨房','七下'),('garden','花园','七上'),('first','第一','七上'),
    ('second','第二','七上'),('third','第三','七上'),('next','下一个','七上'),
    ('today','今天','七下'),('tomorrow','明天','七下'),('Sunday','星期日','七下'),
    ('Monday','星期一','七下'),('Tuesday','星期二','七下'),('Wednesday','星期三','七下'),
    ('Thursday','星期四','七下'),('Friday','星期五','七下'),('Saturday','星期六','七下'),
    ('week','周','七上'),('weekend','周末','七上'),('homework','作业','七上'),
    ('zoo','动物园','七下'),('park','公园','七上'),('library','图书馆','七上'),
    ('supermarket','超市','七上'),('play','玩；打','七下'),('go','去','七上'),
    ('get','得到','七上'),('let','让','七上'),('make','使；做','七下'),
    ('want','想要','七上'),('would','愿意','七上'),('sure','当然','七上'),
    ('often','经常','七上'),('usually','通常','七下'),('never','从不','七上'),
    ('sometimes','有时','七上'),('wake','醒来','七上'),('must','必须','七上'),
    ('still','仍然','七上'),('subway','地铁','七下'),('ship','轮船','七下'),
    ('sea','海','七上'),('train','火车','七下'),('plane','飞机','七下'),
    ('stop','停止；车站','八上'),('wait','等待','七上'),('walk','步行','七上'),
    ('ride','骑','七下'),('take','乘坐','七上'),('finish','结束','七上'),
    ('lesson','课','七上'),('subject','科目','七上'),('math','数学','七上'),
    ('history','历史','七上'),('physics','物理','七上'),('geography','地理','七上'),
    ('biology','生物','七上'),('music','音乐','七下'),('science','科学','八下'),
    ('easy','容易的','七下'),('difficult','困难的','七下'),('interesting','有趣的','七下'),
    ('important','重要的','八下'),('street','街道','七上'),('road','路','七上'),
    ('left','左边','七上'),('north','北','七上'),('south','南','七上'),
    ('east','东','七上'),('west','西','七上'),('store','商店','七下'),
    ('museum','博物馆','七下'),('bookstore','书店','七上'),('airport','机场','七上'),
    ('hotel','旅馆','七上'),('room','房间','七下'),('door','门','七上'),
    ('window','窗户','七上'),('wall','墙','七上'),('table','桌子','七上'),
    ('key','钥匙','七上'),('put','放','七下'),('move','移动','七上'),
    ('party','聚会','七上'),('month','月份','七下'),('January','一月','七下'),
    ('February','二月','七下'),('March','三月','七下'),('April','四月','七下'),
    ('May','五月','七下'),('June','六月','七下'),('July','七月','七下'),
    ('September','九月','七下'),('October','十月','七下'),('November','十一月','七下'),
    ('calendar','日历','七上'),('plan','计划','八上'),('present','礼物','七上'),
    ('song','歌曲','七下'),('sing','唱歌','七下'),('perform','表演','七上'),
    ('wish','祝愿','七上'),('cut','切','七上'),('tell','告诉','七上'),
    ('speak','说','七上'),('say','说','七上'),('talk','谈话','七上'),
    ('season','季节','七下'),('weather','天气','七下'),('spring','春天','七下'),
    ('summer','夏天','七下'),('winter','冬天','七下'),('warm','温暖的','七下'),
    ('hot','热的','七下'),('cloudy','多云的','七下'),('sunny','晴朗的','七下'),
    ('rainy','下雨的','七下'),('snowy','下雪的','七下'),('windy','有风的','七下'),
    ('rain','雨；下雨','七下'),('snow','雪；下雪','七下'),('wind','风','七下'),
    ('sun','太阳','七上'),('moon','月亮','七下'),('sky','天空','七上'),
    ('temperature','温度','七上'),('low','低的','七上'),('high','高的','七上'),
    ('holiday','假期','八上'),('trip','旅行','七上'),('travel','旅游','七上'),
    ('visit','参观','七上'),('place','地方','七上'),('mountain','山','七上'),
    ('river','河流','七上'),('lake','湖','七上'),('forest','森林','七上'),
    ('field','田野','七上'),('wear','穿','七下'),('jacket','夹克','七上'),
    ('sweater','毛衣','七上'),('scarf','围巾','七上'),('glove','手套','七上'),
    ('hat','帽子','七上'),('shoe','鞋子','七上'),('sport','运动','七下'),
    ('game','游戏；比赛','八上'),('volleyball','排球','七下'),('tennis','网球','七下'),
    ('badminton','羽毛球','七下'),('soccer','足球','七下'),('football','足球','七下'),
    ('swimming','游泳','七下'),('running','跑步','七下'),('jumping','跳跃','七下'),
    ('win','赢','七上'),('lose','输','七上'),('team','队','七上'),
    ('exercise','锻炼','八上'),('health','健康','八上'),('healthy','健康的','八上'),
    ('strong','强壮的','七下'),('weak','虚弱的','七下'),('join','加入','七上'),
    ('spend','花费','七上'),('prefer','更喜欢','七下'),('quite','相当','七上'),
    ('ill','生病的','七下'),('sick','生病的','七下'),('fever','发烧','七上'),
    ('headache','头痛','七上'),('toothache','牙痛','七上'),('stomachache','胃痛','七上'),
    ('medicine','药','八下'),('patient','病人','八下'),('suggest','建议','七上'),
    ('rest','休息','七上'),('stay','停留','七上'),('drink','喝','七下'),
    ('habit','习惯','七上'),('enough','足够的','八上'),('serious','严重的','八上'),
    ('terrible','糟糕的','七下'),('worry','担心','八下'),('hobby','爱好','七上'),
    ('interest','兴趣','七上'),('interested','感兴趣的','七下'),('collection','收藏','七上'),
    ('model','模型','七上'),('toy','玩具','七下'),('robot','机器人','七下'),
    ('paint','绘画','七上'),('draw','画','七上'),('read','阅读','七下'),
    ('write','写','七下'),('story','故事','七上'),('novel','小说','七上'),
    ('magazine','杂志','八上'),('newspaper','报纸','八上'),('piano','钢琴','七下'),
    ('guitar','吉他','七下'),('violin','小提琴','七下'),('movie','电影','七下'),
    ('film','电影','七下'),('show','演出','七上'),('world','世界','七上'),
    ('nation','国家；民族','七下'),('capital','首都','七上'),('language','语言','七上'),
    ('famous','著名的','八上'),('popular','流行的','八上'),('modern','现代的','七下'),
    ('ancient','古代的','七下'),('palace','宫殿','七上'),('tower','塔','七上'),
    ('castle','城堡','七上'),('temple','寺庙','七上'),('nature','自然','七上'),
    ('environment','环境','八下'),('protect','保护','七上'),('pollution','污染','八下'),
    ('plant','植物','七上'),('ocean','海洋','七上'),('island','岛屿','七上'),
    ('desert','沙漠','七上'),('climate','气候','七上'),('technology','技术','八下'),
    ('information','信息','八上'),('message','消息','八上'),('email','电子邮件','七下'),
    ('website','网站','八上'),('feeling','感觉','八上'),('excited','兴奋的','七下'),
    ('exciting','令人兴奋的','八上'),('nervous','紧张的','八下'),('calm','冷静的','七下'),
    ('relaxed','放松的','七下'),('surprised','惊讶的','七下'),('tired','疲倦的','七下'),
    ('lonely','孤独的','七下'),('shy','害羞的','七下'),('proud','骄傲的','九年级'),
    ('laugh','笑','七上'),('smile','微笑','七上'),('shout','大喊','七上'),
    ('express','表达','七上'),('emotion','情绪','七上'),('attitude','态度','七上'),
    ('comfort','安慰','七上'),('encourage','鼓励','八下'),('support','支持','八下'),
    ('understand','理解','七上'),('refuse','拒绝','八上'),('tourist','游客','七上'),
    ('guide','导游','七上'),('ticket','票','八上'),('passport','护照','七上'),
    ('luggage','行李','七上'),('return','返回','七上'),('station','车站','七上'),
    ('explore','探索','七上'),('experience','经历','七上'),('view','景色','七上'),
    ('gift','礼物','七上'),('memory','记忆','七上'),('recommend','推荐','九年级'),
    ('food','食物','七上'),('meal','餐','七上'),('lunch','午餐','七下'),
    ('dinner','晚餐','七下'),('snack','零食','七上'),('rice','米饭','七上'),
    ('noodle','面条','七上'),('dumpling','饺子','七上'),('soup','汤','七上'),
    ('salad','沙拉','七上'),('sandwich','三明治','七下'),('hamburger','汉堡','七上'),
    ('pizza','披萨','七上'),('meat','肉','七上'),('pork','猪肉','七上'),
    ('fish','鱼','七上'),('vegetable','蔬菜','七上'),('fruit','水果','七上'),
    ('tomato','西红柿','七下'),('potato','土豆','七上'),('delicious','美味的','七下'),
    ('sweet','甜的','七上'),('sour','酸的','七上'),('bitter','苦的','七上'),
    ('spicy','辣的','七上'),('fresh','新鲜的','七上'),('free','空闲的','七下'),
    ('education','教育','九年级'),('provide','提供','八下'),('offer','提供','八下'),
    ('save','拯救；节省','八上'),('waste','浪费；废物','八上'),('recycle','回收','七上'),
    ('energy','能源','七上'),('electricity','电','七上'),('power','电力；力量','八上'),
    ('water','水','七上'),('resource','资源','七上'),('natural','自然的','七下'),
    ('harm','伤害','七上'),('safe','安全的','八下'),('safety','安全','八下'),
    ('tree','树','七上'),('grass','草','七上'),('dirty','脏的','七下'),
    ('grammar','语法','七上'),('vocabulary','词汇','七上'),('word','单词','七上'),
    ('phrase','短语','七上'),('sentence','句子','七上'),('text','课文','七上'),
    ('writing','写作','七下'),('reading','阅读','七下'),('listening','听力','七上'),
    ('speaking','口语','七上'),('skill','技能','九年级'),('ability','能力','九年级'),
    ('improve','提高','七上'),('learn','学习','七上'),('study','学习','七上'),
    ('review','复习','七上'),('remember','记住','七上'),('forget','忘记','七上'),
    ('dictionary','词典','七上'),('difference','差异','七上'),('similar','相似的','七下'),
    ('funny','有趣的','七下'),('swim','游泳','七下'),('help','帮助','七上'),
    ('dream','梦想','七上'),('grow','成长','七上'),('future','将来','七上'),
    ('friendly','友好的','七下'),('excellent','杰出的','七下'),('fantastic','极好的','七下'),
    ('matter','问题','七上'),('trouble','麻烦','七上'),('decision','决定','八上'),
    ('importance','重要性','八下'),('research','研究','八下'),('discover','发现','八下'),
    ('develop','发展','八下'),('success','成功','九年级'),('successful','成功的','九年级'),
    ('influence','影响','七上'),('society','社会','八下'),('international','国际的','七下'),
    ('translate','翻译','七上'),('pronunciation','发音','七上'),('accent','口音','七上'),
    ('conversation','对话','七上'),('communication','交流','九年级'),
    ('progress','进步','七上'),('education','教育','九年级'),
    ('medical','医疗的','七下'),('pollute','污染','八下'),('reduce','减少','八下'),
    ('electric','电的','七上'),('plastic','塑料','七上'),('paper','纸','七上'),
    ('global','全球的','七下'),
    ('everyday','每天的','七下'),('everybody','每人','八上'),('everyone','每个人','八下'),
    ('everything','每件事','七下'),('everywhere','到处','七上'),('examine','检查','九年级'),
    ('example','例子','七上'),('except','除了','七上'),('exist','存在','七上'),
    ('expect','期望','八上'),('expensive','贵的','七上'),('experiment','实验','八下'),
    ('explain','解释','八下'),('fact','事实','七上'),('factory','工厂','七上'),
    ('fail','失败','八下'),('fair','公平的','七下'),('faith','信任','七上'),
    ('fall','落下','七上'),('far','远的','七上'),('fast','快的','七下'),
    ('fat','胖的','七上'),('fear','害怕','八下'),('feed','喂养','七上'),
    ('feel','感觉','八上'),('few','很少','七上'),('fight','打架','七上'),
    ('fill','填充','七上'),('find','找到','七上'),('fine','好的','七上'),
    ('fire','火','七上'),('first','第一','七上'),('flat','平的','七上'),
    ('flight','航班','七上'),('float','漂浮','七上'),('flood','洪水','七上'),
    ('flower','花','七上'),('fly','飞','七下'),('focus','焦点','七下'),
    ('fold','折叠','七上'),('follow','跟随','七上'),('for','为了','七上'),
    ('force','强迫','七上'),('forever','永远','七上'),('forgive','原谅','七上'),
    ('fork','叉子','七上'),('form','形成','七上'),('forward','向前','七上'),
    ('freedom','自由','七上'),('fridge','冰箱','七上'),('front','前面','七上'),
    ('full','满的','七上'),('fun','有趣的事','七下'),('gather','聚集','七上'),
    ('gentle','温和的','七下'),('girl','女孩','七上'),('glad','高兴的','七上'),
    ('glass','玻璃','七上'),('goal','目标','七上'),('golden','金色的','七下'),
    ('govern','统治','七上'),('grateful','感激的','七下'),('great','伟大的','七上'),
    ('greet','问候','七上'),('ground','地面','七上'),('group','小组','七上'),
    ('guess','猜测','七上'),('guest','客人','七上'),('gun','枪','七上'),
    ('handle','处理','七上'),('handsome','英俊的','七下'),('hang','悬挂','七上'),
    ('happen','发生','八上'),('hard','困难的','七下'),('hardly','几乎不','八上'),
    ('hate','讨厌','七上'),('hear','听见','七上'),('heart','心脏','七下'),
    ('heat','热量','七下'),('heavy','重的','七上'),('height','高度','七上'),
    ('helpful','有帮助的','七下'),('her','她的','七上'),('here','这里','七上'),
    ('hero','英雄','七上'),('hill','小山','七上'),('him','他','七上'),
    ('his','他的','七上'),('hit','打击','七上'),('hold','握住','七上'),
    ('hole','洞','七上'),('honest','诚实的','七下'),('hope','希望','八上'),
    ('host','主人','七上'),('hour','小时','七上'),('house','房子','七上'),
    ('however','然而','八上'),('huge','巨大的','七上'),('humorous','幽默的','七下'),
    ('hungry','饿的','七上'),('hurry','赶紧','七上'),('ice','冰','七上'),
    ('idea','主意','七上'),('if','如果','七上'),('ignore','忽视','七上'),
    ('imagine','想象','八下'),('immediate','立即的','七下'),('impossible','不可能的','八下'),
    ('include','包括','七上'),('increase','增加','八下'),('indeed','确实','七上'),
    ('independent','独立的','七下'),('industry','工业','七上'),('inside','里面','七上'),
    ('insist','坚持','七上'),('inspire','激励','八下'),('instant','立即的','七下'),
    ('instead','代替','七上'),('intelligence','智力','七上'),('Internet','互联网','八上'),
    ('interview','面试','七上'),('introduce','介绍','八下'),('invent','发明','八下'),
    ('invest','投资','七上'),('invite','邀请','七上'),('its','它的','七上'),
    ('joke','笑话','七上'),('joy','快乐','七下'),('judge','判断','九年级'),
    ('juice','果汁','七上'),('jump','跳','七下'),('just','刚才','七上'),
    ('keep','保持','七上'),('kick','踢','七上'),('kill','杀死','七上'),
    ('kind','善良的','七下'),('king','国王','七上'),('kiss','亲吻','七上'),
    ('kite','风筝','七下'),('knee','膝盖','七上'),('knock','敲','七上'),
    ('knowledge','知识','九年级'),('lack','缺乏','七上'),('land','陆地','七上'),
    ('large','大的','七上'),('last','最后的','七下'),('law','法律','七上'),
    ('lazy','懒惰的','七下'),('lead','领导','七上'),('leaf','叶子','七上'),
    ('leave','离开','七下'),('length','长度','七上'),('level','水平','七上'),
    ('life','生命','七上'),('light','轻的','七上'),('limit','限制','七上'),
    ('line','线','七上'),('link','链接','七上'),('lion','狮子','七上'),
    ('list','列表','七上'),('listen','听','七上'),('literature','文学','七上'),
    ('little','小的','七上'),('live','生活','七上'),('local','当地的','七下'),
    ('lock','锁','七上'),('loss','损失','七上'),('loud','大声的','七上'),
    ('love','爱','七上'),('lovely','可爱的','七下'),('luck','运气','七上'),
    ('machine','机器','七上'),('mad','生气的','七下'),('mail','邮件','七下'),
    ('main','主要的','七下'),('man','男人','七上'),('manage','管理','七上'),
    ('manager','经理','七上'),('many','许多','七上'),('mark','标记','七上'),
    ('market','市场','七下'),('marry','结婚','七上'),('match','比赛','八上'),
    ('may','可以','七上'),('maybe','也许','八上'),('mean','意思是','七上'),
    ('meaning','意思','七上'),('medium','中等的','七下'),('metal','金属','七上'),
    ('mention','提到','七上'),('menu','菜单','八上'),('method','方法','七上'),
    ('million','百万','七上'),('mind','介意','八上'),('mine','我的','七上'),
    ('minute','分钟','七上'),('mirror','镜子','七上'),('miss','想念','七上'),
    ('mistake','错误','七上'),('mix','混合','七上'),('moment','时刻','七下'),
    ('money','钱','七上'),('monitor','监视器','七下'),('monkey','猴子','七上'),
    ('most','最多的','七下'),('mouse','老鼠','七上'),('much','许多','七上'),
    ('myself','我自己','七下'),('narrow','窄的','七上'),('national','国家的','七下'),
    ('near','近的','七上'),('nearly','几乎','八上'),('necessary','必要的','八下'),
    ('need','需要','七上'),('neither','两者都不','七下'),('network','网络','七上'),
    ('news','新闻','八上'),('night','夜晚','七下'),('nobody','没有人','七下'),
    ('noise','噪音','七上'),('none','没有','七上'),('normal','正常的','八上'),
    ('note','笔记','七上'),('notebook','笔记本','七上'),('nothing','没有东西','七下'),
    ('notice','注意','八下'),('nowhere','无处','七上'),('obey','服从','七上'),
    ('observe','观察','七上'),('obvious','明显的','七下'),('of','的','七上'),
    ('off','离开','七下'),('oil','油','七上'),('okay','好的','七上'),
    ('once','一次','七上'),('open','打开','七下'),('opinion','意见','七上'),
    ('opposite','相反的','七下'),('or','或者','七上'),('order','命令','七上'),
    ('organize','组织','九年级'),('other','其他的','七下'),('otherwise','否则','七上'),
    ('our','我们的','七下'),('out','出去','七上'),('outstanding','杰出的','七下'),
    ('own','自己的','七下'),('owner','主人','七上'),('oxygen','氧气','七上'),
    ('page','页','七上'),('pair','一对','七上'),('pale','苍白的','七下'),
    ('panda','熊猫','七上'),('pardon','原谅','七上'),('part','部分','七上'),
    ('partner','伙伴','七上'),('pass','通过','七上'),('path','小径','七上'),
    ('pattern','模式','七上'),('pay','支付','七上'),('peace','和平','七上'),
    ('people','人们','七上'),('percent','百分比','七下'),('perfect','完美的','七下'),
    ('perhaps','也许','八上'),('period','时期','七上'),('person','人','七上'),
    ('personal','个人的','八下'),('persuade','说服','七上'),('pet','宠物','七上'),
    ('phone','电话','七上'),('physical','身体的','七下'),('pick','捡起','七上'),
    ('piece','碎片','七上'),('pig','猪','七上'),('pile','堆','七上'),
    ('pioneer','先锋','七上'),('pity','遗憾','七上'),('planet','行星','七上'),
    ('pleasant','令人愉快的','七下'),('pleasure','愉快','七下'),('plenty','大量','七上'),
    ('plus','加上','七上'),('poet','诗人','七上'),('point','指向','七上'),
    ('police','警察','七下'),('polite','有礼貌的','七下'),('pool','水池','七上'),
    ('poor','穷的','八上'),('position','位置','七上'),('positive','积极的','七下'),
    ('possible','可能的','八下'),('post','邮寄','七下'),('pot','锅','七上'),
    ('pound','英镑','七上'),('pour','倾倒','七上'),('powerful','强大的','七上'),
    ('praise','表扬','七上'),('prepare','准备','七上'),('president','总统','七上'),
    ('press','压','七上'),('pressure','压力','八下'),('pretend','假装','七上'),
    ('pretty','漂亮的','七下'),('previous','以前的','七下'),('price','价格','七上'),
    ('pride','骄傲','九年级'),('primary','主要的','七下'),('prince','王子','七上'),
    ('principle','原则','七上'),('print','打印','七上'),('prison','监狱','七上'),
    ('private','私人的','八下'),('prize','奖品','七上'),('problem','问题','七上'),
    ('process','过程','七上'),('produce','生产','八下'),('product','产品','七上'),
    ('professor','教授','七上'),('program','程序','七上'),('project','项目','八下'),
    ('promise','承诺','七上'),('prove','证明','七上'),('public','公共的','八下'),
    ('publish','出版','七上'),('pull','拉','七上'),('push','推','七上'),
    ('punish','惩罚','七上'),('purpose','目的','七上'),('pupil','小学生','七上'),
    ('quality','质量','九年级'),('quantity','数量','七上'),('queen','女王','七上'),
    ('question','问题','七上'),('quick','迅速的','七下'),('quiet','安静的','七下'),
    ('quiz','测验','七上'),('radio','收音机','七下'),('rare','稀有的','七下'),
    ('rate','比率','七上'),('rather','相当','七上'),('raw','生的','七上'),
    ('ready','准备好的','七下'),('real','真实的','七下'),('realize','意识到','八下'),
    ('receive','收到','七上'),('recent','最近的','七下'),('recently','最近','七上'),
    ('recover','恢复','七上'),('reflect','反映','七上'),('regular','规律的','七下'),
    ('relate','关联','七上'),('relation','关系','八上'),('relax','放松','七下'),
    ('release','释放','七下'),('religion','宗教','七上'),('rely','依赖','七上'),
    ('remain','保持','七上'),('remind','提醒','七上'),('remote','遥远的','七下'),
    ('remove','移除','七上'),('rent','租金','七上'),('repeat','重复','七上'),
    ('replace','替换','七上'),('reply','回复','七上'),('report','报告','七上'),
    ('reporter','记者','七上'),('request','请求','七上'),('require','要求','七上'),
    ('respect','尊重','九年级'),('respond','回应','七上'),('result','结果','八上'),
    ('retire','退休','七上'),('reward','奖励','七上'),('rich','富的','八上'),
    ('ring','戒指','七上'),('rock','石头','七上'),('rocket','火箭','七上'),
    ('role','角色','七上'),('roll','滚动','七上'),('roof','屋顶','七上'),
    ('root','根','七上'),('rope','绳子','七上'),('rose','玫瑰','七上'),
    ('rough','粗糙的','七下'),('rule','规则','七上'),('run','跑','七下'),
    ('rush','冲','七上'),('sale','销售','七上'),('salt','盐','七上'),
    ('sand','沙子','七上'),('satellite','卫星','七上'),('scene','场景','七上'),
    ('scissors','剪刀','七上'),('score','得分','七上'),('screen','屏幕','八上'),
    ('search','搜索','七上'),('seat','座位','八上'),('secret','秘密','七上'),
    ('section','部分','七上'),('seek','寻找','七上'),('seem','似乎','八上'),
    ('seldom','很少','七上'),('select','选择','七上'),('sell','卖','七上'),
    ('send','发送','七上'),('sense','感觉','八上'),('separate','分开','七下'),
    ('series','系列','七上'),('serve','服务','八上'),('service','服务','八上'),
    ('set','设置','七上'),('settle','解决','七上'),('several','几个','七上'),
    ('shape','形状','七上'),('shadow','影子','七上'),('shake','摇动','七上'),
    ('shall','将','七上'),('shame','羞耻','七上'),('share','分享','七上'),
    ('sharp','锋利的','七下'),('sheep','绵羊','七上'),('sheet','床单','七上'),
    ('shelf','架子','七上'),('shine','闪耀','七上'),('shock','震惊','七上'),
    ('shoot','射击','七上'),('should','应该','七上'),('shoulder','肩膀','七上'),
    ('shower','淋浴','七上'),('shut','关闭','七上'),('side','边','七上'),
    ('sign','标志','七上'),('signal','信号','七上'),('silence','沉默','七上'),
    ('simple','简单的','七下'),('since','自从','七上'),('single','单个的','七下'),
    ('sir','先生','七上'),('sit','坐','七上'),('situation','情况','七上'),
    ('skin','皮肤','七上'),('sleep','睡觉','七下'),('smart','聪明的','七下'),
    ('social','社会的','八下'),('soft','柔软的','七下'),('soil','土壤','七上'),
    ('soldier','士兵','七上'),('solid','固体的','七下'),('solution','解决方案','七下'),
    ('solve','解决','七上'),('some','一些','七上'),('somebody','某人','七上'),
    ('someone','某人','七上'),('something','某事','七上'),('somewhere','某地','七上'),
    ('soon','很快','七下'),('sort','种类','七上'),('sound','声音','八上'),
    ('space','空间','七上'),('special','特别的','九年级'),('speech','演讲','七上'),
    ('speed','速度','七上'),('spell','拼写','七下'),('spirit','精神','七上'),
    ('spoon','勺子','七上'),('spread','传播','七上'),('stage','舞台','七上'),
    ('stand','站立','七上'),('standard','标准','七上'),('start','开始','七下'),
    ('state','州','七上'),('steal','偷','七上'),('steel','钢','七上'),
    ('step','步骤','七上'),('stick','粘贴','七上'),('stone','石头','七上'),
    ('storm','暴风雨','七下'),('straight','直的','七上'),('strange','奇怪的','七下'),
    ('stress','压力','八下'),('strict','严格的','七下'),('struggle','奋斗','七上'),
    ('succeed','成功','九年级'),('such','这样的','七上'),('sugar','糖','七上'),
    ('supply','提供','八下'),('suppose','假设','七上'),('surface','表面','七上'),
    ('surprise','惊讶','七上'),('switch','开关','七下'),('symbol','象征','七上'),
    ('system','系统','七上'),('tail','尾巴','七上'),('tale','故事','七上'),
    ('task','任务','七上'),('tea','茶','七上'),('technical','技术的','八下'),
    ('teenager','青少年','七下'),('television','电视','七下'),('tent','帐篷','七上'),
    ('test','测试','七上'),('than','比','七上'),('that','那个','七上'),
    ('their','他们的','七下'),('them','他们','七上'),('themselves','他们自己','七下'),
    ('theory','理论','七上'),('there','那里','七上'),('therefore','因此','七上'),
    ('thick','厚的','七上'),('thief','小偷','七上'),('thin','瘦的','七上'),
    ('thing','东西','七上'),('think','思考','七上'),('thirsty','渴的','七上'),
    ('this','这个','七上'),('those','那些','七上'),('though','虽然','八上'),
    ('thought','想法','七上'),('thousand','千','七上'),('thread','线','七上'),
    ('through','通过','七上'),('thunder','雷声','七上'),('tidy','整洁的','七下'),
    ('tiger','老虎','七上'),('tight','紧的','七上'),('till','直到','七上'),
    ('title','标题','七上'),('together','一起','七上'),('toilet','厕所','七上'),
    ('tongue','舌头','七上'),('tool','工具','七上'),('top','顶部','七上'),
    ('topic','话题','七上'),('total','总的','七上'),('touch','触摸','七上'),
    ('toward','朝向','七上'),('town','城镇','七上'),('trade','贸易','七上'),
    ('traffic','交通','七上'),('treasure','财宝','七上'),('treat','对待','七上'),
    ('truck','卡车','七上'),('true','真的','七上'),('trust','信任','七上'),
    ('truth','真相','七上'),('try','尝试','八上'),('twice','两次','七上'),
    ('type','类型','七上'),('ugly','丑陋的','七下'),('umbrella','雨伞','七下'),
    ('under','在...下面','八上'),('unless','除非','七上'),('until','直到','七上'),
    ('unusual','不寻常的','七下'),('up','向上','七上'),('upset','心烦的','七下'),
    ('use','使用','七上'),('useful','有用的','七下'),('useless','无用的','七下'),
    ('usual','通常的','七下'),('valuable','有价值的','七下'),('value','价值','七上'),
    ('variety','种类','七上'),('various','各种各样的','八上'),('vast','广阔的','七下'),
    ('verb','动词','七上'),('very','非常','七上'),('victory','胜利','七上'),
    ('video','视频','七上'),('village','村庄','七上'),('virtue','美德','七上'),
    ('visitor','访客','七上'),('voice','声音','八上'),('wage','工资','七上'),
    ('warn','警告','七上'),('wash','洗','七下'),('wave','波浪','七上'),
    ('way','路','七上'),('wealth','财富','八上'),('weekday','工作日','七下'),
    ('weight','重量','七上'),('web','网','七上'),('well','好','七上'),
    ('wet','湿的','七上'),('whatever','无论什么','七上'),('wheel','轮子','七上'),
    ('when','什么时候','七上'),('whether','是否','七上'),('which','哪一个','七上'),
    ('while','当...时候','八上'),('whole','整个的','七下'),('whom','谁','七上'),
    ('whose','谁的','七上'),('why','为什么','七上'),('wild','野生的','七下'),
    ('wine','酒','七上'),('wing','翅膀','七上'),('winner','获胜者','七下'),
    ('wipe','擦','七上'),('wise','明智的','七下'),('within','在...之内','八上'),
    ('without','没有','七上'),('wolf','狼','七上'),('woman','女人','七上'),
    ('wonder','想知道','七下'),('wonderful','精彩的','七下'),('wood','木头','七上'),
    ('worth','值得','七上'),('wrong','错误的','七下'),('yard','院子','七上'),
    ('yesterday','昨天','七下'),('yet','还','七上'),('yourself','你自己','七下'),
    ('youth','青春','七下'),('zebra','斑马','七上'),('zero','零','七上'),
    ('zone','区域','七上'),
    # 八年级补充
    ('screen','屏幕','八上'),('talent','才能','八上'),('magician','魔术师','八上'),
    ('creative','有创造力的','八上'),('beautifully','漂亮地','八上'),('role','角色；作用','八上'),
    ('winner','获胜者','八上'),('carefully','小心地','八上'),('comfortably','舒服地','八上'),
    ('writer','作家','八上'),('reason','原因；理由','八上'),('unlucky','不幸的','八上'),
    ('meaningless','无意义的','八上'),('enjoyable','愉快的','八上'),('discussion','讨论','八上'),
    ('stand','站立；容忍','八上'),('educational','有教育意义的','八上'),
    ('relationship','关系','八上'),('communicate','交流；沟通','八上'),
    ('typical','典型的','八上'),('possibly','可能地','八上'),
    ('available','可获得的；有空的','八上'),('forward','向前','八上'),
    ('suggestion','建议','八上'),('delete','删除','八上'),
    ('glue','胶水','八上'),('satisfy','使满意','八上'),
    ('sweep','打扫；清扫','八下'),('throw','扔；投掷','八下'),
    ('depend','依靠；依赖','八下'),
    # 九年级补充
    ('acquire','获得；学到','九年级'),('wisely','明智地；聪明地','九年级'),
    ('textbook','教科书；课本','九年级'),('repetition','重复；反复','九年级'),
    ('chemise','化学家','九年级'),('stranger','陌生人','九年级'),
    ('admire','钦佩；羡慕','九年级'),('Christmas','圣诞节','九年级'),
    ('spider','蜘蛛','九年级'),('ghost','鬼；鬼魂','九年级'),
    ('warmth','温暖；热情','九年级'),('background','背景','九年级'),
    ('Asian','亚洲的；亚洲人','九年级'),('European','欧洲的；欧洲人','九年级'),
    ('African','非洲的；非洲人','九年级'),('British','英国的；英国人','九年级'),
    ('dare','敢于；胆敢','九年级'),('general','总的；普遍的','九年级'),
    ('conclusion','结论；结尾','九年级'),('related','相关的；有联系的','九年级'),
    ('manner','方式；举止；礼貌','九年级'),('impolite','无礼貌的','九年级'),
    ('direct','直接的；指导','九年级'),('plenty','大量；充足','九年级'),
    ('brand','品牌；牌子','九年级'),('advertisement','广告','九年级'),
    ('vehicle','交通工具；车辆','九年级'),('unbelievable','难以置信的','九年级'),
    ('congratulate','祝贺','九年级'),('caring','关心他人的；体贴的','九年级'),
    ('sadness','悲伤；悲痛','九年级'),('painful','痛苦的；疼痛的','九年级'),
    ('recall','回忆起；召回','九年级'),('direction','方向；指导','九年级'),
    ('invention','发明；创造','九年级'),('inventor','发明家；创造者','九年级'),
    ('popularity','普及；流行','九年级'),('professional','职业的；专业的','九年级'),
    ('lifelong','终身的；毕生的','九年级'),('dessert','甜点；甜品','九年级'),
    ('ancestor','祖先；祖宗','九年级'),
]

REVIEW_CYCLES = [1, 2, 4, 7, 15, 30]

# ==================== 数据管理 ====================
def _load_json(filename, default):
    path = os.path.join(BASE_DIR, filename)
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return default

def _save_json(filename, data):
    path = os.path.join(BASE_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_mistakes():
    return _load_json('mistakes.json', {"math": [], "physics": [], "english": []})

def save_mistakes(m):
    _save_json('mistakes.json', m)

def add_mistake(subject, question, user_ans, correct_ans, explanation):
    m = load_mistakes()
    if subject not in m:
        m[subject] = []
    m[subject].append({
        "question": question, "user_answer": user_ans,
        "correct_answer": correct_ans, "explanation": explanation,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_mistakes(m)

def load_reward():
    return _load_json('reward_data.json', {
        "stars": 0, "hearts": 0, "level": 1, "points": 0,
        "total_stars": 0, "total_hearts_earned": 0,
        "consecutive_days": 0, "last_checkin_date": None,
        "achievements": [], "combo": 0, "max_combo": 0,
        "stats": {"total_correct": 0, "total_wrong": 0,
                   "math_correct": 0, "math_wrong": 0,
                   "physics_correct": 0, "physics_wrong": 0,
                   "english_correct": 0, "english_wrong": 0,
                   "max_combo": 0},
        "daily_study_seconds": 0, "last_save_date": None
    })

def save_reward(r):
    _save_json('reward_data.json', r)

def load_word_mastery():
    return _load_json('word_mastery.json', {
        "words": {}, "word_list": []
    })

def save_word_mastery(wm):
    _save_json('word_mastery.json', wm)

def load_settings():
    return _load_json('settings.json', {
        "font_size": 16, "theme": "dark", "sound": True
    })

def save_settings(s):
    _save_json('settings.json', s)


# ==================== 奖励系统 ====================
class RewardManager:
    ACHIEVEMENT_LIST = [
        {"id": "first_star", "name": "初露锋芒", "desc": "获得第一颗★", "icon": "⭐", "need": 1, "type": "stars"},
        {"id": "star_10", "name": "小有成就", "desc": "获得10颗★", "icon": "🌟", "need": 10, "type": "stars"},
        {"id": "star_50", "name": "学富五车", "desc": "获得50颗★", "icon": "🏅", "need": 50, "type": "stars"},
        {"id": "star_100", "name": "学识渊博", "desc": "获得100颗★", "icon": "🎓", "need": 100, "type": "stars"},
        {"id": "star_500", "name": "大师级", "desc": "获得500颗★", "icon": "🏆", "need": 500, "type": "stars"},
        {"id": "consecutive_3", "name": "持之以恒", "desc": "连续学习3天", "icon": "📅", "need": 3, "type": "days"},
        {"id": "consecutive_7", "name": "一周坚持", "desc": "连续学习7天", "icon": "📆", "need": 7, "type": "days"},
        {"id": "consecutive_30", "name": "月度达人", "desc": "连续学习30天", "icon": "🗓", "need": 30, "type": "days"},
        {"id": "level_5", "name": "初出茅庐", "desc": "达到5级", "icon": "🔰", "need": 5, "type": "level"},
        {"id": "level_10", "name": "学有所成", "desc": "达到10级", "icon": "⭐", "need": 10, "type": "level"},
        {"id": "level_20", "name": "学贯中西", "desc": "达到20级", "icon": "👑", "need": 20, "type": "level"},
        {"id": "combo_5", "name": "小试牛刀", "desc": "达成5连击", "icon": "⚡", "need": 5, "type": "combo"},
        {"id": "combo_10", "name": "龙卷风", "desc": "达成10连击", "icon": "🌪", "need": 10, "type": "combo"},
        {"id": "combo_20", "name": "无人能敌", "desc": "达成20连击", "icon": "💎", "need": 20, "type": "combo"},
    ]

    def __init__(self):
        self.data = load_reward()
        self._check_new_day()

    def _check_new_day(self):
        today = datetime.now().date()
        last = self.data.get("last_save_date")
        if last != str(today):
            self.data["daily_study_seconds"] = 0
            last_date = self.data.get("last_checkin_date")
            if last_date:
                try:
                    ld = datetime.strptime(last_date, "%Y-%m-%d").date()
                    if ld != today - timedelta(days=1):
                        self.data["consecutive_days"] = 0
                except Exception:
                    self.data["consecutive_days"] = 0
            self.save()

    def add_stars(self, count=1, subject="math"):
        self.data["stars"] += count
        self.data["total_stars"] = self.data.get("total_stars", 0) + count
        self.data["combo"] = self.data.get("combo", 0) + 1
        if self.data["combo"] > self.data.get("max_combo", 0):
            self.data["max_combo"] = self.data["combo"]
            self.data["stats"]["max_combo"] = self.data["combo"]
        self.data["stats"]["total_correct"] = self.data["stats"].get("total_correct", 0) + 1
        if subject in self.data["stats"]:
            self.data["stats"][f"{subject}_correct"] = self.data["stats"].get(f"{subject}_correct", 0) + 1

        msgs = [f"+{count}★"]
        if self.data["combo"] >= 5:
            msgs.append(f"🔥{self.data['combo']}连击")

        # ★→❤
        while self.data["stars"] >= 3:
            self.data["stars"] -= 3
            self.data["hearts"] = self.data.get("hearts", 0) + 1
            self.data["total_hearts_earned"] = self.data.get("total_hearts_earned", 0) + 1
            msgs.append("+1❤")

        # ❤→等级
        while self.data["hearts"] >= 5:
            self.data["hearts"] -= 5
            self.data["level"] = self.data.get("level", 1) + 1
            msgs.append(f"🎉升级到Lv.{self.data['level']}！")

        ach = self._check_achievements()
        if ach:
            msgs.append(f"{ach['icon']} 解锁: {ach['name']}")

        # Check study time
        self.data["daily_study_seconds"] = self.data.get("daily_study_seconds", 0) + 60
        self._check_study_time()
        self.save()
        return " | ".join(msgs)

    def wrong_answer(self, subject="math"):
        self.data["combo"] = 0
        self.data["stats"]["total_wrong"] = self.data["stats"].get("total_wrong", 0) + 1
        if subject in self.data["stats"]:
            self.data["stats"][f"{subject}_wrong"] = self.data["stats"].get(f"{subject}_wrong", 0) + 1
        msgs = ["连击中断"]
        if self.data.get("hearts", 0) > 0:
            self.data["hearts"] -= 1
            msgs.append("-1❤")
        else:
            msgs.append("❤已用完")
        self.save()
        return " | ".join(msgs)

    def add_points(self, amount=5):
        self.data["points"] = self.data.get("points", 0) + amount
        self.save()

    def daily_checkin(self):
        today = datetime.now().date()
        if self.data.get("last_checkin_date") == str(today):
            return False
        last = self.data.get("last_checkin_date")
        if last:
            try:
                ld = datetime.strptime(last, "%Y-%m-%d").date()
                if ld == today - timedelta(days=1):
                    self.data["consecutive_days"] = self.data.get("consecutive_days", 0) + 1
                else:
                    self.data["consecutive_days"] = 1
            except Exception:
                self.data["consecutive_days"] = 1
        else:
            self.data["consecutive_days"] = 1
        self.data["last_checkin_date"] = str(today)
        self.save()
        return True

    def _check_study_time(self):
        if self.data.get("daily_study_seconds", 0) >= 7200:
            self.daily_checkin()

    def _check_achievements(self):
        for ach in self.ACHIEVEMENT_LIST:
            if ach["id"] not in self.data.get("achievements", []):
                t = ach["type"]
                need = ach["need"]
                val = 0
                if t == "stars":
                    val = self.data.get("total_stars", 0)
                elif t == "days":
                    val = self.data.get("consecutive_days", 0)
                elif t == "level":
                    val = self.data.get("level", 1)
                elif t == "combo":
                    val = self.data.get("max_combo", 0)
                if val >= need:
                    if "achievements" not in self.data:
                        self.data["achievements"] = []
                    self.data["achievements"].append(ach["id"])
                    return ach
        return None

    def save(self):
        self.data["last_save_date"] = str(datetime.now().date())
        save_reward(self.data)


# ==================== 自适应训练引擎 ====================
class AdaptiveTrainer:
    def __init__(self, subject, questions):
        self.subject = subject
        self.questions = list(questions)
        self.level = 1
        self.correct_in_level = 0
        self.need_correct = 3
        self.mastered = set()
        self.all_done = False
        self.current_q = None
        self.pending_upgrade = False

    def available(self):
        return [(i, q) for i, q in enumerate(self.questions)
                if q["level"] == self.level and i not in self.mastered]

    def next_question(self):
        if self.pending_upgrade:
            self.pending_upgrade = False
            if self.level < 3:
                self.level += 1
                self.correct_in_level = 0
                return ("upgrade", self.level)
            else:
                self.all_done = True
                return ("complete", None)
        avail = self.available()
        if not avail:
            if self.level < 3:
                self.level += 1
                self.correct_in_level = 0
                return ("upgrade", self.level)
            else:
                self.all_done = True
                return ("complete", None)
        idx, q = random.choice(avail)
        self.current_q = (idx, q)
        return ("question", q)

    def check_answer(self, user_ans):
        if self.current_q is None:
            return False, None
        idx, q = self.current_q
        a = q["answer"].lower()
        u = user_ans.lower().strip()
        correct = (a in u) or (u in a) or (u == a)
        if correct:
            self.correct_in_level += 1
            self.mastered.add(idx)
            remaining = self.available()
            if self.correct_in_level >= self.need_correct and not remaining and self.level < 3:
                self.pending_upgrade = True
            return True, q
        else:
            self.correct_in_level = 0
            return False, q


# ==================== 主题颜色 ====================
THEMES = {
    "dark": {
        "bg": "#1a1a2e", "card": "#16213e", "accent": "#0f3460",
        "text": "#ffffff", "text2": "#b0b0b0", "primary": "#2196F3",
        "secondary": "#FF9800", "success": "#4CAF50", "error": "#F44336",
        "highlight": "#e94560", "nav_bg": "#0d0d1a", "btn": "#2196F3",
    },
    "light": {
        "bg": "#f5f5f5", "card": "#ffffff", "accent": "#e3f2fd",
        "text": "#212121", "text2": "#757575", "primary": "#1976D2",
        "secondary": "#F57C00", "success": "#388E3C", "error": "#D32F2F",
        "highlight": "#C62828", "nav_bg": "#ffffff", "btn": "#1976D2",
    }
}

def get_theme():
    s = load_settings()
    return THEMES.get(s.get("theme", "dark"), THEMES["dark"])

def theme_color(key):
    return get_theme()[key]


# ==================== 通用组件 ====================
def make_label(text, bold=False, size=None, color_key="text", halign="center"):
    t = get_theme()
    s = load_settings()
    fs = size or s.get("font_size", 16)
    lbl = Label(text=text, font_size=fs,
                color=t.get(color_key, t["text"]),
                halign=halign, valign="middle")
    lbl.bind(width=lambda *x: setattr(lbl, 'text_size', (lbl.width, None)))
    return lbl

def make_button(text, callback, color_key="btn", size=None, bold=True):
    t = get_theme()
    s = load_settings()
    fs = size or (s.get("font_size", 16) - 2)
    btn = Button(text=text, font_size=fs, bold=bold,
                 background_color=t[color_key],
                 color=(1, 1, 1, 1),
                 size_hint=(1, None), height=50)
    btn.bind(on_press=callback)
    return btn

def make_card():
    t = get_theme()
    bl = BoxLayout(orientation='vertical', padding=12, spacing=8,
                   size_hint=(1, None))
    bl.canvas.before
    return bl

def show_popup(title, content_text, auto_close=True):
    t = get_theme()
    box = BoxLayout(orientation='vertical', padding=20, spacing=10)
    box.add_widget(make_label(title, bold=True, size=18, color_key="highlight"))
    box.add_widget(make_label(content_text, size=14, color_key="text2", halign="center"))
    btn = Button(text="确定", size_hint=(1, None), height=40,
                 background_color=t["primary"], color=(1,1,1,1))
    popup = Popup(title="", content=box, size_hint=(0.85, 0.4), auto_dismiss=True)
    btn.bind(on_press=popup.dismiss)
    box.add_widget(btn)
    popup.open()
    return popup

def make_scrollable(content_widget):
    sv = ScrollView(size_hint=(1, 1), do_scroll_x=False)
    sv.add_widget(content_widget)
    return sv


# ==================== 各页面类 ====================

class HomePage(BoxLayout):
    def __init__(self, app, **kw):
        super().__init__(orientation='vertical', spacing=8, padding=10, **kw)
        self.app = app
        t = get_theme()
        s = load_settings()
        fs = s.get("font_size", 16)

        # 标题
        self.add_widget(make_label("📚 学练考系统", bold=True, size=fs+6, color_key="highlight"))

        # 状态面板
        self.status_label = make_label("", bold=True, size=fs+2, color_key="primary")
        self.add_widget(self.status_label)
        self.refresh_status()

        # 快捷按钮
        grid = GridLayout(cols=2, spacing=8, size_hint=(1, None), height=280)
        buttons = [
            ("🎯 自适应训练", self.go_train),
            ("📖 英语专项", self.go_english),
            ("📝 考试模式", self.go_exam),
            ("❌ 错题本", self.go_mistakes),
            ("📊 学习统计", self.go_stats),
            ("⚙️ 设置", self.go_settings),
        ]
        for text, cb in buttons:
            btn = Button(text=text, font_size=fs, bold=True,
                         background_color=t["accent"], color=t["text"],
                         size_hint=(1, None), height=55)
            btn.bind(on_press=cb)
            grid.add_widget(btn)
        self.add_widget(grid)

        # 打卡状态
        self.checkin_label = make_label("", size=fs-2, color_key="text2")
        self.add_widget(self.checkin_label)
        self.refresh_checkin()

    def refresh_status(self):
        if not self.app:
            return
        r = self.app.reward
        self.status_label.text = (
            f"⭐{r.data.get('stars',0)}  "
            f"❤{r.data.get('hearts',0)}  "
            f"Lv.{r.data.get('level',1)}  "
            f"🔥连击{r.data.get('combo',0)}  "
            f"📅{r.data.get('consecutive_days',0)}天"
        )

    def refresh_checkin(self):
        if not self.app:
            return
        r = self.app.reward
        secs = r.data.get("daily_study_seconds", 0)
        h, m = divmod(secs, 3600)
        m2 = (secs % 3600) // 60
        self.checkin_label.text = f"今日学习: {int(h)}时{int(m2)}分 | 满2小时自动打卡"

    def go_train(self, *a):
        self.app.switch_tab(1)

    def go_english(self, *a):
        self.app.switch_tab(2)

    def go_exam(self, *a):
        self.app.switch_tab(3)

    def go_mistakes(self, *a):
        self.app.switch_tab(4)

    def go_stats(self, *a):
        self.app.switch_tab(4)
        self.app.mistakes_page.show_stats()

    def go_settings(self, *a):
        self.app.switch_tab(4)
        self.app.mistakes_page.show_settings()


class TrainingPage(BoxLayout):
    def __init__(self, app, **kw):
        super().__init__(orientation='vertical', spacing=8, padding=10, **kw)
        self.app = app
        self.trainer = None
        self.subject = None
        t = get_theme()
        s = load_settings()
        fs = s.get("font_size", 16)

        # 科目选择（初始显示）
        self.select_layout = BoxLayout(orientation='vertical', spacing=10)
        self.select_layout.add_widget(make_label("选择训练科目", bold=True, size=fs+4, color_key="highlight"))

        for name, key, color in [("📐 数学", "math", t["primary"]),
                                   ("⚛️ 物理", "physics", t["secondary"])]:
            btn = Button(text=name, font_size=fs+2, bold=True,
                         background_color=color, color=(1,1,1,1),
                         size_hint=(1, None), height=70)
            btn.bind(on_press=lambda *a, k=key: self.start_training(k))
            self.select_layout.add_widget(btn)

        self.back_btn = Button(text="← 返回首页", font_size=fs,
                               background_color=t["accent"], color=t["text"],
                               size_hint=(1, None), height=45)
        self.back_btn.bind(on_press=lambda *a: self.app.switch_tab(0))
        self.select_layout.add_widget(self.back_btn)

        # 训练区域（初始隐藏）
        self.train_layout = BoxLayout(orientation='vertical', spacing=8)

        self.info_label = make_label("", size=fs, color_key="secondary")
        self.train_layout.add_widget(self.info_label)

        self.question_label = make_label("", bold=True, size=fs, halign="left")
        self.question_label.bind(width=lambda *x: setattr(self.question_label, 'text_size', (self.question_label.width, None)))
        self.train_layout.add_widget(self.question_label)

        self.answer_input = TextInput(hint_text="输入你的答案...",
                                       font_size=fs, multiline=False,
                                       size_hint=(1, None), height=45,
                                       background_color=t["card"],
                                       foreground_color=t["text"],
                                       cursor_color=t["primary"])
        self.answer_input.bind(on_text_validate=self.submit_answer)
        self.train_layout.add_widget(self.answer_input)

        self.submit_btn = Button(text="提交答案", font_size=fs, bold=True,
                                  background_color=t["primary"], color=(1,1,1,1),
                                  size_hint=(1, None), height=50)
        self.submit_btn.bind(on_press=self.submit_answer)
        self.train_layout.add_widget(self.submit_btn)

        self.feedback_label = make_label("", size=fs-2, color_key="text2", halign="left")
        self.feedback_label.bind(width=lambda *x: setattr(self.feedback_label, 'text_size', (self.feedback_label.width, None)))
        self.train_layout.add_widget(self.feedback_label)

        self.next_btn = Button(text="下一题 →", font_size=fs, bold=True,
                                background_color=t["success"], color=(1,1,1,1),
                                size_hint=(1, None), height=50)
        self.next_btn.bind(on_press=self.next_question)
        self.train_layout.add_widget(self.next_btn)

        self.end_btn = Button(text="结束训练", font_size=fs,
                                background_color=t["error"], color=(1,1,1,1),
                                size_hint=(1, None), height=45)
        self.end_btn.bind(on_press=self.end_training)
        self.train_layout.add_widget(self.end_btn)

        self.add_widget(self.select_layout)
        self.add_widget(self.train_layout)
        self.train_layout.opacity = 0
        self.train_layout.size_hint_y = 0

    def start_training(self, subject):
        self.subject = subject
        self.trainer = AdaptiveTrainer(subject, ALL_SUBJECTS[subject])
        self.select_layout.opacity = 0
        self.select_layout.size_hint_y = 0
        self.train_layout.opacity = 1
        self.train_layout.size_hint_y = 1
        self.load_question()

    def load_question(self):
        if not self.trainer:
            return
        result = self.trainer.next_question()
        if result[0] == "question":
            q = result[1]
            self.question_label.text = f"[难度{'⭐'*self.trainer.level}] {q['text']}"
            self.info_label.text = f"连续正确: {self.trainer.correct_in_level}/{self.trainer.need_correct}  已掌握: {len(self.trainer.mastered)}/{len(self.trainer.questions)}"
            self.answer_input.text = ""
            self.answer_input.disabled = False
            self.submit_btn.disabled = False
            self.feedback_label.text = ""
            self.next_btn.disabled = True
        elif result[0] == "upgrade":
            level = result[1]
            self.app.reward.add_points(100)
            show_popup("🎉 升级！", f"恭喜升级到难度 {level} 星！\n获得 100 积分！")
            self.load_question()
        elif result[0] == "complete":
            self.feedback_label.text = "🏆 太棒了！已掌握所有题目！"
            self.answer_input.disabled = True
            self.submit_btn.disabled = True
            self.next_btn.disabled = True
            show_popup("🏆 全部完成", "太棒了！已掌握本学科所有题目！")

    def submit_answer(self, *a):
        if not self.trainer or not self.trainer.current_q:
            return
        user_ans = self.answer_input.text.strip()
        if not user_ans:
            self.feedback_label.text = "⚠️ 请输入答案"
            return
        correct, q = self.trainer.check_answer(user_ans)
        if correct:
            msg = self.app.reward.add_stars(1, self.subject)
            video = q.get('video', '')
            self.feedback_label.text = f"✅ 正确！\n讲解：{q['explain']}\n{msg}\n🎥 {video}" if video else f"✅ 正确！\n讲解：{q['explain']}\n{msg}"
        else:
            msg = self.app.reward.wrong_answer(self.subject)
            add_mistake(self.subject, q["text"], user_ans, q["answer"], q["explain"])
            video = q.get('video', '')
            self.feedback_label.text = f"❌ 错误 {msg}\n正确：{q['answer']}\n讲解：{q['explain']}\n🎥 {video}" if video else f"❌ 错误 {msg}\n正确：{q['answer']}\n讲解：{q['explain']}"
        self.info_label.text = f"连续正确: {self.trainer.correct_in_level}/{self.trainer.need_correct}  已掌握: {len(self.trainer.mastered)}/{len(self.trainer.questions)}"
        self.answer_input.disabled = True
        self.submit_btn.disabled = True
        self.next_btn.disabled = False

    def next_question(self, *a):
        if self.trainer and not self.trainer.all_done:
            self.load_question()

    def end_training(self, *a):
        self.trainer = None
        self.subject = None
        self.select_layout.opacity = 1
        self.select_layout.size_hint_y = 1
        self.train_layout.opacity = 0
        self.train_layout.size_hint_y = 0


class EnglishPage(BoxLayout):
    def __init__(self, app, **kw):
        super().__init__(orientation='vertical', spacing=6, padding=8, **kw)
        self.app = app
        self.current_mode = None
        self.current_word = None
        self.word_idx = 0
        self.tts_engine = None
        t = get_theme()
        s = load_settings()
        fs = s.get("font_size", 16)

        # 模式选择
        self.mode_layout = BoxLayout(orientation='vertical', spacing=6)
        self.mode_layout.add_widget(make_label("📖 英语专项学习", bold=True, size=fs+4, color_key="highlight"))

        modes = [
            ("🔀 随机抽查", self.mode_random),
            ("🔄 记忆曲线复习", self.mode_review),
            ("✏️ 单词补全", self.mode_fill),
            ("📚 词库管理", self.mode_wordlist),
        ]
        grid = GridLayout(cols=2, spacing=6, size_hint=(1, None), height=250)
        for text, cb in modes:
            btn = Button(text=text, font_size=fs, bold=True,
                         background_color=t["accent"], color=t["text"],
                         size_hint=(1, None), height=55)
            btn.bind(on_press=cb)
            grid.add_widget(btn)
        self.mode_layout.add_widget(grid)

        # 练习区域
        self.practice_layout = BoxLayout(orientation='vertical', spacing=6)

        self.engl_info = make_label("", size=fs, color_key="secondary")
        self.practice_layout.add_widget(self.engl_info)

        self.engl_word = make_label("", bold=True, size=fs+4, color_key="highlight")
        self.practice_layout.add_widget(self.engl_word)

        self.engl_question = make_label("", size=fs, halign="left")
        self.engl_question.bind(width=lambda *x: setattr(self.engl_question, 'text_size', (self.engl_question.width, None)))
        self.practice_layout.add_widget(self.engl_question)

        self.engl_input = TextInput(hint_text="输入答案...", font_size=fs,
                                     multiline=False, size_hint=(1, None), height=45,
                                     background_color=t["card"], foreground_color=t["text"])
        self.engl_input.bind(on_text_validate=self._on_engl_submit)
        self.practice_layout.add_widget(self.engl_input)

        self.engl_submit = Button(text="提交", font_size=fs, bold=True,
                                   background_color=t["primary"], color=(1,1,1,1),
                                   size_hint=(1, None), height=45)
        self.engl_submit.bind(on_press=self._on_engl_submit)
        self.practice_layout.add_widget(self.engl_submit)

        self.engl_feedback = make_label("", size=fs-2, color_key="text2", halign="left")
        self.engl_feedback.bind(width=lambda *x: setattr(self.engl_feedback, 'text_size', (self.engl_feedback.width, None)))
        self.practice_layout.add_widget(self.engl_feedback)

        self.engl_next = Button(text="下一题 →", font_size=fs, bold=True,
                                 background_color=t["success"], color=(1,1,1,1),
                                 size_hint=(1, None), height=45)
        self.engl_next.bind(on_press=self._on_engl_next)
        self.practice_layout.add_widget(self.engl_next)

        self.engl_speak = Button(text="🔊 朗读", font_size=fs,
                                  background_color=t["secondary"], color=(1,1,1,1),
                                  size_hint=(1, None), height=40)
        self.engl_speak.bind(on_press=self._on_engl_speak)
        self.practice_layout.add_widget(self.engl_speak)

        self.engl_back = Button(text="← 返回", font_size=fs,
                                 background_color=t["accent"], color=t["text"],
                                 size_hint=(1, None), height=40)
        self.engl_back.bind(on_press=self._on_engl_back)
        self.practice_layout.add_widget(self.engl_back)

        # 词库管理页
        self.wordlist_layout = BoxLayout(orientation='vertical', spacing=6)

        self.wl_title = make_label("📚 词库管理", bold=True, size=fs+2, color_key="highlight")
        self.wordlist_layout.add_widget(self.wl_title)

        self.wl_grade_spinner = Spinner(text="全部年级", values=["全部年级", "七上", "七下", "八上", "八下", "九年级"],
                                          size_hint=(1, None), height=40)
        self.wl_grade_spinner.bind(text=self.filter_words)
        self.wordlist_layout.add_widget(self.wl_grade_spinner)

        self.wl_stats = make_label("", size=fs-2, color_key="text2")
        self.wordlist_layout.add_widget(self.wl_stats)

        self.wl_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.wl_content = BoxLayout(orientation='vertical', spacing=3, size_hint=(1, None))
        self.wl_content.bind(minimum_height=self.wl_content.setter('height'))
        self.wl_scroll.add_widget(self.wl_content)
        self.wordlist_layout.add_widget(self.wl_scroll)

        self.wl_back = Button(text="← 返回", font_size=fs,
                               background_color=t["accent"], color=t["text"],
                               size_hint=(1, None), height=40)
        self.wl_back.bind(on_press=self.wordlist_back)
        self.wordlist_layout.add_widget(self.wl_back)

        self.add_widget(self.mode_layout)
        self.add_widget(self.practice_layout)
        self.add_widget(self.wordlist_layout)
        self.practice_layout.opacity = 0
        self.practice_layout.size_hint_y = 0
        self.wordlist_layout.opacity = 0
        self.wordlist_layout.size_hint_y = 0

    def _hide_all(self):
        self.mode_layout.opacity = 0; self.mode_layout.size_hint_y = 0
        self.practice_layout.opacity = 0; self.practice_layout.size_hint_y = 0
        self.wordlist_layout.opacity = 0; self.wordlist_layout.size_hint_y = 0

    def _init_tts(self):
        try:
            import pyttsx3
            if not self.tts_engine:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 150)
            return True
        except Exception:
            return False

    def _speak(self, text):
        def do_speak(dt):
            if self._init_tts():
                try:
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                except Exception:
                    pass
        Clock.schedule_once(do_speak, 0.1)

    def _get_review_words(self):
        wm = load_word_mastery()
        words_data = wm.get("words", {})
        today = datetime.now().date()
        due = []
        for word, info in words_data.items():
            last = info.get("last_review")
            if last:
                try:
                    ld = datetime.strptime(last, "%Y-%m-%d").date()
                    for cycle in REVIEW_CYCLES:
                        next_date = ld + timedelta(days=cycle)
                        if next_date <= today:
                            due.append((word, info.get("meaning", ""), cycle))
                            break
                except Exception:
                    pass
        return due

    def _pick_random_word(self):
        return random.choice(WORD_LIST)

    def _show_word(self, word_tuple, mode="en2cn"):
        word, meaning, grade = word_tuple[:3] if len(word_tuple) >= 3 else (word_tuple[0], word_tuple[1], "")
        self.current_word = word_tuple
        if mode == "en2cn":
            self.engl_word.text = word
            self.engl_question.text = "请输入中文含义："
        elif mode == "cn2en":
            self.engl_word.text = meaning
            self.engl_question.text = "请输入英文单词："
        elif mode == "fill":
            # Word completion: show word with blanks
            if len(word) <= 3:
                display = word[0] + "___"
            elif len(word) <= 6:
                display = word[0] + "___" + word[-1]
            else:
                mid = len(word) // 2
                display = word[:mid-1] + "___" + word[mid+2:]
            self.engl_word.text = display
            self.engl_question.text = f"补全单词（{meaning}）："
        self.engl_input.text = ""
        self.engl_input.disabled = False
        self.engl_submit.disabled = False
        self.engl_next.disabled = True
        self.engl_feedback.text = ""

    def mode_random(self, *a):
        self.current_mode = random.choice(["en2cn", "cn2en"])
        self._hide_all()
        self.practice_layout.opacity = 1; self.practice_layout.size_hint_y = 1
        self.engl_info.text = f"随机抽查 ({'英→中' if self.current_mode == 'en2cn' else '中→英'})"
        w = self._pick_random_word()
        self._show_word(w, self.current_mode)

    def mode_review(self, *a):
        due = self._get_review_words()
        if not due:
            show_popup("无待复习", "没有需要复习的单词！\n先做随机抽查来添加单词吧。")
            return
        self.current_mode = random.choice(["en2cn", "cn2en"])
        self._hide_all()
        self.practice_layout.opacity = 1; self.practice_layout.size_hint_y = 1
        self.engl_info.text = f"记忆曲线复习 ({len(due)}个待复习)"
        self.word_idx = 0
        self._show_review_word(due)

    def _show_review_word(self, due_list):
        if self.word_idx >= len(due_list):
            show_popup("复习完成", "所有待复习单词已完成！")
            return
        word, meaning, cycle = due_list[self.word_idx]
        self._show_word((word, meaning, ""), self.current_mode)

    def mode_fill(self, *a):
        self.current_mode = "fill"
        self._hide_all()
        self.practice_layout.opacity = 1; self.practice_layout.size_hint_y = 1
        self.engl_info.text = "单词补全"
        w = self._pick_random_word()
        self._show_word(w, "fill")

    def mode_wordlist(self, *a):
        self._hide_all()
        self.wordlist_layout.opacity = 1; self.wordlist_layout.size_hint_y = 1
        self.filter_words()

    def filter_words(self, *a):
        grade_filter = self.wl_grade_spinner.text
        wm = load_word_mastery()
        mastered = set(wm.get("words", {}).keys())

        # Clear
        self.wl_content.clear_widgets()

        filtered = WORD_LIST
        if grade_filter != "全部年级":
            filtered = [w for w in WORD_LIST if len(w) >= 3 and w[2] == grade_filter]

        total = len(filtered)
        mastered_count = sum(1 for w in filtered if w[0] in mastered)
        self.wl_stats.text = f"共{total}词 | 已掌握{mastered_count} | 未掌握{total-mastered_count}"

        s = load_settings()
        fs = s.get("font_size", 16) - 4

        for w in filtered[:80]:  # Show max 80 to avoid performance issues
            word, meaning = w[0], w[1]
            is_mastered = word in mastered
            mark = "✅" if is_mastered else "⬜"
            grade_str = w[2] if len(w) >= 3 else ""
            lbl = Label(text=f"{mark} {word} - {meaning} [{grade_str}]",
                        font_size=fs, halign="left", valign="middle",
                        color=get_theme()["text"], size_hint=(1, None), height=32)
            lbl.bind(width=lambda *x, l=lbl: setattr(l, 'text_size', (l.width, None)))

            def toggle_mastery(wd=word, lb=lbl):
                wm2 = load_word_mastery()
                if "words" not in wm2:
                    wm2["words"] = {}
                if wd in wm2["words"]:
                    del wm2["words"][wd]
                    lb.text = lb.text.replace("✅", "⬜")
                else:
                    wm2["words"][wd] = {
                        "meaning": meaning,
                        "last_review": str(datetime.now().date()),
                        "review_count": 0,
                        "interval_index": 0
                    }
                    lb.text = lb.text.replace("⬜", "✅")
                save_word_mastery(wm2)
                self.filter_words()

            lbl.bind(on_touch_down=toggle_mastery)
            self.wl_content.add_widget(lbl)

    def _on_engl_submit(self, *a):
        if not self.current_word:
            return
        user_ans = self.engl_input.text.strip().lower()
        if not user_ans:
            return
        word, meaning = self.current_word[0], self.current_word[1]
        correct = False

        if self.current_mode == "en2cn":
            # Check if meaning contains user's answer or vice versa
            correct = (meaning.lower().find(user_ans) >= 0) or (user_ans in meaning.lower())
        elif self.current_mode == "cn2en":
            correct = (user_ans == word.lower()) or (word.lower().find(user_ans) >= 0)
        elif self.current_mode == "fill":
            correct = (user_ans == word.lower())

        # Update word mastery
        wm = load_word_mastery()
        if "words" not in wm:
            wm["words"] = {}

        if correct:
            self.app.reward.add_stars(1, "english")
            self.app.reward.add_points(5)
            msg_parts = ["✅ 正确！"]
            if self.current_mode == "en2cn":
                msg_parts.append(f"{word} = {meaning}")
            elif self.current_mode == "cn2en":
                msg_parts.append(f"{meaning} = {word}")

            # Update mastery review schedule
            if word in wm["words"]:
                info = wm["words"][word]
                info["review_count"] = info.get("review_count", 0) + 1
                idx = info.get("interval_index", 0)
                idx = min(idx + 1, len(REVIEW_CYCLES) - 1)
                info["interval_index"] = idx
                info["last_review"] = str(datetime.now().date())
                msg_parts.append(f"下次复习：{REVIEW_CYCLES[idx]}天后")
            else:
                wm["words"][word] = {
                    "meaning": meaning,
                    "last_review": str(datetime.now().date()),
                    "review_count": 1,
                    "interval_index": 0
                }
                msg_parts.append("已加入复习计划")

            self.engl_feedback.text = "\n".join(msg_parts)
        else:
            self.app.reward.wrong_answer("english")
            msg_parts = [f"❌ 错误"]
            if self.current_mode == "en2cn":
                msg_parts.append(f"正确：{meaning}")
            elif self.current_mode == "cn2en":
                msg_parts.append(f"正确：{word}")
            elif self.current_mode == "fill":
                msg_parts.append(f"正确：{word}")
            self.engl_feedback.text = "\n".join(msg_parts)

        save_word_mastery(wm)
        self.engl_input.disabled = True
        self.engl_submit.disabled = True
        self.engl_next.disabled = False

    def _on_engl_next(self, *a):
        if self.current_mode == "review":
            due = self._get_review_words()
            self.word_idx += 1
            self._show_review_word(due)
        else:
            w = self._pick_random_word()
            self._show_word(w, self.current_mode)

    def _on_engl_speak(self, *a):
        if self.current_word:
            self._speak(self.current_word[0])

    def _on_engl_back(self, *a):
        self._hide_all()
        self.mode_layout.opacity = 1; self.mode_layout.size_hint_y = 1

    def wordlist_back(self, *a):
        self._hide_all()
        self.mode_layout.opacity = 1; self.mode_layout.size_hint_y = 1


class ExamPage(BoxLayout):
    def __init__(self, app, **kw):
        super().__init__(orientation='vertical', spacing=8, padding=10, **kw)
        self.app = app
        self.exam_questions = []
        self.exam_idx = 0
        self.exam_score = 0
        self.exam_active = False
        t = get_theme()
        s = load_settings()
        fs = s.get("font_size", 16)

        self.title_label = make_label("📝 考试模式", bold=True, size=fs+4, color_key="highlight")
        self.add_widget(self.title_label)

        self.exam_info = make_label("点击开始考试", size=fs, color_key="secondary")
        self.add_widget(self.exam_info)

        self.exam_question = make_label("", bold=True, size=fs, halign="left")
        self.exam_question.bind(width=lambda *x: setattr(self.exam_question, 'text_size', (self.exam_question.width, None)))
        self.add_widget(self.exam_question)

        self.exam_input = TextInput(hint_text="输入答案...", font_size=fs,
                                     multiline=False, size_hint=(1, None), height=45,
                                     background_color=t["card"], foreground_color=t["text"],
                                     disabled=True)
        self.exam_input.bind(on_text_validate=self.exam_submit)
        self.add_widget(self.exam_input)

        self.exam_submit_btn = Button(text="提交", font_size=fs, bold=True,
                                       background_color=t["primary"], color=(1,1,1,1),
                                       size_hint=(1, None), height=45, disabled=True)
        self.exam_submit_btn.bind(on_press=self.exam_submit)
        self.add_widget(self.exam_submit_btn)

        self.exam_next_btn = Button(text="下一题 →", font_size=fs, bold=True,
                                     background_color=t["success"], color=(1,1,1,1),
                                     size_hint=(1, None), height=45, disabled=True)
        self.exam_next_btn.bind(on_press=self.exam_next)
        self.add_widget(self.exam_next_btn)

        self.exam_feedback = make_label("", size=fs-2, color_key="text2", halign="left")
        self.exam_feedback.bind(width=lambda *x: setattr(self.exam_feedback, 'text_size', (self.exam_feedback.width, None)))
        self.add_widget(self.exam_feedback)

        self.exam_start_btn = Button(text="🚀 开始考试 (10题)", font_size=fs, bold=True,
                                      background_color=t["secondary"], color=(1,1,1,1),
                                      size_hint=(1, None), height=55)
        self.exam_start_btn.bind(on_press=self.start_exam)
        self.add_widget(self.exam_start_btn)

    def start_exam(self, *a):
        self.exam_questions = []
        for sub in ["math", "physics"]:
            sub_q = random.sample(ALL_SUBJECTS[sub], min(5, len(ALL_SUBJECTS[sub])))
            for q in sub_q:
                self.exam_questions.append((sub, q))
        # Also add some english words
        word_qs = random.sample(WORD_LIST, min(3, len(WORD_LIST)))
        for w in word_qs:
            self.exam_questions.append(("english", {
                "text": f"单词 '{w[0]}' 的中文意思是？",
                "answer": w[1].split("；")[0].split("/")[0].strip(),
                "explain": f"'{w[0]}' 的含义是 {w[1]}",
                "level": 1, "video": ""
            }))
        random.shuffle(self.exam_questions)
        self.exam_idx = 0
        self.exam_score = 0
        self.exam_active = True
        self.exam_start_btn.disabled = True
        self.show_exam_question()

    def show_exam_question(self):
        if self.exam_idx >= len(self.exam_questions):
            self.finish_exam()
            return
        sub, q = self.exam_questions[self.exam_idx]
        self.exam_info.text = f"第{self.exam_idx+1}/{len(self.exam_questions)}题 | 得分:{self.exam_score}"
        sub_name = {"math": "数学", "physics": "物理", "english": "英语"}.get(sub, sub)
        self.exam_question.text = f"【{sub_name}】{q['text']}"
        self.exam_input.text = ""
        self.exam_input.disabled = False
        self.exam_submit_btn.disabled = False
        self.exam_next_btn.disabled = True
        self.exam_feedback.text = ""

    def exam_submit(self, *a):
        if not self.exam_active or self.exam_idx >= len(self.exam_questions):
            return
        user_ans = self.exam_input.text.strip()
        if not user_ans:
            return
        sub, q = self.exam_questions[self.exam_idx]
        a = q["answer"].lower()
        u = user_ans.lower()
        correct = (a in u) or (u in a) or (u == a)
        if correct:
            self.exam_score += 10
            self.app.reward.add_stars(1, sub)
            self.app.reward.add_points(5)
            self.exam_feedback.text = f"✅ 正确 +10分\n{q.get('explain','')}"
        else:
            self.app.reward.wrong_answer(sub)
            add_mistake(sub, q["text"], user_ans, q["answer"], q.get("explain", ""))
            self.exam_feedback.text = f"❌ 错误\n正确：{q['answer']}\n{q.get('explain','')}"
        self.exam_info.text = f"第{self.exam_idx+1}/{len(self.exam_questions)}题 | 得分:{self.exam_score}"
        self.exam_input.disabled = True
        self.exam_submit_btn.disabled = True
        self.exam_next_btn.disabled = False

    def exam_next(self, *a):
        self.exam_idx += 1
        self.show_exam_question()

    def finish_exam(self):
        self.exam_active = False
        total = len(self.exam_questions) * 10
        self.exam_question.text = f"📊 考试结束！得分：{self.exam_score}/{total}"
        self.exam_input.disabled = True
        self.exam_submit_btn.disabled = True
        self.exam_next_btn.disabled = True
        self.exam_start_btn.disabled = False
        self.exam_start_btn.text = "🔄 再考一次"
        pct = int(self.exam_score / total * 100) if total > 0 else 0
        grade = "A" if pct >= 90 else "B" if pct >= 70 else "C" if pct >= 60 else "D"
        self.exam_feedback.text = f"评级：{grade} ({pct}%)"
        show_popup("📝 考试完成", f"得分：{self.exam_score}/{total}\n评级：{grade} ({pct}%)\n积分+{self.exam_score}")


class MorePage(BoxLayout):
    def __init__(self, app, **kw):
        super().__init__(orientation='vertical', spacing=8, padding=10, **kw)
        self.app = app
        t = get_theme()
        s = load_settings()
        fs = s.get("font_size", 16)

        # Tab buttons
        tab_layout = BoxLayout(size_hint=(1, None), height=40, spacing=4)
        self.tab_buttons = {}
        for text, key in [("错题本", "mistakes"), ("统计", "stats"), ("成就", "ach"), ("设置", "settings")]:
            btn = Button(text=text, font_size=fs-2, bold=True,
                         background_color=t["accent"], color=t["text"],
                         size_hint=(1, 1))
            btn.bind(on_press=lambda *a, k=key: self.show_tab(k))
            tab_layout.add_widget(btn)
            self.tab_buttons[key] = btn
        self.add_widget(tab_layout)

        # Content areas
        self.mistakes_layout = BoxLayout(orientation='vertical', spacing=6)
        self.mistakes_title = make_label("📖 错题本", bold=True, size=fs+2, color_key="highlight")
        self.mistakes_layout.add_widget(self.mistakes_title)

        self.mistakes_filter = Spinner(text="全部科目", values=["全部科目", "数学", "物理", "英语"],
                                        size_hint=(1, None), height=35)
        self.mistakes_filter.bind(text=self.load_mistakes)
        self.mistakes_layout.add_widget(self.mistakes_filter)

        self.mistakes_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.mistakes_content = BoxLayout(orientation='vertical', spacing=3, size_hint=(1, None))
        self.mistakes_content.bind(minimum_height=self.mistakes_content.setter('height'))
        self.mistakes_scroll.add_widget(self.mistakes_content)
        self.mistakes_layout.add_widget(self.mistakes_scroll)

        self.mistakes_clear = Button(text="🗑️ 清空错题本", font_size=fs,
                                       background_color=t["error"], color=(1,1,1,1),
                                       size_hint=(1, None), height=40)
        self.mistakes_clear.bind(on_press=self.clear_mistakes)
        self.mistakes_layout.add_widget(self.mistakes_clear)

        # Stats layout
        self.stats_layout = BoxLayout(orientation='vertical', spacing=6)
        self.stats_layout.add_widget(make_label("📊 学习统计", bold=True, size=fs+2, color_key="highlight"))
        self.stats_content = BoxLayout(orientation='vertical', spacing=4, size_hint=(1, None))
        self.stats_content.bind(minimum_height=self.stats_content.setter('height'))
        self.stats_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.stats_scroll.add_widget(self.stats_content)
        self.stats_layout.add_widget(self.stats_scroll)

        # Achievement layout
        self.ach_layout = BoxLayout(orientation='vertical', spacing=6)
        self.ach_layout.add_widget(make_label("🏆 成就系统", bold=True, size=fs+2, color_key="highlight"))
        self.ach_content = BoxLayout(orientation='vertical', spacing=4, size_hint=(1, None))
        self.ach_content.bind(minimum_height=self.ach_content.setter('height'))
        self.ach_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.ach_scroll.add_widget(self.ach_content)
        self.ach_layout.add_widget(self.ach_scroll)

        # Settings layout
        self.settings_layout = BoxLayout(orientation='vertical', spacing=8)
        self.settings_layout.add_widget(make_label("⚙️ 设置", bold=True, size=fs+2, color_key="highlight"))

        # Font size
        fs_layout = BoxLayout(size_hint=(1, None), height=50)
        fs_layout.add_widget(make_label("字体大小", size=fs, halign="left"))
        self.font_slider = Slider(min=12, max=24, value=s.get("font_size", 16), step=1)
        self.font_slider.bind(value=self.change_font_size)
        fs_layout.add_widget(self.font_slider)
        self.font_size_label = Label(text=f"{s.get('font_size', 16)}", font_size=fs,
                                      color=t["text"], size_hint=(None, 1))
        self.font_slider.bind(value=lambda v, l=self.font_size_label: setattr(l, 'text', f"{int(v)}"))
        fs_layout.add_widget(self.font_size_label)
        self.settings_layout.add_widget(fs_layout)

        # Theme
        theme_layout = BoxLayout(size_hint=(1, None), height=50)
        theme_layout.add_widget(make_label("主题", size=fs, halign="left"))
        self.theme_spinner = Spinner(text=s.get("theme", "dark"), values=["dark", "light"],
                                       size_hint=(0.6, 1))
        self.theme_spinner.bind(text=self.change_theme)
        theme_layout.add_widget(self.theme_spinner)
        self.settings_layout.add_widget(theme_layout)

        # Backup/Restore
        br_layout = BoxLayout(size_hint=(1, None), height=50, spacing=8)
        self.backup_btn = Button(text="备份数据", font_size=fs,
                                  background_color=t["primary"], color=(1,1,1,1),
                                  size_hint=(0.5, None), height=45)
        self.backup_btn.bind(on_press=self.backup_data)
        self.settings_layout.add_widget(self.backup_btn)

        self.restore_btn = Button(text="恢复数据", font_size=fs,
                                    background_color=t["secondary"], color=(1,1,1,1),
                                    size_hint=(0.5, None), height=45)
        self.restore_btn.bind(on_press=self.restore_data)
        self.settings_layout.add_widget(self.restore_btn)

        # About
        self.settings_layout.add_widget(Widget(size_hint=(1, 0.1)))
        self.settings_layout.add_widget(make_label("学练考系统 v2.0\nKivy手机APP版\n整合自适应训练+英语专项", size=fs-2, color_key="text2"))

        # Add all content areas
        self.content_areas = {
            "mistakes": self.mistakes_layout,
            "stats": self.stats_layout,
            "ach": self.ach_layout,
            "settings": self.settings_layout,
        }
        for layout in self.content_areas.values():
            self.add_widget(layout)

        # Show mistakes by default
        self.show_tab("mistakes")

    def show_tab(self, key):
        for k, layout in self.content_areas.items():
            layout.opacity = 1 if k == key else 0
            layout.size_hint_y = 1 if k == key else 0
        t = get_theme()
        for k, btn in self.tab_buttons.items():
            btn.background_color = t["primary"] if k == key else t["accent"]
        if key == "mistakes":
            self.load_mistakes()
        elif key == "stats":
            self.load_stats()
        elif key == "ach":
            self.load_achievements()

    def load_mistakes(self, *a):
        mistakes = load_mistakes()
        subject_filter = self.mistakes_filter.text
        self.mistakes_content.clear_widgets()

        sub_map = {"数学": "math", "物理": "physics", "英语": "english"}
        fs = load_settings().get("font_size", 16) - 4

        if subject_filter != "全部科目":
            mistakes = {sub_map.get(subject_filter, subject_filter): mistakes.get(sub_map.get(subject_filter, subject_filter), [])}

        total = sum(len(v) for v in mistakes.values())
        self.mistakes_title.text = f"📖 错题本 ({total}题)"

        if total == 0:
            self.mistakes_content.add_widget(make_label("✅ 暂无错题！", size=fs+2, color_key="success"))
            return

        sub_names = {"math": "📐 数学", "physics": "⚛️ 物理", "english": "📖 英语"}
        for sub, items in mistakes.items():
            if not items:
                continue
            self.mistakes_content.add_widget(make_label(
                f"{sub_names.get(sub, sub)} ({len(items)}题)", bold=True, size=fs, color_key="secondary", halign="left"))
            for item in items[-20:]:
                q_text = item.get('question', '')[:50]
                lbl = Label(
                    text=f"📌 {q_text}\n   ✗{item.get('user_answer','')[:30]} → ✓{item.get('correct_answer','')[:30]}\n   🕐{item.get('timestamp','')}",
                    font_size=fs-2, halign="left", valign="middle",
                    color=get_theme()["text"], size_hint=(1, None), height=55)
                lbl.bind(width=lambda *x, l=lbl: setattr(l, 'text_size', (l.width, None)))
                self.mistakes_content.add_widget(lbl)

    def clear_mistakes(self, *a):
        save_mistakes({"math": [], "physics": [], "english": []})
        self.load_mistakes()
        show_popup("已清空", "错题本已清空！")

    def load_stats(self):
        self.stats_content.clear_widgets()
        r = self.app.reward.data
        s = r.get("stats", {})
        fs = load_settings().get("font_size", 16) - 2
        stats_lines = [
            f"⭐ 总获得星星: {r.get('total_stars', 0)}",
            f"❤ 总获得爱心: {r.get('total_hearts_earned', 0)}",
            f"📊 等级: Lv.{r.get('level', 1)}",
            f"✅ 总正确: {s.get('total_correct', 0)}",
            f"❌ 总错误: {s.get('total_wrong', 0)}",
            f"🔥 最高连击: {r.get('max_combo', 0)}",
            f"📅 连续学习: {r.get('consecutive_days', 0)}天",
            "",
            "📐 数学",
            f"   ✅ {s.get('math_correct', 0)} | ❌ {s.get('math_wrong', 0)}",
            "",
            "⚛️ 物理",
            f"   ✅ {s.get('physics_correct', 0)} | ❌ {s.get('physics_wrong', 0)}",
            "",
            "📖 英语",
            f"   ✅ {s.get('english_correct', 0)} | ❌ {s.get('english_wrong', 0)}",
        ]
        for line in stats_lines:
            self.stats_content.add_widget(make_label(line, size=fs, halign="left"))

    def load_achievements(self):
        self.ach_content.clear_widgets()
        r = self.app.reward.data
        unlocked = r.get("achievements", [])
        fs = load_settings().get("font_size", 16) - 2

        for ach in RewardManager.ACHIEVEMENT_LIST:
            is_unlocked = ach["id"] in unlocked
            status = "✅" if is_unlocked else "🔒"
            lbl = Label(
                text=f"{status} {ach['icon']} {ach['name']}\n    {ach['desc']}",
                font_size=fs, halign="left", valign="middle",
                color=get_theme()["success"] if is_unlocked else get_theme()["text2"],
                size_hint=(1, None), height=45)
            lbl.bind(width=lambda *x, l=lbl: setattr(l, 'text_size', (l.width, None)))
            self.ach_content.add_widget(lbl)

    def show_stats(self):
        self.show_tab("stats")

    def show_settings(self):
        self.show_tab("settings")

    def change_font_size(self, *a):
        s = load_settings()
        s["font_size"] = int(self.font_slider.value)
        save_settings(s)

    def change_theme(self, *a):
        s = load_settings()
        s["theme"] = self.theme_spinner.text
        save_settings(s)
        show_popup("提示", "主题已更改，需重启APP生效。")

    def backup_data(self, *a):
        import zipfile
        backup_path = os.path.join(BASE_DIR, "study_backup.zip")
        files = ['mistakes.json', 'reward_data.json', 'word_mastery.json', 'settings.json']
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for f in files:
                    fp = os.path.join(BASE_DIR, f)
                    if os.path.exists(fp):
                        zf.write(fp, f)
            show_popup("备份成功", f"已备份到:\n{backup_path}")
        except Exception as e:
            show_popup("备份失败", str(e))

    def restore_data(self, *a):
        import zipfile
        backup_path = os.path.join(BASE_DIR, "study_backup.zip")
        if not os.path.exists(backup_path):
            show_popup("恢复失败", "未找到备份文件 study_backup.zip")
            return
        try:
            with zipfile.ZipFile(backup_path, 'r') as zf:
                zf.extractall(BASE_DIR)
            show_popup("恢复成功", "数据已恢复！需重启APP。")
        except Exception as e:
            show_popup("恢复失败", str(e))


# ==================== 主APP ====================
class StudyApp(App):
    def build(self):
        self.reward = RewardManager()
        self.title = "学练考系统"

        # Main layout
        self.root_layout = BoxLayout(orientation='vertical')

        # Content area
        self.content = BoxLayout(orientation='vertical')

        self.home_page = HomePage(self)
        self.training_page = TrainingPage(self)
        self.english_page = EnglishPage(self)
        self.exam_page = ExamPage(self)
        self.mistakes_page = MorePage(self)

        self.pages = [self.home_page, self.training_page, self.english_page,
                     self.exam_page, self.mistakes_page]
        self.current_tab = 0

        # Show first page
        for i, page in enumerate(self.pages):
            if i == 0:
                page.opacity = 1
                page.size_hint_y = 1
            else:
                page.opacity = 0
                page.size_hint_y = 0
            self.content.add_widget(page)

        self.root_layout.add_widget(self.content)

        # Bottom navigation bar
        t = get_theme()
        s = load_settings()
        fs = s.get("font_size", 16) - 4
        nav = BoxLayout(size_hint=(1, None), height=55, spacing=2,
                        padding=[0, 0, 0, 2])
        nav.canvas.before

        nav_items = [
            ("🏠首页", 0), ("🎯训练", 1), ("📖英语", 2),
            ("📝考试", 3), ("⚙️更多", 4)
        ]
        self.nav_buttons = []
        for text, idx in nav_items:
            btn = Button(text=text, font_size=fs, bold=True,
                         background_color=t["primary"] if idx == 0 else t["nav_bg"],
                         color=t["text"] if idx == 0 else t["text2"],
                         size_hint=(1, 1))
            btn.bind(on_press=lambda *a, i=idx: self.switch_tab(i))
            nav.add_widget(btn)
            self.nav_buttons.append(btn)

        self.root_layout.add_widget(nav)

        # Timer for status updates
        Clock.schedule_interval(self.update_timer, 30)

        return self.root_layout

    def switch_tab(self, idx):
        self.current_tab = idx
        t = get_theme()
        for i, page in enumerate(self.pages):
            if i == idx:
                page.opacity = 1
                page.size_hint_y = 1
            else:
                page.opacity = 0
                page.size_hint_y = 0
        for i, btn in enumerate(self.nav_buttons):
            btn.background_color = t["primary"] if i == idx else t["nav_bg"]
            btn.color = t["text"] if i == idx else t["text2"]
        # Refresh home page status
        if idx == 0:
            self.home_page.refresh_status()
            self.home_page.refresh_checkin()

    def update_timer(self, dt):
        # Track study time
        self.reward.data["daily_study_seconds"] = self.reward.data.get("daily_study_seconds", 0) + 30
        self.reward._check_study_time()
        self.reward.save()
        if self.current_tab == 0:
            self.home_page.refresh_status()
            self.home_page.refresh_checkin()


if __name__ == '__main__':
    StudyApp().run()
