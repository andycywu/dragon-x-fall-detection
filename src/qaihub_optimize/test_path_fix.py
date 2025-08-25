#!/usr/bin/env python3
"""
测试路径修复脚本
验证pipeline.py中的路径计算是否正确
"""
import sys
from pathlib import Path

# 模拟pipeline.py中的路径计算逻辑
def test_path_calculation():
    print("🔍 测试路径计算逻辑...")
    
    # 模拟当前工作目录是 src/qaihub_optimize
    base_dir = Path.cwd()
    print(f"当前工作目录: {base_dir}")
    
    # 测试路径计算逻辑（新的优先级顺序）
    if (base_dir.parent.parent / 'models').exists():
        models_base_dir = base_dir.parent.parent / 'models'
        print(f"✅ 找到项目根目录的 models 目录: {models_base_dir}")
    elif (base_dir.parent / 'models').exists():
        models_base_dir = base_dir.parent / 'models'
        print(f"✅ 找到上级 models 目录: {models_base_dir}")
    elif (base_dir / 'models').exists():
        models_base_dir = base_dir / 'models'
        print(f"✅ 找到本地 models 目录: {models_base_dir}")
    else:
        models_base_dir = base_dir
        print(f"⚠️  未找到 models 目录，使用当前目录: {models_base_dir}")
    
    # 检查org目录是否存在
    org_dir = models_base_dir / 'org'
    if org_dir.exists():
        print(f"✅ 找到 org 目录: {org_dir}")
        org_files = list(org_dir.glob('*.*'))
        print(f"📁 org 目录中的文件: {[f.name for f in org_files]}")
    else:
        print(f"❌ 未找到 org 目录: {org_dir}")
    
    # 检查qaihub_optimized目录是否存在
    optimized_dir = models_base_dir / 'qaihub_optimized'
    if optimized_dir.exists():
        print(f"✅ 找到 qaihub_optimized 目录: {optimized_dir}")
    else:
        print(f"⚠️  未找到 qaihub_optimized 目录: {optimized_dir}")

if __name__ == "__main__":
    test_path_calculation()
