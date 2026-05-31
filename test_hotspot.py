# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r"C:\Users\Administrator\Desktop\学练考")
from question_shitu_final import SHITU_QUESTIONS

# 检查 image_hotspot 题目
for q in SHITU_QUESTIONS:
    if q.get("type") == "image_hotspot":
        print(f"Found image_hotspot: {q['id']}")
        print(f"  image: {q.get('image')}")
        print(f"  hotspots: {len(q.get('hotspots', []))}")
        for i, h in enumerate(q.get('hotspots', [])):
            print(f"    {i+1}. {h['label']} -> ({h['x']}, {h['y']}) width={h.get('width', 8)}")
        print(f"  answer: {q.get('answer')}")

# 统计各类型题目数量
counts = {}
for q in SHITU_QUESTIONS:
    t = q.get("type", "unknown")
    counts[t] = counts.get(t, 0) + 1
print(f"\n题型统计: {counts}")
