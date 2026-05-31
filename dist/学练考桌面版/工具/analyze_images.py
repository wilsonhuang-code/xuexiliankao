# -*- coding: utf-8 -*-
"""分析所有识图选择题，找出图片上可能直接标注了答案的题"""
import sys, os
sys.path.insert(0, r"C:\Users\Administrator\Desktop\学练考")
from question_shitu_final import SHITU_QUESTIONS
from PIL import Image

img_dir = r"C:\Users\Administrator\Desktop\学练考\_shitu_images"

# 按图片分组
groups = {}
for q in SHITU_QUESTIONS:
    if q.get("type") == "select" and q.get("image"):
        img = q.get("image")
        groups.setdefault(img, []).append(q)

print("=" * 60)
print("带图片的选择题分组（可能图片上有标注的）：")
print("=" * 60)
for img, qs in sorted(groups.items()):
    img_path = os.path.join(img_dir, img)
    size = "?"
    if os.path.exists(img_path):
        try:
            im = Image.open(img_path)
            size = f"{im.size[0]}x{im.size[1]}"
        except:
            pass
    print(f"\n【{img}】尺寸:{size}  {len(qs)}道题")
    for q in qs:
        print(f"  - {q['id']}: {q['question'][:55]}")
