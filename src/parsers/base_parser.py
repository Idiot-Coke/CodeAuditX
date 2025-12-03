#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from src.rules import rule_manager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseParser:
    def __init__(self, ruleset):
        self.ruleset = ruleset
        self.supported_extensions = []
        self.language_name = "Unknown"
        
        # 导入对应的规则集
        self.rules = self._load_ruleset(ruleset)
        
        # 如果规则为空，使用默认规则
        if not self.rules:
            logger.warning(f"规则集 '{ruleset}' 为空或未找到，使用默认规则")
            self.rules = self._get_default_rules()
    
    def _load_ruleset(self, ruleset_name):
        """加载规则集"""
        try:
            logger.debug(f"尝试加载规则集: {ruleset_name}")
            
            # 首先尝试直接使用rule_manager.get_rules_for_language获取特定语言的规则
            # 这样可以确保正确应用规则集和语言的组合
            language_key = self.language_name.lower()
            logger.debug(f"当前解析器语言: {language_key}")
            
            # 尝试使用get_rules_for_language方法
            language_rules = rule_manager.get_rules_for_language(ruleset_name, language_key)
            
            if language_rules:
                logger.debug(f"直接从rule_manager获取到{language_key}的规则数量: {len(language_rules)}")
                return language_rules
            
            # 如果直接获取失败，尝试通过get_rules_for_ruleset获取整个规则集
            rules = rule_manager.get_rules_for_ruleset(ruleset_name)
            logger.debug(f"从规则管理器获取规则集: {ruleset_name}, 规则集是否存在: {rules is not None}")
            
            if rules and isinstance(rules, dict):
                # 尝试获取当前语言的规则
                language_rules = rules.get(language_key, {})
                
                # 如果找不到当前语言的规则，尝试一些可能的映射
                if not language_rules:
                    # 特殊处理一些可能的语言名称映射
                    language_mappings = {
                        'c': 'cpp',
                        'typescript': 'javascript',
                        'js': 'javascript',
                        'c++': 'cpp'
                    }
                    
                    mapped_lang = language_mappings.get(language_key)
                    if mapped_lang and mapped_lang in rules:
                        language_rules = rules.get(mapped_lang, {})
                        logger.debug(f"使用映射语言 {mapped_lang} 的规则")
                
                logger.debug(f"获取到的{language_key}规则数量: {len(language_rules)}")
                return language_rules
            else:
                logger.warning(f"规则集 '{ruleset_name}' 未返回有效规则")
        except Exception as e:
            logger.error(f"加载规则集时出错: {str(e)}")
        
        # 如果所有尝试都失败，返回空规则集
        logger.warning(f"无法加载规则集 '{ruleset_name}'，将使用默认规则")
        return {}
    
    def _get_default_rules(self):
        """获取默认规则，确保即使在规则加载失败时也能进行基本检查"""
        # 为不同语言提供基本规则
        default_rules = {
            'variable_naming': '^[a-z_][a-z0-9_]*$',
            'function_naming': '^[a-z_][a-z0-9_]*$',
            'class_naming': '^[A-Z][a-zA-Z0-9]*$',
            'constant_naming': '^[A-Z_][A-Z0-9_]*$',
            'max_line_length': 120,
            'expected_indent': 4,
            'min_comment_coverage': 0.1
        }
        
        logger.debug(f"使用默认规则: {default_rules.keys()}")
        return default_rules
    
    def can_parse(self, file_path):
        """检查是否可以解析该文件"""
        import os
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.supported_extensions
    
    def parse(self, file_content):
        """解析文件内容，返回结构化数据"""
        # 由子类实现
        return {}
    
    def check_rules(self, parsed_data):
        """应用规则检查，返回违规信息列表"""
        violations = []
        # 由子类实现具体的规则检查逻辑
        return violations
    
    def scan(self, file_path):
        """扫描文件并返回违规信息列表"""
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # 验证内容不为空
            if not content.strip():
                logger.warning(f"文件为空: {file_path}")
                return []
            
            # 解析文件内容
            parsed_data = self.parse(content)
            
            # 验证解析结果
            if not parsed_data:
                logger.warning(f"文件解析结果为空: {file_path}")
                parsed_data = {'content': content}
            
            # 确保content存在于解析结果中
            if 'content' not in parsed_data:
                parsed_data['content'] = content
            
            # 应用规则检查
            violations = self.check_rules(parsed_data)
            
            # 验证违规结果
            if isinstance(violations, list):
                # 如果没有检测到违规，尝试执行基本的检查作为后备
                if len(violations) == 0:
                    basic_violations = self._perform_basic_checks(content)
                    violations.extend(basic_violations)
                
                logger.debug(f"文件扫描完成: {file_path}, 发现 {len(violations)} 个违规")
                return violations
            else:
                logger.error(f"违规结果类型错误，应为列表: {type(violations)}")
                return []
        except UnicodeDecodeError as e:
            logger.error(f"文件编码错误: {file_path}, {str(e)}")
            # 返回编码错误作为一个违规
            return [{
                'type': '文件编码错误',
                'message': f'文件无法以UTF-8编码读取',
                'line': 1
            }]
        except Exception as e:
            logger.error(f"扫描文件时出错: {file_path}, {str(e)}")
            # 在生产环境中不抛出异常，而是返回一个错误违规
            return [{
                'type': '扫描错误',
                'message': f'文件扫描过程中发生错误: {str(e)}',
                'line': 1
            }]
    
    def _perform_basic_checks(self, content):
        """执行基本的代码检查，作为规则检查失败时的后备"""
        violations = []
        
        try:
            # 检查行长度
            lines = content.split('\n')
            max_length = self.rules.get('max_line_length', 120)
            
            for i, line in enumerate(lines, 1):
                if len(line) > max_length:
                    violations.append({
                        'type': '行长度过长',
                        'message': f'行长度超过{max_length}个字符',
                        'line': i
                    })
                    # 最多报告10个行长度问题，避免过多重复
                    if len(violations) >= 10:
                        break
            
            # 检查文件是否有注释
            if '#' not in content and '"""' not in content and "'''" not in content:
                violations.append({
                    'type': '缺少注释',
                    'message': '文件缺少注释说明',
                    'line': 1
                })
                
        except Exception as e:
            logger.error(f"执行基本检查时出错: {str(e)}")
        
        return violations
    
    def get_language(self):
        """获取解析器支持的语言名称"""
        return self.language_name
    
    # 辅助方法：检查命名规范
    def _check_naming_convention(self, name, pattern, violation_type):
        """检查名称是否符合指定的正则表达式模式"""
        import re
        if not re.match(pattern, name):
            return {
                'type': violation_type,
                'message': f"命名不符合规范: {name}",
                'line': -1  # 具体行号由子类提供
            }
        return None
    
    # 辅助方法：检查注释覆盖率
    def _check_comment_coverage(self, file_content, min_coverage=0.1):
        """检查文件的注释覆盖率是否达到要求"""
        import re
        
        # 去除字符串字面量，避免影响注释统计
        # 这是一个简化的实现，实际情况可能更复杂
        content = re.sub(r'"""(.*?)"""', '', file_content, flags=re.DOTALL)
        content = re.sub(r"'''(.*?)'''", '', content, flags=re.DOTALL)
        content = re.sub(r'"(.*?)"', '', content)
        content = re.sub(r"'(.*?)'", '', content)
        
        # 提取注释行
        lines = content.split('\n')
        total_lines = len(lines)
        comment_lines = 0
        
        in_multi_line_comment = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检查多行注释
            if in_multi_line_comment:
                comment_lines += 1
                if '*/' in line:
                    in_multi_line_comment = False
                continue
            
            # 检查单行注释和多行注释开始
            if line.startswith('#') or line.startswith('//'):
                comment_lines += 1
            elif '/*' in line:
                comment_lines += 1
                if '*/' not in line:
                    in_multi_line_comment = True
        
        # 计算注释覆盖率
        if total_lines == 0:
            coverage = 1.0
        else:
            coverage = comment_lines / total_lines
        
        # 检查是否达到最低覆盖率要求
        if coverage < min_coverage:
            return {
                'type': '注释覆盖率不足',
                'message': f"注释覆盖率: {coverage:.1%}, 要求: {min_coverage:.1%}",
                'line': -1
            }
        
        return None
    
    # 辅助方法：检查代码行长度
    def _check_line_length(self, file_content, max_length=100):
        """检查文件中的代码行长度是否符合规范"""
        lines = file_content.split('\n')
        violations = []
        
        for i, line in enumerate(lines):
            # 跳过注释行和空行
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith('#') or stripped_line.startswith('//'):
                continue
            
            # 检查行长度
            if len(line) > max_length:
                violations.append({
                    'type': '代码行过长',
                    'message': f"行长度: {len(line)}, 最大允许: {max_length}",
                    'line': i + 1
                })
        
        return violations
    
    # 辅助方法：检查缩进规范
    def _check_indentation(self, file_content, expected_indent=4):
        """检查文件中的缩进是否符合规范"""
        lines = file_content.split('\n')
        violations = []
        
        # 获取语言特定的缩进规则设置
        language_indent_settings = self.rules.get('indentation', {})
        strict_check = language_indent_settings.get('strict_check', False)
        
        for i, line in enumerate(lines):
            # 跳过空行和只有空格的行
            stripped_line = line.strip()
            if not stripped_line:
                continue
            
            # 计算缩进空格数
            indent_count = len(line) - len(line.lstrip(' '))
            
            # 对于缩进为0的行（如类定义、函数定义的第一行），不需要检查是否为倍数
            if indent_count > 0 and indent_count % expected_indent != 0:
                # 特殊处理1个空格缩进的情况
                if indent_count == 1:
                    # 对于JavaScript/TypeScript，如果不是严格检查模式，降低严重性
                    if self.language_name == "JavaScript/TypeScript" and not strict_check:
                        # 记录为低严重性警告，而不是错误
                        violations.append({
                            'type': '缩进不规范',
                            'message': f"缩进空格数: {indent_count}, 建议为{expected_indent}的倍数。注意：在某些JavaScript风格中，也可接受较小的缩进增量。",
                            'line': i + 1,
                            'severity': 'low'  # 添加严重性标记
                        })
                    else:
                        # 其他情况按照原来的规则处理
                        if stripped_line.startswith('#') or stripped_line.startswith('//'):
                            violations.append({
                                'type': '缩进不规范',
                                'message': f"注释行缩进空格数: {indent_count}, 建议为{expected_indent}的倍数",
                                'line': i + 1
                            })
                        else:
                            violations.append({
                                'type': '缩进不规范',
                                'message': f"缩进空格数: {indent_count}, 应为{expected_indent}的倍数",
                                'line': i + 1
                            })
                else:
                    # 对于注释行，可以适当放宽检查，但仍然记录警告
                    if stripped_line.startswith('#') or stripped_line.startswith('//'):
                        violations.append({
                            'type': '缩进不规范',
                            'message': f"注释行缩进空格数: {indent_count}, 建议为{expected_indent}的倍数",
                            'line': i + 1
                        })
                    else:
                        # 非注释行严格检查
                        violations.append({
                            'type': '缩进不规范',
                            'message': f"缩进空格数: {indent_count}, 应为{expected_indent}的倍数",
                            'line': i + 1
                        })
        
        return violations
    
    # 辅助方法：提取函数和变量名称
    def _extract_names(self, parsed_data):
        """从解析后的数据中提取函数和变量名称"""
        # 由子类实现
        return {'functions': [], 'variables': []}
    
    # 辅助方法：获取规则配置
    def _get_rule_config(self, rule_name, default=None):
        """获取特定规则的配置"""
        return self.rules.get(rule_name, default)
        
    def set_rules(self, rules):
        """动态设置规则"""
        self.rules = rules