# -*- coding: utf-8 -*-
"""测试 image_hotspot 题型渲染"""
import sys, os
sys.path.insert(0, r"C:\Users\Administrator\Desktop\学练考")
os.chdir(r"C:\Users\Administrator\Desktop\学练考")

import tkinter as tk
from 学练考桌面版 import StudyApp

app = StudyApp()
app.geometry("900x700")

# 找到 image_hotspot 题目
from question_shitu_final import SHITU_QUESTIONS
hotspot_q = None
for q in SHITU_QUESTIONS:
    if q.get("type") == "image_hotspot":
        hotspot_q = q
        break

if hotspot_q:
    print(f"测试题目: {hotspot_q['id']}")
    print(f"  type: {hotspot_q['type']}")
    print(f"  hotspots: {len(hotspot_q.get('hotspots', []))}")
    print(f"  answer: {hotspot_q.get('answer')}")

    # 模拟设置题目列表并渲染
    app.questions = [hotspot_q]
    app.current_index = 0
    app.stats = {"total": 0, "correct": 0, "wrong": 0, "score": 0}
    app.mode = "practice"

    try:
        app._render_question()
        print("\n渲染成功！")
        print(f"fill_entries count: {len(app.fill_entries)}")
        print(f"fill_vars count: {len(app.fill_vars)}")
        for i, (e, v) in enumerate(zip(app.fill_entries, app.fill_vars)):
            hs = hotspot_q['hotspots'][i]
            print(f"  Entry {i+1} ({hs['label']}): 位置=({hs['x']},{hs['y']}) width={hs.get('width',8)}")
    except Exception as ex:
        print(f"渲染失败: {ex}")
        import traceback
        traceback.print_exc()
else:
    print("未找到 image_hotspot 题目")

# 保持窗口打开以便查看
print("\n按 Ctrl+C 关闭测试窗口")
root.mainloop()
