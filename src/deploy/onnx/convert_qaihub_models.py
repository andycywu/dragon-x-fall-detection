#!/usr/bin/env python3
"""Batch convert QAI Hub compiled ONNX assets under src/models/qaihub_optimized

This script scans for .onnx files or .onnx-named directories and runs build_deployable_asset.py
on each candidate that appears to be a compiled asset. It produces convert_report.json.
"""
from pathlib import Path
import json
import subprocess
import os
import shutil
import hashlib
import sys

# compute repository root (three levels up from this script: repo/.../src/deploy/onnx)
ROOT = Path(__file__).resolve().parents[3]
MODELS_DIR = ROOT / 'src' / 'models' / 'qaihub_optimized'
OUT_REPORT = Path(__file__).resolve().parent / 'convert_report.json'
OUT_DIR = ROOT / 'src' / 'models' / 'deploy'
OUT_DIR.mkdir(parents=True, exist_ok=True)

candidates = []
for p in MODELS_DIR.rglob('*'):
    if p.is_file() and p.suffix == '.onnx':
        candidates.append(str(p))
    elif p.is_dir() and p.name.lower().endswith('.onnx'):
        # prefer model.onnx
        m = p / 'model.onnx'
        if m.exists():
            candidates.append(str(m))
        else:
            for f in p.rglob('*.onnx'):
                candidates.append(str(f))

print(f'Found {len(candidates)} candidate ONNX files to process')

report = []
script = Path(__file__).resolve().parent / 'build_deployable_asset.py'
for c in sorted(set(candidates)):
    print('Processing', c)
    try:
        src = Path(c)
        # create a deterministic unique filename/dir in OUT_DIR
        rel = src.relative_to(MODELS_DIR)
        safe_name = str(rel).replace(os.sep, '__')

        # If the source has sibling files (e.g. model.data) or lives inside a *.onnx directory,
        # copy the entire parent directory so external_data files are preserved.
        deploy_model_path = None
        parent = src.parent
        siblings = [p for p in parent.iterdir() if p.is_file() and p.name != src.name]
        if parent.name.lower().endswith('.onnx') or len(siblings) > 0:
            # copy whole directory
            target_dir = OUT_DIR / (safe_name + '__dir')
            if target_dir.exists():
                shutil.rmtree(target_dir)
            shutil.copytree(parent, target_dir)
            deploy_model_path = target_dir / src.name
        else:
            # single-file model: copy just the file
            target = OUT_DIR / safe_name
            if not target.suffix == '.onnx':
                target = target.with_suffix('.onnx')
            shutil.copy2(src, target)
            deploy_model_path = target

        # run upstream converter on the copied model path
        res = subprocess.run([
            sys.executable,
            str(Path(__file__).resolve().parent / 'build_deployable_asset.py'),
            '-f', str(deploy_model_path)
        ], capture_output=True, text=True, check=False)
        out = (res.stdout or '') + '\n' + (res.stderr or '')

        # Record deploy path and optional meta written by converter
        deploy_path = str(deploy_model_path)
        meta_json = None
        meta = Path(deploy_path).with_suffix(Path(deploy_path).suffix + '.meta.json')
        if meta.exists():
            with open(meta, 'r') as mf:
                try:
                    meta_json = json.load(mf)
                except Exception:
                    meta_json = {'error': 'failed to parse meta json'}

        report.append({'source': c, 'deployed_copy': deploy_path, 'meta': meta_json, 'stdout': out})
    except Exception as e:
        report.append({'source': c, 'error': str(e)})

with open(OUT_REPORT, 'w') as f:
    json.dump(report, f, indent=2)

print('Wrote report to', OUT_REPORT)
