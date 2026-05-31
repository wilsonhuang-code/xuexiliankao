# -*- coding: utf-8 -*-
"""测试 image_hotspot 提交判题逻辑（精确匹配）"""
import sys
sys.path.insert(0, r"C:\Users\Administrator\Desktop\学练考")
from question_shitu_final import SHITU_QUESTIONS

q = None
for item in SHITU_QUESTIONS:
    if item.get("type") == "image_hotspot":
        q = item
        break

if not q:
    print("未找到 image_hotspot 题目")
    sys.exit(1)

print(f"题目: {q['question'][:40]}")
print(f"答案: {q['answer']}")

def check_hotspot_answer(user_answer, correct_answer):
    answers = correct_answer if isinstance(correct_answer, list) else [correct_answer]
    if len(user_answer) != len(answers):
        return False
    match_count = 0
    for ua, ca in zip(user_answer, answers):
        if str(ua).strip().lower() == str(ca).strip().lower():
            match_count += 1
    return match_count == len(answers)

tests = [
    (["细胞壁", "叶绿体", "液泡", "细胞核", "细胞膜", "细胞质", "线粒体"], "全对"),
    (["细胞壁", "叶绿体", "液泡", "细胞核", "细胞膜", "细胞质", "线粒体aaa"], "错一个"),
    (["壁", "叶绿体", "液泡", "细胞核", "细胞膜", "细胞质", "线粒体"], "部分匹配"),
    (["", "", "", "", "", "", ""], "全空"),
    (["细胞壁", "叶绿体", "液泡", "细胞核", "细胞膜", "细胞质", ""], "漏一个"),
]

for ans, desc in tests:
    result = check_hotspot_answer(ans, q['answer'])
    print(f"{desc}: {result}")

print("\n测试完成!")
