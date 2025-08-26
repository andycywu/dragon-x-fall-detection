import json, os
p = 'src/onnx_official_full.json'
with open(p, 'r') as f:
    data = json.load(f)
print('TOTAL_ENTRIES=', len(data))
print('\n--- TOP 20 SUMMARY ---')
for i, entry in enumerate(data[:20], 1):
    path = os.path.basename(entry.get('path', ''))
    typ = entry.get('type')
    ensemble = entry.get('ensemble', {})
    det = ensemble.get('detected')
    best = ensemble.get('best_model')
    angle = ensemble.get('best_angle')
    print('{:02d}. {} | {} | ensemble_detected={} | best_model={} | angle={}'.format(i, path, typ, det, best, angle))

print('\n--- VIDEO SUMMARIES ---')
video_found = 0
for entry in data:
    vs = entry.get('video_summary')
    if not vs:
        continue
    video_found += 1
    path = os.path.basename(entry.get('path',''))
    print('\nVIDEO: {}'.format(path))
    for k in ['window_k','window_weighted','window_detected_count','window_detected_ratio','ratio_detected','longest_detected','final_detected']:
        if k in vs:
            print('  {}: {}'.format(k, vs[k]))
    if 'frames' in vs:
        fr = vs['frames']
        print('  frames: total={} sampled={}'.format(fr.get('total'), fr.get('sampled')))

print('\nFound video entries with video_summary:', video_found)
