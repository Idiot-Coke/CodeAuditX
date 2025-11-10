#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from src.ui.main_window import MainWindow

def main():
    # 确保中文显示正常
    os.environ['QT_FONT_DPI'] = '96'  # 设置字体DPI，避免字体过小
    
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