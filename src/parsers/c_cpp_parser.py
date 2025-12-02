#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import subprocess
import logging
from src.parsers.base_parser import BaseParser

# 创建logger实例
logger = logging.getLogger(__name__)

class CCppParser(BaseParser):
    def __init__(self, ruleset):
        super().__init__(ruleset)
        self.supported_extensions = ['.c', '.cc', '.cpp', '.cxx', '.h', '.hh', '.hpp', '.hxx']
        self.language_name = "C/C++"
        
        # 根据规则集设置具体的检查规则
        self.naming_patterns = {
            'function': self.rules.get('function_naming', '^[a-z][a-zA-Z0-9]*$'),  # 小驼峰或下划线风格
            'variable': self.rules.get('variable_naming', '^[a-z][a-zA-Z0-9]*$|^[a-z_][a-z0-9_]*$'),  # 小驼峰或下划线风格
            'class': self.rules.get('class_naming', '^[A-Z][a-zA-Z0-9]*$'),  # 大驼峰
            'constant': self.rules.get('constant_naming', '^[A-Z_][A-Z0-9_]*$')  # 全大写加下划线
        }
        
        self.max_line_length = self.rules.get('max_line_length', 100)
        self.expected_indent = self.rules.get('expected_indent', 4)
        self.min_comment_coverage = self.rules.get('min_comment_coverage', 0.1)
    
    def parse(self, file_content):
        """解析C/C++代码，提取基本信息"""
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
        """应用规则检查C/C++代码"""
        violations = []
        
        # 检查是否有解析错误
        if parsed_data.get('parse_error'):
            violations.append({
                'type': '代码解析错误',
                'message': parsed_data.get('error_message', '未知解析错误')
            })
            return violations
        
        # 检查函数命名
        allow_error_naming = self.rules.get('allow_error_naming', False)
        for func in parsed_data.get('functions', []):
            # 特殊处理：如果允许错误相关命名，且函数名包含Error或ERROR，则跳过检查
            if allow_error_naming and ('Error' in func['name'] or 'ERROR' in func['name']):
                continue
            
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
            # 特殊处理：如果允许错误相关命名，且变量名包含Error或ERROR，则跳过检查
            if allow_error_naming and ('Error' in var['name'] or 'ERROR' in var['name']):
                continue
                
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
        
        # 检查头文件包含顺序
        include_violation = self._check_include_order(parsed_data['content'])
        if include_violation:
            violations.append(include_violation)
        
        # 检查大括号风格
        brace_style_violations = self._check_brace_style(parsed_data['content'])
        violations.extend(brace_style_violations)
        
        # 检查命名空间使用
        namespace_violation = self._check_namespace_usage(parsed_data['content'])
        if namespace_violation:
            violations.append(namespace_violation)
        
        return violations
    
    def _extract_functions(self, file_content):
        """提取C/C++中的函数"""
        functions = []
        lines = file_content.split('\n')
        
        # 正则表达式匹配函数声明和定义（简化版）
        # 这是一个复杂的问题，实际应用中可能需要更复杂的解析器
        func_pattern = re.compile(r'(\w+(?:\s*<[^>]*>)?\s+)+(\w+)\s*\([^)]*\)\s*(?:const\s*)?\{?')
        
        for i, line in enumerate(lines):
            matches = func_pattern.finditer(line)
            for match in matches:
                # 排除类成员函数声明（在.h文件中）
                if 'class' not in line and 'struct' not in line:
                    functions.append({
                        'name': match.group(2),
                        'line': i + 1
                    })
        
        return functions
    
    def _extract_variables(self, file_content):
        """提取C/C++中的变量"""
        variables = []
        lines = file_content.split('\n')
        
        # 正则表达式匹配变量声明（简化版）
        var_patterns = [
            # 简单变量声明
            re.compile(r'(\w+(?:\s*<[^>]*>)?(?:\s+\*)?\s+)+([a-z_]\w*)\s*(?:=|;)'),
            # 数组声明
            re.compile(r'(\w+(?:\s*<[^>]*>)?\s+)+([a-z_]\w*)\s*\[[^\]]*\]\s*(?:=|;)')
        ]
        
        for i, line in enumerate(lines):
            # 跳过函数定义行
            if '(' in line and ')' in line and ('{' in line or ';' in line):
                continue
            
            for pattern in var_patterns:
                matches = pattern.finditer(line)
                for match in matches:
                    # 排除常量
                    if not match.group(2).isupper():
                        variables.append({
                            'name': match.group(2),
                            'line': i + 1
                        })
        
        return variables
    
    def _extract_classes(self, file_content):
        """提取C/C++中的类和结构体"""
        classes = []
        lines = file_content.split('\n')
        
        # 正则表达式匹配类和结构体声明
        class_pattern = re.compile(r'(class|struct)\s+(\w+)')
        
        for i, line in enumerate(lines):
            matches = class_pattern.finditer(line)
            for match in matches:
                classes.append({
                    'name': match.group(2),
                    'line': i + 1
                })
        
        return classes
    
    def _extract_constants(self, file_content):
        """提取C/C++中的常量"""
        constants = []
        lines = file_content.split('\n')
        
        # 正则表达式匹配常量定义
        const_patterns = [
            # const常量
            re.compile(r'const\s+(\w+(?:\s*<[^>]*>)?(?:\s+\*)?)\s+([A-Z_][A-Z0-9_]*)\s*='),
            # #define常量
            re.compile(r'#define\s+([A-Z_][A-Z0-9_]*)')
        ]
        
        for i, line in enumerate(lines):
            for pattern in const_patterns:
                matches = pattern.finditer(line)
                for match in matches:
                    constants.append({
                        'name': match.group(len(match.groups())),
                        'line': i + 1
                    })
        
        return constants
    
    def _check_include_order(self, file_content):
        """检查头文件包含顺序是否符合规范"""
        # 提取头文件包含顺序
        includes = []
        lines = file_content.split('\n')
        
        for i, line in enumerate(lines):
            if line.startswith('#include'):
                includes.append((line, i + 1))
        
        # 检查顺序是否符合规范：C标准库 -> C++标准库 -> 第三方库 -> 本地库
        # 这是一个简化的实现，实际情况可能更复杂
        std_c_pattern = re.compile(r'#include\s*<[a-z]')
        std_cpp_pattern = re.compile(r'#include\s*<[A-Z]')
        third_party_pattern = re.compile(r'#include\s*<\w')
        local_pattern = re.compile(r'#include\s*"')
        
        # 定义头文件类型顺序
        order = [std_c_pattern, std_cpp_pattern, third_party_pattern, local_pattern]
        
        for i in range(len(includes) - 1):
            current_include = includes[i][0]
            next_include = includes[i + 1][0]
            
            # 检查当前头文件类型
            current_type = None
            for j, pattern in enumerate(order):
                if pattern.match(current_include):
                    current_type = j
                    break
            
            # 检查下一个头文件类型
            next_type = None
            for j, pattern in enumerate(order):
                if pattern.match(next_include):
                    next_type = j
                    break
            
            # 如果顺序不正确
            if current_type is not None and next_type is not None and current_type > next_type:
                return {
                    'type': '头文件包含顺序不规范',
                    'message': '建议按照：C标准库 -> C++标准库 -> 第三方库 -> 本地库 的顺序包含头文件',
                    'line': includes[i + 1][1]
                }
        
        return None
    
    def _check_brace_style(self, file_content):
        """检查大括号风格是否规范"""
        violations = []
        lines = file_content.split('\n')
        
        # 检查大括号风格（Google C++ Style Guide推荐的风格）
        for i, line in enumerate(lines):
            # 检查函数、类、结构体定义的大括号
            brace_patterns = [
                re.compile(r'(\w+(?:\s*<[^>]*>)?\s+)+(\w+)\s*\([^)]*\)\s*(?:const\s*)?\{'),
                re.compile(r'(class|struct)\s+(\w+)\s*\{'),
                re.compile(r'(if|else|for|while|switch)\s*\([^)]*\)\s*\{')
            ]
            
            for pattern in brace_patterns:
                match = pattern.search(line)
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
    
    def _check_namespace_usage(self, file_content):
        """检查命名空间使用是否规范"""
        # 检查是否有using namespace std;的使用
        if 'using namespace std;' in file_content:
            return {
                'type': '命名空间使用不规范',
                'message': '不建议在头文件中使用using namespace std;，可能导致命名冲突'
            }
        
        return None
    
    # 重写基类的扫描方法，增加对cpplint的集成支持
    def scan(self, file_path):
        """扫描C/C++文件，集成cpplint的检查结果"""
        try:
            # 调用基类的扫描方法获取基本违规信息
            violations = super().scan(file_path)
            
            # 尝试使用cpplint进行额外检查
            try:
                # 检查是否安装了cpplint
                subprocess.run(['cpplint', '--version'], check=True, capture_output=True)
                
                # 运行cpplint检查
                result = subprocess.run(
                    ['cpplint', '--filter=-build/include_subdir,-build/header_guard', file_path],
                    capture_output=True,
                    text=True
                )
                
                # 解析cpplint输出
                if result.stdout:
                    cpplint_errors = self._parse_cpplint_output(result.stdout)
                    violations.extend(cpplint_errors)
            except (subprocess.SubprocessError, FileNotFoundError):
                # cpplint未安装，跳过这部分检查
                try:
                    # 尝试使用Python模块方式导入cpplint
                    import cpplint
                    # 这里可以直接调用cpplint的API进行检查，但为了简化，我们跳过这部分
                except ImportError:
                    pass
            
            return violations
        except Exception as e:
            error_message = f"C/C++文件扫描失败: {str(e)}"
            logger.error(error_message)
            return [{
                'type': '扫描错误',
                'message': error_message,
                'line': 1
            }]
    
    def _parse_cpplint_output(self, output):
        """解析cpplint的输出"""
        violations = []
        lines = output.split('\n')
        
        # 解析每一行输出
        for line in lines:
            if line.strip():
                violations.append({
                    'type': 'cpplint检查问题',
                    'message': line.strip()
                })
        
        return violations