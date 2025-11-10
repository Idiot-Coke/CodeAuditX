#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import logging
from typing import Dict, Any, Optional

class ConfigManager:
    """配置管理器，负责管理应用程序的配置设置"""
    
    # 默认配置路径
    DEFAULT_CONFIG_PATH = os.path.join(
        os.path.expanduser("~"), 
        ".codeauditx", 
        "config.json"
    )
    
    # 默认配置
    DEFAULT_CONFIG = {
        "ui": {
            "theme": "light",
            "font_size": 12,
            "show_log": True,
            "show_progress": True
        },
        "scanner": {
            "exclude_dirs": [
                ".git", ".svn", "__pycache__", "node_modules", "venv", 
                "env", ".env", "build", "dist", ".idea", ".vscode"
            ],
            "exclude_files": [
                "*.min.js", "*.min.css", "*.min.html", "*.swp", "*.tmp", 
                "*.temp", "*.cache", "*.log"
            ],
            "max_file_size": 5242880,  # 5MB
            "concurrency": 4
        },
        "report": {
            "default_format": "txt",
            "include_summary": True,
            "include_details": True,
            "output_dir": os.path.join(os.path.expanduser("~"), "Desktop", "CodeAuditX_Reports")
        },
        "rules": {
            "default_ruleset": "Google",
            "enable_custom_rules": True
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化配置管理器"""
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config = self.DEFAULT_CONFIG.copy()
        self._ensure_config_dir()
        self.load_config()
        
    def _ensure_config_dir(self):
        """确保配置文件目录存在"""
        config_dir = os.path.dirname(self.config_path)
        if not os.path.exists(config_dir):
            try:
                os.makedirs(config_dir, exist_ok=True)
            except Exception as e:
                logging.error(f"无法创建配置目录: {e}")
    
    def load_config(self):
        """从文件加载配置"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # 合并用户配置和默认配置
                    self._merge_configs(self.config, user_config)
                logging.info(f"配置已从 {self.config_path} 加载")
            else:
                # 如果配置文件不存在，创建默认配置文件
                self.save_config()
                logging.info(f"默认配置已保存到 {self.config_path}")
        except json.JSONDecodeError:
            logging.error(f"配置文件格式错误: {self.config_path}")
            # 备份损坏的配置文件
            if os.path.exists(self.config_path):
                backup_path = f"{self.config_path}.bak"
                try:
                    os.rename(self.config_path, backup_path)
                    logging.info(f"损坏的配置文件已备份到 {backup_path}")
                except Exception as e:
                    logging.error(f"无法备份损坏的配置文件: {e}")
            # 使用默认配置
            self.config = self.DEFAULT_CONFIG.copy()
            self.save_config()
        except Exception as e:
            logging.error(f"加载配置时发生错误: {e}")
    
    def save_config(self):
        """保存配置到文件"""
        try:
            # 确保配置目录存在
            self._ensure_config_dir()
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logging.info(f"配置已保存到 {self.config_path}")
        except Exception as e:
            logging.error(f"保存配置时发生错误: {e}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """获取配置项的值
        
        Args:
            key_path: 配置项的路径，使用点号分隔，例如 "ui.theme"
            default: 如果配置项不存在，返回的默认值
        
        Returns:
            配置项的值或默认值
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> bool:
        """设置配置项的值
        
        Args:
            key_path: 配置项的路径，使用点号分隔，例如 "ui.theme"
            value: 要设置的新值
        
        Returns:
            是否设置成功
        """
        keys = key_path.split('.')
        config_section = self.config
        
        try:
            # 导航到目标配置项的父级
            for key in keys[:-1]:
                if key not in config_section:
                    config_section[key] = {}
                config_section = config_section[key]
            
            # 设置值
            config_section[keys[-1]] = value
            return True
        except Exception as e:
            logging.error(f"设置配置项 {key_path} 时发生错误: {e}")
            return False
    
    def reset_to_default(self) -> None:
        """重置配置为默认值"""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save_config()
        logging.info("配置已重置为默认值")
    
    def _merge_configs(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        """合并两个配置字典
        
        Args:
            base: 基础配置字典
            update: 要合并的更新配置字典
        """
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                # 递归合并嵌套字典
                self._merge_configs(base[key], value)
            else:
                # 直接覆盖值
                base[key] = value
    
    def get_excluded_dirs(self) -> list:
        """获取排除的目录列表"""
        return self.get("scanner.exclude_dirs", [])
    
    def get_excluded_files(self) -> list:
        """获取排除的文件列表"""
        return self.get("scanner.exclude_files", [])
    
    def get_max_file_size(self) -> int:
        """获取最大文件大小限制"""
        return self.get("scanner.max_file_size", 5242880)  # 默认5MB
    
    def get_concurrency(self) -> int:
        """获取并发数量"""
        return self.get("scanner.concurrency", 4)
    
    def get_default_ruleset(self) -> str:
        """获取默认规则集"""
        return self.get("rules.default_ruleset", "Google")
    
    def is_custom_rules_enabled(self) -> bool:
        """检查是否启用自定义规则"""
        return self.get("rules.enable_custom_rules", True)

# 创建全局配置管理器实例
config_manager = ConfigManager()

def get_config() -> ConfigManager:
    """获取全局配置管理器实例"""
    return config_manager