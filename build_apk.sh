#!/bin/bash
# 一键打包学练考系统APK
# 在Ubuntu/Debian Linux或WSL2 Ubuntu中运行
# 用法: bash build_apk.sh

set -e

echo "=== 学练考系统 APK 打包脚本 ==="

# 1. 安装依赖
echo "[1/5] 安装系统依赖..."
sudo apt-get update -y
sudo apt-get install -y python3-pip python3-venv unzip openjdk-17-jdk autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev libltdl-dev

# 2. 安装Buildozer
echo "[2/5] 安装Buildozer..."
pip3 install --upgrade pip
pip3 install buildozer cython

# 3. 准备工作目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 4. 初始化Buildozer（首次需要下载SDK/NDK，约2-3GB）
echo "[3/5] 初始化Buildozer（首次运行需下载SDK/NDK，约2-3GB）..."
buildozer init 2>/dev/null || true

# 5. 开始打包
echo "[4/5] 开始打包APK（约15-30分钟）..."
buildozer android debug

echo "[5/5] 打包完成！"
echo "APK位置: $SCRIPT_DIR/bin/*.apk"
echo ""
echo "将APK传到手机安装即可测试"
ls -lh "$SCRIPT_DIR"/bin/*.apk 2>/dev/null || echo "未找到APK，请检查错误日志"
