#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
开源协议扫描结果显示窗口
"""

import os
import json
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QMessageBox, QGroupBox, QGridLayout, QProgressBar,
    QFileDialog, QAction, QMenu, QTreeWidget, QTreeWidgetItem, QSplitter
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QFont

from src.core.license_scanner import LicenseScanner


class LicenseScanThread(QThread):
    """协议扫描线程"""
    progress_updated = pyqtSignal(int)
    scan_completed = pyqtSignal(dict)
    scan_failed = pyqtSignal(str)
    
    def __init__(self, directory_path):
        super().__init__()
        self.directory_path = directory_path
    
    def run(self):
        try:
            scanner = LicenseScanner()
            # 先计算总文件数用于进度显示
            total_files = 0
            for root, _, files in os.walk(self.directory_path):
                total_files += len([f for f in files if not f.startswith('.')])
            
            # 定义进度回调函数
            processed_files = 0
            
            def progress_callback():
                nonlocal processed_files
                processed_files += 1
                progress = int((processed_files / total_files) * 100) if total_files > 0 else 0
                self.progress_updated.emit(progress)
            
            # 扫描目录
            results = scanner.scan_directory(self.directory_path)
            self.scan_completed.emit(results)
        except Exception as e:
            self.scan_failed.emit(str(e))


class LicenseWindow(QDialog):
    """开源协议扫描窗口"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("开源协议扫描")
        self.setGeometry(100, 100, 1200, 700)
        self.results = None
        # 加载许可证描述信息
        self.license_descriptions = self._load_license_descriptions()
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        
        # 顶部控制面板
        control_layout = QHBoxLayout()
        
        self.scan_button = QPushButton("扫描目录")
        self.scan_button.clicked.connect(self.start_scan)
        control_layout.addWidget(self.scan_button)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)
        
        control_layout.addStretch()
        main_layout.addLayout(control_layout)
        
        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧风险统计面板
        stats_group = QGroupBox("风险统计")
        stats_layout = QGridLayout()
        
        self.high_risk_label = QLabel("高风险: 0")
        self.high_risk_label.setStyleSheet("color: #e74c3c; font-weight: bold")
        self.medium_risk_label = QLabel("中风险: 0")
        self.medium_risk_label.setStyleSheet("color: #f39c12; font-weight: bold")
        self.low_risk_label = QLabel("低风险: 0")
        self.low_risk_label.setStyleSheet("color: #2ecc71; font-weight: bold")
        self.total_files_label = QLabel("总文件数: 0")
        self.total_licenses_label = QLabel("发现协议数: 0")
        
        stats_layout.addWidget(self.high_risk_label, 0, 0)
        stats_layout.addWidget(self.medium_risk_label, 1, 0)
        stats_layout.addWidget(self.low_risk_label, 2, 0)
        stats_layout.addWidget(self.total_files_label, 3, 0)
        stats_layout.addWidget(self.total_licenses_label, 4, 0)
        
        stats_group.setLayout(stats_layout)
        splitter.addWidget(stats_group)
        
        # 中间协议分布树
        licenses_group = QGroupBox("协议分布")
        licenses_layout = QVBoxLayout()
        
        self.licenses_tree = QTreeWidget()
        self.licenses_tree.setHeaderLabels(["协议名称", "风险级别", "文件数"])
        self.licenses_tree.header().setSectionResizeMode(QHeaderView.Stretch)
        
        licenses_layout.addWidget(self.licenses_tree)
        licenses_group.setLayout(licenses_layout)
        splitter.addWidget(licenses_group)
        
        # 右侧详细表格
        details_group = QGroupBox("文件详细信息")
        details_layout = QVBoxLayout()
        
        self.details_table = QTableWidget()
        self.details_table.setColumnCount(4)
        self.details_table.setHorizontalHeaderLabels(["文件路径", "检测到的协议", "协议描述", "风险级别"])
        self.details_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.details_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.details_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.details_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Interactive)
        
        details_layout.addWidget(self.details_table)
        details_group.setLayout(details_layout)
        splitter.addWidget(details_group)
        
        # 设置分割器比例
        splitter.setSizes([200, 300, 700])
        main_layout.addWidget(splitter, 1)
        
        # 添加高风险协议说明
        warning_label = QLabel(
            '''<html><body>
            <p style='color: #e74c3c;'>⚠️ <strong>高风险协议说明:</strong></p>
            <ul>
                <li><strong>GPL系列协议</strong>: 要求衍生作品也必须使用相同的开源协议</li>
                <li><strong>LGPL系列协议</strong>: 较GPL宽松，但仍有传播要求</li>
                <li><strong>AGPL协议</strong>: GPL的网络版，要求通过网络访问的软件也要开源</li>
            </ul>
            </body></html>'''
        )
        warning_label.setWordWrap(True)
        main_layout.addWidget(warning_label)
    
    def start_scan(self):
        """开始扫描目录"""
        directory_path = QFileDialog.getExistingDirectory(self, "选择扫描目录")
        if not directory_path:
            return
        
        # 禁用扫描按钮，显示进度条
        self.scan_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 清空现有数据
        self.details_table.setRowCount(0)
        self.licenses_tree.clear()
        
        # 创建扫描线程
        self.scan_thread = LicenseScanThread(directory_path)
        self.scan_thread.progress_updated.connect(self.update_progress)
        self.scan_thread.scan_completed.connect(self.on_scan_completed)
        self.scan_thread.scan_failed.connect(self.on_scan_failed)
        self.scan_thread.start()
    
    def update_progress(self, progress):
        """更新进度条"""
        self.progress_bar.setValue(progress)
    
    def on_scan_completed(self, results):
        """扫描完成处理"""
        self.results = results
        self.scan_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # 更新统计信息
        self.update_stats()
        
        # 更新协议分布树
        self.update_licenses_tree()
        
        # 更新详细表格
        self.update_details_table()
        
        QMessageBox.information(self, "扫描完成", f"扫描完成！共发现 {len(results['licenses_by_file'])} 个包含开源协议的文件")
    
    def on_scan_failed(self, error_msg):
        """扫描失败处理"""
        self.scan_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "扫描失败", f"扫描过程中出现错误：{error_msg}")
    
    def update_stats(self):
        """更新统计信息"""
        if not self.results:
            return
        
        risk_summary = self.results['risk_summary']
        
        self.high_risk_label.setText(f"高风险: {risk_summary['high']}")
        self.medium_risk_label.setText(f"中风险: {risk_summary['medium']}")
        self.low_risk_label.setText(f"低风险: {risk_summary['low']}")
        self.total_files_label.setText(f"总文件数: {len(self.results['licenses_by_file'])}")
        self.total_licenses_label.setText(f"发现协议数: {len(self.results['licenses_summary'])}")
    
    def update_licenses_tree(self):
        """更新协议分布树"""
        if not self.results:
            return
        
        # 按风险级别分组
        risk_groups = {'high': [], 'medium': [], 'low': []}
        scanner = LicenseScanner()
        
        for license_name, count in self.results['licenses_summary'].items():
            risk_level = scanner._get_license_risk(license_name)
            risk_groups[risk_level].append((license_name, count, risk_level))
        
        # 创建风险级别节点
        risk_names = {'high': '高风险协议', 'medium': '中风险协议', 'low': '低风险协议'}
        risk_colors = {'high': QColor('#e74c3c'), 'medium': QColor('#f39c12'), 'low': QColor('#2ecc71')}
        
        for risk_level, licenses in risk_groups.items():
            if licenses:
                group_item = QTreeWidgetItem([risk_names[risk_level], '', ''])
                group_item.setForeground(0, risk_colors[risk_level])
                font = group_item.font(0)
                font.setBold(True)
                group_item.setFont(0, font)
                
                # 添加协议子节点
                for license_name, count, risk in sorted(licenses):
                    item = QTreeWidgetItem([license_name, risk_names[risk], str(count)])
                    item.setForeground(1, risk_colors[risk])
                    group_item.addChild(item)
                
                self.licenses_tree.addTopLevelItem(group_item)
                group_item.setExpanded(True)
    
    def update_details_table(self):
        """更新详细表格"""
        if not self.results:
            return
        
        scanner = LicenseScanner()
        risk_names = {'high': '高风险', 'medium': '中风险', 'low': '低风险'}
        risk_colors = {'high': QColor('#e74c3c'), 'medium': QColor('#f39c12'), 'low': QColor('#2ecc71')}
        
        # 填充表格
        for row, (file_path, licenses) in enumerate(self.results['licenses_by_file'].items()):
            self.details_table.insertRow(row)
            
            # 文件路径
            item_path = QTableWidgetItem(file_path)
            self.details_table.setItem(row, 0, item_path)
            
            # 协议列表
            licenses_text = ', '.join(licenses)
            item_licenses = QTableWidgetItem(licenses_text)
            self.details_table.setItem(row, 1, item_licenses)
            
            # 协议描述（使用第一个协议的描述）
            if licenses:
                first_license = licenses[0]
                description = self.license_descriptions.get(first_license, {}).get("description", "未知许可证")
            else:
                description = "无许可证"
            item_description = QTableWidgetItem(description)
            self.details_table.setItem(row, 2, item_description)
            
            # 风险级别（显示最高风险级别）
            risk_levels = [scanner._get_license_risk(l) for l in licenses]
            max_risk = 'low'
            if 'high' in risk_levels:
                max_risk = 'high'
            elif 'medium' in risk_levels:
                max_risk = 'medium'
            
            item_risk = QTableWidgetItem(risk_names[max_risk])
            item_risk.setForeground(risk_colors[max_risk])
            font = item_risk.font()
            font.setBold(True)
            item_risk.setFont(font)
            self.details_table.setItem(row, 3, item_risk)
        
        # 自动调整列宽
        self.details_table.resizeColumnsToContents()
        
    def _load_license_descriptions(self):
        """加载许可证描述信息"""
        descriptions = {}
        # 获取配置文件路径
        config_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = os.path.join(config_dir, "src", "core", "config", "license_rules.json")
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    for license_info in config.get("license_patterns", []):
                        descriptions[license_info["name"]] = {
                            "description": license_info["description"],
                            "risk_level": license_info["risk_level"]
                        }
        except Exception as e:
            print(f"加载许可证描述信息失败: {e}")
        
        # 添加默认描述
        default_descriptions = {
            "MIT": {"description": "MIT许可证是一种宽松的许可证，允许在几乎任何条件下使用、修改和分发代码", "risk_level": "low"},
            "Apache-2.0": {"description": "Apache许可证包含专利条款，提供专利保护，同时保持商业友好性", "risk_level": "low"},
            "GPL-3.0": {"description": "GNU通用公共许可证要求衍生作品也必须在GPL下发布（病毒式传播）", "risk_level": "high"},
            "LGPL-3.0": {"description": "GNU宽通用公共许可证允许将库与非LGPL软件链接，限制较少", "risk_level": "medium"},
            "BSD-3-Clause": {"description": "BSD许可证是宽松的许可证，类似于MIT但有特定条款", "risk_level": "low"},
            "MPL-2.0": {"description": "Mozilla公共许可证要求修改后的文件在MPL下发布，但允许与专有代码链接", "risk_level": "medium"}
        }
        
        # 合并默认描述和从配置文件加载的描述
        for license_name, info in default_descriptions.items():
            if license_name not in descriptions:
                descriptions[license_name] = info
        
        return descriptions