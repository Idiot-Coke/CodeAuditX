# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

import os
import sys
from pathlib import Path

# 收集所有需要添加的数据文件
datas = []

# 添加所有src下的子目录
for folder in ["core", "parsers", "rules", "ui"]:
    if Path(f"src/{folder}").exists():
        datas.append((f"src/{folder}", folder))

# 添加配置目录
if Path("config").exists():
    datas.append(("config", "config"))

# 项目已迁移到WeasyPrint，不再需要包含wkhtmltopdf.exe

# 隐藏导入
hiddenimports = [
    "src.rules.rulesets",
    "src.parsers.python_parser",
    "src.parsers.c_cpp_parser",
    "src.parsers.javascript_parser",
    "src.parsers.php_parser",
    "src.parsers.go_parser",
    "src.parsers.java_parser",
    "weasyprint",
    "weasyprint.css",
    "weasyprint.css.computed_values",
    "weasyprint.css.properties",
    "weasyprint.css.validation",
    "weasyprint.html",
    "weasyprint.html.clean",
    "weasyprint.html.document",
    "weasyprint.html.html5lib_adapter",
    "weasyprint.layout",
    "weasyprint.layout.backgrounds",
    "weasyprint.layout.boxes",
    "weasyprint.layout.collapsing",
    "weasyprint.layout.context",
    "weasyprint.layout.floats",
    "weasyprint.layout.inlines",
    "weasyprint.layout.page",
    "weasyprint.layout.blocks",
    "weasyprint.presentational_hints",
    "weasyprint.images",
    "weasyprint.text",
    "weasyprint.urls",
    "weasyprint.pdf",
    # 添加GObject相关的隐藏导入
    "gi",
    "gi.repository",
    "gi.repository.GObject",
    "gi.repository.Gio",
    "gi.repository.GLib",
    # 添加WeasyPrint的其他依赖
    "pydyf",
    "cssselect2",
    "html5lib",
    "cairo",
    "cairocffi"
]

# 收集子模块
collect_submodules = [
    "src.rules",
    "src.parsers"
]

# 收集所有内容
collect_all = [
    "src.core"
]

# Windows平台特定配置
def get_gobject_binaries():
    """尝试获取GObject相关的二进制文件"""
    import os
    import sys
    binaries = []
    # 检查常见的GTK/GObject安装路径
    possible_paths = [
        os.path.join(sys.base_prefix, 'Library', 'bin'),
        os.path.join(os.environ.get('ProgramFiles', ''), 'GTK3-Runtime Win64', 'bin'),
        os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'GTK3-Runtime Win32', 'bin')
    ]
    
    # 关键的GObject DLLs
    critical_dlls = [
        'gobject-2.0-0.dll',
        'glib-2.0-0.dll',
        'gmodule-2.0-0.dll',
        'gthread-2.0-0.dll'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            for dll in critical_dlls:
                dll_path = os.path.join(path, dll)
                if os.path.exists(dll_path):
                    binaries.append((dll_path, '.'))
    return binaries

# 获取GObject二进制文件
gobject_binaries = get_gobject_binaries()

a = Analysis(['src/main.py'],
             pathex=[],
             binaries=gobject_binaries,
             datas=datas,
             hiddenimports=hiddenimports,
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=True,  # 使用私有程序集以避免DLL冲突
             cipher=block_cipher,
             noarchive=False)

# 处理收集的子模块
for module in collect_submodules:
    a.pure.extend(Tree(module, prefix=module))

# 处理收集的所有内容
for module in collect_all:
    a.pure.extend(Tree(module, prefix=module))

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

executables = [
    EXE(pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='CodeAuditX',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=['*.dll'],  # 排除DLL文件的UPX压缩，避免加载问题
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None)
]

# 对于Windows，我们只需要EXE文件
coll = COLLECT(executables,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='CodeAuditX')