#!/usr/bin/env python3
"""Probe ONNX models under src/models/qaihub_optimized:
- list inputs/outputs metadata
- run a best-effort single inference with synthetic data
"""
import os
import glob
import json
import numpy as np
import traceback

try:
    import onnxruntime as ort
except Exception as e:
    print('onnxruntime not available:', e)
    raise

BASE = os.path.dirname(os.path.dirname(__file__))
MODELS_DIR = os.path.join(BASE, 'models', 'qaihub_optimized')


def find_models():
    if not os.path.isdir(MODELS_DIR):
        return []
    return sorted(glob.glob(os.path.join(MODELS_DIR, '**', '*.onnx'), recursive=True))


def make_input_for_shape(shape):
    # shape is a list-like possibly containing None or strings
    s = []
    for d in shape:
        try:
            if d is None:
                s.append(1)
            else:
                s.append(int(d))
        except Exception:
            s.append(1)
    # heuristics
    if len(s) == 4:
        # [N,C,H,W] -> ensure C==3
        if s[1] in (0, 1):
            s[1] = 3
        if s[2] <= 0:
            s[2] = 224
        if s[3] <= 0:
            s[3] = 224
    if len(s) == 3:
        # assume [C,H,W] or [H,W,C] -> prefer [C,H,W]
        if s[0] in (0, 1):
            s[0] = 3
        # ensure reasonable H/W
        if s[-1] <= 0:
            s[-1] = 224
    if len(s) == 0:
        s = [1]
    return tuple(s)


def probe_model(path):
    print('\n==== MODEL:', path)
    try:
        sess = ort.InferenceSession(path, providers=['CPUExecutionProvider'])
    except Exception as e:
        print('Failed to load model:', e)
        traceback.print_exc()
        return

    inputs = sess.get_inputs()
    outputs = sess.get_outputs()
    meta = {
        'path': path,
        'inputs': [{'name': i.name, 'shape': list(i.shape), 'type': str(i.type)} for i in inputs],
        'outputs': [{'name': o.name, 'shape': list(o.shape), 'type': str(o.type)} for o in outputs]
    }
    print(json.dumps(meta, indent=2))

    # prepare feed dict
    feed = {}
    for i in inputs:
        name = i.name
        shape = list(i.shape)
        target = make_input_for_shape(shape)
        # create float32 zeros by default
        arr = np.zeros(target, dtype=np.float32)
        # if channel likely first dim smaller than 4, fill with random to vary
        feed[name] = arr

    print('Running sample inference...')
    try:
        out = sess.run(None, feed)
        for idx, o in enumerate(out):
            a = np.array(o)
            print(f' output[{idx}] shape={a.shape} dtype={a.dtype}  sample=', end='')
            flat = a.flatten()
            print(flat[:10].tolist())
    except Exception as e:
        print('Sample inference failed:', e)
        traceback.print_exc()


def main():
    models = find_models()
    if not models:
        print('No ONNX models found in', MODELS_DIR)
        return
    for m in models:
        probe_model(m)


if __name__ == '__main__':
    main()
