#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import csv
import datetime
from .config_manager import ConfigManager
# 延迟导入WeasyPrint，避免启动时加载GTK3/GObject依赖
# WeasyPrint仅在生成PDF报告时需要
HTML = None
CSS = None

class ReportGenerator:
    def __init__(self, results, ruleset=None):
        self.results = results
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.config_manager = ConfigManager()
        # 如果提供了ruleset参数，使用它；否则从配置管理器获取默认值
        self.ruleset = ruleset or self.config_manager.get_default_ruleset()
        
        # 确保报告目录存在
        self.reports_dir = os.path.join(os.path.expanduser('~'), 'CodeAuditReports')
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
    
    def save_report(self, format='txt'):
        """保存报告到文件，默认保存为文本格式"""
        if format.lower() == 'json':
            return self._save_json_report()
        elif format.lower() == 'csv':
            return self._save_csv_report()
        elif format.lower() == 'html':
            return self._save_html_report()
        elif format.lower() == 'pdf':
            return self._save_pdf_report()
        else:
            return self._save_text_report()
            
    def generate_report(self, file_path, format='txt', include_summary=True, include_details=True):
        """生成报告并保存到指定路径"""
        try:
            # 根据格式生成报告
            if format.lower() == 'json':
                return self._generate_json_report(file_path, include_summary, include_details)
            elif format.lower() == 'csv':
                return self._generate_csv_report(file_path, include_summary, include_details)
            elif format.lower() == 'html':
                return self._generate_html_report(file_path, include_summary, include_details)
            elif format.lower() == 'pdf':
                # 直接生成PDF格式报告，不再创建HTML备份
                try:
                    return self._generate_pdf_report(file_path, include_summary, include_details)
                except Exception as pdf_error:
                    # 如果PDF生成失败，直接抛出异常
                    raise Exception(f"PDF生成失败: {str(pdf_error)}")
            else:
                return self._generate_text_report(file_path, include_summary, include_details)
        except Exception as e:
            raise Exception(f"生成报告失败: {str(e)}")
    
    def _save_text_report(self):
        """保存文本格式的报告"""
        report_path = os.path.join(self.reports_dir, f'audit_report_{self.timestamp}.txt')
        return self._generate_text_report(report_path)
    
    def _generate_text_report(self, file_path, include_summary=True, include_details=True):
        """生成文本格式的报告"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # 写入报告标题和时间
                f.write('=' * 60 + '\n')
                f.write('代码规范度扫描报告\n')
                f.write('=' * 60 + '\n\n')
                f.write(f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                if include_summary:
                    # 写入总体统计
                    f.write('【总体统计】\n')
                    f.write('-' * 40 + '\n')
                    f.write(f"总文件数: {self.results.get('total_files', 0)}\n")
                    f.write(f"已扫描文件: {self.results.get('scanned_files', 0)}\n")
                    f.write(f"跳过文件: {self.results.get('skipped_files', 0)}\n")
                    f.write(f"扫描时间: {self.results.get('scan_time', 0):.2f}秒\n")
                    f.write(f"规范度评分: {self._calculate_score():.1f}%\n\n")
                    
                    # 写入语言分布
                    f.write('【语言分布】\n')
                    f.write('-' * 40 + '\n')
                    languages = self.results.get('languages', {})
                    if languages:
                        for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
                            percentage = (count / self.results.get('scanned_files', 1)) * 100
                            f.write(f'{lang}: {count}个文件 ({percentage:.1f}%)\n')
                    else:
                        f.write('未扫描到支持的编程语言文件\n')
                    f.write('\n')
                    
                    # 写入违规统计
                    f.write('【违规统计】\n')
                    f.write('-' * 40 + '\n')
                    # 使用过滤后的违规数据
                    violations = self._filter_special_messages(self.results.get('violations', {}))
                    if violations:
                        total_violations = sum(violations.values())
                        for violation, count in sorted(violations.items(), key=lambda x: x[1], reverse=True):
                            percentage = (count / total_violations) * 100
                            f.write(f'{violation}: {count}次 ({percentage:.1f}%)\n')
                    else:
                        f.write('未发现规范违规问题\n')
                
                if include_details and 'details' in self.results:
                    f.write('\n【高风险违规信息】\n')
                    f.write('-' * 40 + '\n')
                    details = self.results['details']
                    if details:
                        has_high_violations = False
                        for file_path, violations in details.items():
                            high_violations_found = False
                            file_high_violations = []
                            for violation in violations:
                                # 检查是否是特殊消息
                                description = violation.get('description', '').lower()
                                rule_name = violation.get('rule_name', '').lower()
                                if 'done processing' in description or 'total errors found' in description or \
                                   'done processing' in rule_name or 'total errors found' in rule_name:
                                    continue
                                
                                if violation.get('severity', 'medium') == 'high':
                                    has_high_violations = True
                                    high_violations_found = True
                                    file_high_violations.append(violation)
                            # 只输出有高风险违规的文件
                            if high_violations_found:
                                f.write(f'\n文件: {file_path}\n')
                                for violation in file_high_violations:
                                    f.write(f"  - [{violation.get('severity', 'medium')}] {violation.get('rule_name', 'Unknown')}: {violation.get('description', '')}\n")
                                    if 'line_number' in violation and violation['line_number']:
                                        f.write(f"    行号: {violation['line_number']}\n")
                        # 如果没有高风险违规，显示相应提示
                        if not has_high_violations:
                            f.write('未发现高风险违规项\n')
                    else:
                        f.write('无详细违规信息\n')
                
                # 写入报告结尾
                f.write('\n' + '=' * 60 + '\n')
                f.write('报告生成完毕\n')
                f.write('=' * 60 + '\n')
                
            return file_path
        except Exception as e:
            raise Exception(f"生成文本报告失败: {str(e)}")
    
    def _save_json_report(self):
        """保存JSON格式的报告"""
        report_path = os.path.join(self.reports_dir, f'audit_report_{self.timestamp}.json')
        return self._generate_json_report(report_path)
    
    def _generate_json_report(self, file_path, include_summary=True, include_details=True):
        """生成JSON格式的报告"""
        try:
            report_data = {
                'report_info': {
                    'generated_at': datetime.datetime.now().isoformat(),
                    'score': self._calculate_score()
                }
            }
            
            if include_summary:
                report_data['statistics'] = {
                    'total_files': self.results.get('total_files', 0),
                    'scanned_files': self.results.get('scanned_files', 0),
                    'skipped_files': self.results.get('skipped_files', 0),
                    'scan_time': self.results.get('scan_time', 0),
                    'languages': self.results.get('languages', {}),
                    'violations': self.results.get('violations', {})
                }
            
            if include_details and 'details' in self.results:
                # 只包含高风险的违规信息
                filtered_details = {}
                for file_path, violations in self.results['details'].items():
                    high_violations = [v for v in violations if v.get('severity', 'medium') == 'high']
                    if high_violations:
                        filtered_details[file_path] = high_violations
                report_data['details'] = filtered_details
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            return file_path
        except Exception as e:
            raise Exception(f"生成JSON报告失败: {str(e)}")
    
    def _save_csv_report(self):
        """保存CSV格式的报告"""
        report_path = os.path.join(self.reports_dir, f'audit_report_{self.timestamp}.csv')
        return self._generate_csv_report(report_path)
    
    def _generate_csv_report(self, file_path, include_summary=True, include_details=True):
        """生成CSV格式的报告"""
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                if include_summary:
                    # 写入总体统计
                    writer.writerow(['报告类型', '代码规范度扫描报告'])
                    writer.writerow(['生成时间', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                    writer.writerow([])
                    writer.writerow(['【总体统计】'])
                    writer.writerow(['统计项', '数值'])
                    writer.writerow(['总文件数', self.results.get('total_files', 0)])
                    writer.writerow(['已扫描文件', self.results.get('scanned_files', 0)])
                    writer.writerow(['跳过文件', self.results.get('skipped_files', 0)])
                    writer.writerow(['扫描时间(秒)', f"{self.results.get('scan_time', 0):.2f}"])
                    writer.writerow(['规范度评分(%)', f"{self._calculate_score():.1f}"])
                    writer.writerow([])
                    
                    # 写入语言分布
                    writer.writerow(['【语言分布】'])
                    writer.writerow(['语言', '文件数量'])
                    languages = self.results.get('languages', {})
                    if languages:
                        for lang, count in sorted(languages.items()):
                            writer.writerow([lang, count])
                    else:
                        writer.writerow(['未扫描到支持的编程语言文件', ''])
                    writer.writerow([])
                    
                    # 写入违规统计
                    writer.writerow(['【违规统计】'])
                    writer.writerow(['违规类型', '数量'])
                    # 使用过滤后的违规数据
                    violations = self._filter_special_messages(self.results.get('violations', {}))
                    if violations:
                        for violation, count in sorted(violations.items()):
                            writer.writerow([violation, count])
                    else:
                        writer.writerow(['未发现规范违规问题', ''])
                    writer.writerow([])
                
                if include_details and 'details' in self.results:
                    # 写入高风险违规信息
                    writer.writerow(['【高风险违规信息】'])
                    writer.writerow(['文件路径', '规则名称', '违规描述', '行号', '严重性'])
                    details = self.results['details']
                    if details:
                        has_high_violations = False
                        for file_path, violations in details.items():
                            for violation in violations:
                                if violation.get('severity', 'medium') == 'high':
                                    has_high_violations = True
                                    writer.writerow([
                                        file_path,
                                        violation.get('rule_name', 'Unknown'),
                                        violation.get('description', ''),
                                        violation.get('line_number', ''),
                                        violation.get('severity', 'medium')
                                    ])
                        # 如果没有高风险违规，显示相应提示
                        if not has_high_violations:
                            writer.writerow(['未发现高风险违规项', '', '', '', ''])
            
            return file_path
        except Exception as e:
            raise Exception(f"生成CSV报告失败: {str(e)}")
    
    def _save_pdf_report(self):
        """保存PDF格式的报告"""
        report_path = os.path.join(self.reports_dir, f'audit_report_{self.timestamp}.pdf')
        return self._generate_pdf_report(report_path)
        
    def _generate_pdf_report(self, file_path, include_summary=True, include_details=True):
        """生成PDF格式的报告"""
        try:
            # 先生成HTML内容
            html_content = self._generate_html_content(include_summary, include_details)
            
            # 提前导入platform并获取系统信息
            import platform
            system = platform.system()
            
            # 使用WeasyPrint将HTML转换为PDF
            try:
                from weasyprint import HTML, CSS
                # 注意：不同版本的WeasyPrint可能有不同的初始化参数需求
                
                # 定义页面样式，确保与原设计一致
                page_css = CSS(string='''
                    @page {
                        size: A4;
                        margin-top: 20mm;
                        margin-right: 20mm;
                        margin-bottom: 20mm;
                        margin-left: 20mm;
                    }
                    body {
                        font-family: Arial, sans-serif;
                        font-size: 12pt;
                    }
                ''')
                
                # 生成PDF - 适配不同版本的WeasyPrint
                # 使用更简单的方式调用write_pdf，避免参数不匹配问题
                html = HTML(string=html_content)
                # 只传递必要的参数
                html.write_pdf(file_path, stylesheets=[page_css])
                
                print(f"PDF报告已成功生成: {file_path}")
                
            except ImportError:
                # 处理WeasyPrint未安装的情况
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("PDF报告生成需要安装WeasyPrint\n\n")
                    f.write("请运行以下命令安装WeasyPrint: pip install weasyprint\n")
                    f.write("安装后，重启应用程序即可生成PDF报告\n\n")
                    
                    # 添加针对不同平台的具体安装指南
                    if system == 'Windows':
                        f.write("Windows安装指南:\n")
                        f.write("1. 确保已安装pip和Python\n")
                        f.write("2. 运行命令: pip install weasyprint\n")
                        f.write("3. WeasyPrint可能需要安装GTK+依赖，详细信息请参考官方文档\n")
                    elif system == 'Darwin':
                        f.write("macOS安装指南:\n")
                        f.write("1. 确保已安装pip和Python\n")
                        f.write("2. 运行命令: pip install weasyprint\n")
                        f.write("3. WeasyPrint在macOS上依赖Cairo，可能需要通过Homebrew安装\n")
                        f.write("   运行: brew install cairo pango gdk-pixbuf libffi\n")
                    elif system == 'Linux':
                        f.write("Linux安装指南:\n")
                        f.write("Ubuntu/Debian: sudo apt-get install python3-pip python3-dev\n")
                        f.write("CentOS/RHEL: sudo yum install python3-pip python3-devel\n")
                        f.write("然后运行: pip install weasyprint==55.0\n")  # 指定稳定版本
                        f.write("可能还需要安装系统依赖: sudo apt-get install libcairo2-dev libpango1.0-dev libgdk-pixbuf2.0-dev libffi-dev\n")
            except Exception as e:
                # 捕获并提供更具体的错误信息
                error_message = str(e)
                if "__init__() takes 1 positional argument but 3 were given" in error_message:
                    # 针对Linux上常见的参数错误提供更具体的解决建议
                    raise Exception(f"生成PDF报告失败: 版本兼容性问题。请尝试安装特定版本的WeasyPrint: pip install weasyprint==55.0")
                else:
                    raise Exception(f"生成PDF报告失败: {error_message}")
            
            return file_path
        except Exception as e:
            # 包装异常，提供更明确的错误链
            raise Exception(f"生成PDF报告失败: {str(e)}") from e
    
    def _save_html_report(self):
        """保存HTML格式的报告"""
        report_path = os.path.join(self.reports_dir, f'audit_report_{self.timestamp}.html')
        return self._generate_html_report(report_path)
        
    def _generate_html_report(self, file_path, include_summary=True, include_details=True):
        """生成HTML格式的报告"""
        try:
            html = self._generate_html_content(include_summary, include_details)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html)
            return file_path
        except Exception as e:
            raise Exception(f"生成HTML报告失败: {str(e)}")
    
    def _generate_html_content(self, include_summary=True, include_details=True):
        """生成HTML内容"""
        score = self._calculate_score()
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>代码规范度扫描报告</title>
    <style>
        /* 基础样式 */
        body {{ font-family: Arial, sans-serif; margin: 20px; font-size: 12px; }}
        h1 {{ color: #333; font-size: 18px; }}
        .summary {{ background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .section {{ margin-bottom: 30px; }}
        
        /* 表格基础样式 - 为PDF优化 */
        table {{ border-collapse: collapse; width: 100%; table-layout: fixed; margin-bottom: 20px; white-space: normal; }}
        th, td {{ 
            border: 1px solid #ddd; 
            padding: 6px; 
            text-align: left; 
            word-wrap: break-word; 
            word-break: break-all; 
            white-space: normal; 
            max-width: 100%; 
        }}
        th {{ background-color: #4CAF50; color: white; font-size: 11px; padding: 8px 4px; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        
        /* 评分样式 */
        .score {{ font-size: 24px; font-weight: bold; color: {'green' if score >= 80 else 'orange' if score >= 60 else 'red'}; }}
        
        /* 严重性样式 */
        .high {{ background-color: #ffcccc; }}
        .medium {{ background-color: #ffffcc; }}
        .low {{ background-color: #ccffcc; }}
        
        /* 违规信息表格 - 优化列宽和换行 */
        .violations-table th:nth-child(1), .violations-table td:nth-child(1) {{ width: 20%; font-size: 9px; }}
        .violations-table th:nth-child(2), .violations-table td:nth-child(2) {{ width: 14%; font-size: 9px; }}
        .violations-table th:nth-child(3), .violations-table td:nth-child(3) {{ width: 35%; font-size: 9px; }}
        .violations-table th:nth-child(4), .violations-table td:nth-child(4) {{ width: 10%; text-align: center; font-size: 9px; }}
        .violations-table th:nth-child(5), .violations-table td:nth-child(5) {{ width: 12%; text-align: center; font-size: 9px; }}
        
        /* PDF导出专用优化 */
        @media print {{ 
            body {{ font-size: 10px; margin: 10px; }}
            .violations-table td {{ 
                font-size: 9px; 
                line-height: 1.2; 
                padding: 4px; 
                overflow-wrap: break-word; 
                word-break: break-word; 
            }}
            .violations-table th {{ 
                font-size: 9px; 
                padding: 6px 2px; 
            }}
        }}
        </style>
</head>
<body>
    <h1>代码规范度扫描报告</h1>
    
    <div class="summary">
            <p>生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>扫描规范标准: {self.ruleset}</p>
            <p>规范度评分: <span class="score">{score:.1f}%</span></p>
        </div>
"""
        
        if include_summary:
            html += f"""
    <div class="section">
        <h2>总体统计</h2>
        <table>
            <tr><th>统计项</th><th>数值</th></tr>
            <tr><td>总文件数</td><td>{self.results.get('total_files', 0)}</td></tr>
            <tr><td>已扫描文件</td><td>{self.results.get('scanned_files', 0)}</td></tr>
            <tr><td>跳过文件</td><td>{self.results.get('skipped_files', 0)}</td></tr>
            <tr><td>总代码行数</td><td>{self.results.get('total_lines', 0)}</td></tr>
            <tr><td>违规占比</td><td>{self._calculate_violation_ratio():.2f}%</td></tr>
            <tr><td>扫描时间</td><td>{self.results.get('scan_time', 0):.2f}秒</td></tr>
            <tr><td>规范度评分</td><td>{self._calculate_score():.1f}%</td></tr>
        </table>
        
        <!-- 添加按严重性统计的违规数据 -->
        <table>
            <tr><th>违规严重性</th><th>违规数量</th><th>占总行数比例</th></tr>
            <tr class="high"><td>高风险违规</td><td>{self.results.get('violations_by_severity', {}).get('high', 0)}</td><td>{(self.results.get('violations_by_severity', {}).get('high', 0) / max(1, self.results.get('total_lines', 1))) * 100:.4f}%</td></tr>
            <tr class="medium"><td>中风险违规</td><td>{self.results.get('violations_by_severity', {}).get('medium', 0)}</td><td>{(self.results.get('violations_by_severity', {}).get('medium', 0) / max(1, self.results.get('total_lines', 1))) * 100:.4f}%</td></tr>
            <tr class="low"><td>低风险违规</td><td>{self.results.get('violations_by_severity', {}).get('low', 0)}</td><td>{(self.results.get('violations_by_severity', {}).get('low', 0) / max(1, self.results.get('total_lines', 1))) * 100:.4f}%</td></tr>
        </table>
    </div>
    
    <div class="section">
        <h2>语言分布</h2>
        <table>
            <tr><th>语言</th><th>文件数量</th><th>占比</th></tr>
"""
            
            # 添加语言分布数据
            languages = self.results.get('languages', {})
            if languages:
                scanned_files = self.results.get('scanned_files', 1)
                for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / scanned_files) * 100
                    html += f"            <tr><td>{lang}</td><td>{count}</td><td>{percentage:.1f}%</td></tr>\n"
            else:
                html += "            <tr><td colspan='3'>未扫描到支持的编程语言文件</td></tr>\n"
            
            html += f"""
        </table>
    </div>
    
    <div class="section">
        <h2>违规统计</h2>
        <table>
            <tr><th>违规类型</th><th>数量</th><th>占比</th></tr>
"""
            
            # 添加违规统计数据（使用过滤后的数据）
            violations = self._filter_special_messages(self.results.get('violations', {}))
            if violations:
                total_violations = sum(violations.values())
                for violation, count in sorted(violations.items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / total_violations) * 100
                    html += f"            <tr><td>{violation}</td><td>{count}</td><td>{percentage:.1f}%</td></tr>\n"
            else:
                html += "            <tr><td colspan='3'>未发现规范违规问题</td></tr>\n"
            
            html += f"""
        </table>
    </div>
"""
        
        if include_details and 'details' in self.results:
            html += f"""
    <div class="section">
        <h2>高风险违规信息</h2>
        <table class="violations-table">
            <tr><th>文件路径</th><th>规则名称</th><th>违规描述</th><th>行号</th><th>严重性</th></tr>
"""
            
            # 添加详细违规信息（仅高风险，过滤特殊消息）
            details = self.results['details']
            if details:
                has_high_violations = False
                for file_path, violations in details.items():
                    for violation in violations:
                        # 检查是否是特殊消息
                        description = violation.get('description', '').lower()
                        rule_name = violation.get('rule_name', '').lower()
                        if 'done processing' in description or 'total errors found' in description or \
                           'done processing' in rule_name or 'total errors found' in rule_name:
                            continue
                        
                        severity = violation.get('severity', 'medium')
                        # 只添加高风险的违规项
                        if severity == 'high':
                            has_high_violations = True
                            html += f"            <tr class='{severity}'><td>{file_path}</td><td>{violation.get('rule_name', 'Unknown')}</td><td>{violation.get('description', '')}</td><td>{violation.get('line_number', '')}</td><td>{severity}</td></tr>\n"
                # 如果没有高风险违规，显示相应提示
                if not has_high_violations:
                    html += "            <tr><td colspan='5'>未发现高风险违规项</td></tr>\n"
            else:
                html += "            <tr><td colspan='5'>无详细违规信息</td></tr>\n"
            
            html += f"""
        </table>
    </div>
"""
        
        html += f"""
</body>
</html>"""
        
        return html
    
    def _filter_special_messages(self, violations):
        """过滤掉包含特殊消息的违规项"""
        if not violations:
            return {}
        
        filtered = {}
        for violation_type, count in violations.items():
            # 跳过特殊消息类型
            if not ("done processing" in violation_type.lower() or "total errors found" in violation_type.lower()):
                filtered[violation_type] = count
        return filtered
    
    def _calculate_score(self):
        """计算规范度评分
        
        根据不规范代码行占总代码行的比例计算规范度评分：
        1. 计算每种严重级别的不规范代码行占比
        2. 使用新公式：100 - 低违规代码占比×0.1 - 中违规代码占比×1 - 高违规代码占比×10
        """
        # 获取扫描结果中的总行数
        total_lines = self.results.get('total_lines', 0)
        if total_lines == 0:
            # 如果没有收集到总行数，使用估算值
            scanned_files = self.results.get('scanned_files', 0)
            total_lines = scanned_files * 200
            if total_lines == 0:
                return 100.0
        
        # 使用扫描器提供的按严重性统计的违规数据
        violations_by_severity = self.results.get('violations_by_severity', {})
        high_violations = violations_by_severity.get('high', 0)
        medium_violations = violations_by_severity.get('medium', 0)
        low_violations = violations_by_severity.get('low', 0)
        
        # 如果没有按严重性统计的数据，尝试从详细违规信息中计算
        if high_violations == 0 and medium_violations == 0 and low_violations == 0:
            details = self.results.get('details', {})
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
    
    def _calculate_violation_ratio(self):
        """计算违规占比"""
        total_violations = sum(self.results.get('violations', {}).values())
        total_lines = self.results.get('total_lines', 0)
        if total_lines > 0:
            return (total_violations / total_lines) * 100
        return 0.0

# 辅助函数：生成HTML格式的报告预览

def generate_html_preview(results, ruleset=None):
    """生成HTML格式的报告预览"""
    generator = ReportGenerator(results, ruleset)
    score = generator._calculate_score()
    ruleset = generator.ruleset
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>代码规范度扫描报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .section {{ margin-bottom: 30px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .score {{ font-size: 24px; font-weight: bold; color: {'green' if score >= 80 else 'orange' if score >= 60 else 'red'}; }}
    </style>
</head>
<body>
    <h1>代码规范度扫描报告</h1>
    
    <div class="summary">
        <p>生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>扫描规范标准: {ruleset}</p>
        <p>规范度评分: <span class="score">{score:.1f}%</span></p>
        <p>扫描文件总数: {results.get('total_files', 0)}</p>
        <p>扫描时间: {results.get('scan_time', 0):.2f}秒</p>
    </div>
    
    <div class="section">
        <h2>语言分布</h2>
        <table>
            <tr><th>语言</th><th>文件数量</th></tr>
"""
    
    # 添加语言分布数据
    languages = results.get('languages', {})
    if languages:
        for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
            html += f"        <tr><td>{lang}</td><td>{count}</td></tr>\n"
    else:
        html += "        <tr><td colspan='2'>未扫描到支持的编程语言文件</td></tr>\n"
    
    html += f"""        </table>
    </div>
    
    <div class="section">
        <h2>违规统计</h2>
        <table>
            <tr><th>违规类型</th><th>数量</th></tr>
"""
    
    # 添加违规统计数据
    violations = results.get('violations', {})
    if violations:
        for violation, count in sorted(violations.items(), key=lambda x: x[1], reverse=True):
            html += f"        <tr><td>{violation}</td><td>{count}</td></tr>\n"
    else:
        html += "        <tr><td colspan='2'>未发现规范违规问题</td></tr>\n"
    
    html += f"""        </table>
    </div>
</body>
</html>"""
    
    return html