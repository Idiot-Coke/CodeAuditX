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
    """直接使用已知的GTK3 DLL路径，确保PyInstaller能够找到它们"""
    import os
    import sys
    import subprocess
    
    binaries = []
    
    # 直接指定GTK3运行时的DLL路径
    # 这些路径是基于GitHub Actions环境和标准Windows安装路径
    gtk_paths = [
        "C:\\Program Files\\GTK3-Runtime Win64\\bin",
        "C:\\Program Files (x86)\\GTK3-Runtime Win32\\bin",
        os.path.join(sys.base_prefix, "Library", "bin")
    ]
    
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
    
    # 首先尝试直接添加已知路径的DLLs
    for path in gtk_paths:
        for dll in critical_dlls:
            dll_path = os.path.join(path, dll)
            if os.path.exists(dll_path):
                binaries.append((dll_path, '.'))
    
    # 如果没有找到任何DLLs，尝试从GitHub下载并解压
    if not binaries:
        print("没有找到GTK3 DLLs，尝试下载...")
        import zipfile
        import tempfile
        
        # 下载GTK3 DLLs
        gtk_url = "https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases/download/2023-12-29/gtk3-runtime-3.24.37-2023-12-29-ts-win64.exe"
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            gtk_exe = os.path.join(temp_dir, "gtk3-runtime.exe")
            
            # 下载GTK3运行时安装包
            import urllib.request
            urllib.request.urlretrieve(gtk_url, gtk_exe)
            
            # 解压安装包中的DLLs（使用7zip，如果可用）
            if os.path.exists(gtk_exe):
                print("下载成功，尝试解压...")
                
                # 检查是否安装了7zip
                try:
                    subprocess.run(["7z", "x", gtk_exe, "-o" + temp_dir, "*.dll"], check=True, capture_output=True)
                    
                    # 查找解压后的DLLs
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            if file.lower().endswith(".dll") and file in critical_dlls:
                                dll_path = os.path.join(root, file)
                                binaries.append((dll_path, '.'))
                except:
                    print("无法解压GTK3运行时，跳过...")
    
    print(f"找到{len(binaries)}个GTK/GObject相关DLLs")
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