#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全自动题库采集器（图像识别版）
- 无需手动输入任何坐标，依赖图片模板自动定位选项按钮
- 题目区域和答案文本区域首次运行需用热键记录，之后自动保存使用
- 支持保存采集记录为 JSON / CSV
"""

import os
import sys
import subprocess
import importlib
import threading
import time
import re
import json
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, font, scrolledtext, filedialog

# ==================== 自动安装缺失库 ====================
REQUIRED_LIBRARIES = {
    'pyautogui': 'pyautogui',
    'keyboard': 'keyboard',
    'pyperclip': 'pyperclip',
    'PIL': 'Pillow'
}
MIRRORS = [
    "https://pypi.tuna.tsinghua.edu.cn/simple",
    "https://mirrors.aliyun.com/pypi/simple/",
]

def install_package(pkg, mirror):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-i", mirror],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        return False

def check_and_install():
    missing = []
    for mod, pkg in REQUIRED_LIBRARIES.items():
        try:
            if mod == 'PIL':
                from PIL import Image
            else:
                importlib.import_module(mod)
        except ImportError:
            missing.append(pkg)
    if not missing:
        return True
    temp = tk.Tk()
    temp.withdraw()
    ans = messagebox.askyesno("缺失依赖", f"需要安装 {', '.join(missing)}\n是否自动安装？")
    temp.destroy()
    if not ans:
        sys.exit(1)
    for pkg in missing:
        for mirror in MIRRORS:
            if install_package(pkg, mirror):
                print(f"{pkg} 安装成功")
                break
        else:
            print(f"{pkg} 安装失败")
            sys.exit(1)
    msg = tk.Tk()
    msg.withdraw()
    messagebox.showinfo("完成", "依赖已安装，请重启程序")
    msg.destroy()
    sys.exit(0)

check_and_install()

import pyautogui
import keyboard
import pyperclip
from PIL import Image

# ==================== 配置类 ====================
class Config:
    CONFIG_FILE = "quiz_auto_config.json"
    RECORD_FILE = "collected_questions.json"
    OPTION_IMAGES = {
        'A': 'A.png',
        'B': 'B.png',
        'C': 'C.png',
        'D': 'D.png'
    }

# ==================== 主程序 ====================
class AutoQuizCollector:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("全自动题库采集器（图像识别版）")
        self.root.geometry("800x700")
        self.root.configure(bg='#F5F7FA')

        self.collecting = False
        self.collect_thread = None
        self.records = []

        # 存储坐标（从配置文件加载）
        self.question_pos = None      # (x, y)
        self.answer_text_pos = None   # (x, y)

        # 加载配置
        self.load_config()
        self.load_records()

        self.create_widgets()
        self.register_hotkeys()

    def create_widgets(self):
        # 说明区域
        info = """🤖 全自动采集模式（基于图像识别）
使用步骤：
1. 准备好选项按钮的截图（A.png, B.png, C.png, D.png），放在程序同目录下。
2. 将鼠标移动到【题目区域】（题目文字上），按 F2 记录位置。
3. 将鼠标移动到【答案文本区域】（显示正确答案的文字上），按 F3 记录位置。
4. 按 F4 或点击【开始采集】，程序将自动：
   - 点击题目区域复制题目
   - 点击答案文本区域复制答案
   - 根据识别出的答案字母，自动搜索屏幕上的对应选项图片并点击
   - 自动翻页（可设置翻页热键）
5. 按 ESC 或 F4 停止采集。
"""
        info_frame = tk.Frame(self.root, bg='#E3F2FD', relief=tk.GROOVE, bd=1)
        info_frame.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(info_frame, text=info, bg='#E3F2FD', fg='#0D47A1', justify=tk.LEFT,
                 font=('微软雅黑', 9)).pack(padx=10, pady=8)

        # 参数设置区域
        param_frame = ttk.LabelFrame(self.root, text="参数设置", padding=10)
        param_frame.pack(fill=tk.X, padx=20, pady=5)

        # 图片路径
        img_frame = tk.Frame(param_frame, bg='#F5F7FA')
        img_frame.pack(fill=tk.X, pady=5)
        tk.Label(img_frame, text="选项图片目录:", width=12, anchor=tk.W, bg='#F5F7FA').pack(side=tk.LEFT)
        self.img_dir = tk.StringVar(value=os.getcwd())
        tk.Entry(img_frame, textvariable=self.img_dir, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(img_frame, text="浏览", command=self.select_img_dir, bg='#42A5F5', fg='white').pack(side=tk.LEFT)

        # 翻页热键
        hotkey_frame = tk.Frame(param_frame, bg='#F5F7FA')
        hotkey_frame.pack(fill=tk.X, pady=5)
        tk.Label(hotkey_frame, text="翻页热键:", width=12, anchor=tk.W, bg='#F5F7FA').pack(side=tk.LEFT)
        self.next_hotkey = tk.StringVar(value="ctrl+right")
        tk.Entry(hotkey_frame, textvariable=self.next_hotkey, width=15).pack(side=tk.LEFT, padx=5)
        tk.Label(hotkey_frame, text="  采集间隔(秒):", bg='#F5F7FA').pack(side=tk.LEFT, padx=10)
        self.interval = tk.DoubleVar(value=1.0)
        tk.Spinbox(hotkey_frame, from_=0.5, to=3.0, increment=0.5, textvariable=self.interval, width=5).pack(side=tk.LEFT)

        # 坐标状态显示
        status_frame = ttk.LabelFrame(self.root, text="当前已记录的坐标", padding=10)
        status_frame.pack(fill=tk.X, padx=20, pady=5)
        self.q_status = tk.Label(status_frame, text="题目区域: 未记录", bg='#F5F7FA', fg='#F44336')
        self.q_status.pack(anchor=tk.W)
        self.a_status = tk.Label(status_frame, text="答案文本区域: 未记录", bg='#F5F7FA', fg='#F44336')
        self.a_status.pack(anchor=tk.W)
        if self.question_pos:
            self.q_status.config(text=f"题目区域: ({self.question_pos[0]}, {self.question_pos[1]})", fg='#2ECC71')
        if self.answer_text_pos:
            self.a_status.config(text=f"答案文本区域: ({self.answer_text_pos[0]}, {self.answer_text_pos[1]})", fg='#2ECC71')

        # 控制按钮
        btn_frame = tk.Frame(self.root, bg='#F5F7FA')
        btn_frame.pack(pady=10)
        self.start_btn = tk.Button(btn_frame, text="▶ 开始采集 (F4)", command=self.start_collection,
                                   bg='#4CAF50', fg='white', padx=20, pady=5, font=('', 10, 'bold'))
        self.start_btn.pack(side=tk.LEFT, padx=10)
        self.stop_btn = tk.Button(btn_frame, text="⏹ 停止采集 (ESC)", command=self.stop_collection,
                                  bg='#F44336', fg='white', padx=20, pady=5, state=tk.DISABLED, font=('', 10, 'bold'))
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="清空日志", command=self.clear_log, bg='#78909C', fg='white').pack(side=tk.LEFT, padx=10)

        # 日志区域
        log_frame = ttk.LabelFrame(self.root, text="运行日志", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, state=tk.DISABLED, font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 记录查看区域
        record_frame = ttk.LabelFrame(self.root, text="采集记录", padding=5)
        record_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        self.record_tree = ttk.Treeview(record_frame, columns=("num","time","question","answer"), show="headings", height=6)
        self.record_tree.heading("num", text="序号")
        self.record_tree.heading("time", text="时间")
        self.record_tree.heading("question", text="题目")
        self.record_tree.heading("answer", text="答案")
        self.record_tree.column("num", width=50)
        self.record_tree.column("time", width=140)
        self.record_tree.column("question", width=400)
        self.record_tree.column("answer", width=60)
        scroll = ttk.Scrollbar(record_frame, orient=tk.VERTICAL, command=self.record_tree.yview)
        self.record_tree.configure(yscrollcommand=scroll.set)
        self.record_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        btn_record = tk.Frame(self.root, bg='#F5F7FA')
        btn_record.pack(pady=5)
        tk.Button(btn_record, text="导出CSV", command=self.export_csv, bg='#FFA726', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_record, text="清空记录", command=self.clear_records, bg='#EF5350', fg='white').pack(side=tk.LEFT, padx=5)

        self.root.bind('<Escape>', lambda e: self.stop_collection())

    def select_img_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.img_dir.set(d)

    def load_config(self):
        if os.path.exists(Config.CONFIG_FILE):
            try:
                with open(Config.CONFIG_FILE, 'r') as f:
                    cfg = json.load(f)
                self.question_pos = tuple(cfg.get('question_pos', [None, None]))
                self.answer_text_pos = tuple(cfg.get('answer_text_pos', [None, None]))
                if self.question_pos[0] is not None:
                    self.question_pos = (int(self.question_pos[0]), int(self.question_pos[1]))
                else:
                    self.question_pos = None
                if self.answer_text_pos[0] is not None:
                    self.answer_text_pos = (int(self.answer_text_pos[0]), int(self.answer_text_pos[1]))
                else:
                    self.answer_text_pos = None
            except:
                pass

    def save_config(self):
        cfg = {
            'question_pos': list(self.question_pos) if self.question_pos else [None, None],
            'answer_text_pos': list(self.answer_text_pos) if self.answer_text_pos else [None, None]
        }
        with open(Config.CONFIG_FILE, 'w') as f:
            json.dump(cfg, f)

    def load_records(self):
        if os.path.exists(Config.RECORD_FILE):
            try:
                with open(Config.RECORD_FILE, 'r', encoding='utf-8') as f:
                    self.records = json.load(f)
                self.refresh_record_display()
            except:
                self.records = []

    def save_records(self):
        with open(Config.RECORD_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.records, f, ensure_ascii=False, indent=2)

    def refresh_record_display(self):
        for item in self.record_tree.get_children():
            self.record_tree.delete(item)
        for idx, rec in enumerate(self.records, 1):
            q_short = rec['question'][:40] + "..." if len(rec['question']) > 40 else rec['question']
            self.record_tree.insert("", tk.END, values=(idx, rec['timestamp'], q_short, rec['answer']))

    def export_csv(self):
        if not self.records:
            messagebox.showinfo("提示", "无记录")
            return
        fn = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if fn:
            import csv
            with open(fn, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["序号", "时间", "题目", "答案"])
                for idx, rec in enumerate(self.records, 1):
                    writer.writerow([idx, rec['timestamp'], rec['question'], rec['answer']])
            self.log(f"已导出 {len(self.records)} 条记录")

    def clear_records(self):
        if messagebox.askyesno("确认", "清空所有记录？"):
            self.records = []
            self.save_records()
            self.refresh_record_display()
            self.log("记录已清空")

    def register_hotkeys(self):
        # F2: 记录当前鼠标位置为题目区域坐标
        keyboard.add_hotkey('f2', self.capture_question_pos)
        # F3: 记录答案文本区域坐标
        keyboard.add_hotkey('f3', self.capture_answer_text_pos)
        # F4: 开始/停止
        keyboard.add_hotkey('f4', self.toggle_collection)
        self.log("热键已注册：F2(记录题目坐标)  F3(记录答案坐标)  F4(开始/停止)")

    def capture_question_pos(self):
        x, y = pyautogui.position()
        self.question_pos = (x, y)
        self.save_config()
        self.q_status.config(text=f"题目区域: ({x}, {y})", fg='#2ECC71')
        self.log(f"题目坐标已记录: ({x}, {y})")

    def capture_answer_text_pos(self):
        x, y = pyautogui.position()
        self.answer_text_pos = (x, y)
        self.save_config()
        self.a_status.config(text=f"答案文本区域: ({x}, {y})", fg='#2ECC71')
        self.log(f"答案文本坐标已记录: ({x}, {y})")

    def toggle_collection(self):
        if self.collecting:
            self.stop_collection()
        else:
            self.start_collection()

    def log(self, msg):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def press_hotkey(self, key):
        try:
            if '+' in key:
                mod, k = key.split('+')
                if mod == 'ctrl':
                    keyboard.press_and_release(f'ctrl+{k}')
                elif mod == 'alt':
                    keyboard.press_and_release(f'alt+{k}')
                else:
                    keyboard.press_and_release(key)
            else:
                keyboard.press_and_release(key)
        except:
            pass

    def find_and_click_option(self, letter):
        """使用图像识别找到选项按钮并点击"""
        # 构建图片完整路径
        img_name = Config.OPTION_IMAGES.get(letter)
        if not img_name:
            return False
        img_path = os.path.join(self.img_dir.get(), img_name)
        if not os.path.exists(img_path):
            self.log(f"图片不存在: {img_path}")
            return False
        try:
            # 在屏幕上查找图片，置信度0.8
            location = pyautogui.locateOnScreen(img_path, confidence=0.8)
            if location:
                center = pyautogui.center(location)
                pyautogui.click(center)
                self.log(f"图像识别成功：点击选项 {letter} 在 {center}")
                return True
            else:
                self.log(f"未在屏幕中找到选项 {letter} 的图片")
                return False
        except Exception as e:
            self.log(f"图像识别异常: {e}")
            return False

    def start_collection(self):
        if self.collecting:
            return
        if not self.question_pos or not self.answer_text_pos:
            messagebox.showerror("错误", "请先使用 F2 和 F3 记录题目坐标和答案文本坐标")
            return
        # 检查选项图片是否存在
        missing = []
        for letter, fname in Config.OPTION_IMAGES.items():
            path = os.path.join(self.img_dir.get(), fname)
            if not os.path.exists(path):
                missing.append(fname)
        if missing:
            messagebox.showerror("错误", f"缺少选项图片: {', '.join(missing)}\n请将图片放在 {self.img_dir.get()} 目录下")
            return

        self.collecting = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.log("开始采集，按 ESC 或 F4 停止")
        self.collect_thread = threading.Thread(target=self.collect_loop, daemon=True)
        self.collect_thread.start()

    def stop_collection(self):
        self.collecting = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log("采集已停止")

    def collect_loop(self):
        qx, qy = self.question_pos
        atx, aty = self.answer_text_pos
        interval = self.interval.get()
        next_hk = self.next_hotkey.get()
        copy_hk = "ctrl+c"

        count = 0
        time.sleep(1)

        while self.collecting:
            try:
                # 1. 点击题目区域，复制题目
                pyautogui.click(qx, qy)
                time.sleep(0.2)
                self.press_hotkey(copy_hk)
                time.sleep(0.3)
                question = pyperclip.paste().strip()
                if not question:
                    self.log(f"第{count+1}题复制失败，跳过")
                    self.press_hotkey(next_hk)
                    time.sleep(interval)
                    continue

                # 2. 点击答案文本区域，复制答案
                pyautogui.click(atx, aty)
                time.sleep(0.2)
                self.press_hotkey(copy_hk)
                time.sleep(0.3)
                answer_raw = pyperclip.paste().strip().upper()
                match = re.search(r'[A-D]', answer_raw)
                if match:
                    ans_letter = match.group()
                    # 3. 图像识别点击选项
                    if self.find_and_click_option(ans_letter):
                        self.log(f"第{count+1}题 答案{ans_letter} 已勾选")
                    else:
                        self.log(f"第{count+1}题 答案{ans_letter} 勾选失败")
                    # 保存记录
                    self.records.append({
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "question": question,
                        "answer": ans_letter
                    })
                    self.save_records()
                    self.root.after(0, self.refresh_record_display)
                else:
                    self.log(f"第{count+1}题 未识别答案: {answer_raw}")
                count += 1
                self.log(f"已完成 {count} 题")

                # 4. 翻页
                self.press_hotkey(next_hk)
                time.sleep(interval)

            except Exception as e:
                self.log(f"采集异常: {e}")
                time.sleep(2)

        self.log(f"采集结束，共处理 {count} 题")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    print("=" * 60)
    print("全自动题库采集器（图像识别版）")
    print("使用说明：")
    print("1. 准备四个选项按钮截图：A.png, B.png, C.png, D.png 放在程序目录下")
    print("2. 将鼠标移到题目文字上，按 F2")
    print("3. 将鼠标移到答案文字上，按 F3")
    print("4. 按 F4 自动开始采集，ESC 停止")
    print("=" * 60)
    app = AutoQuizCollector()
    app.run()
