#!/usr/bin/env python3
"""
📘 QAI Hub 官方 Post-Install 教程風格範例 (MobileNetV2)

步驟: Compile → Profile → Inference → Download
目標設備: Snapdragon X Elite CRD (若找不到則回退第一台可用設備)

需求套件: qai-hub, torch, torchvision, requests, pillow, numpy
執行前請確保已設置環境變數 QAI_HUB_API_TOKEN 或在 client.ini 中完成 configure。

用法:
  python qai_hub_mobilenet_demo.py
  python qai_hub_mobilenet_demo.py --device "Snapdragon X Elite CRD" --skip-profile

參數:
  --device          指定設備名稱 (預設優先找含 Snapdragon X Elite 的名稱)
  --skip-profile    跳過 profiling 步驟 (僅 compile + inference)
  --download-path   指定下載 onnx 模型路徑 (預設 mobilenet_v2.onnx)
  --timeout         單一 Job 等待逾時秒數 (預設 900 秒)

"""
import os
import sys
import time
import argparse
import logging
import json
import numpy as np
import requests
from PIL import Image

import torch
from torchvision.models import mobilenet_v2
import qai_hub as hub

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')
logger = logging.getLogger("mobilenet_demo")


def wait_job(job, label: str, timeout: int = 900, poll: int = 5):
    start = time.time()
    while True:
        try:
            job.wait(timeout=1)
            logger.info(f"✅ {label} 完成 (job_id={job.job_id})")
            return True
        except Exception:
            pass
        if time.time() - start > timeout:
            logger.error(f"⏰ {label} 等待逾時 {timeout}s")
            return False
        if int(time.time() - start) % poll == 0:
            logger.info(f"⏳ 等待 {label} ... 已 {int(time.time()-start)}s")
        time.sleep(1)


def pick_device(preferred_name: str | None):
    devices = hub.get_devices()
    if not devices:
        raise RuntimeError("無可用設備")
    if preferred_name:
        for d in devices:
            if d.name.strip().lower() == preferred_name.strip().lower():
                logger.info(f"🎯 使用指定設備: {d.name}")
                return d
    # 優先包含 Snapdragon X Elite
    for d in devices:
        if 'snapdragon x elite' in d.name.lower():
            logger.info(f"🎯 選擇 Snapdragon X Elite: {d.name}")
            return d
    logger.info(f"⚠️ 未找到 Snapdragon X Elite，回退第一台: {devices[0].name}")
    return devices[0]


def run_pipeline(args):
    # Step 0: 準備 & 驗證 token
    api_token = os.getenv('QAI_HUB_API_TOKEN')
    if not api_token:
        logger.warning("⚠️ 沒有 QAI_HUB_API_TOKEN，假設已透過 client.ini 配置")

    device = pick_device(args.device)

    # Step 1: 載入預訓練 Torch 模型並 trace
    logger.info("🔁 載入 torchvision MobileNetV2 (pretrained)")
    torch_model = mobilenet_v2(pretrained=True)
    torch_model.eval()
    input_shape = (1, 3, 224, 224)
    example_input = torch.rand(input_shape)
    traced_torch_model = torch.jit.trace(torch_model, example_input)
    logger.info("✅ TorchScript trace 完成")

    # Step 2: Compile
    logger.info("🚀 提交 Compile Job (target_runtime=onnx)...")
    compile_job = hub.submit_compile_job(
        model=traced_torch_model,
        device=device,
        input_specs=dict(image=input_shape),
        options="--target_runtime onnx",
    )
    wait_job(compile_job, "Compile")

    target_model = compile_job.get_target_model()

    # Step 3: Profile (可選)
    profile_job = None
    if not args.skip_profile:
        logger.info("📈 提交 Profile Job ...")
        try:
            profile_job = hub.submit_profile_job(model=target_model, device=device)
            wait_job(profile_job, "Profile")
        except Exception as e:
            logger.warning(f"⚠️ Profile 失敗 (略過): {e}")
    else:
        logger.info("⏭️ 跳過 Profile Job")

    # Step 4: Inference
    logger.info("🧪 提交雲端 Inference Job ...")
    sample_image_url = (
        "https://qaihub-public-assets.s3.us-west-2.amazonaws.com/apidoc/input_image1.jpg"
    )
    response = requests.get(sample_image_url, stream=True, timeout=30)
    response.raise_for_status()
    response.raw.decode_content = True
    image = Image.open(response.raw).resize((224, 224))
    input_array = np.expand_dims(
        np.transpose(np.array(image, dtype=np.float32) / 255.0, (2, 0, 1)), axis=0
    )

    inference_job = hub.submit_inference_job(
        model=target_model,
        device=device,
        inputs=dict(image=[input_array]),
    )
    wait_job(inference_job, "Inference")
    on_device_output = inference_job.download_output_data()

    output_name = list(on_device_output.keys())[0]
    out = on_device_output[output_name][0]
    on_device_probabilities = np.exp(out) / np.sum(np.exp(out), axis=1)

    classes_url = "https://qaihub-public-assets.s3.us-west-2.amazonaws.com/apidoc/imagenet_classes.txt"
    cls_resp = requests.get(classes_url, stream=True, timeout=30)
    cls_resp.raise_for_status()
    cls_resp.raw.decode_content = True
    categories = [str(s.strip()) for s in cls_resp.raw]

    logger.info("🏁 Top-5 On-Device predictions:")
    top5 = np.argsort(on_device_probabilities[0])[-5:][::-1]
    for c in top5:
        logger.info(f"  {c:>4} {categories[c]:25s} {on_device_probabilities[0][c]:6.2%}")

    # Step 5: Download compiled (target) model
    download_path = args.download_path
    logger.info(f"💾 下載目標模型到 {download_path} ...")
    target_model.download(download_path)
    logger.info("✅ 下載完成")

    summary = {
        "device": device.name,
        "compile_job_id": compile_job.job_id,
        "profile_job_id": getattr(profile_job, 'job_id', None),
        "inference_job_id": inference_job.job_id,
        "download_path": download_path,
        "timestamp": time.time(),
    }
    with open('mobilenet_demo_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info("📝 Summary 已寫入 mobilenet_demo_summary.json")


def parse_args():
    p = argparse.ArgumentParser(description="QAI Hub MobileNet Demo")
    p.add_argument('--device', type=str, default=None, help='指定設備名稱')
    p.add_argument('--skip-profile', action='store_true', help='跳過 Profiling')
    p.add_argument('--download-path', type=str, default='mobilenet_v2.onnx', help='下載模型檔案路徑')
    p.add_argument('--timeout', type=int, default=900, help='單一 Job 等待逾時秒數')
    return p.parse_args()


if __name__ == '__main__':
    try:
        args = parse_args()
        run_pipeline(args)
    except Exception as e:
        logger.error(f"❌ Demo 失敗: {e}")
        raise
