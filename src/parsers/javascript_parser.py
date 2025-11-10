#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
import subprocess
import sys
import logging
from src.parsers.base_parser import BaseParser

# 创建logger实例
logger = logging.getLogger(__name__)

class JavascriptParser(BaseParser):
    def __init__(self, ruleset):
        super().__init__(ruleset)
        self.supported_extensions = ['.js', '.jsx', '.ts', '.tsx']
        self.language_name = "JavaScript/TypeScript"
        
        # 根据规则集设置具体的检查规则
        self.naming_patterns = {
            'function': self.rules.get('function_naming', '^(function\s+)?[a-z][a-zA-Z0-9]*$|^(function\s+)?[_$][a-zA-Z0-9]*$'),  # 小驼峰或下划线/美元符号开头
            'variable': self.rules.get('variable_naming', '^[a-z][a-zA-Z0-9]*$|^_[a-zA-Z0-9]*$'),  # 小驼峰或下划线开头
            'class': self.rules.get('class_naming', '^[A-Z][a-zA-Z0-9]*$'),  # 大驼峰
            'constant': self.rules.get('constant_naming', '^[A-Z_][A-Z0-9_]*$')  # 全大写加下划线
        }
        
        self.max_line_length = self.rules.get('max_line_length', 120)
        self.expected_indent = self.rules.get('expected_indent', 2)  # JavaScript通常使用2空格缩进
        self.min_comment_coverage = self.rules.get('min_comment_coverage', 0.1)
    
    def parse(self, file_content):
        """解析JavaScript代码，提取基本信息"""
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
        """应用规则检查JavaScript代码"""
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
        
        # 检查分号使用
        semicolon_violations = self._check_semicolon_usage(parsed_data['content'])
        violations.extend(semicolon_violations)
        
        # 检查大括号风格
        brace_style_violations = self._check_brace_style(parsed_data['content'])
        violations.extend(brace_style_violations)
        
        return violations
    
    def _extract_functions(self, file_content):
        """提取JavaScript中的函数"""
        functions = []
        lines = file_content.split('\n')
        
        # 正则表达式匹配函数声明和函数表达式
        func_patterns = [
            # 函数声明: function funcName(...)
            re.compile(r'function\s+([a-zA-Z0-9_$]+)\s*\('),
            # 箭头函数表达式: const funcName = (...) => {}
            re.compile(r'const\s+([a-zA-Z0-9_$]+)\s*=\s*\([^)]*\)\s*=>')
        ]
        
        for i, line in enumerate(lines):
            for pattern in func_patterns:
                matches = pattern.finditer(line)
                for match in matches:
                    functions.append({
                        'name': match.group(1),
                        'line': i + 1
                    })
        
        return functions
    
    def _extract_variables(self, file_content):
        """提取JavaScript中的变量"""
        variables = []
        lines = file_content.split('\n')
        
        # 正则表达式匹配变量声明
        var_patterns = [
            re.compile(r'var\s+([a-zA-Z0-9_$]+)'),
            re.compile(r'let\s+([a-zA-Z0-9_$]+)')
        ]
        
        for i, line in enumerate(lines):
            for pattern in var_patterns:
                matches = pattern.finditer(line)
                for match in matches:
                    # 排除全大写的常量
                    if not match.group(1).isupper():
                        variables.append({
                            'name': match.group(1),
                            'line': i + 1
                        })
        
        return variables
    
    def _extract_classes(self, file_content):
        """提取JavaScript中的类"""
        classes = []
        lines = file_content.split('\n')
        
        # 正则表达式匹配类声明
        class_pattern = re.compile(r'class\s+([a-zA-Z0-9_$]+)')
        
        for i, line in enumerate(lines):
            matches = class_pattern.finditer(line)
            for match in matches:
                classes.append({
                    'name': match.group(1),
                    'line': i + 1
                })
        
        return classes
    
    def _extract_constants(self, file_content):
        """提取JavaScript中的常量"""
        constants = []
        lines = file_content.split('\n')
        
        # 正则表达式匹配常量声明
        const_pattern = re.compile(r'const\s+([A-Z_][A-Z0-9_]*)')
        
        for i, line in enumerate(lines):
            matches = const_pattern.finditer(line)
            for match in matches:
                constants.append({
                    'name': match.group(1),
                    'line': i + 1
                })
        
        return constants
    
    def _check_semicolon_usage(self, file_content):
        """检查分号使用是否规范"""
        # 首先检查规则集中是否要求使用分号
        semicolon_required = self.rules.get('semicolon_required', True)
        
        # 如果规则集明确指定不需要分号，则跳过分号检查
        if not semicolon_required:
            return []
        
        violations = []
        lines = file_content.split('\n')
        
        # 检查每行是否缺少分号（简化版）
        for i, line in enumerate(lines):
            # 跳过空行、注释行
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith('//') or stripped_line.startswith('/*'):
                continue
            
            # 跳过已经有分号的行
            if stripped_line.endswith(';'):
                continue
            
            # 检查是否是需要分号的语句
            if re.search(r'[\w\(\)\[\]\{\}\+\-\*/%\^&\|!]=[^=]|\w+\([^)]*\)|\w+\[.*\]|return|break|continue|throw', stripped_line):
                violations.append({
                    'type': '缺少分号',
                    'message': 'JavaScript语句应以分号结束',
                    'line': i + 1
                })
        
        return violations
    
    def _check_brace_style(self, file_content):
        """检查大括号风格是否规范"""
        violations = []
        lines = file_content.split('\n')
        
        # 检查大括号是否在同一行（K&R风格）
        for i, line in enumerate(lines):
            # 检查函数、if、else、for、while、switch等语句的大括号
            brace_patterns = [
                re.compile(r'(function\s+\w+\s*\([^)]*\)|if\s*\([^)]*\)|else|for\s*\([^)]*\)|while\s*\([^)]*\)|switch\s*\([^)]*\))\s*$')
            ]
            
            for pattern in brace_patterns:
                match = pattern.match(line.strip())
                if match:
                    # 检查下一行是否以{开头
                    if i + 1 < len(lines) and lines[i + 1].strip().startswith('{'):
                        violations.append({
                            'type': '大括号风格不规范',
                            'message': '建议使用K&R风格：将大括号放在同一行',
                            'line': i + 1
                        })
        
        return violations
    
    # 重写基类的扫描方法，增加对ESLint的集成支持
    def scan(self, file_path):
        """扫描JavaScript文件，集成ESLint的检查结果"""
        try:
            # 调用基类的扫描方法获取基本违规信息
            violations = super().scan(file_path)
            
            # 尝试使用ESLint进行额外检查
            try:
                # 检查是否安装了Node.js和ESLint
                if self._check_node_and_eslint_installed():
                    # 运行ESLint检查
                    eslint_violations = self._run_eslint_check(file_path)
                    violations.extend(eslint_violations)
            except Exception:
                # ESLint执行出错，跳过
                pass
            
            return violations
        except Exception as e:
            error_message = f"JavaScript文件扫描失败: {str(e)}"
            logger.error(error_message)
            return [{
                'type': '扫描错误',
                'message': error_message,
                'line': 1
            }]
    
    def _check_node_and_eslint_installed(self):
        """检查是否安装了Node.js和ESLint"""
        try:
            # 检查Node.js是否安装
            subprocess.run(['node', '--version'], check=True, capture_output=True)
            # 检查ESLint是否安装
            try:
                subprocess.run(['eslint', '--version'], check=True, capture_output=True)
                return True
            except (subprocess.SubprocessError, FileNotFoundError):
                # 尝试使用npx运行ESLint
                try:
                    result = subprocess.run(['npx', '--no-install', 'eslint', '--version'], 
                                           capture_output=True, text=True)
                    return 'ESLint' in result.stdout
                except Exception:
                    return False
        except Exception:
            return False
    
    def _run_eslint_check(self, file_path):
        """使用ESLint检查文件"""
        violations = []
        
        try:
            # 尝试使用ESLint的JSON输出格式运行检查
            result = subprocess.run(
                ['npx', '--no-install', 'eslint', file_path, '--format=json'],
                capture_output=True,
                text=True
            )
            
            # 解析ESLint输出
            if result.stdout:
                try:
                    eslint_results = json.loads(result.stdout)
                    
                    # 处理ESLint结果
                    for file_result in eslint_results:
                        if 'messages' in file_result:
                            for message in file_result['messages']:
                                if message.get('severity', 0) >= 2:  # 只关注错误和警告
                                    violations.append({
                                        'type': 'ESLint检查问题',
                                        'message': f"{message.get('ruleId', '未知规则')}: {message.get('message', '')}",
                                        'line': message.get('line', 0)
                                    })
                except json.JSONDecodeError:
                    # JSON解析失败，记录简单信息
                    if result.returncode != 0:
                        violations.append({
                            'type': 'ESLint检查问题',
                            'message': 'ESLint检测到代码规范问题'
                        })
        except Exception:
            # ESLint执行出错，跳过
            pass
        
        return violations