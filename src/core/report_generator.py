#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import csv
import datetime
import pdfkit

class ReportGenerator:
    def __init__(self, results):
        self.results = results
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        
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
                return self._generate_pdf_report(file_path, include_summary, include_details)
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
                    violations = self.results.get('violations', {})
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
                    violations = self.results.get('violations', {})
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
            
            # 尝试使用pdfkit将HTML转换为PDF
            try:
                # 设置pdfkit选项
                options = {
                    'page-size': 'A4',
                    'margin-top': '20mm',
                    'margin-right': '20mm',
                    'margin-bottom': '20mm',
                    'margin-left': '20mm',
                    'encoding': "UTF-8",
                    'no-outline': None,
                    'enable-local-file-access': True
                }
                
                # 生成PDF
                pdfkit.from_string(html_content, file_path, options=options)
            except OSError as e:
                # 处理wkhtmltopdf未安装的情况
                if "No wkhtmltopdf executable found" in str(e):
                    # 创建一个简单的文本文件提示用户安装wkhtmltopdf
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write("PDF报告生成需要安装wkhtmltopdf\n\n")
                        f.write("请访问 https://wkhtmltopdf.org/downloads.html 下载并安装适合您系统的版本\n")
                        f.write("安装后，重启应用程序即可生成PDF报告")
                else:
                    raise Exception(f"生成PDF报告失败: {str(e)}")
            
            return file_path
        except Exception as e:
            raise Exception(f"生成PDF报告失败: {str(e)}")
    
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
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .section {{ margin-bottom: 30px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .score {{ font-size: 24px; font-weight: bold; color: {'green' if score >= 80 else 'orange' if score >= 60 else 'red'}; }}
        .high {{ background-color: #ffcccc; }}
        .medium {{ background-color: #ffffcc; }}
        .low {{ background-color: #ccffcc; }}
    </style>
</head>
<body>
    <h1>代码规范度扫描报告</h1>
    
    <div class="summary">
        <p>生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
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
        <table>
            <tr><th>统计项</th><th>数值</th></tr>
            <tr><td>总文件数</td><td>{self.results.get('total_files', 0)}</td></tr>
            <tr><td>已扫描文件</td><td>{self.results.get('scanned_files', 0)}</td></tr>
            <tr><td>跳过文件</td><td>{self.results.get('skipped_files', 0)}</td></tr>
            <tr><td>扫描时间</td><td>{self.results.get('scan_time', 0):.2f}秒</td></tr>
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
            
            # 添加违规统计数据
            violations = self.results.get('violations', {})
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
        <h2>详细违规信息</h2>
        <table>
            <tr><th>文件路径</th><th>规则名称</th><th>违规描述</th><th>行号</th><th>严重性</th></tr>
"""
            
            # 添加详细违规信息（仅高风险）
            details = self.results['details']
            if details:
                has_high_violations = False
                for file_path, violations in details.items():
                    for violation in violations:
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
    
    def _calculate_score(self):
        """计算规范度评分
        
        根据不规范代码行占总代码行的比例计算规范度评分：
        1. 计算每种严重级别的不规范代码行占比
        2. 基于占比直接计算得分（占比越低，得分越高）
        3. 根据严重级别设置不同权重，高严重度权重更高
        """
        scanned_files = self.results.get('scanned_files', 0)
        if scanned_files == 0:
            return 100.0
        
        # 统计代码总行数（需要在扫描时收集这个信息）
        # 这里我们可以通过扫描结果估算，或者使用一个更简单的方法
        # 假设每个扫描的文件平均有200行代码（可根据实际情况调整）
        estimated_lines = scanned_files * 200
        
        # 获取不同严重性级别的违规数量
        violations_by_severity = self.results.get('violations_by_severity', {})
        high_violations = violations_by_severity.get('high', 0)
        medium_violations = violations_by_severity.get('medium', 0)
        low_violations = violations_by_severity.get('low', 0)
        
        # 计算各严重级别的不规范代码行占比
        if estimated_lines > 0:
            high_ratio = high_violations / estimated_lines
            medium_ratio = medium_violations / estimated_lines
            low_ratio = low_violations / estimated_lines
        else:
            high_ratio = 0
            medium_ratio = 0
            low_ratio = 0
        
        # 基于占比直接计算各严重级别的得分
        # 使用自然指数函数让分数在低占比时变化更平缓，高占比时下降更快
        high_score = max(0, 100 * (1 - high_ratio) ** 0.3)
        medium_score = max(0, 100 * (1 - medium_ratio) ** 0.5)
        low_score = max(0, 100 * (1 - low_ratio))
        
        # 各严重级别的权重（高严重性对最终分数影响更大）
        weights = {
            'high': 0.5,      # 高严重度权重
            'medium': 0.3,    # 中严重度权重
            'low': 0.2        # 低严重度权重
        }
        
        # 计算加权平均得分
        final_score = (
            high_score * weights['high'] +
            medium_score * weights['medium'] +
            low_score * weights['low']
        )
        
        return final_score
    
    def _calculate_violation_ratio(self):
        """计算违规占比"""
        total_violations = sum(self.results.get('violations', {}).values())
        total_lines = self.results.get('total_lines', 0)
        if total_lines > 0:
            return (total_violations / total_lines) * 100
        return 0.0

# 辅助函数：生成HTML格式的报告预览

def generate_html_preview(results):
    """生成HTML格式的报告预览"""
    generator = ReportGenerator(results)
    score = generator._calculate_score()
    
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