# -*- coding: utf-8 -*-
"""
==========================================================================
    图片内容智能识别器 v1
    集成 OCR文字识别 + 视觉AI内容理解
    专为生物/地理教学图片设计
    
    支持三种识别模式：
    1. 视觉AI模式（需API Key）— 通义千问VL/智谱GLM-4V/兼容OpenAI视觉模型
    2. OCR+关键词模式（本地）— PaddleOCR识别文字 + 关键词分类
    3. 纯OCR模式（本地）— 仅识别图片上的文字
==========================================================================
"""

import os
import sys
import json
import base64
import threading
import time
from datetime import datetime
from pathlib import Path
from tkinter import (
    Tk, Frame, Label, Button, Entry, Text, Scrollbar, StringVar, OptionMenu,
    filedialog, messagebox, END, RIGHT, Y, BOTH, LEFT, BOTTOM, X, VERTICAL,
    HORIZONTAL, NORMAL, DISABLED, WORD, Checkbutton, Canvas, SUNKEN, Spinbox,
    IntVar, Toplevel
)
from tkinter.ttk import Progressbar, Notebook
import tkinter as tk

# 第三方库
try:
    from PIL import Image, ImageTk
    import cv2
    import numpy as np
except ImportError as e:
    print(f"缺少必要的库: {e}")
    print("请运行: pip install opencv-python pillow numpy")
    sys.exit(1)

# ============ 中文路径兼容 ============
def cv2_imread(filepath):
    try:
        img_array = np.fromfile(filepath, dtype=np.uint8)
        return cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"[错误] 读取失败 ({filepath}): {e}")
        return None


# ============ 视觉AI API 配置 ============
# 支持的视觉AI后端
VISION_BACKENDS = {
    "qwen_vl": {
        "name": "通义千问VL",
        "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-vl-plus",
        "env_key": "DASHSCOPE_API_KEY",
    },
    "zhipu": {
        "name": "智谱GLM-4V",
        "api_base": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4v-flash",
        "env_key": "ZHIPU_API_KEY",
    },
    "openai": {
        "name": "OpenAI兼容(自定义)",
        "api_base": "",
        "model": "gpt-4o",
        "env_key": "OPENAI_API_KEY",
    },
}

# ============ 生物/地理图片分类知识库 ============
BIO_KEYWORDS = {
    "显微镜结构": ["目镜", "物镜", "准焦螺旋", "转换器", "载物台", "反光镜", "遮光器", "镜筒", "压片夹"],
    "细胞结构": ["细胞壁", "细胞膜", "细胞核", "细胞质", "液泡", "叶绿体", "线粒体", "核膜", "核仁"],
    "制作装片": ["临时装片", "洋葱鳞片", "口腔上皮", "碘液", "盖玻片", "载玻片"],
    "草履虫": ["纤毛", "口沟", "胞肛", "伸缩泡", "食物泡", "收集管", "表膜", "大核", "小核"],
    "昆虫结构": ["触角", "复眼", "气门", "前足", "中足", "后足", "翅", "外骨骼"],
    "环节动物": ["体节", "刚毛", "环带", "蚯蚓"],
    "刺胞动物": ["触手", "内胚层", "外胚层", "消化腔", "芽体", "刺细胞", "水螅", "水母"],
    "扁形动物": ["眼点", "咽", "涡虫", "两侧对称"],
    "鱼类": ["鳃盖", "侧线", "尾鳍", "胸鳍", "背鳍", "臀鳍", "鳞片"],
    "两栖动物": ["鼓膜", "后肢粗壮", "蹼", "蛙", "蟾蜍"],
    "爬行动物": ["鳞片", "角质", "蜥蜴", "龟", "蛇"],
    "鸟类": ["胸骨", "龙骨突", "羽毛", "翼", "喙", "气囊", "双重呼吸"],
    "哺乳动物": ["膈肌", "胸腔", "腹腔", "家兔", "胎生", "哺乳"],
    "病毒": ["病毒", "噬菌体", "腺病毒", "烟草花叶", "蛋白质外壳", "遗传物质"],
    "分类等级": ["界门纲目科属种"],
    "叶芽结构": ["叶芽", "芽轴", "幼叶", "芽原基", "生长点"],
    "花的结构": ["花药", "花丝", "花瓣", "萼片", "柱头", "花柱", "子房", "胚珠"],
    "受精过程": ["花粉管", "受精卵", "卵细胞", "精子", "双受精", "极核"],
    "果实种子": ["子房壁", "胚珠", "珠被", "果皮", "种皮", "胚", "子叶"],
    "光合作用": ["二氧化碳+水", "有机物+氧气", "叶绿体", "光反应", "暗反应", "光下制造有机物"],
    "呼吸作用": ["萌发种子", "煮熟种子", "澄清的石灰水", "有机物分解", "线粒体"],
    "蒸腾作用": ["气孔", "保卫细胞", "蒸腾", "水分散失"],
    "消化系统": ["消化腺", "消化道", "十二指肠", "胃腺", "肠腺", "肝脏", "胰腺", "胆汁"],
    "消化曲线": ["营养物质未被消化", "淀粉", "蛋白质", "脂肪"],
    "呼吸系统": ["会厌软骨", "呼吸道", "肺", "气管", "支气管", "肺泡"],
    "循环系统": ["心脏", "心房", "心室", "瓣膜", "动脉", "静脉", "毛细血管"],
    "血液": ["血细胞", "红细胞", "白细胞", "血小板", "血浆", "血红蛋白"],
    "泌尿系统": ["肾脏", "肾单位", "肾小球", "肾小管", "输尿管", "膀胱", "尿液"],
    "神经系统": ["神经末梢", "反射弧", "感受器", "效应器", "神经中枢", "突触"],
    "眼球结构": ["角膜", "晶状体", "视网膜", "玻璃体", "虹膜", "瞳孔", "巩膜"],
    "近视远视": ["近视", "远视", "凹透镜", "凸透镜"],
    "耳结构": ["鼓膜", "听小骨", "耳蜗", "半规管", "前庭"],
    "内分泌系统": ["激素", "甲状腺", "垂体", "胰岛素", "生长激素", "肾上腺"],
    "传染病": ["传染源", "传播途径", "易感人群", "病原体"],
    "免疫": ["抗体", "抗原", "淋巴细胞", "吞噬细胞", "特异性免疫"],
    "食物链": ["被取食", "被捕食", "生产者", "消费者", "分解者"],
    "生态系统": ["太阳", "农作物", "生态平衡", "物质循环", "能量流动"],
    "DNA基因": ["遗传效", "蛋白质合成", "DNA", "染色体", "基因", "碱基"],
    "遗传图解": ["亲代", "子代", "高茎", "矮茎", "显性", "隐性", "基因型", "表现型"],
    "性别决定": ["22对+XY", "22对+XX", "性染色体", "常染色体"],
    "变异": ["可遗传变异", "不可遗传变异", "基因突变", "染色体变异"],
    "鸟卵结构": ["壳膜", "鸡卵", "胚盘", "卵黄", "卵白", "系带", "卵壳"],
    "生殖发育": ["卵巢", "输卵管", "受精卵", "精子", "子宫", "胎盘", "胚胎"],
    "植物类群": ["藻类", "苔藓", "蕨类", "种子植物", "裸子植物", "被子植物", "孢子"],
    "动物类群": ["无脊椎动物", "脊椎动物", "原生动物", "腔肠动物", "扁形动物", "线形动物", "环节动物", "软体动物", "节肢动物"],
    "微生物": ["细菌", "真菌", "酵母菌", "青霉", "蘑菇", "孢子繁殖", "分裂生殖", "芽孢"],
}

GEO_KEYWORDS = {
    "世界地图": ["大洲", "大洋", "赤道", "回归线", "极圈"],
    "中国地形": ["山脉", "高原", "盆地", "平原", "丘陵", "地势"],
    "中国气候": ["温度带", "干湿地区", "季风", "气候类型", "降水量"],
    "中国河流": ["长江", "黄河", "珠江", "淮河", "水系", "流域"],
    "中国资源": ["矿产资源", "土地资源", "水资源", "森林资源"],
    "中国农业": ["种植业", "畜牧业", "渔业", "林业", "农作物分布"],
    "中国工业": ["工业基地", "高新技术", "钢铁", "纺织"],
    "中国交通": ["铁路", "公路", "航空", "水运", "管道"],
    "中国人口": ["人口密度", "人口分布", "人口增长", "计划生育"],
    "中国民族": ["少数民族", "民族分布", "民族自治区"],
    "板块构造": ["板块", "火山", "地震", "海岭", "海沟", "俯冲"],
    "经纬度": ["经度", "纬度", "经线", "纬线", "本初子午线"],
    "等高线": ["等高线", "山脊", "山谷", "鞍部", "陡崖", "海拔"],
    "世界气候": ["热带", "温带", "寒带", "地中海", "海洋性", "大陆性"],
    "亚洲": ["亚洲", "东亚", "东南亚", "南亚", "西亚", "中亚"],
    "非洲": ["非洲", "撒哈拉", "尼罗河", "热带草原", "热带雨林"],
    "欧洲": ["欧洲", "欧盟", "阿尔卑斯", "莱茵河"],
    "美洲": ["北美洲", "南美洲", "安第斯", "落基山", "亚马逊"],
    "大洋洲": ["澳大利亚", "大自流盆地", "袋鼠", "考拉"],
    "极地": ["南极", "北极", "企鹅", "北极熊", "极昼", "极夜"],
    "湖南地理": ["湖南", "湘江", "洞庭湖", "长沙", "韶山"],
}

# 合并所有关键词
ALL_KEYWORDS = {}
ALL_KEYWORDS.update({f"bio_{k}": v for k, v in BIO_KEYWORDS.items()})
ALL_KEYWORDS.update({f"geo_{k}": v for k, v in GEO_KEYWORDS.items()})


def classify_by_keywords(texts):
    """根据OCR文字用关键词分类图片内容"""
    all_text = " ".join(texts)
    matches = {}
    for category, keywords in ALL_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in all_text)
        if score > 0:
            matches[category] = score
    
    if not matches:
        return "未知", 0, {}
    
    # 按得分排序
    sorted_matches = sorted(matches.items(), key=lambda x: x[1], reverse=True)
    best_cat, best_score = sorted_matches[0]
    return best_cat, best_score, dict(sorted_matches[:5])


def encode_image_base64(image_path):
    """将图片编码为base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def call_vision_api(image_path, api_key, api_base, model, prompt):
    """
    调用视觉AI API识别图片内容
    兼容 OpenAI Vision API 格式（通义千问VL、智谱GLM-4V都兼容此格式）
    """
    import openai
    
    b64_img = encode_image_base64(image_path)
    
    # 判断图片格式
    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".bmp": "image/bmp", ".webp": "image/webp"}
    mime_type = mime_map.get(ext, "image/png")
    
    client = openai.OpenAI(api_key=api_key, base_url=api_base)
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{b64_img}"
                        }
                    }
                ]
            }
        ],
        max_tokens=1000,
        temperature=0.1
    )
    
    return response.choices[0].message.content


class ImageAnalyzer:
    """图片内容智能识别器"""
    
    def __init__(self, parent_app_dir=None):
        self.root = Tk()
        self.root.title("图片内容智能识别器 - OCR + 视觉AI v1")
        self.root.geometry("1400x900")
        self.root.minsize(1024, 768)
        
        self.app_dir = parent_app_dir or os.path.dirname(os.path.abspath(__file__))
        
        # OCR引擎
        self.paddle_ocr = None
        self.paddle_available = False
        
        # 视觉AI配置
        self.vision_backend = StringVar(value="qwen_vl")
        self.api_key_var = StringVar(value=os.environ.get("DASHSCOPE_API_KEY", ""))
        self.api_base_var = StringVar(value="")
        self.model_var = StringVar(value="")
        
        # 识别模式
        self.recognize_mode = StringVar(value="combined")  # combined/vision/ocr_only
        
        # 图片列表
        self.image_list = []
        self.current_idx = 0
        self.current_image_tk = None
        self.batch_cancel = False
        
        # 结果存储
        self.results = {}  # filename -> {ocr_text, vision_desc, category, keywords}
        
        self._setup_ui()
        self._log("系统初始化中...")
        threading.Thread(target=self._load_ocr, daemon=True).start()
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _setup_ui(self):
        """构建界面"""
        # === 顶部：模式选择和配置 ===
        config_frame = Frame(self.root, bg="#F5F5F5")
        config_frame.pack(fill=X, padx=10, pady=5)
        
        # 识别模式
        Label(config_frame, text="识别模式:", bg="#F5F5F5", font=("Microsoft YaHei UI", 10)).pack(side=LEFT, padx=5)
        modes = [("🔍 综合(OCR+AI)", "combined"), ("🤖 仅视觉AI", "vision"), ("📝 仅OCR文字", "ocr_only")]
        for text, val in modes:
            tk.Radiobutton(config_frame, text=text, variable=self.recognize_mode, value=val,
                          bg="#F5F5F5", font=("Microsoft YaHei UI", 9),
                          indicatoron=0, padx=10, pady=3, bd=1, relief=tk.RAISED,
                          selectcolor="#4A90D9", activebackground="#4A90D9",
                          activeforeground="white").pack(side=LEFT, padx=3)
        
        # 分隔线
        Label(config_frame, text="  |  ", bg="#F5F5F5").pack(side=LEFT, padx=5)
        
        # 视觉AI后端选择
        Label(config_frame, text="AI引擎:", bg="#F5F5F5", font=("Microsoft YaHei UI", 10)).pack(side=LEFT, padx=5)
        backend_names = [VISION_BACKENDS[k]["name"] for k in VISION_BACKENDS]
        self.backend_menu = OptionMenu(config_frame, self.vision_backend, *VISION_BACKENDS.keys(),
                                       command=self._on_backend_change)
        # 显示名称映射
        self.backend_menu.pack(side=LEFT, padx=3)
        self.vision_backend.trace('w', self._on_backend_change_trace)
        
        # API Key
        Label(config_frame, text="API Key:", bg="#F5F5F5", font=("Microsoft YaHei UI", 10)).pack(side=LEFT, padx=5)
        self.api_key_entry = Entry(config_frame, width=30, show="*", font=("Microsoft YaHei UI", 9))
        self.api_key_entry.pack(side=LEFT, padx=3)
        self.api_key_entry.bind("<KeyRelease>", self._on_api_key_change)
        
        # 配置API按钮
        self.config_btn = Button(config_frame, text="⚙ API配置", font=("Microsoft YaHei UI", 9),
                                  command=self._show_api_config)
        self.config_btn.pack(side=LEFT, padx=5)
        
        # === 第二行：操作按钮 ===
        action_frame = Frame(self.root, bg="#F5F5F5")
        action_frame.pack(fill=X, padx=10, pady=2)
        
        Button(action_frame, text="📁 选择图片", font=("Microsoft YaHei UI", 10),
               command=self._select_images, bg="#4A90D9", fg="white", padx=12).pack(side=LEFT, padx=5)
        Button(action_frame, text="📂 选择文件夹", font=("Microsoft YaHei UI", 10),
               command=self._select_folder, bg="#4A90D9", fg="white", padx=12).pack(side=LEFT, padx=5)
        Button(action_frame, text="🔍 识别当前", font=("Microsoft YaHei UI", 10),
               command=self._recognize_current, bg="#27AE60", fg="white", padx=12).pack(side=LEFT, padx=5)
        Button(action_frame, text="🚀 批量识别", font=("Microsoft YaHei UI", 10),
               command=self._batch_recognize, bg="#E67E22", fg="white", padx=12).pack(side=LEFT, padx=5)
        self.cancel_btn = Button(action_frame, text="⏹ 停止", font=("Microsoft YaHei UI", 10),
                                  command=self._cancel_batch, bg="#E74C3C", fg="white", padx=12, state=DISABLED)
        self.cancel_btn.pack(side=LEFT, padx=5)
        
        # 图片导航
        Label(action_frame, text="  |  导航:", bg="#F5F5F5").pack(side=LEFT, padx=5)
        Button(action_frame, text="◀ 上一张", command=self._prev_image, font=("Microsoft YaHei UI", 9)).pack(side=LEFT, padx=2)
        self.nav_label = Label(action_frame, text="0/0", bg="#F5F5F5", font=("Microsoft YaHei UI", 10, "bold"))
        self.nav_label.pack(side=LEFT, padx=5)
        Button(action_frame, text="下一张 ▶", command=self._next_image, font=("Microsoft YaHei UI", 9)).pack(side=LEFT, padx=2)
        
        # 右侧：保存结果
        Button(action_frame, text="💾 保存结果JSON", font=("Microsoft YaHei UI", 10),
               command=self._save_results, bg="#8E44AD", fg="white", padx=12).pack(side=RIGHT, padx=5)
        Button(action_frame, text="📊 生成识图题", font=("Microsoft YaHei UI", 10),
               command=self._generate_questions, bg="#16A085", fg="white", padx=12).pack(side=RIGHT, padx=5)
        
        # === 主内容区域（三栏） ===
        main_frame = Frame(self.root)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        # 左栏：图片预览
        left_frame = Frame(main_frame, width=400)
        left_frame.pack(side=LEFT, fill=tk.Y, padx=(0, 5))
        left_frame.pack_propagate(False)
        
        Label(left_frame, text="📷 图片预览", font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w")
        self.image_canvas = Canvas(left_frame, bg='#E0E0E0', width=380, height=500)
        self.image_canvas.pack(fill=BOTH, expand=True, pady=5)
        
        # 图片信息
        self.img_info_label = Label(left_frame, text="", font=("Microsoft YaHei UI", 9),
                                     fg="#666666", wraplength=380, justify=tk.LEFT)
        self.img_info_label.pack(anchor="w", fill=tk.X)
        
        # 中栏：OCR文字结果
        mid_frame = Frame(main_frame, width=350)
        mid_frame.pack(side=LEFT, fill=tk.Y, padx=5)
        mid_frame.pack_propagate(False)
        
        Label(mid_frame, text="📝 OCR识别文字", font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w")
        ocr_frame = Frame(mid_frame)
        ocr_frame.pack(fill=BOTH, expand=True, pady=5)
        self.ocr_text = Text(ocr_frame, wrap=WORD, font=("Microsoft YaHei UI", 10),
                             bg="#FAFAFA", relief=tk.GROOVE, bd=1)
        ocr_scrollbar = Scrollbar(ocr_frame, orient=VERTICAL, command=self.ocr_text.yview)
        self.ocr_text.config(yscrollcommand=ocr_scrollbar.set)
        ocr_scrollbar.pack(side=RIGHT, fill=Y)
        self.ocr_text.pack(side=LEFT, fill=BOTH, expand=True)
        
        # 关键词分类结果
        Label(mid_frame, text="🏷 关键词分类", font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w", pady=(10, 0))
        self.category_text = Text(mid_frame, wrap=WORD, font=("Microsoft YaHei UI", 10),
                                   height=8, bg="#FFF8E1", relief=tk.GROOVE, bd=1)
        self.category_text.pack(fill=tk.X, pady=5)
        
        # 右栏：AI视觉理解结果
        right_frame = Frame(main_frame)
        right_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(5, 0))
        
        Label(right_frame, text="🤖 AI内容理解", font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w")
        ai_frame = Frame(right_frame)
        ai_frame.pack(fill=BOTH, expand=True, pady=5)
        self.ai_text = Text(ai_frame, wrap=WORD, font=("Microsoft YaHei UI", 10),
                            bg="#E8F5E9", relief=tk.GROOVE, bd=1)
        ai_scrollbar = Scrollbar(ai_frame, orient=VERTICAL, command=self.ai_text.yview)
        self.ai_text.config(yscrollcommand=ai_scrollbar.set)
        ai_scrollbar.pack(side=RIGHT, fill=Y)
        self.ai_text.pack(side=LEFT, fill=BOTH, expand=True)
        
        # === 底部状态栏 ===
        status_frame = Frame(self.root)
        status_frame.pack(side=BOTTOM, fill=X)
        self.status_bar = Label(status_frame, text="就绪", bd=1, relief=SUNKEN, anchor="w",
                                font=("Microsoft YaHei UI", 9))
        self.status_bar.pack(fill=tk.X)
        self.progress_bar = Progressbar(status_frame, mode='determinate')
        self.progress_bar.pack(fill=X)
    
    # ==================== OCR引擎 ====================
    
    def _load_ocr(self):
        """加载PaddleOCR"""
        try:
            from paddleocr import PaddleOCR
            self.paddle_ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False, rec_batch_num=8)
            self.paddle_available = True
            self._log("✓ PaddleOCR 引擎加载完成")
        except Exception as e:
            self.paddle_available = False
            self._log(f"✗ PaddleOCR 加载失败: {e}")
    
    def _ocr_image(self, image_path):
        """用PaddleOCR识别单张图片"""
        if not self.paddle_available:
            return []
        try:
            # 预处理：缩小大图
            img = cv2_imread(image_path)
            if img is None:
                return []
            h, w = img.shape[:2]
            if w > 1600 or h > 1200:
                scale = min(1600 / w, 1200 / h)
                img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
                # 保存临时文件
                temp_path = os.path.join(self.app_dir, f"_temp_ocr_{int(time.time())}.jpg")
                result_cv, buf = cv2.imencode('.jpg', img)
                if result_cv:
                    buf.tofile(temp_path)
                else:
                    temp_path = image_path
            else:
                temp_path = image_path
            
            result = self.paddle_ocr.ocr(temp_path, cls=True)
            
            # 清理临时文件
            if temp_path != image_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            
            texts = []
            if result and result[0]:
                for line in result[0]:
                    texts.append(line[1][0])
            return texts
        except Exception as e:
            self._log(f"OCR识别出错: {e}")
            return []
    
    # ==================== 视觉AI ====================
    
    def _get_vision_config(self):
        """获取当前视觉AI配置"""
        backend_key = self.vision_backend.get()
        backend = VISION_BACKENDS.get(backend_key, VISION_BACKENDS["qwen_vl"])
        
        api_key = self.api_key_entry.get().strip()
        api_base = backend["api_base"]
        model = backend["model"]
        
        if not api_key:
            # 尝试环境变量
            api_key = os.environ.get(backend["env_key"], "")
        
        return api_key, api_base, model
    
    def _vision_analyze(self, image_path):
        """用视觉AI分析图片内容"""
        api_key, api_base, model = self._get_vision_config()
        
        if not api_key:
            return None, "未配置API Key，请在顶部输入或点击⚙配置"
        
        prompt = """你是一个专业的生物和地理教学图片分析专家。请分析这张图片，给出以下信息：

1. **图片类型**：这是生物图片还是地理图片？
2. **具体内容**：图片具体展示的是什么？（如"显微镜结构图"、"中国气候类型分布图"等）
3. **标注内容**：图中有哪些标注的文字或数字？分别标注的是什么结构/区域？
4. **学科知识点**：这张图对应哪个知识点？（如"七年级生物上册-显微镜的使用"）
5. **适合出题方向**：基于这张图，可以出哪些类型的识图题？

请用简洁的中文回答。"""
        
        try:
            result = call_vision_api(image_path, api_key, api_base, model, prompt)
            return result, None
        except Exception as e:
            return None, f"API调用失败: {e}"
    
    # ==================== 图片选择与导航 ====================
    
    def _select_images(self):
        """选择图片文件"""
        paths = filedialog.askopenfilenames(
            title="选择图片文件（可多选）",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp *.tiff *.webp"), ("所有文件", "*.*")]
        )
        if paths:
            self.image_list = list(paths)
            self.current_idx = 0
            self._show_current_image()
            self.nav_label.config(text=f"1/{len(self.image_list)}")
    
    def _select_folder(self):
        """选择文件夹"""
        folder = filedialog.askdirectory(title="选择包含图片的文件夹")
        if not folder:
            return
        
        image_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}
        paths = []
        for f in os.listdir(folder):
            ext = os.path.splitext(f)[1].lower()
            if ext in image_exts:
                paths.append(os.path.join(folder, f))
        
        if not paths:
            messagebox.showinfo("提示", "文件夹中没有找到图片文件")
            return
        
        self.image_list = sorted(paths)
        self.current_idx = 0
        self._show_current_image()
        self.nav_label.config(text=f"1/{len(self.image_list)}")
    
    def _show_current_image(self):
        """显示当前图片"""
        if not self.image_list:
            return
        
        path = self.image_list[self.current_idx]
        try:
            img = Image.open(path)
            # 获取尺寸信息
            w, h = img.size
            fsize = os.path.getsize(path) / 1024
            self.img_info_label.config(text=f"📄 {os.path.basename(path)}\n📐 {w}×{h}px | {fsize:.1f}KB")
            
            img.thumbnail((380, 500))
            self.current_image_tk = ImageTk.PhotoImage(img)
            self.image_canvas.delete("all")
            self.image_canvas.create_image(190, 250, anchor="center", image=self.current_image_tk)
            
            # 如果已有结果则显示
            fname = os.path.basename(path)
            if fname in self.results:
                self._display_result(self.results[fname])
            
            self.nav_label.config(text=f"{self.current_idx + 1}/{len(self.image_list)}")
        except Exception as e:
            self._log(f"图片加载失败: {e}")
    
    def _prev_image(self):
        if self.image_list and self.current_idx > 0:
            self.current_idx -= 1
            self._show_current_image()
    
    def _next_image(self):
        if self.image_list and self.current_idx < len(self.image_list) - 1:
            self.current_idx += 1
            self._show_current_image()
    
    # ==================== 识别操作 ====================
    
    def _recognize_current(self):
        """识别当前图片"""
        if not self.image_list:
            messagebox.showwarning("提示", "请先选择图片")
            return
        
        path = self.image_list[self.current_idx]
        mode = self.recognize_mode.get()
        
        self.status_bar.config(text="识别中...")
        threading.Thread(target=self._do_recognize, args=(path, mode), daemon=True).start()
    
    def _do_recognize(self, image_path, mode="combined"):
        """执行识别（子线程）"""
        fname = os.path.basename(image_path)
        result = {"file": fname, "path": image_path}
        
        start = time.time()
        
        # OCR识别（combined和ocr_only模式都执行）
        if mode in ("combined", "ocr_only"):
            self.root.after(0, lambda: self.status_bar.config(text="OCR文字识别中..."))
            texts = self._ocr_image(image_path)
            result["ocr_texts"] = texts
            
            # 关键词分类
            category, score, top_matches = classify_by_keywords(texts)
            result["keyword_category"] = category
            result["keyword_score"] = score
            result["keyword_matches"] = top_matches
            
            # 显示OCR结果
            self.root.after(0, lambda t=texts: self._show_ocr_result(t))
            self.root.after(0, lambda c=category, s=score, m=top_matches: self._show_category_result(c, s, m))
        
        # 视觉AI识别（combined和vision模式都执行）
        if mode in ("combined", "vision"):
            self.root.after(0, lambda: self.status_bar.config(text="AI视觉分析中..."))
            vision_result, error = self._vision_analyze(image_path)
            result["vision_desc"] = vision_result
            result["vision_error"] = error
            
            if vision_result:
                self.root.after(0, lambda v=vision_result: self._show_vision_result(v))
            elif error:
                self.root.after(0, lambda e=error: self._show_vision_result(f"❌ {e}"))
        
        elapsed = time.time() - start
        result["elapsed"] = elapsed
        
        # 保存结果
        self.results[fname] = result
        
        self.root.after(0, lambda e=elapsed: self.status_bar.config(text=f"识别完成（{e:.1f}秒）"))
        self.root.after(0, lambda: self._log(f"✓ {fname} 识别完成（{elapsed:.1f}秒）"))
    
    def _show_ocr_result(self, texts):
        """显示OCR文字结果"""
        self.ocr_text.delete("1.0", END)
        if texts:
            for i, t in enumerate(texts, 1):
                self.ocr_text.insert(END, f"{i}. {t}\n")
        else:
            self.ocr_text.insert(END, "（未识别到文字）")
    
    def _show_category_result(self, category, score, matches):
        """显示关键词分类结果"""
        self.category_text.delete("1.0", END)
        prefix = category.split("_")[0]
        cat_name = "_".join(category.split("_")[1:]) if "_" in category else category
        subject = "生物" if prefix == "bio" else "地理" if prefix == "geo" else "未知"
        
        self.category_text.insert(END, f"📌 学科：{subject}\n")
        self.category_text.insert(END, f"🏷 分类：{cat_name}\n")
        self.category_text.insert(END, f"⭐ 匹配度：{score}个关键词\n\n")
        
        if matches:
            self.category_text.insert(END, "Top匹配：\n")
            for cat, s in matches.items():
                p = cat.split("_")[0]
                n = "_".join(cat.split("_")[1:])
                self.category_text.insert(END, f"  {p}/{n}: {s}分\n")
    
    def _show_vision_result(self, text):
        """显示视觉AI结果"""
        self.ai_text.delete("1.0", END)
        self.ai_text.insert(END, text)
    
    def _display_result(self, result):
        """显示已保存的结果"""
        if "ocr_texts" in result:
            self._show_ocr_result(result["ocr_texts"])
        if "keyword_category" in result:
            self._show_category_result(result["keyword_category"], 
                                        result.get("keyword_score", 0),
                                        result.get("keyword_matches", {}))
        if "vision_desc" in result and result["vision_desc"]:
            self._show_vision_result(result["vision_desc"])
        elif "vision_error" in result and result["vision_error"]:
            self._show_vision_result(f"❌ {result['vision_error']}")
    
    # ==================== 批量识别 ====================
    
    def _batch_recognize(self):
        """批量识别所有图片"""
        if not self.image_list:
            messagebox.showwarning("提示", "请先选择图片")
            return
        
        total = len(self.image_list)
        self.batch_cancel = False
        self.cancel_btn.config(state=NORMAL)
        self.progress_bar['mode'] = 'determinate'
        self.progress_bar['maximum'] = total
        self.progress_bar['value'] = 0
        
        mode = self.recognize_mode.get()
        self._log(f"\n🚀 批量识别开始：{total}张图片，模式：{mode}")
        
        def batch_worker():
            for i, path in enumerate(self.image_list):
                if self.batch_cancel:
                    break
                self.current_idx = i
                self.root.after(0, lambda: self._show_current_image())
                self._do_recognize(path, mode)
                self.root.after(0, lambda v=i+1: self.progress_bar.update(value=v))
                self.root.after(0, lambda v=i+1, t=total: self.nav_label.config(text=f"{v}/{t}"))
            
            self.root.after(0, lambda: self.cancel_btn.config(state=DISABLED))
            done = len(self.results)
            self.root.after(0, lambda: self.status_bar.config(text=f"批量识别完成，共{done}张"))
            self._log(f"🏁 批量识别完成！共{done}张\n")
        
        threading.Thread(target=batch_worker, daemon=True).start()
    
    def _cancel_batch(self):
        self.batch_cancel = True
        self._log("⚠ 正在取消...")
    
    # ==================== 保存与导出 ====================
    
    def _save_results(self):
        """保存识别结果为JSON"""
        if not self.results:
            messagebox.showwarning("提示", "还没有识别结果")
            return
        
        path = filedialog.asksaveasfilename(
            title="保存识别结果",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json")],
            initialdir=self.app_dir,
            initialfile=f"image_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            self._log(f"✓ 结果已保存到：{path}")
    
    def _generate_questions(self):
        """根据识别结果生成识图题"""
        if not self.results:
            messagebox.showwarning("提示", "请先识别图片")
            return
        
        # 收集所有有分类结果的数据
        questions = []
        for fname, data in self.results.items():
            category = data.get("keyword_category", "未知")
            if category == "未知":
                continue
            
            texts = data.get("ocr_texts", [])
            all_text = " ".join(texts)
            prefix = category.split("_")[0]
            
            # 根据分类生成题目
            q = {
                "image": f"/shitu_images/{fname}",
                "category": category,
                "subject": "bio" if prefix == "bio" else "geo",
                "ocr_texts": texts,
                "vision_desc": data.get("vision_desc", ""),
            }
            questions.append(q)
        
        if not questions:
            messagebox.showinfo("提示", "没有可用的分类结果来生成题目")
            return
        
        # 保存题目数据
        path = os.path.join(self.app_dir, f"image_analysis_questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)
        
        self._log(f"✓ 已生成 {len(questions)} 条识图题数据，保存到：{path}")
        self._log("  提示：可使用 _gen_shitu_v2.py 基于此数据生成完整题目")
    
    # ==================== API配置 ====================
    
    def _on_backend_change_trace(self, *args):
        self._on_backend_change(self.vision_backend.get())
    
    def _on_backend_change(self, backend_key):
        backend = VISION_BACKENDS.get(backend_key, VISION_BACKENDS["qwen_vl"])
        # 尝试从环境变量获取key
        env_key = os.environ.get(backend["env_key"], "")
        if env_key and not self.api_key_entry.get().strip():
            self.api_key_entry.delete(0, END)
            self.api_key_entry.insert(0, env_key)
    
    def _on_api_key_change(self, event=None):
        pass  # 实时读取
    
    def _show_api_config(self):
        """显示API配置对话框"""
        win = Toplevel(self.root)
        win.title("视觉AI API 配置")
        win.geometry("550x400")
        win.transient(self.root)
        win.grab_set()
        
        # 说明
        info = Label(win, text="配置视觉AI后端，用于智能识别图片内容\n"
                    "推荐：通义千问VL（免费额度，中文效果好）\n"
                    "获取API Key：https://dashscope.console.aliyun.com/",
                    font=("Microsoft YaHei UI", 10), justify=tk.LEFT, fg="#333")
        info.pack(padx=20, pady=15, anchor="w")
        
        # 后端选择
        f1 = Frame(win)
        f1.pack(fill=X, padx=20, pady=5)
        Label(f1, text="AI引擎:", font=("Microsoft YaHei UI", 10)).pack(side=LEFT)
        for key, info_dict in VISION_BACKENDS.items():
            rb = tk.Radiobutton(f1, text=info_dict["name"], variable=self.vision_backend, value=key,
                               font=("Microsoft YaHei UI", 9))
            rb.pack(side=LEFT, padx=8)
        
        # API Key
        f2 = Frame(win)
        f2.pack(fill=X, padx=20, pady=10)
        Label(f2, text="API Key:", font=("Microsoft YaHei UI", 10)).pack(anchor="w")
        key_entry = Entry(f2, width=50, show="*", font=("Microsoft YaHei UI", 10))
        key_entry.pack(fill=X, pady=5)
        # 填入当前值
        current_key = self.api_key_entry.get()
        if current_key:
            key_entry.insert(0, current_key)
        
        # 自定义API Base（仅OpenAI兼容模式需要）
        f3 = Frame(win)
        f3.pack(fill=X, padx=20, pady=5)
        Label(f3, text="自定义API地址(仅OpenAI兼容模式):", font=("Microsoft YaHei UI", 10)).pack(anchor="w")
        base_entry = Entry(f3, width=50, font=("Microsoft YaHei UI", 10))
        base_entry.pack(fill=X, pady=5)
        backend = VISION_BACKENDS.get(self.vision_backend.get(), VISION_BACKENDS["openai"])
        base_entry.insert(0, backend["api_base"])
        
        # 自定义模型
        f4 = Frame(win)
        f4.pack(fill=X, padx=20, pady=5)
        Label(f4, text="模型名称:", font=("Microsoft YaHei UI", 10)).pack(anchor="w")
        model_entry = Entry(f4, width=50, font=("Microsoft YaHei UI", 10))
        model_entry.pack(fill=X, pady=5)
        model_entry.insert(0, backend["model"])
        
        # 保存按钮
        def save_config():
            key = key_entry.get().strip()
            self.api_key_entry.delete(0, END)
            self.api_key_entry.insert(0, key)
            
            # 如果是OpenAI兼容模式，更新base和model
            if self.vision_backend.get() == "openai":
                VISION_BACKENDS["openai"]["api_base"] = base_entry.get().strip()
                VISION_BACKENDS["openai"]["model"] = model_entry.get().strip()
            
            # 保存到配置文件
            config_path = os.path.join(self.app_dir, "_vision_api_config.json")
            config = {
                "backend": self.vision_backend.get(),
                "api_key": key,
                "api_base": base_entry.get().strip() if self.vision_backend.get() == "openai" else "",
                "model": model_entry.get().strip() if self.vision_backend.get() == "openai" else "",
            }
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            self._log(f"✓ API配置已保存")
            win.destroy()
        
        Button(win, text="💾 保存配置", font=("Microsoft YaHei UI", 11),
               bg="#4A90D9", fg="white", padx=20, pady=6, command=save_config).pack(pady=15)
    
    # ==================== 工具方法 ====================
    
    def _log(self, msg):
        """日志输出到AI结果区域"""
        self.ai_text.insert(END, f"\n{msg}\n")
        self.ai_text.see(END)
    
    def _on_closing(self):
        self.batch_cancel = True
        if messagebox.askokcancel("退出", "确定要退出吗？"):
            self.root.destroy()
    
    def run(self):
        # 加载保存的API配置
        config_path = os.path.join(self.app_dir, "_vision_api_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                if config.get("backend"):
                    self.vision_backend.set(config["backend"])
                if config.get("api_key"):
                    self.api_key_entry.delete(0, END)
                    self.api_key_entry.insert(0, config["api_key"])
                if config.get("api_base") and config["backend"] == "openai":
                    VISION_BACKENDS["openai"]["api_base"] = config["api_base"]
                if config.get("model") and config["backend"] == "openai":
                    VISION_BACKENDS["openai"]["model"] = config["model"]
            except:
                pass
        
        self.root.mainloop()


if __name__ == "__main__":
    app = ImageAnalyzer()
    app.run()
