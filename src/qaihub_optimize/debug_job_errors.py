#!/usr/bin/env python3
"""
调试 QAI Hub Job 对象，提取详细的错误信息
用于解决编译任务失败但无法获取详细错误信息的问题
"""
import sys
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent))

from modules.qaihub_client import QAIHubClient
from modules.pipeline import QAIHubPipeline

def debug_job_objects():
    """调试 Job 对象，提取详细的错误信息"""
    print("🔍 开始调试 QAI Hub Job 对象...")
    
    try:
        # 初始化 pipeline
        pipeline = QAIHubPipeline()
        
        # 扫描模型
        models = pipeline.scan_models()
        if not models:
            print("❌ 没有找到可用的模型文件")
            return False
        
        # 加载模型
        loaded = pipeline.qaihub_client.load_models('onnx', 'org', '.onnx')
        if not loaded:
            print("❌ 加载模型失败")
            return False
        
        # 上传模型
        if not pipeline.qaihub_client.upload_models():
            print("❌ 上传模型失败")
            return False
        
        # 提交编译任务
        if not pipeline.qaihub_client.submit_compilation_jobs():
            print("❌ 提交编译任务失败")
            return False
        
        print("\n🔄 等待任务开始执行...")
        time.sleep(10)  # 等待任务开始
        
        # 检查所有编译任务的状态
        for model_name, model_info in pipeline.qaihub_client.qai_hub_models.items():
            if 'compile_job' not in model_info:
                continue
                
            job = model_info['compile_job']
            print(f"\n🔍 检查任务: {model_name}")
            print(f"   Job ID: {getattr(job, 'job_id', 'N/A')}")
            
            # 刷新任务状态
            try:
                if hasattr(job, 'refresh'):
                    job.refresh()
                    print("✅ 任务状态已刷新")
            except Exception as refresh_error:
                print(f"❌ 刷新任务状态失败: {refresh_error}")
            
            # 获取任务状态
            status = getattr(job, 'status', None)
            print(f"   Status: {status}")
            
            # 深度检查 Job 对象的所有属性
            print("   🔍 检查 Job 对象的所有属性:")
            job_attrs = [attr for attr in dir(job) if not attr.startswith('_')]
            for attr in job_attrs:
                try:
                    value = getattr(job, attr)
                    if callable(value):
                        print(f"     {attr}: <method>")
                    else:
                        print(f"     {attr}: {repr(value)}")
                except Exception as e:
                    print(f"     {attr}: <error: {e}>")
            
            # 检查 Status 对象的所有属性（如果存在）
            if status is not None:
                print("   🔍 检查 Status 对象的所有属性:")
                status_attrs = [attr for attr in dir(status) if not attr.startswith('_')]
                for attr in status_attrs:
                    try:
                        value = getattr(status, attr)
                        if callable(value):
                            print(f"     {attr}: <method>")
                        else:
                            print(f"     {attr}: {repr(value)}")
                    except Exception as e:
                        print(f"     {attr}: <error: {e}>")
            
            # 尝试获取详细的错误信息
            print("   🔍 尝试获取详细的错误信息:")
            
            # 方法1: 检查 status.error
            if hasattr(status, 'error') and status.error:
                print(f"     status.error: {status.error}")
            
            # 方法2: 检查 job.error
            if hasattr(job, 'error') and job.error:
                print(f"     job.error: {job.error}")
            
            # 方法3: 检查 job.failure_reason
            if hasattr(job, 'failure_reason') and job.failure_reason:
                print(f"     job.failure_reason: {job.failure_reason}")
            
            # 方法4: 检查 job.status_message
            if hasattr(job, 'status_message') and job.status_message:
                print(f"     job.status_message: {job.status_message}")
            
            # 方法5: 检查 job.get_status() 的返回值
            if hasattr(job, 'get_status'):
                try:
                    detailed_status = job.get_status()
                    print(f"     job.get_status(): {detailed_status}")
                    if hasattr(detailed_status, 'error') and detailed_status.error:
                        print(f"     detailed_status.error: {detailed_status.error}")
                except Exception as e:
                    print(f"     job.get_status() error: {e}")
            
            # 方法6: 检查 job.details 或类似属性
            if hasattr(job, 'details'):
                print(f"     job.details: {job.details}")
            
            # 方法7: 检查 job.metadata
            if hasattr(job, 'metadata'):
                print(f"     job.metadata: {job.metadata}")
            
            print("-" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ 调试过程发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def inspect_failed_jobs():
    """检查失败的 Job 对象"""
    print("\n🔍 检查失败的 Job 对象...")
    
    try:
        import qai_hub as hub
        
        # 获取所有失败的 Job
        failed_jobs = []
        try:
            # 尝试使用不同的方法来获取 Job 列表
            if hasattr(hub, 'get_job_summaries'):
                job_summaries = hub.get_job_summaries()
                for js in job_summaries:
                    if hasattr(js, 'status') and hasattr(js.status, 'code'):
                        if str(js.status.code).upper() in ['FAILED', 'ERROR']:
                            failed_jobs.append(js)
            elif hasattr(hub, 'get_jobs'):
                jobs = hub.get_jobs()
                for job in jobs:
                    if hasattr(job, 'status') and hasattr(job.status, 'code'):
                        if str(job.status.code).upper() in ['FAILED', 'ERROR']:
                            failed_jobs.append(job)
        except Exception as e:
            print(f"❌ 获取 Job 列表失败: {e}")
        
        print(f"📊 找到 {len(failed_jobs)} 个失败的 Job")
        
        # 只检查前几个失败的 Job 以避免输出过多
        for i, job in enumerate(failed_jobs[:5]):
            print(f"\n🔍 失败的 Job {i+1}:")
            print(f"   Job ID: {getattr(job, 'job_id', 'N/A')}")
            print(f"   Name: {getattr(job, 'name', 'N/A')}")
            
            # 获取详细的状态信息
            if hasattr(job, 'get_status'):
                try:
                    status = job.get_status()
                    print(f"   Status Code: {getattr(status, 'code', 'N/A')}")
                    print(f"   Status Message: {getattr(status, 'message', 'N/A')}")
                    
                    # 深度检查 Status 对象的所有属性
                    if status is not None:
                        print("   🔍 检查 Status 对象的所有属性:")
                        status_attrs = [attr for attr in dir(status) if not attr.startswith('_')]
                        for attr in status_attrs:
                            try:
                                value = getattr(status, attr)
                                if callable(value):
                                    print(f"     {attr}: <method>")
                                else:
                                    print(f"     {attr}: {repr(value)}")
                            except Exception as e:
                                print(f"     {attr}: <error: {e}>")
                    
                    if hasattr(status, 'error') and status.error:
                        print(f"   Error: {status.error}")
                except Exception as e:
                    print(f"   Status Error: {e}")
            
            # 深度检查 Job 对象的所有属性
            print("   🔍 检查 Job 对象的所有属性:")
            job_attrs = [attr for attr in dir(job) if not attr.startswith('_')]
            for attr in job_attrs:
                try:
                    value = getattr(job, attr)
                    if callable(value):
                        print(f"     {attr}: <method>")
                    else:
                        print(f"     {attr}: {repr(value)}")
                except Exception as e:
                    print(f"     {attr}: <error: {e}>")
            
            # 检查其他可能的错误属性
            error_sources = ['error', 'failure_reason', 'status_message', 'details', 'metadata', 'failure_details']
            for attr in error_sources:
                if hasattr(job, attr):
                    value = getattr(job, attr)
                    if value:
                        print(f"   {attr}: {value}")
            
            print("-" * 40)
        
        return True
        
    except Exception as e:
        print(f"❌ 检查失败 Job 时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import time
    
    print("=" * 80)
    print("🤖 QAI Hub Job 对象调试工具")
    print("=" * 80)
    
    # 运行调试
    success1 = debug_job_objects()
    
    # 检查失败的 Job
    success2 = inspect_failed_jobs()
    
    print("\n" + "=" * 80)
    if success1 or success2:
        print("✅ 调试完成！请查看上面的输出以了解 Job 对象的结构")
        print("\n💡 建议:")
        print("1. 查看 Job 和 Status 对象的所有属性")
        print("2. 找到包含详细错误信息的属性")
        print("3. 修改 job_monitor.py 中的错误提取逻辑")
    else:
        print("❌ 调试失败")
    
    print("=" * 80)
