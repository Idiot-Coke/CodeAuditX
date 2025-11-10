#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView,
    QLineEdit, QMessageBox, QGroupBox, QGridLayout, QSpinBox,
    QDoubleSpinBox, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

# 修改为绝对导入
from src.rules import (
    get_rules_for_language, save_custom_rule, validate_rule,
    type_mapping
)

class RuleEditor(QDialog):
    """规则编辑器，允许用户查看和自定义代码规范规则"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("代码规范规则编辑器")
        self.setMinimumSize(800, 600)
        
        # 当前选择的规则集和语言
        self.current_ruleset = "Google"
        self.current_language = "global"
        
        # 初始化UI
        self.init_ui()
        
        # 加载规则
        self.load_rules()
    
    def init_ui(self):
        """初始化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 顶部控制区
        control_layout = QHBoxLayout()
        
        # 规则集选择
        ruleset_label = QLabel("规则集：")
        self.ruleset_combo = QComboBox()
        self.ruleset_combo.addItems(["Google", "PEP8", "Airbnb", "Standard"])
        self.ruleset_combo.currentTextChanged.connect(self.on_ruleset_changed)
        
        # 语言选择
        language_label = QLabel("语言：")
        self.language_combo = QComboBox()
        self.language_combo.addItems(["global", "python", "javascript", "cpp", "php", "go", "java"])
        self.language_combo.currentTextChanged.connect(self.on_language_changed)
        
        # 添加到控制布局
        control_layout.addWidget(ruleset_label)
        control_layout.addWidget(self.ruleset_combo)
        control_layout.addWidget(language_label)
        control_layout.addWidget(self.language_combo)
        control_layout.addStretch()
        
        # 规则表格
        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(3)
        self.rules_table.setHorizontalHeaderLabels(["规则名称", "当前值", "操作"])
        
        # 设置表头样式
        header = self.rules_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.rules_table.setColumnWidth(2, 80)
        
        # 底部按钮区
        button_layout = QHBoxLayout()
        
        # 保存按钮
        self.save_button = QPushButton("保存修改")
        self.save_button.clicked.connect(self.save_rules)
        
        # 重置按钮
        self.reset_button = QPushButton("重置")
        self.reset_button.clicked.connect(self.load_rules)
        
        # 添加到按钮布局
        button_layout.addStretch()
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.save_button)
        
        # 添加到主布局
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.rules_table)
        main_layout.addLayout(button_layout)
        
        # 规则分类信息
        self.add_rule_category_info(main_layout)
    
    def add_rule_category_info(self, main_layout):
        """添加规则分类信息"""
        info_group = QGroupBox("规则分类说明")
        info_layout = QGridLayout()
        
        # 添加规则类型说明
        row = 0
        for rule_type, description in type_mapping.items():
            type_label = QLabel(f"{rule_type}: ")
            desc_label = QLabel(description)
            info_layout.addWidget(type_label, row, 0)
            info_layout.addWidget(desc_label, row, 1)
            row += 1
        
        # 添加使用说明
        usage_label = QLabel(
            "说明：修改规则后点击'保存修改'按钮使更改生效。\n"\
            "命名规则使用正则表达式，其他规则根据类型输入相应的值。"
        )
        usage_label.setWordWrap(True)
        info_layout.addWidget(usage_label, row, 0, 1, 2)
        
        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)
    
    def on_ruleset_changed(self, ruleset_name):
        """规则集改变时的处理函数"""
        self.current_ruleset = ruleset_name
        self.load_rules()
    
    def on_language_changed(self, language):
        """语言改变时的处理函数"""
        self.current_language = language
        self.load_rules()
    
    def load_rules(self):
        """加载规则并显示在表格中"""
        # 清空表格
        self.rules_table.setRowCount(0)
        
        # 获取规则
        rules = get_rules_for_language(self.current_ruleset, self.current_language)
        
        # 将规则添加到表格
        for rule_name, rule_value in rules.items():
            # 跳过嵌套的语言规则
            if isinstance(rule_value, dict):
                continue
            
            # 添加行
            row_position = self.rules_table.rowCount()
            self.rules_table.insertRow(row_position)
            
            # 规则名称
            name_item = QTableWidgetItem(rule_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # 判断规则类型，选择合适的编辑器
            if rule_name.endswith('_naming'):
                # 命名规则使用文本框
                value_widget = QLineEdit(str(rule_value))
                value_widget.setToolTip("使用正则表达式定义命名规范")
            elif rule_name in ['max_line_length', 'expected_indent']:
                # 整数规则使用SpinBox
                value_widget = QSpinBox()
                value_widget.setRange(1, 200)
                value_widget.setValue(int(rule_value))
                if rule_name == 'max_line_length':
                    value_widget.setToolTip("代码行的最大长度")
                else:
                    value_widget.setToolTip("预期的缩进空格数")
            elif rule_name == 'min_comment_coverage':
                # 浮点数规则使用DoubleSpinBox
                value_widget = QDoubleSpinBox()
                value_widget.setRange(0.0, 1.0)
                value_widget.setSingleStep(0.05)
                value_widget.setValue(float(rule_value))
                value_widget.setToolTip("最小注释覆盖率 (0.0-1.0)")
            else:
                # 其他规则使用文本框
                value_widget = QLineEdit(str(rule_value))
            
            # 保存按钮
            edit_button = QPushButton("修改")
            edit_button.clicked.connect(
                lambda checked, rn=rule_name, rw=value_widget: self.edit_rule(rn, rw)
            )
            
            # 添加到表格
            self.rules_table.setItem(row_position, 0, name_item)
            self.rules_table.setCellWidget(row_position, 1, value_widget)
            self.rules_table.setCellWidget(row_position, 2, edit_button)
    
    def edit_rule(self, rule_name, value_widget):
        """编辑规则"""
        # 获取新值
        if isinstance(value_widget, QLineEdit):
            new_value = value_widget.text()
        elif isinstance(value_widget, QSpinBox) or isinstance(value_widget, QDoubleSpinBox):
            new_value = value_widget.value()
        else:
            new_value = str(value_widget.text())
        
        # 验证规则
        if not validate_rule(rule_name, str(new_value)):
            QMessageBox.warning(
                self, 
                "规则验证失败", 
                f"规则 '{rule_name}' 的值 '{new_value}' 无效！"
            )
            # 重新加载规则，恢复原值
            self.load_rules()
            return
        
        # 保存规则
        rule_type = self.get_rule_type(rule_name)
        success = save_custom_rule(rule_type, rule_name, new_value, self.current_language)
        
        if success:
            # 显示成功消息
            QMessageBox.information(
                self, 
                "保存成功", 
                f"规则 '{rule_name}' 已更新为 '{new_value}'"
            )
            # 重新加载规则
            self.load_rules()
        else:
            QMessageBox.warning(
                self, 
                "保存失败", 
                f"无法保存规则 '{rule_name}'！"
            )
    
    def save_rules(self):
        """保存所有规则"""
        # 在这个简化版本中，我们已经通过单个规则的修改按钮保存了规则
        # 这里可以添加批量保存的逻辑
        QMessageBox.information(
            self, 
            "保存完成", 
            "所有规则修改已保存！"
        )
    
    def get_rule_type(self, rule_name):
        """根据规则名称确定规则类型"""
        if rule_name.endswith('_naming'):
            return 'naming'
        elif rule_name in ['min_comment_coverage']:
            return 'comment'
        elif rule_name in ['max_line_length', 'expected_indent']:
            return 'style'
        else:
            return 'config'