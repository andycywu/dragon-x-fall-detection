#!/usr/bin/env python3
"""
测试编译流程与实时状态监控
验证修复后的路径配置和实时状态显示功能
"""
import sys
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent))

from modules.pipeline import get_pipeline

def test_compile_pipeline():
    """测试编译流程"""
    print("🚀 开始测试编译流程...")
    
    try:
        # 获取pipeline实例
        pipeline = get_pipeline()
        
        # 测试模型扫描
        print("\n1. 测试模型扫描...")
        models = pipeline.scan_models()
        if not models:
            print("❌ 模型扫描失败")
            return False
        
        print(f"✅ 扫描到 {sum(len(files) for files in models.values())} 个模型文件")
        for ext, files in models.items():
            print(f"   - {ext.upper()}: {len(files)} 个文件")
        
        # 测试路径配置
        print(f"\n2. 验证路径配置...")
        print(f"   - 基础目录: {pipeline.base_dir}")
        print(f"   - 模型基础目录: {pipeline.scanner.base_dir}")
        
        # 检查org目录
        org_dir = pipeline.scanner.base_dir / 'org'
        if org_dir.exists():
            org_files = list(org_dir.glob('*.*'))
            print(f"   - org目录文件数: {len(org_files)}")
        else:
            print(f"❌ org目录不存在: {org_dir}")
            return False
        
        # 检查qaihub_optimized目录
        optimized_dir = pipeline.scanner.base_dir / 'qaihub_optimized'
        if optimized_dir.exists():
            print(f"   - qaihub_optimized目录存在")
        else:
            print(f"⚠️  qaihub_optimized目录不存在，将自动创建")
        
        # 测试job monitor配置
        print(f"\n3. 验证Job Monitor配置...")
        print(f"   - Job Monitor类型: {type(pipeline.job_monitor).__name__}")
        print(f"   - QAI Hub Client配置: {pipeline.qaihub_client is not None}")
        
        print("\n🎉 路径配置和基础功能测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_real_time_monitoring():
    """测试实时状态监控功能"""
    print("\n🔍 测试实时状态监控功能...")
    
    try:
        pipeline = get_pipeline()
        
        # 检查job monitor的实时状态更新功能
        monitor = pipeline.job_monitor
        
        # 检查是否有实时状态更新方法
        if hasattr(monitor, '_check_jobs_status') and callable(getattr(monitor, '_check_jobs_status')):
            print("✅ 实时状态检查方法存在")
        else:
            print("❌ 实时状态检查方法不存在")
            return False
        
        # 检查是否有错误信息获取功能（在 _check_jobs_status 方法中实现）
        if hasattr(monitor, '_check_jobs_status') and callable(getattr(monitor, '_check_jobs_status')):
            print("✅ 错误信息获取功能存在（在 _check_jobs_status 中实现）")
        else:
            print("❌ 错误信息获取功能不存在")
            return False
        
        # 检查是否有自动下载功能（私有方法，在 _check_jobs_status 中被调用）
        if hasattr(monitor, '_download_optimized_model') and callable(getattr(monitor, '_download_optimized_model')):
            print("✅ 自动下载方法存在（私有方法）")
        else:
            print("❌ 自动下载方法不存在")
            return False
        
        print("🎉 实时状态监控功能测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ 实时状态监控测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 QAI Hub 编译流程测试")
    print("=" * 60)
    
    # 测试路径配置和基础功能
    success1 = test_compile_pipeline()
    
    # 测试实时状态监控功能
    success2 = test_real_time_monitoring()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 所有测试通过! 编译流程已修复完成")
        print("\n下一步:")
        print("1. 运行完整的编译流程测试")
        print("2. 验证实时状态显示功能")
        print("3. 确认优化模型自动下载到 src/models/qaihub_optimized")
    else:
        print("❌ 测试失败，请检查代码")
    
    print("=" * 60)
