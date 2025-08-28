"""
Generate suggested model mappings from reports/batch_diagnostic_summary.json.
Produces config/model_mappings.json with conservative kps hints for models
that produced usable keypoint heatmap or adapter outputs.
"""
import json
import os

SRC = os.path.abspath(os.path.dirname(__file__) + '/../')
REPORT = os.path.join(SRC, 'reports', 'batch_diagnostic_summary.json')
OUT = os.path.join(SRC, 'config', 'model_mappings.json')

def main():
    if not os.path.exists(REPORT):
        print('batch_diagnostic_summary.json not found at', REPORT)
        return
    with open(REPORT, 'r', encoding='utf-8') as f:
        data = json.load(f)
    mappings = {}
    for entry in data:
        m = entry.get('model')
        wrote = entry.get('wrote', [])
        if not wrote:
            continue
        # derive a short key from basename
        key = os.path.basename(m).lower()
        # heuristics: if adapter_named or heatmaps_softargmax written, suggest heatmap hints
        suggest = {}
        joined = ' '.join(wrote)
        if 'adapter_named_litehrnet' in joined:
            suggest = {'kps': ['keypoints', 'pred', 'keypoints_output'], 'scores': ['scores']}
        elif 'heatmaps_softargmax' in joined or 'output_' in joined and 'softargmax' in joined:
            suggest = {'kps': ['heatmap', 'hm', 'output_0'], 'scores': []}
        elif 'flat3' in joined or 'flat2' in joined:
            suggest = {'kps': ['output_0', 'output_1'], 'scores': []}
        else:
            # generic fallback if something was written
            suggest = {'kps': ['output_0', 'keypoints', 'heatmap'], 'scores': []}
        mappings[key] = suggest
    # ensure config dir exists
    cfg_dir = os.path.dirname(OUT)
    os.makedirs(cfg_dir, exist_ok=True)
    # if file exists, merge conservatively
    if os.path.exists(OUT):
        try:
            with open(OUT, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except Exception:
            existing = {}
    else:
        existing = {}
    # merge but do not overwrite existing keys
    for k, v in mappings.items():
        if k not in existing:
            existing[k] = v
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
    print('Wrote suggestions to', OUT)

if __name__ == '__main__':
    main()
