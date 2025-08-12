#!/usr/bin/env python3
"""
一鍵部署腳本 - Mac 到 Qualcomm Device Cloud
自動將檔案從 Mac 開發環境部署到 Windows Device Cloud
"""

import os
import sys
import time
import subprocess
import argparse
import logging
from pathlib import Path

# 配置日誌記錄
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 配置
DEFAULT_SSH_KEY = "qdc_id_2025-8-11_62.pem"
DEFAULT_USERNAME = "hcktest"
DEFAULT_PORT = 2222
DEFAULT_TARGET_DIR = "C:/dragon_x_fall_detection"

def run_command(command, verbose=True):
    """執行Shell命令並返回輸出"""
    if verbose:
        logger.info(f"執行: {command}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=False,  # 不在非零退出時拋出異常
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"命令失敗，代碼 {result.returncode}")
            logger.error(f"錯誤: {result.stderr}")
            return False, result.stderr
        
        return True, result.stdout
    except Exception as e:
        logger.error(f"執行命令時出現異常: {e}")
        return False, str(e)

def check_ssh_connection(ssh_key, username, port):
    """檢查與設備的SSH連接是否正常工作"""
    logger.info("檢查與設備的SSH連接...")
    
    command = f'ssh -i "{ssh_key}" -p {port} -o StrictHostKeyChecking=no -o ConnectTimeout=5 {username}@localhost "echo 連接成功"'
    success, output = run_command(command)
    
    if success:
        logger.info("SSH連接成功！")
        return True
    else:
        logger.error("SSH連接失敗")
        return False

def create_remote_directory(ssh_key, username, port, directory):
    """在遠程設備上創建目錄"""
    logger.info(f"創建遠程目錄: {directory}")
    
    command = f'ssh -i "{ssh_key}" -p {port} -o StrictHostKeyChecking=no {username}@localhost "mkdir -p {directory}"'
    success, output = run_command(command)
    
    if success:
        logger.info(f"已創建目錄: {directory}")
        return True
    else:
        logger.error(f"無法創建目錄: {directory}")
        return False

def deploy_file(ssh_key, username, port, local_file, remote_file):
    """將單個文件部署到遠程設備"""
    logger.info(f"部署文件: {local_file} -> {remote_file}")
    
    if not os.path.exists(local_file):
        logger.warning(f"本地文件不存在: {local_file}")
        return False
    
    # 如果需要，創建遠程目錄
    remote_dir = os.path.dirname(remote_file)
    if remote_dir:
        create_remote_directory(ssh_key, username, port, remote_dir)
    
    # 複製文件
    command = f'scp -i "{ssh_key}" -P {port} -o StrictHostKeyChecking=no "{local_file}" {username}@localhost:"{remote_file}"'
    success, output = run_command(command, verbose=False)
    
    if success:
        logger.info(f"已部署: {os.path.basename(local_file)}")
        return True
    else:
        logger.error(f"無法部署: {os.path.basename(local_file)}")
        return False

def install_requirements(ssh_key, username, port, requirements_file):
    """在Device Cloud上安裝Python依賴項"""
    logger.info("安裝Python依賴項...")
    
    # 首先檢查Python是否可用
    check_cmd = f'ssh -i "{ssh_key}" -p {port} -o StrictHostKeyChecking=no {username}@localhost "python --version"'
    success, output = run_command(check_cmd)
    
    if not success:
        logger.error("在Device Cloud上未檢測到Python")
        return False
    
    logger.info(f"檢測到Python: {output.strip()}")
    
    # 安裝依賴項
    install_cmd = f'ssh -i "{ssh_key}" -p {port} -o StrictHostKeyChecking=no {username}@localhost "pip install -r {requirements_file}"'
    success, output = run_command(install_cmd)
    
    if success:
        logger.info("已成功安裝依賴項")
        return True
    else:
        logger.error(f"安裝依賴項失敗: {output}")
        return False

def get_deployment_files():
    """獲取要部署的文件列表，按優先級排序"""
    # Windows兼容文件 (ASCII版本)
    windows_files = [
        # 核心檢測模塊
        "unified_ai_detector_windows.py",
        "dragon_x_fall_detection_system_windows.py",
        "fall_detector.py",
        "fall_detector_opencv.py",
        
        # AWS虛擬相機集成
        "aws_virtual_camera_rfc.py",
        "aws_virtual_camera_test_windows.py",
        
        # Windows版示範程式
        "snapdragon_realtime_demo_windows.py", 
        "snapdragon_video_demo_windows.py",
        "snapdragon_performance_benchmark_windows.py",
        
        # 主要Windows版應用程式
        "main_windows.py",
        
        # 融合系統
        "fusion_trigger.py",
        
        # 依賴項文件
        "requirements_windows.txt",
        
        # 文檔
        "MAC_TO_WINDOWS_MIGRATION_GUIDE.md",
        "DEVICE_CLOUD_DEMO_GUIDE.md",
        "README.md"
    ]
    
    # 可能不相容的文件（可選）
    mac_files = [
        # Mac版本的原始檔案
        "main.py", 
        "whisper_infer.py",
        "unified_ai_detector.py",
        "dragon_x_fall_detection_system.py",
        "qai_hub_demo.py"
    ]
    
    return windows_files

def deploy_files(ssh_key, username, port, target_dir, files, source_dir):
    """將多個文件部署到遠程設備"""
    logger.info(f"將 {len(files)} 個文件部署到 {username}@localhost:{target_dir}")
    
    # 創建目標目錄
    create_remote_directory(ssh_key, username, port, target_dir)
    
    # 部署文件
    successful = 0
    failed = 0
    
    for local_file in files:
        local_path = os.path.join(source_dir, local_file)
        remote_path = f"{target_dir}/{local_file.replace('/', '\\')}"
        
        if deploy_file(ssh_key, username, port, local_path, remote_path):
            successful += 1
        else:
            failed += 1
    
    logger.info(f"部署摘要: {successful} 成功, {failed} 失敗")
    return successful, failed

def deploy_test_images(ssh_key, username, port, target_dir, source_dir):
    """將測試圖像部署到遠程設備"""
    # 檢查目錄中是否有圖像文件
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    image_files = []
    
    for filename in os.listdir(source_dir):
        if any(filename.lower().endswith(ext) for ext in image_extensions):
            image_files.append(filename)
    
    if not image_files:
        logger.warning("未找到測試圖像，跳過")
        return 0, 0
    
    # 創建目標目錄
    create_remote_directory(ssh_key, username, port, target_dir)
    
    logger.info(f"找到 {len(image_files)} 個測試圖像來部署")
    
    # 部署圖像
    successful = 0
    failed = 0
    
    for local_file in image_files:
        local_path = os.path.join(source_dir, local_file)
        remote_path = f"{target_dir}/{local_file}"
        
        if deploy_file(ssh_key, username, port, local_path, remote_path):
            successful += 1
        else:
            failed += 1
    
    logger.info(f"測試圖像部署摘要: {successful} 成功, {failed} 失敗")
    return successful, failed

def main():
    parser = argparse.ArgumentParser(description="將Dragon X跌倒偵測系統部署到Qualcomm Device Cloud")
    parser.add_argument("--ssh-key", default=DEFAULT_SSH_KEY, help=f"SSH密鑰文件 (預設: {DEFAULT_SSH_KEY})")
    parser.add_argument("--username", default=DEFAULT_USERNAME, help=f"SSH用戶名 (預設: {DEFAULT_USERNAME})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"SSH端口 (預設: {DEFAULT_PORT})")
    parser.add_argument("--target-dir", default=DEFAULT_TARGET_DIR, help=f"目標目錄 (預設: {DEFAULT_TARGET_DIR})")
    parser.add_argument("--source-dir", default=os.getcwd(), help="源目錄 (預設: 當前目錄)")
    parser.add_argument("--install-deps", action="store_true", help="安裝Python依賴項")
    parser.add_argument("--skip-test-images", action="store_true", help="跳過部署測試圖像")
    parser.add_argument("--test-connection", action="store_true", help="僅測試SSH連接")
    
    args = parser.parse_args()
    
    # 檢查SSH連接
    if not check_ssh_connection(args.ssh_key, args.username, args.port):
        logger.error("沒有SSH連接，無法繼續")
        return 1
    
    if args.test_connection:
        logger.info("連接測試成功，退出")
        return 0
    
    # 獲取要部署的文件
    files = get_deployment_files()
    
    # 部署文件
    deploy_files(args.ssh_key, args.username, args.port, args.target_dir, files, args.source_dir)
    
    # 部署測試圖像（如果需要）
    if not args.skip_test_images:
        deploy_test_images(args.ssh_key, args.username, args.port, args.target_dir, args.source_dir)
    
    # 安裝依賴項（如果需要）
    if args.install_deps:
        requirements_file = f"{args.target_dir}/requirements_windows.txt"
        install_requirements(args.ssh_key, args.username, args.port, requirements_file)
    
    logger.info("部署完成")
    
    # 打印說明
    print("\n部署完成！")
    print("\n要在設備上運行主要示範，請執行:")
    print(f"  python {args.target_dir}\\main_windows.py")
    print("\n要測試相機功能:")
    print(f"  python {args.target_dir}\\aws_virtual_camera_test_windows.py --list")
    print("\n要運行實時演示:")
    print(f"  python {args.target_dir}\\snapdragon_realtime_demo_windows.py")
    print("\n要查看平台兼容性指南:")
    print(f"  notepad {args.target_dir}\\MAC_TO_WINDOWS_MIGRATION_GUIDE.md")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
