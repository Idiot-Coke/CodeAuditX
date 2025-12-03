#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import subprocess
import logging
from src.parsers.base_parser import BaseParser

# 创建logger实例
logger = logging.getLogger(__name__)

class JavaParser(BaseParser):
    def __init__(self, ruleset):
        super().__init__(ruleset)
        self.supported_extensions = ['.java']
        self.language_name = "Java"
        
        # 根据规则集设置具体的检查规则
        self.naming_patterns = {
            'function': self.rules.get('function_naming', '^[a-z][a-zA-Z0-9]*$'),  # 小驼峰
            'variable': self.rules.get('variable_naming', '^[a-z][a-zA-Z0-9]*$'),  # 小驼峰
            'class': self.rules.get('class_naming', '^[A-Z][a-zA-Z0-9]*$'),  # 大驼峰
            'constant': self.rules.get('constant_naming', '^[A-Z_][A-Z0-9_]*$'),  # 全大写加下划线
            'package': self.rules.get('package_naming', '^[a-z]+(\.[a-z0-9]+)*$')  # 小写字母和数字
        }
        
        self.max_line_length = self.rules.get('max_line_length', 120)
        self.expected_indent = self.rules.get('expected_indent', 4)
        self.min_comment_coverage = self.rules.get('min_comment_coverage', 0.1)
    
    def parse(self, file_content):
        """解析Java代码，提取基本信息"""
        try:
            # 提取函数、变量、类和常量
            functions = self._extract_functions(file_content)
            variables = self._extract_variables(file_content)
            classes = self._extract_classes(file_content)
            constants = self._extract_constants(file_content)
            packages = self._extract_packages(file_content)
            
            return {
                'functions': functions,
                'variables': variables,
                'classes': classes,
                'constants': constants,
                'packages': packages,
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
        """应用规则检查Java代码"""
        violations = []
        
        # 检查是否有解析错误
        if parsed_data.get('parse_error'):
            violations.append({
                'type': '代码解析错误',
                'message': parsed_data.get('error_message', '未知解析错误')
            })
            return violations
        
        # 检查是否允许包含Error/ERROR的命名
        allow_error_naming = self.rules.get('allow_error_naming', False)
        
        # 检查函数命名
        for func in parsed_data.get('functions', []):
            # 如果允许包含Error/ERROR的命名且名称中包含这些词汇，则跳过检查
            if not (allow_error_naming and ('Error' in func['name'] or 'ERROR' in func['name'])):
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
            # 如果允许包含Error/ERROR的命名且名称中包含这些词汇，则跳过检查
            if not (allow_error_naming and ('Error' in var['name'] or 'ERROR' in var['name'])):
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
            # 如果允许包含Error/ERROR的命名且名称中包含这些词汇，则跳过检查
            if not (allow_error_naming and ('Error' in cls['name'] or 'ERROR' in cls['name'])):
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
            # 如果允许包含Error/ERROR的命名且名称中包含这些词汇，则跳过检查
            if not (allow_error_naming and ('Error' in const['name'] or 'ERROR' in const['name'])):
                violation = self._check_naming_convention(
                    const['name'], 
                    self.naming_patterns['constant'], 
                    '常量命名不规范'
                )
                if violation:
                    violation['line'] = const['line']
                    violations.append(violation)
        
        # 检查包命名
        for pkg in parsed_data.get('packages', []):
            # 包名通常不包含Error/ERROR，但为了一致性也添加检查
            if not (allow_error_naming and ('Error' in pkg['name'] or 'ERROR' in pkg['name'])):
                violation = self._check_naming_convention(
                    pkg['name'], 
                    self.naming_patterns['package'], 
                    '包命名不规范'
                )
                if violation:
                    violation['line'] = pkg['line']
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
        
        # 检查大括号风格
        brace_style_violations = self._check_brace_style(parsed_data['content'])
        violations.extend(brace_style_violations)
        
        # 检查import语句顺序
        import_violation = self._check_import_order(parsed_data['content'])
        if import_violation:
            violations.append(import_violation)
        
        return violations
    
    def _extract_functions(self, file_content):
        """提取Java中的方法"""
        functions = []
        lines = file_content.split('\n')
        
        # 正则表达式匹配方法声明
        func_pattern = re.compile(r'\s*(public|protected|private|static|final|abstract)?\s*(public|protected|private|static|final|abstract)?\s*(public|protected|private|static|final|abstract)?\s*(\w+(?:\<[^>]*\>)?(?:\[\])?)\s+([a-zA-Z0-9_]+)\s*\(')
        
        for i, line in enumerate(lines):
            matches = func_pattern.finditer(line)
            for match in matches:
                # 提取方法名（第五个捕获组）
                func_name = match.group(5)
                functions.append({
                    'name': func_name,
                    'line': i + 1
                })
        
        return functions
    
    def _extract_variables(self, file_content):
        """提取Java中的变量"""
        variables = []
        lines = file_content.split('\n')
        
        # 正则表达式匹配变量声明（简化版）
        var_patterns = [
            # 成员变量和局部变量
            re.compile(r'\s*(public|protected|private|static|final|volatile|transient)?\s*(public|protected|private|static|final|volatile|transient)?\s*(\w+(?:\<[^>]*\>)?(?:\[\])?)\s+([a-z][a-zA-Z0-9_]*)\s*(?:=|;)'),
            # 数组声明
            re.compile(r'\s*(\w+(?:\<[^>]*\>)?(?:\[\])?)\s+([a-z][a-zA-Z0-9_]*)\s*\[[^\]]*\]\s*(?:=|;)')
        ]
        
        for i, line in enumerate(lines):
            # 跳过方法定义行
            if '(' in line and ')' in line and ('{' in line or ';' in line):
                continue
            
            for pattern in var_patterns:
                matches = pattern.finditer(line)
                for match in matches:
                    # 提取变量名（最后一个捕获组）
                    var_name = match.group(len(match.groups()))
                    # 排除常量
                    if 'final' not in line or not var_name.isupper():
                        variables.append({
                            'name': var_name,
                            'line': i + 1
                        })
        
        return variables
    
    def _extract_classes(self, file_content):
        """提取Java中的类和接口"""
        classes = []
        lines = file_content.split('\n')
        
        # 正则表达式匹配类和接口声明
        class_pattern = re.compile(r'\s*(public|protected|private|abstract|final)?\s*(class|interface|enum)\s+([A-Z][a-zA-Z0-9]*)')
        
        for i, line in enumerate(lines):
            matches = class_pattern.finditer(line)
            for match in matches:
                classes.append({
                    'name': match.group(3),
                    'line': i + 1
                })
        
        return classes
    
    def _extract_constants(self, file_content):
        """提取Java中的常量"""
        constants = []
        lines = file_content.split('\n')
        
        # 正则表达式匹配常量定义
        const_pattern = re.compile(r'\s*(public|protected|private)?\s*static\s+final\s+(\w+(?:\<[^>]*\>)?(?:\[\])?)\s+([A-Z_][A-Z0-9_]*)\s*=')
        
        for i, line in enumerate(lines):
            matches = const_pattern.finditer(line)
            for match in matches:
                constants.append({
                    'name': match.group(3),
                    'line': i + 1
                })
        
        return constants
    
    def _extract_packages(self, file_content):
        """提取Java中的包声明"""
        packages = []
        lines = file_content.split('\n')
        
        # 正则表达式匹配包声明
        package_pattern = re.compile(r'package\s+([a-zA-Z0-9_.]+);')
        
        for i, line in enumerate(lines):
            matches = package_pattern.finditer(line)
            for match in matches:
                packages.append({
                    'name': match.group(1),
                    'line': i + 1
                })
        
        return packages
    
    def _check_brace_style(self, file_content):
        """检查大括号风格是否规范"""
        violations = []
        lines = file_content.split('\n')
        
        # 检查大括号风格（Google Java Style Guide推荐的风格）
        for i, line in enumerate(lines):
            # 检查类、方法、if、else、for、while、switch等语句的大括号
            brace_patterns = [
                re.compile(r'\s*(public|protected|private|abstract|final)?\s*(class|interface|enum)\s+([A-Z][a-zA-Z0-9]*)\s*$'),
                re.compile(r'\s*(public|protected|private|static|final|abstract)?\s*(public|protected|private|static|final|abstract)?\s*(public|protected|private|static|final|abstract)?\s*(\w+(?:\<[^>]*\>)?(?:\[\])?)\s+([a-zA-Z0-9_]+)\s*\([^)]*\)\s*(throws\s+[\w.]+\s*)*\s*$'),
                re.compile(r'\s*(if|else|for|while|switch)\s*\([^)]*\)\s*$')
            ]
            
            for pattern in brace_patterns:
                match = pattern.match(line.strip())
                if match and i + 1 < len(lines):
                    # Google风格要求大括号在同一行
                    # 检查是否有大括号单独占一行的情况
                    stripped_next_line = lines[i + 1].strip()
                    if stripped_next_line == '{':
                        violations.append({
                            'type': '大括号风格不规范',
                            'message': '建议使用Google风格：将大括号放在同一行',
                            'line': i + 2
                        })
        
        return violations
    
    def _check_import_order(self, file_content):
        """检查import语句顺序是否符合规范"""
        # 提取import语句
        imports = []
        lines = file_content.split('\n')
        
        for i, line in enumerate(lines):
            if line.startswith('import'):
                imports.append((line, i + 1))
        
        # 检查顺序是否符合规范：Java标准库 -> 第三方库 -> 静态导入
        # 这是一个简化的实现，实际情况可能更复杂
        java_lang_pattern = re.compile(r'import\s+java\.lang')
        java_std_pattern = re.compile(r'import\s+java\.')
        javax_pattern = re.compile(r'import\s+javax\.')
        third_party_pattern = re.compile(r'import\s+[a-zA-Z]')
        static_import_pattern = re.compile(r'import\s+static')
        
        # 定义import类型顺序
        order = [java_lang_pattern, java_std_pattern, javax_pattern, third_party_pattern, static_import_pattern]
        
        for i in range(len(imports) - 1):
            current_import = imports[i][0]
            next_import = imports[i + 1][0]
            
            # 检查当前import类型
            current_type = None
            for j, pattern in enumerate(order):
                if pattern.match(current_import):
                    current_type = j
                    break
            
            # 检查下一个import类型
            next_type = None
            for j, pattern in enumerate(order):
                if pattern.match(next_import):
                    next_type = j
                    break
            
            # 如果顺序不正确
            if current_type is not None and next_type is not None and current_type > next_type:
                return {
                    'type': 'import语句顺序不规范',
                    'message': '建议按照：Java标准库 -> 第三方库 -> 静态导入 的顺序组织import语句',
                    'line': imports[i + 1][1]
                }
        
        return None
    
    # 重写基类的扫描方法，增加对Checkstyle的集成支持
    def scan(self, file_path):
        """扫描Java文件，集成Checkstyle的检查结果"""
        try:
            # 调用基类的扫描方法获取基本违规信息
            violations = super().scan(file_path)
            
            # 尝试使用Checkstyle进行额外检查
            try:
                # 检查是否安装了Java
                if self._check_java_installed():
                    # 运行Checkstyle检查
                    checkstyle_violations = self._run_checkstyle_check(file_path)
                    violations.extend(checkstyle_violations)
            except Exception:
                # Checkstyle执行出错，跳过
                pass
            
            return violations
        except Exception as e:
            error_message = f"Java文件扫描失败: {str(e)}"
            logger.error(error_message)
            return [{
                'type': '扫描错误',
                'message': error_message,
                'line': 1
            }]
    
    def _check_java_installed(self):
        """检查是否安装了Java"""
        try:
            subprocess.run(['java', '--version'], check=True, capture_output=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _run_checkstyle_check(self, file_path):
        """使用Checkstyle检查文件"""
        violations = []
        
        try:
            # 检查是否安装了Checkstyle
            checkstyle_installed = False
            try:
                subprocess.run(['checkstyle', '-version'], check=True, capture_output=True)
                checkstyle_installed = True
            except (subprocess.SubprocessError, FileNotFoundError):
                # 尝试使用Java命令直接运行Checkstyle jar包
                pass
            
            if checkstyle_installed:
                # 运行Checkstyle检查，使用Google风格
                result = subprocess.run(
                    ['checkstyle', '-c', 'google_checks.xml', file_path],
                    capture_output=True,
                    text=True
                )
                
                # 解析Checkstyle输出
                if result.returncode != 0 and result.stdout:
                    # 简单解析输出，提取错误信息
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if line.strip() and 'ERROR' in line:
                            violations.append({
                                'type': 'Checkstyle检查问题',
                                'message': line.strip()
                            })
        except Exception:
            # Checkstyle执行出错，跳过
            pass
        
        return violations