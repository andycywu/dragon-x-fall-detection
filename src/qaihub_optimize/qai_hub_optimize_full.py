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
try:
    from dotenv import load_dotenv
except Exception:
    # If python-dotenv is not installed, provide a noop fallback so --help and static analysis work
    def load_dotenv(path=None):
        return None
import subprocess
import shutil
import re
import logging

# 嘗試匯入專案內模組；若匯入失敗，設為 None，並在使用時採取延遲匯入或友善提示
try:
    from modules.scanner import ModelScanner
    from modules.conversion import ModelConverter
    from modules.advanced_conversion import AdvancedModelConverter, get_advanced_converter
    from modules.format_check import FormatChecker
    from modules.qaihub_client import QAIHubClient
    from modules.pipeline import QAIHubPipeline
    from modules.job_monitor import QAIHubJobMonitor, get_job_monitor
except Exception:
    ModelScanner = None
    ModelConverter = None
    AdvancedModelConverter = None
    get_advanced_converter = None
    FormatChecker = None
    QAIHubClient = None
    QAIHubPipeline = None
    QAIHubJobMonitor = None
    get_job_monitor = None

try:
    from practical_qai_hub_onnx import PracticalQAIHubONNX
    from final_qai_hub_onnx_system import FinalQAIHubONNXSystem
    from qai_hub_unified_detector import QAIHubUnifiedDetector, demo_qai_hub_detection, test_live_detection
    from official_qai_hub_detector import OfficialQAIHubDetector, demo_official_qai_hub_detection
except Exception:
    PracticalQAIHubONNX = None
    FinalQAIHubONNXSystem = None
    QAIHubUnifiedDetector = None
    demo_qai_hub_detection = None
    test_live_detection = None
    OfficialQAIHubDetector = None
    demo_official_qai_hub_detection = None
import sys
from pathlib import Path
import json

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


# NOTE:
# .env 必要變數的檢查會延後到 main() 執行時進行，避免在 import 階段直接 sys.exit()
def validate_and_expand_env_vars():
    """
    驗證並展開必要的環境變數，若缺少則拋出 EnvironmentError (由呼叫端處理)
    此函式會更新 module-level 的路徑常數（MODELS_BASE_DIR, ONNX_MODEL_DIR, RAW_MODEL_DIR, OPTIMIZED_MODEL_DIR）
    """
    global MODELS_BASE_DIR, ONNX_MODEL_DIR, RAW_MODEL_DIR, OPTIMIZED_MODEL_DIR
    MODELS_BASE_DIR = os.getenv("MODELS_BASE_DIR")
    if MODELS_BASE_DIR:
        MODELS_BASE_DIR = os.path.expanduser(MODELS_BASE_DIR)
        ONNX_MODEL_DIR = os.path.join(MODELS_BASE_DIR, os.getenv("ONNX_MODEL_DIR") or "")
        RAW_MODEL_DIR = os.path.join(MODELS_BASE_DIR, os.getenv("MODEL_SOURCE_DIR") or "")
        OPTIMIZED_MODEL_DIR = os.path.join(MODELS_BASE_DIR, os.getenv("OPTIMIZED_MODEL_DIR") or "")

    if not MODELS_BASE_DIR or not ONNX_MODEL_DIR or not RAW_MODEL_DIR or not OPTIMIZED_MODEL_DIR:
        raise EnvironmentError(
            "缺少必要的 .env 設定：MODELS_BASE_DIR / ONNX_MODEL_DIR / MODEL_SOURCE_DIR / OPTIMIZED_MODEL_DIR"
        )


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
    # 延遲匯入 QAIHubPipeline
    if QAIHubPipeline is None:
        print('❌ QAIHubPipeline 模組不可用，請確認 modules/pipeline.py 是否存在')
        return False
    pipeline = QAIHubPipeline(get_models_dir())

    # 執行編譯流程
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
    if QAIHubPipeline is None:
        print('❌ QAIHubPipeline 模組不可用，請確認 modules/pipeline.py 是否存在')
        return False
    pipeline = QAIHubPipeline(get_models_dir())
    success = pipeline.run_profile_pipeline()
    
    if success:
        print(f"\n✅ Profile 完成！")
    else:
        print(f"\n❌ Profile 失敗！")


def run_infer():
    """進行模型推論測試"""
    print("\n[Infer] QAI Hub Inference Demo (Practical)")
    if PracticalQAIHubONNX is None:
        print('❌ PracticalQAIHubONNX 不可用，請確認模組是否存在')
        return
    system = PracticalQAIHubONNX()
    system.load_mediapipe_models()
    print("(目前僅支援現有模型推論，無自動轉換)")
    print("\nInfer 完成！")


def run_demo():
    """啟動互動式 Demo"""
    print("\n[Demo] QAI Hub Unified Detection Demo")
    # existing interactive demo (if available)
    try:
        if demo_qai_hub_detection is None:
            raise RuntimeError('demo_qai_hub_detection not available')
        demo_qai_hub_detection()
    except Exception as e:
        print('Warning: demo_qai_hub_detection failed or not available:', e)

    # Run quick ONNX runner (quick 20 images/videos)
    try:
        repo_root = Path(__file__).parent.parent
        runner = repo_root / 'tools' / 'run_onnx_fall_detection.py'
        # prefer project .venv python if available to ensure required deps (onnx, etc.) are present
        python_exec = find_executable_in_venv('python') or sys.executable
        cmd = [
            python_exec,
            str(runner),
            '--test_dir', 'test_data',
            '--model_dir', 'models/qaihub_optimized',
            '--out_json', 'onnx_demo_quick20.json',
            '--out_html', 'onnx_demo_quick20.html',
            '--verbose',
            '--ensemble_votes', '1',    # more permissive for demo
            '--frame_stride', '8',      # denser sampling for video
            '--video_vote_ratio', '0.15',
            '--video_min_consec', '2'
        ]
        # ensure quick_n=20 explicitly
        cmd += ['--quick_n', '20']
        print('Running ONNX quick demo runner:', ' '.join(cmd))
        subprocess.run(cmd, cwd=str(repo_root))
    except Exception as e:
        print('Warning: failed to run ONNX demo runner:', e)

    print("\nDemo 完成！")


def run_official():
    """官方模式（特殊用途）"""
    print("\n[Official] 官方 QAI Hub Detector Demo")
    try:
        if demo_official_qai_hub_detection is None:
            raise RuntimeError('demo_official_qai_hub_detection not available')
        demo_official_qai_hub_detection()
    except Exception as e:
        print('Warning: demo_official_qai_hub_detection failed or not available:', e)

    # Run full ONNX runner (process all images/videos) - no quick_n
    try:
        repo_root = Path(__file__).parent.parent
        runner = repo_root / 'tools' / 'run_onnx_fall_detection.py'
        # prefer project .venv python if available
        python_exec = find_executable_in_venv('python') or sys.executable
        cmd = [
            python_exec,
            str(runner),
            '--test_dir', 'test_data',
            '--model_dir', 'models/qaihub_optimized',
            '--out_json', 'onnx_official_full.json',
            '--out_html', 'onnx_official_full.html',
            '--verbose',
            '--ensemble_votes', '2'
        ]
        # omit --quick_n to run full
        print('Running ONNX full runner:', ' '.join(cmd))
        subprocess.run(cmd, cwd=str(repo_root))
    except Exception as e:
        print('Warning: failed to run ONNX official runner:', e)

    print("\nOfficial Demo 完成！")


def run_test():
    """執行測試流程"""
    print("\n[Test] QAI Hub Unified Detector 測試 (Live)")
    if test_live_detection is None:
        print('❌ test_live_detection 不可用，請確認模組是否存在')
        return
    test_live_detection()
    print("\nTest 完成！")


def run_compile_profile_jobs(source='dlc'):
    """批次編譯並分析多模型（自動處理多個模型）"""
    print(f"\n[Compile+Profile] QAI Hub Compile+Profile Pipeline (Full)")
    
    # 使用 pipeline 模組執行完整的編譯+分析流程，傳遞正確的基礎目錄
    if QAIHubPipeline is None:
        print('❌ QAIHubPipeline 模組不可用，請確認 modules/pipeline.py 是否存在')
        return
    pipeline = QAIHubPipeline(get_models_dir())
    pipeline.run_compile_profile_pipeline(do_infer=False)
    print("\nCompile+Profile Jobs 全部完成！")


def run_compile_profile(source='dlc'):
    """單一模型編譯與分析（針對單一模型）"""
    print(f"\n[Compile+Profile+Infer] QAI Hub Compile+Profile+Infer Pipeline (Full Run)")
    
    # 使用 pipeline 模組執行完整的編譯+分析+推論流程，傳遞正確的基礎目錄
    if QAIHubPipeline is None:
        print('❌ QAIHubPipeline 模組不可用，請確認 modules/pipeline.py 是否存在')
        return
    pipeline = QAIHubPipeline(get_models_dir())
    pipeline.run_compile_profile_pipeline(do_infer=True)
    print("\nCompile+Profile+Infer 完成！")


def run_link(link_config_path: str = None, auto_link: bool = False):
    """Link Job（模型串接）

    Args:
        link_config_path: 如果提供則從檔案載入 link_config (JSON)。
        auto_link: 若 True，將直接提交（非互動式）。
    """
    print(f"\n[Link] QAI Hub Link Job Pipeline")

    # 使用 QAIHubPipeline 進行模型串接流程
    pipeline = QAIHubPipeline(get_models_dir())

    link_config = None
    # 若提供 config path，嘗試從檔案載入
    if link_config_path:
        try:
            with open(link_config_path, 'r') as f:
                link_config = json.load(f)
            print(f"載入 link config: {link_config_path}")
        except Exception as e:
            print(f"❌ 讀取 link config 失敗: {e}")
            return

    # 若未提供 config，使用預設示例（開發範例）
    if link_config is None:
        link_config = {
            "models": [
                {"id": "DETECT_MODEL_ID", "alias": "detector"},
                {"id": "LANDMARK_MODEL_ID", "alias": "landmark"}
            ],
            "connections": [
                {"from": "detector:output_boxes", "to": "landmark:input_boxes"}
            ]
        }

    print("🔗 模型串接配置: ")
    print(f"   - 模型數量: {len(link_config.get('models', []))}")
    print(f"   - 連接數量: {len(link_config.get('connections', []))}")

    print("\n⚠️  請注意：需要先完成模型的編譯，取得模型 ID 後才能進行串接")

    if not auto_link:
        # 互動式提示（保留原先行為）
        response = input("\n是否要提交此串接配置？(y/n): ").strip().lower()
        if response != 'y':
            print("\n⏭️ 已取消提交，請手動準備 link_config.json 後再執行")
            print("\nLink Job 流程完成！")
            return

    # 提交串接任務
    try:
        link_job = pipeline.qaihub_client.submit_link_job(link_config, "fall_detection_pipeline")
        if link_job:
            print(f"\n✅ Link Job 提交成功！Job ID: {getattr(link_job, 'job_id', 'unknown')}")
            print("   請等待串接任務完成...")
        else:
            print("\n❌ Link Job 提交失敗")
    except Exception as e:
        print(f"❌ 提交 Link Job 發生例外: {e}")

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
    parser.add_argument('mode', choices=['compile', 'profile', 'infer', 'demo', 'official', 'test', 'compile_profile_jobs', 'compile_profile', 'link', 'quantize'],
                        help="子命令: compile | profile | infer | demo | official | test | compile_profile_jobs | compile_profile | link | quantize")
    parser.add_argument('--calib_dir', type=str, default=None, help='校準資料目錄 (for quantize)')
    parser.add_argument('--input_name', type=str, default='image_tensor', help='模型輸入名稱 (for quantize)')
    parser.add_argument('--samples', type=int, default=100, help='校準樣本數 (for quantize)')
    parser.add_argument('--weights', type=str, default='INT8', help='權重量化類型 (e.g., INT8)')
    parser.add_argument('--activations', type=str, default='INT8', help='activation 量化類型 (e.g., INT8)')
    parser.add_argument('--replace_convinteger', action='store_true', help='Run ConvInteger->Dequant+Conv replacement before upload')
    parser.add_argument('--no-conversion-test', dest='no_conversion_test', action='store_true', help='跳過啟動時的 tflite->onnx 測試轉換')
    parser.add_argument('--auto-link', dest='auto_link', action='store_true', help='在 link 模式下自動提交（非互動）')
    parser.add_argument('--link-config', dest='link_config', type=str, default=None, help='指定 link config JSON 檔案路徑')
    parser.add_argument('--mode', nargs='?', help=argparse.SUPPRESS)
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
    elif args.mode == 'quantize':
        print('\n[Quantize] QAI Hub Quantize Pipeline')
        if QAIHubPipeline is None:
            print('❌ QAIHubPipeline 模組不可用，請確認 modules/pipeline.py 是否存在')
            sys.exit(1)
        pipeline = QAIHubPipeline(get_models_dir())
        # 將簡單的字串類型轉換為 None 或預設（實際類型由 SDK 處理）
        weights = getattr(args, 'weights', None)
        activations = getattr(args, 'activations', None)
        # If requested, set env var so pipeline will run ConvInteger replacement before upload
        if getattr(args, 'replace_convinteger', False):
            os.environ['REPLACE_CONVINTEGER'] = '1'
        success = pipeline.run_quantize_pipeline(calib_dir=args.calib_dir, input_name=args.input_name, sample_limit=args.samples, weights_dtype=weights, activations_dtype=activations)
        if success:
            print('\n✅ Quantize 完成！')
        else:
            print('\n❌ Quantize 失敗！')
    elif args.mode == 'link':
        run_link(link_config_path=getattr(args, 'link_config', None), auto_link=getattr(args, 'auto_link', False))
    else:
        print("未知模式！")
        sys.exit(1)


# 在主程式中加入目錄檢查
if __name__ == "__main__":
    # 驗證並展開必要的 env 變數，若失敗則顯示訊息並退出
    try:
        validate_and_expand_env_vars()
    except EnvironmentError as e:
        print(f"❌ .env 配置錯誤: {e}")
        sys.exit(1)

    # 確保所有必要目錄存在
    ensure_directory_exists(MODELS_BASE_DIR)
    ensure_directory_exists(os.path.dirname(ONNX_MODEL_DIR) or ONNX_MODEL_DIR)
    ensure_directory_exists(ONNX_MODEL_DIR)
    ensure_directory_exists(RAW_MODEL_DIR)
    ensure_directory_exists(OPTIMIZED_MODEL_DIR)

    # 解析初始 args 以判斷是否執行啟動時的轉換測試
    # 如果使用者希望跳過，會使用 --no-conversion-test
    # 先 run help-less parse to check flag default; main() will parse again for normal dispatch
    quick_parser = argparse.ArgumentParser(add_help=False)
    quick_parser.add_argument('--no-conversion-test', dest='no_conversion_test', action='store_true')
    quick_args, _ = quick_parser.parse_known_args()

    if not getattr(quick_args, 'no_conversion_test', False):
        # 測試轉換流程（僅在啟動且未指定 skip 時執行）
        tflite_model_path = os.path.join(RAW_MODEL_DIR, "face_detector.tflite")
        onnx_model_path = os.path.join(ONNX_MODEL_DIR, "face_detector.onnx")
        try:
            convert_tflite_to_onnx(tflite_model_path, onnx_model_path)
        except Exception as e:
            print(f"⚠️  啟動時轉換測試發生錯誤（已捕捉）: {e}")

    try:
        main()
    except FileNotFoundError as e:
        print(f"❌ 發生錯誤: {e}")
    except Exception as e:
        import traceback
        print(f"❌ 未知錯誤: {e}")
        traceback.print_exc()
