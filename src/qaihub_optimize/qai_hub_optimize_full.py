#!/usr/bin/env python3
"""
QAI Hub Optimize Full - All-in-One 整合工具 (模組化版本)
支援 Compile、Profile、Infer、Demo、Test 等多模式入口
使用模組化架構，提高程式碼可維護性和重用性
"""
import argparse
import sys
import os
import time
from pathlib import Path
from dotenv import load_dotenv
import subprocess
import shutil
import re
import logging

# 匯入模組化組件
from modules.scanner import ModelScanner
from modules.conversion import ModelConverter
from modules.advanced_conversion import AdvancedModelConverter, get_advanced_converter
from modules.format_check import FormatChecker
from modules.qaihub_client import QAIHubClient
from modules.pipeline import QAIHubPipeline
from modules.job_monitor import QAIHubJobMonitor, get_job_monitor

# 匯入其他必要的功能模組
from practical_qai_hub_onnx import PracticalQAIHubONNX
from final_qai_hub_onnx_system import FinalQAIHubONNXSystem
from qai_hub_unified_detector import QAIHubUnifiedDetector, demo_qai_hub_detection, test_live_detection
from official_qai_hub_detector import OfficialQAIHubDetector, demo_official_qai_hub_detection

# 加載 .env 配置
load_dotenv()

# 獲取模型相關目錄
MODELS_BASE_DIR = os.getenv("MODELS_BASE_DIR")
ONNX_MODEL_DIR = os.path.join(MODELS_BASE_DIR, os.getenv("ONNX_MODEL_DIR"))
RAW_MODEL_DIR = os.path.join(MODELS_BASE_DIR, os.getenv("MODEL_SOURCE_DIR"))
OPTIMIZED_MODEL_DIR = os.path.join(MODELS_BASE_DIR, os.getenv("OPTIMIZED_MODEL_DIR"))


def get_models_dir():
    """取得 models 目錄路徑"""
    # 優先使用環境變數中的路徑
    models_base_dir = os.getenv('MODELS_BASE_DIR')
    if models_base_dir:
        return Path(models_base_dir)
    # 備用方案：使用相對路徑
    return Path(__file__).parent.parent / 'models'


# 新增檢查 .env 變數是否正確載入
if not MODELS_BASE_DIR or not ONNX_MODEL_DIR or not RAW_MODEL_DIR or not OPTIMIZED_MODEL_DIR:
    print("❌ .env 配置錯誤，請檢查以下變數是否正確設置：")
    print("   - MODELS_BASE_DIR")
    print("   - ONNX_MODEL_DIR")
    print("   - MODEL_SOURCE_DIR")
    print("   - OPTIMIZED_MODEL_DIR")
    sys.exit(1)


def ensure_directory_exists(directory):
    """
    確保目錄存在，若不存在則建立。

    Args:
        directory (str): 目錄路徑。

    Returns:
        None
    """
    try:
        if not os.path.exists(directory):
            print(f"📁 目錄不存在，正在建立: {directory}")
            os.makedirs(directory, exist_ok=True)
    except Exception as e:
        print(f"❌ 建立目錄失敗: {directory}，錯誤: {e}")
        sys.exit(1)


def run_compile():
    """編譯並最佳化模型（自動掃描 raw 目錄）"""
    print(f"\n[Compile] QAI Hub Compile Pipeline")
    
    # 使用 QAIHubPipeline 進行完整的編譯流程
    pipeline = QAIHubPipeline(get_models_dir())
    
    
    # 執行編譯流程，使用新的 job monitor 會自動處理狀態監控和模型下載
    # 自動掃描 raw 目錄並根據目標裝置支援決定來源類型
    # 使用 source 參數而不是 quantize
    success = pipeline.run_compile_pipeline(source='onnx')
    
    if success:
        # 檢查並顯示下載的優化模型
        downloaded_models = []
        for model_name, model_info in pipeline.qaihub_client.qai_hub_models.items():
            if model_info.get('optimized_model_downloaded', False):
                downloaded_models.append(model_name)
        
        if downloaded_models:
            print(f"\n💾 優化模型已下載到 src/models/qaihub_optimized/ ({len(downloaded_models)} 個):")
            for model_name in downloaded_models:
                model_path = pipeline.qaihub_client.qai_hub_models[model_name].get('optimized_model_path', '未知路徑')
                print(f"   - {model_name} -> {model_path}")
        else:
            print("\n⚠️  沒有下載優化模型，請檢查編譯任務是否成功完成")
        
        print(f"\n✅ Compile 完成！")
    else:
        print(f"\n❌ Compile 失敗！")


def run_profile():
    """進行模型效能分析（自動掃描 raw 目錄）"""
    print("\n[Profile] QAI Hub Profile Pipeline")
    
    # 使用 QAIHubPipeline 進行完整的分析流程
    pipeline = QAIHubPipeline(get_models_dir())
    
    # 執行分析流程，使用新的 job monitor 會自動處理狀態監控
    # 自動掃描 raw 目錄並根據目標裝置支援決定來源類型
    success = pipeline.run_profile_pipeline()
    
    if success:
        print(f"\n✅ Profile 完成！")
    else:
        print(f"\n❌ Profile 失敗！")


def run_infer():
    """進行模型推論測試"""
    print("\n[Infer] QAI Hub Inference Demo (Practical)")
    system = PracticalQAIHubONNX()
    system.load_mediapipe_models()
    print("(目前僅支援現有模型推論，無自動轉換)")
    print("\nInfer 完成！")


def run_demo():
    """啟動互動式 Demo"""
    print("\n[Demo] QAI Hub Unified Detection Demo")
    demo_qai_hub_detection()
    print("\nDemo 完成！")


def run_official():
    """官方模式（特殊用途）"""
    print("\n[Official] 官方 QAI Hub Detector Demo")
    demo_official_qai_hub_detection()
    print("\nOfficial Demo 完成！")


def run_test():
    """執行測試流程"""
    print("\n[Test] QAI Hub Unified Detector 測試 (Live)")
    test_live_detection()
    print("\nTest 完成！")


def run_compile_profile_jobs(source='dlc'):
    """批次編譯並分析多模型（自動處理多個模型）"""
    print(f"\n[Compile+Profile] QAI Hub Compile+Profile Pipeline (Full)")
    
    # 使用 pipeline 模組執行完整的編譯+分析流程，傳遞正確的基礎目錄
    pipeline = QAIHubPipeline(get_models_dir())
    pipeline.run_compile_profile_pipeline(do_infer=False)
    print("\nCompile+Profile Jobs 全部完成！")


def run_compile_profile(source='dlc'):
    """單一模型編譯與分析（針對單一模型）"""
    print(f"\n[Compile+Profile+Infer] QAI Hub Compile+Profile+Infer Pipeline (Full Run)")
    
    # 使用 pipeline 模組執行完整的編譯+分析+推論流程，傳遞正確的基礎目錄
    pipeline = QAIHubPipeline(get_models_dir())
    pipeline.run_compile_profile_pipeline(do_infer=True)
    print("\nCompile+Profile+Infer 完成！")


def run_link():
    """Link Job（模型串接）"""
    print(f"\n[Link] QAI Hub Link Job Pipeline")
    
    # 使用 QAIHubPipeline 進行模型串接流程
    pipeline = QAIHubPipeline(get_models_dir())
    
    # 這裡示範一個基本的串接配置範例
    # 實際使用時應該從配置文件或使用者輸入獲取
    link_config = {
        "models": [
            {
                "id": "DETECT_MODEL_ID",  # 需要替換為實際的模型 ID
                "alias": "detector"
            },
            {
                "id": "LANDMARK_MODEL_ID",  # 需要替換為實際的模型 ID
                "alias": "landmark"
            }
        ],
        "connections": [
            {
                "from": "detector:output_boxes",
                "to": "landmark:input_boxes"
            }
        ]
    }
    
    print("🔗 模型串接配置範例:")
    print(f"   - 模型數量: {len(link_config['models'])}")
    print(f"   - 連接數量: {len(link_config['connections'])}")
    
    # 提示使用者輸入實際的模型 ID
    print("\n⚠️  請注意：需要先完成模型的編譯，取得模型 ID 後才能進行串接")
    print("   請將配置中的 'DETECT_MODEL_ID' 和 'LANDMARK_MODEL_ID' 替換為實際的模型 ID")
    
    # 詢問使用者是否要使用範例配置或從文件載入
    response = input("\n是否要使用範例配置進行串接？(y/n): ").strip().lower()
    if response == 'y':
        # 提交串接任務
        link_job = pipeline.qaihub_client.submit_link_job(link_config, "fall_detection_pipeline")
        if link_job:
            print(f"\n✅ Link Job 提交成功！Job ID: {link_job.job_id}")
            print("   請等待串接任務完成...")
        else:
            print("\n❌ Link Job 提交失敗")
    else:
        print("\n⏭️ 跳過串接任務，請手動準備 link_config.json 後再執行")
    
    print("\nLink Job 流程完成！")


# 設定 logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger('qaihub_optimize')


def find_executable_in_venv(exe_name):
    """嘗試在專案 virtualenv 或系統 PATH 中尋找可執行檔。回傳完整路徑或 None。"""
    # 1. 檢查虛擬環境 .venv/bin
    venv_bin = Path(__file__).parent / '.venv' / 'bin'
    candidate = venv_bin / exe_name
    if candidate.exists():
        return str(candidate)
    # 2. 檢查當前環境 PATH
    which = shutil.which(exe_name)
    if which:
        return which
    return None


def convert_tflite_to_onnx_advanced(tflite_path, onnx_path):
    """
    使用進階轉換方法進行 TFLite 到 ONNX 轉換
    
    回傳值： (success: bool, err_msg: str)
    """
    try:
        converter = get_advanced_converter()
        tflite_path_obj = Path(tflite_path)
        onnx_dir = Path(onnx_path).parent
        
        result = converter.convert_tflite_to_onnx_fixed(tflite_path_obj, onnx_dir)
        
        if result["status"] == "ok":
            logger.info(f'轉換成功: {tflite_path} -> {onnx_path}')
            return True, result["message"]
        elif result["status"] == "warning":
            logger.warning(f'轉換完成但有警告: {tflite_path} -> {result["message"]}')
            return True, result["message"]
        else:
            logger.error(f'轉換失敗: {tflite_path} -> {result["message"]}')
            return False, result["message"]
            
    except Exception as e:
        logger.exception(f'執行轉換時發生例外: {str(e)}')
        return False, str(e)


# 替換原先的轉換函數
def convert_tflite_to_onnx(tflite_path, onnx_path):
    # 確保 onnx 目錄存在
    onnx_dir = os.path.dirname(onnx_path)
    try:
        os.makedirs(onnx_dir, exist_ok=True)
    except Exception as e:
        return False

    success, msg = convert_tflite_to_onnx_advanced(tflite_path, onnx_path)
    if not success:
        # 將錯誤寫入 log 檔，方便後續分析
        log_path = os.path.join(onnx_dir, 'conversion_errors.log')
        with open(log_path, 'a') as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {tflite_path} -> {msg}\n")
    return success


def main():
    parser = argparse.ArgumentParser(
        description=(
            """
    QAI Hub Optimize Full - All-in-One 整合工具 (模組化版本)

    用法 (Usage):
        python qai_hub_optimize_full.py <mode>

    可用子命令 (mode)：
        compile                編譯並最佳化模型（自動掃描 raw 目錄）
        profile                進行模型效能分析（自動掃描 raw 目錄）
        compile_profile_jobs   批次編譯並分析多模型（自動處理多個模型）（自動掃描 raw 目錄）
        compile_profile        單一模型編譯與分析（針對單一模型（自動掃描 raw 目錄））
        infer                  進行模型推論測試
        demo                   啟動互動式 Demo
        official               官方模式（特殊用途）
        test                   執行測試流程
        link                   Link Job（進階用途）

    範例 (Examples):
        python qai_hub_optimize_full.py compile
        python qai_hub_optimize_full.py profile

    說明：
        - 所有模型來源已統一自動從 raw 目錄取得，無需手動切換來源參數。
        - 各模式細節請參考 doc/QAI_HUB_README.md。
    """
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('mode', choices=['compile', 'profile', 'infer', 'demo', 'official', 'test', 'compile_profile_jobs', 'compile_profile', 'link'],
                        help="子命令: compile | profile | infer | demo | official | test | compile_profile_jobs | compile_profile | link")
    args = parser.parse_args()

    if args.mode == 'compile':
        run_compile()
    elif args.mode == 'profile':
        run_profile()
    elif args.mode == 'infer':
        run_infer()
    elif args.mode == 'demo':
        run_demo()
    elif args.mode == 'official':
        run_official()
    elif args.mode == 'test':
        run_test()
    elif args.mode == 'compile_profile_jobs':
        run_compile_profile_jobs()
    elif args.mode == 'compile_profile':
        run_compile_profile()
    elif args.mode == 'link':
        run_link()
    else:
        print("未知模式！")
        sys.exit(1)


# 在主程式中加入目錄檢查
if __name__ == "__main__":
    # 確保所有必要目錄存在
    # MODELS_BASE_DIR 必須為絕對路徑
    MODELS_BASE_DIR = os.path.expanduser(MODELS_BASE_DIR)
    ONNX_MODEL_DIR = os.path.join(MODELS_BASE_DIR, os.getenv("ONNX_MODEL_DIR"))
    RAW_MODEL_DIR = os.path.join(MODELS_BASE_DIR, os.getenv("MODEL_SOURCE_DIR"))
    OPTIMIZED_MODEL_DIR = os.path.join(MODELS_BASE_DIR, os.getenv("OPTIMIZED_MODEL_DIR"))
    
    ensure_directory_exists(MODELS_BASE_DIR)
    ensure_directory_exists(os.path.dirname(ONNX_MODEL_DIR) or ONNX_MODEL_DIR)
    ensure_directory_exists(ONNX_MODEL_DIR)
    ensure_directory_exists(RAW_MODEL_DIR)
    ensure_directory_exists(OPTIMIZED_MODEL_DIR)

    # 測試轉換流程
    tflite_model_path = os.path.join(RAW_MODEL_DIR, "face_detector.tflite")
    onnx_model_path = os.path.join(ONNX_MODEL_DIR, "face_detector.onnx")
    convert_tflite_to_onnx(tflite_model_path, onnx_model_path)

    try:
        main()
    except FileNotFoundError as e:
        print(f"❌ 發生錯誤: {e}")
    except Exception as e:
        print(f"❌ 未知錯誤: {e}")
