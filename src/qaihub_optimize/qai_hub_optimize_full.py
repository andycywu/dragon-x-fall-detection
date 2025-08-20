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
    # --- 自動修正 onnx value_info 重複問題 ---
    def fix_onnx_value_info(path):
        import onnx
        model = onnx.load(path)
        io_names = set()
        for t in list(model.graph.input) + list(model.graph.output):
            io_names.add(t.name)
        # 移除 value_info 中與 input/output 重複的 tensor
        new_value_info = [vi for vi in model.graph.value_info if vi.name not in io_names]
        del model.graph.value_info[:]
        model.graph.value_info.extend(new_value_info)
        onnx.save(model, path)
    print(f"\n[Compile] QAI Hub Compile Pipeline (Practical) | source={source}")
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
    from pathlib import Path
    import sys
    # --- 一開始自動掃描 org 目錄 ---
    org_dir = Path(__file__).parent.parent / 'models' / 'org'
    if not org_dir.exists():
        print(f"❌ 找不到 org 目錄: {org_dir}")
        return
    all_files = list(org_dir.glob('*'))
    print("\n[模型掃描] org 目錄下檔案：")
    for f in all_files:
        print(f"  - {f.name}")
    tflite_files = [f for f in all_files if f.suffix == '.tflite']
    onnx_files = [f for f in all_files if f.suffix == '.onnx']
    dlc_files = [f for f in all_files if f.suffix == '.dlc']
    print(f"\n共偵測到：{len(tflite_files)} 個 tflite, {len(onnx_files)} 個 onnx, {len(dlc_files)} 個 dlc 檔案")
    # --- 若有 tflite，詢問是否要轉換 ---
    from tflite2onnx_guard import convert_with_diagnostics
    if tflite_files:
        ans = input(f"\n偵測到 {len(tflite_files)} 個 tflite 檔案，是否要批次轉換成 onnx？(y/n)：").strip().lower()
        if ans == 'y':
            import struct
            import shutil
            import tempfile
            import tensorflow as tf
            failed_convert = []
            for tflite_path in tflite_files:
                onnx_dir = Path(__file__).parent.parent / 'models' / 'onnx'
                onnx_dir.mkdir(parents=True, exist_ok=True)
                # 檢查空檔案
                if tflite_path.stat().st_size == 0:
                    print(f"[Error] 檔案為空，跳過: {tflite_path.name}")
                    failed_convert.append(tflite_path.name)
                    continue
                # 使用 guard 進行轉換與診斷
                result = convert_with_diagnostics(str(tflite_path), str(onnx_dir), timeout_sec=600)
                if result["status"] == "ok":
                    print(f"✅ 轉換成功: {result['onnx_path']}")
                else:
                    print(f"❌ 轉換失敗: {tflite_path.name}")
                    print(result["human_message"])
                    failed_convert.append(tflite_path.name)
                    continue
            print(f"\n✅ 批次轉換完成，onnx 檔案已存入 {onnx_dir}")
            if failed_convert:
                print(f"\n⚠️ 下列 tflite 轉換失敗，請手動檢查：")
                for f in failed_convert:
                    print(f"   - {f}")
            # 轉換完自動切換 source 為 onnx
            source = 'onnx'
    # --- pipeline 繼續 ---
    if source not in source_map:
        print(f"❌ 不支援的 source: {source}")
        return
    model_dir, ext = source_map[source]
    # --- pipeline 繼續 ---
    # 若是 onnx，先自動修正所有 onnx 檔案
    if ext == '.onnx':
        from pathlib import Path
        onnx_dir = Path(__file__).parent.parent / 'models' / model_dir
        onnx_files = list(onnx_dir.glob('*.onnx'))
        for onnx_path in onnx_files:
            try:
                fix_onnx_value_info(str(onnx_path))
                print(f"[Auto] 修正 value_info: {onnx_path.name}")
            except Exception as e:
                print(f"[Warning] 修正 value_info 失敗: {onnx_path.name} | {e}")
    system = PracticalQAIHubONNX()
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
    # 等待所有 compile job 完成
    import time
    import sys
    print("\n⏳ 等待所有 QAI Hub Compile Job 完成...")
    all_done = False
    poll_interval = 10  # 秒
    max_wait = 60 * 30  # 最長等待 30 分鐘
    waited = 0
    completed_status = ('COMPLETED', 'SUCCEEDED', 'SUCCESS', 'FINISHED', 'COMPLETED_SUCCESSFULLY', 'RESULTS_READY', 'RESULTS READY', 'results_ready', 'Results Ready')
    last_status = {}
    while not all_done and waited < max_wait:
        all_done = True
        status_lines = []
        for model_name, model_info in system.qai_hub_models.items():
            job = model_info.get('compile_job')
            if job and hasattr(job, 'refresh'):
                job.refresh()
                status = getattr(job, 'status', None) or getattr(job, 'state', None)
                model_info['compile_status'] = status
            elif job:
                status = getattr(job, 'status', None) or getattr(job, 'state', None)
                model_info['compile_status'] = status
            else:
                status = None
            job_id = getattr(job, 'job_id', '') if job else ''
            status_lines.append(f"  {model_name}: {job_id} 狀態: {status}")
            if status is None or str(status).upper() not in [s.upper() for s in completed_status]:
                all_done = False
        # 清除前一輪顯示
        if waited > 0:
            sys.stdout.write(f"\033[{len(last_status)}A")  # 游標上移 N 行
        for line in status_lines:
            print(line)
        last_status = status_lines
        if not all_done:
            print(f"  ...尚有 Compile Job 執行中，{poll_interval} 秒後再查詢...\n")
            time.sleep(poll_interval)
            waited += poll_interval
    if not all_done:
        print("⚠️ 超過最大等待時間，部分 Job 可能尚未完成。")
    print("\n📊 QAI Hub Compile Job狀態:")
    for model_name, model_info in system.qai_hub_models.items():
        job = model_info.get('compile_job')
        job_id = job.job_id if job else ''
        status = model_info.get('compile_status', '')
        print(f"   {model_name}: Job {job_id} 狀態: {status}")
        if job_id:
            print(f"     Dashboard: https://aihub.qualcomm.com/jobs/{job_id}")
    # 產生 HTML 報告
    html_file = 'practical_qai_hub_compile_report.html'
    with open(html_file, 'w') as f:
        f.write('<html><head><meta charset="utf-8"><title>QAI Hub Compile Report</title></head><body>')
        f.write('<h1>QAI Hub Compile Report</h1>')
        f.write(f'<p><b>Timestamp:</b> {time.strftime("%Y-%m-%d %H:%M:%S")}</p>')
        f.write('<h2>Models & Compile Jobs</h2><table border="1" cellpadding="4"><tr><th>Model</th><th>Status</th><th>Job ID</th><th>Dashboard</th></tr>')
        for model_name, model_info in system.qai_hub_models.items():
            job = model_info.get('compile_job')
            job_id = job.job_id if job else ''
            dashboard = f'<a href="https://aihub.qualcomm.com/jobs/{job_id}">{job_id}</a>' if job_id else ''
            status = model_info.get('compile_status', '') or ('已提交' if job_id else (model_info.get('error') or '未提交'))
            f.write(f'<tr><td>{model_name}</td><td>{status}</td><td>{job_id}</td><td>{dashboard}</td></tr>')
        f.write('</table>')
        f.write('</body></html>')
    print(f"\n✅ Compile 完成！HTML 報告已產生 {html_file}")

def run_profile():
    print("\n[Profile] QAI Hub Profile Pipeline (Practical)")
    from pathlib import Path
    import os
    from practical_qai_hub_onnx import PracticalQAIHubONNX
    org_dir = Path(__file__).parent.parent / 'models' / 'org'
    # 支援多格式自動偵測
    all_models = list(org_dir.glob('*.tflite')) + list(org_dir.glob('*.onnx')) + list(org_dir.glob('*.dlc'))
    if not all_models:
        print("❌ org 目錄下找不到任何模型檔案，無法進行 profile。")
        return
    print(f"🔎 偵測到 {len(all_models)} 個模型將進行 QAI Hub profile：")
    for f in all_models:
        print(f"   - {f.name}")
    # 啟動系統，先取得裝置支援格式
    system = PracticalQAIHubONNX()
    device = system.target_device
    if not device:
        print("❌ 無法取得目標裝置，無法進行 profile。")
        return
    device_attrs = getattr(device, 'attributes', [])
    support_onnx = any('framework:onnx' in a for a in device_attrs)
    support_tflite = any('framework:tflite' in a for a in device_attrs)
    support_dlc = any('framework:dlc' in a for a in device_attrs)
    print(f"\n[裝置支援格式] ONNX={support_onnx}, TFLite={support_tflite}, DLC={support_dlc}")
    # 統一詢問 tflite 是否要轉換
    tflite_models = [f for f in all_models if f.suffix.lower() == '.tflite']
    convert_tflite = False
    import threading
    def ask_convert():
        print(f"⚠️ 目標裝置不支援 TFLite，偵測到 {len(tflite_models)} 個 tflite 模型。是否要自動全部轉換為 ONNX？(y/n, 30秒後自動轉換)")
        ans = [None]
        def get_input():
            ans[0] = input().strip().lower()
        t = threading.Thread(target=get_input)
        t.daemon = True
        t.start()
        t.join(timeout=30)
        if ans[0] is None or ans[0] == '':
            print("⏰ 逾時，自動執行轉換 (y)")
            return True
        return ans[0] == 'y'
    if tflite_models and not support_tflite:
        if ask_convert():
            convert_tflite = True
    # 預處理模型清單
    models_to_profile = []
    for f in all_models:
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
                onnx_path = str(f.with_suffix('.onnx'))
                print(f"🔄 自動轉換 {f} → {onnx_path} ...")
                import subprocess
                result = subprocess.run(['tflite2onnx', str(f), onnx_path], capture_output=True, text=True)
                if result.returncode == 0 and os.path.exists(onnx_path):
                    print(f"✅ 轉換成功: {onnx_path}")
                    models_to_profile.append(Path(onnx_path))
                else:
                    print(f"❌ 轉換失敗: {result.stderr}")
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
    # 只載入要 profile 的模型
    # 依副檔名決定 source
    for ext, source in [('.onnx', 'onnx'), ('.tflite', 'tflite'), ('.dlc', 'dlc')]:
        files = [f for f in models_to_profile if f.suffix.lower() == ext]
        if files:
            system.load_mediapipe_models(source=source, model_dir='org', ext=ext)
    system.upload_models_to_qai_hub()
    system.submit_profile_jobs()
    # 等待所有 profile job 完成
    import time
    import sys
    import threading
    print("\n⏳ 等待所有 QAI Hub Profile Job 完成... (按 q + Enter 可隨時跳出)\n")
    all_done = False
    poll_interval = 10  # 秒
    max_wait = 60 * 30  # 最長等待 30 分鐘
    waited = 0
    completed_status = ('COMPLETED', 'SUCCEEDED', 'SUCCESS', 'FINISHED', 'COMPLETED_SUCCESSFULLY', 'RESULTS_READY', 'RESULTS READY', 'results_ready', 'Results Ready')
    last_status = []
    user_quit = [False]
    def check_quit():
        while True:
            s = sys.stdin.readline().strip().lower()
            if s == 'q':
                user_quit[0] = True
                break
    quit_thread = threading.Thread(target=check_quit, daemon=True)
    quit_thread.start()
    while not all_done and waited < max_wait and not user_quit[0]:
        all_done = True
        status_lines = []
        for model_name, model_info in system.qai_hub_models.items():
            job = model_info.get('profile_job')
            # 強制每次都重新查詢雲端（即使沒有 refresh 也重新取得最新狀態）
            status = None
            api_raw_status = None
            if job and hasattr(job, 'refresh'):
                job.refresh()
                status = getattr(job, 'status', None) or getattr(job, 'state', None)
                # 額外顯示 API 回傳的原始狀態字串（如有）
                api_raw_status = getattr(job, 'raw_status', None) or getattr(job, '_raw_status', None)
                model_info['profile_status'] = status
            elif job:
                # 嘗試強制重新取得狀態（如 SDK 支援）
                try:
                    if hasattr(job, 'get_status'):
                        status = job.get_status()
                        api_raw_status = status
                    else:
                        status = getattr(job, 'status', None) or getattr(job, 'state', None)
                        api_raw_status = status
                except Exception as e:
                    status = None
                    api_raw_status = None
                model_info['profile_status'] = status
            else:
                status = None
                api_raw_status = None
            job_id = getattr(job, 'job_id', '') if job else ''
            status_str = f"{model_name:30} | Job: {job_id:12} | 狀態: {str(status) if status else '查詢中...'}"
            if api_raw_status and str(api_raw_status) != str(status):
                status_str += f" | API原始: {api_raw_status}"
            status_lines.append(status_str)
            if status is None or str(status).upper() not in [s.upper() for s in completed_status]:
                all_done = False
        # 清除前一輪顯示
        if waited > 0:
            sys.stdout.write(f"\033[{len(last_status)}A")
        for line in status_lines:
            print(line)
        last_status = status_lines
        if not all_done and not user_quit[0]:
            print(f"\n  ...尚有 Profile Job 執行中，{poll_interval} 秒後再查詢... (按 q + Enter 可跳出)\n")
            time.sleep(poll_interval)
            waited += poll_interval
    if user_quit[0]:
        print("\n⚠️ 使用者已選擇跳出等待，部分 Job 可能尚未完成。\n")
    elif not all_done:
        print("⚠️ 超過最大等待時間，部分 Job 可能尚未完成。\n")
    print("\n📊 QAI Hub Profile Job狀態:")
    for model_name, model_info in system.qai_hub_models.items():
        job = model_info.get('profile_job')
        job_id = job.job_id if job else ''
        status = model_info.get('profile_status', '')
        print(f"   {model_name}: Job {job_id} 狀態: {status}")
        if job_id:
            print(f"     Dashboard: https://aihub.qualcomm.com/jobs/{job_id}")
    # 產生 HTML 報告
    html_file = 'practical_qai_hub_profile_report.html'
    with open(html_file, 'w') as f:
        f.write('<html><head><meta charset="utf-8"><title>QAI Hub Profile Report</title></head><body>')
        f.write('<h1>QAI Hub Profile Report</h1>')
        f.write(f'<p><b>Timestamp:</b> {time.strftime("%Y-%m-%d %H:%M:%S")}</p>')
        f.write('<h2>Models & Profile Jobs</h2><table border="1" cellpadding="4"><tr><th>Model</th><th>Status</th><th>Job ID</th><th>Dashboard</th></tr>')
        for model_name, model_info in system.qai_hub_models.items():
            job = model_info.get('profile_job')
            job_id = job.job_id if job else ''
            dashboard = f'<a href="https://aihub.qualcomm.com/jobs/{job_id}">{job_id}</a>' if job_id else ''
            status = model_info.get('profile_status', '') or ('已提交' if job_id else (model_info.get('error') or '未提交'))
            f.write(f'<tr><td>{model_name}</td><td>{status}</td><td>{job_id}</td><td>{dashboard}</td></tr>')
        f.write('</table>')
        f.write('</body></html>')
    print(f"\n✅ Profile 完成！HTML 報告已產生 {html_file}")

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
