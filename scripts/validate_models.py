"""
Validate ONNX model files under src/models.
- Try to load with onnx.load and onnx.checker.check_model
- Try to create an ONNX Runtime InferenceSession (CPU) to catch runtime load errors
Writes reports/model_validation_report.json with per-model results.
"""
import os
import json
import traceback
from glob import glob

ROOT = os.path.abspath(os.path.dirname(__file__) + '/../')
MODELS_GLOB = os.path.join(ROOT, 'src', 'models', '**', '*.onnx')
OUT = os.path.join(ROOT, 'reports', 'model_validation_report.json')

try:
    import onnx
except Exception:
    onnx = None

try:
    import onnxruntime as ort
except Exception:
    ort = None


def check_model(path: str):
    rec = {'model': path, 'onnx_load': None, 'onnx_check': None, 'ort_session': None, 'errors': []}
    # if path is a directory (some exported bundles are named .onnx but are folders),
    # attempt to find an inner model.onnx and validate that instead
    if os.path.isdir(path):
        inner = os.path.join(path, 'model.onnx')
        if os.path.exists(inner):
            rec['model'] = inner
            path = inner
        else:
            rec['onnx_load'] = 'path_is_dir_no_model_onx'
            rec['errors'].append(f"Directory found but no model.onnx inside: {path}")
            return rec
    # try onnx.load
    if onnx is None:
        rec['onnx_load'] = 'onnx_not_installed'
        rec['errors'].append('onnx package not installed')
    else:
        try:
            m = onnx.load(path)
            rec['onnx_load'] = 'ok'
            try:
                onnx.checker.check_model(m)
                rec['onnx_check'] = 'ok'
            except Exception as e:
                rec['onnx_check'] = 'check_failed'
                rec['errors'].append('onnx.checker: ' + str(e))
        except Exception as e:
            rec['onnx_load'] = 'load_failed'
            rec['errors'].append('onnx.load: ' + str(e))
    # try onnxruntime session
    if ort is None:
        rec['ort_session'] = 'onnxruntime_not_installed'
        rec['errors'].append('onnxruntime not installed')
    else:
        try:
            # delay import heavy providers
            sess = ort.InferenceSession(path, providers=['CPUExecutionProvider'])
            rec['ort_session'] = 'ok'
        except Exception as e:
            rec['ort_session'] = 'create_failed'
            # capture full traceback for easier triage
            rec['errors'].append('ort.InferenceSession: ' + ''.join(traceback.format_exception_only(type(e), e)).strip())
    return rec


def main():
    files = glob(MODELS_GLOB, recursive=True)
    files = sorted(set(files))
    results = []
    for f in files:
        try:
            r = check_model(f)
        except Exception as e:
            r = {'model': f, 'error_unexpected': str(e)}
        results.append(r)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as fo:
        json.dump(results, fo, indent=2, ensure_ascii=False)
    # print short summary
    total = len(results)
    ok_onnx = sum(1 for r in results if r.get('onnx_load') == 'ok' and r.get('onnx_check') == 'ok')
    ok_ort = sum(1 for r in results if r.get('ort_session') == 'ok')
    print(f"Validated {total} models: onnx_ok={ok_onnx}, ort_ok={ok_ort}")
    print('Report written to', OUT)

if __name__ == '__main__':
    main()
