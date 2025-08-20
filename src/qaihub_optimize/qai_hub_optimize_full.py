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

# 匯入模組化組件
from modules.scanner import ModelScanner
from modules.conversion import ModelConverter
from modules.format_check import FormatChecker
from modules.qaihub_client import QAIHubClient
from modules.pipeline import QAIHubPipeline
from modules.job_monitor import QAIHubJobMonitor

# 匯入其他必要的功能模組
from practical_qai_hub_onnx import PracticalQAIHubONNX
from final_qai_hub_onnx_system import FinalQAIHubONNXSystem
from qai_hub_unified_detector import QAIHubUnifiedDetector, demo_qai_hub_detection, test_live_detection
from official_qai_hub_detector import OfficialQAIHubDetector, demo_official_qai_hub_detection


def get_models_dir():
    """取得 models 目錄路徑"""
    return Path(__file__).parent.parent / 'models'


def run_compile(source='dlc'):
    """編譯並最佳化模型（自動掃描 org 目錄）"""
    print(f"\n[Compile] QAI Hub Compile Pipeline (Practical) | source={source}")
    
    # 初始化模組
    scanner = ModelScanner()
    converter = ModelConverter()
    format_checker = FormatChecker()
    qaihub_client = QAIHubClient()
    pipeline = QAIHubPipeline()
    
    # 掃描 org 目錄
    model_files = scanner.scan_org_directory()
    counts = scanner.get_model_counts(model_files)
    
    if counts['total'] == 0:
        print("❌ org 目錄下沒有可用模型檔案！")
        return
    
    print(f"\n共偵測到：{counts['tflite']} 個 tflite, {counts['onnx']} 個 onnx, {counts['dlc']} 個 dlc 檔案")
    
    # 自動轉換 TFLite 到 ONNX
    if counts['tflite'] > 0:
        tflite_files = model_files['tflite']
        results, failed_conversions = converter.batch_convert_tflite(tflite_files, get_models_dir() / 'onnx')
        
        successful_conversions = [r for r in results if r["status"] == "ok"]
        if successful_conversions:
            print(f"✅ 批次轉換完成，{len(successful_conversions)} 個 onnx 檔案已存入 {get_models_dir() / 'onnx'}")
            # 轉換完自動切換 source 為 onnx
            source = 'onnx'
        if failed_conversions:
            print(f"⚠️  有 {len(failed_conversions)} 個檔案轉換失敗")
    
    # 根據 source 決定目錄與格式
    source_map = {
        'onnx':      ('onnx', '.onnx'),
        'tflite':    ('org-tflite', '.tflite'),
        'dlc':       ('org-dlc', '.dlc'),
        'org-onnx':  ('onnx', '.onnx'),
        'org-tflite':('org-tflite', '.tflite'),
        'org-dlc':   ('org-dlc', '.dlc'),
        'original':  ('original', '.tflite'),
    }
    
    if source not in source_map:
        print(f"❌ 不支援的 source: {source}")
        return
    
    model_dir, ext = source_map[source]
    
    # 若是 onnx，先自動修正所有 onnx 檔案
    if ext == '.onnx':
        onnx_dir = get_models_dir() / model_dir
        format_checker.batch_fix_onnx_value_info(onnx_dir)
    
    # 使用 pipeline 進行完整的編譯流程
    system = PracticalQAIHubONNX()
    system.load_mediapipe_models(source=source, model_dir=model_dir, ext=ext)
    
    # ONNX 檢查
    if ext == '.onnx':
        invalid_models = format_checker.check_onnx_models(system.qai_hub_models)
        if invalid_models:
            print("\n❌ 偵測到下列 ONNX 模型檔案格式異常，請修正後再執行：")
            for name, path, err in invalid_models:
                print(f"   - {name}: {path}\n     錯誤: {err}")
            print("\n流程中止。")
            return
    
    # 列出要處理的模型
    models_to_process = [k for k, v in system.qai_hub_models.items() if v.get('loaded')]
    print(f"\n🔎 偵測到 {len(models_to_process)} 個模型將進行 QAI Hub 最佳化：")
    for m in models_to_process:
        print(f"   - {m}")
    
    # 提示 QAI Hub 作業流程
    print("""
📋 QAI Hub 雲端最佳化作業流程：
1. 上傳模型（Upload Model）
2. 提交編譯任務（Submit Compile Job）
3. 等待雲端完成最佳化（Job Queue & Compile）
4. 下載最佳化模型（Download）
5. 可進行 Profile、Infer、Demo 等後續測試
""")
    
    # 執行編譯流程
    system.upload_models_to_qai_hub()
    system.submit_compilation_jobs()
    
    # 使用 JobMonitor 等待所有 compile job 完成
    job_monitor = QAIHubJobMonitor()
    job_monitor.wait_for_compile_jobs(system.qai_hub_models, timeout_minutes=30)
    
    # 產生 HTML 報告
    job_monitor.generate_compile_report(system.qai_hub_models, 'practical_qai_hub_compile_report.html')
    print(f"\n✅ Compile 完成！HTML 報告已產生 practical_qai_hub_compile_report.html")


def run_profile():
    """進行模型效能分析（自動掃描 org 目錄）"""
    print("\n[Profile] QAI Hub Profile Pipeline (Practical)")
    
    # 初始化模組
    scanner = ModelScanner()
    converter = ModelConverter()
    qaihub_client = QAIHubClient()
    job_monitor = QAIHubJobMonitor(qaihub_client)
    
    # 掃描 org 目錄
    model_files = scanner.scan_org_directory()
    counts = scanner.get_model_counts(model_files)
    
    if counts['total'] == 0:
        print("❌ org 目錄下找不到任何模型檔案，無法進行 profile。")
        return
    
    # 合併所有模型檔案
    all_model_files = model_files['tflite'] + model_files['onnx'] + model_files['dlc']
    
    print(f"🔎 偵測到 {counts['total']} 個模型檔案：")
    for file_list in [model_files['tflite'], model_files['onnx'], model_files['dlc']]:
        for f in file_list:
            print(f"   - {f.name}")
    
    # 啟動系統，先取得裝置支援格式
    system = PracticalQAIHubONNX()
    device = system.target_device
    if not device:
        print("❌ 無法取得目標裝置，無法進行 profile。")
        return
    
    # 檢查裝置支援的框架
    device_attrs = getattr(device, 'attributes', [])
    support_onnx = any('framework:onnx' in a for a in device_attrs)
    support_tflite = any('framework:tflite' in a for a in device_attrs)
    support_dlc = any('framework:dlc' in a for a in device_attrs)
    
    print(f"\n[裝置支援格式] ONNX={support_onnx}, TFLite={support_tflite}, DLC={support_dlc}")
    
    # 處理 TFLite 轉換
    tflite_models = model_files['tflite']
    convert_tflite = False
    
    if tflite_models and not support_tflite:
        convert_tflite = converter.ask_for_conversion(len(tflite_models))
    
    # 篩選可 profile 的模型
    models_to_profile = []
    for f in all_model_files:
        ext = f.suffix.lower()
        if ext == '.onnx' and not support_onnx:
            print(f"⏭️ 跳過 {f.name}，因目標裝置不支援 ONNX")
            continue
        if ext == '.dlc' and not support_dlc:
            print(f"⏭️ 跳過 {f.name}，因目標裝置不支援 DLC")
            continue
        if ext == '.tflite':
            if support_tflite:
                models_to_profile.append(f)
            elif convert_tflite:
                # 嘗試轉換
                result = converter.convert_tflite_to_onnx(f, get_models_dir() / 'onnx')
                if result["status"] == "ok" and result["onnx_path"]:
                    models_to_profile.append(Path(result["onnx_path"]))
                    print(f"✅ 轉換成功: {f.name} -> {result['onnx_path'].name}")
                else:
                    print(f"❌ 轉換失敗: {f.name} - {result['message']}")
            else:
                print(f"⏭️ 跳過 {f.name}，因目標裝置不支援 TFLite 且未選擇自動轉換")
        else:
            models_to_profile.append(f)
    
    if not models_to_profile:
        print("❌ 無可 profile 的模型。流程結束。")
        return
    
    print(f"\n✅ 最終將進行 profile 的模型：")
    for f in models_to_profile:
        print(f"   - {f.name}")
    
    # 載入、上傳、profile
    for ext, source in [('.onnx', 'onnx'), ('.tflite', 'tflite'), ('.dlc', 'dlc')]:
        files = [f for f in models_to_profile if f.suffix.lower() == ext]
        if files:
            system.load_mediapipe_models(source=source, model_dir='org', ext=ext)
    
    system.upload_models_to_qai_hub()
    system.submit_profile_jobs()
    
    # 使用 JobMonitor 等待所有 profile job 完成
    job_monitor.wait_for_profile_jobs(system.qai_hub_models, timeout_minutes=30)
    
    # 產生 HTML 報告
    job_monitor.generate_profile_report(system.qai_hub_models, 'practical_qai_hub_profile_report.html')
    print(f"\n✅ Profile 完成！HTML 報告已產生 practical_qai_hub_profile_report.html")


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


def run_link(source='dlc'):
    """Link Job（進階用途）"""
    print(f"\n[Link] QAI Hub Link Job Pipeline | source={source}")
    print("(目前僅支援現有檔案，不做自動轉換)")
    print("\nLink Job 完成！")


def main():
    parser = argparse.ArgumentParser(
        description=(
            """
    QAI Hub Optimize Full - All-in-One 整合工具 (模組化版本)

    用法 (Usage):
        python qai_hub_optimize_full.py <mode>

    可用子命令 (mode)：
        compile                編譯並最佳化模型（自動掃描 org 目錄）
        profile                進行模型效能分析（自動掃描 org 目錄）
        compile_profile_jobs   批次編譯並分析多模型（自動處理多個模型）（自動掃描 org 目錄）
        compile_profile        單一模型編譯與分析（針對單一模型（自動掃描 org 目錄））
        infer                  進行模型推論測試
        demo                   啟動互動式 Demo
        official               官方模式（特殊用途）
        test                   執行測試流程
        link                   Link Job（進階用途）

    範例 (Examples):
        python qai_hub_optimize_full.py compile
        python qai_hub_optimize_full.py profile

    說明：
        - 所有模型來源已統一自動從 org 目錄取得，無需手動切換來源參數。
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


if __name__ == "__main__":
    main()
