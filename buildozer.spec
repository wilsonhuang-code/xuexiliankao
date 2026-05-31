[app]
# 应用名称
title = 自适应学练考系统

# 包名（必须是唯一标识符）
package.name = com.example.xuexiliankao

# 包域名
package.domain = org.example

# 源代码目录
source.dir = .

# 源代码需要包含的文件
source.include_exts = py,png,jpg,kv,atlas,json,txt,md

# 应用版本
version = 1.0

# 配置文件版本
version.code = 1

# 应用要求
requirements = python3,kivy,json

# 图标（可选）
#icon.filename = %(source.dir)s/icon.png

# 启动图片（可选）
#presplash.filename = %(source.dir)s/presplash.png

# 支持的方向
orientation = portrait

# Android API 版本
android.api = 31

# 最低 Android 版本
android.minapi = 21

# 目标 Android 版本
android.targetapi = 31

# 屏幕兼容性
android.allow_backup = True

# 权限
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# 功能
android.features = 

# 全屏
fullscreen = 0

# 保持屏幕常亮
wake_lock = False

# 启动器
presplash.color = #FFFFFF

# 主题颜色
android.gradle_dependencies = 

#  AAR 依赖
android.armeabi_v7a = True
android.arm64_v8a = True
android.x86 = False
android.x86_64 = False

#  Python 优化
python.for_androide = True

# 应用配置
[app:test]
title = 自适应学练考系统测试版

[app:release]
title = 自适应学练考系统正式版
