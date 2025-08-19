#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
QAI Hub 離線演示模式
此腳本提供一個離線演示模式，在無法連接 QAI Hub API 時仍然可以展示系統功能。
它使用預先保存的模型結果來模擬 QAI Hub 的行為。
"""

import os
import json
import time
import random
import logging
import argparse
import numpy as np
from datetime import datetime

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("QAI_HUB_OFFLINE")

# 模擬的 QAI Hub 模型結果
MOCK_MODEL_RESULTS = {
    "face_detection": {
        "boxes": [[0.2, 0.3, 0.4, 0.5], [0.6, 0.2, 0.8, 0.4]],
        "scores": [0.98, 0.85],
        "inference_time": 0.045
    },
    "pose_estimation": {
        "keypoints": [
            [0.3, 0.2], [0.35, 0.25], [0.4, 0.3],  # 右肩, 右肘, 右手腕
            [0.25, 0.2], [0.2, 0.25], [0.15, 0.3],  # 左肩, 左肘, 左手腕
            [0.3, 0.4], [0.35, 0.6], [0.4, 0.8],    # 右髖, 右膝, 右腳踝
            [0.25, 0.4], [0.2, 0.6], [0.15, 0.8],   # 左髖, 左膝, 左腳踝
            [0.275, 0.1], [0.27, 0.12], [0.28, 0.15]  # 鼻子, 右眼, 左眼
        ],
        "scores": [0.9] * 17,
        "inference_time": 0.067
    },
    "fall_detection": {
        "is_falling": False,
        "fall_confidence": 0.15,
        "standing_confidence": 0.85,
        "inference_time": 0.023
    }
}

# 模擬的 QAI Hub 連線失敗錯誤信息
MOCK_CONNECTION_ERROR = {
    "error_type": "ConnectionError",
    "message": "無法連接到 QAI Hub API",
    "suggestion": "請檢查網絡連接或使用離線模式"
}

class QAIHubOfflineDemo:
    """QAI Hub 離線演示模式類"""
    
    def __init__(self, use_random_results=False, simulate_fall=False):
        """
        初始化離線演示模式
        
        Args:
            use_random_results: 是否使用隨機變化的結果
            simulate_fall: 是否模擬跌倒情況
        """
        self.use_random_results = use_random_results
        self.simulate_fall = simulate_fall
        self.session_id = f"offline_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        logger.info(f"QAI Hub 離線演示模式已啟動 (Session ID: {self.session_id})")
        
        # 創建結果目錄
        self.results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "offline_results")
        os.makedirs(self.results_dir, exist_ok=True)
        
        # 如果設置了模擬跌倒，準備跌倒數據
        if self.simulate_fall:
            self._prepare_fall_simulation()

    def _prepare_fall_simulation(self):
        """準備跌倒模擬數據"""
        # 初始化為站立姿勢
        self.current_state = "standing"
        self.fall_sequence = [
            "standing",   # 0-10 秒：正常站立
            "standing",
            "bending",    # 10-15 秒：彎腰
            "falling",    # 15-20 秒：跌倒過程
            "fallen",     # 20-30 秒：已經跌倒在地
            "fallen",
            "standing"    # 30+ 秒：恢復站立 (模擬假警報或恢復)
        ]
        self.sequence_index = 0
        self.sequence_timer = time.time()
        self.sequence_duration = 5.0  # 每個狀態持續秒數
        logger.info("已配置跌倒模擬序列")

    def _update_fall_state(self):
        """更新跌倒狀態"""
        if not self.simulate_fall:
            return
            
        current_time = time.time()
        if current_time - self.sequence_timer > self.sequence_duration:
            self.sequence_index = (self.sequence_index + 1) % len(self.fall_sequence)
            self.current_state = self.fall_sequence[self.sequence_index]
            self.sequence_timer = current_time
            logger.info(f"狀態更新: {self.current_state}")
            
        # 根據當前狀態更新跌倒檢測結果
        if self.current_state == "standing":
            MOCK_MODEL_RESULTS["fall_detection"]["is_falling"] = False
            MOCK_MODEL_RESULTS["fall_detection"]["fall_confidence"] = 0.05 + random.random() * 0.1
            MOCK_MODEL_RESULTS["fall_detection"]["standing_confidence"] = 0.85 + random.random() * 0.1
        elif self.current_state == "bending":
            MOCK_MODEL_RESULTS["fall_detection"]["is_falling"] = False
            MOCK_MODEL_RESULTS["fall_detection"]["fall_confidence"] = 0.3 + random.random() * 0.1
            MOCK_MODEL_RESULTS["fall_detection"]["standing_confidence"] = 0.6 + random.random() * 0.1
        elif self.current_state == "falling":
            MOCK_MODEL_RESULTS["fall_detection"]["is_falling"] = True
            MOCK_MODEL_RESULTS["fall_detection"]["fall_confidence"] = 0.7 + random.random() * 0.2
            MOCK_MODEL_RESULTS["fall_detection"]["standing_confidence"] = 0.2 + random.random() * 0.1
        elif self.current_state == "fallen":
            MOCK_MODEL_RESULTS["fall_detection"]["is_falling"] = True
            MOCK_MODEL_RESULTS["fall_detection"]["fall_confidence"] = 0.9 + random.random() * 0.1
            MOCK_MODEL_RESULTS["fall_detection"]["standing_confidence"] = 0.05 + random.random() * 0.05
            
        # 同時更新姿勢估計結果以匹配跌倒狀態
        self._update_pose_for_fall_state()

    def _update_pose_for_fall_state(self):
        """根據跌倒狀態更新姿勢估計"""
        keypoints = MOCK_MODEL_RESULTS["pose_estimation"]["keypoints"]
        
        # 添加一些隨機變化
        noise = 0.02 if self.use_random_results else 0.0
        
        if self.current_state == "standing":
            # 正常站立姿勢 - 維持垂直分布的關鍵點
            for i in range(len(keypoints)):
                keypoints[i][0] += random.uniform(-noise, noise)
                keypoints[i][1] += random.uniform(-noise, noise)
                
        elif self.current_state == "bending":
            # 彎腰姿勢 - 上半身關鍵點向下移動
            for i in range(6):  # 上半身關鍵點
                keypoints[i][1] += 0.1 + random.uniform(-noise, noise)
                
        elif self.current_state == "falling":
            # 跌倒過程 - 所有關鍵點向一側移動
            fall_direction = 0.15  # 向右跌倒
            for i in range(len(keypoints)):
                keypoints[i][0] += fall_direction + random.uniform(-noise, noise)
                if i > 5:  # 下半身關鍵點
                    keypoints[i][1] -= 0.05 + random.uniform(-noise, noise)
                
        elif self.current_state == "fallen":
            # 已跌倒 - 關鍵點水平分布
            for i in range(len(keypoints)):
                if i < 6:  # 上半身關鍵點
                    keypoints[i][0] += 0.2 + random.uniform(-noise, noise)
                    keypoints[i][1] += 0.2 + random.uniform(-noise, noise)
                else:  # 下半身關鍵點
                    keypoints[i][0] -= 0.1 + random.uniform(-noise, noise)
                    keypoints[i][1] += 0.1 + random.uniform(-noise, noise)

    def _add_random_variation(self, results):
        """添加隨機變化到結果中"""
        if not self.use_random_results:
            return results
            
        # 深拷貝以避免修改原始數據
        import copy
        varied_results = copy.deepcopy(results)
        
        # 添加隨機變化到臉部檢測結果
        if "face_detection" in varied_results:
            for box in varied_results["face_detection"]["boxes"]:
                for i in range(len(box)):
                    box[i] += random.uniform(-0.03, 0.03)
                    box[i] = max(0.0, min(1.0, box[i]))  # 確保在 [0,1] 範圍內
            
            for i in range(len(varied_results["face_detection"]["scores"])):
                varied_results["face_detection"]["scores"][i] += random.uniform(-0.05, 0.05)
                varied_results["face_detection"]["scores"][i] = max(0.0, min(1.0, varied_results["face_detection"]["scores"][i]))
                
            varied_results["face_detection"]["inference_time"] += random.uniform(-0.01, 0.01)
        
        # 添加隨機變化到姿勢估計結果
        if "pose_estimation" in varied_results:
            for kp in varied_results["pose_estimation"]["keypoints"]:
                kp[0] += random.uniform(-0.02, 0.02)
                kp[1] += random.uniform(-0.02, 0.02)
                kp[0] = max(0.0, min(1.0, kp[0]))
                kp[1] = max(0.0, min(1.0, kp[1]))
                
            varied_results["pose_estimation"]["inference_time"] += random.uniform(-0.01, 0.01)
        
        return varied_results

    def run_inference(self, model_name, input_data=None):
        """
        模擬運行推理
        
        Args:
            model_name: 模型名稱
            input_data: 輸入數據 (離線模式中被忽略)
            
        Returns:
            模擬的推理結果
        """
        # 模擬網絡延遲
        time.sleep(random.uniform(0.1, 0.3))
        
        # 更新跌倒狀態 (如果啟用了模擬跌倒)
        self._update_fall_state()
        
        # 獲取模擬結果
        if model_name == "all":
            results = MOCK_MODEL_RESULTS
        elif model_name in MOCK_MODEL_RESULTS:
            results = {model_name: MOCK_MODEL_RESULTS[model_name]}
        else:
            logger.warning(f"未知模型: {model_name}，返回錯誤")
            return {"error": f"模型 '{model_name}' 在離線模式中不可用"}
        
        # 添加隨機變化 (如果啟用)
        results = self._add_random_variation(results)
        
        # 保存結果
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        result_file = os.path.join(self.results_dir, f"{model_name}_{timestamp}.json")
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
            
        logger.info(f"模型 {model_name} 的離線結果已保存到 {result_file}")
        return results
        
    def get_connection_status(self):
        """
        獲取連接狀態
        
        Returns:
            一個表示離線模式的字典
        """
        return {
            "status": "offline",
            "message": "運行在離線演示模式",
            "timestamp": datetime.now().isoformat()
        }
        
    def get_sdk_info(self):
        """
        獲取 SDK 信息
        
        Returns:
            模擬的 SDK 信息
        """
        return {
            "qai_hub_version": "0.31.0 (離線模式)",
            "protobuf_version": "4.25.3 (離線模式)",
            "session_id": self.session_id,
            "mode": "offline_demo"
        }
        
    def cleanup(self):
        """清理資源"""
        logger.info("離線演示模式已關閉")

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="QAI Hub 離線演示模式")
    parser.add_argument("--random", action="store_true", help="使用隨機變化的結果")
    parser.add_argument("--simulate-fall", action="store_true", help="模擬跌倒情況")
    parser.add_argument("--test-all", action="store_true", help="測試所有模型")
    args = parser.parse_args()
    
    try:
        # 初始化離線演示模式
        demo = QAIHubOfflineDemo(
            use_random_results=args.random,
            simulate_fall=args.simulate_fall
        )
        
        # 顯示初始信息
        print("\n" + "=" * 50)
        print("QAI Hub 離線演示模式")
        print("=" * 50)
        print(f"會話 ID: {demo.session_id}")
        print(f"使用隨機變化: {'是' if args.random else '否'}")
        print(f"模擬跌倒: {'是' if args.simulate_fall else '否'}")
        print(f"結果保存目錄: {demo.results_dir}")
        print("=" * 50 + "\n")
        
        if args.test_all:
            # 測試所有模型
            print("測試所有模型...")
            for _ in range(10):  # 運行10次
                results = demo.run_inference("all")
                is_falling = results["fall_detection"]["is_falling"]
                fall_conf = results["fall_detection"]["fall_confidence"]
                print(f"跌倒狀態: {'是' if is_falling else '否'} (置信度: {fall_conf:.2f})")
                time.sleep(1)
        else:
            # 互動模式
            print("互動模式 - 輸入命令 (輸入 'help' 獲取幫助):")
            while True:
                cmd = input("> ").strip().lower()
                if cmd == "exit" or cmd == "quit":
                    break
                elif cmd == "help":
                    print("\n可用命令:")
                    print("  face    - 運行臉部檢測")
                    print("  pose    - 運行姿勢估計")
                    print("  fall    - 運行跌倒檢測")
                    print("  all     - 運行所有模型")
                    print("  status  - 顯示連接狀態")
                    print("  info    - 顯示 SDK 信息")
                    print("  monitor - 持續監控 (按 Ctrl+C 停止)")
                    print("  exit    - 退出程序\n")
                elif cmd == "face":
                    print(json.dumps(demo.run_inference("face_detection"), indent=2))
                elif cmd == "pose":
                    print(json.dumps(demo.run_inference("pose_estimation"), indent=2))
                elif cmd == "fall":
                    print(json.dumps(demo.run_inference("fall_detection"), indent=2))
                elif cmd == "all":
                    print(json.dumps(demo.run_inference("all"), indent=2))
                elif cmd == "status":
                    print(json.dumps(demo.get_connection_status(), indent=2))
                elif cmd == "info":
                    print(json.dumps(demo.get_sdk_info(), indent=2))
                elif cmd == "monitor":
                    try:
                        print("開始監控 (按 Ctrl+C 停止)...")
                        while True:
                            results = demo.run_inference("fall_detection")
                            is_falling = results["fall_detection"]["is_falling"]
                            fall_conf = results["fall_detection"]["fall_confidence"]
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] 跌倒狀態: {'是' if is_falling else '否'} (置信度: {fall_conf:.2f})")
                            time.sleep(1)
                    except KeyboardInterrupt:
                        print("\n停止監控")
                else:
                    print(f"未知命令: {cmd}")
        
    except KeyboardInterrupt:
        print("\n程序已中斷")
    finally:
        if 'demo' in locals():
            demo.cleanup()
            
    print("\n離線演示模式已結束")

if __name__ == "__main__":
    main()
