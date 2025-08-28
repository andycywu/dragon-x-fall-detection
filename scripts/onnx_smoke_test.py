#!/usr/bin/env python3
import os
import glob
import json
import traceback
import sys
import numpy as np

sys.path.insert(0, os.path.abspath('.'))
from src.infer_demo_Mac.adapters.pose_adapter import PoseAdapter
import onnxruntime as ort
import sys


def main():
    repo_root = os.getcwd()
    rpt_dir = os.path.join(repo_root, 'reports')
    os.makedirs(rpt_dir, exist_ok=True)
    report = {'models_tested': []}

    # optional single-model arg
    argv_model = None
    if len(sys.argv) > 1:
        argv_model = sys.argv[1]

    raw_candidates = sorted(glob.glob('src/models/**/*', recursive=True))
    # normalize candidates: prefer actual .onnx files; if a directory name ends with .onnx,
    # prefer its inner model.onnx or first .onnx descendant
    candidates = []
    for p in raw_candidates:
        try:
            if os.path.isfile(p) and p.lower().endswith('.onnx'):
                candidates.append(p)
            elif os.path.isdir(p) and p.lower().endswith('.onnx'):
                # try model.onnx inside directory
                m = os.path.join(p, 'model.onnx')
                if os.path.isfile(m):
                    candidates.append(m)
                else:
                    inner = sorted(glob.glob(os.path.join(p, '**', '*.onnx'), recursive=True))
                    for ip in inner:
                        if os.path.isfile(ip):
                            candidates.append(ip)
                            break
        except Exception:
            continue
    if not candidates and not argv_model:
        print('No ONNX models found under src/models and no model arg provided')
        sys.exit(1)

    if argv_model:
        # resolve argv_model if it's a directory or shorthand
        if os.path.isdir(argv_model) and argv_model.lower().endswith('.onnx'):
            m = os.path.join(argv_model, 'model.onnx')
            if os.path.isfile(m):
                chosen = [m]
            else:
                inner = sorted(glob.glob(os.path.join(argv_model, '**', '*.onnx'), recursive=True))
                chosen = inner[:1] if inner else [argv_model]
        else:
            chosen = [argv_model]
    else:
        chosen = []
        for p in candidates:
            if 'litehrnet' in p.lower() or 'pose_landmarks' in p.lower():
                chosen.append(p)
                break
        chosen.extend(candidates[:3])
        chosen = list(dict.fromkeys(chosen))[:3]

    adapter = PoseAdapter()

    def try_resolve_model_path(m):
        """Return a resolved absolute path for model m if possible.

        If m exists as file, return abspath. If not, try to find a candidate in
        src/models that matches the basename or name prefix. Otherwise return m
        unchanged (caller will mark file_ok False).
        """
        try:
            if os.path.isabs(m) and os.path.isfile(m):
                return os.path.abspath(m)
            # if m is a directory ending with .onnx, prefer inner model.onnx or first inner .onnx
            if os.path.isdir(m) and m.lower().endswith('.onnx'):
                cand = os.path.join(m, 'model.onnx')
                if os.path.isfile(cand):
                    return os.path.abspath(cand)
                inner = sorted(glob.glob(os.path.join(m, '**', '*.onnx'), recursive=True))
                for ip in inner:
                    if os.path.isfile(ip):
                        return os.path.abspath(ip)
            # if the path exists relative to repo root
            abs_try = os.path.abspath(m)
            if os.path.isfile(abs_try):
                return abs_try
            # try to match by basename inside src/models folder
            b = os.path.basename(m)
            name_no_ext = os.path.splitext(b)[0]
            for base in ['src/models', 'src/models/deploy', 'src/models/qaihub_optimized']:
                for ip in sorted(glob.glob(os.path.join(base, '**', b), recursive=True)):
                    if os.path.isfile(ip):
                        return os.path.abspath(ip)
                for ip in sorted(glob.glob(os.path.join(base, '**', f'{name_no_ext}*.onnx'), recursive=True)):
                    if os.path.isfile(ip):
                        return os.path.abspath(ip)
            # fallback: return original
            return m
        except Exception:
            return m


    for model in chosen:
        # normalize model var to a resolved absolute path when possible
        try:
            resolved = try_resolve_model_path(model)
            model = resolved
        except Exception:
            pass
        entry = {
            'model': model,
            'provider_used': None,
            'attempted_providers': [],
            'provider_errors': {},
            'inference_ok': False,
            'adapt_ok': False,
            'kps_shape': None,
            'error': None,
            'file_ok': True,
            'onnx_parse_error': None,
        }

        try:
            # quick file checks (model should already be resolved when possible)
            if not os.path.isfile(model):
                entry['file_ok'] = False
                entry['error'] = f'Model file not found: {model}'
                # keep the reported model path absolute if possible
                entry['model'] = os.path.abspath(model) if not os.path.isabs(model) else model
                report['models_tested'].append(entry)
                continue
            try:
                if os.path.getsize(model) == 0:
                    entry['file_ok'] = False
                    entry['error'] = f'Model file is empty: {model}'
                    report['models_tested'].append(entry)
                    continue
            except Exception:
                pass

            # optional ONNX parse check for clearer diagnostics
            try:
                import onnx
                try:
                    _ = onnx.load(model)
                except Exception as e:
                    entry['onnx_parse_error'] = repr(e)
                    # continue — some runtime builds accept models parsing fails here; record and try session creation
            except Exception:
                # onnx package not installed; skip parse check
                pass

            avail = ort.get_available_providers()
            pref_order = ['CoreMLExecutionProvider','SNPEExecutionProvider','QNNExecutionProvider','CUDAExecutionProvider','TensorrtExecutionProvider','DMLExecutionProvider','OpenVINOExecutionProvider','CPUExecutionProvider']
            used = [p for p in pref_order if p in avail]
            if not used:
                used = avail or ['CPUExecutionProvider']

            sess = None
            # try providers in order and capture errors
            for prov in used:
                entry['attempted_providers'].append(prov)
                try:
                    sess = ort.InferenceSession(model, providers=[prov])
                    entry['provider_used'] = prov
                    break
                except Exception as e:
                    entry['provider_errors'][prov] = traceback.format_exc()
                    continue

            if sess is None:
                # final attempt with CPU to surface error
                try:
                    entry['attempted_providers'].append('CPUExecutionProvider')
                    sess = ort.InferenceSession(model, providers=['CPUExecutionProvider'])
                    entry['provider_used'] = 'CPUExecutionProvider'
                except Exception as e:
                    entry['provider_errors']['CPUExecutionProvider'] = traceback.format_exc()
                    entry['error'] = traceback.format_exc()
                    report['models_tested'].append(entry)
                    continue

            # if we have a session, try a dummy inference
            inp = sess.get_inputs()[0]
            ishape = [1 if (not isinstance(d,int) or d<=0) else int(d) for d in inp.shape]
            arr = np.zeros(tuple(ishape), dtype=np.float32)
            outs = sess.run(None, {inp.name: arr})
            entry['inference_ok'] = True

            outputs = {}
            for o, meta in zip(outs if outs else [], sess.get_outputs()):
                try:
                    outputs[meta.name] = np.array(o).tolist()
                except Exception:
                    outputs[meta.name] = None

            try:
                kps = adapter.adapt_named_onnx_outputs(os.path.splitext(os.path.basename(model))[0].lower(), outputs, img_w=640, img_h=480)
                if kps is None:
                    kps = adapter.detect_and_adapt(list(outputs.values()), 640, 480)
                if kps is not None:
                    entry['adapt_ok'] = True
                    arrk = np.array(kps)
                    entry['kps_shape'] = list(arrk.shape)
            except Exception as e:
                entry['error'] = repr(e)

        except Exception as e:
            entry['error'] = traceback.format_exc()
        report['models_tested'].append(entry)

    # ensure report model paths are absolute for easier UI matching
    for m in report['models_tested']:
        try:
            if isinstance(m.get('model'), str) and not os.path.isabs(m.get('model')):
                m['model'] = os.path.abspath(m['model'])
        except Exception:
            pass

    out_path = os.path.join(rpt_dir, 'onnx_smoke_test.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f'Wrote report to {out_path}')
    # print a short per-model status summary
    for m in report['models_tested']:
        print(f"MODEL: {m['model']} | provider: {m.get('provider_used')} | infer_ok: {m.get('inference_ok')} | adapt_ok: {m.get('adapt_ok')} | kps_shape: {m.get('kps_shape')}")


if __name__ == '__main__':
    main()
