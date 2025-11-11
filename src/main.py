#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import platform

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# macOS特定的初始化设置，解决资源加载和NSImage断言问题
if platform.system() == 'Darwin':
    # 重要：在导入PyQt5之前设置环境变量
    # 这些环境变量必须在Qt初始化之前设置才有效
    os.environ['QT_MAC_WANTS_LAYER'] = '1'
    os.environ['QT_SCALE_FACTOR_ROUNDING_POLICY'] = 'PassThrough'
    os.environ['QT_MAC_DISABLE_FOREGROUND_APPLICATION_TRANSFORM'] = '1'
    # 禁用高DPI缩放以提高兼容性
    os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '0'
    # 额外安全设置，防止bundle路径问题
    os.environ['QT_MAC_USE_NATIVE_MENUBAR'] = '0'
    
    # 对于打包的应用，需要确保正确设置bundle路径和环境
    # 检查是否是冻结应用（PyInstaller打包后的应用）
    if getattr(sys, 'frozen', False):
        # 获取应用程序路径
        app_path = sys.executable
        
        # 确定应用程序目录，为资源查找提供基础
        app_dir = os.path.dirname(app_path)
        
        # 确保库路径正确设置
        if 'DYLD_LIBRARY_PATH' in os.environ:
            # 添加应用程序目录到库路径
            os.environ['DYLD_LIBRARY_PATH'] = app_dir + ':' + os.environ['DYLD_LIBRARY_PATH']
        else:
            os.environ['DYLD_LIBRARY_PATH'] = app_dir
        
        # 对于.app包，特殊处理
        if '.app/' in app_path:
            # 提取.app目录
            bundle_dir = app_path.split('.app/')[0] + '.app'
            # 确保Resources目录存在于环境路径中
            resources_dir = os.path.join(bundle_dir, 'Contents', 'Resources')
            if os.path.exists(resources_dir):
                # 添加Resources目录到Python路径
                sys.path.insert(0, resources_dir)
        
    # 尝试使用PyObjC设置bundle，这是可选的，但可以帮助解决某些问题
    pyobjc_available = False
    try:
        import Foundation
        import AppKit
        pyobjc_available = True
        
        # 尝试创建一个临时bundle来避免NSImage断言失败
        # 这是一种安全措施，确保即使在bundle路径无效的情况下也能运行
        try:
            # 获取当前可执行文件目录
            exec_dir = os.path.dirname(os.path.abspath(sys.executable))
            # 创建一个基于当前目录的bundle
            temp_bundle = Foundation.NSBundle.bundleWithPath_(exec_dir)
            if temp_bundle:
                # 设置为主要bundle
                Foundation.NSBundle.setMainBundle_(temp_bundle)
        except Exception:
            # 忽略bundle设置错误，继续运行
            pass
            
        # 尝试禁用NSImage的系统图标加载，防止断言失败
        # 使用异常处理包装所有NSImage相关操作
        try:
            # 预先初始化NSImage系统
            _ = AppKit.NSImage.alloc().init()
        except Exception:
            pass
            
    except ImportError:
        # PyObjC未安装，这在某些环境中是正常的
        print("警告: PyObjC未安装，某些macOS特定功能可能受限，但应用仍可运行")
    
    # 对于打包应用，确保Qt插件路径正确
    if getattr(sys, 'frozen', False):
        # 设置Qt插件路径指向应用程序目录
        qt_plugin_path = os.path.join(os.path.dirname(sys.executable), 'Qt', 'plugins')
        if os.path.exists(qt_plugin_path):
            os.environ['QT_PLUGIN_PATH'] = qt_plugin_path
        else:
            # 如果找不到Qt/plugins目录，使用应用程序目录
            os.environ['QT_PLUGIN_PATH'] = os.path.dirname(sys.executable)

from PyQt5.QtWidgets import QApplication
from src.ui.main_window import MainWindow

def main():
    # 确保中文显示正常
    os.environ['QT_FONT_DPI'] = '96'  # 设置字体DPI，避免字体过小
    
    # 注意：macOS特定设置已在文件顶部导入PyQt5前设置
    # 避免在Qt初始化后设置环境变量导致的问题
    
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle('Fusion')  # 使用Fusion样式，跨平台一致性更好
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())

if __name__ == '__main__':
    main()