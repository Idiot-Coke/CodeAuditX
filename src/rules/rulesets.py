#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 代码规范规则集定义

# 全局通用规则
global_rules = {
    # 命名规范
    "function_naming": r"^[a-z_][a-z0-9_]*$",  # 小写字母和下划线
    "variable_naming": r"^[a-z_][a-z0-9_]*$",  # 小写字母和下划线
    "class_naming": r"^[A-Z][a-zA-Z0-9]*$",   # 大驼峰命名法
    "constant_naming": r"^[A-Z_][A-Z0-9_]*$",  # 全大写字母和下划线
    
    # 代码风格
    "max_line_length": 120,      # 最大行长度
    "expected_indent": 4,       # 预期缩进空格数
    "min_comment_coverage": 0.1,  # 最小注释覆盖率(10%)
    
    # 配置
    "allow_trailing_whitespace": False,  # 不允许行尾空格
    "allow_multiple_statements": False,  # 不允许一行多个语句
    "max_empty_lines": 2,       # 最大空行数
    "allow_error_naming": True,  # 允许包含Error/ERROR的命名
}

# Google 规则集
google_rules = {
    **global_rules,  # 继承全局规则
    
    # Python 特定规则
    "python": {
        "function_naming": r"^[a-z_][a-z0-9_]*$",  # 蛇形命名法
        "variable_naming": r"^[a-z_][a-z0-9_]*$",  # 蛇形命名法
        "class_naming": r"^[A-Z][a-zA-Z0-9]*$",   # 大驼峰命名法
        "constant_naming": r"^[A-Z_][A-Z0-9_]*$",  # 全大写字母和下划线
        "max_line_length": 120,      # 最大行长度
        "expected_indent": 4,       # 预期缩进空格数
        "min_comment_coverage": 0.15,  # 最小注释覆盖率(15%)
        "docstring_style": "google",  # Google风格的文档字符串
        "allow_error_naming": True,  # 允许包含Error/ERROR的命名
    },
    
    # JavaScript 特定规则
    "javascript": {
        "function_naming": r"^[a-z][a-zA-Z0-9]*$",  # 小驼峰命名法
        "variable_naming": r"^[a-z][a-zA-Z0-9]*$",  # 小驼峰命名法
        "class_naming": r"^[A-Z][a-zA-Z0-9]*$",   # 大驼峰命名法
        "constant_naming": r"^[A-Z_][A-Z0-9_]*$",  # 全大写字母和下划线
        "max_line_length": 120,      # 最大行长度
        "expected_indent": 2,       # 预期缩进空格数
        "min_comment_coverage": 0.1,  # 最小注释覆盖率(10%)
        "semicolon_required": True,  # 要求分号
        "allow_error_naming": True,  # 允许包含Error/ERROR的命名
    },
    
    # C/C++ 特定规则
    "cpp": {
        "function_naming": r"^[a-z][a-zA-Z0-9]*$",  # 小驼峰命名法（允许包含Error等词汇）
        "variable_naming": r"^[a-z][a-zA-Z0-9]*$",  # 小驼峰命名法
        "class_naming": r"^[A-Z][a-zA-Z0-9]*$",   # 大驼峰命名法
        "constant_naming": r"^[A-Z_][A-Z0-9_]*$",  # 全大写字母和下划线
        "max_line_length": 120,      # 最大行长度
        "expected_indent": 4,       # 预期缩进空格数
        "min_comment_coverage": 0.2,  # 最小注释覆盖率(20%)
        "header_guard_style": "include_guard",  # 头文件保护风格
        # 添加一个配置项来明确允许错误相关的命名
        "allow_error_naming": True,
    },
    
    # PHP 特定规则
    "php": {
        "function_naming": r"^[a-z_][a-z0-9_]*$",  # 蛇形命名法
        "variable_naming": r"^\$[a-z_][a-z0-9_]*$",  # 蛇形命名法，带$符号
        "class_naming": r"^[A-Z][a-zA-Z0-9]*$",   # 大驼峰命名法
        "constant_naming": r"^[A-Z_][A-Z0-9_]*$",  # 全大写字母和下划线
        "max_line_length": 120,     # 最大行长度
        "expected_indent": 4,       # 预期缩进空格数
        "min_comment_coverage": 0.1,  # 最小注释覆盖率(10%)
        "allow_error_naming": True,  # 允许包含Error/ERROR的命名
    },
    
    # Go 特定规则
    "go": {
        "function_naming": r"^[A-Z][a-zA-Z0-9]*$",  # 大驼峰命名法（导出函数）
        "variable_naming": r"^[a-z][a-zA-Z0-9]*$",  # 小驼峰命名法
        "type_naming": r"^[A-Z][a-zA-Z0-9]*$",      # 大驼峰命名法
        "constant_naming": r"^[A-Z_][A-Z0-9_]*$",  # 全大写字母和下划线
        "max_line_length": 120,     # 最大行长度
        "expected_indent": 4,       # 预期缩进空格数
        "min_comment_coverage": 0.1,  # 最小注释覆盖率(10%)
        "allow_error_naming": True,  # 允许包含Error/ERROR的命名
    },
    
    # Java 特定规则
    "java": {
        "function_naming": r"^[a-z][a-zA-Z0-9]*$",  # 小驼峰命名法
        "variable_naming": r"^[a-z][a-zA-Z0-9]*$",  # 小驼峰命名法
        "class_naming": r"^[A-Z][a-zA-Z0-9]*$",   # 大驼峰命名法
        "constant_naming": r"^[A-Z_][A-Z0-9_]*$",  # 全大写字母和下划线
        "max_line_length": 120,     # 最大行长度
        "expected_indent": 4,       # 预期缩进空格数
        "min_comment_coverage": 0.15,  # 最小注释覆盖率(15%)
        "allow_error_naming": True,  # 允许包含Error/ERROR的命名
    },
}

# PEP8 规则集 - 主要适用于 Python
pep8_rules = {
    **global_rules,  # 继承全局规则
    
    # Python 特定规则
    "python": {
        "function_naming": r"^[a-z_][a-z0-9_]*$",  # 蛇形命名法
        "variable_naming": r"^[a-z_][a-z0-9_]*$",  # 蛇形命名法
        "class_naming": r"^[A-Z][a-zA-Z0-9]*$",   # 大驼峰命名法
        "constant_naming": r"^[A-Z_][A-Z0-9_]*$",  # 全大写字母和下划线
        "max_line_length": 120,      # 最大行长度
        "expected_indent": 4,       # 预期缩进空格数
        "min_comment_coverage": 0.1,  # 最小注释覆盖率(10%)
        "blank_lines_after_imports": 2,  # 导入语句后空行数
        "blank_lines_before_class": 2,   # 类定义前空行数
        "blank_lines_before_function": 2,  # 函数定义前空行数
        "allow_error_naming": True,  # 允许包含Error/ERROR的命名
    },
    
    # 其他语言规则沿用全局规则
}

# Airbnb 规则集 - 主要适用于 JavaScript
airbnb_rules = {
    **global_rules,  # 继承全局规则
    
    # JavaScript 特定规则
    "javascript": {
        "function_naming": r"^[a-z][a-zA-Z0-9]*$",  # 小驼峰命名法
        "variable_naming": r"^[a-z][a-zA-Z0-9]*$",  # 小驼峰命名法
        "class_naming": r"^[A-Z][a-zA-Z0-9]*$",   # 大驼峰命名法
        "constant_naming": r"^[A-Z_][A-Z0-9_]*$",  # 全大写字母和下划线
        "max_line_length": 120,     # 最大行长度
        "expected_indent": 2,       # 预期缩进空格数
        "min_comment_coverage": 0.1,  # 最小注释覆盖率(10%)
        "semicolon_required": False,  # 不要求分号
        "arrow_function_preference": "always",  # 优先使用箭头函数
        "allow_error_naming": True,  # 允许包含Error/ERROR的命名
    },
    
    # 其他语言规则沿用全局规则
}

# Standard 规则集 - 主要适用于 JavaScript
standard_rules = {
    **global_rules,  # 继承全局规则
    
    # JavaScript 特定规则
    "javascript": {
        "function_naming": r"^[a-z][a-zA-Z0-9]*$",  # 小驼峰命名法
        "variable_naming": r"^[a-z][a-zA-Z0-9]*$",  # 小驼峰命名法
        "class_naming": r"^[A-Z][a-zA-Z0-9]*$",   # 大驼峰命名法
        "constant_naming": r"^[A-Z_][A-Z0-9_]*$",  # 全大写字母和下划线
        "max_line_length": 120,      # 最大行长度
        "expected_indent": 2,       # 预期缩进空格数
        "min_comment_coverage": 0.1,  # 最小注释覆盖率(10%)
        "semicolon_required": False,  # 不要求分号
        "quotes_style": "single",  # 单引号
        "allow_error_naming": True,  # 允许包含Error/ERROR的命名
    },
    
    # 其他语言规则沿用全局规则
}

# 所有规则集的映射
all_rulesets = {
    "Google": google_rules,
    "PEP8": pep8_rules,
    "Airbnb": airbnb_rules,
    "Standard": standard_rules
}

# 规则类型映射
type_mapping = {
    "naming": "命名规范",
    "style": "代码风格",
    "comment": "注释规范",
    "config": "配置规范"
}