#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import subprocess
import logging
from src.parsers.base_parser import BaseParser

# 创建logger实例
logger = logging.getLogger(__name__)

class PhpParser(BaseParser):
    def __init__(self, ruleset):
        super().__init__(ruleset)
        self.supported_extensions = ['.php']
        self.language_name = "PHP"
        
        # 根据规则集设置具体的检查规则
        self.naming_patterns = {
            'function': self.rules.get('function_naming', '^[a-z_][a-z0-9_]*$'),  # 蛇形命名法
            'variable': self.rules.get('variable_naming', '^\$[a-z_][a-z0-9_]*$'),  # 美元符号+蛇形命名法
            'class': self.rules.get('class_naming', '^[A-Z][a-zA-Z0-9]*$'),  # 大驼峰
            'constant': self.rules.get('constant_naming', '^[A-Z_][A-Z0-9_]*$')  # 全大写加下划线
        }
        
        self.max_line_length = self.rules.get('max_line_length', 120)
        self.expected_indent = self.rules.get('expected_indent', 4)
        self.min_comment_coverage = self.rules.get('min_comment_coverage', 0.1)
    
    def parse(self, file_content):
        """解析PHP代码，提取基本信息"""
        try:
            # 提取函数、变量、类和常量
            functions = self._extract_functions(file_content)
            variables = self._extract_variables(file_content)
            classes = self._extract_classes(file_content)
            constants = self._extract_constants(file_content)
            
            return {
                'functions': functions,
                'variables': variables,
                'classes': classes,
                'constants': constants,
                'content': file_content
            }
        except Exception as e:
            # 解析错误
            return {
                'parse_error': True,
                'error_message': str(e),
                'content': file_content
            }
    
    def check_rules(self, parsed_data):
        """应用规则检查PHP代码"""
        violations = []
        
        # 检查是否有解析错误
        if parsed_data.get('parse_error'):
            violations.append({
                'type': '代码解析错误',
                'message': parsed_data.get('error_message', '未知解析错误')
            })
            return violations
        
        # 检查函数命名
        for func in parsed_data.get('functions', []):
            violation = self._check_naming_convention(
                func['name'], 
                self.naming_patterns['function'], 
                '函数命名不规范'
            )
            if violation:
                violation['line'] = func['line']
                violations.append(violation)
        
        # 检查变量命名
        for var in parsed_data.get('variables', []):
            violation = self._check_naming_convention(
                var['name'], 
                self.naming_patterns['variable'], 
                '变量命名不规范'
            )
            if violation:
                violation['line'] = var['line']
                violations.append(violation)
        
        # 检查类命名
        for cls in parsed_data.get('classes', []):
            violation = self._check_naming_convention(
                cls['name'], 
                self.naming_patterns['class'], 
                '类命名不规范'
            )
            if violation:
                violation['line'] = cls['line']
                violations.append(violation)
        
        # 检查常量命名
        for const in parsed_data.get('constants', []):
            violation = self._check_naming_convention(
                const['name'], 
                self.naming_patterns['constant'], 
                '常量命名不规范'
            )
            if violation:
                violation['line'] = const['line']
                violations.append(violation)
        
        # 检查代码行长度
        line_violations = self._check_line_length(
            parsed_data['content'], 
            self.max_line_length
        )
        violations.extend(line_violations)
        
        # 检查缩进规范
        indent_violations = self._check_indentation(
            parsed_data['content'], 
            self.expected_indent
        )
        violations.extend(indent_violations)
        
        # 检查注释覆盖率
        comment_violation = self._check_comment_coverage(
            parsed_data['content'], 
            self.min_comment_coverage
        )
        if comment_violation:
            violations.append(comment_violation)
        
        # 检查闭合标签使用
        closing_tag_violation = self._check_closing_tag_usage(parsed_data['content'])
        if closing_tag_violation:
            violations.append(closing_tag_violation)
        
        # 检查短标签使用
        short_tag_violations = self._check_short_tag_usage(parsed_data['content'])
        violations.extend(short_tag_violations)
        
        return violations
    
    def _extract_functions(self, file_content):
        """提取PHP中的函数"""
        functions = []
        lines = file_content.split('\n')
        
        # 正则表达式匹配函数声明
        func_patterns = [
            # 普通函数: function func_name(...)
            re.compile(r'function\s+([a-zA-Z0-9_]+)\s*\('),
            # 类成员函数: public function func_name(...)
            re.compile(r'\s*(public|protected|private|static)?\s*(final|abstract)?\s*function\s+([a-zA-Z0-9_]+)\s*\(')
        ]
        
        for i, line in enumerate(lines):
            for pattern in func_patterns:
                matches = pattern.finditer(line)
                for match in matches:
                    # 提取函数名
                    func_name = match.group(len(match.groups()))
                    functions.append({
                        'name': func_name,
                        'line': i + 1
                    })
        
        return functions
    
    def _extract_variables(self, file_content):
        """提取PHP中的变量"""
        variables = []
        lines = file_content.split('\n')
        
        # 正则表达式匹配变量声明和使用
        # 注意：这会提取所有变量引用，可能会有重复
        var_pattern = re.compile(r'\$([a-zA-Z0-9_]+)')
        
        for i, line in enumerate(lines):
            matches = var_pattern.finditer(line)
            for match in matches:
                # 排除常量（全大写）
                var_name = '$' + match.group(1)
                if not match.group(1).isupper():
                    variables.append({
                        'name': var_name,
                        'line': i + 1
                    })
        
        # 去重（基于名称和行号）
        variables = list({(v['name'], v['line']): v for v in variables}.values())
        
        return variables
    
    def _extract_classes(self, file_content):
        """提取PHP中的类"""
        classes = []
        lines = file_content.split('\n')
        
        # 正则表达式匹配类声明
        class_pattern = re.compile(r'class\s+([a-zA-Z0-9_]+)')
        
        for i, line in enumerate(lines):
            matches = class_pattern.finditer(line)
            for match in matches:
                classes.append({
                    'name': match.group(1),
                    'line': i + 1
                })
        
        return classes
    
    def _extract_constants(self, file_content):
        """提取PHP中的常量"""
        constants = []
        lines = file_content.split('\n')
        
        # 正则表达式匹配常量定义
        const_patterns = [
            # define() 常量
            re.compile(r'define\s*\(\s*[\'"]([A-Z_][A-Z0-9_]*)[\'"]'),
            # const 常量
            re.compile(r'const\s+([A-Z_][A-Z0-9_]*)\s*=')
        ]
        
        for i, line in enumerate(lines):
            for pattern in const_patterns:
                matches = pattern.finditer(line)
                for match in matches:
                    constants.append({
                        'name': match.group(1),
                        'line': i + 1
                    })
        
        return constants
    
    def _check_closing_tag_usage(self, file_content):
        """检查PHP闭合标签使用是否规范"""
        # PSR-2规范建议在只包含PHP代码的文件中省略闭合标签
        if file_content.strip().endswith('?>'):
            # 检查文件是否只包含PHP代码
            # 这是一个简化的检查
            if ('<?php' in file_content and '?>' in file_content and \
                len(file_content.split('<?php')[1].split('?>')[0].strip()) > 0):
                return {
                    'type': '闭合标签使用不规范',
                    'message': 'PSR-2规范建议在只包含PHP代码的文件中省略闭合标签 ?>'
                }
        
        return None
    
    def _check_short_tag_usage(self, file_content):
        """检查PHP短标签使用是否规范"""
        violations = []
        lines = file_content.split('\n')
        
        # 检查是否使用了短标签（不包括 <?=）
        short_tag_pattern = re.compile(r'<\?\s')
        
        for i, line in enumerate(lines):
            if short_tag_pattern.search(line) and not line.strip().startswith('<?='):
                violations.append({
                    'type': '短标签使用不规范',
                    'message': 'PSR-2规范建议使用完整的PHP标签 <?php 而不是短标签 <?',
                    'line': i + 1
                })
        
        return violations
    
    # 重写基类的扫描方法，增加对PHP_CodeSniffer的集成支持
    def scan(self, file_path):
        """扫描PHP文件，集成PHP_CodeSniffer的检查结果"""
        try:
            # 调用基类的扫描方法获取基本违规信息
            violations = super().scan(file_path)
            
            # 尝试使用PHP_CodeSniffer进行额外检查
            try:
                # 检查是否安装了PHP和PHP_CodeSniffer
                if self._check_php_and_codesniffer_installed():
                    # 运行PHP_CodeSniffer检查
                    phpcs_violations = self._run_phpcs_check(file_path)
                    violations.extend(phpcs_violations)
            except Exception:
                # PHP_CodeSniffer执行出错，跳过
                pass
            
            return violations
        except Exception as e:
            error_message = f"PHP文件扫描失败: {str(e)}"
            logger.error(error_message)
            return [{
                'type': '扫描错误',
                'message': error_message,
                'line': 1
            }]
    
    def _check_php_and_codesniffer_installed(self):
        """检查是否安装了PHP和PHP_CodeSniffer"""
        try:
            # 检查PHP是否安装
            subprocess.run(['php', '--version'], check=True, capture_output=True)
            # 检查PHP_CodeSniffer是否安装
            try:
                subprocess.run(['phpcs', '--version'], check=True, capture_output=True)
                return True
            except (subprocess.SubprocessError, FileNotFoundError):
                # 尝试使用php命令运行PHP_CodeSniffer
                try:
                    result = subprocess.run(['php', '-m'], capture_output=True, text=True)
                    return 'phpcs' in result.stdout
                except Exception:
                    return False
        except Exception:
            return False
    
    def _run_phpcs_check(self, file_path):
        """使用PHP_CodeSniffer检查文件"""
        violations = []
        
        try:
            # 运行PHP_CodeSniffer检查，使用PSR2标准
            result = subprocess.run(
                ['phpcs', '--standard=PSR2', file_path],
                capture_output=True,
                text=True
            )
            
            # 解析PHP_CodeSniffer输出
            if result.returncode != 0 and result.stdout:
                # 简单解析输出，提取错误信息
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'ERROR' in line or 'WARNING' in line:
                        violations.append({
                            'type': 'PHP_CodeSniffer检查问题',
                            'message': line.strip()
                        })
        except Exception:
            # PHP_CodeSniffer执行出错，跳过
            pass
        
        return violations