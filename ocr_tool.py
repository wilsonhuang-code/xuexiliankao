# -*- coding: utf-8 -*-
"""
==========================================================================
    OCR图片文字识别提取系统 v1 - 多线程加速版
    从 D:\快递出库系统\图片文字识别_v5.py 适配而来
    集成到学练考系统中，可通过主程序工具栏启动
==========================================================================
"""

import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from tkinter import (
    Tk, Frame, Label, Button, Entry, Text, Scrollbar, StringVar, OptionMenu,
    filedialog, messagebox, END, RIGHT, Y, BOTH, LEFT, BOTTOM, X, VERTICAL,
    HORIZONTAL, NORMAL, DISABLED, WORD, Checkbutton, Canvas, SUNKEN, Spinbox,
    IntVar
)
from tkinter.ttk import Progressbar
import tkinter as tk

try:
    from PIL import Image, ImageTk
    import cv2
    import numpy as np
except ImportError as e:
    print(f"缺少必要的库: {e}")
    print("请先运行: pip install opencv-python pillow numpy")
    sys.exit(1)


def cv2_imread(filepath):
    """兼容中文路径的图片读取"""
    try:
        img_array = np.fromfile(filepath, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"[错误] cv2_imread 读取失败 ({filepath}): {e}")
        return None


def cv2_imwrite(filepath, img):
    """兼容中文路径的图片写入"""
    try:
        ext = os.path.splitext(filepath)[1]
        result, buf = cv2.imencode(ext, img)
        if result:
            buf.tofile(filepath)
            return True
        return False
    except Exception as e:
        print(f"[错误] cv2_imwrite 写入失败 ({filepath}): {e}")
        return False


class OcrSystem:
    """OCR综合图片文字识别提取系统 - 多线程加速版"""
    
    def __init__(self):
        self.root = Tk()
        self.root.title("OCR图片文字识别提取系统 - 多线程加速版 [v1]")
        self.root.geometry("1300x850")
        self.root.minsize(1024, 768)

        self.paddle_ocr = None
        self.easy_reader = None
        self.paddle_available = False
        self.easy_available = False
        self.easy_loading = False
        
        self.current_engine = StringVar(value="PaddleOCR")
        self.current_image_path = None
        self.current_image_tk = None
        self.preprocessed_image_tk = None

        cpu_count = os.cpu_count() or 2
        self.max_workers = IntVar(value=min(4, cpu_count))
        self.ocr_lock = threading.Lock()
        self.batch_cancel = False
        self.executor = None

        self.auto_resize_var = tk.BooleanVar(value=True)
        self.angle_cls_var = tk.BooleanVar(value=True)
        self.fast_mode_var = tk.BooleanVar(value=False)

        self.paddle_lang_map = {
            "中文简体": "ch", "中文繁体": "chinese_cht", "英文": "en",
            "日文": "japan", "韩文": "korean", "法文": "french",
            "德文": "german", "西班牙文": "spanish"
        }
        self.easyocr_lang_map = {
            "中文简体": "ch_sim", "中文繁体": "ch_tra", "英文": "en",
            "日文": "ja", "韩文": "ko", "法文": "fr",
            "德文": "de", "西班牙文": "es"
        }
        self.current_lang = StringVar(value="中文简体")
        self.current_lang.trace('w', self._on_lang_change)

        self._setup_ui()
        
        self._log_message("系统初始化中...")
        self._log_message(f"CPU核心数：{cpu_count}，默认线程数：{self.max_workers.get()}")
        self._log_message("已启用中文路径兼容模式")
        self._log_message("多线程批量识别已就绪")
        threading.Thread(target=self._load_paddle_ocr, daemon=True).start()
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_ui(self):
        top_frame = Frame(self.root)
        top_frame.pack(fill=X, padx=10, pady=5)

        Label(top_frame, text="识别引擎:").pack(side=LEFT, padx=5)
        self.engine_menu = OptionMenu(top_frame, self.current_engine, "PaddleOCR", "EasyOCR")
        self.engine_menu.pack(side=LEFT, padx=5)
        self.current_engine.trace('w', self._on_engine_change)

        Label(top_frame, text="识别语言:").pack(side=LEFT, padx=5)
        self.lang_menu = OptionMenu(top_frame, self.current_lang, *self.paddle_lang_map.keys())
        self.lang_menu.pack(side=LEFT, padx=5)

        Label(top_frame, text="图片路径:").pack(side=LEFT, padx=5)
        self.path_entry = Entry(top_frame, width=35)
        self.path_entry.pack(side=LEFT, padx=5)
        Button(top_frame, text="浏览", command=self._select_image).pack(side=LEFT, padx=2)
        Button(top_frame, text="识别", command=self._start_recognition, fg="blue").pack(side=LEFT, padx=5)

        batch_frame = Frame(self.root)
        batch_frame.pack(fill=X, padx=10, pady=2)

        Label(batch_frame, text="批量操作:").pack(side=LEFT, padx=5)
        Button(batch_frame, text="批量选择图片", command=self._batch_select_images).pack(side=LEFT, padx=2)
        Button(batch_frame, text="选择文件夹", command=self._select_folder).pack(side=LEFT, padx=2)
        self.cancel_btn = Button(batch_frame, text="停止", command=self._cancel_batch, fg="red", state=DISABLED)
        self.cancel_btn.pack(side=LEFT, padx=2)

        Label(batch_frame, text="  |  速度优化:").pack(side=LEFT, padx=5)
        Checkbutton(batch_frame, text="自动缩放大图", variable=self.auto_resize_var).pack(side=LEFT, padx=2)
        Checkbutton(batch_frame, text="角度分类", variable=self.angle_cls_var).pack(side=LEFT, padx=2)
        Checkbutton(batch_frame, text="快速模式", variable=self.fast_mode_var).pack(side=LEFT, padx=2)

        Label(batch_frame, text="  线程数:").pack(side=LEFT, padx=5)
        Spinbox(batch_frame, from_=1, to=8, width=3, textvariable=self.max_workers).pack(side=LEFT, padx=2)

        Button(batch_frame, text="清空结果", command=self._clear_results).pack(side=RIGHT, padx=5)
        Button(batch_frame, text="💾 保存结果JSON", command=self._save_results).pack(side=RIGHT, padx=5)

        pre_frame = Frame(self.root)
        pre_frame.pack(fill=X, padx=10, pady=2)
        Label(pre_frame, text="预处理:").pack(side=LEFT, padx=5)
        self.grayscale_var = tk.BooleanVar()
        Checkbutton(pre_frame, text="灰度化", variable=self.grayscale_var).pack(side=LEFT, padx=2)
        self.binarize_var = tk.BooleanVar()
        Checkbutton(pre_frame, text="二值化", variable=self.binarize_var).pack(side=LEFT, padx=2)
        self.denoise_var = tk.BooleanVar()
        Checkbutton(pre_frame, text="降噪", variable=self.denoise_var).pack(side=LEFT, padx=2)
        self.resize_var = tk.BooleanVar()
        Checkbutton(pre_frame, text="缩放到标准尺寸", variable=self.resize_var).pack(side=LEFT, padx=2)

        main_frame = Frame(self.root)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)
        left_frame = Frame(main_frame)
        left_frame.pack(side=LEFT, fill=BOTH, expand=True)
        right_frame = Frame(main_frame)
        right_frame.pack(side=RIGHT, fill=BOTH, expand=True)

        Label(left_frame, text="原始图片:").pack(anchor="w")
        self.image_canvas = Canvas(left_frame, bg='gray', width=500, height=400)
        self.image_canvas.pack(fill=BOTH, expand=True, padx=5, pady=5)
        Label(left_frame, text="预处理图片:").pack(anchor="w")
        self.preprocess_canvas = Canvas(left_frame, bg='gray', width=500, height=400)
        self.preprocess_canvas.pack(fill=BOTH, expand=True, padx=5, pady=5)

        Label(right_frame, text="识别结果:").pack(anchor="w")
        text_frame = Frame(right_frame)
        text_frame.pack(fill=BOTH, expand=True)
        self.result_text = Text(text_frame, wrap=WORD, font=("Microsoft YaHei", 11))
        self.result_text.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar = Scrollbar(text_frame, orient=VERTICAL, command=self.result_text.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.result_text.config(yscrollcommand=scrollbar.set)

        status_frame = Frame(self.root)
        status_frame.pack(side=BOTTOM, fill=X)
        self.status_bar = Label(status_frame, text="就绪", bd=1, relief=SUNKEN, anchor="w")
        self.status_bar.pack(fill=X)
        self.progress_bar = Progressbar(status_frame, mode='determinate')
        self.progress_bar.pack(fill=X)
        
        # 保存识别结果的数据
        self._ocr_results = {}

    def _load_paddle_ocr(self):
        try:
            from paddleocr import PaddleOCR
            lang_code = self.paddle_lang_map[self.current_lang.get()]
            use_angle = self.angle_cls_var.get()
            if self.fast_mode_var.get():
                self.paddle_ocr = PaddleOCR(
                    use_angle_cls=use_angle, lang=lang_code, show_log=False,
                    rec_batch_num=8, det_db_score_mode="fast", max_text_length=30, use_dilation=False)
            else:
                self.paddle_ocr = PaddleOCR(use_angle_cls=use_angle, lang=lang_code, show_log=False, rec_batch_num=8)
            self.paddle_available = True
            self._log_message(f"PaddleOCR引擎加载完成")
        except Exception as e:
            self.paddle_available = False
            self._log_message(f"PaddleOCR加载失败: {e}")

    def _load_easy_ocr(self):
        if self.easy_loading:
            return
        self.easy_loading = True
        try:
            import easyocr
            lang_code = self.easyocr_lang_map[self.current_lang.get()]
            self._log_message("正在加载 EasyOCR 引擎...")
            self.easy_reader = easyocr.Reader([lang_code], gpu=False, verbose=False)
            self.easy_available = True
            self._log_message("EasyOCR引擎加载完成")
        except Exception as e:
            self.easy_available = False
            self._log_message(f"EasyOCR加载失败: {e}")
        finally:
            self.easy_loading = False

    def _on_engine_change(self, *args):
        engine = self.current_engine.get()
        if engine == "EasyOCR" and not self.easy_available and not self.easy_loading:
            threading.Thread(target=self._load_easy_ocr, daemon=True).start()

    def _on_lang_change(self, *args):
        threading.Thread(target=self._load_paddle_ocr, daemon=True).start()
        if self.easy_available or self.easy_loading:
            self.easy_available = False
            threading.Thread(target=self._load_easy_ocr, daemon=True).start()

    def _select_image(self):
        file_path = filedialog.askopenfilename(
            title="选择图片文件",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp *.tiff"), ("所有文件", "*.*")])
        if file_path:
            self.path_entry.delete(0, END)
            self.path_entry.insert(0, file_path)
            self.current_image_path = file_path
            self._display_original_image()

    def _batch_select_images(self):
        file_paths = filedialog.askopenfilenames(
            title="选择多个图片文件",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp *.tiff"), ("所有文件", "*.*")])
        if file_paths:
            self._start_batch_recognition(list(file_paths))

    def _select_folder(self):
        folder = filedialog.askdirectory(title="选择包含图片的文件夹")
        if not folder:
            return
        image_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}
        paths = [os.path.join(folder, f) for f in os.listdir(folder)
                 if os.path.splitext(f)[1].lower() in image_exts]
        if not paths:
            messagebox.showinfo("提示", "文件夹中没有找到图片文件")
            return
        paths.sort()
        self._start_batch_recognition(paths)

    def _display_original_image(self):
        try:
            img = Image.open(self.current_image_path)
            img.thumbnail((500, 400))
            self.current_image_tk = ImageTk.PhotoImage(img)
            self.image_canvas.delete("all")
            self.image_canvas.create_image(250, 200, anchor="center", image=self.current_image_tk)
            self.image_canvas.image = self.current_image_tk
        except Exception as e:
            self._log_message(f"图片加载失败: {e}")

    def _display_preprocessed_image(self, image_path):
        try:
            img = Image.open(image_path)
            img.thumbnail((500, 400))
            self.preprocessed_image_tk = ImageTk.PhotoImage(img)
            self.preprocess_canvas.delete("all")
            self.preprocess_canvas.create_image(250, 200, anchor="center", image=self.preprocessed_image_tk)
            self.preprocess_canvas.image = self.preprocessed_image_tk
        except Exception as e:
            self._log_message(f"预处理图片显示失败: {e}")

    def _auto_resize_image(self, img, max_width=1600, max_height=1200):
        h, w = img.shape[:2]
        if w <= max_width and h <= max_height:
            return img
        scale = min(max_width / w, max_height / h)
        resized = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        self._log_message(f"  图片已缩放：{w}x{h} -> {int(w*scale)}x{int(h*scale)}")
        return resized

    def _preprocess_image(self, image_path):
        img = cv2_imread(image_path)
        if img is None:
            raise ValueError(f"无法读取图片: {image_path}")
        if self.auto_resize_var.get():
            img = self._auto_resize_image(img)
        if self.grayscale_var.get():
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if self.binarize_var.get():
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            img = binary
        if self.denoise_var.get():
            img = cv2.medianBlur(img, 3)
        if self.resize_var.get():
            img = cv2.resize(img, (800, 600))
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        temp_dir = os.path.dirname(os.path.abspath(__file__))
        temp_path = os.path.join(temp_dir, f"temp_preprocessed_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg")
        if not cv2_imwrite(temp_path, img):
            raise ValueError(f"无法保存预处理图片: {temp_path}")
        return temp_path

    def _start_recognition(self):
        if not self.current_image_path:
            messagebox.showwarning("警告", "请先选择图片")
            return
        engine = self.current_engine.get()
        if engine == "PaddleOCR" and not self.paddle_available:
            messagebox.showerror("引擎不可用", "PaddleOCR 引擎加载失败")
            return
        elif engine == "EasyOCR" and not self.easy_available:
            if not self.easy_loading:
                threading.Thread(target=self._load_easy_ocr, daemon=True).start()
                messagebox.showinfo("提示", "EasyOCR 正在后台加载中，请稍后再试")
                return
            else:
                messagebox.showinfo("提示", "EasyOCR 正在加载中，请等待...")
                return
        self.progress_bar['mode'] = 'indeterminate'
        self.progress_bar.start()
        self.status_bar.config(text="识别中...")
        start_time = time.time()
        threading.Thread(target=self._recognize, args=(self.current_image_path, start_time), daemon=True).start()

    def _recognize(self, image_path, start_time=None):
        preprocessed_path = None
        try:
            preprocessed_path = self._preprocess_image(image_path)
            self.root.after(0, lambda: self._display_preprocessed_image(preprocessed_path))
            engine = self.current_engine.get()
            with self.ocr_lock:
                if engine == "PaddleOCR":
                    result = self.paddle_ocr.ocr(preprocessed_path, cls=True)
                elif engine == "EasyOCR":
                    result = self.easy_reader.readtext(preprocessed_path)
            if engine == "PaddleOCR":
                self._parse_paddle_result(result)
            elif engine == "EasyOCR":
                self._parse_easy_result(result)
            if start_time:
                elapsed = time.time() - start_time
                self.root.after(0, lambda e=elapsed: self._log_message(f"识别耗时：{e:.2f}秒"))
                self.root.after(0, lambda e=elapsed: self.status_bar.config(text=f"识别完成（{e:.2f}秒）"))
        except Exception as e:
            self._log_message(f"识别失败: {e}")
        finally:
            if preprocessed_path and os.path.exists(preprocessed_path):
                try: os.remove(preprocessed_path)
                except: pass
            self.root.after(0, lambda: self.progress_bar.stop())

    def _start_batch_recognition(self, image_paths):
        engine = self.current_engine.get()
        if engine == "PaddleOCR" and not self.paddle_available:
            messagebox.showerror("引擎不可用", "PaddleOCR 引擎加载失败")
            return
        total = len(image_paths)
        workers = self.max_workers.get()
        self.batch_cancel = False
        self._log_message(f"\n批量识别开始：共 {total} 张图片，{workers} 个线程")
        self.progress_bar['mode'] = 'determinate'
        self.progress_bar['maximum'] = total
        self.progress_bar['value'] = 0
        self.cancel_btn.config(state=NORMAL)
        self.status_bar.config(text=f"批量识别中（0/{total}）...")
        batch_start = time.time()
        completed = [0]
        lock = threading.Lock()

        def process_single_image(path):
            if self.batch_cancel:
                return None
            try:
                preprocessed_path = self._preprocess_image(path)
                if self.batch_cancel:
                    if os.path.exists(preprocessed_path): os.remove(preprocessed_path)
                    return None
                with self.ocr_lock:
                    if self.batch_cancel:
                        if os.path.exists(preprocessed_path): os.remove(preprocessed_path)
                        return None
                    engine = self.current_engine.get()
                    if engine == "PaddleOCR":
                        result = self.paddle_ocr.ocr(preprocessed_path, cls=True)
                    elif engine == "EasyOCR":
                        result = self.easy_reader.readtext(preprocessed_path)
                if os.path.exists(preprocessed_path): os.remove(preprocessed_path)
                elapsed = time.time()
                return (path, result, elapsed)
            except Exception as e:
                return (path, None, str(e))

        self.executor = ThreadPoolExecutor(max_workers=workers)
        futures = {self.executor.submit(process_single_image, p): p for p in image_paths}

        def collect_results():
            for future in as_completed(futures):
                if self.batch_cancel: break
                try:
                    data = future.result()
                    if data is None: continue
                    path, result, elapsed_or_error = data
                    with lock:
                        completed[0] += 1
                        current = completed[0]
                    filename = os.path.basename(path)
                    if isinstance(elapsed_or_error, str):
                        self.root.after(0, lambda f=filename, e=elapsed_or_error, c=current, t=total:
                            self._log_message(f"[{c}/{t}] {f} - 失败: {e}"))
                    else:
                        # 保存结果
                        texts = []
                        if self.current_engine.get() == "PaddleOCR" and result and result[0]:
                            for res in result[0]:
                                texts.append(res[1][0])
                        elif self.current_engine.get() == "EasyOCR" and result:
                            for det in result:
                                texts.append(det[1])
                        self._ocr_results[filename] = texts
                        
                        self.root.after(0, lambda f=filename, lc=len(texts), c=current, t=total:
                            self._log_message(f"[{c}/{t}] {f} - {lc}行文本"))
                        for t in texts:
                            self.root.after(0, lambda t=t: self._log_message(f"  {t}"))
                    self.root.after(0, lambda c=current: self.progress_bar.update(value=c))
                    self.root.after(0, lambda c=current, t=total:
                        self.status_bar.config(text=f"批量识别中（{c}/{t}）..."))
                except Exception as e:
                    with lock:
                        completed[0] += 1
            total_elapsed = time.time() - batch_start
            actual = completed[0]
            self.root.after(0, lambda: self.cancel_btn.config(state=DISABLED))
            self.root.after(0, lambda: self.status_bar.config(
                text=f"批量识别完成（{actual}/{total}，总耗时 {total_elapsed:.1f}秒）"))
            self.root.after(0, lambda: self.progress_bar.update(value=0))
            if self.executor:
                self.executor.shutdown(wait=False)
                self.executor = None
            self._log_message(f"\n批量识别完成！共{actual}张，耗时{total_elapsed:.1f}秒\n")

        threading.Thread(target=collect_results, daemon=True).start()

    def _cancel_batch(self):
        self.batch_cancel = True
        self._log_message("正在取消批量识别...")

    def _parse_paddle_result(self, result):
        if not result or not result[0]:
            self.root.after(0, lambda: self._log_message("未识别到文本"))
            return
        for res in result[0]:
            text = res[1][0]
            self.root.after(0, lambda s=text: self._log_message(s))
        self.root.after(0, lambda n=len(result[0]): self._log_message(f"\n总计 {n} 行文本"))

    def _parse_easy_result(self, result):
        if not result:
            self.root.after(0, lambda: self._log_message("未识别到文本"))
            return
        for detection in result:
            text = detection[1]
            self.root.after(0, lambda s=text: self._log_message(s))
        self.root.after(0, lambda n=len(result): self._log_message(f"\n总计 {n} 行文本"))

    def _save_results(self):
        """保存OCR结果为JSON"""
        if not self._ocr_results:
            messagebox.showwarning("提示", "还没有识别结果")
            return
        path = filedialog.asksaveasfilename(
            title="保存OCR识别结果",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json")],
            initialdir=os.path.dirname(os.path.abspath(__file__)),
            initialfile=f"ocr_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        if path:
            import json
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self._ocr_results, f, ensure_ascii=False, indent=2)
            self._log_message(f"结果已保存到：{path}")

    def _log_message(self, message):
        self.result_text.insert(END, message + "\n")
        self.result_text.see(END)

    def _clear_results(self):
        self.result_text.delete(1.0, END)

    def _on_closing(self):
        self.batch_cancel = True
        if self.executor:
            self.executor.shutdown(wait=False)
        if messagebox.askokcancel("退出", "确定要退出吗？"):
            self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = OcrSystem()
    app.run()
