#!/usr/bin/env python3
"""
🚀 QAI Hub Live Demo 啟動器
支持Streamlit和Web兩種模式
"""

import sys
import os
import subprocess
import argparse

def run_streamlit_demo():
    """啟動Streamlit演示"""
    print("🚀 啟動Streamlit演示...")
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "qai_hub_streamlit_demo.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Streamlit演示已停止")
    except Exception as e:
        print(f"❌ Streamlit啟動失敗: {e}")

def run_web_demo():
    """啟動普通Web演示"""
    print("🚀 啟動Web演示...")
    try:
        subprocess.run([sys.executable, "qai_hub_web_demo.py"])
    except KeyboardInterrupt:
        print("\n🛑 Web演示已停止")
    except Exception as e:
        print(f"❌ Web演示啟動失敗: {e}")

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="QAI Hub Live Demo 啟動器")
    parser.add_argument(
        "--mode", 
        choices=["streamlit", "web", "both"], 
        default="streamlit",
        help="選擇演示模式: streamlit(Streamlit應用), web(普通Web), both(顯示選項)"
    )
    
    args = parser.parse_args()
    
    print("🧠 QAI Hub 老人行為檢測系統 - Live Demo")
    print("=" * 50)
    
    if args.mode == "both":
        print("請選擇演示模式:")
        print("1. 📊 Streamlit Web應用 (推薦)")
        print("2. 🌐 普通Web應用")
        print("3. ❌ 退出")
        
        while True:
            choice = input("\n請輸入選項 (1-3): ").strip()
            
            if choice == "1":
                run_streamlit_demo()
                break
            elif choice == "2":
                run_web_demo()
                break
            elif choice == "3":
                print("👋 再見！")
                break
            else:
                print("❌ 無效選項，請重新輸入")
    
    elif args.mode == "streamlit":
        run_streamlit_demo()
    
    elif args.mode == "web":
        run_web_demo()

if __name__ == "__main__":
    main()
