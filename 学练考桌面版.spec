# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\Administrator\\Desktop\\学练考\\学练考桌面版.py'],
    pathex=[],
    binaries=[],
    datas=[('all_expanded_questions.json', '.'), ('study_data.db', '.'), ('quiz_auto_config.json', '.'), ('_shitu_images', '_shitu_images'), ('question_bank.py', '.'), ('question_gen.py', '.'), ('question_shitu_final.py', '.'), ('question_shitu.py', '.'), ('question_shitu_v2.py', '.'), ('question_geo_shitu.py', '.'), ('question_geo_xiangjiao.py', '.'), ('question_exam_real.py', '.'), ('question_hunan_exam.py', '.'), ('question_hunan_bio.py', '.'), ('question_hunan_geo.py', '.'), ('question_hunan_geo_v2.py', '.'), ('question_match.py', '.'), ('quiz_collector.py', '.'), ('image_analyzer.py', '.'), ('ocr_tool.py', '.'), ('analyze_images.py', '.'), ('check_img.py', '.'), ('list_select_img.py', '.')],
    hiddenimports=['pythoncom', 'win32com.client', 'pywintypes', 'question_bank', 'question_gen', 'question_shitu', 'question_shitu_final', 'question_shitu_v2', 'question_geo_shitu', 'question_geo_xiangjiao', 'question_exam_real', 'question_hunan_exam', 'question_hunan_bio', 'question_hunan_geo', 'question_hunan_geo_v2', 'question_match'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='学练考桌面版',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='学练考桌面版',
)
