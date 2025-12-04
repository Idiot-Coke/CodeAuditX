# -*- mode: python ; coding: utf-8 -*-
"""
CodeAuditX Linux ARM64打包配置文件
"""

import os
import sys
import platform

# 设置基本参数
block_cipher = None

# 定义要包含的资源文件
a_add_data = [
    ('config/custom_rules.json', 'config'),
    ('src/ui', 'src/ui'),
    ('src/rules', 'src/rules'),
]

# 隐藏导入列表
hidden_imports = [
    "PyQt5",
    "PyQt5.QtCore",
    "PyQt5.QtGui",
    "PyQt5.QtWidgets",
    "PyQt5.QtPrintSupport",
    "PyQt5.QtSvg",
    "esprima",
    "jsonschema",
    "weasyprint",
    "weasyprint.urls",
    "weasyprint.pdf",
    # 额外的WeasyPrint依赖
    "pydyf",
    "tinycss2",
    "cssselect2",
    "html5lib",
    "cairocffi",
    # 其他可能需要的隐藏导入
    "collections.abc",
    "importlib.resources",
    "importlib.metadata",
]

# Linux ARM架构特定配置
arch = "arm64"

# 创建分析对象
a = Analysis(['src/main.py'],
             pathex=['/Users/zhangke/Desktop/CodeAuditX-Trae'],
             binaries=[],
             datas=a_add_data,
             hiddenimports=hidden_imports,
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

# 创建PYZ对象
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 创建EXE对象
executable_name = f"CodeAuditX_{arch}"

# Linux ARM特定的EXE配置
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name=executable_name,
          debug=False,
          bootloader_ignore_signals=False,
          strip=True,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=False,
          target_arch=arch,
          codesign_identity=None,
          entitlements_file=None)

# 创建最终的DIST文件夹
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=True,
               upx=True,
               upx_exclude=[],
               name=f"CodeAuditX_{arch}")