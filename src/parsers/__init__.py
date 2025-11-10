#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from src.parsers.base_parser import BaseParser

# 创建logger实例
logger = logging.getLogger(__name__)

# 动态导入所有解析器
_available_parsers = {
    'python': None,
    'cpp': None,  # 这里会映射到c_cpp_parser
    'php': None,
    'javascript': None,
    'go': None,
    'java': None
}

def get_parser_for_file(file_path, ruleset):
    """根据文件路径获取合适的解析器"""
    # 获取文件扩展名
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    # 根据扩展名选择解析器
    if ext == '.py':
        return _get_parser('python', ruleset)
    elif ext in ['.c', '.cpp', '.cc', '.h', '.hpp']:
        return _get_parser('cpp', ruleset)
    elif ext == '.php':
        return _get_parser('php', ruleset)
    elif ext in ['.js', '.jsx']:
        return _get_parser('javascript', ruleset)
    elif ext == '.go':
        return _get_parser('go', ruleset)
    elif ext == '.java':
        return _get_parser('java', ruleset)
    
    # 不支持的文件类型
    return None

def _get_parser(parser_name, ruleset):
    """延迟加载并返回指定的解析器"""
    if _available_parsers.get(parser_name) is None:
        try:
            # 动态导入解析器模块
            # 特殊处理C/C++解析器，因为文件名是c_cpp_parser.py
            if parser_name == 'cpp':
                module_name = 'src.parsers.c_cpp_parser'
                class_name = 'CCppParser'
            else:
                module_name = f'src.parsers.{parser_name}_parser'
                class_name = f'{parser_name.capitalize()}Parser'
            
            module = __import__(module_name, fromlist=[class_name])
            parser_class = getattr(module, class_name)
            _available_parsers[parser_name] = parser_class
        except ImportError:
            # 如果解析器模块不存在，返回None
            logger.error(f"无法导入解析器模块: src.parsers.{parser_name}_parser")
            return None
    
    # 创建并返回解析器实例
    parser_class = _available_parsers[parser_name]
    return parser_class(ruleset)

def register_parser(parser_name, parser_class):
    """注册自定义解析器"""
    _available_parsers[parser_name] = parser_class

def get_available_parsers():
    """获取所有可用的解析器"""
    return list(_available_parsers.keys())