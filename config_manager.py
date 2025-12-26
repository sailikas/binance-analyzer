"""
配置管理模块
"""
import json
import os

class ConfigManager:
    def __init__(self, config_file="app_config.json"):
        self.config_file = config_file
        self.default_config = {
            "MIN_CHANGE_PERCENT": 100.0,
            "LIQUIDITY_THRESHOLD_USDT": 1000000,
            "MAX_ANALYZE_SYMBOLS": 500,
            "CACHE_EXPIRY": 3600,
            "REQUEST_DELAY": 0.15,
            "schedule_enabled": False,
            "schedule_interval": 7200,
            "notify_on_change": True,
            "notify_on_complete": True,
            "auto_start": False,
            "keep_screen_on": False,
            "wifi_only": True,
            "serverchan_enabled": True,
            "serverchan_key": "",
            "serverchan_title": "币安分析完成",
            "serverchan_content": "找到 {count} 个符合条件的交易对",
            "auto_minimize": False,
            "minimize_delay": 0.5
        }
        self.config = self.load_config()
    
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    config = self.default_config.copy()
                    config.update(loaded)
                    return config
            except Exception as e:
                print(f"配置加载失败: {e}，使用默认配置")
                return self.default_config.copy()
        return self.default_config.copy()
    
    def save_config(self):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"配置保存失败: {e}")
            return False
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value, auto_save=True):
        self.config[key] = value
        if auto_save:
            return self.save_config()
        return True
    
    def reset_to_default(self):
        self.config = self.default_config.copy()
        return self.save_config()
    
    def set_batch(self, config_dict):
        """批量设置配置，一次性保存"""
        for key, value in config_dict.items():
            self.config[key] = value
        return self.save_config()
    
    def get_analyzer_config(self):
        return {
            "MIN_CHANGE_PERCENT": self.config["MIN_CHANGE_PERCENT"],
            "LIQUIDITY_THRESHOLD_USDT": self.config["LIQUIDITY_THRESHOLD_USDT"],
            "MAX_ANALYZE_SYMBOLS": self.config["MAX_ANALYZE_SYMBOLS"],
            "CACHE_EXPIRY": self.config["CACHE_EXPIRY"],
            "REQUEST_DELAY": self.config["REQUEST_DELAY"]
        }
