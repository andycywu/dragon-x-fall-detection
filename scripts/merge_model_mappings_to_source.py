#!/usr/bin/env python3
"""Generate a patch-like JSON from config/model_mappings.json that can be
used to merge suggested mappings into source-level `model_output_map`.

This script does NOT modify source files; it writes `scripts/model_mappings_patch.json`
which lists normalized keys and the mapping dicts. Use it to review before applying.
"""
import os
import json
import sys


def main():
    repo_root = os.getcwd()
    cfg = os.path.join(repo_root, 'config', 'model_mappings.json')
    out = os.path.join(repo_root, 'scripts', 'model_mappings_patch.json')
    if not os.path.exists(cfg):
        print('No config/model_mappings.json found; nothing to do')
        return
    try:
        with open(cfg, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print('Failed to read config/model_mappings.json:', e)
        sys.exit(1)

    out_obj = {}
    for k, v in (data.items() if isinstance(data, dict) else []):
        try:
            nk = str(k).lower()
            if nk.endswith('.onnx'):
                nk = nk[:-5]
            if isinstance(v, dict):
                out_obj[nk] = v
        except Exception:
            continue

    with open(out, 'w', encoding='utf-8') as f:
        json.dump(out_obj, f, indent=2)

    print('Wrote patch to', out)


if __name__ == '__main__':
    main()
