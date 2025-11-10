# -*- coding: utf-8 -*-

import ast
import re
from src.parsers.base_parser import BaseParser

class PythonParser(BaseParser):
    def __init__(self, ruleset):
        super().__init__(ruleset)
        self.supported_extensions = ['.py']
        self.language_name = "Python"
        
        # 根据规则集设置具体的检查规则
        self.naming_patterns = {
            'function': self.rules.get('function_naming', '^[a-z_][a-z0-9_]*$'),  # 蛇形命名法
            'variable': self.rules.get('variable_naming', '^[a-z_][a-z0-9_]*$'),  # 蛇形命名法
            'class': self.rules.get('class_naming', '^[A-Z][a-zA-Z0-9]*$'),  # 驼峰命名法
            'constant': self.rules.get('constant_naming', '^[A-Z_][A-Z0-9_]*$')  # 全大写加下划线
        }
        
        self.max_line_length = self.rules.get('max_line_length', 100)
        self.expected_indent = self.rules.get('expected_indent', 4)
        self.min_comment_coverage = self.rules.get('min_comment_coverage', 0.1)
    
    def parse(self, file_content):
        """使用ast模块解析Python代码"""
        try:
            # 解析代码为AST
            tree = ast.parse(file_content)
            
            # 提取基本信息
            functions = []
            variables = []
            classes = []
            constants = []
            
            # 遍历AST，提取函数、变量、类和常量
            class NameExtractor(ast.NodeVisitor):
                def visit_FunctionDef(self, node):
                    functions.append({"name": node.name, "line": node.lineno})
                    self.generic_visit(node)
                
                def visit_ClassDef(self, node):
                    classes.append({"name": node.name, "line": node.lineno})
                    self.generic_visit(node)
                
                def visit_Name(self, node):
                    # 简单的变量检测，实际情况可能更复杂
                    if hasattr(node, 'name') and hasattr(node, 'ctx'):
                        if isinstance(node.ctx, ast.Store):
                            # 检查是否是常量（全大写）
                            if node.name.isupper() and '_' in node.name:
                                constants.append({"name": node.name, "line": node.lineno})
                            else:
                                variables.append({"name": node.name, "line": node.lineno})
                    self.generic_visit(node)
            
            # 执行提取
            extractor = NameExtractor()
            extractor.visit(tree)
            
            # 去重（基于名称）
            functions = list({f['name']: f for f in functions}.values())
            variables = list({v['name']: v for v in variables}.values())
            classes = list({c['name']: c for c in classes}.values())
            constants = list({con['name']: con for con in constants}.values())
            
            return {
                'ast': tree,
                'functions': functions,
                'variables': variables,
                'classes': classes,
                'constants': constants,
                'content': file_content
            }
        except SyntaxError as e:
            # 语法错误，返回基本信息
            return {
                'syntax_error': True,
                'error_message': str(e),
                'content': file_content
            }
        except Exception as e:
            # 其他错误
            return {
                'parse_error': True,
                'error_message': str(e),
                'content': file_content
            }
    
    def check_rules(self, parsed_data):
        """应用规则检查Python代码"""
        violations = []
        
        # 检查是否有解析错误
        if parsed_data.get('syntax_error') or parsed_data.get('parse_error'):
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
        
        # 检查是否使用了制表符进行缩进
        tab_violations = self._check_tab_indentation(parsed_data['content'])
        violations.extend(tab_violations)
        
        # 检查导入语句顺序
        import_violation = self._check_import_order(parsed_data['ast'])
        if import_violation:
            violations.append(import_violation)
        
        return violations
    
    def _check_tab_indentation(self, file_content):
        """检查是否使用了制表符进行缩进"""
        lines = file_content.split('\n')
        violations = []
        
        for i, line in enumerate(lines):
            # 检查行首是否有制表符
            if line.startswith('\t'):
                violations.append({
                    'type': '使用制表符缩进',
                    'message': 'Python代码应使用空格而非制表符进行缩进',
                    'line': i + 1
                })
        
        return violations
    
    def _check_import_order(self, ast_tree):
        """检查导入语句的顺序是否符合规范"""
        # 提取导入语句
        imports = []
        std_imports = []
        third_party_imports = []
        local_imports = []
        
        # 预定义的标准库模块（简化版本）
        std_modules = {
            'os', 'sys', 're', 'math', 'datetime', 'collections',
            'json', 'csv', 'io', 'random', 'itertools', 'functools'
        }
        
        for node in ast.iter_child_nodes(ast_tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                # 记录导入语句的行号和模块名
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name.split('.')[0]
                        imports.append((module_name, node.lineno))
                elif isinstance(node, ast.ImportFrom):
                    module_name = node.module.split('.')[0] if node.module else ''
                    imports.append((module_name, node.lineno))
        
        # 简单检查：标准库导入应在第三方库导入之前
        # 这是一个简化的实现，实际情况可能更复杂
        for i, (module_name, lineno) in enumerate(imports):
            if i > 0 and module_name in std_modules and imports[i-1][0] not in std_modules:
                return {
                    'type': '导入语句顺序不规范',
                    'message': f'标准库模块 {module_name} 应在第三方库导入之前',
                    'line': lineno
                }
        
        return None
    
    # 覆盖基类的方法，提供更详细的命名规范解释
    def _check_naming_convention(self, name, pattern, violation_type):
        """检查名称是否符合指定的正则表达式模式"""
        import re
        if not re.match(pattern, name):
            # 提供更详细的命名规范解释
            convention_explanation = {
                '函数命名不规范': '函数名称应使用蛇形命名法（全部小写字母，单词间用下划线分隔）',
                '变量命名不规范': '变量名称应使用蛇形命名法（全部小写字母，单词间用下划线分隔）',
                '类命名不规范': '类名称应使用驼峰命名法（首字母大写，其余单词首字母大写，无下划线）',
                '常量命名不规范': '常量名称应使用全大写字母，单词间用下划线分隔'
            }
            
            explanation = convention_explanation.get(violation_type, '命名不符合项目规范')
            return {
                'type': violation_type,
                'message': f"{explanation}: '{name}'",
                'line': -1  # 具体行号由子类提供
            }
        return None
    
    # 重写基类的扫描方法，增加对pycodestyle和pylint的集成支持
    def scan(self, file_path):
        """扫描Python文件，集成pycodestyle和pylint的检查结果，避免重复报告并确保行号正确"""
        try:
            # 调用基类的扫描方法获取基本违规信息
            violations = super().scan(file_path)
            
            # 记录已经发现的问题，用于去重
            existing_issues = set()
            for v in violations:
                # 使用问题类型和行号(如果有)作为唯一标识符
                issue_key = f"{v.get('type', '')}_{v.get('line', -1)}"
                existing_issues.add(issue_key)
            
            # 尝试使用pycodestyle进行额外检查，并获取详细行号信息
            try:
                    from pycodestyle import Checker
                    
                    # 创建一个简单的reporter函数来捕获错误
                    errors = []
                    
                    def pycodestyle_reporter(line_number, offset, text, check):
                        # 确保我们不会处理None对象
                        if text is None:
                            return
                        
                        # 解析错误信息，提取错误代码和描述
                        error_code = text.split(':')[0].strip() if text else 'Unknown'
                        error_desc = text.split(':', 1)[1].strip() if ':' in text else text if text else 'Unknown error'
                        
                        # 创建唯一键用于去重
                        issue_key = f"PEP 8规范违反_{line_number}"
                        if issue_key not in existing_issues:
                            errors.append({
                                'type': f'PEP 8规范违反 ({error_code})',
                                'message': f'{error_desc}',
                                'line': line_number
                            })
                            existing_issues.add(issue_key)
                    
                    # 创建一个简单的reporter类
                    class SimpleReporter:
                        def __init__(self):
                            self.errors = []
                        
                        def error(self, line_number, offset, text, check):
                            # 调用我们的reporter函数
                            pycodestyle_reporter(line_number, offset, text, check)
                        
                        # 确保这个类可以被调用
                        def __call__(self, *args, **kwargs):
                            pass
                    
                    # 使用pycodestyle检查文件
                    try:
                        reporter = SimpleReporter()
                        checker = Checker(file_path, reporter=reporter)
                        # 调用check_all方法，但处理可能的异常
                        try:
                            checker.check_all()
                        except Exception:
                            # 忽略check_all过程中可能出现的任何错误
                            pass
                        
                        # 添加pycodestyle发现的问题到违规列表
                        violations.extend(errors)
                    except Exception:
                        # 忽略整个pycodestyle检查过程中可能出现的任何错误
                        pass
                
            except ImportError:
                # pycodestyle未安装，跳过这部分检查
                pass
            
            # 尝试使用pylint进行额外检查
            try:
                from pylint.lint import Run
                from pylint.reporters.text import TextReporter
                import io
                
                # 捕获pylint的输出
                output_stream = io.StringIO()
                reporter = TextReporter(output_stream)
                
                # 运行pylint检查
                try:
                    Run([file_path, '--output-format=text', '--reports=n'], reporter=reporter, exit=False)
                    output = output_stream.getvalue()
                    
                    # 解析输出，提取详细错误信息
                    lines = output.split('\n')
                    for line in lines:
                        if ':' in line and any(code in line for code in ['C', 'R', 'W', 'E', 'F']):
                            # 尝试解析行号和错误信息
                            try:
                                parts = line.split(':')
                                if len(parts) >= 4:
                                    line_number = int(parts[1])
                                    error_type = parts[2].strip()
                                    error_msg = ':'.join(parts[3:]).strip()
                                    
                                    # 创建唯一键用于去重
                                    issue_key = f"Pylint检查问题_{line_number}"
                                    if issue_key not in existing_issues:
                                        violations.append({
                                            'type': f'Pylint检查问题 ({error_type})',
                                            'message': error_msg,
                                            'line': line_number
                                        })
                                        existing_issues.add(issue_key)
                            except (ValueError, IndexError):
                                # 解析失败，跳过
                                continue
                except Exception:
                    # pylint执行出错，跳过
                    pass
            except ImportError:
                # pylint未安装，跳过这部分检查
                pass
            
            return violations
        except Exception as e:
            raise Exception(f"Python文件扫描失败: {str(e)}")