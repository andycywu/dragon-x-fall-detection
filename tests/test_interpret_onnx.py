import os
import sys
import numpy as np

# ensure project root is on sys.path so `src` package can be imported
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# also add src/infer_demo_Mac to sys.path so internal `adapters` imports resolve
INFER_MAC = os.path.join(ROOT, 'src', 'infer_demo_Mac')
if INFER_MAC not in sys.path:
    sys.path.insert(0, INFER_MAC)

from src.infer_demo_Mac.live_demo_mac import interpret_onnx_output, _soft_argmax_heatmaps, normalize_keypoints_list


def test_regression_flat_keypoints():
    # simulate ONNX output: shape (1, 34) -> 17*(x,y), no conf
    pts = np.linspace(0, 1, 34, dtype=np.float32).reshape(1, 34)
    res = interpret_onnx_output([pts])
    assert 'keypoints' in res and res['keypoints'] is not None
    kps = res['keypoints']
    assert len(kps) == 17
    # confidences should be 0.0 by conservative fallback
    for p in kps:
        assert len(p) == 3
        assert p[2] == 0.0


def test_soft_argmax_heatmap():
    # create a simple heatmap with a clear peak at (x=4,y=2) for 3 keypoints
    K, H, W = 3, 6, 7
    hmaps = np.zeros((K, H, W), dtype=np.float32)
    # place peaks
    hmaps[0, 2, 4] = 10.0
    hmaps[1, 1, 1] = 8.0
    hmaps[2, 5, 6] = 6.0
    kps = _soft_argmax_heatmaps(hmaps)
    assert len(kps) == K
    # check approximate positions and confidences > 0
    assert abs(kps[0][0] - 4.0) < 1.0
    assert abs(kps[0][1] - 2.0) < 1.0
    assert kps[0][2] > 0.0
    assert abs(kps[1][0] - 1.0) < 1.0
    assert abs(kps[2][1] - 5.0) < 1.0


def test_interpret_onnx_detects_heatmap_layouts():
    # heatmap as (H,W,K) layout
    K, H, W = 4, 8, 9
    h = np.zeros((H, W, K), dtype=np.float32)
    h[3, 5, 2] = 12.0
    out = interpret_onnx_output([h])
    assert out.get('keypoints') is not None
    assert len(out.get('keypoints')) == K


def test_interpret_onnx_handles_batch_heatmap():
    # heatmap as (1,K,H,W)
    K, H, W = 5, 6, 6
    h = np.zeros((1, K, H, W), dtype=np.float32)
    h[0, 1, 2, 3] = 7.5
    out = interpret_onnx_output([h])
    assert out.get('keypoints') is not None
    assert len(out.get('keypoints')) == K


def test_soft_argmax_with_nans():
    # NaNs in heatmap should be handled gracefully
    K, H, W = 2, 4, 4
    h = np.full((K, H, W), np.nan, dtype=np.float32)
    # set one finite peak
    h[0, 1, 1] = 5.0
    kps = _soft_argmax_heatmaps(h)
    assert isinstance(kps, list)
    assert len(kps) == K


def test_regression_batch_flat():
    # batch of regression outputs: shape (2, 34) -> two samples
    b = np.vstack([np.linspace(0, 1, 34, dtype=np.float32), np.linspace(1, 0, 34, dtype=np.float32)])
    out = interpret_onnx_output([b])
    # interpret should pick first batch element or handle gracefully; we expect keypoints
    assert out.get('keypoints') is not None
    assert len(out.get('keypoints')) == 17


def test_normalize_keypoints_list():
    # normalized coords should be scaled to pixels
    kps = [[0.5, 0.25], [0.0, 1.0, 0.8]]
    norm = normalize_keypoints_list(kps, frame_w=200, frame_h=100)
    assert len(norm) == 2
    assert abs(norm[0][0] - 100.0) < 1e-3
    assert abs(norm[0][1] - 25.0) < 1e-3
    assert norm[0][2] == 0.0
    assert abs(norm[1][2] - 0.8) < 1e-6
