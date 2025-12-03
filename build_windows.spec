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
    "cssutils",
    # 系统性能监控依赖
    "psutil"
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
    """收集GTK3 DLLs，支持多种安装方式（Chocolatey、标准安装、conda）"""
    import os
    import sys
    import subprocess
    
    binaries = []
    
    # 关键的GTK/GObject DLLs列表
    critical_dlls = [
        'gobject-2.0-0.dll',
        'glib-2.0-0.dll',
        'gmodule-2.0-0.dll',
        'gthread-2.0-0.dll',
        'cairo-2.dll',
        'cairo-gobject-2.dll',
        'pango-1.0-0.dll',
        'pangocairo-1.0-0.dll',
        'pangoft2-1.0-0.dll',
        'pangowin32-1.0-0.dll',
        'harfbuzz.dll',
        'gdk-3-0.dll',
        'gdk_pixbuf-2.0-0.dll',
        'gtk-3-0.dll',
        'freetype6.dll',
        'libpng16-16.dll',
        'zlib1.dll',
        'libxml2-2.dll',
        'libxslt-1.dll'
    ]
    
    # 尝试多种可能的GTK3安装路径
    # 1. Chocolatey安装路径
    chocolatey_paths = [
        os.path.join(os.environ.get("ProgramData", ""), "chocolatey", "lib", "gtk-runtime", "tools", "bin"),
        os.path.join(os.environ.get("ChocolateyInstall", ""), "lib", "gtk-runtime", "tools", "bin")
    ]
    
    # 2. 标准Windows安装路径
    standard_paths = [
        "C:\\Program Files\\GTK3-Runtime Win64\\bin",
        "C:\\Program Files (x86)\\GTK3-Runtime Win32\\bin"
    ]
    
    # 3. Conda/Anaconda路径
    conda_paths = [
        os.path.join(sys.base_prefix, "Library", "bin")
    ]
    
    # 4. 环境变量中的路径
    env_paths = os.environ.get("PATH", "").split(os.pathsep)
    
    # 合并所有可能的路径
    all_paths = chocolatey_paths + standard_paths + conda_paths + env_paths
    
    # 去重并检查路径是否存在
    unique_paths = []
    for path in all_paths:
        if path and path not in unique_paths and os.path.exists(path) and os.path.isdir(path):
            unique_paths.append(path)
    
    # 收集DLLs
    for path in unique_paths:
        print(f"检查GTK3 DLLs在: {path}")
        found_in_path = 0
        for dll in critical_dlls:
            dll_path = os.path.join(path, dll)
            if os.path.exists(dll_path):
                binaries.append((dll_path, '.'))
                found_in_path += 1
        if found_in_path > 0:
            print(f"  在该路径找到 {found_in_path} 个DLLs")
    
    # 如果找到DLLs，直接返回
    if binaries:
        print(f"总计找到 {len(binaries)} 个GTK/GObject相关DLLs")
        return binaries
    
    # 如果没有找到任何DLLs，尝试搜索整个系统
    print("在所有已知路径中未找到GTK3 DLLs，尝试在系统中搜索...")
    try:
        # 使用where命令查找DLLs
        for dll in critical_dlls:
            try:
                result = subprocess.run(["where", dll], capture_output=True, text=True, check=True)
                for line in result.stdout.strip().split('\n'):
                    if line and os.path.exists(line):
                        binaries.append((line, '.'))
                        print(f"  找到: {line}")
            except:
                pass
    except:
        pass
    
    print(f"最终找到 {len(binaries)} 个GTK/GObject相关DLLs")
    return binaries

# 获取GObject二进制文件
gobject_binaries = get_gobject_binaries()

a = Analysis(['src/main.py'],
             pathex=[],
             binaries=gobject_binaries,
             datas=datas,
             hiddenimports=hiddenimports,
             hookspath=['hooks'],  # 使用自定义钩子目录
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