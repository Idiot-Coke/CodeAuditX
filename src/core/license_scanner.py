#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
开源协议扫描模块
负责检测代码文件中的开源协议信息
"""

import re
import os
import json
from typing import Dict, List, Tuple


class LicenseScanner:
    """开源协议扫描器"""
    
    def __init__(self):
        # 从配置文件加载开源协议规则
        self.load_license_rules()
        self.results = {
            'licenses_by_file': {},  # 文件到协议的映射
            'licenses_summary': {},  # 协议统计
            'risk_summary': {'high': 0, 'medium': 0, 'low': 0},  # 风险统计
            'high_risk_files': []    # 高风险文件列表
        }
    
    def load_license_rules(self):
        """从配置文件加载开源协议规则"""
        # 获取配置文件路径
        config_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(config_dir, "core", "config", "license_rules.json")
        
        # 默认规则，当配置文件不存在时使用
        default_rules = {
            "license_patterns": [
                {
                    "name": "MIT",
                    "patterns": [r'MIT\s+License', r'Permission\s+is\s+hereby\s+granted,\s+free\s+of\s+charge'],
                    "risk_level": "low",
                    "description": "MIT许可证"
                },
                {
                    "name": "Apache-2.0",
                    "patterns": [r'Apache\s+License\s+v?2(\.0)?', r'Apache-2\.0'],
                    "risk_level": "low",
                    "description": "Apache 2.0许可证"
                },
                {
                    "name": "GPL-3.0",
                    "patterns": [r'GNU\s+General\s+Public\s+License\s+v?3(\.0)?', r'GPL\s+v?3(\.0)?'],
                    "risk_level": "high",
                    "description": "GPL 3.0许可证"
                }
            ],
            "risk_levels": {
                "low": {"description": "低风险", "color": "#4CAF50"},
                "medium": {"description": "中等风险", "color": "#FFC107"},
                "high": {"description": "高风险", "color": "#F44336"}
            }
        }
        
        # 尝试加载配置文件
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 转换配置格式
                    self.LICENSE_PATTERNS = {}
                    self.RISK_LEVELS = {'high': [], 'medium': [], 'low': []}
                    
                    for license_info in config.get("license_patterns", []):
                        # 编译正则表达式
                        regex_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in license_info["patterns"]]
                        self.LICENSE_PATTERNS[license_info["name"]] = regex_patterns
                        # 构建风险级别映射
                        risk_level = license_info["risk_level"]
                        if risk_level in self.RISK_LEVELS:
                            self.RISK_LEVELS[risk_level].append(license_info["name"])
            else:
                # 使用默认规则
                self.LICENSE_PATTERNS = {}
                self.RISK_LEVELS = {'high': [], 'medium': [], 'low': []}
                
                for license_info in default_rules["license_patterns"]:
                    # 编译正则表达式
                    regex_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in license_info["patterns"]]
                    self.LICENSE_PATTERNS[license_info["name"]] = regex_patterns
                    # 构建风险级别映射
                    risk_level = license_info["risk_level"]
                    if risk_level in self.RISK_LEVELS:
                        self.RISK_LEVELS[risk_level].append(license_info["name"])
        except Exception as e:
            print(f"加载许可证配置文件失败: {e}")
            # 如果加载失败，使用原始的硬编码规则
            self.LICENSE_PATTERNS = {
                'GPL-2.0': [re.compile(r'GNU\s+General\s+Public\s+License\s+v?2(\.0)?', re.IGNORECASE)],
                'MIT': [re.compile(r'MIT\s+License', re.IGNORECASE)],
                'Apache-2.0': [re.compile(r'Apache\s+License\s+v?2(\.0)?', re.IGNORECASE)]
            }
            self.RISK_LEVELS = {
                'high': ['GPL-2.0'],
                'medium': [],
                'low': ['MIT', 'Apache-2.0']
            }
    
    def scan_file(self, file_path: str) -> List[str]:
        """扫描单个文件中的开源协议
        
        Args:
            file_path: 文件路径
            
        Returns:
            找到的协议列表
        """
        detected_licenses = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # 只检查文件开头的几百行（通常注释在开头）
                # 提取前1000个字符进行检查，提高性能
                content_preview = content[:1000]
                
                for license_name, patterns in self.LICENSE_PATTERNS.items():
                    for pattern in patterns:
                        if pattern.search(content_preview):
                            detected_licenses.append(license_name)
                            break  # 一个协议只添加一次
        
        except Exception as e:
            # 如果文件无法读取，忽略
            pass
        
        return detected_licenses
    
    def scan_directory(self, directory_path: str) -> Dict:
        """扫描目录下所有文件的开源协议
        
        Args:
            directory_path: 目录路径
            
        Returns:
            扫描结果
        """
        # 重置结果
        self.results = {
            'licenses_by_file': {},
            'licenses_summary': {},
            'risk_summary': {'high': 0, 'medium': 0, 'low': 0},
            'high_risk_files': []
        }
        
        # 遍历目录
        for root, _, files in os.walk(directory_path):
            for file in files:
                # 跳过隐藏文件和二进制文件
                if file.startswith('.'):
                    continue
                
                file_path = os.path.join(root, file)
                
                # 只处理文本文件
                if self._is_text_file(file_path):
                    licenses = self.scan_file(file_path)
                    
                    if licenses:
                        # 保存文件的协议信息
                        self.results['licenses_by_file'][file_path] = licenses
                        
                        # 更新协议统计
                        for license_name in licenses:
                            self.results['licenses_summary'][license_name] = \
                                self.results['licenses_summary'].get(license_name, 0) + 1
                        
                        # 更新风险统计
                        for license_name in licenses:
                            risk_level = self._get_license_risk(license_name)
                            self.results['risk_summary'][risk_level] += 1
                        
                        # 检查是否包含高风险协议
                        if any(license_name in self.RISK_LEVELS['high'] for license_name in licenses):
                            self.results['high_risk_files'].append((file_path, licenses))
        
        return self.results
    
    def _get_license_risk(self, license_name: str) -> str:
        """获取协议的风险级别
        
        Args:
            license_name: 协议名称
            
        Returns:
            风险级别：high, medium, low
        """
        for risk, licenses in self.RISK_LEVELS.items():
            if license_name in licenses:
                return risk
        return 'low'  # 默认低风险
    
    def _is_text_file(self, file_path: str) -> bool:
        """检查文件是否为文本文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否为文本文件
        """
        try:
            # 读取文件的前2048个字节
            with open(file_path, 'rb') as f:
                chunk = f.read(2048)
                
                # 检查是否包含空字节（通常是二进制文件的特征）
                if b'\x00' in chunk:
                    return False
                
                # 检查文本编码
                # 如果大部分字节都在可打印字符范围内，认为是文本文件
                text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
                non_text = sum(1 for byte in chunk if byte not in text_chars)
                return non_text / len(chunk) < 0.3
        except Exception:
            return False