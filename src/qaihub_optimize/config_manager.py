#!/usr/bin/env python3
"""
配置管理模塊
管理環境變量和API配置
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# 配置日誌
logger = logging.getLogger(__name__)

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, env_file: Optional[str] = None):
        """初始化配置管理器"""
        self.project_root = Path(__file__).parent
        self.env_file = env_file or self.project_root / ".env"
        self.load_environment()
        self.setup_qai_hub_config()
        
    def load_environment(self):
        """加載環境變量"""
        if self.env_file.exists():
            load_dotenv(self.env_file)
            logger.info(f"已加載配置文件: {self.env_file}")
        else:
            logger.warning(f"配置文件不存在: {self.env_file}")
            
    def setup_qai_hub_config(self):
        """設置QAI Hub配置"""
        api_token = self.get_qai_hub_token()
        if api_token and api_token != "your_api_token_here":
            qai_config_dir = Path.home() / ".qai_hub"
            qai_config_dir.mkdir(exist_ok=True)
            config_file = qai_config_dir / "client.ini"
            config_content = f"""[default]
api_token = {api_token}

[api]
api_token = {api_token}
api_url = https://app.aihub.qualcomm.com
web_url = https://app.aihub.qualcomm.com
verbose = True
"""
            with open(config_file, 'w') as f:
                f.write(config_content)
            logger.info("QAI Hub配置文件已創建 (含 [default] 與 [api] section)")
        else:
            logger.warning("QAI Hub API Token未設置，請在.env文件中配置")
            
    def get_qai_hub_token(self) -> Optional[str]:
        """獲取QAI Hub API Token"""
        return os.getenv("QAI_HUB_API_TOKEN")
        
    def get_config(self, key: str, default: Any = None) -> Any:
        """獲取配置值"""
        return os.getenv(key, default)
        
    def get_bool_config(self, key: str, default: bool = False) -> bool:
        """獲取布爾配置值"""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
        
    def get_int_config(self, key: str, default: int = 0) -> int:
        """獲取整數配置值"""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default
            
    def get_float_config(self, key: str, default: float = 0.0) -> float:
        """獲取浮點配置值"""
        try:
            return float(os.getenv(key, str(default)))
        except ValueError:
            return default
            
    def get_detection_config(self) -> Dict[str, Any]:
        """獲取檢測相關配置"""
        return {
            'fall_threshold': self.get_float_config('FALL_DETECTION_THRESHOLD', 0.7),
            'body_angle_threshold': self.get_float_config('BODY_ANGLE_THRESHOLD', 30.0),
            'position_change_threshold': self.get_float_config('POSITION_CHANGE_THRESHOLD', 0.3),
            'enable_audio': self.get_bool_config('ENABLE_AUDIO_DETECTION', True),
            'whisper_model': self.get_config('WHISPER_MODEL_SIZE', 'tiny'),
            'sample_rate': self.get_int_config('AUDIO_SAMPLE_RATE', 16000)
        }
        
    def get_qai_hub_config(self) -> Dict[str, Any]:
        """獲取QAI Hub相關配置"""
        return {
            'api_token': self.get_qai_hub_token(),
            'base_url': self.get_config('QAI_HUB_BASE_URL', 'https://app.aihub.qualcomm.com'),
            'device_group': self.get_config('QAI_HUB_DEVICE_GROUP', 'default'),
            'enable_acceleration': self.get_bool_config('ENABLE_QAI_ACCELERATION', True),
            'optimization_level': self.get_config('MODEL_OPTIMIZATION_LEVEL', 'balanced'),
            'device_type': self.get_config('INFERENCE_DEVICE_TYPE', 'auto')
        }
        
    def get_web_config(self) -> Dict[str, Any]:
        """獲取Web界面配置"""
        return {
            'port': self.get_int_config('STREAMLIT_PORT', 8502),
            'host': self.get_config('STREAMLIT_HOST', '0.0.0.0'),
            'title': self.get_config('WEB_TITLE', '黑客松跌倒檢測系統')
        }
        
    def get_logging_config(self) -> Dict[str, Any]:
        """獲取日誌配置"""
        return {
            'level': self.get_config('LOG_LEVEL', 'INFO'),
            'file': self.get_config('LOG_FILE', 'logs/detection.log'),
            'enable_performance': self.get_bool_config('ENABLE_PERFORMANCE_LOGGING', True)
        }
        
    def validate_config(self) -> Dict[str, Any]:
        """驗證配置"""
        issues = []
        
        # 檢查QAI Hub配置
        if not self.get_qai_hub_token():
            issues.append("QAI_HUB_API_TOKEN 未設置")
        elif self.get_qai_hub_token() == "your_api_token_here":
            issues.append("請設置有效的 QAI_HUB_API_TOKEN")
            
        # 檢查數值範圍
        fall_threshold = self.get_float_config('FALL_DETECTION_THRESHOLD', 0.7)
        if not 0.0 <= fall_threshold <= 1.0:
            issues.append("FALL_DETECTION_THRESHOLD 應該在 0.0-1.0 範圍內")
            
        # 檢查模型大小
        whisper_model = self.get_config('WHISPER_MODEL_SIZE', 'tiny')
        valid_models = ['tiny', 'base', 'small', 'medium', 'large']
        if whisper_model not in valid_models:
            issues.append(f"WHISPER_MODEL_SIZE 應該是 {valid_models} 之一")
            
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }
        
    def display_config_status(self):
        """顯示配置狀態"""
        print("\n🔧 配置狀態檢查")
        print("=" * 40)
        
        # QAI Hub配置
        qai_config = self.get_qai_hub_config()
        print(f"📱 QAI Hub API Token: {'✅ 已設置' if qai_config['api_token'] and qai_config['api_token'] != 'your_api_token_here' else '❌ 未設置'}")
        print(f"🚀 硬件加速: {'✅ 啟用' if qai_config['enable_acceleration'] else '❌ 禁用'}")
        print(f"⚡ 優化級別: {qai_config['optimization_level']}")
        
        # 檢測配置
        detection_config = self.get_detection_config()
        print(f"🎯 跌倒閾值: {detection_config['fall_threshold']}")
        print(f"📐 角度閾值: {detection_config['body_angle_threshold']}°")
        print(f"🎤 音頻檢測: {'✅ 啟用' if detection_config['enable_audio'] else '❌ 禁用'}")
        
        # Web配置
        web_config = self.get_web_config()
        print(f"🌐 Web端口: {web_config['port']}")
        print(f"📊 界面標題: {web_config['title']}")
        
        # 驗證結果
        validation = self.validate_config()
        print(f"\n✅ 配置驗證: {'通過' if validation['valid'] else '失敗'}")
        
        if validation['issues']:
            print("⚠️  配置問題:")
            for issue in validation['issues']:
                print(f"  • {issue}")
                
        print("=" * 40)

# 全局配置實例
config = ConfigManager()

def get_config() -> ConfigManager:
    """獲取全局配置實例"""
    return config

def main():
    """測試配置管理器"""
    print("🔧 配置管理器測試")
    
    # 創建配置管理器
    config_manager = ConfigManager()
    
    # 顯示配置狀態
    config_manager.display_config_status()
    
    # 顯示所有配置
    print("\n📋 完整配置:")
    print(f"QAI Hub: {config_manager.get_qai_hub_config()}")
    print(f"檢測設置: {config_manager.get_detection_config()}")
    print(f"Web設置: {config_manager.get_web_config()}")
    print(f"日誌設置: {config_manager.get_logging_config()}")

if __name__ == "__main__":
    main()
