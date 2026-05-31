# -*- coding: utf-8 -*-
"""
全能学练考系统 - 题库模块 v4
支持难度筛选：简单/中等/困难
"""

import random
import json
import os
import sys
from typing import List, Dict

# 导入题库生成模块
from question_gen import (
    gen_bio_chapter_questions,
    gen_geo_chapter_questions,
    gen_bio_human_questions,
    gen_geo_china_questions,
    # 专项题库（10个）
    gen_china_terrain_questions,
    gen_china_climate_questions,
    gen_china_rivers_questions,
    gen_yangtze_yellow_questions,
    gen_natural_resources_questions,
    gen_agriculture_questions,
    gen_population_climate_questions,
    gen_disaster_prevention_questions,
    gen_ocean_island_questions,
    gen_economic_development_questions,
)

# 导入识图卡和真题题库
# from question_shitu import get_all_shitu_questions  # 旧版，有图片匹配问题
from question_shitu_final import get_all_shitu_questions  # 新版，基于OCR重新编写
from question_exam_real import get_all_exam_questions

# 导入湖南地理预测分析题库
from question_hunan_geo import get_all_hunan_geo_questions

# 导入湖南生地会考真题（新增）
from question_hunan_exam import get_all_hunan_exam_questions

# 导入湖南生地生物核心专项（新增）
from question_hunan_bio import get_all_hunan_bio_questions

# 导入湖南乡土地理专项v2（新增）
from question_hunan_geo_v2 import get_all_hunan_geo_v2_questions

# 导入湘教版地理填充图题库
from question_geo_xiangjiao import get_all_xj_questions

# 导入连线题（新增）
from question_match import get_all_match_questions

# 难度中文标签
DIFFICULTY_LABELS = {
    'easy': '简单',
    'medium': '中等',
    'hard': '困难',
}

# 难度配色
DIFFICULTY_COLORS = {
    'easy': '#10B981',     # 绿色
    'medium': '#F59E0B',  # 橙色
    'hard': '#EF4444',    # 红色
}


class QuestionBank:
    """题库类"""

    def __init__(self):
        self.subjects = {}
        self.questions = {}              # {chapter_id: [所有题目]}
        self.questions_by_diff = {}      # {chapter_id: {'easy': [], 'medium': [], 'hard': [], 'all': []}}
        self._build_knowledge_tree()
        self._generate_all_questions()

    def _build_knowledge_tree(self):
        """构建知识框架树"""
        self.subjects = {
            'biology': {
                'name': '初中生物',
                'grades': {
                    'grade7_up': {
                        'name': '七年级上册',
                        'chapters': {
                            'bio_7_1_1': {'name': '认识生物', 'topics': ['观察周边环境中的生物', '生物的特征', '应激性', '遗传变异', '人类的起源', '病毒']},
                            'bio_7_1_2': {'name': '认识细胞', 'topics': ['显微镜的使用', '植物细胞结构', '动物细胞结构', '细胞的生活', '细胞分裂', '细胞分化']},
                            'bio_7_1_3': {'name': '从细胞到生物体', 'topics': ['细胞分裂', '动物体结构层次', '植物体结构层次', '单细胞生物', '四大组织']},
                            'bio_7_2_1': {'name': '藻类与植物类群', 'topics': ['藻类植物', '苔藓植物', '蕨类植物', '种子植物', '植物进化']},
                            'bio_7_2_2': {'name': '动物类群', 'topics': ['无脊椎动物', '脊椎动物', '腔肠动物', '扁形动物', '环节动物', '节肢动物']},
                            'bio_7_2_3': {'name': '微生物', 'topics': ['细菌', '真菌', '病毒', '微生物与人类']},
                            'bio_7_2_4': {'name': '生物分类', 'topics': ['分类方法', '生物命名', '分类等级']},
                        }
                    },
                    'grade7_down': {
                        'name': '七年级下册',
                        'chapters': {
                            'bio_7_3_1': {'name': '被子植物的一生', 'topics': ['种子萌发', '植株生长', '开花结果', '传粉', '受精']},
                            'bio_7_3_2': {'name': '植物体内物质与能量', 'topics': ['蒸腾作用', '光合作用', '呼吸作用', '有机物运输']},
                            'bio_7_3_3': {'name': '植物在自然界中的作用', 'topics': ['物质循环', '能量流动', '生态平衡']},
                            'bio_7_4_1': {'name': '人的由来', 'topics': ['人类起源', '生殖系统', '青春期', '受精', '胚胎发育']},
                            'bio_7_4_2': {'name': '人体营养', 'topics': ['营养物质', '消化系统', '吸收', '小肠', '合理营养']},
                            'bio_7_4_3': {'name': '人体呼吸', 'topics': ['呼吸系统', '气体交换', '肺泡', '呼吸运动']},
                            'bio_7_4_4': {'name': '物质运输', 'topics': ['血液循环', '心脏', '血管', '血型', '输血']},
                            'bio_7_4_5': {'name': '废物排出', 'topics': ['泌尿系统', '肾脏', '排泄', '尿的形成']},
                        }
                    },
                    'grade8_up': {
                        'name': '八年级上册',
                        'chapters': {
                            'bio_8_1_1': {'name': '动物的运动', 'topics': ['运动系统的组成', '骨、关节、肌肉的配合', '运动机制']},
                            'bio_8_1_2': {'name': '动物的行为', 'topics': ['先天性行为', '学习行为', '社会行为', '动物行为研究']},
                            'bio_8_2_1': {'name': '微生物在生物圈中的作用', 'topics': ['作用概述', '与人类关系', '分解者']},
                            'bio_8_3_1': {'name': '细菌和真菌', 'topics': ['分布', '培养', '繁殖', '结构']},
                            'bio_8_3_2': {'name': '人类对细菌和真菌的利用', 'topics': ['发酵原理', '食品保存', '疾病防治', '环境保护']},
                            'bio_8_4_1': {'name': '植物的生殖', 'topics': ['无性生殖', '有性生殖', '发育', '营养繁殖']},
                            'bio_8_4_2': {'name': '动物的生殖和发育', 'topics': ['昆虫', '两栖动物', '鸟', '变态发育']},
                            'bio_8_4_3': {'name': '人类的生殖和发育', 'topics': ['生殖系统', '青春期', '计划生育', '避孕']},
                        }
                    },
                    'grade8_down': {
                        'name': '八年级下册',
                        'chapters': {
                            'bio_8_5_1': {'name': '生物的遗传和变异', 'topics': ['DNA', '基因', '性状遗传', '变异', '遗传规律']},
                            'bio_8_5_2': {'name': '生物的进化', 'topics': ['进化历程', '自然选择', '化石证据', '进化论']},
                            'bio_8_6_1': {'name': '传染病和免疫', 'topics': ['传染病', '免疫', '抗原', '抗体', '计划免疫']},
                            'bio_8_6_2': {'name': '用药与急救', 'topics': ['安全用药', '急救常识', '人工呼吸', '心肺复苏']},
                            'bio_8_7_1': {'name': '了解自己 增进健康', 'topics': ['健康', '生活方式', '心理健康', '良好习惯']},
                        }
                    },
                    'shitu': {
                        'name': '🖼 识图卡专项',
                        'chapters': {
                            'shitu_all': {'name': '识图卡全题库', 'topics': ['显微镜', '细胞结构', '植物类群', '消化系统', '呼吸系统', '血液循环', '光合作用', '泌尿系统', '神经感官', '运动系统', '遗传进化', '生态系统', '地理图像']},
                        }
                    },
                    'exam_real': {
                        'name': '📝 会考真题',
                        'chapters': {
                            'exam_real_all': {'name': '生地会考真题（2021-2025）', 'topics': ['广东生地会考真题', '生物真题', '地理真题']},
                        }
                    },
                    'hunan_geo': {
                        'name': '🏔️ 湖南地理预测',
                        'chapters': {
                            'hunan_geo_all': {'name': '湖南生地会考地理预测分析题', 'topics': ['地球运动', '地图判读', '农业区位', '交通建设', '生态保护', '产业区位', '极地地理', '清洁能源', '乡村振兴', '防灾减灾']},
                        }
                    },
                    'hunan_exam': {
                        'name': '🎯 湖南生地会考真题',
                        'chapters': {
                            'hunan_exam_all': {'name': '湖南生地会考真题（2021-2025）', 'topics': ['湖南生物真题', '湖南地理真题', '2025真题', '2024真题', '2023真题', '2022真题', '2021真题']},
                        }
                    },
                    'hunan_bio': {
                        'name': '🧬 湖南生地生物核心专项',
                        'chapters': {
                            'hunan_bio_all': {'name': '湖南生地会考生物核心知识点', 'topics': ['显微镜使用', '细胞结构', '人体八大系统', '光合作用', '呼吸作用', '遗传变异', '生态系统', '反射与神经']},
                        }
                    },
                    'hunan_geo_v2': {
                        'name': '🗺️ 湖南乡土地理专项',
                        'chapters': {
                            'hunan_geo_v2_all': {'name': '湖南乡土地理专项（扩充版）', 'topics': ['湖南概况', '湘江四水', '长株潭', '交通枢纽', '农业物产', '矿产资源', '民族文化', '自然灾害', '地球运动']},
                        }
                    },
                    'xj_geo': {
                        'name': '🗺️ 湘教版地理填充图',
                        'chapters': {
                            'xj_geo_all': {'name': '湘教版地理填充图识图题', 'topics': ['经纬网', '地球运动', '五带划分', '等高线', '大洲大洋', '板块构造', '世界气候', '亚洲地形', '亚洲气候', '东南亚', '南亚', '西亚', '欧洲西部', '非洲', '极地地区', '日本', '埃及', '俄罗斯', '法国', '美国', '巴西', '澳大利亚', '中国行政区', '中国地形', '中国温度带', '中国干湿区', '中国河流', '黄河', '南水北调', '长江', '中国铁路']},
                        }
                    },
                    'match': {
                        'name': '🔗 连线匹配专项',
                        'chapters': {
                            'match_all': {'name': '连线匹配题（全题型）', 'topics': ['生物连线', '地理连线', '器官功能', '交通干线', '世界地理']},
                        }
                    }
                }
            },
            'geography': {
                'name': '初中地理',
                'grades': {
                    'grade7_up': {
                        'name': '七年级上册',
                        'chapters': {
                            'geo_7_1_1': {'name': '地球和地图', 'topics': ['地球形状', '大小', '地球仪', '经纬线', '经纬网', '地图三要素', '比例尺', '方向', '地形图']},
                            'geo_7_1_2': {'name': '陆地和海洋', 'topics': ['海陆分布', '七大洲', '四大洋', '海陆变迁', '板块构造', '火山', '地震']},
                            'geo_7_1_3': {'name': '天气与气候', 'topics': ['天气', '气候', '气温', '降水', '气候类型', '影响因素', '环境保护']},
                            'geo_7_1_4': {'name': '居民与聚落', 'topics': ['世界人口', '人口问题', '人种', '语言', '宗教', '聚落', '城市化', '民居建筑', '文化景观']},
                        }
                    },
                    'grade7_down': {
                        'name': '七年级下册',
                        'chapters': {
                            'geo_7_2_1': {'name': '认识大洲', 'topics': ['亚洲', '非洲', '美洲', '欧洲', '大洋洲', '南极洲', '地形', '气候', '河流']},
                            'geo_7_2_2': {'name': '认识地区', 'topics': ['东南亚', '南亚', '西亚', '欧洲西部', '中东', '撒哈拉以南非洲', '自然环境', '人文特色']},
                            'geo_7_2_3': {'name': '认识国家', 'topics': ['日本', '印度', '俄罗斯', '美国', '巴西', '澳大利亚', '法国', '德国', '资源', '经济']},
                        }
                    },
                    'grade8_up': {
                        'name': '八年级上册',
                        'chapters': {
                            'geo_8_1_1': {'name': '中国的疆域与人口', 'topics': ['位置', '疆域', '行政区划', '人口', '民族', '人口政策']},
                            'geo_8_1_2': {'name': '中国的自然环境', 'topics': ['地形', '地势', '气候', '河流', '自然灾害']},
                            'geo_8_1_3': {'name': '中国的自然资源', 'topics': ['土地资源', '水资源', '矿产资源', '海洋资源']},
                            'geo_8_1_4': {'name': '中国的经济发展', 'topics': ['交通运输', '农业', '工业', '高新技术产业']},
                        }
                    },
                    'grade8_down': {
                        'name': '八年级下册',
                        'chapters': {
                            'geo_8_2_1': {'name': '中国的地理差异', 'topics': ['四大地理区域', '秦岭-淮河', '南北方差异']},
                            'geo_8_2_2': {'name': '北方地区', 'topics': ['位置', '地形', '气候', '工业', '农业']},
                            'geo_8_2_3': {'name': '南方地区', 'topics': ['位置', '地形', '气候', '经济', '水乡特色']},
                            'geo_8_2_4': {'name': '西北地区', 'topics': ['位置', '干旱', '畜牧业', '绿洲农业', '能源']},
                            'geo_8_2_5': {'name': '青藏地区', 'topics': ['位置', '高寒', '河谷农业', '自然保护区', '雪山冰川']},
                            'geo_8_3_1': {'name': '中国与世界', 'topics': ['国际合作', '可持续发展', '和平发展', '一带一路']},
                        }
                    }
                }
            }
        }

    def _normalize_question(self, q: Dict) -> Dict:
        """规范化题目格式，统一不同来源的题目结构"""
        q = dict(q)  # 不修改原字典

        # 1. 统一 type: "choice" -> "select"
        if q.get('type') == 'choice':
            q['type'] = 'select'

        # 2. 处理答案格式
        # 如果 answer 是字符串且有 options，尝试转为整数索引
        answer = q.get('answer')
        options = q.get('options', [])
        if isinstance(answer, str) and options:
            # 在 options 中查找匹配的字符串
            for idx, opt in enumerate(options):
                if str(opt).strip() == str(answer).strip():
                    q['answer'] = idx
                    break
            # 如果找不到匹配，保留原样

        # 3. 判断题处理：V/X 转 True/False
        if q.get('type') == 'judge':
            # 如果有 is_correct 字段，用它替代 answer
            if 'is_correct' in q:
                q['answer'] = bool(q['is_correct'])
            elif isinstance(answer, str):
                if answer.upper() in ['V', '√', 'T', 'TRUE', 'YES', '对', '正确']:
                    q['answer'] = True
                elif answer.upper() in ['X', '×', 'F', 'FALSE', 'NO', '错', '错误']:
                    q['answer'] = False

        # 4. 确保有 difficulty 字段
        if 'difficulty' not in q:
            q['difficulty'] = 'medium'

        # 5. 确保有 topic 字段
        if 'topic' not in q:
            q['topic'] = '基础知识'

        # 6. 确保有 explanation 字段
        if 'explanation' not in q:
            q['explanation'] = ''

        return q

    def _get_difficulty(self, q: Dict) -> str:
        """获取题目难度，默认medium"""
        diff = q.get('difficulty', 'medium')
        # 处理数字难度值：1=easy, 2=medium, 3=hard
        if diff == 1 or diff == '1':
            return 'easy'
        elif diff == 2 or diff == '2':
            return 'medium'
        elif diff == 3 or diff == '3':
            return 'hard'
        return diff if diff in ['easy', 'medium', 'hard'] else 'medium'

    def _add_to_difficulty_groups(self, chapter_id: str, q: Dict):
        """将题目按难度分组（先规范化）"""
        q = self._normalize_question(q)
        diff = self._get_difficulty(q)
        if chapter_id not in self.questions_by_diff:
            self.questions_by_diff[chapter_id] = {
                'easy': [], 'medium': [], 'hard': [], 'all': []
            }
        self.questions_by_diff[chapter_id][diff].append(q)
        self.questions_by_diff[chapter_id]['all'].append(q)

    def _generate_all_questions(self):
        """生成所有章节的题目"""
        all_chapters = {}
        for subject in self.subjects.values():
            for grade in subject['grades'].values():
                all_chapters.update(grade['chapters'])

        for chapter_id, chapter_info in all_chapters.items():
            topics = chapter_info.get('topics', ['基础知识'])

            if chapter_id.startswith('geo_8_1_') or chapter_id.startswith('geo_8_2_') or chapter_id.startswith('geo_8_3_'):
                questions = gen_geo_china_questions(chapter_id, topics, 200)
            elif chapter_id.startswith('bio_7_3_') or chapter_id.startswith('bio_7_4_') or chapter_id.startswith('bio_8_4_') or chapter_id.startswith('bio_8_5_') or chapter_id.startswith('bio_8_6_') or chapter_id.startswith('bio_8_7_'):
                questions = gen_bio_human_questions(chapter_id, topics, 200)
            elif chapter_id.startswith('bio_'):
                questions = gen_bio_chapter_questions(chapter_id, topics, 200)
            elif chapter_id.startswith('geo_'):
                questions = gen_geo_chapter_questions(chapter_id, topics, 200)
            else:
                questions = gen_bio_chapter_questions(chapter_id, topics, 200)

            for idx, q in enumerate(questions):
                q['id'] = f"{chapter_id}_{q['type']}_{idx}"
                self._add_to_difficulty_groups(chapter_id, q)
            self.questions[chapter_id] = questions

        # 专项题库（10个）
        special_topics = [
            ('terrain',        gen_china_terrain_questions),
            ('climate',        gen_china_climate_questions),
            ('rivers',         gen_china_rivers_questions),
            ('yangtze_yellow', gen_yangtze_yellow_questions),
            ('resources',      gen_natural_resources_questions),
            ('agriculture',    gen_agriculture_questions),
            ('population',     gen_population_climate_questions),
            ('disaster',       gen_disaster_prevention_questions),
            ('ocean',          gen_ocean_island_questions),
            ('economy',        gen_economic_development_questions),
        ]
        for topic_name, fn in special_topics:
            questions = fn(count=500)
            chapter_id = f'special_{topic_name}'
            for idx, q in enumerate(questions):
                q['id'] = f"special_{topic_name}_{q['type']}_{idx}"
                self._add_to_difficulty_groups(chapter_id, q)
            self.questions[chapter_id] = questions

        print(f"题库生成完成！共 {sum(len(qs) for qs in self.questions.values())} 道题，覆盖 {len(self.questions)} 个章节")

        # ── 加载扩充题目 ──
        try:
            # 使用相对于当前文件的路径（支持 PyInstaller 打包）
            if getattr(sys, 'frozen', False):
                # 打包模式：EXE所在目录
                script_dir = os.path.dirname(sys.executable)
                internal_dir = os.path.join(script_dir, '_internal')
                # 先尝试 _internal 目录，再尝试 EXE 目录
                expanded_path = os.path.join(internal_dir, 'all_expanded_questions.json')
                if not os.path.exists(expanded_path):
                    expanded_path = os.path.join(script_dir, 'all_expanded_questions.json')
            else:
                # 开发模式
                script_dir = os.path.dirname(os.path.abspath(__file__))
                expanded_path = os.path.join(script_dir, 'all_expanded_questions.json')
            # 尝试UTF-8，失败则用GBK
            for enc in ['utf-8', 'gbk']:
                try:
                    with open(expanded_path, 'r', encoding=enc) as f:
                        expanded_data = json.load(f)
                    break
                except UnicodeDecodeError:
                    continue
            loaded_count = 0
            for chapter_id, data in expanded_data.items():
                if chapter_id in self.questions:
                    # 合并题目（避免重复）
                    existing_ids = {q.get('id') for q in self.questions[chapter_id]}
                    new_questions = []
                    for q in data['questions']:
                        if q.get('id') not in existing_ids:
                            new_questions.append(q)
                    # 同时添加到难度分组
                    for q in new_questions:
                        self._add_to_difficulty_groups(chapter_id, q)
                    self.questions[chapter_id].extend(new_questions)
                    loaded_count += len(new_questions)

            if loaded_count > 0:
                print(f"  扩充题目: 已加载 {loaded_count} 道新题目")
        except FileNotFoundError:
            print("  扩充题目: 未找到扩充文件")
        except Exception as e:
            print(f"  扩充题目加载失败: {e}")

        # ── 识图卡专项 ──
        shitu_qs = get_all_shitu_questions()
        for idx, q in enumerate(shitu_qs):
            q['id'] = f"shitu_{q['type']}_{idx}"
            self._add_to_difficulty_groups('shitu_all', q)
        self.questions['shitu_all'] = shitu_qs
        print(f"  识图卡专项: {len(shitu_qs)} 道题（覆盖102张图片）")

        # ── 会考真题专项 ──
        exam_qs = get_all_exam_questions()
        # 加载扩充的会考真题
        try:
            # 尝试UTF-8，失败则用GBK
            for enc in ['utf-8', 'gbk']:
                try:
                    with open('all_expanded_questions.json', 'r', encoding=enc) as f:
                        expanded = json.load(f)
                    break
                except UnicodeDecodeError:
                    continue
            if 'exam_real_all' in expanded:
                exam_qs.extend(expanded['exam_real_all']['questions'])
        except:
            pass
        for idx, q in enumerate(exam_qs):
            q['id'] = f"exam_{q['type']}_{idx}"
            self._add_to_difficulty_groups('exam_real_all', q)
        self.questions['exam_real_all'] = exam_qs
        years = {}
        for q in exam_qs:
            y = q.get('year', '?')
            years[y] = years.get(y, 0) + 1
        year_str = ' / '.join([f"{y}年({n}题)" for y, n in sorted(years.items(), key=lambda x: str(x[0]))])
        print(f"  会考真题专项: {len(exam_qs)} 道题（{year_str}）")

        # ── 湖南地理预测分析题 ──
        hunan_qs = get_all_hunan_geo_questions()
        # 加载扩充的湖南地理题目
        try:
            # 尝试UTF-8，失败则用GBK
            for enc in ['utf-8', 'gbk']:
                try:
                    with open('all_expanded_questions.json', 'r', encoding=enc) as f:
                        expanded = json.load(f)
                    break
                except UnicodeDecodeError:
                    continue
            if 'hunan_geo_all' in expanded:
                hunan_qs.extend(expanded['hunan_geo_all']['questions'])
        except:
            pass
        for idx, q in enumerate(hunan_qs):
            q['id'] = f"hunan_geo_{idx}"
            self._add_to_difficulty_groups('hunan_geo_all', q)
        self.questions['hunan_geo_all'] = hunan_qs
        topics = {}
        for q in hunan_qs:
            t = q.get('topic', '其他')
            topics[t] = topics.get(t, 0) + 1
        topic_str = ' / '.join([f"{t}({n}题)" for t, n in sorted(topics.items())])
        print(f"  湖南地理预测分析题: {len(hunan_qs)} 道题（{topic_str}）")

        # ── 湖南生地会考真题（新增）─
        hunan_exam_qs = get_all_hunan_exam_questions()
        for idx, q in enumerate(hunan_exam_qs):
            q['id'] = f"hunan_exam_{idx}"
            self._add_to_difficulty_groups('hunan_exam_all', q)
        self.questions['hunan_exam_all'] = hunan_exam_qs
        # 按年份和科目统计
        bio_count = sum(1 for q in hunan_exam_qs if q.get('subject') == '生物')
        geo_count = sum(1 for q in hunan_exam_qs if q.get('subject') == '地理')
        print(f"  ★ 湖南生地会考真题: {len(hunan_exam_qs)} 道题（生物{bio_count}题·地理{geo_count}题）")

        # ── 湖南生地生物核心专项（新增）─
        hunan_bio_qs = get_all_hunan_bio_questions()
        for idx, q in enumerate(hunan_bio_qs):
            q['id'] = f"hunan_bio_{idx}"
            self._add_to_difficulty_groups('hunan_bio_all', q)
        self.questions['hunan_bio_all'] = hunan_bio_qs
        bio_topics = {}
        for q in hunan_bio_qs:
            t = q.get('topic', '其他')
            bio_topics[t] = bio_topics.get(t, 0) + 1
        bio_topic_str = ' / '.join([f"{t}({n}题)" for t, n in sorted(bio_topics.items())])
        print(f"  ★ 湖南生地生物核心专项: {len(hunan_bio_qs)} 道题（{bio_topic_str}）")

        # ── 湖南乡土地理专项v2（新增）─
        hunan_geo_v2_qs = get_all_hunan_geo_v2_questions()
        for idx, q in enumerate(hunan_geo_v2_qs):
            q['id'] = f"hunan_geo_v2_{idx}"
            self._add_to_difficulty_groups('hunan_geo_v2_all', q)
        self.questions['hunan_geo_v2_all'] = hunan_geo_v2_qs
        geo_v2_topics = {}
        for q in hunan_geo_v2_qs:
            t = q.get('topic', '其他')
            geo_v2_topics[t] = geo_v2_topics.get(t, 0) + 1
        geo_v2_topic_str = ' / '.join([f"{t}({n}题)" for t, n in sorted(geo_v2_topics.items())])
        print(f"  ★ 湖南乡土地理专项v2: {len(hunan_geo_v2_qs)} 道题（{geo_v2_topic_str}）")

        # ── 湘教版地理填充图识图题 ──
        try:
            xj_qs = get_all_xj_questions()
            for idx, q in enumerate(xj_qs):
                q['id'] = f"xj_{idx}"
                self._add_to_difficulty_groups('xj_geo_all', q)
            self.questions['xj_geo_all'] = xj_qs
            print(f"  湘教版地理填充图识图题: {len(xj_qs)} 道题")
        except Exception as e:
            print(f"  湘教版地理识图题加载失败: {e}")

        # ── 连线匹配题（新增）─
        match_qs = get_all_match_questions()
        match_bio = 0
        match_geo = 0
        for idx, q in enumerate(match_qs):
            orig_id = q.get('id', '')
            if 'match_bio' in orig_id:
                match_bio += 1
            elif 'match_geo' in orig_id:
                match_geo += 1
            q['id'] = f"match_{idx}"
            self._add_to_difficulty_groups('match_all', q)
        self.questions['match_all'] = match_qs
        print(f"  ★ 连线匹配专项: {len(match_qs)} 道题（生物{match_bio}题·地理{match_geo}题）")

        print(f"题库总计: {sum(len(qs) for qs in self.questions.values())} 道题")

    def get_questions(self, chapter_id: str, count: int = 10, difficulty: str = 'all') -> List[Dict]:
        """获取指定章节的题目，支持难度筛选"""
        if chapter_id not in self.questions_by_diff:
            return []
        pool = self.questions_by_diff[chapter_id].get(difficulty, self.questions_by_diff[chapter_id]['all'])
        return random.sample(pool, min(count, len(pool)))

    def get_chapters(self, subject: str = None) -> Dict:
        """获取章节列表"""
        if subject:
            return self.subjects.get(subject, {})
        return self.subjects

    def get_all_subjects(self) -> List[Dict]:
        """获取所有学科和章节"""
        result = []
        for subject_id, subject_data in self.subjects.items():
            grades = []
            for grade_id, grade_data in subject_data.get('grades', {}).items():
                chapters = []
                for chapter_id, chapter_data in grade_data.get('chapters', {}).items():
                    chapters.append({
                        'id': chapter_id,
                        'name': chapter_data.get('name', chapter_id),
                        'count': len(self.questions.get(chapter_id, []))
                    })
                grades.append({
                    'id': grade_id,
                    'name': grade_data.get('name', grade_id),
                    'chapters': chapters
                })
            result.append({
                'id': subject_id,
                'name': subject_data.get('name', subject_id),
                'grades': grades
            })
        return result

    def get_chapters_by_subject(self, subject_id: str) -> List[Dict]:
        """获取指定学科的所有章节"""
        subject = self.subjects.get(subject_id, {})
        chapters = []
        for grade_id, grade_data in subject.get('grades', {}).items():
            for chapter_id, chapter_data in grade_data.get('chapters', {}).items():
                chapters.append({
                    'id': chapter_id,
                    'name': chapter_data.get('name', chapter_id),
                    'count': len(self.questions.get(chapter_id, []))
                })
        return chapters

    def get_questions_by_chapter(self, chapter_id: str, mode: str = 'practice', count: int = 50, difficulty: str = 'all') -> List[Dict]:
        """获取章节题目，支持练习/考试模式和难度筛选"""
        if chapter_id not in self.questions_by_diff:
            return []
        pool = self.questions_by_diff[chapter_id].get(difficulty, self.questions_by_diff[chapter_id]['all'])
        return random.sample(pool, min(count, len(pool)))

    def check_answer(self, question_id: str, user_answer: str) -> Dict:
        """检查答案，返回详细解析"""
        for chapter_id, questions in self.questions.items():
            for q in questions:
                if q.get('id') == question_id:
                    q_type = q.get('type', 'select')
                    correct_answer = q.get('answer')
                    explanation = q.get('explanation', '本题考察对知识点的理解和应用。')
                    difficulty = q.get('difficulty', 'medium')
                    options = q.get('options', [])

                    is_correct = False

                    if q_type == 'select':
                        try:
                            is_correct = int(user_answer) == int(correct_answer)
                        except (ValueError, TypeError):
                            is_correct = str(user_answer).strip() == str(correct_answer).strip()
                    elif q_type == 'judge':
                        if isinstance(user_answer, bool):
                            is_correct = user_answer == correct_answer
                        elif str(user_answer).lower() in ['true', 'false']:
                            is_correct = (user_answer.lower() == 'true') == correct_answer
                        else:
                            # 处理中文答案格式：判断题用户可能提交"正确/对/✓"或"错误/错/×"
                            ua_str = str(user_answer).strip()
                            true_aliases = ['true', 'false', '正确', '对', 't', 'v', '√', 'o', 'yes', '1', 't']
                            false_aliases = ['错误', '错', 'f', 'x', '×', 'no', '0', 'f']
                            # 仅当 correct_answer 为 True 时接受"正确/对"类答案
                            if correct_answer is True or correct_answer == True:
                                is_correct = ua_str.lower() in true_aliases
                            elif correct_answer is False or correct_answer == False:
                                is_correct = ua_str.lower() in false_aliases
                            else:
                                is_correct = str(user_answer).strip() == str(correct_answer).strip()
                    elif q_type in ('fill', 'image_fill', 'image_hotspot'):
                        user_ans = str(user_answer).strip().lower()
                        if isinstance(correct_answer, list):
                            is_correct = any(user_ans == str(a).strip().lower() for a in correct_answer)
                        else:
                            is_correct = user_ans == str(correct_answer).strip().lower()

                    result = {
                        'is_correct': is_correct,
                        'correct_answer': correct_answer,
                        'explanation': explanation,
                        'difficulty': difficulty,
                        'difficulty_label': DIFFICULTY_LABELS.get(difficulty, '中等'),
                        'difficulty_color': DIFFICULTY_COLORS.get(difficulty, '#F59E0B'),
                        'question_type': q_type,
                    }

                    # 选择题：额外返回选项列表和正确索引
                    if q_type == 'select' and options:
                        result['detail_explanation'] = {
                            'full': explanation,
                            'difficulty': difficulty,
                            'difficulty_label': DIFFICULTY_LABELS.get(difficulty, '中等'),
                            'difficulty_color': DIFFICULTY_COLORS.get(difficulty, '#F59E0B'),
                            'options': options,
                            'correct_idx': correct_answer if isinstance(correct_answer, int) else -1,
                        }
                    elif q_type in ('judge', 'fill', 'image_fill', 'image_hotspot'):
                        result['detail_explanation'] = {
                            'full': explanation,
                            'difficulty': difficulty,
                            'difficulty_label': DIFFICULTY_LABELS.get(difficulty, '中等'),
                            'difficulty_color': DIFFICULTY_COLORS.get(difficulty, '#F59E0B'),
                        }

                    return result

        return {'is_correct': False, 'correct_answer': '', 'explanation': '题目不存在',
                'difficulty': 'medium', 'difficulty_label': '中等', 'difficulty_color': '#F59E0B',
                'question_type': 'select'}

    def get_question_info(self, question_id: str) -> Dict:
        """根据题目ID获取完整的题目信息，用于错题本"""
        for chapter_id, questions in self.questions.items():
            for q in questions:
                if q.get('id') == question_id:
                    # 返回规范化的完整题目信息
                    return self._normalize_question(q)
        return {}

    def get_difficulty_stats(self, chapter_id: str) -> Dict:
        """获取章节各难度题目数量"""
        if chapter_id not in self.questions_by_diff:
            return {}
        groups = self.questions_by_diff[chapter_id]
        return {
            'easy': len(groups.get('easy', [])),
            'medium': len(groups.get('medium', [])),
            'hard': len(groups.get('hard', [])),
            'all': len(groups.get('all', [])),
        }

    def get_total_count(self) -> int:
        """获取总题数"""
        return sum(len(qs) for qs in self.questions.values())

    def get_stats(self) -> str:
        """获取统计信息"""
        stats = []
        for chapter_id, qs in self.questions.items():
            stats.append(f"{chapter_id}: {len(qs)}题")
        return ", ".join(stats[:5]) + f"...共{len(self.questions)}章节"
