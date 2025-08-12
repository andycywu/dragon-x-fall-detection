#!/usr/bin/env python3
"""
🌐 跨平台AI檢測系統
支持MacBook Pro M4和Snapdragon X Elite的統一接口
"""

import os
import platform
import logging
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import json

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlatformDetector:
    """平台檢測器"""
    
    @staticmethod
    def detect_platform() -> Dict[str, str]:
        """檢測當前運行平台"""
        system = platform.system().lower()
        machine = platform.machine().lower()
        processor = platform.processor().lower()
        
        platform_info = {
            "system": system,
            "machine": machine,
            "processor": processor,
            "platform_type": "unknown"
        }
        
        # MacBook Pro M4檢測
        if system == "darwin" and ("arm" in machine or "arm64" in machine):
            platform_info["platform_type"] = "mac_apple_silicon"
            platform_info["ai_accelerator"] = "apple_neural_engine"
            platform_info["primary_provider"] = "CoreMLExecutionProvider"
            
        # Snapdragon X Elite檢測
        elif "snapdragon" in processor.lower() or "qualcomm" in processor.lower():
            platform_info["platform_type"] = "snapdragon_x_elite"
            platform_info["ai_accelerator"] = "hexagon_npu"
            platform_info["primary_provider"] = "QNNExecutionProvider"
            
        # Windows ARM (可能的Snapdragon設備)
        elif system == "windows" and ("arm" in machine or "aarch64" in machine):
            platform_info["platform_type"] = "windows_arm"
            platform_info["ai_accelerator"] = "hexagon_npu"
            platform_info["primary_provider"] = "QNNExecutionProvider"
            
        # 通用x86/x64
        elif "x86" in machine or "amd64" in machine:
            platform_info["platform_type"] = "x86_generic"
            platform_info["ai_accelerator"] = "cpu_generic"
            platform_info["primary_provider"] = "CPUExecutionProvider"
        
        return platform_info

class ONNXRuntimeManager(ABC):
    """ONNX Runtime管理器抽象基類"""
    
    def __init__(self, platform_info: Dict[str, str]):
        self.platform_info = platform_info
        self.providers = []
        self.sessions = {}
        
    @abstractmethod
    def get_providers(self) -> List[str]:
        """獲取ONNX Runtime提供商列表"""
        pass
    
    @abstractmethod
    def optimize_session_options(self) -> Any:
        """優化會話選項"""
        pass

class MacONNXManager(ONNXRuntimeManager):
    """Mac平台ONNX Runtime管理器"""
    
    def get_providers(self) -> List[str]:
        """獲取Mac平台提供商"""
        try:
            import onnxruntime as ort
            available = ort.get_available_providers()
            
            providers = []
            if 'CoreMLExecutionProvider' in available:
                providers.append('CoreMLExecutionProvider')
                logger.info("✅ 啟用Apple Neural Engine加速")
            else:
                logger.warning("⚠️ CoreML提供商不可用")
            
            providers.append('CPUExecutionProvider')
            logger.info("✅ 添加CPU後備支援")
            
            return providers
            
        except ImportError:
            logger.error("❌ ONNX Runtime未安裝")
            return ['CPUExecutionProvider']
    
    def optimize_session_options(self) -> Any:
        """Mac平台會話優化"""
        try:
            import onnxruntime as ort
            
            session_options = ort.SessionOptions()
            session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            session_options.enable_cpu_mem_arena = True
            session_options.enable_mem_pattern = True
            
            # Mac特定優化
            session_options.add_session_config_entry("session.load_model_format", "ORT")
            
            return session_options
            
        except ImportError:
            return None

class SnapdragonONNXManager(ONNXRuntimeManager):
    """Snapdragon平台ONNX Runtime管理器"""
    
    def get_providers(self) -> List[str]:
        """獲取Snapdragon平台提供商"""
        try:
            import onnxruntime as ort
            available = ort.get_available_providers()
            
            providers = []
            if 'QNNExecutionProvider' in available:
                providers.append('QNNExecutionProvider')
                logger.info("✅ 啟用Qualcomm Hexagon NPU加速")
            else:
                logger.warning("⚠️ QNN提供商不可用，檢查QNN SDK安裝")
            
            providers.append('CPUExecutionProvider')
            logger.info("✅ 添加CPU後備支援")
            
            return providers
            
        except ImportError:
            logger.error("❌ ONNX Runtime未安裝")
            return ['CPUExecutionProvider']
    
    def optimize_session_options(self) -> Any:
        """Snapdragon平台會話優化"""
        try:
            import onnxruntime as ort
            
            session_options = ort.SessionOptions()
            session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            session_options.enable_cpu_mem_arena = True
            session_options.enable_mem_pattern = True
            
            # Snapdragon特定優化
            session_options.add_session_config_entry("session.load_model_format", "ORT")
            
            return session_options
            
        except ImportError:
            return None

class GenericONNXManager(ONNXRuntimeManager):
    """通用平台ONNX Runtime管理器"""
    
    def get_providers(self) -> List[str]:
        """獲取通用平台提供商"""
        try:
            import onnxruntime as ort
            available = ort.get_available_providers()
            
            providers = []
            
            # 嘗試CUDA
            if 'CUDAExecutionProvider' in available:
                providers.append('CUDAExecutionProvider')
                logger.info("✅ 啟用CUDA加速")
            
            # 嘗試DirectML (Windows)
            elif 'DmlExecutionProvider' in available:
                providers.append('DmlExecutionProvider')
                logger.info("✅ 啟用DirectML加速")
            
            providers.append('CPUExecutionProvider')
            logger.info("✅ 添加CPU後備支援")
            
            return providers
            
        except ImportError:
            logger.error("❌ ONNX Runtime未安裝")
            return ['CPUExecutionProvider']
    
    def optimize_session_options(self) -> Any:
        """通用平台會話優化"""
        try:
            import onnxruntime as ort
            
            session_options = ort.SessionOptions()
            session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            session_options.enable_cpu_mem_arena = True
            session_options.enable_mem_pattern = True
            
            return session_options
            
        except ImportError:
            return None

class CrossPlatformAIDetector:
    """跨平台AI檢測系統"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化跨平台檢測系統"""
        self.platform_info = PlatformDetector.detect_platform()
        self.config = self._load_config(config_path)
        self.onnx_manager = self._create_onnx_manager()
        self.qai_hub_enabled = self._check_qai_hub_availability()
        
        logger.info("🌐 初始化跨平台AI檢測系統...")
        self._log_platform_info()
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """載入配置文件"""
        default_config = {
            "mac_apple_silicon": {
                "model_path": "./models/mac",
                "batch_size": 1,
                "num_threads": 4,
                "enable_coreml": True
            },
            "snapdragon_x_elite": {
                "model_path": "./models/snapdragon", 
                "batch_size": 1,
                "num_threads": 8,
                "enable_qnn": True
            },
            "fallback": {
                "model_path": "./models/generic",
                "batch_size": 1,
                "num_threads": 2,
                "enable_acceleration": False
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"⚠️ 配置文件載入失敗: {e}")
        
        return default_config
    
    def _create_onnx_manager(self) -> ONNXRuntimeManager:
        """創建適合的ONNX Runtime管理器"""
        platform_type = self.platform_info["platform_type"]
        
        if platform_type == "mac_apple_silicon":
            return MacONNXManager(self.platform_info)
        elif platform_type in ["snapdragon_x_elite", "windows_arm"]:
            return SnapdragonONNXManager(self.platform_info)
        else:
            return GenericONNXManager(self.platform_info)
    
    def _check_qai_hub_availability(self) -> bool:
        """檢查QAI Hub可用性"""
        try:
            import qai_hub as hub
            api_token = os.getenv('QAI_HUB_API_TOKEN')
            return bool(api_token)
        except ImportError:
            logger.warning("⚠️ QAI Hub SDK未安裝")
            return False
    
    def _log_platform_info(self):
        """記錄平台信息"""
        logger.info(f"🖥️ 檢測到平台: {self.platform_info['platform_type']}")
        logger.info(f"💻 系統: {self.platform_info['system']}")
        logger.info(f"🔧 架構: {self.platform_info['machine']}")
        logger.info(f"🧠 AI加速器: {self.platform_info.get('ai_accelerator', 'Unknown')}")
        logger.info(f"⚡ 主要提供商: {self.platform_info.get('primary_provider', 'Unknown')}")
        logger.info(f"☁️ QAI Hub: {'✅ 可用' if self.qai_hub_enabled else '❌ 不可用'}")
    
    def get_platform_config(self) -> Dict[str, Any]:
        """獲取當前平台配置"""
        platform_type = self.platform_info["platform_type"]
        return self.config.get(platform_type, self.config["fallback"])
    
    def initialize_onnx_runtime(self) -> bool:
        """初始化ONNX Runtime"""
        try:
            providers = self.onnx_manager.get_providers()
            session_options = self.onnx_manager.optimize_session_options()
            
            logger.info(f"📋 可用提供商: {providers}")
            
            # 這裡可以載入實際的ONNX模型
            # self.load_models(providers, session_options)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ ONNX Runtime初始化失敗: {e}")
            return False
    
    def setup_qai_hub_integration(self) -> bool:
        """設置QAI Hub集成"""
        if not self.qai_hub_enabled:
            logger.warning("⚠️ QAI Hub不可用，跳過雲端集成")
            return False
        
        try:
            import qai_hub as hub
            
            # 獲取設備列表
            devices = hub.get_devices()
            logger.info(f"☁️ QAI Hub連接成功，可用設備: {len(devices)}")
            
            # 根據平台選擇目標設備
            platform_type = self.platform_info["platform_type"]
            if platform_type == "snapdragon_x_elite":
                # 優先選擇Snapdragon X設備
                target_devices = [d for d in devices if 'Snapdragon X' in d.name or 'X Elite' in d.name]
            else:
                # Mac開發環境下也可以選擇Snapdragon設備進行雲端測試
                target_devices = [d for d in devices if 'Snapdragon' in d.name]
            
            if target_devices:
                self.target_device = target_devices[0]
                logger.info(f"🎯 選擇目標設備: {self.target_device.name}")
            else:
                self.target_device = devices[0] if devices else None
                logger.info(f"🎯 使用預設設備: {self.target_device.name if self.target_device else 'None'}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ QAI Hub集成失敗: {e}")
            return False
    
    def get_deployment_strategy(self) -> Dict[str, Any]:
        """獲取部署策略"""
        platform_type = self.platform_info["platform_type"]
        
        strategies = {
            "mac_apple_silicon": {
                "development_mode": True,
                "primary_execution": "local_coreml",
                "cloud_testing": "qai_hub_validation",
                "model_source": "local_onnx_models",
                "optimization_target": "development_speed"
            },
            "snapdragon_x_elite": {
                "development_mode": False,
                "primary_execution": "local_qnn",
                "cloud_integration": "qai_hub_optimized",
                "model_source": "qai_hub_compiled_models",
                "optimization_target": "inference_performance"
            },
            "generic": {
                "development_mode": True,
                "primary_execution": "cpu_fallback",
                "cloud_testing": "qai_hub_validation",
                "model_source": "generic_onnx_models",
                "optimization_target": "compatibility"
            }
        }
        
        return strategies.get(platform_type, strategies["generic"])
    
    def generate_migration_report(self) -> Dict[str, Any]:
        """生成移植報告"""
        platform_config = self.get_platform_config()
        deployment_strategy = self.get_deployment_strategy()
        
        report = {
            "platform_analysis": {
                "current_platform": self.platform_info,
                "qai_hub_available": self.qai_hub_enabled,
                "onnx_providers": self.onnx_manager.get_providers(),
                "platform_config": platform_config
            },
            "deployment_strategy": deployment_strategy,
            "migration_readiness": {
                "mac_development": self.platform_info["platform_type"] == "mac_apple_silicon",
                "snapdragon_ready": self.qai_hub_enabled,
                "cross_platform_code": True,
                "hardware_abstraction": True
            },
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """生成建議"""
        recommendations = []
        platform_type = self.platform_info["platform_type"]
        
        if platform_type == "mac_apple_silicon":
            recommendations.extend([
                "🍎 在Mac上進行核心功能開發和測試",
                "☁️ 使用QAI Hub進行Snapdragon設備雲端驗證",
                "🔧 實現硬件抽象層以支持未來移植",
                "📊 建立性能基準以對比不同平台"
            ])
        elif platform_type == "snapdragon_x_elite":
            recommendations.extend([
                "🐉 啟用QNN加速獲得最佳性能",
                "⚡ 使用QAI Hub優化的模型",
                "📈 監控NPU使用率和性能指標",
                "🔄 建立與雲端的持續集成"
            ])
        else:
            recommendations.extend([
                "🖥️ 考慮升級到支持的平台",
                "☁️ 充分利用QAI Hub雲端資源",
                "⚡ 尋找合適的硬件加速選項"
            ])
        
        if not self.qai_hub_enabled:
            recommendations.append("🔑 配置QAI Hub API Token以啟用雲端功能")
        
        return recommendations

def main():
    """主函數：跨平台系統測試"""
    print("🌐 跨平台AI檢測系統分析")
    print("=" * 50)
    
    try:
        # 初始化跨平台檢測器
        detector = CrossPlatformAIDetector()
        
        # 初始化ONNX Runtime
        onnx_success = detector.initialize_onnx_runtime()
        
        # 設置QAI Hub
        qai_hub_success = detector.setup_qai_hub_integration()
        
        # 生成移植報告
        migration_report = detector.generate_migration_report()
        
        # 顯示結果
        print("\n📊 平台分析結果:")
        platform = migration_report["platform_analysis"]["current_platform"]
        print(f"   平台類型: {platform['platform_type']}")
        print(f"   AI加速器: {platform.get('ai_accelerator', 'Unknown')}")
        print(f"   ONNX Runtime: {'✅ 成功' if onnx_success else '❌ 失敗'}")
        print(f"   QAI Hub: {'✅ 成功' if qai_hub_success else '❌ 失敗'}")
        
        print("\n🚀 部署策略:")
        strategy = migration_report["deployment_strategy"]
        print(f"   執行模式: {strategy['primary_execution']}")
        print(f"   優化目標: {strategy['optimization_target']}")
        
        print("\n💡 建議:")
        for rec in migration_report["recommendations"]:
            print(f"   {rec}")
        
        # 保存報告
        with open('cross_platform_analysis.json', 'w') as f:
            json.dump(migration_report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📝 詳細報告已保存: cross_platform_analysis.json")
        print("✅ 跨平台分析完成！")
        
    except Exception as e:
        print(f"❌ 分析失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
