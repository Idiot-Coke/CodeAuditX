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
    # 增强GObject相关的隐藏导入
    "gi",
    "gi.repository",
    "gi.repository.GObject",
    "gi.repository.Gio",
    "gi.repository.GLib",
    "gi.repository.Cairo",
    "gi.repository.Pango",
    "gi.repository.PangoCairo",
    "gi.repository.GdkPixbuf",
    "gi.repository.Gdk",
    # 添加WeasyPrint的其他依赖
    "pydyf",
    "cssselect2",
    "html5lib",
    "cairo",
    "cairocffi",
    "cairosvg",
    "fontTools",
    "PIL",
    "tinycss2",
    "webencodings",
    "lxml",
    "cssutils"
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
    import subprocess
    
    binaries = []
    # 关键的GTK/GObject DLLs列表，包含更多必要的依赖
    critical_dlls = [
        # GObject核心DLLs
        'gobject-2.0-0.dll',
        'glib-2.0-0.dll',
        'gmodule-2.0-0.dll',
        'gthread-2.0-0.dll',
        # Cairo相关DLLs
        'cairo-2.dll',
        'cairo-gobject-2.dll',
        # Pango相关DLLs
        'pango-1.0-0.dll',
        'pangocairo-1.0-0.dll',
        'pangoft2-1.0-0.dll',
        'pangowin32-1.0-0.dll',
        # Harfbuzz相关DLLs
        'harfbuzz.dll',
        # GTK3相关DLLs
        'gdk-3-0.dll',
        'gdk_pixbuf-2.0-0.dll',
        'gtk-3-0.dll',
        # 其他必要的依赖
        'freetype6.dll',
        'libpng16-16.dll',
        'zlib1.dll',
        'libxml2-2.dll',
        'libxslt-1.dll'
    ]
    
    # 检查常见的GTK/GObject安装路径
    possible_paths = [
        # Anaconda/Miniconda安装路径
        os.path.join(sys.base_prefix, 'Library', 'bin'),
        # 标准GTK3安装路径
        os.path.join(os.environ.get('ProgramFiles', ''), 'GTK3-Runtime Win64', 'bin'),
        os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'GTK3-Runtime Win32', 'bin'),
        # Chocolatey安装路径
        os.path.join(os.environ.get('ProgramData', ''), 'chocolatey', 'lib', 'gtk-runtime', 'tools', 'bin'),
        # 环境变量中的PATH路径
        *os.environ.get('PATH', '').split(';')
    ]
    
    # 去重并过滤存在的路径
    possible_paths = list(set([path for path in possible_paths if os.path.exists(path) and os.path.isdir(path)]))
    
    # 遍历所有可能的路径，查找关键DLLs
    for path in possible_paths:
        for dll in critical_dlls:
            dll_path = os.path.join(path, dll)
            if os.path.exists(dll_path) and (dll_path, '.') not in binaries:
                binaries.append((dll_path, '.'))
    
    # 如果没有找到足够的DLLs，尝试使用where命令查找
    if len(binaries) < len(critical_dlls) // 2:
        print("尝试使用where命令查找DLLs...")
        for dll in critical_dlls:
            try:
                result = subprocess.run(['where', dll], capture_output=True, text=True, check=True)
                if result.stdout.strip():
                    dll_path = result.stdout.strip().split('\n')[0]
                    if (dll_path, '.') not in binaries:
                        binaries.append((dll_path, '.'))
            except subprocess.CalledProcessError:
                continue
    
    print(f"找到{len(binaries)}个GTK/GObject相关DLLs")
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