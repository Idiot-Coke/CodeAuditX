# -*- coding: utf-8 -*-
"""
PyInstaller钩子文件，用于处理gi.repository.GObject依赖
"""

from PyInstaller.utils.hooks import get_gi_typelibs
import os

# 获取GObject的typelibs
typlibs = get_gi_typelibs('GObject')

data = []

def find_gtk_dlls():
    """查找GTK3 DLLs"""
    import sys
    import subprocess
    
    # 尝试查找GTK3的安装路径
    possible_paths = [
        # GitHub Actions环境下的GTK3安装路径
        "C:\\Program Files\\GTK3-Runtime Win64\\bin",
        "C:\\Program Files (x86)\\GTK3-Runtime Win32\\bin",
        # Anaconda/Miniconda路径
        os.path.join(sys.base_prefix, "Library", "bin"),
        # Chocolatey安装路径
        os.path.join(os.environ.get("ProgramData", ""), "chocolatey", "lib", "gtk-runtime", "tools", "bin")
    ]
    
    # 关键DLLs
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
    
    found_dlls = []
    
    for path in possible_paths:
        if os.path.exists(path) and os.path.isdir(path):
            for dll in critical_dlls:
                dll_path = os.path.join(path, dll)
                if os.path.exists(dll_path):
                    found_dlls.append((dll_path, '.'))
    
    return found_dlls

# 查找并添加GTK3 DLLs
data.extend(find_gtk_dlls())

# 导出数据
datas = data
binaries = data
hiddenimports = [
    'gi.repository.GObject',
    'gi.repository.Cairo',
    'gi.repository.Pango',
    'gi.repository.PangoCairo',
    'gi.repository.GdkPixbuf',
    'gi.repository.Gdk',
    'cairosvg',
    'fontTools',
    'PIL'
]