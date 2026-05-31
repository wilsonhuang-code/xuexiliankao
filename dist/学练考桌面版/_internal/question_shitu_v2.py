# -*- coding: utf-8 -*-
"""
识图卡题库 - 重新编写版
每道题基于图片实际内容编写，确保图-题-答案匹配
"""
import random

# ==================== 显微镜系列 ====================
MICROSCOPE_QUESTIONS = [
    {
        "id": "shitu_microscope_01",
        "chapter_id": "bio_7_1_1",
        "image": "image1.png",
        "question": "图中①所示的结构名称是？",
        "options": ["目镜", "物镜", "转换器", "粗准焦螺旋"],
        "answer": "A",
        "explanation": "①是目镜，位于镜筒上方，观察时眼睛对着目镜。"
    },
    {
        "id": "shitu_microscope_02",
        "chapter_id": "bio_7_1_1",
        "image": "image1.png",
        "question": "图中⑦所示的结构名称是？",
        "options": ["粗准焦螺旋", "细准焦螺旋", "转换器", "镜臂"],
        "answer": "A",
        "explanation": "⑦是粗准焦螺旋，用于较大幅度升降镜筒。"
    },
    {
        "id": "shitu_microscope_03",
        "chapter_id": "bio_7_1_1",
        "image": "image1.png",
        "question": "图中③所示的结构名称是？",
        "options": ["目镜", "物镜", "转换器", "镜筒"],
        "answer": "B",
        "explanation": "③是物镜，安装在转换器上，接近玻片标本。"
    },
    {
        "id": "shitu_microscope_04",
        "chapter_id": "bio_7_1_1",
        "image": "image4.png",
        "question": "图中①所示的结构名称是？",
        "options": ["目镜", "镜筒", "转换器", "粗准焦螺旋"],
        "answer": "A",
        "explanation": "①是目镜，位于显微镜最上方。"
    },
    {
        "id": "shitu_microscope_05",
        "chapter_id": "bio_7_1_1",
        "image": "image4.png",
        "question": "转动图中⑧可以使镜筒升降幅度较小，该结构名称是？",
        "options": ["粗准焦螺旋", "细准焦螺旋", "转换器", "镜臂"],
        "answer": "B",
        "explanation": "⑧是细准焦螺旋，使镜筒升降幅度较小，用于精细调焦。"
    },
]

# ==================== 细胞结构系列 ====================
CELL_QUESTIONS = [
    {
        "id": "shitu_cell_01",
        "chapter_id": "bio_7_1_2",
        "image": "image5.png",
        "question": "图中①所示的结构名称是？",
        "options": ["细胞壁", "细胞膜", "细胞核", "叶绿体"],
        "answer": "A",
        "explanation": "①是细胞壁，植物细胞特有，位于细胞最外层，起保护和支持作用。"
    },
    {
        "id": "shitu_cell_02",
        "chapter_id": "bio_7_1_2",
        "image": "image5.png",
        "question": "图中④所示的结构名称是？",
        "options": ["细胞膜", "叶绿体", "液泡", "线粒体"],
        "answer": "B",
        "explanation": "④是叶绿体，植物细胞特有，是光合作用的场所。"
    },
    {
        "id": "shitu_cell_03",
        "chapter_id": "bio_7_1_2",
        "image": "image5.png",
        "question": "图中⑥所示的结构名称是？",
        "options": ["细胞核", "细胞质", "液泡", "线粒体"],
        "answer": "C",
        "explanation": "⑥是液泡，内含细胞液，可储存糖类、色素等物质。"
    },
    {
        "id": "shitu_cell_04",
        "chapter_id": "bio_7_1_2",
        "image": "image5.png",
        "question": "图中能控制物质进出细胞的结构是？",
        "options": ["①细胞壁", "②细胞膜", "③细胞核", "④叶绿体"],
        "answer": "B",
        "explanation": "②细胞膜能控制物质进出细胞，让有用的物质进入，有害的物质挡在外面。"
    },
    {
        "id": "shitu_cell_05",
        "chapter_id": "bio_7_1_2",
        "image": "image5.png",
        "question": "图中含有遗传物质、控制细胞生命活动的结构是？",
        "options": ["①细胞壁", "②细胞膜", "③细胞核", "⑤细胞质"],
        "answer": "C",
        "explanation": "③细胞核内含有遗传物质，控制着生物的发育和遗传。"
    },
]

# ==================== 草履虫结构系列 ====================
PARAMECIUM_QUESTIONS = [
    {
        "id": "shitu_paramecium_01",
        "chapter_id": "bio_7_1_3",
        "image": "image14.png",
        "question": "图中①所示的结构名称是？",
        "options": ["胞肛", "食物泡", "口沟", "纤毛"],
        "answer": "A",
        "explanation": "①是胞肛，位于草履虫后端，用于排出食物残渣。"
    },
    {
        "id": "shitu_paramecium_02",
        "chapter_id": "bio_7_1_3",
        "image": "image14.png",
        "question": "图中②所示的结构名称是？",
        "options": ["胞肛", "食物泡", "伸缩泡", "收集管"],
        "answer": "B",
        "explanation": "②是食物泡，食物在食物泡内进行消化。"
    },
    {
        "id": "shitu_paramecium_03",
        "chapter_id": "bio_7_1_3",
        "image": "image14.png",
        "question": "图中③所示的结构名称是？",
        "options": ["胞肛", "食物泡", "口沟", "纤毛"],
        "answer": "C",
        "explanation": "③是口沟，位于草履虫前端，食物由此进入体内。"
    },
    {
        "id": "shitu_paramecium_04",
        "chapter_id": "bio_7_1_3",
        "image": "image14.png",
        "question": "图中④所示的结构名称是？",
        "options": ["纤毛", "伸缩泡", "表膜", "细胞核"],
        "answer": "A",
        "explanation": "④是纤毛，草履虫靠纤毛的摆动在水中旋转前进。"
    },
    {
        "id": "shitu_paramecium_05",
        "chapter_id": "bio_7_1_3",
        "image": "image14.png",
        "question": "图中⑧所示的结构名称是？",
        "options": ["伸缩泡", "收集管", "表膜", "大核"],
        "answer": "C",
        "explanation": "⑧是表膜（即细胞膜），氧气通过表膜渗入，二氧化碳通过表膜排出。"
    },
    {
        "id": "shitu_paramecium_06",
        "chapter_id": "bio_7_1_3",
        "image": "image14.png",
        "question": "图中负责收集和排出体内多余水分的结构是？",
        "options": ["①胞肛", "②食物泡", "⑨伸缩泡", "④纤毛"],
        "answer": "C",
        "explanation": "⑨伸缩泡和⑩收集管协同工作，收集并排出体内多余水分，调节渗透压。"
    },
]

# ==================== 蝗虫结构系列 ====================
GRASSHOPPER_QUESTIONS = [
    {
        "id": "shitu_grasshopper_01",
        "chapter_id": "bio_7_2_3",
        "image": "image15.png",
        "question": "蝗虫的身体分为几个部分？",
        "options": ["两部分", "三部分", "四部分", "五部分"],
        "answer": "B",
        "explanation": "蝗虫身体分为头部、胸部、腹部三部分。"
    },
    {
        "id": "shitu_grasshopper_02",
        "chapter_id": "bio_7_2_3",
        "image": "image15.png",
        "question": "图中①所示的结构名称是？",
        "options": ["头部", "胸部", "腹部", "尾部"],
        "answer": "A",
        "explanation": "①是头部，有触角、复眼、单眼和口器。"
    },
    {
        "id": "shitu_grasshopper_03",
        "chapter_id": "bio_7_2_3",
        "image": "image15.png",
        "question": "图中②所示的结构名称是？",
        "options": ["头部", "胸部", "腹部", "尾部"],
        "answer": "B",
        "explanation": "②是胸部，有三对足和两对翅，是运动中心。"
    },
    {
        "id": "shitu_grasshopper_04",
        "chapter_id": "bio_7_2_3",
        "image": "image15.png",
        "question": "图中③所示的结构名称是？",
        "options": ["头部", "胸部", "腹部", "尾部"],
        "answer": "C",
        "explanation": "③是腹部，有气门，是呼吸和生殖中心。"
    },
    {
        "id": "shitu_grasshopper_05",
        "chapter_id": "bio_7_2_3",
        "image": "image15.png",
        "question": "蝗虫的呼吸器官是？",
        "options": ["肺", "气管", "鳃", "皮肤"],
        "answer": "B",
        "explanation": "蝗虫通过气门与气管相连，进行气体交换。"
    },
]

# ==================== 蚯蚓结构系列 ====================
EARTHWORM_QUESTIONS = [
    {
        "id": "shitu_earthworm_01",
        "chapter_id": "bio_7_2_3",
        "image": "image16.png",
        "question": "图中①所示的结构名称是？",
        "options": ["体节", "刚毛", "环带", "口"],
        "answer": "A",
        "explanation": "①是体节，蚯蚓身体由许多体节构成。"
    },
    {
        "id": "shitu_earthworm_02",
        "chapter_id": "bio_7_2_3",
        "image": "image16.png",
        "question": "图中②所示的结构名称是？",
        "options": ["体节", "刚毛", "环带", "肛门"],
        "answer": "B",
        "explanation": "②是刚毛，蚯蚓靠刚毛和肌肉配合运动。"
    },
    {
        "id": "shitu_earthworm_03",
        "chapter_id": "bio_7_2_3",
        "image": "image16.png",
        "question": "图中③所示的结构名称是？",
        "options": ["体节", "刚毛", "环带", "口"],
        "answer": "C",
        "explanation": "③是环带，位于蚯蚓前端，与生殖有关。"
    },
    {
        "id": "shitu_earthworm_04",
        "chapter_id": "bio_7_2_3",
        "image": "image16.png",
        "question": "蚯蚓依靠什么结构运动？",
        "options": ["①体节", "②刚毛", "③环带", "翅膀"],
        "answer": "B",
        "explanation": "蚯蚓依靠刚毛和肌肉的配合进行运动。"
    },
]

# ==================== 水螅结构系列 ====================
HYDRA_QUESTIONS = [
    {
        "id": "shitu_hydra_01",
        "chapter_id": "bio_7_2_3",
        "image": "image17.png",
        "question": "图中①所示的结构名称是？",
        "options": ["触手", "口", "芽体", "消化腔"],
        "answer": "A",
        "explanation": "①是触手，水螅用触手捕食。"
    },
    {
        "id": "shitu_hydra_02",
        "chapter_id": "bio_7_2_3",
        "image": "image17.png",
        "question": "图中②所示的结构名称是？",
        "options": ["触手", "口", "芽体", "消化腔"],
        "answer": "B",
        "explanation": "②是口，位于触手中央，食物由此进入消化腔。"
    },
    {
        "id": "shitu_hydra_03",
        "chapter_id": "bio_7_2_3",
        "image": "image17.png",
        "question": "图中⑥所示的结构名称是？",
        "options": ["触手", "口", "芽体", "消化腔"],
        "answer": "C",
        "explanation": "⑥是芽体，水螅通过出芽生殖产生新个体。"
    },
    {
        "id": "shitu_hydra_04",
        "chapter_id": "bio_7_2_3",
        "image": "image17.png",
        "question": "水螅属于哪类动物？",
        "options": ["扁形动物", "线形动物", "刺胞动物", "环节动物"],
        "answer": "C",
        "explanation": "水螅属于刺胞动物，身体呈辐射对称。"
    },
]

# ==================== 青蛙结构系列 ====================
FROG_QUESTIONS = [
    {
        "id": "shitu_frog_01",
        "chapter_id": "bio_7_2_3",
        "image": "image20.png",
        "question": "图中④所示的结构名称是？",
        "options": ["鼻孔", "眼睛", "鼓膜", "前肢"],
        "answer": "C",
        "explanation": "④是鼓膜，青蛙靠鼓膜感知声波产生听觉。"
    },
    {
        "id": "shitu_frog_02",
        "chapter_id": "bio_7_2_3",
        "image": "image20.png",
        "question": "图中⑥所示的结构名称是？",
        "options": ["鼻孔", "眼睛", "鼓膜", "前肢"],
        "answer": "A",
        "explanation": "⑥是鼻孔，是气体进出的通道。"
    },
    {
        "id": "shitu_frog_03",
        "chapter_id": "bio_7_2_3",
        "image": "image20.png",
        "question": "图中⑦所示的结构名称是？",
        "options": ["前肢", "后肢", "尾巴", "翅膀"],
        "answer": "B",
        "explanation": "⑦是后肢，青蛙的后肢粗壮，善于跳跃。"
    },
    {
        "id": "shitu_frog_04",
        "chapter_id": "bio_7_2_3",
        "image": "image20.png",
        "question": "青蛙的呼吸器官是？",
        "options": ["肺", "鳃", "气管", "皮肤"],
        "answer": "A",
        "explanation": "青蛙主要用肺呼吸，皮肤辅助呼吸。"
    },
]

# ==================== 鱼的结构系列 ====================
FISH_QUESTIONS = [
    {
        "id": "shitu_fish_01",
        "chapter_id": "bio_7_2_3",
        "image": "image21.png",
        "question": "图中④所示的结构名称是？",
        "options": ["背鳍", "尾鳍", "侧线", "鳃盖"],
        "answer": "C",
        "explanation": "④是侧线，能感知水流方向和水压。"
    },
    {
        "id": "shitu_fish_02",
        "chapter_id": "bio_7_2_3",
        "image": "image21.png",
        "question": "图中⑥所示的结构名称是？",
        "options": ["背鳍", "尾鳍", "胸鳍", "腹鳍"],
        "answer": "B",
        "explanation": "⑥是尾鳍，控制鱼的前进方向。"
    },
    {
        "id": "shitu_fish_03",
        "chapter_id": "bio_7_2_3",
        "image": "image21.png",
        "question": "鱼用什么呼吸？",
        "options": ["肺", "鳃", "气管", "皮肤"],
        "answer": "B",
        "explanation": "鱼用鳃呼吸，水流经鳃丝时进行气体交换。"
    },
]

# ==================== 病毒结构系列 ====================
VIRUS_QUESTIONS = [
    {
        "id": "shitu_virus_01",
        "chapter_id": "bio_8_2_2",
        "image": "image31.png",
        "question": "图中①所示的是哪种病毒？",
        "options": ["烟草花叶病毒", "腺病毒", "大肠杆菌噬菌体", "流感病毒"],
        "answer": "A",
        "explanation": "①是烟草花叶病毒，呈杆状，感染烟草叶片。"
    },
    {
        "id": "shitu_virus_02",
        "chapter_id": "bio_8_2_2",
        "image": "image31.png",
        "question": "图中②所示的是哪种病毒？",
        "options": ["烟草花叶病毒", "腺病毒", "大肠杆菌噬菌体", "流感病毒"],
        "answer": "B",
        "explanation": "②是腺病毒，呈球形，可引起呼吸道感染。"
    },
    {
        "id": "shitu_virus_03",
        "chapter_id": "bio_8_2_2",
        "image": "image31.png",
        "question": "图中③所示的是哪种病毒？",
        "options": ["烟草花叶病毒", "腺病毒", "大肠杆菌噬菌体", "流感病毒"],
        "answer": "C",
        "explanation": "③是大肠杆菌噬菌体，呈蝌蚪状，专门寄生在细菌体内。"
    },
    {
        "id": "shitu_virus_04",
        "chapter_id": "bio_8_2_2",
        "image": "image31.png",
        "question": "病毒的结构特点是？",
        "options": ["有细胞结构", "只有蛋白质外壳和遗传物质", "有完整的细胞核", "能独立生活"],
        "answer": "B",
        "explanation": "病毒没有细胞结构，由蛋白质外壳和内部的遗传物质组成。"
    },
]

# ==================== 光合作用系列 ====================
PHOTOSYNTHESIS_QUESTIONS = [
    {
        "id": "shitu_photo_01",
        "chapter_id": "bio_7_3_2",
        "image": "image44.png",
        "question": "光合作用的原料是？",
        "options": ["氧气和有机物", "二氧化碳和水", "水和有机物", "氧气和二氧化碳"],
        "answer": "B",
        "explanation": "光合作用以二氧化碳和水为原料，在光下合成有机物并释放氧气。"
    },
    {
        "id": "shitu_photo_02",
        "chapter_id": "bio_7_3_2",
        "image": "image44.png",
        "question": "光合作用的产物是？",
        "options": ["氧气和有机物", "二氧化碳和水", "水和有机物", "氧气和二氧化碳"],
        "answer": "A",
        "explanation": "光合作用产生有机物（储存能量）和氧气。"
    },
    {
        "id": "shitu_photo_03",
        "chapter_id": "bio_7_3_2",
        "image": "image44.png",
        "question": "光合作用的场所是？",
        "options": ["线粒体", "叶绿体", "细胞核", "液泡"],
        "answer": "B",
        "explanation": "叶绿体是光合作用的场所，能将光能转化为化学能。"
    },
]

# ==================== 消化系统系列 ====================
DIGESTION_QUESTIONS = [
    {
        "id": "shitu_digest_01",
        "chapter_id": "bio_7_4_1",
        "image": "image54.png",
        "question": "淀粉开始消化的部位是？",
        "options": ["口腔", "胃", "小肠", "大肠"],
        "answer": "A",
        "explanation": "淀粉在口腔中开始被唾液淀粉酶分解。"
    },
    {
        "id": "shitu_digest_02",
        "chapter_id": "bio_7_4_1",
        "image": "image54.png",
        "question": "蛋白质开始消化的部位是？",
        "options": ["口腔", "胃", "小肠", "大肠"],
        "answer": "B",
        "explanation": "蛋白质在胃中开始被胃液中的胃蛋白酶分解。"
    },
    {
        "id": "shitu_digest_03",
        "chapter_id": "bio_7_4_1",
        "image": "image54.png",
        "question": "脂肪消化的主要部位是？",
        "options": ["口腔", "胃", "小肠", "大肠"],
        "answer": "C",
        "explanation": "脂肪在小肠中被胆汁乳化和肠液、胰液中的酶分解。"
    },
]

# ==================== 生殖系统系列 ====================
REPRODUCTION_QUESTIONS = [
    {
        "id": "shitu_repro_01",
        "chapter_id": "bio_8_5_1",
        "image": "image51.png",
        "question": "图中①所示的结构名称是？",
        "options": ["卵巢", "输卵管", "子宫", "睾丸"],
        "answer": "A",
        "explanation": "①是卵巢，是女性主要的生殖器官，产生卵细胞和分泌雌性激素。"
    },
    {
        "id": "shitu_repro_02",
        "chapter_id": "bio_8_5_1",
        "image": "image51.png",
        "question": "图中⑦所示的结构名称是？",
        "options": ["卵巢", "输卵管", "子宫", "睾丸"],
        "answer": "D",
        "explanation": "⑦是睾丸，是男性主要的生殖器官，产生精子和分泌雄性激素。"
    },
    {
        "id": "shitu_repro_03",
        "chapter_id": "bio_8_5_1",
        "image": "image51.png",
        "question": "受精的场所是？",
        "options": ["卵巢", "输卵管", "子宫", "阴道"],
        "answer": "B",
        "explanation": "精子与卵细胞在输卵管内结合形成受精卵。"
    },
]

# ==================== 生物分类系列 ====================
CLASSIFICATION_QUESTIONS = [
    {
        "id": "shitu_class_01",
        "chapter_id": "bio_8_6_1",
        "image": "image34.png",
        "question": "生物分类的基本单位是？",
        "options": ["界", "门", "种", "科"],
        "answer": "C",
        "explanation": "种（物种）是生物分类的基本单位。"
    },
    {
        "id": "shitu_class_02",
        "chapter_id": "bio_8_6_1",
        "image": "image34.png",
        "question": "分类等级越低，生物之间的共同特征？",
        "options": ["越少", "越多", "不变", "无关"],
        "answer": "B",
        "explanation": "分类等级越低，生物之间的共同特征越多，亲缘关系越近。"
    },
]

# ==================== 蘑菇结构系列 ====================
MUSHROOM_QUESTIONS = [
    {
        "id": "shitu_mushroom_01",
        "chapter_id": "bio_8_6_2",
        "image": "image30.png",
        "question": "图中②所示的结构名称是？",
        "options": ["菌盖", "菌褶", "菌柄", "菌丝"],
        "answer": "B",
        "explanation": "②是菌褶，位于菌盖下方，是产生孢子的部位。"
    },
    {
        "id": "shitu_mushroom_02",
        "chapter_id": "bio_8_6_2",
        "image": "image30.png",
        "question": "蘑菇靠什么繁殖后代？",
        "options": ["种子", "孢子", "芽体", "卵细胞"],
        "answer": "B",
        "explanation": "蘑菇属于真菌，靠孢子繁殖后代。"
    },
]

# ==================== 子房结构系列 ====================
OVARY_QUESTIONS = [
    {
        "id": "shitu_ovary_01",
        "chapter_id": "bio_7_2_2",
        "image": "image41.png",
        "question": "图中①所示的结构名称是？",
        "options": ["子房壁", "珠被", "胚珠", "受精卵"],
        "answer": "A",
        "explanation": "①是子房壁，将来发育成果皮。"
    },
    {
        "id": "shitu_ovary_02",
        "chapter_id": "bio_7_2_2",
        "image": "image41.png",
        "question": "图中⑤所示的结构名称是？",
        "options": ["子房壁", "珠被", "胚珠", "受精卵"],
        "answer": "C",
        "explanation": "⑤是胚珠，将来发育成种子。"
    },
    {
        "id": "shitu_ovary_03",
        "chapter_id": "bio_7_2_2",
        "image": "image41.png",
        "question": "受精后，子房发育成？",
        "options": ["果实", "种子", "果皮", "胚"],
        "answer": "A",
        "explanation": "受精后，子房发育成果实，子房壁发育成果皮，胚珠发育成种子。"
    },
]

# ==================== 叶芽结构系列 ====================
LEAFBUD_QUESTIONS = [
    {
        "id": "shitu_leafbud_01",
        "chapter_id": "bio_7_2_2",
        "image": "image36.png",
        "question": "图中叶芽的②将来发育成？",
        "options": ["叶", "茎", "芽", "花"],
        "answer": "A",
        "explanation": "②是叶原基，将来发育成叶。"
    },
    {
        "id": "shitu_leafbud_02",
        "chapter_id": "bio_7_2_2",
        "image": "image36.png",
        "question": "图中叶芽的③将来发育成？",
        "options": ["叶", "茎", "芽", "花"],
        "answer": "B",
        "explanation": "③是芽轴，将来发育成茎。"
    },
    {
        "id": "shitu_leafbud_03",
        "chapter_id": "bio_7_2_2",
        "image": "image36.png",
        "question": "图中叶芽的④将来发育成？",
        "options": ["叶", "茎", "侧芽", "花"],
        "answer": "C",
        "explanation": "④是芽原基，将来发育成侧芽。"
    },
]

# ==================== 地理填充图系列 (1-18.png) ====================
GEO_CHINA_QUESTIONS = [
    {
        "id": "shitu_geo_01",
        "chapter_id": "geo_7_2_1",
        "image": "1.png",
        "question": "图中A表示哪个海洋？",
        "options": ["太平洋", "大西洋", "印度洋", "北冰洋"],
        "answer": "A",
        "explanation": "图中A是太平洋，位于南美洲西岸。"
    },
    {
        "id": "shitu_geo_02",
        "chapter_id": "geo_7_2_1",
        "image": "2.png",
        "question": "图中A表示哪个大洋？",
        "options": ["太平洋", "大西洋", "印度洋", "北冰洋"],
        "answer": "A",
        "explanation": "北美洲西临太平洋。"
    },
    {
        "id": "shitu_geo_03",
        "chapter_id": "geo_7_2_1",
        "image": "3.png",
        "question": "图中③所示的地形区名称是？",
        "options": ["撒哈拉沙漠", "刚果盆地", "东非高原", "南非高原"],
        "answer": "B",
        "explanation": "③是刚果盆地，位于非洲中部。"
    },
    {
        "id": "shitu_geo_04",
        "chapter_id": "geo_7_2_1",
        "image": "4.png",
        "question": "图中①所示的气候类型是？",
        "options": ["热带雨林气候", "热带草原气候", "热带沙漠气候", "地中海气候"],
        "answer": "A",
        "explanation": "①是热带雨林气候，分布在刚果盆地。"
    },
]

# ==================== 合并所有题目 ====================
ALL_SHITU_QUESTIONS = (
    MICROSCOPE_QUESTIONS +
    CELL_QUESTIONS +
    PARAMECIUM_QUESTIONS +
    GRASSHOPPER_QUESTIONS +
    EARTHWORM_QUESTIONS +
    HYDRA_QUESTIONS +
    FROG_QUESTIONS +
    FISH_QUESTIONS +
    VIRUS_QUESTIONS +
    PHOTOSYNTHESIS_QUESTIONS +
    DIGESTION_QUESTIONS +
    REPRODUCTION_QUESTIONS +
    CLASSIFICATION_QUESTIONS +
    MUSHROOM_QUESTIONS +
    OVARY_QUESTIONS +
    LEAFBUD_QUESTIONS +
    GEO_CHINA_QUESTIONS
)

def get_shitu_questions(image_name=None, limit=None):
    """获取识图卡题目"""
    if image_name:
        questions = [q for q in ALL_SHITU_QUESTIONS if q.get("image") == image_name]
    else:
        questions = ALL_SHITU_QUESTIONS.copy()
    
    if limit:
        questions = questions[:limit]
    
    return questions

def get_all_shitu_images():
    """获取所有识图卡图片列表"""
    images = set()
    for q in ALL_SHITU_QUESTIONS:
        if "image" in q:
            images.add(q["image"])
    return sorted(images)

# 测试
if __name__ == "__main__":
    print("识图卡题库统计:")
    print(f"总题数: {len(ALL_SHITU_QUESTIONS)}")
    print(f"涉及图片: {len(get_all_shitu_images())}张")
    print()
    print("各章节题目数:")
    from collections import Counter
    chapter_counts = Counter(q["chapter_id"] for q in ALL_SHITU_QUESTIONS)
    for ch, cnt in sorted(chapter_counts.items()):
        print(f"  {ch}: {cnt}题")
