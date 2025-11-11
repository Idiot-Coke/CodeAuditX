import os
import sys
import time
import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QTableWidget, QTableWidgetItem, QTabWidget,
    QTextEdit, QComboBox, QProgressBar, QSplitter, QMessageBox, QHeaderView,
    QAction
)
from src.ui.license_window import LicenseWindow
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QFont

# 修改为绝对导入
from src.core.scanner import CodeScanner
from src.core.report_generator import ReportGenerator
from src.core.config_manager import ConfigManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("代码规范扫描工具")
        self.setGeometry(100, 100, 1200, 800)
        
        # 设置字体
        self.setup_font()
        
        # 配置管理
        self.config_manager = ConfigManager()
        self.load_config_settings()
        
        # 初始化UI
        self.init_ui()
        
        # 扫描器实例
        self.scanner = None
        self.scanner_thread = None
        self.last_scan_results = None
        
    def setup_font(self):
        """设置应用程序字体"""
        font = QFont()
        font.setFamily("Arial")
        font.setPointSize(12)  # 增大字体大小
        self.setFont(font)
    
    def load_config_settings(self):
        """加载配置设置"""
        # 可以在这里加载默认配置
        pass
    
    def init_ui(self):
        """初始化用户界面"""
        # 设置菜单栏
        self.setup_menu()
        
        # 确保MacOS上菜单栏正确显示
        if sys.platform == 'darwin':
            self.menuBar().setNativeMenuBar(False)
        
        # 主布局
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # 项目路径选择区域
        path_widget = QWidget()
        path_layout = QHBoxLayout(path_widget)
        
        path_label = QLabel("项目路径：")
        self.path_input = QLabel("未选择项目")
        self.path_input.setStyleSheet("background-color: #f0f0f0; padding: 5px;")
        self.path_input.setMinimumWidth(400)
        
        browse_button = QPushButton("浏览")
        browse_button.clicked.connect(self.browse_directory)
        browse_button.setFixedWidth(100)  # 增大按钮宽度
        
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_button)
        
        # 配置区域
        config_widget = QWidget()
        config_layout = QHBoxLayout(config_widget)
        
        # 规范标准选择
        standard_label = QLabel("规范标准：")
        self.standard_combo = QComboBox()
        self.standard_combo.addItems(["PEP 8", "Google", "Airbnb", "Standard", "自定义"])
        self.standard_combo.setCurrentText(self.config_manager.get("scanner.standard", "PEP 8"))
        
        # 排除目录输入
        exclude_label = QLabel("排除目录：")
        self.exclude_input = QTextEdit()
        self.exclude_input.setPlaceholderText("例如：venv,__pycache__,node_modules")
        self.exclude_input.setMaximumHeight(60)
        # 修复：将列表转换为逗号分隔的字符串
        exclude_dirs = self.config_manager.get("scanner.exclude_dirs", ["venv", "__pycache__", "node_modules"])
        if isinstance(exclude_dirs, list):
            exclude_dirs_str = ",".join(exclude_dirs)
        else:
            exclude_dirs_str = str(exclude_dirs)
        self.exclude_input.setPlainText(exclude_dirs_str)
        
        # 扫描按钮
        self.scan_button = QPushButton("扫描")
        self.scan_button.clicked.connect(self.start_scan)
        self.scan_button.setFixedWidth(100)  # 增大按钮宽度
        
        # 暂停按钮
        self.pause_button = QPushButton("暂停")
        self.pause_button.clicked.connect(self.pause_scan)
        self.pause_button.setFixedWidth(100)  # 增大按钮宽度
        self.pause_button.setEnabled(False)
        
        # 恢复按钮
        self.resume_button = QPushButton("恢复")
        self.resume_button.clicked.connect(self.resume_scan)
        self.resume_button.setFixedWidth(100)  # 增大按钮宽度
        self.resume_button.setEnabled(False)
        
        # 停止按钮
        self.stop_button = QPushButton("停止")
        self.stop_button.clicked.connect(self.stop_scan)
        self.stop_button.setFixedWidth(100)  # 增大按钮宽度
        
        config_layout.addWidget(standard_label)
        config_layout.addWidget(self.standard_combo)
        config_layout.addWidget(exclude_label)
        config_layout.addWidget(self.exclude_input)
        config_layout.addWidget(self.scan_button)
        config_layout.addWidget(self.pause_button)
        config_layout.addWidget(self.resume_button)
        config_layout.addWidget(self.stop_button)
        
        # 导出按钮区域
        export_widget = QWidget()
        export_layout = QHBoxLayout(export_widget)
        export_layout.setAlignment(Qt.AlignRight)
        
        # 导出PDF按钮
        self.export_pdf_button = QPushButton("导出PDF")
        self.export_pdf_button.clicked.connect(self.export_pdf_report)
        self.export_pdf_button.setFixedWidth(120)  # 增大按钮宽度
        self.export_pdf_button.setEnabled(False)
        
        # 导出其他格式按钮
        self.export_other_button = QPushButton("其他格式")
        self.export_other_button.clicked.connect(self.export_other_report)
        self.export_other_button.setFixedWidth(120)  # 增大按钮宽度
        self.export_other_button.setEnabled(False)
        
        export_layout.addWidget(self.export_pdf_button)
        export_layout.addWidget(self.export_other_button)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        # 结果区域
        splitter = QSplitter(Qt.Vertical)
        
        # 日志区域
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        log_label = QLabel("扫描日志")
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(log_label)
        log_layout.addWidget(self.log_text)
        splitter.addWidget(log_widget)
        
        # 结果标签页
        self.tabs = QTabWidget()
        
        # 详细结果标签页
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        self.details_table = QTableWidget()
        self.details_table.setColumnCount(5)
        self.details_table.setHorizontalHeaderLabels(["文件路径", "规则名称", "违规描述", "行号", "严重性"])
        self.details_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.details_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.details_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.details_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Interactive)
        self.details_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Interactive)
        
        details_layout.addWidget(self.details_table)
        self.tabs.addTab(details_widget, "详细结果")
        
        # 总体统计标签页
        overall_stats_widget = QWidget()
        overall_stats_layout = QVBoxLayout(overall_stats_widget)
        stats_label = QLabel("总体统计")
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["统计项", "数值"])
        self.stats_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.stats_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        overall_stats_layout.addWidget(stats_label)
        overall_stats_layout.addWidget(self.stats_table)
        self.tabs.addTab(overall_stats_widget, "总体统计")
        
        # 语言分布标签页
        lang_dist_widget = QWidget()
        lang_dist_layout = QVBoxLayout(lang_dist_widget)
        lang_label = QLabel("语言分布")
        self.language_table = QTableWidget()
        self.language_table.setColumnCount(2)
        self.language_table.setHorizontalHeaderLabels(["语言", "文件数"])
        self.language_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.language_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        lang_dist_layout.addWidget(lang_label)
        lang_dist_layout.addWidget(self.language_table)
        self.tabs.addTab(lang_dist_widget, "语言分布")
        
        # 违规统计（按类型）标签页
        violations_type_widget = QWidget()
        violations_type_layout = QVBoxLayout(violations_type_widget)
        violations_label = QLabel("违规统计（按类型）")
        self.violations_table = QTableWidget()
        self.violations_table.setColumnCount(2)
        self.violations_table.setHorizontalHeaderLabels(["违规类型", "数量"])
        self.violations_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.violations_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        violations_type_layout.addWidget(violations_label)
        violations_type_layout.addWidget(self.violations_table)
        self.tabs.addTab(violations_type_widget, "违规类型统计")
        
        # 违规统计（按文件）标签页
        violations_file_widget = QWidget()
        violations_file_layout = QVBoxLayout(violations_file_widget)
        violations_by_file_label = QLabel("违规统计（按文件）")
        self.violations_by_file_table = QTableWidget()
        self.violations_by_file_table.setColumnCount(3)
        self.violations_by_file_table.setHorizontalHeaderLabels(["文件名", "文件路径", "违规数"])
        self.violations_by_file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.violations_by_file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.violations_by_file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)
        violations_file_layout.addWidget(violations_by_file_label)
        violations_file_layout.addWidget(self.violations_by_file_table)
        self.tabs.addTab(violations_file_widget, "文件违规统计")
        
        # 违规统计（按严重性）标签页
        violations_severity_widget = QWidget()
        violations_severity_layout = QVBoxLayout(violations_severity_widget)
        violations_by_severity_label = QLabel("违规统计（按严重性）")
        self.violations_by_severity_table = QTableWidget()
        self.violations_by_severity_table.setColumnCount(2)
        self.violations_by_severity_table.setHorizontalHeaderLabels(["严重性", "数量"])
        self.violations_by_severity_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.violations_by_severity_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        violations_severity_layout.addWidget(violations_by_severity_label)
        violations_severity_layout.addWidget(self.violations_by_severity_table)
        self.tabs.addTab(violations_severity_widget, "严重性统计")
        
        # 许可证扫描标签页
        license_widget = QWidget()
        license_layout = QVBoxLayout(license_widget)
        license_label = QLabel("许可证扫描结果")
        self.license_table = QTableWidget()
        self.license_table.setColumnCount(3)
        self.license_table.setHorizontalHeaderLabels(["文件路径", "许可证类型", "是否高风险"])
        self.license_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.license_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.license_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)
        license_layout.addWidget(license_label)
        license_layout.addWidget(self.license_table)
        self.tabs.addTab(license_widget, "许可证扫描")
        
        splitter.addWidget(self.tabs)
        
        # 设置分割比例，让结果区域更大
        splitter.setSizes([200, 600])
        
        # 添加所有部件到主布局
        main_layout.addWidget(path_widget)
        main_layout.addWidget(config_widget)
        main_layout.addWidget(export_widget)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(splitter)
        
        self.setCentralWidget(main_widget)
    
    def browse_directory(self):
        """浏览选择目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择项目目录")
        if directory:
            self.path_input.setText(directory)
            # 保存到配置
            self.config_manager.set("scanner.project_path", directory)
            self.config_manager.save_config()
    
    def start_scan(self):
        """开始扫描"""
        project_path = self.path_input.text()
        if not self._is_valid_directory(project_path):
            QMessageBox.warning(self, "警告", "请选择有效的项目目录")
            return
        
        # 获取排除目录
        exclude_dirs = [d.strip() for d in self.exclude_input.toPlainText().split(",") if d.strip()]
        
        # 获取规范标准并映射到实际规则集名称
        standard_display = self.standard_combo.currentText()
        # 映射UI显示名称到规则集实际名称
        standard_mapping = {
            "PEP 8": "PEP8",
            "Google": "Google",
            "Airbnb": "Airbnb",
            "Standard": "Standard",
            "自定义": "Google"  # 自定义模式默认使用Google规则集作为基础
        }
        standard = standard_mapping.get(standard_display, standard_display)
        
        # 保存配置
        self.config_manager.set("scanner.project_path", project_path)
        self.config_manager.set("scanner.exclude_dirs", ",".join(exclude_dirs))
        self.config_manager.set("scanner.standard", standard)
        self.config_manager.save_config()
        
        # 清空之前的结果
        self.clear_results()
        
        # 创建扫描器线程
        self.scanner_thread = QThread()
        self.scanner = CodeScanner(project_path, standard)
        self.scanner.moveToThread(self.scanner_thread)
        
        # 连接信号和槽
        self.scanner_thread.started.connect(self.scanner.start)
        self.scanner.progress_updated.connect(self.update_progress)
        self.scanner.log_updated.connect(self.update_log)
        self.scanner.scan_completed.connect(self.scan_completed)
        
        # 启动线程
        self.scanner_thread.start()
        
        # 更新按钮状态
        self.scan_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.resume_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # 记录开始时间
        self.start_time = time.time()
    
    def stop_scan(self):
        """停止扫描"""
        if self.scanner and self.scanner_thread and self.scanner_thread.isRunning():
            self.scanner.stop()
            self.scanner_thread.quit()
            self.scanner_thread.wait()
            
            # 更新按钮状态
            self.scan_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.resume_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            
            self.update_log("扫描已停止")
    
    def pause_scan(self):
        """暂停扫描"""
        if self.scanner:
            self.scanner.pause_scan()
            self.pause_button.setEnabled(False)
            self.resume_button.setEnabled(True)
    
    def resume_scan(self):
        """恢复扫描"""
        if self.scanner:
            self.scanner.resume_scan()
            self.pause_button.setEnabled(True)
            self.resume_button.setEnabled(False)
    
    def scan_completed(self, results):
        """扫描完成回调"""
        # 保存结果
        self.last_scan_results = results
        
        # 计算总耗时
        elapsed_time = time.time() - self.start_time
        
        # 更新UI
        self.update_log(f"扫描完成！耗时: {elapsed_time:.2f}秒")
        self.update_log(f"共扫描{results['scanned_files']}个文件")
        
        # 显示结果
        self._display_details(results)
        self._display_statistics(results)
        
        # 执行许可证扫描
        self._scan_licenses()
        
        # 更新按钮状态
        self.scan_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.resume_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.export_pdf_button.setEnabled(True)
        self.export_other_button.setEnabled(True)
        
        # 清理线程
        if self.scanner_thread and self.scanner_thread.isRunning():
            self.scanner_thread.quit()
            self.scanner_thread.wait()
    
    def update_progress(self, progress):
        """更新进度条"""
        self.progress_bar.setValue(progress)
    
    def update_log(self, message):
        """更新日志"""
        timestamp = time.strftime("%H:%M:%S")
        
        # 确保消息是字符串类型
        if not isinstance(message, str):
            message = str(message)
        
        # 构建要显示的完整消息
        full_message = f"[{timestamp}] {message}"
        
        # 保存当前文本颜色
        current_color = self.log_text.textColor()
        
        # 检查是否是特殊消息，如果是，确保使用正常文本颜色
        if "done processing" in message.lower() or "total error found" in message.lower():
            # 明确设置为黑色文本，避免被错误标识为错误
            self.log_text.setTextColor(QColor(0, 0, 0))
        
        # 添加消息
        self.log_text.append(full_message)
        
        # 恢复原始文本颜色
        self.log_text.setTextColor(current_color)
        
        # 滚动到底部
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def clear_results(self):
        """清空结果"""
        # 清空日志
        self.log_text.clear()
        
        # 清空表格
        self.details_table.setRowCount(0)
        self.stats_table.setRowCount(0)
        self.language_table.setRowCount(0)
        self.violations_table.setRowCount(0)
        self.violations_by_file_table.setRowCount(0)
        self.violations_by_severity_table.setRowCount(0)
        
        # 重置进度条
        self.progress_bar.setValue(0)
    
    def _display_statistics(self, results):
        """显示统计结果"""
        # 清空表格
        self.stats_table.setRowCount(0)
        self.language_table.setRowCount(0)
        self.violations_table.setRowCount(0)
        self.violations_by_file_table.setRowCount(0)
        self.violations_by_severity_table.setRowCount(0)
        
        # 过滤掉包含特殊文本的违规项
        filtered_violations = {}
        if results.get('violations'):
            for violation_type, count in results['violations'].items():
                # 跳过特殊消息类型
                if not ("done processing" in violation_type.lower() or "total errors found" in violation_type.lower()):
                    filtered_violations[violation_type] = count
        
        # 使用扫描器提供的按严重性统计的违规数据
        violations_by_severity = results.get('violations_by_severity', {})
        high_severity_count = violations_by_severity.get('high', 0)
        medium_severity_count = violations_by_severity.get('medium', 0)
        low_severity_count = violations_by_severity.get('low', 0)
        
        # 如果没有按严重性统计的数据，尝试从详细违规信息中计算
        if high_severity_count == 0 and medium_severity_count == 0 and low_severity_count == 0:
            details = results.get('details', {})
            for file_path, violations in details.items():
                for violation in violations:
                    # 过滤特殊消息
                    description = violation.get('description', '').lower()
                    rule_name = violation.get('rule_name', '').lower()
                    if 'done processing' in description or 'total errors found' in description or \
                       'done processing' in rule_name or 'total errors found' in rule_name:
                        continue
                    
                    severity = violation.get('severity', 'low').lower()
                    if severity == 'high':
                        high_severity_count += 1
                    elif severity == 'medium':
                        medium_severity_count += 1
                    else:
                        low_severity_count += 1
        
        # 更新结果中的违规严重性数据，确保一致性
        violations_by_severity = {
            'high': high_severity_count,
            'medium': medium_severity_count,
            'low': low_severity_count
        }
        
        # 基本统计信息
        stats_data = [
            ("扫描文件总数", results['scanned_files']),
            ("发现违规总数", sum(filtered_violations.values()) if filtered_violations else 0),
            ("总代码行数", results.get('total_lines', 0)),
            ("规范度评分", f"{self._calculate_score(results):.1f}%")
        ]
        
        # 添加细粒度统计信息
        # 如果有按文件统计的数据
        if results.get('violations_by_file'):
            files_with_violations = sum(1 for count in results['violations_by_file'].values() if count > 0)
            stats_data.append(("有违规文件数", files_with_violations))
        
        # 计算并显示违规占比
        total_violations = sum(results['violations'].values()) if results.get('violations') else 0
        total_lines = results.get('total_lines', 0)
        if total_lines > 0:
            violation_ratio = (total_violations / total_lines) * 100
            stats_data.append(("违规占比", f"{violation_ratio:.2f}%"))
        
        # 添加高中低违规数据到统计信息
        stats_data.extend([
            ("高严重性违规", high_severity_count),
            ("中严重性违规", medium_severity_count),
            ("低严重性违规", low_severity_count)
        ])
        
        for row, (name, value) in enumerate(stats_data):
            self.stats_table.insertRow(row)
            self.stats_table.setItem(row, 0, QTableWidgetItem(name))
            self.stats_table.setItem(row, 1, QTableWidgetItem(str(value)))
        
        # 语言分布
        for row, (lang, count) in enumerate(results['languages'].items()):
            self.language_table.insertRow(row)
            self.language_table.setItem(row, 0, QTableWidgetItem(lang))
            self.language_table.setItem(row, 1, QTableWidgetItem(str(count)))
        
        # 违规统计（按类型）- 使用过滤后的数据
        for row, (violation, count) in enumerate(filtered_violations.items()):
            self.violations_table.insertRow(row)
            self.violations_table.setItem(row, 0, QTableWidgetItem(violation))
            self.violations_table.setItem(row, 1, QTableWidgetItem(str(count)))
        
        # 违规统计（按文件）
        if results.get('violations_by_file'):
            # 按违规数量排序
            sorted_files = sorted(results['violations_by_file'].items(), key=lambda x: x[1], reverse=True)
            for row, (file_path, count) in enumerate(sorted_files):
                if count > 0:  # 只显示有违规的文件
                    self.violations_by_file_table.insertRow(row)
                    self.violations_by_file_table.setItem(row, 0, QTableWidgetItem(os.path.basename(file_path)))
                    self.violations_by_file_table.setItem(row, 1, QTableWidgetItem(file_path))
                    self.violations_by_file_table.setItem(row, 2, QTableWidgetItem(str(count)))
        
        # 违规统计（按严重性）- 使用我们计算的准确数据
        severity_map = {
            'high': '高严重性',
            'medium': '中严重性',
            'low': '低严重性'
        }
        
        # 添加高中低严重性数据到表格
        for row, (severity, count) in enumerate([('high', high_severity_count), ('medium', medium_severity_count), ('low', low_severity_count)]):
            if count > 0:  # 只显示有违规的严重性级别
                self.violations_by_severity_table.insertRow(row)
                severity_display = severity_map.get(severity, severity)
                self.violations_by_severity_table.setItem(row, 0, QTableWidgetItem(severity_display))
                self.violations_by_severity_table.setItem(row, 1, QTableWidgetItem(str(count)))
        
        # 如果没有任何违规，添加一个空行显示无违规
        if high_severity_count == 0 and medium_severity_count == 0 and low_severity_count == 0:
            self.violations_by_severity_table.insertRow(0)
            self.violations_by_severity_table.setItem(0, 0, QTableWidgetItem('无违规'))
            self.violations_by_severity_table.setItem(0, 1, QTableWidgetItem('0'))
        
        # 切换到统计结果标签页
        self.tabs.setCurrentIndex(1)
    
    def _display_details(self, results):
        """显示详细结果"""
        # 清空表格
        self.details_table.setRowCount(0)
        
        # 添加详细结果到表格
        if 'details' in results:
            for file_path, violations in results['details'].items():
                for violation in violations:
                    # 获取违规描述
                    description = violation.get("description", "")
                    rule_name = violation.get("rule_name", "")
                    
                    # 过滤掉包含特殊文本的条目
                    if ("done processing" in description.lower() or 
                        "total errors found" in description.lower() or
                        "done processing" in rule_name.lower() or 
                        "total errors found" in rule_name.lower()):
                        continue  # 跳过这些特殊消息
                    
                    # 添加行
                    row_position = self.details_table.rowCount()
                    self.details_table.insertRow(row_position)
                    
                    # 文件路径
                    file_item = QTableWidgetItem(file_path)
                    
                    # 规则名称
                    rule_item = QTableWidgetItem(rule_name)
                    
                    # 违规描述
                    desc_item = QTableWidgetItem(description)
                    
                    # 行号
                    line_item = QTableWidgetItem(str(violation.get("line_number", "")))
                    line_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    # 严重性
                    severity = violation.get("severity", "medium")
                    severity_item = QTableWidgetItem(severity)
                    severity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    # 设置不同严重性的颜色
                    if severity == "high":
                        severity_item.setBackground(QColor(255, 180, 180))
                    elif severity == "medium":
                        severity_item.setBackground(QColor(255, 230, 150))
                    elif severity == "low":
                        severity_item.setBackground(QColor(200, 230, 255))
                    
                    # 添加到表格
                    self.details_table.setItem(row_position, 0, file_item)
                    self.details_table.setItem(row_position, 1, rule_item)
                    self.details_table.setItem(row_position, 2, desc_item)
                    self.details_table.setItem(row_position, 3, line_item)
                    self.details_table.setItem(row_position, 4, severity_item)
    
    def open_license_scanner(self):
        """打开开源协议扫描窗口"""
        license_window = LicenseWindow(self)
        license_window.exec_()
        
    def _scan_licenses(self):
        """执行许可证扫描并显示结果"""
        if not hasattr(self, 'last_scan_results') or not self.last_scan_results:
            return
        
        from src.core.license_scanner import LicenseScanner
        
        # 获取项目路径
        project_path = self.path_input.text()
        if not project_path:
            return
        
        self.update_log("开始执行许可证扫描...")
        
        try:
            # 创建许可证扫描器
            scanner = LicenseScanner()
            
            # 执行扫描
            scan_results = scanner.scan_directory(project_path)
            
            # 显示许可证扫描结果
            self._display_license_results(scan_results)
            
            # 获取实际的许可证数量
            license_count = len(scan_results.get('licenses_by_file', {}))
            self.update_log(f"许可证扫描完成，发现{license_count}个许可证")
        except Exception as e:
            self.update_log(f"许可证扫描失败: {str(e)}")
    
    def _display_license_results(self, scan_results):
        """显示许可证扫描结果"""
        # 清空表格
        self.license_table.setRowCount(0)
        
        # 获取文件到许可证的映射（修正数据访问）
        licenses_by_file = scan_results.get('licenses_by_file', {})
        
        # 设置高风险许可证列表
        high_risk_licenses = ["GPL-2.0", "GPL-3.0", "LGPL", "AGPL"]
        
        # 添加结果到表格
        for file_path, licenses in licenses_by_file.items():
            for license_type in licenses:
                # 检查是否为高风险许可证
                is_high_risk = "是" if any(risk_license in license_type.upper() for risk_license in high_risk_licenses) else "否"
                
                # 添加行
                row_position = self.license_table.rowCount()
                self.license_table.insertRow(row_position)
                
                # 设置单元格内容
                file_item = QTableWidgetItem(file_path)
                license_item = QTableWidgetItem(license_type)
                risk_item = QTableWidgetItem(is_high_risk)
                
                # 设置单元格不可编辑
                file_item.setFlags(file_item.flags() & ~Qt.ItemIsEditable)
                license_item.setFlags(license_item.flags() & ~Qt.ItemIsEditable)
                risk_item.setFlags(risk_item.flags() & ~Qt.ItemIsEditable)
                
                # 设置高风险许可证的样式
                if is_high_risk == "是":
                    risk_item.setForeground(QColor("red"))
                
                # 确保列数据正确映射
                # 第0列: 文件路径
                self.license_table.setItem(row_position, 0, file_item)
                # 第1列: 许可证类型
                self.license_table.setItem(row_position, 1, license_item)
                # 第2列: 是否高风险
                self.license_table.setItem(row_position, 2, risk_item)
        
        # 自动调整列宽
        for column in range(self.license_table.columnCount()):
            self.license_table.horizontalHeader().setSectionResizeMode(column, QHeaderView.Interactive)
    
    def export_pdf_report(self):
        """导出PDF格式报告"""
        if hasattr(self, 'last_scan_results') and self.last_scan_results:
            try:
                # 获取默认保存目录
                default_dir = self.config_manager.get("report.output_dir", os.path.join(os.path.expanduser("~"), "Desktop"))
                
                # 确保默认目录存在
                if not os.path.exists(default_dir):
                    try:
                        os.makedirs(default_dir)
                    except Exception as e:
                        self.update_log(f"创建报告目录失败：{str(e)}")
                        default_dir = os.path.expanduser("~")
                
                # 获取项目路径并从中提取项目名称
                project_path = self.path_input.text()
                if project_path and project_path != "未选择项目":
                    # 提取项目名称（路径的最后一个部分）
                    project_name = os.path.basename(project_path)
                else:
                    project_name = "unknown_project"
                
                # 构建默认文件名：项目名称-codeaudit-report-时间戳.pdf
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                default_filename = f"{project_name}-codeaudit-report-{timestamp}.pdf"
                
                # 打开保存对话框，允许用户选择保存路径和文件名
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "导出PDF报告", os.path.join(default_dir, default_filename),
                    "PDF文件 (*.pdf);;所有文件 (*)"
                )
                
                if file_path:
                    # 确保文件扩展名为pdf
                    if not file_path.lower().endswith('.pdf'):
                        file_path += '.pdf'
                    
                    # 创建报告生成器，传递用户选择的规范标准
                    ruleset = self.standard_combo.currentText()
                    report_generator = ReportGenerator(self.last_scan_results, ruleset)
                    
                    # 生成报告
                    try:
                        # 记录尝试导出的信息
                        self.update_log(f"尝试导出PDF格式报告到：{file_path}")
                        
                        # 使用generate_report方法
                        report_path = report_generator.generate_report(
                            file_path,
                            'pdf',
                            include_summary=self.config_manager.get("report.include_summary", True),
                            include_details=self.config_manager.get("report.include_details", True)
                        )
                        
                        # 检查生成的文件是否为提示文件而非真正的PDF
                        try:
                            with open(report_path, 'r', encoding='utf-8') as f:
                                content = f.read(100)  # 读取文件开头
                                if "wkhtmltopdf" in content and len(content) < 1000:
                                    # 这是一个提示文件，不是真正的PDF
                                    self.update_log(f"PDF生成需要安装wkhtmltopdf，已创建说明文件")
                                    QMessageBox.information(self, "依赖缺失", 
                                                           f"已创建说明文件：{report_path}\n\n" +
                                                           "PDF报告生成需要安装wkhtmltopdf。说明文件中包含详细的安装指南。")
                                    return
                        except Exception:
                            # 如果无法以文本方式打开，可能是真正的PDF文件
                            pass
                        
                        # 显示成功消息
                        self.update_log(f"报告已成功导出到：{report_path}")
                        QMessageBox.information(self, "成功", f"报告已导出到：{report_path}")
                        
                        # 保存最后导出路径
                        self.config_manager.set("report.output_dir", os.path.dirname(file_path))
                        self.config_manager.save_config()
                    except Exception as e:
                        error_msg = f"生成报告失败：{str(e)}"
                        self.update_log(error_msg)
                        QMessageBox.warning(self, "失败", error_msg)
            except Exception as e:
                error_msg = f"导出报告过程中发生错误：{str(e)}"
                self.update_log(error_msg)
                QMessageBox.warning(self, "失败", error_msg)
        else:
            QMessageBox.information(self, "提示", "请先进行扫描获取结果")
    
    def export_other_report(self):
        """导出其他格式报告"""
        if hasattr(self, 'last_scan_results') and self.last_scan_results:
            # 获取默认保存目录
            default_dir = self.config_manager.get("report.output_dir", os.path.join(os.path.expanduser("~"), "Desktop"))
            
            # 确保默认目录存在
            if not os.path.exists(default_dir):
                try:
                    os.makedirs(default_dir)
                except Exception as e:
                    self.update_log(f"创建报告目录失败：{str(e)}")
                    default_dir = os.path.expanduser("~")
            
            # 打开保存对话框
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存报告", os.path.join(default_dir, "code_audit_report.txt"),
                "文本文件 (*.txt);;JSON文件 (*.json);;CSV文件 (*.csv);;HTML文件 (*.html);;PDF文件 (*.pdf)"
            )
            
            if file_path:
                # 获取文件扩展名
                _, file_ext = os.path.splitext(file_path)
                file_ext = file_ext.lower()
                
                # 获取用户选择的规范标准
                ruleset = self.standard_combo.currentText()
                
                # 映射文件扩展名到报告格式
                format_map = {
                    '.txt': 'txt',
                    '.json': 'json',
                    '.csv': 'csv',
                    '.html': 'html',
                    '.pdf': 'pdf'
                }
                report_format = format_map.get(file_ext, 'txt')
                
                # 确保文件目录存在
                report_dir = os.path.dirname(file_path)
                if not os.path.exists(report_dir):
                    os.makedirs(report_dir)
                
                # 创建报告生成器，传递用户选择的规范标准
                report_generator = ReportGenerator(self.last_scan_results, ruleset)
                
                # 生成报告
                try:
                    # 记录尝试导出的信息
                    self.update_log(f"尝试导出{report_format.upper()}格式报告到：{file_path}")
                    
                    # 使用generate_report方法
                    report_path = report_generator.generate_report(
                        file_path,
                        report_format,
                        include_summary=self.config_manager.get("report.include_summary", True),
                        include_details=self.config_manager.get("report.include_details", True)
                    )
                    
                    # 显示成功消息
                    self.update_log(f"报告已成功导出到：{report_path}")
                    QMessageBox.information(self, "成功", f"报告已导出到：{report_path}")
                    
                    # 保存最后导出路径
                    self.config_manager.set("report.output_dir", os.path.dirname(file_path))
                    self.config_manager.save_config()
                except Exception as e:
                    error_msg = f"生成报告失败：{str(e)}"
                    self.update_log(error_msg)
                    QMessageBox.warning(self, "失败", error_msg)
        else:
            QMessageBox.information(self, "提示", "请先进行扫描获取结果")
    
    def _calculate_score(self, results):
        """计算规范度评分
        
        根据不规范代码行占总代码行的比例计算规范度评分：
        1. 计算每种严重级别的不规范代码行占比
        2. 使用新公式：100 - 低违规代码占比×0.1 - 中违规代码占比×1 - 高违规代码占比×10
        """
        # 获取扫描结果中的总行数
        total_lines = results.get('total_lines', 0)
        if total_lines == 0:
            # 如果没有收集到总行数，使用估算值
            scanned_files = results.get('scanned_files', 0)
            total_lines = scanned_files * 200
            if total_lines == 0:
                return 100.0
        
        # 使用扫描器提供的按严重性统计的违规数据
        violations_by_severity = results.get('violations_by_severity', {})
        high_violations = violations_by_severity.get('high', 0)
        medium_violations = violations_by_severity.get('medium', 0)
        low_violations = violations_by_severity.get('low', 0)
        
        # 如果没有按严重性统计的数据，尝试从详细违规信息中计算
        if high_violations == 0 and medium_violations == 0 and low_violations == 0:
            details = results.get('details', {})
            for file_path, violations in details.items():
                for violation in violations:
                    # 过滤特殊消息
                    description = violation.get('description', '').lower()
                    rule_name = violation.get('rule_name', '').lower()
                    if 'done processing' in description or 'total errors found' in description or \
                       'done processing' in rule_name or 'total errors found' in rule_name:
                        continue
                    
                    severity = violation.get('severity', 'low').lower()
                    if severity == 'high':
                        high_violations += 1
                    elif severity == 'medium':
                        medium_violations += 1
                    else:
                        low_violations += 1
        
        # 计算各严重级别的不规范代码行占比（转换为百分比）
        high_ratio_percent = (high_violations / total_lines) * 100
        medium_ratio_percent = (medium_violations / total_lines) * 100
        low_ratio_percent = (low_violations / total_lines) * 100
        
        # 使用新的评分公式：100 - 低违规×0.1 - 中违规×1 - 高违规×10
        # 高严重性违规影响最大，中严重性次之，低严重性影响最小
        final_score = 100 - (low_ratio_percent * 0.1) - (medium_ratio_percent * 1) - (high_ratio_percent * 10)
        
        # 确保分数不低于0分
        final_score = max(0, final_score)
        
        return final_score
    
    def _is_valid_directory(self, path):
        """检查路径是否为有效的目录"""
        try:
            return os.path.isdir(path) and os.access(path, os.R_OK)
        except:
            return False
            
    def setup_menu(self):
        """设置菜单栏"""
        # 获取菜单栏
        menu_bar = self.menuBar()
        
        # 帮助菜单
        help_menu = menu_bar.addMenu("帮助")
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于",
            "代码规范扫描工具\n版本: 1.0.0\n\n用于扫描代码中的规范问题并生成报告。\n\n软件著作权声明：\n本软件由张可开发，保留所有权利。\n未经授权，不得复制、修改或分发本软件。"
        )