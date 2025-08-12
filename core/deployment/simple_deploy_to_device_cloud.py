#!/usr/bin/env python3
"""
簡易Windows Device Cloud部署腳本
專門針對Dragon X Fall Detection系統的快速部署
"""

import os
import sys
import subprocess
import argparse
import logging
from pathlib import Path

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 預設設定
DEFAULT_SSH_KEY = "qdc_id_key.pem"
DEFAULT_USERNAME = "qualcomm"
DEFAULT_PORT = 22
DEFAULT_TARGET_DIR = "C:/dragon_x_fall_detection"

def run_command(command, verbose=True):
    """執行Shell命令並返回輸出"""
    if verbose:
        logger.info(f"執行: {command}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"命令執行失敗，代碼 {result.returncode}")
            logger.error(f"錯誤: {result.stderr}")
            return False, result.stderr
        
        return True, result.stdout
    except Exception as e:
        logger.error(f"執行命令時出現異常: {e}")
        return False, str(e)

def check_ssh_connection(ssh_key, username, host, port):
    """檢查SSH連接是否正常"""
    logger.info("檢查到設備的SSH連接...")
    
    command = f'ssh -i "{ssh_key}" -p {port} -o StrictHostKeyChecking=no -o ConnectTimeout=5 {username}@{host} "echo 連接成功"'
    success, output = run_command(command)
    
    if success:
        logger.info("SSH連接成功!")
        return True
    else:
        logger.error("SSH連接失敗")
        return False

def create_remote_directory(ssh_key, username, host, port, directory):
    """在遠程設備上創建目錄"""
    logger.info(f"創建遠程目錄: {directory}")
    
    command = f'ssh -i "{ssh_key}" -p {port} -o StrictHostKeyChecking=no {username}@{host} "mkdir -p {directory}"'
    success, output = run_command(command)
    
    if success:
        logger.info(f"已創建目錄: {directory}")
        return True
    else:
        logger.error(f"無法創建目錄: {directory}")
        return False

def deploy_file(ssh_key, username, host, port, local_file, remote_file):
    """部署單個文件到遠程設備"""
    logger.info(f"部署文件: {local_file} -> {remote_file}")
    
    if not os.path.exists(local_file):
        logger.warning(f"本地文件不存在: {local_file}")
        return False
    
    # 創建遠程目錄
    remote_dir = os.path.dirname(remote_file)
    if remote_dir:
        create_remote_directory(ssh_key, username, host, port, remote_dir)
    
    # 複製文件
    command = f'scp -i "{ssh_key}" -P {port} -o StrictHostKeyChecking=no "{local_file}" {username}@{host}:"{remote_file}"'
    success, output = run_command(command, verbose=False)
    
    if success:
        logger.info(f"已部署: {os.path.basename(local_file)}")
        return True
    else:
        logger.error(f"無法部署: {os.path.basename(local_file)}")
        return False

def get_windows_compatible_files():
    """獲取Windows相容文件列表"""
    return [
        # Windows相容版本
        "main_windows.py",
        "unified_ai_detector_windows.py",
        "dragon_x_fall_detection_system_windows.py",
        "aws_virtual_camera_test_windows.py",
        "snapdragon_realtime_demo_windows.py", 
        "snapdragon_video_demo_windows.py",
        "snapdragon_performance_benchmark_windows.py",
        
        # 備用檢測器
        "fall_detector.py",
        "fall_detector_opencv.py",
        
        # 通用組件
        "fusion_trigger.py",
        "whisper_infer.py",
        
        # 配置文件
        "requirements_windows.txt",
        "cross_platform_config.json",
        
        # 文檔
        "README.md",
        "DEVICE_CLOUD_DEMO_GUIDE.md",
        "MAC_TO_WINDOWS_MIGRATION_GUIDE.md"
    ]

def deploy_files(ssh_key, username, host, port, target_dir, source_dir):
    """部署多個文件到遠程設備"""
    files = get_windows_compatible_files()
    logger.info(f"部署 {len(files)} 個文件到 {username}@{host}:{target_dir}")
    
    # 創建目標目錄
    create_remote_directory(ssh_key, username, host, port, target_dir)
    
    # 部署文件
    successful = 0
    failed = 0
    
    for local_file in files:
        local_path = os.path.join(source_dir, local_file)
        remote_path = f"{target_dir}/{local_file.replace('/', '\\')}"
        
        if deploy_file(ssh_key, username, host, port, local_path, remote_path):
            successful += 1
        else:
            failed += 1
    
    logger.info(f"部署摘要: {successful} 成功, {failed} 失敗")
    return successful, failed

def main():
    parser = argparse.ArgumentParser(description="簡易Dragon X Fall Detection系統部署腳本")
    parser.add_argument("--ssh-key", default=DEFAULT_SSH_KEY, help=f"SSH密鑰文件 (預設: {DEFAULT_SSH_KEY})")
    parser.add_argument("--username", default=DEFAULT_USERNAME, help=f"SSH用戶名 (預設: {DEFAULT_USERNAME})")
    parser.add_argument("--host", default="localhost", help="主機地址 (預設: localhost)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"SSH端口 (預設: {DEFAULT_PORT})")
    parser.add_argument("--target-dir", default=DEFAULT_TARGET_DIR, help=f"目標目錄 (預設: {DEFAULT_TARGET_DIR})")
    parser.add_argument("--source-dir", default=os.getcwd(), help="源目錄 (預設: 當前目錄)")
    parser.add_argument("--test-connection", action="store_true", help="僅測試SSH連接")
    
    args = parser.parse_args()
    
    # 檢查SSH連接
    if not check_ssh_connection(args.ssh_key, args.username, args.host, args.port):
        logger.error("沒有SSH連接，無法繼續")
        return 1
    
    if args.test_connection:
        logger.info("連接測試成功，退出")
        return 0
    
    # 部署文件
    deploy_files(args.ssh_key, args.username, args.host, args.port, args.target_dir, args.source_dir)
    
    logger.info("部署完成")
    
    # 打印說明
    print("\n部署完成!")
    print("\n要在設備上執行核心演示，請執行:")
    print(f"  python {args.target_dir}\\main_windows.py --camera_id 1")
    print("\n要測試攝像頭功能:")
    print(f"  python {args.target_dir}\\aws_virtual_camera_test_windows.py --list")
    print("\n要運行即時演示:")
    print(f"  python {args.target_dir}\\snapdragon_realtime_demo_windows.py")
    print("\n要運行視頻處理演示:")
    print(f"  python {args.target_dir}\\snapdragon_video_demo_windows.py --video test.mp4")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
