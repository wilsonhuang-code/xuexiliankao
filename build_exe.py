# -*- coding: utf-8 -*-
"""学练考桌面版 - EXE打包脚本 v2"""

import os
import sys
import shutil
import subprocess

# ============ 配置 ============
APP_DIR = r"C:\Users\Administrator\Desktop\学练考"
MAIN_SCRIPT = os.path.join(APP_DIR, "学练考桌面版.py")
OUTPUT_NAME = "学练考桌面版"
ICON_PATH = None  # 有图标就写路径

# 需要打包的Python模块
PYTHON_MODULES = [
    "question_bank.py",
    "question_gen.py",
    "question_shitu_final.py",
    "question_shitu.py",
    "question_shitu_v2.py",
    "question_geo_shitu.py",
    "question_geo_xiangjiao.py",
    "question_exam_real.py",
    "question_hunan_exam.py",
    "question_hunan_bio.py",
    "question_hunan_geo.py",
    "question_hunan_geo_v2.py",
    "question_match.py",
]

# 需要打包的数据文件
DATA_FILES = [
    "all_expanded_questions.json",
    "study_data.db",
    "quiz_auto_config.json",
]

# 需要打包的目录
DATA_DIRS = [
    "_shitu_images",
]

# 工具脚本（独立启动）
TOOL_SCRIPTS = [
    "quiz_collector.py",
    "image_analyzer.py",
    "ocr_tool.py",
    "analyze_images.py",
    "check_img.py",
    "list_select_img.py",
]

# 隐藏导入
HIDDEN_IMPORTS = [
    "pythoncom",
    "win32com.client",
    "pywintypes",
    "question_bank",
    "question_gen",
    "question_shitu",
    "question_shitu_final",
    "question_shitu_v2",
    "question_geo_shitu",
    "question_geo_xiangjiao",
    "question_exam_real",
    "question_hunan_exam",
    "question_hunan_bio",
    "question_hunan_geo",
    "question_hunan_geo_v2",
    "question_match",
]

# ============ 构建命令 ============
def build():
    print("=" * 50)
    print("学练考桌面版 - EXE打包 v2")
    print("=" * 50)

    os.chdir(APP_DIR)
    print(f"工作目录: {APP_DIR}")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", OUTPUT_NAME,
        "--onedir",
        "--windowed",
        "--noconfirm",
        "--clean",
    ]

    if ICON_PATH and os.path.exists(ICON_PATH):
        cmd.extend(["--icon", ICON_PATH])

    for imp in HIDDEN_IMPORTS:
        cmd.extend(["--hidden-import", imp])

    for f in DATA_FILES:
        if os.path.exists(f):
            cmd.extend(["--add-data", f"{f};."])
            print(f"  + 文件: {f}")

    for d in DATA_DIRS:
        if os.path.exists(d):
            cmd.extend(["--add-data", f"{d};{d}"])
            print(f"  + 目录: {d}/")

    for mod in PYTHON_MODULES:
        if os.path.exists(mod):
            cmd.extend(["--add-data", f"{mod};."])
            print(f"  + 模块: {mod}")

    for tool in TOOL_SCRIPTS:
        if os.path.exists(tool):
            cmd.extend(["--add-data", f"{tool};."])
            print(f"  + 工具: {tool}")

    cmd.append(MAIN_SCRIPT)

    print("\n执行命令...")
    print(" ".join(cmd[:10]), "...")
    print()

    result = subprocess.run(cmd, cwd=APP_DIR)

    if result.returncode == 0:
        print("\n" + "=" * 50)
        print("打包成功!")
        print("=" * 50)
        output_dir = os.path.join(APP_DIR, "dist", OUTPUT_NAME)
        exe_path = os.path.join(output_dir, f"{OUTPUT_NAME}.exe")
        print(f"输出目录: {output_dir}")
        print(f"主程序: {exe_path}")

        # 复制启动脚本
        bat_src = os.path.join(APP_DIR, "启动系统.bat")
        bat_dst = os.path.join(output_dir, "启动系统.bat")
        if os.path.exists(bat_src):
            shutil.copy(bat_src, bat_dst)
            print("已复制启动脚本")

        # 创建工具快捷方式目录
        tools_dir = os.path.join(output_dir, "工具")
        os.makedirs(tools_dir, exist_ok=True)
        for tool in TOOL_SCRIPTS:
            src = os.path.join(APP_DIR, tool)
            if os.path.exists(src):
                shutil.copy(src, tools_dir)
        print("已复制工具脚本到 工具/ 目录")

        print("\n打包完成！")
    else:
        print("\n打包失败，请检查错误信息")
        return False

    return True

if __name__ == "__main__":
    success = build()
    sys.exit(0 if success else 1)
