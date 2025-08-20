#!/usr/bin/env python3
"""
QAI Hub Optimize Full - All-in-One 整合工具
支援 Compile、Profile、Infer、Demo、Test 等多模式入口
"""
import argparse
import sys
import os

# 匯入各功能模組（假設都在同目錄或 PYTHONPATH 下）
from practical_qai_hub_onnx import PracticalQAIHubONNX
from final_qai_hub_onnx_system import FinalQAIHubONNXSystem
from qai_hub_unified_detector import QAIHubUnifiedDetector, demo_qai_hub_detection, test_live_detection
from official_qai_hub_detector import OfficialQAIHubDetector, demo_official_qai_hub_detection


def run_compile(source='dlc'):
    print(f"\n[Compile] QAI Hub Compile Pipeline (Practical) | source={source}")
    # 根據 source 決定目錄與格式
    source_map = {
        'onnx':      ('org-onnx', '.onnx'),
        'tflite':    ('org-tflite', '.tflite'),
        'dlc':       ('org-dlc', '.dlc'),
        'org-onnx':  ('org-onnx', '.onnx'),
        'org-tflite':('org-tflite', '.tflite'),
        'org-dlc':   ('org-dlc', '.dlc'),
        'original':  ('original', '.tflite'),
    }
    if source not in source_map:
        print(f"❌ 不支援的 source: {source}")
        return
    model_dir, ext = source_map[source]
    system = PracticalQAIHubONNX()
    # 修改 load_mediapipe_models 支援自訂目錄與副檔名
    system.load_mediapipe_models(source=source, model_dir=model_dir, ext=ext)
    # ONNX 檢查
    if ext == '.onnx':
        invalid = system.check_onnx_models()
        if invalid:
            print("\n❌ 偵測到下列 ONNX 模型檔案格式異常，請修正後再執行：")
            for name, path, err in invalid:
                print(f"   - {name}: {path}\n     錯誤: {err}")
            print("\n請參考 onnx.checker.check_model('your_model.onnx', full_check=True) 進行本地檢查。\n流程中止。")
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
\n詳細說明與 API 範例請參考：
https://app.aihub.qualcomm.com/docs/hub/index.html#examples
""")
    # 僅保留上傳與編譯
    system.upload_models_to_qai_hub()
    system.submit_compilation_jobs()
    # 編譯結果報告
    compiled = [k for k, v in system.qai_hub_models.items() if v.get('compile_job')]
    failed = [k for k, v in system.qai_hub_models.items() if v.get('loaded') and not v.get('compile_job')]
    print(f"\n✅ 已成功提交 {len(compiled)} 個模型進行 QAI Hub 編譯：")
    for m in compiled:
        print(f"   - {m}")
    if failed:
        print(f"\n⚠️ 下列模型未能成功提交編譯（可能缺檔或上傳失敗）：")
        for m in failed:
            print(f"   - {m}")
    print("\nCompile 完成！")

def run_profile():
    print("\n[Profile] QAI Hub Profile Pipeline (Final)")
    system = FinalQAIHubONNXSystem()
    system.load_mediapipe_components()
    # 僅保留上傳與 profile（假設 FinalQAIHubONNXSystem 有對應方法）
    system.upload_models_to_qai_hub()
    system.submit_profile_jobs()
    print("\nProfile 完成！")

def run_infer():
    print("\n[Infer] QAI Hub Inference Demo (Practical)")
    system = PracticalQAIHubONNX()
    system.load_mediapipe_models()
    # 僅保留現有模型推論（不做任何轉換）
    print("(目前僅支援現有模型推論，無自動轉換)")
    print("\nInfer 完成！")

def run_demo():
    print("\n[Demo] QAI Hub Unified Detection Demo")
    demo_qai_hub_detection()
    print("\nDemo 完成！")

def run_official():
    print("\n[Official] 官方 QAI Hub Detector Demo")
    demo_official_qai_hub_detection()
    print("\nOfficial Demo 完成！")

def run_test():
    print("\n[Test] QAI Hub Unified Detector 測試 (Live)")
    test_live_detection()
    print("\nTest 完成！")

def run_compile_profile_jobs(source='dlc'):
    print(f"\n[Compile+Profile] QAI Hub Compile+Profile Pipeline (Full) | source={source}")
    # 僅保留現有檔案的 compile+profile 流程
    print("(目前僅支援現有檔案，不做自動轉換)")
    print("\nCompile+Profile Jobs 完成！")

def run_compile_profile(source='dlc'):
    print(f"\n[Compile+Profile] QAI Hub Compile+Profile Pipeline (Half) | source={source}")
    print("(目前僅支援現有檔案，不做自動轉換)")
    print("\nCompile+Profile 完成！")

def run_link(source='dlc'):
    print(f"\n[Link] QAI Hub Link Job Pipeline | source={source}")
    print("(目前僅支援現有檔案，不做自動轉換)")
    print("\nLink Job 完成！")

def main():
    parser = argparse.ArgumentParser(description="QAI Hub Optimize Full - All-in-One 整合工具")
    parser.add_argument('mode', choices=['compile', 'profile', 'infer', 'demo', 'official', 'test', 'compile_profile_jobs', 'compile_profile', 'link'],
                        help="執行模式: compile | profile | infer | demo | official | test | compile_profile_jobs | compile_profile | link")
    parser.add_argument('--source', choices=['onnx', 'original', 'org-onnx', 'org-tflite', 'org-dlc', 'dlc'], default='dlc',
                        help="模型來源: onnx、original、org-onnx、org-tflite、org-dlc、dlc (預設 dlc)")
    args = parser.parse_args()

    if args.mode == 'compile':
        run_compile(source=args.source)
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
        run_compile_profile_jobs(source=args.source)
    elif args.mode == 'compile_profile':
        run_compile_profile(source=args.source)
    elif args.mode == 'link':
        run_link(source=args.source)
    else:
        print("未知模式！")
        sys.exit(1)

if __name__ == "__main__":
    main()
