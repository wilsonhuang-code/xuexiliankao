# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r"C:\Users\Administrator\Desktop\学练考")
from question_shitu_final import SHITU_QUESTIONS

# 找出所有 type=select 且有图片的题目（可能图片上有标注）
for q in SHITU_QUESTIONS:
    if q.get("type") == "select" and q.get("image"):
        print(f"img={q.get('image')}, id={q['id']}, Q={q.get('question')[:70]}")
