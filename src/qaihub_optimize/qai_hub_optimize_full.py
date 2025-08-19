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


def run_compile():
    print("\n[Compile] QAI Hub Compile Pipeline (Practical)")
    system = PracticalQAIHubONNX()
    system.load_mediapipe_models()
    system.export_models_to_torchscript()
    system.upload_models_to_qai_hub()
    system.submit_compilation_jobs()
    print("\nCompile 完成！")

def run_profile():
    print("\n[Profile] QAI Hub Compile+Profile Pipeline (Final)")
    system = FinalQAIHubONNXSystem()
    system.load_mediapipe_components()
    system.convert_to_torchscript_and_upload()
    system.submit_qai_hub_jobs()
    print("\nProfile 完成！")

def run_infer():
    print("\n[Infer] QAI Hub ONNX Inference Demo (Practical)")
    system = PracticalQAIHubONNX()
    system.load_mediapipe_models()
    system.export_models_to_torchscript()
    system.convert_torchscript_to_onnx()
    test_images = ['andy.jpg', 'official_test_image.jpg']
    for img_path in test_images:
        if os.path.exists(img_path):
            print(f"\n📷 測試圖像: {img_path}")
            import cv2
            image = cv2.imread(img_path)
            if image is not None:
                for model_name in system.onnx_sessions.keys():
                    result = system.detect_with_onnx(image, model_name)
                    print(f"   {model_name}: {result.get('inference_time_ms', 'N/A')}ms")
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

def main():
    parser = argparse.ArgumentParser(description="QAI Hub Optimize Full - All-in-One 整合工具")
    parser.add_argument('mode', choices=['compile', 'profile', 'infer', 'demo', 'official', 'test'],
                        help="執行模式: compile | profile | infer | demo | official | test")
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
    else:
        print("未知模式！")
        sys.exit(1)

if __name__ == "__main__":
    main()
