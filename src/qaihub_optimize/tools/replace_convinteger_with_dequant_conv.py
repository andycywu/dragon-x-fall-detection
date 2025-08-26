#!/usr/bin/env python3
"""
Heuristic tool: replace ConvInteger nodes with Conv using float weights.

This is a best-effort, local workaround to avoid ConvInteger NOT_IMPLEMENTED
errors on runtimes that don't implement that op. It attempts to convert
integer weight initializers to float (applying zero point and optional scale
if corresponding initializers are found). When initializers are absent, it
inserts Cast nodes to float for inputs/weights and replaces ConvInteger with
Conv.

Output models are written under `quantized_models/` next to this script.
The tool will also try to load the converted model with ONNX Runtime and
produce a JSON report `onnx_conv_replace_report.json`.
"""
import os
import sys
import json
from pathlib import Path
import uuid

try:
    import onnx
    from onnx import helper, numpy_helper, TensorProto
    import numpy as np
except Exception as e:
    print("Missing dependency (onnx/numpy). Install in your venv and re-run.")
    raise

try:
    import onnxruntime as ort
except Exception:
    ort = None


ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = Path(__file__).resolve().parent
OUT_DIR = TOOLS_DIR.parent / 'quantized_models'
OUT_DIR.mkdir(parents=True, exist_ok=True)


def find_initializer(graph, name):
    for init in graph.initializer:
        if init.name == name:
            return init
    return None


def to_array_safe(init):
    try:
        return numpy_helper.to_array(init)
    except Exception:
        return None


def convert_convinteger_to_conv(model):
    graph = model.graph
    name_to_init = {init.name: to_array_safe(init) for init in graph.initializer}

    nodes = list(graph.node)
    new_nodes = []
    modified = False

    uniq_counter = 0
    def unique(base):
        nonlocal uniq_counter
        uniq_counter += 1
        return f"{base}_{uniq_counter:04d}"

    for node in nodes:
        if node.op_type != 'ConvInteger':
            new_nodes.append(node)
            continue

        # Heuristic conversion
        modified = True
        inp = list(node.input)
        out = list(node.output)
        x_name = inp[0] if len(inp) >= 1 else None
        w_name = inp[1] if len(inp) >= 2 else None
        x_zp = inp[2] if len(inp) >= 3 else None
        w_zp = inp[3] if len(inp) >= 4 else None

        # Attempt to produce a float weight initializer
        new_w_name = None
        if w_name and w_name in name_to_init and name_to_init[w_name] is not None:
            w_arr = name_to_init[w_name]
            if np.issubdtype(w_arr.dtype, np.integer):
                w_float = w_arr.astype(np.float32)
                # subtract zero point if available
                if w_zp and w_zp in name_to_init and name_to_init[w_zp] is not None:
                    try:
                        wzp = name_to_init[w_zp].astype(np.float32)
                        w_float = w_float - wzp.reshape(wzp.shape)
                    except Exception:
                        pass
                # try to find a scale initializer (best-effort)
                scale_val = None
                candidates = [w_name + '_scale', w_name + '_scales', w_name + '_s', (w_zp + '_scale') if w_zp else None]
                for c in candidates:
                    if c and c in name_to_init and name_to_init[c] is not None:
                        arr = name_to_init[c]
                        if arr.size == 1:
                            scale_val = float(arr.reshape(()))
                        else:
                            scale_val = arr.astype(np.float32)
                        break
                if scale_val is not None:
                    try:
                        w_float = w_float * scale_val
                    except Exception:
                        pass

                new_w_name = unique(w_name + '_dequant_float') if w_name else unique('weight_dequant_float')
                new_init = numpy_helper.from_array(w_float.astype(np.float32), new_w_name)
                # avoid duplicate initializer names
                if find_initializer(graph, new_w_name) is None:
                    graph.initializer.extend([new_init])

        # Insert a Cast/Dequantize for input X if needed
        conv_input_name = x_name
        cast_nodes = []
        if x_name:
            # If there is a zero point & scale initializer for X, create DequantizeLinear
            if x_zp and x_zp in name_to_init:
                # try to find scale
                x_scale = None
                candidates = [x_name + '_scale', x_name + '_scales', x_name + '_s', (x_zp + '_scale') if x_zp else None]
                for c in candidates:
                    if c and c in name_to_init and name_to_init[c] is not None:
                        arr = name_to_init[c]
                        x_scale = arr.astype(np.float32) if arr.size > 1 else float(arr.reshape(()))
                        break
                if x_scale is not None:
                    dq_out = unique(x_name + '_dequant')
                    # Create scale initializer if needed
                    scale_init_name = x_name + '_dq_scale'
                    if scale_init_name not in name_to_init:
                        sarr = np.array(x_scale, dtype=np.float32)
                        graph.initializer.extend([numpy_helper.from_array(sarr, scale_init_name)])
                    # ensure zero point initializer exists (reuse existing x_zp)
                    dq_node = helper.make_node('DequantizeLinear', inputs=[x_name, scale_init_name, x_zp], outputs=[dq_out], name=unique(x_name + '_dequantize'))
                    cast_nodes.append(dq_node)
                    conv_input_name = dq_out
                else:
                    # fallback: cast to float
                    cast_out = unique(x_name + '_cast_float')
                    cast_nodes.append(helper.make_node('Cast', inputs=[x_name], outputs=[cast_out], name=unique(x_name + '_cast'), to=TensorProto.FLOAT))
                    conv_input_name = cast_out
            else:
                # No zp info: insert cast
                cast_out = unique(x_name + '_cast_float')
                cast_nodes.append(helper.make_node('Cast', inputs=[x_name], outputs=[cast_out], name=unique(x_name + '_cast'), to=TensorProto.FLOAT))
                conv_input_name = cast_out

        # Determine weight input for Conv
        conv_w_input = new_w_name if new_w_name else (unique(w_name + '_cast_float') if w_name else None)
        if not new_w_name and w_name:
            # insert Cast for weight
            cast_w_out = conv_w_input
            cast_nodes.append(helper.make_node('Cast', inputs=[w_name], outputs=[cast_w_out], name=unique(w_name + '_cast'), to=TensorProto.FLOAT))

        # Build Conv node attributes copied from original
        attrs = {a.name: helper.get_attribute_value(a) for a in node.attribute}
        # ensure conv node name unique and outputs do not clash
        conv_name = unique((node.name or (out[0] + '_conv')))
        # ensure outputs unique
        new_out = []
        for o in out:
            if any(n == o for n in [n.name for n in new_nodes]):
                new_out.append(unique(o))
            else:
                new_out.append(o)

        conv_node = helper.make_node('Conv', inputs=[conv_input_name, conv_w_input], outputs=new_out, name=conv_name, **attrs)

        # Append cast_nodes then conv_node
        new_nodes.extend(cast_nodes)
        new_nodes.append(conv_node)

    if modified:
        # replace nodes
        del graph.node[:]
        graph.node.extend(new_nodes)
        try:
            onnx.checker.check_model(model)
        except Exception as e:
            print('Warning: model check failed after conversion:', e)
        return model
    return None


def process_models(paths):
    report = {}
    for p in paths:
        p = Path(p)
        if not p.exists():
            continue
        out_path = OUT_DIR / (p.stem + '.conv_replaced.onnx')
        print('Processing', p, '->', out_path)
        try:
            model = onnx.load(str(p))
        except Exception as e:
            print('  failed to load', p, e)
            report[str(p)] = {'loaded': False, 'error': str(e)}
            continue

        new_model = convert_convinteger_to_conv(model)
        if new_model is None:
            print('  no ConvInteger found in', p)
            report[str(p)] = {'converted': False, 'reason': 'no ConvInteger'}
            continue

        onnx.save(new_model, str(out_path))
        # try to load with ORT if available
        ort_ok = None
        ort_err = None
        if ort is not None:
            try:
                sess = ort.InferenceSession(str(out_path), providers=['CPUExecutionProvider'])
                ort_ok = True
            except Exception as e:
                ort_ok = False
                ort_err = str(e)
        else:
            ort_ok = None

        report[str(p)] = {'converted': True, 'out': str(out_path), 'ort_ok': ort_ok, 'ort_error': ort_err}

    return report


def collect_candidate_models():
    candidates = []
    # common model folders
    cand_dirs = [ROOT / 'src' / 'models' / 'onnx', ROOT / 'src' / 'models' / 'qaihub_optimized', TOOLS_DIR.parent / 'quantized_models']
    for d in cand_dirs:
        if not d.exists():
            continue
        for p in d.rglob('*.onnx'):
            candidates.append(p)
    return candidates


def main():
    candidates = collect_candidate_models()
    print('Found', len(candidates), 'ONNX files to inspect')
    report = process_models(candidates)
    out_file = TOOLS_DIR / 'onnx_conv_replace_report.json'
    with open(out_file, 'w') as f:
        json.dump(report, f, indent=2)
    print('Wrote report to', out_file)


if __name__ == '__main__':
    main()
