"""
Scan ONNX models under src/models and produce a JSON report with output shapes
and simple heuristics to guess keypoint counts/layouts.

Run inside the project's inference venv (e.g. source .venv_infer/bin/activate)

Usage:
    python3 scripts/auto_map_models.py

Outputs:
    reports/model_scan.json
    reports/model_scan_summary.md
"""
import os, json
from pathlib import Path

ROOT = Path('src/models')
OUT_JSON = Path('reports/model_scan.json')
OUT_MD = Path('reports/model_scan_summary.md')

def guess_from_shape(shape):
    # shape: list or tuple of ints or '?'
    # return dict with guesses
    guesses = []
    try:
        s = tuple(int(x) if isinstance(x,(int,)) else None for x in shape)
    except Exception:
        s = tuple(None for _ in shape)
    # common patterns
    # 1) (1, N, 3) => N keypoints with (x,y,score)
    if len(s) >= 3 and s[0] in (1, None) and s[-1] == 3 and s[-2] is not None:
        guesses.append({'type': 'seq_kps_3', 'kps': s[-2], 'layout': '(x,y,score)'})
    # 2) (1, N, 2) => N keypoints x,y
    if len(s) >= 3 and s[0] in (1, None) and s[-1] == 2 and s[-2] is not None:
        guesses.append({'type': 'seq_kps_2', 'kps': s[-2], 'layout': '(x,y)'})
    # 3) flat (1, M) where M divisible by 3 or 2
    if len(s) >= 2 and s[0] in (1, None) and s[1] is not None:
        M = s[1]
        if M % 3 == 0:
            guesses.append({'type': 'flat', 'kps': M//3, 'layout': 'flattened (x,y,score) or (x,y,z) per kp'})
        if M % 2 == 0:
            guesses.append({'type': 'flat', 'kps': M//2, 'layout': 'flattened (x,y) per kp'})
    # 4) heatmap channel last dim small (e.g., 39 channels) -> suspect keypoint heatmaps
    if len(s) >= 3 and s[-1] is not None and s[-1] <= 256 and s[-1] >= 10:
        ch = s[-1]
        # if channel small and divisible by 3
        if ch % 3 == 0:
            guesses.append({'type': 'heatmap_channels', 'channels': ch, 'kps': ch//3, 'layout': 'channels as (x,y,score) maps'})
        elif ch % 1 == 0:
            guesses.append({'type': 'heatmap_channels', 'channels': ch, 'kps': None, 'layout': 'channels maybe per-kp heatmap'})
    return guesses


def scan_models():
    import onnx
    import onnxruntime as ort
    import numpy as np

    results = {}
    onnx_files = []
    for p in ROOT.rglob('*.onnx'):
        onnx_files.append(p)
    onnx_files = sorted(onnx_files)

    for p in onnx_files:
        key = str(p)
        results[key] = {'path': key, 'onnx_load_ok': False, 'graph_outputs': [], 'ort_ok': False, 'ort_outputs': [], 'guesses': []}
        try:
            m = onnx.load(p)
            results[key]['onnx_load_ok'] = True
            for out in m.graph.output:
                dims = []
                for d in out.type.tensor_type.shape.dim:
                    v = d.dim_value
                    dims.append(v if v>0 else '?')
                results[key]['graph_outputs'].append({'name': out.name, 'shape': dims})
        except Exception as e:
            results[key]['onnx_load_err'] = str(e)
        try:
            sess = ort.InferenceSession(str(p), providers=['CPUExecutionProvider'])
            results[key]['ort_ok'] = True
            ins = sess.get_inputs(); outs = sess.get_outputs()
            in_meta = []
            for i in ins:
                in_meta.append({'name': i.name, 'shape': [s if (isinstance(s,int) and s>0) else '?' for s in i.shape], 'type': str(i.type)})
            out_meta = []
            for o in outs:
                out_meta.append({'name': o.name, 'shape': [s if (isinstance(s,int) and s>0) else '?' for s in o.shape], 'type': str(o.type)})
            results[key]['ort_inputs'] = in_meta
            results[key]['ort_outputs'] = out_meta
            # dummy run
            feed = {}
            for i in ins:
                shp = []
                for s in i.shape:
                    if isinstance(s,int) and s>0:
                        shp.append(int(s))
                    else:
                        shp.append(1)
                feed[i.name] = np.zeros(shp, dtype=np.float32)
            try:
                res = sess.run(None, feed)
                res_meta = []
                for r in res:
                    res_meta.append({'shape': getattr(r,'shape',None), 'dtype': str(getattr(r,'dtype',None))})
                results[key]['dummy_run'] = res_meta
            except Exception as e:
                results[key]['dummy_run_err'] = str(e)
            # heuristics from output shapes
            guesses = []
            for o in results[key].get('ort_outputs', []):
                g = guess_from_shape(o['shape'])
                if g:
                    guesses.append({'output_name': o['name'], 'shape': o['shape'], 'guesses': g})
            results[key]['guesses'] = guesses
        except Exception as e:
            results[key]['ort_err'] = str(e)
    return results

if __name__ == '__main__':
    os.makedirs('reports', exist_ok=True)
    r = scan_models()
    OUT_JSON.write_text(json.dumps(r, indent=2))
    # summary md
    lines = ['# Model scan summary\n']
    for k,v in sorted(r.items())[:200]:
        lines.append('## ' + k)
        lines.append('- onnx_load_ok: ' + str(v.get('onnx_load_ok',False)))
        lines.append('- ort_ok: ' + str(v.get('ort_ok',False)))
        if v.get('ort_outputs'):
            for o in v['ort_outputs']:
                lines.append('  - out: %s shape=%s' % (o['name'], o['shape']))
        if v.get('guesses'):
            for gg in v['guesses']:
                lines.append('  - guess for %s: %s' % (gg['output_name'], json.dumps(gg['guesses'])))
        lines.append('')
    OUT_MD.write_text('\n'.join(lines))
    print('Wrote', OUT_JSON, 'and', OUT_MD)
