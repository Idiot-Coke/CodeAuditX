#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import subprocess
import logging
from src.parsers.base_parser import BaseParser

# 创建logger实例
logger = logging.getLogger(__name__)

class GoParser(BaseParser):
    def __init__(self, ruleset):
        super().__init__(ruleset)
        self.supported_extensions = ['.go']
        self.language_name = "Go"
        
        # 根据规则集设置具体的检查规则
        self.naming_patterns = {
            'function': self.rules.get('function_naming', '^[A-Z][a-zA-Z0-9]*$|^[a-z][a-zA-Z0-9]*$'),  # 大驼峰(导出)或小驼峰(非导出)
            'variable': self.rules.get('variable_naming', '^[a-z][a-z0-9]*$'),  # 小驼峰
            'type': self.rules.get('type_naming', '^[A-Z][a-zA-Z0-9]*$'),  # 大驼峰
            'constant': self.rules.get('constant_naming', '^[A-Z_][A-Z0-9_]*$')  # 全大写加下划线
        }
        
        self.max_line_length = self.rules.get('max_line_length', 100)
        self.expected_indent = self.rules.get('expected_indent', 4)
        self.min_comment_coverage = self.rules.get('min_comment_coverage', 0.1)
    
    def parse(self, file_content):
        """解析Go代码，提取基本信息"""
        try:
            # 提取函数、变量、类型和常量
            functions = self._extract_functions(file_content)
            variables = self._extract_variables(file_content)
            types = self._extract_types(file_content)
            constants = self._extract_constants(file_content)
            
            return {
                'functions': functions,
                'variables': variables,
                'types': types,
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
        """应用规则检查Go代码"""
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
        
        # 检查类型命名
        for type_info in parsed_data.get('types', []):
            violation = self._check_naming_convention(
                type_info['name'], 
                self.naming_patterns['type'], 
                '类型命名不规范'
            )
            if violation:
                violation['line'] = type_info['line']
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
        
        # 检查未使用的导入
        unused_import_violations = self._check_unused_imports(parsed_data['content'])
        violations.extend(unused_import_violations)
        
        # 检查大括号风格
        brace_style_violations = self._check_brace_style(parsed_data['content'])
        violations.extend(brace_style_violations)
        
        return violations
    
    def _extract_functions(self, file_content):
        """提取Go中的函数"""
        functions = []
        lines = file_content.split('\n')
        
        # 正则表达式匹配函数声明
        func_pattern = re.compile(r'func\s+(?:\(\w+\s+\*?\w+\)\s+)?([a-zA-Z0-9_]+)\s*\(')
        
        for i, line in enumerate(lines):
            matches = func_pattern.finditer(line)
            for match in matches:
                functions.append({
                    'name': match.group(1),
                    'line': i + 1
                })
        
        return functions
    
    def _extract_variables(self, file_content):
        """提取Go中的变量"""
        variables = []
        lines = file_content.split('\n')
        
        # 正则表达式匹配变量声明（简化版）
        var_patterns = [
            # var 声明
            re.compile(r'var\s+([a-z][a-z0-9]*)\s+(?:[\w\[\]\*]+)(?:\s*=|;)'),
            # 短变量声明
            re.compile(r'([a-z][a-z0-9]*)\s*:=')
        ]
        
        for i, line in enumerate(lines):
            for pattern in var_patterns:
                matches = pattern.finditer(line)
                for match in matches:
                    variables.append({
                        'name': match.group(1),
                        'line': i + 1
                    })
        
        return variables
    
    def _extract_types(self, file_content):
        """提取Go中的类型定义"""
        types = []
        lines = file_content.split('\n')
        
        # 正则表达式匹配类型定义
        type_pattern = re.compile(r'type\s+([A-Z][a-zA-Z0-9]*)\s+')
        
        for i, line in enumerate(lines):
            matches = type_pattern.finditer(line)
            for match in matches:
                types.append({
                    'name': match.group(1),
                    'line': i + 1
                })
        
        return types
    
    def _extract_constants(self, file_content):
        """提取Go中的常量"""
        constants = []
        lines = file_content.split('\n')
        
        # 正则表达式匹配常量定义
        const_patterns = [
            # const 声明
            re.compile(r'const\s+([A-Z_][A-Z0-9_]*)\s*='),
            # const 块内声明
            re.compile(r'\s+([A-Z_][A-Z0-9_]*)\s*=')
        ]
        
        # 标记是否在const块内
        in_const_block = False
        
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # 检查是否进入const块
            if stripped_line.startswith('const') and ('=' not in stripped_line or '(' in stripped_line):
                in_const_block = True
            # 检查是否离开const块
            elif in_const_block and stripped_line == '}':
                in_const_block = False
            
            for pattern in const_patterns:
                matches = pattern.finditer(line)
                for match in matches:
                    # 如果是const块内的声明，确保它是大写的
                    if not in_const_block or match.group(1).isupper():
                        constants.append({
                            'name': match.group(1),
                            'line': i + 1
                        })
        
        return constants
    
    def _check_unused_imports(self, file_content):
        """检查未使用的导入"""
        violations = []
        
        # 这是一个简化的检查，实际应用中可能需要更复杂的解析器
        # 检查是否有import块
        import_blocks = re.findall(r'import\s+(?:\(.*?\)|\S+)', file_content, re.DOTALL)
        
        if import_blocks:
            violations.append({
                'type': '可能存在未使用的导入',
                'message': 'Go编译器要求移除未使用的导入，请使用goimports工具进行检查'
            })
        
        return violations
    
    def _check_brace_style(self, file_content):
        """检查大括号风格是否规范"""
        violations = []
        lines = file_content.split('\n')
        
        # Go语言要求大括号在同一行（K&R风格）
        for i, line in enumerate(lines):
            # 检查函数、if、else、for、switch等语句的大括号
            brace_patterns = [
                re.compile(r'func\s+(?:\(\w+\s+\*?\w+\)\s+)?([a-zA-Z0-9_]+)\s*\(.*\)\s*$'),
                re.compile(r'(if|else|for|switch|select)\s*\([^)]*\)\s*$')
            ]
            
            for pattern in brace_patterns:
                match = pattern.match(line.strip())
                if match:
                    # 检查下一行是否以{开头
                    if i + 1 < len(lines) and lines[i + 1].strip().startswith('{'):
                        violations.append({
                            'type': '大括号风格不规范',
                            'message': 'Go语言要求将大括号放在同一行',
                            'line': i + 2
                        })
        
        return violations
    
    # 重写基类的扫描方法，增加对go fmt和go vet的集成支持
    def scan(self, file_path):
        """扫描Go文件，集成go fmt和go vet的检查结果"""
        try:
            # 调用基类的扫描方法获取基本违规信息
            violations = super().scan(file_path)
            
            # 尝试使用go工具链进行额外检查
            try:
                # 检查是否安装了Go
                if self._check_go_installed():
                    # 运行go fmt检查
                    fmt_violations = self._run_go_fmt_check(file_path)
                    violations.extend(fmt_violations)
                    
                    # 运行go vet检查
                    vet_violations = self._run_go_vet_check(file_path)
                    violations.extend(vet_violations)
            except Exception:
                # Go工具执行出错，跳过
                pass
            
            return violations
        except Exception as e:
            error_message = f"Go文件扫描失败: {str(e)}"
            logger.error(error_message)
            return [{
                'type': '扫描错误',
                'message': error_message,
                'line': 1
            }]
    
    def _check_go_installed(self):
        """检查是否安装了Go"""
        try:
            subprocess.run(['go', 'version'], check=True, capture_output=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _run_go_fmt_check(self, file_path):
        """使用go fmt检查文件格式"""
        violations = []
        
        try:
            # 运行go fmt检查
            result = subprocess.run(
                ['go', 'fmt', file_path],
                capture_output=True,
                text=True
            )
            
            # 如果go fmt返回了文件路径，说明文件格式不规范
            if result.stdout.strip() == file_path:
                violations.append({
                    'type': 'Go代码格式不规范',
                    'message': '文件格式不符合Go标准，请运行go fmt进行格式化'
                })
        except Exception:
            # 执行出错，跳过
            pass
        
        return violations
    
    def _run_go_vet_check(self, file_path):
        """使用go vet检查代码潜在问题"""
        violations = []
        
        try:
            # 运行go vet检查
            result = subprocess.run(
                ['go', 'vet', file_path],
                capture_output=True,
                text=True
            )
            
            # 解析go vet输出
            if result.returncode != 0 and result.stderr:
                # 简单解析输出，提取错误信息
                lines = result.stderr.split('\n')
                for line in lines:
                    if line.strip():
                        violations.append({
                            'type': 'go vet检查问题',
                            'message': line.strip()
                        })
        except Exception:
            # 执行出错，跳过
            pass
        
        return violations