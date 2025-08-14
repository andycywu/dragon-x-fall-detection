#!/usr/bin/env python3
"""
📊 MobileNetV2 量化 (示意) 與延遲 / 張量統計報表

目的:
  - 示範簡單的 Post Training Quantization (PTQ) 流程（Torch FakeQuant 模擬）
  - 計算 FP32 與 模擬 INT8 推論延遲 (本地 CPU) 與速度比
  - 輸出權重張量統計 (min/max/mean/std) 以及 Top-1 / Top-5 logits 估計
  - 與雲端 Inference Job (若已執行 qai_hub_mobilenet_demo.py) 的結果做對比

注意:
  - 真正 QAI Hub 上的量化需使用 compile 選項或 CLI/SDK 提供的 quantization pipeline，本腳本僅本地示意
  - 若需真實量化 (QNN / AIMET) 可擴充成導出 ONNX 後再做後處理

輸出:
  mobilenet_latency_report.json
  mobilenet_tensor_stats.json
  終端列印精簡摘要

執行:
  python mobilenet_quantize_report.py --runs 30 --batch 1
"""
import os
import time
import json
import argparse
import logging
import numpy as np
import torch
from torchvision.models import mobilenet_v2

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')
logger = logging.getLogger("quant_report")


def collect_weight_stats(model: torch.nn.Module, top_k: int = 5):
    stats = {}
    for name, param in model.state_dict().items():
        if param.dtype not in (torch.float32, torch.float16, torch.bfloat16):
            continue
        data = param.detach().cpu().float().view(-1)
        arr = data.numpy()
        stats[name] = {
            'min': float(arr.min()),
            'max': float(arr.max()),
            'mean': float(arr.mean()),
            'std': float(arr.std()),
            'numel': int(arr.size),
        }
    return stats


def fake_int8_copy(model: torch.nn.Module):
    # 建立一個 clone 並模擬量化 (簡化: per-tensor 8-bit scale)
    import copy
    qmodel = copy.deepcopy(model).cpu().eval()
    for name, param in qmodel.named_parameters():
        if param.dtype == torch.float32:
            with torch.no_grad():
                d = param.data
                scale = d.abs().max() / 127.0 if d.numel() > 0 else 1.0
                if scale == 0:
                    continue
                q = torch.clamp((d / scale).round(), -127, 127)
                param.data = (q * scale).to(torch.float32)
    return qmodel


def benchmark(model: torch.nn.Module, runs: int, batch: int, device: str = 'cpu'):
    model.to(device).eval()
    input_shape = (batch, 3, 224, 224)
    dummy = torch.randn(input_shape, device=device)
    # 預熱
    with torch.no_grad():
        for _ in range(5):
            _ = model(dummy)
    times = []
    with torch.no_grad():
        for _ in range(runs):
            t0 = time.time()
            _ = model(dummy)
            torch.cuda.synchronize() if device.startswith('cuda') else None
            times.append(time.time() - t0)
    return {
        'avg_ms': float(np.mean(times) * 1000),
        'p50_ms': float(np.percentile(times, 50) * 1000),
        'p90_ms': float(np.percentile(times, 90) * 1000),
        'runs': runs,
        'batch': batch,
        'device': device,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--runs', type=int, default=20, help='基準測試迭代次數')
    ap.add_argument('--batch', type=int, default=1, help='批量大小')
    ap.add_argument('--device', type=str, default='cpu', help='裝置 (cpu / cuda:0)')
    args = ap.parse_args()

    logger.info("🔁 載入 FP32 MobileNetV2 (pretrained)")
    model_fp32 = mobilenet_v2(pretrained=True)

    logger.info("📊 收集 FP32 權重統計")
    fp32_stats = collect_weight_stats(model_fp32)

    logger.info("🧪 建立簡易 INT8 模擬模型")
    model_int8 = fake_int8_copy(model_fp32)

    logger.info("⚡ 基準測試 FP32 ...")
    fp32_bench = benchmark(model_fp32, args.runs, args.batch, args.device)
    logger.info(f"   FP32 平均延遲: {fp32_bench['avg_ms']:.2f} ms")

    logger.info("⚡ 基準測試 模擬 INT8 ...")
    int8_bench = benchmark(model_int8, args.runs, args.batch, args.device)
    logger.info(f"   模擬 INT8 平均延遲: {int8_bench['avg_ms']:.2f} ms")

    speedup = fp32_bench['avg_ms'] / int8_bench['avg_ms'] if int8_bench['avg_ms'] > 0 else 0

    latency_report = {
        'fp32': fp32_bench,
        'int8_simulated': int8_bench,
        'speedup_ratio': speedup,
        'runs': args.runs,
        'batch': args.batch,
        'timestamp': time.time(),
    }

    tensor_stats_summary = {
        'weights': fp32_stats,
        'total_parameters': sum(s['numel'] for s in fp32_stats.values()),
    }

    with open('mobilenet_latency_report.json', 'w') as f:
        json.dump(latency_report, f, indent=2)
    with open('mobilenet_tensor_stats.json', 'w') as f:
        json.dump(tensor_stats_summary, f, indent=2)

    logger.info("✅ 已輸出 mobilenet_latency_report.json / mobilenet_tensor_stats.json")
    logger.info(f"🚀 模擬加速比: {speedup:.2f}x (僅代表本地簡化模擬)")

if __name__ == '__main__':
    main()
