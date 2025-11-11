#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入规则集定义
from .rulesets import all_rulesets, type_mapping

class RuleManager:
    """规则管理器，负责规则加载、解析和管理"""
    
    def __init__(self):
        """初始化规则管理器"""
        # 初始化规则集
        self.rulesets = {}
        self.custom_rules = {}
        
        # 规则存储路径
        self.custom_rules_dir = os.path.join(
            os.path.expanduser("~"), 
            ".codeauditx", 
            "custom_rules"
        )
        
        # 加载内置规则
        self._load_builtin_rules()
        
        # 加载自定义规则
        self._load_custom_rules()
        
        # 合并规则
        self.merge_custom_rules()
    
    def _load_builtin_rules(self):
        """加载内置规则"""
        try:
            # 验证规则集
            if all_rulesets and isinstance(all_rulesets, dict):
                self.rulesets = all_rulesets.copy()
                logging.info(f"内置规则已加载: {list(self.rulesets.keys())}")
            else:
                logging.warning("规则集为空或格式错误")
                # 使用后备规则集
                self.rulesets = self._define_fallback_rulesets()
        except ImportError as e:
            logging.error(f"导入规则集模块失败: {e}")
            # 定义基本规则集
            self.rulesets = self._define_fallback_rulesets()
        except Exception as e:
            logging.error(f"加载内置规则时发生错误: {e}")
            # 如果加载失败，创建基本的默认规则集
            self.rulesets = self._define_fallback_rulesets()
            logging.warning("使用默认后备规则集")
    
    def _define_fallback_rulesets(self):
        """定义后备规则集，确保在规则加载失败时有基本的规则可用"""
        fallback_rulesets = {
            'Google': {
                'python': {
                    'variable_naming': '^[a-z_][a-z0-9_]*$',
                    'function_naming': '^[a-z_][a-z0-9_]*$',
                    'class_naming': '^[A-Z][a-zA-Z0-9]*$',
                    'constant_naming': '^[A-Z_][A-Z0-9_]*$',
                    'max_line_length': 100,
                    'expected_indent': 4,
                    'min_comment_coverage': 0.1
                }
            },
            'PEP8': {
                'python': {
                    'variable_naming': '^[a-z_][a-z0-9_]*$',
                    'function_naming': '^[a-z_][a-z0-9_]*$',
                    'class_naming': '^[A-Z][a-zA-Z0-9]*$',
                    'constant_naming': '^[A-Z_][A-Z0-9_]*$',
                    'max_line_length': 79,
                    'expected_indent': 4
                }
            },
            'Airbnb': {},
            'Standard': {}
        }
        logging.debug("定义了后备规则集")
        return fallback_rulesets
    
    def _load_custom_rules(self):
        """加载自定义规则"""
        try:
            # 确保自定义规则目录存在
            os.makedirs(self.custom_rules_dir, exist_ok=True)
            
            # 遍历规则集
            for ruleset_name in all_rulesets.keys():
                rules_file = os.path.join(self.custom_rules_dir, f"{ruleset_name}.json")
                if os.path.exists(rules_file):
                    with open(rules_file, 'r', encoding='utf-8') as f:
                        self.custom_rules[ruleset_name] = json.load(f)
            
            logging.info(f"自定义规则已加载: {list(self.custom_rules.keys())}")
        except Exception as e:
            logging.error(f"加载自定义规则时发生错误: {e}")
            self.custom_rules = {}
    
    def get_rules_for_language(self, ruleset_name: str, language: str) -> Dict[str, Any]:
        """获取特定语言的规则
        
        Args:
            ruleset_name: 规则集名称
            language: 语言名称
        
        Returns:
            规则字典
        """
        if ruleset_name not in self.rulesets:
            return {}
        
        ruleset = self.rulesets[ruleset_name]
        
        # 获取全局规则
        global_rules = {k: v for k, v in ruleset.items() if k != "python" and k != "javascript" and \
                       k != "cpp" and k != "php" and k != "go" and k != "java"}
        
        # 获取语言特定规则
        if language in ruleset and isinstance(ruleset[language], dict):
            language_rules = ruleset[language]
        else:
            language_rules = {}
        
        # 合并全局规则和语言特定规则
        return {**global_rules, **language_rules}
    
    def save_custom_rule(self, rule_type: str, rule_name: str, rule_value: Any, \
                        language: str = "global") -> bool:
        """保存自定义规则
        
        Args:
            rule_type: 规则类型
            rule_name: 规则名称
            rule_value: 规则值
            language: 语言名称
        
        Returns:
            是否保存成功
        """
        try:
            # 获取当前配置的规则集（这里使用Google作为默认规则集）
            ruleset_name = "Google"
            
            # 确保规则集存在
            if ruleset_name not in self.custom_rules:
                self.custom_rules[ruleset_name] = {}
            
            # 确保语言规则存在
            if language not in self.custom_rules[ruleset_name]:
                self.custom_rules[ruleset_name][language] = {}
            
            # 保存规则
            self.custom_rules[ruleset_name][language][rule_name] = rule_value
            
            # 保存到文件
            self._save_custom_rules_to_file(ruleset_name)
            
            # 重新合并规则
            self.merge_custom_rules()
            
            logging.info(f"自定义规则已保存: {rule_name} = {rule_value}")
            return True
        except Exception as e:
            logging.error(f"保存自定义规则时发生错误: {e}")
            return False
    
    def _save_custom_rules_to_file(self, ruleset_name: str) -> None:
        """将自定义规则保存到文件"""
        try:
            rules_file = os.path.join(self.custom_rules_dir, f"{ruleset_name}.json")
            with open(rules_file, 'w', encoding='utf-8') as f:
                json.dump(self.custom_rules[ruleset_name], f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"保存自定义规则文件时发生错误: {e}")
    
    def validate_rule(self, rule_name: str, rule_value: str) -> bool:
        """验证规则是否有效
        
        Args:
            rule_name: 规则名称
            rule_value: 规则值
        
        Returns:
            规则是否有效
        """
        try:
            # 验证命名规则（正则表达式）
            if rule_name.endswith('_naming'):
                # 检查是否是有效的正则表达式
                re.compile(rule_value)
                return True
            
            # 验证整数值规则
            elif rule_name in ['max_line_length', 'expected_indent', 'max_empty_lines', \
                              'blank_lines_after_imports', 'blank_lines_before_class', \
                              'blank_lines_before_function']:
                value = int(rule_value)
                return value > 0
            
            # 验证浮点数值规则
            elif rule_name == 'min_comment_coverage':
                value = float(rule_value)
                return 0 <= value <= 1
            
            # 验证布尔值规则
            elif rule_name in ['allow_trailing_whitespace', 'allow_multiple_statements', \
                              'semicolon_required', 'enable_custom_rules']:
                return str(rule_value).lower() in ['true', 'false', 'yes', 'no', '1', '0']
            
            # 其他规则（字符串值）
            else:
                return isinstance(rule_value, str) and len(rule_value) > 0
        except:
            return False
    
    def merge_custom_rules(self) -> None:
        """合并自定义规则到主规则集中"""
        try:
            # 复制内置规则集
            self.rulesets = all_rulesets.copy()
            
            # 合并自定义规则
            for ruleset_name, ruleset in self.custom_rules.items():
                if ruleset_name in self.rulesets:
                    for language, language_rules in ruleset.items():
                        if language == "global":
                            # 合并全局规则
                            for rule_name, rule_value in language_rules.items():
                                self.rulesets[ruleset_name][rule_name] = rule_value
                        else:
                            # 合并语言特定规则
                            if language not in self.rulesets[ruleset_name]:
                                self.rulesets[ruleset_name][language] = {}
                            for rule_name, rule_value in language_rules.items():
                                self.rulesets[ruleset_name][language][rule_name] = rule_value
            
            logging.info("自定义规则已合并到主规则集")
        except Exception as e:
            logging.error(f"合并自定义规则时发生错误: {e}")

    def get_rules_for_ruleset(self, ruleset_name: str) -> Dict[str, Dict[str, Any]]:
        """获取指定规则集的所有规则
        
        Args:
            ruleset_name: 规则集名称
            
        Returns:
            包含所有语言规则的字典
        """
        try:
            # 检查规则集是否存在
            if ruleset_name not in self.rulesets:
                logging.warning(f"规则集 '{ruleset_name}' 不存在，返回默认规则")
                # 返回基本的默认规则集
                return {
                    'python': {
                        'variable_naming': '^[a-z_][a-z0-9_]*$',
                        'function_naming': '^[a-z_][a-z0-9_]*$',
                        'class_naming': '^[A-Z][a-zA-Z0-9]*$',
                        'constant_naming': '^[A-Z_][A-Z0-9_]*$',
                        'max_line_length': 100,
                        'expected_indent': 4,
                        'min_comment_coverage': 0.1
                    },
                    'javascript': {
                        'variable_naming': '^[a-z][a-zA-Z0-9]*$',
                        'function_naming': '^[a-z][a-zA-Z0-9]*$',
                        'class_naming': '^[A-Z][a-zA-Z0-9]*$',
                        'max_line_length': 100,
                        'expected_indent': 2
                    }
                }
            
            ruleset = self.rulesets[ruleset_name]
            
            # 如果规则集为空，添加默认规则
            if not ruleset:
                logging.warning(f"规则集 '{ruleset_name}' 为空，添加默认规则")
                return {
                    'python': {
                        'variable_naming': '^[a-z_][a-z0-9_]*$',
                        'function_naming': '^[a-z_][a-z0-9_]*$',
                        'class_naming': '^[A-Z][a-zA-Z0-9]*$',
                        'max_line_length': 100,
                        'expected_indent': 4
                    }
                }
            
            # 定义有效的语言名称列表
            valid_languages = ['python', 'javascript', 'cpp', 'php', 'go', 'java']
            
            # 复制规则集，正确区分语言规则和全局规则
            enhanced_ruleset = ruleset.copy()
            
            # 只对有效的语言名称进行规则验证
            for lang in valid_languages:
                if lang in enhanced_ruleset:
                    rules = enhanced_ruleset[lang]
                    # 验证语言规则是否为空或格式错误
                    if not rules or not isinstance(rules, dict):
                        logging.warning(f"语言 '{lang}' 的规则为空或格式错误，添加基本规则")
                        # 添加基本规则
                        if lang == 'python':
                            enhanced_ruleset[lang] = {
                                'variable_naming': '^[a-z_][a-z0-9_]*$',
                                'function_naming': '^[a-z_][a-z0-9_]*$',
                                'class_naming': '^[A-Z][a-zA-Z0-9]*$',
                                'max_line_length': 100,
                                'expected_indent': 4
                            }
                        elif lang == 'javascript':
                            enhanced_ruleset[lang] = {
                                'variable_naming': '^[a-z][a-zA-Z0-9]*$',
                                'function_naming': '^[a-z][a-zA-Z0-9]*$',
                                'max_line_length': 100,
                                'expected_indent': 2
                            }
                        else:
                            enhanced_ruleset[lang] = {}
            
            return enhanced_ruleset
            
        except Exception as e:
            logging.error(f"获取规则集时出错: {str(e)}")
            # 返回基本的默认规则集
            return {
                'python': {
                    'variable_naming': '^[a-z_][a-z0-9_]*$',
                    'function_naming': '^[a-z_][a-z0-9_]*$',
                    'class_naming': '^[A-Z][a-zA-Z0-9]*$',
                    'max_line_length': 100,
                    'expected_indent': 4
                }
            }

# 全局规则管理器实例
rule_manager = RuleManager()

def get_rules_for_language(ruleset_name: str, language: str) -> Dict[str, Any]:
    """获取特定语言的规则"""
    return rule_manager.get_rules_for_language(ruleset_name, language)

def save_custom_rule(rule_type: str, rule_name: str, rule_value: Any, language: str = "global") -> bool:
    """保存自定义规则"""
    return rule_manager.save_custom_rule(rule_type, rule_name, rule_value, language)

def validate_rule(rule_name: str, rule_value: str) -> bool:
    """验证规则是否有效"""
    return rule_manager.validate_rule(rule_name, rule_value)

def get_available_rulesets() -> List[str]:
    """获取可用的规则集"""
    return list(rule_manager.rulesets.keys())

def get_available_languages() -> List[str]:
    """获取可用的语言"""
    return ["global", "python", "javascript", "cpp", "php", "go", "java"]