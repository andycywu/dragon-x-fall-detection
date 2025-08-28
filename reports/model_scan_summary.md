# Model scan summary

## src/models/deploy/hrnet_pose-hrnetpose-float.onnx
- onnx_load_ok: False
- ort_ok: False

## src/models/deploy/hrnet_pose-hrnetpose-float.onnx/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: heatmaps shape=[1, 17, 64, 48]
  - guess for heatmaps: [{"type": "heatmap_channels", "channels": 48, "kps": 16, "layout": "channels as (x,y,score) maps"}]

## src/models/deploy/j56z76m6g_pose_landmarks_detector_heavy_optimized.onnx__model.onnx__dir/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: output_0 shape=[1, 195]
  - out: output_1 shape=[1, 1]
  - out: output_2 shape=[1, 256, 256, 1]
  - out: output_3 shape=[1, 64, 64, 39]
  - out: output_4 shape=[1, 117]
  - guess for output_0: [{"type": "flat", "kps": 65, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]
  - guess for output_2: [{"type": "flat", "kps": 128, "layout": "flattened (x,y) per kp"}]
  - guess for output_3: [{"type": "flat", "kps": 32, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 39, "kps": 13, "layout": "channels as (x,y,score) maps"}]
  - guess for output_4: [{"type": "flat", "kps": 39, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]

## src/models/deploy/j5m6mr1dg_pose_landmarks_detector_full.quant_optimized.onnx__model.onnx__dir/model.onnx
- onnx_load_ok: True
- ort_ok: False

## src/models/deploy/j5qry81np_pose_landmarks_detector_lite_optimized.onnx__model.onnx__dir/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: output_0 shape=[1, 195]
  - out: output_1 shape=[1, 1]
  - out: output_2 shape=[1, 256, 256, 1]
  - out: output_3 shape=[1, 64, 64, 39]
  - out: output_4 shape=[1, 117]
  - guess for output_0: [{"type": "flat", "kps": 65, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]
  - guess for output_2: [{"type": "flat", "kps": 128, "layout": "flattened (x,y) per kp"}]
  - guess for output_3: [{"type": "flat", "kps": 32, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 39, "kps": 13, "layout": "channels as (x,y,score) maps"}]
  - guess for output_4: [{"type": "flat", "kps": 39, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]

## src/models/deploy/jg9ymoxw5_pose_landmarks_detector_heavy_optimized.onnx__model.onnx__dir/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: output_0 shape=[1, 195]
  - out: output_1 shape=[1, 1]
  - out: output_2 shape=[1, 256, 256, 1]
  - out: output_3 shape=[1, 64, 64, 39]
  - out: output_4 shape=[1, 117]
  - guess for output_0: [{"type": "flat", "kps": 65, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]
  - guess for output_2: [{"type": "flat", "kps": 128, "layout": "flattened (x,y) per kp"}]
  - guess for output_3: [{"type": "flat", "kps": 32, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 39, "kps": 13, "layout": "channels as (x,y,score) maps"}]
  - guess for output_4: [{"type": "flat", "kps": 39, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]

## src/models/deploy/jgdq3wyr5_pose_landmarks_detector_lite.quant_optimized.onnx__model.onnx__dir/model.onnx
- onnx_load_ok: True
- ort_ok: False

## src/models/deploy/jgj273z85_pose_landmarks_detector_heavy_optimized.onnx__model.onnx__dir/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: output_0 shape=[1, 195]
  - out: output_1 shape=[1, 1]
  - out: output_2 shape=[1, 256, 256, 1]
  - out: output_3 shape=[1, 64, 64, 39]
  - out: output_4 shape=[1, 117]
  - guess for output_0: [{"type": "flat", "kps": 65, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]
  - guess for output_2: [{"type": "flat", "kps": 128, "layout": "flattened (x,y) per kp"}]
  - guess for output_3: [{"type": "flat", "kps": 32, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 39, "kps": 13, "layout": "channels as (x,y,score) maps"}]
  - guess for output_4: [{"type": "flat", "kps": 39, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]

## src/models/deploy/jgj27x8v5_pose_detection_optimized.onnx__model.onnx__dir/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: output_0 shape=[1, 2254, 12]
  - out: output_1 shape=[1, 2254, 1]
  - guess for output_0: [{"type": "flat", "kps": 1127, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 12, "kps": 4, "layout": "channels as (x,y,score) maps"}]
  - guess for output_1: [{"type": "flat", "kps": 1127, "layout": "flattened (x,y) per kp"}]

## src/models/deploy/jgkq4z0wg_test_simple_model_fixed.quant_optimized.onnx__model.onnx__dir/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: output_0 shape=[1, 3, 224, 224]
  - guess for output_0: [{"type": "flat", "kps": 1, "layout": "flattened (x,y,score) or (x,y,z) per kp"}, {"type": "heatmap_channels", "channels": 224, "kps": null, "layout": "channels maybe per-kp heatmap"}]

## src/models/deploy/jgonrdkdp_pose_landmarks_detector_lite_optimized.onnx__model.onnx__dir/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: output_0 shape=[1, 195]
  - out: output_1 shape=[1, 1]
  - out: output_2 shape=[1, 256, 256, 1]
  - out: output_3 shape=[1, 64, 64, 39]
  - out: output_4 shape=[1, 117]
  - guess for output_0: [{"type": "flat", "kps": 65, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]
  - guess for output_2: [{"type": "flat", "kps": 128, "layout": "flattened (x,y) per kp"}]
  - guess for output_3: [{"type": "flat", "kps": 32, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 39, "kps": 13, "layout": "channels as (x,y,score) maps"}]
  - guess for output_4: [{"type": "flat", "kps": 39, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]

## src/models/deploy/jgonrywqp_test_simple_model_fixed_optimized.onnx__model.onnx__dir/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: output_0 shape=[1, 3, 224, 224]
  - guess for output_0: [{"type": "flat", "kps": 1, "layout": "flattened (x,y,score) or (x,y,z) per kp"}, {"type": "heatmap_channels", "channels": 224, "kps": null, "layout": "channels maybe per-kp heatmap"}]

## src/models/deploy/jgzjmz4op_pose_landmarks_detector_full_optimized.onnx__model.onnx__dir/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: output_0 shape=[1, 195]
  - out: output_1 shape=[1, 1]
  - out: output_2 shape=[1, 256, 256, 1]
  - out: output_3 shape=[1, 64, 64, 39]
  - out: output_4 shape=[1, 117]
  - guess for output_0: [{"type": "flat", "kps": 65, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]
  - guess for output_2: [{"type": "flat", "kps": 128, "layout": "flattened (x,y) per kp"}]
  - guess for output_3: [{"type": "flat", "kps": 32, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 39, "kps": 13, "layout": "channels as (x,y,score) maps"}]
  - guess for output_4: [{"type": "flat", "kps": 39, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]

## src/models/deploy/jp02jy895_test_simple_model_fixed_optimized.onnx__model.onnx__dir/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: output_0 shape=[1, 3, 224, 224]
  - guess for output_0: [{"type": "flat", "kps": 1, "layout": "flattened (x,y,score) or (x,y,z) per kp"}, {"type": "heatmap_channels", "channels": 224, "kps": null, "layout": "channels maybe per-kp heatmap"}]

## src/models/deploy/jp02jy995_pose_detection.quant_optimized.onnx__model.onnx__dir/model.onnx
- onnx_load_ok: True
- ort_ok: False

## src/models/deploy/jp1wj0k8g_pose_landmarks_detector_full_optimized.onnx__model.onnx__dir/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: output_0 shape=[1, 195]
  - out: output_1 shape=[1, 1]
  - out: output_2 shape=[1, 256, 256, 1]
  - out: output_3 shape=[1, 64, 64, 39]
  - out: output_4 shape=[1, 117]
  - guess for output_0: [{"type": "flat", "kps": 65, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]
  - guess for output_2: [{"type": "flat", "kps": 128, "layout": "flattened (x,y) per kp"}]
  - guess for output_3: [{"type": "flat", "kps": 32, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 39, "kps": 13, "layout": "channels as (x,y,score) maps"}]
  - guess for output_4: [{"type": "flat", "kps": 39, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]

## src/models/deploy/jp1wjov8g_test_simple_model_fixed_optimized.onnx__model.onnx__dir/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: output_0 shape=[1, 3, 224, 224]
  - guess for output_0: [{"type": "flat", "kps": 1, "layout": "flattened (x,y,score) or (x,y,z) per kp"}, {"type": "heatmap_channels", "channels": 224, "kps": null, "layout": "channels maybe per-kp heatmap"}]

## src/models/deploy/jp29w8drg_pose_landmarks_detector_heavy.quant_optimized.onnx__model.onnx__dir/model.onnx
- onnx_load_ok: True
- ort_ok: False

## src/models/deploy/jp8mxodk5_pose_detection_optimized.onnx__model.onnx__dir/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: output_0 shape=[1, 2254, 12]
  - out: output_1 shape=[1, 2254, 1]
  - guess for output_0: [{"type": "flat", "kps": 1127, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 12, "kps": 4, "layout": "channels as (x,y,score) maps"}]
  - guess for output_1: [{"type": "flat", "kps": 1127, "layout": "flattened (x,y) per kp"}]

## src/models/deploy/jp8mxork5_pose_landmarks_detector_full.quant_optimized.onnx__model.onnx__dir/model.onnx
- onnx_load_ok: True
- ort_ok: False

## src/models/deploy/jpr20km05_pose_landmarks_detector_lite_optimized.onnx__model.onnx__dir/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: output_0 shape=[1, 195]
  - out: output_1 shape=[1, 1]
  - out: output_2 shape=[1, 256, 256, 1]
  - out: output_3 shape=[1, 64, 64, 39]
  - out: output_4 shape=[1, 117]
  - guess for output_0: [{"type": "flat", "kps": 65, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]
  - guess for output_2: [{"type": "flat", "kps": 128, "layout": "flattened (x,y) per kp"}]
  - guess for output_3: [{"type": "flat", "kps": 32, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 39, "kps": 13, "layout": "channels as (x,y,score) maps"}]
  - guess for output_4: [{"type": "flat", "kps": 39, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]

## src/models/deploy/jpx64v83p_pose_detection.quant_optimized.onnx__model.onnx__dir/model.onnx
- onnx_load_ok: True
- ort_ok: False

## src/models/deploy/jpyjxek8p_pose_landmarks_detector_heavy_optimized.onnx__model.onnx__dir/model.onnx
- onnx_load_ok: True
- ort_ok: False

## src/models/deploy/litehrnet.onnx
- onnx_load_ok: False
- ort_ok: False

## src/models/deploy/litehrnet.onnx/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: keypoints shape=[1, 17, 2]
  - out: scores shape=[1, 17]
  - out: heatmaps shape=[1, 17, 64, 48]
  - guess for keypoints: [{"type": "seq_kps_2", "kps": 17, "layout": "(x,y)"}]
  - guess for heatmaps: [{"type": "heatmap_channels", "channels": 48, "kps": 16, "layout": "channels as (x,y,score) maps"}]

## src/models/deploy/mediapipe_face-facedetector-float.onnx__model.onnx__dir/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: box_coords shape=[1, 896, 16]
  - out: box_scores shape=[1, 896, 1]
  - guess for box_coords: [{"type": "flat", "kps": 448, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 16, "kps": null, "layout": "channels maybe per-kp heatmap"}]
  - guess for box_scores: [{"type": "flat", "kps": 448, "layout": "flattened (x,y) per kp"}]

## src/models/deploy/mediapipe_hand-handdetector.onnx__model.onnx__dir/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: box_coords shape=[1, 2944, 18]
  - out: box_scores shape=[1, 2944, 1]
  - guess for box_coords: [{"type": "flat", "kps": 1472, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 18, "kps": 6, "layout": "channels as (x,y,score) maps"}]
  - guess for box_scores: [{"type": "flat", "kps": 1472, "layout": "flattened (x,y) per kp"}]

## src/models/deploy/mediapipe_pose-posedetector.onnx__model.onnx__dir/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: box_coords shape=[1, 896, 12]
  - out: box_scores shape=[1, 896, 1]
  - guess for box_coords: [{"type": "flat", "kps": 448, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 12, "kps": 4, "layout": "channels as (x,y,score) maps"}]
  - guess for box_scores: [{"type": "flat", "kps": 448, "layout": "flattened (x,y) per kp"}]

## src/models/deploy/rtmpose_body2d-rtmpose-body2d-float.onnx
- onnx_load_ok: False
- ort_ok: False

## src/models/deploy/rtmpose_body2d-rtmpose-body2d-float.onnx/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: pred_x shape=[1, 133, 384]
  - out: pred_y shape=[1, 133, 512]

## src/models/onnx/face_detector.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: regressors shape=[1, 896, 16]
  - out: classificators shape=[1, 896, 1]
  - guess for regressors: [{"type": "flat", "kps": 448, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 16, "kps": null, "layout": "channels maybe per-kp heatmap"}]
  - guess for classificators: [{"type": "flat", "kps": 448, "layout": "flattened (x,y) per kp"}]

## src/models/onnx/face_detector.quant.onnx
- onnx_load_ok: True
- ort_ok: False

## src/models/onnx/hand_landmarks_detector.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: Identity shape=[1, 63]
  - out: Identity_1 shape=[1, 1]
  - out: Identity_2 shape=[1, 1]
  - out: Identity_3 shape=[1, 63]
  - guess for Identity: [{"type": "flat", "kps": 21, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]
  - guess for Identity_3: [{"type": "flat", "kps": 21, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]

## src/models/onnx/hand_landmarks_detector.quant.onnx
- onnx_load_ok: True
- ort_ok: False

## src/models/onnx/pose_detection.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: Identity shape=[1, 2254, 12]
  - out: Identity_1 shape=[1, 2254, 1]
  - guess for Identity: [{"type": "flat", "kps": 1127, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 12, "kps": 4, "layout": "channels as (x,y,score) maps"}]
  - guess for Identity_1: [{"type": "flat", "kps": 1127, "layout": "flattened (x,y) per kp"}]

## src/models/onnx/pose_detection.quant.onnx
- onnx_load_ok: True
- ort_ok: False

## src/models/onnx/pose_landmarks_detector_full.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: Identity shape=[1, 195]
  - out: Identity_1 shape=[1, 1]
  - out: Identity_2 shape=[1, 256, 256, 1]
  - out: Identity_3 shape=[1, 64, 64, 39]
  - out: Identity_4 shape=[1, 117]
  - guess for Identity: [{"type": "flat", "kps": 65, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]
  - guess for Identity_2: [{"type": "flat", "kps": 128, "layout": "flattened (x,y) per kp"}]
  - guess for Identity_3: [{"type": "flat", "kps": 32, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 39, "kps": 13, "layout": "channels as (x,y,score) maps"}]
  - guess for Identity_4: [{"type": "flat", "kps": 39, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]

## src/models/onnx/pose_landmarks_detector_full.quant.onnx
- onnx_load_ok: True
- ort_ok: False

## src/models/onnx/pose_landmarks_detector_heavy.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: Identity shape=[1, 195]
  - out: Identity_1 shape=[1, 1]
  - out: Identity_2 shape=[1, 256, 256, 1]
  - out: Identity_3 shape=[1, 64, 64, 39]
  - out: Identity_4 shape=[1, 117]
  - guess for Identity: [{"type": "flat", "kps": 65, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]
  - guess for Identity_2: [{"type": "flat", "kps": 128, "layout": "flattened (x,y) per kp"}]
  - guess for Identity_3: [{"type": "flat", "kps": 32, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 39, "kps": 13, "layout": "channels as (x,y,score) maps"}]
  - guess for Identity_4: [{"type": "flat", "kps": 39, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]

## src/models/onnx/pose_landmarks_detector_heavy.quant.onnx
- onnx_load_ok: True
- ort_ok: False

## src/models/onnx/pose_landmarks_detector_lite.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: Identity shape=[1, 195]
  - out: Identity_1 shape=[1, 1]
  - out: Identity_2 shape=[1, 256, 256, 1]
  - out: Identity_3 shape=[1, 64, 64, 39]
  - out: Identity_4 shape=[1, 117]
  - guess for Identity: [{"type": "flat", "kps": 65, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]
  - guess for Identity_2: [{"type": "flat", "kps": 128, "layout": "flattened (x,y) per kp"}]
  - guess for Identity_3: [{"type": "flat", "kps": 32, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 39, "kps": 13, "layout": "channels as (x,y,score) maps"}]
  - guess for Identity_4: [{"type": "flat", "kps": 39, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]

## src/models/onnx/pose_landmarks_detector_lite.quant.onnx
- onnx_load_ok: True
- ort_ok: False

## src/models/onnx/test_simple_model_fixed.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: Y shape=[1, 3, 224, 224]
  - guess for Y: [{"type": "flat", "kps": 1, "layout": "flattened (x,y,score) or (x,y,z) per kp"}, {"type": "heatmap_channels", "channels": 224, "kps": null, "layout": "channels maybe per-kp heatmap"}]

## src/models/onnx/test_simple_model_fixed.quant.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: Y shape=[1, 3, 224, 224]
  - guess for Y: [{"type": "flat", "kps": 1, "layout": "flattened (x,y,score) or (x,y,z) per kp"}, {"type": "heatmap_channels", "channels": 224, "kps": null, "layout": "channels maybe per-kp heatmap"}]

## src/models/qaihub_optimized/j56z76m6g_pose_landmarks_detector_heavy_optimized.onnx
- onnx_load_ok: False
- ort_ok: False

## src/models/qaihub_optimized/j56z76m6g_pose_landmarks_detector_heavy_optimized.onnx/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: output_0 shape=[1, 195]
  - out: output_1 shape=[1, 1]
  - out: output_2 shape=[1, 256, 256, 1]
  - out: output_3 shape=[1, 64, 64, 39]
  - out: output_4 shape=[1, 117]
  - guess for output_0: [{"type": "flat", "kps": 65, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]
  - guess for output_2: [{"type": "flat", "kps": 128, "layout": "flattened (x,y) per kp"}]
  - guess for output_3: [{"type": "flat", "kps": 32, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 39, "kps": 13, "layout": "channels as (x,y,score) maps"}]
  - guess for output_4: [{"type": "flat", "kps": 39, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]

## src/models/qaihub_optimized/j5m6mr1dg_pose_landmarks_detector_full.quant_optimized.onnx
- onnx_load_ok: False
- ort_ok: False

## src/models/qaihub_optimized/j5m6mr1dg_pose_landmarks_detector_full.quant_optimized.onnx/model.onnx
- onnx_load_ok: True
- ort_ok: False

## src/models/qaihub_optimized/j5qry81np_pose_landmarks_detector_lite_optimized.onnx
- onnx_load_ok: False
- ort_ok: False

## src/models/qaihub_optimized/j5qry81np_pose_landmarks_detector_lite_optimized.onnx/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: output_0 shape=[1, 195]
  - out: output_1 shape=[1, 1]
  - out: output_2 shape=[1, 256, 256, 1]
  - out: output_3 shape=[1, 64, 64, 39]
  - out: output_4 shape=[1, 117]
  - guess for output_0: [{"type": "flat", "kps": 65, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]
  - guess for output_2: [{"type": "flat", "kps": 128, "layout": "flattened (x,y) per kp"}]
  - guess for output_3: [{"type": "flat", "kps": 32, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 39, "kps": 13, "layout": "channels as (x,y,score) maps"}]
  - guess for output_4: [{"type": "flat", "kps": 39, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]

## src/models/qaihub_optimized/jg9ymoxw5_pose_landmarks_detector_heavy_optimized.onnx
- onnx_load_ok: False
- ort_ok: False

## src/models/qaihub_optimized/jg9ymoxw5_pose_landmarks_detector_heavy_optimized.onnx/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: output_0 shape=[1, 195]
  - out: output_1 shape=[1, 1]
  - out: output_2 shape=[1, 256, 256, 1]
  - out: output_3 shape=[1, 64, 64, 39]
  - out: output_4 shape=[1, 117]
  - guess for output_0: [{"type": "flat", "kps": 65, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]
  - guess for output_2: [{"type": "flat", "kps": 128, "layout": "flattened (x,y) per kp"}]
  - guess for output_3: [{"type": "flat", "kps": 32, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 39, "kps": 13, "layout": "channels as (x,y,score) maps"}]
  - guess for output_4: [{"type": "flat", "kps": 39, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]

## src/models/qaihub_optimized/jgdq3wyr5_pose_landmarks_detector_lite.quant_optimized.onnx
- onnx_load_ok: False
- ort_ok: False

## src/models/qaihub_optimized/jgdq3wyr5_pose_landmarks_detector_lite.quant_optimized.onnx/model.onnx
- onnx_load_ok: True
- ort_ok: False

## src/models/qaihub_optimized/jgj273z85_pose_landmarks_detector_heavy_optimized.onnx
- onnx_load_ok: False
- ort_ok: False

## src/models/qaihub_optimized/jgj273z85_pose_landmarks_detector_heavy_optimized.onnx/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: output_0 shape=[1, 195]
  - out: output_1 shape=[1, 1]
  - out: output_2 shape=[1, 256, 256, 1]
  - out: output_3 shape=[1, 64, 64, 39]
  - out: output_4 shape=[1, 117]
  - guess for output_0: [{"type": "flat", "kps": 65, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]
  - guess for output_2: [{"type": "flat", "kps": 128, "layout": "flattened (x,y) per kp"}]
  - guess for output_3: [{"type": "flat", "kps": 32, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 39, "kps": 13, "layout": "channels as (x,y,score) maps"}]
  - guess for output_4: [{"type": "flat", "kps": 39, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]

## src/models/qaihub_optimized/jgj27x8v5_pose_detection_optimized.onnx
- onnx_load_ok: False
- ort_ok: False

## src/models/qaihub_optimized/jgj27x8v5_pose_detection_optimized.onnx/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: output_0 shape=[1, 2254, 12]
  - out: output_1 shape=[1, 2254, 1]
  - guess for output_0: [{"type": "flat", "kps": 1127, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 12, "kps": 4, "layout": "channels as (x,y,score) maps"}]
  - guess for output_1: [{"type": "flat", "kps": 1127, "layout": "flattened (x,y) per kp"}]

## src/models/qaihub_optimized/jgkq4z0wg_test_simple_model_fixed.quant_optimized.onnx
- onnx_load_ok: False
- ort_ok: False

## src/models/qaihub_optimized/jgkq4z0wg_test_simple_model_fixed.quant_optimized.onnx/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: output_0 shape=[1, 3, 224, 224]
  - guess for output_0: [{"type": "flat", "kps": 1, "layout": "flattened (x,y,score) or (x,y,z) per kp"}, {"type": "heatmap_channels", "channels": 224, "kps": null, "layout": "channels maybe per-kp heatmap"}]

## src/models/qaihub_optimized/jgonrdkdp_pose_landmarks_detector_lite_optimized.onnx
- onnx_load_ok: False
- ort_ok: False

## src/models/qaihub_optimized/jgonrdkdp_pose_landmarks_detector_lite_optimized.onnx/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: output_0 shape=[1, 195]
  - out: output_1 shape=[1, 1]
  - out: output_2 shape=[1, 256, 256, 1]
  - out: output_3 shape=[1, 64, 64, 39]
  - out: output_4 shape=[1, 117]
  - guess for output_0: [{"type": "flat", "kps": 65, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]
  - guess for output_2: [{"type": "flat", "kps": 128, "layout": "flattened (x,y) per kp"}]
  - guess for output_3: [{"type": "flat", "kps": 32, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 39, "kps": 13, "layout": "channels as (x,y,score) maps"}]
  - guess for output_4: [{"type": "flat", "kps": 39, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]

## src/models/qaihub_optimized/jgonrywqp_test_simple_model_fixed_optimized.onnx
- onnx_load_ok: False
- ort_ok: False

## src/models/qaihub_optimized/jgonrywqp_test_simple_model_fixed_optimized.onnx/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: output_0 shape=[1, 3, 224, 224]
  - guess for output_0: [{"type": "flat", "kps": 1, "layout": "flattened (x,y,score) or (x,y,z) per kp"}, {"type": "heatmap_channels", "channels": 224, "kps": null, "layout": "channels maybe per-kp heatmap"}]

## src/models/qaihub_optimized/jgzjmz4op_pose_landmarks_detector_full_optimized.onnx
- onnx_load_ok: False
- ort_ok: False

## src/models/qaihub_optimized/jgzjmz4op_pose_landmarks_detector_full_optimized.onnx/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: output_0 shape=[1, 195]
  - out: output_1 shape=[1, 1]
  - out: output_2 shape=[1, 256, 256, 1]
  - out: output_3 shape=[1, 64, 64, 39]
  - out: output_4 shape=[1, 117]
  - guess for output_0: [{"type": "flat", "kps": 65, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]
  - guess for output_2: [{"type": "flat", "kps": 128, "layout": "flattened (x,y) per kp"}]
  - guess for output_3: [{"type": "flat", "kps": 32, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 39, "kps": 13, "layout": "channels as (x,y,score) maps"}]
  - guess for output_4: [{"type": "flat", "kps": 39, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]

## src/models/qaihub_optimized/jp02jy895_test_simple_model_fixed_optimized.onnx
- onnx_load_ok: False
- ort_ok: False

## src/models/qaihub_optimized/jp02jy895_test_simple_model_fixed_optimized.onnx/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: output_0 shape=[1, 3, 224, 224]
  - guess for output_0: [{"type": "flat", "kps": 1, "layout": "flattened (x,y,score) or (x,y,z) per kp"}, {"type": "heatmap_channels", "channels": 224, "kps": null, "layout": "channels maybe per-kp heatmap"}]

## src/models/qaihub_optimized/jp02jy995_pose_detection.quant_optimized.onnx
- onnx_load_ok: False
- ort_ok: False

## src/models/qaihub_optimized/jp02jy995_pose_detection.quant_optimized.onnx/model.onnx
- onnx_load_ok: True
- ort_ok: False

## src/models/qaihub_optimized/jp1wj0k8g_pose_landmarks_detector_full_optimized.onnx
- onnx_load_ok: False
- ort_ok: False

## src/models/qaihub_optimized/jp1wj0k8g_pose_landmarks_detector_full_optimized.onnx/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: output_0 shape=[1, 195]
  - out: output_1 shape=[1, 1]
  - out: output_2 shape=[1, 256, 256, 1]
  - out: output_3 shape=[1, 64, 64, 39]
  - out: output_4 shape=[1, 117]
  - guess for output_0: [{"type": "flat", "kps": 65, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]
  - guess for output_2: [{"type": "flat", "kps": 128, "layout": "flattened (x,y) per kp"}]
  - guess for output_3: [{"type": "flat", "kps": 32, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 39, "kps": 13, "layout": "channels as (x,y,score) maps"}]
  - guess for output_4: [{"type": "flat", "kps": 39, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]

## src/models/qaihub_optimized/jp1wjov8g_test_simple_model_fixed_optimized.onnx
- onnx_load_ok: False
- ort_ok: False

## src/models/qaihub_optimized/jp1wjov8g_test_simple_model_fixed_optimized.onnx/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: output_0 shape=[1, 3, 224, 224]
  - guess for output_0: [{"type": "flat", "kps": 1, "layout": "flattened (x,y,score) or (x,y,z) per kp"}, {"type": "heatmap_channels", "channels": 224, "kps": null, "layout": "channels maybe per-kp heatmap"}]

## src/models/qaihub_optimized/jp29w8drg_pose_landmarks_detector_heavy.quant_optimized.onnx
- onnx_load_ok: False
- ort_ok: False

## src/models/qaihub_optimized/jp29w8drg_pose_landmarks_detector_heavy.quant_optimized.onnx/model.onnx
- onnx_load_ok: True
- ort_ok: False

## src/models/qaihub_optimized/jp8mxodk5_pose_detection_optimized.onnx
- onnx_load_ok: False
- ort_ok: False

## src/models/qaihub_optimized/jp8mxodk5_pose_detection_optimized.onnx/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: output_0 shape=[1, 2254, 12]
  - out: output_1 shape=[1, 2254, 1]
  - guess for output_0: [{"type": "flat", "kps": 1127, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 12, "kps": 4, "layout": "channels as (x,y,score) maps"}]
  - guess for output_1: [{"type": "flat", "kps": 1127, "layout": "flattened (x,y) per kp"}]

## src/models/qaihub_optimized/jp8mxork5_pose_landmarks_detector_full.quant_optimized.onnx
- onnx_load_ok: False
- ort_ok: False

## src/models/qaihub_optimized/jp8mxork5_pose_landmarks_detector_full.quant_optimized.onnx/model.onnx
- onnx_load_ok: True
- ort_ok: False

## src/models/qaihub_optimized/jpr20km05_pose_landmarks_detector_lite_optimized.onnx
- onnx_load_ok: False
- ort_ok: False

## src/models/qaihub_optimized/jpr20km05_pose_landmarks_detector_lite_optimized.onnx/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: output_0 shape=[1, 195]
  - out: output_1 shape=[1, 1]
  - out: output_2 shape=[1, 256, 256, 1]
  - out: output_3 shape=[1, 64, 64, 39]
  - out: output_4 shape=[1, 117]
  - guess for output_0: [{"type": "flat", "kps": 65, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]
  - guess for output_2: [{"type": "flat", "kps": 128, "layout": "flattened (x,y) per kp"}]
  - guess for output_3: [{"type": "flat", "kps": 32, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 39, "kps": 13, "layout": "channels as (x,y,score) maps"}]
  - guess for output_4: [{"type": "flat", "kps": 39, "layout": "flattened (x,y,score) or (x,y,z) per kp"}]

## src/models/qaihub_optimized/jpx64v83p_pose_detection.quant_optimized.onnx
- onnx_load_ok: False
- ort_ok: False

## src/models/qaihub_optimized/jpx64v83p_pose_detection.quant_optimized.onnx/model.onnx
- onnx_load_ok: True
- ort_ok: False

## src/models/qaihub_optimized/jpyjxek8p_pose_landmarks_detector_heavy_optimized.onnx
- onnx_load_ok: False
- ort_ok: False

## src/models/qaihub_optimized/jpyjxek8p_pose_landmarks_detector_heavy_optimized.onnx/model.onnx
- onnx_load_ok: True
- ort_ok: False

## src/models/qaihub_optimized/mediapipe_face-facedetector-float.onnx
- onnx_load_ok: False
- ort_ok: False

## src/models/qaihub_optimized/mediapipe_face-facedetector-float.onnx/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: box_coords shape=[1, 896, 16]
  - out: box_scores shape=[1, 896, 1]
  - guess for box_coords: [{"type": "flat", "kps": 448, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 16, "kps": null, "layout": "channels maybe per-kp heatmap"}]
  - guess for box_scores: [{"type": "flat", "kps": 448, "layout": "flattened (x,y) per kp"}]

## src/models/qaihub_optimized/mediapipe_hand-handdetector.onnx
- onnx_load_ok: False
- ort_ok: False

## src/models/qaihub_optimized/mediapipe_hand-handdetector.onnx/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: box_coords shape=[1, 2944, 18]
  - out: box_scores shape=[1, 2944, 1]
  - guess for box_coords: [{"type": "flat", "kps": 1472, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 18, "kps": 6, "layout": "channels as (x,y,score) maps"}]
  - guess for box_scores: [{"type": "flat", "kps": 1472, "layout": "flattened (x,y) per kp"}]

## src/models/qaihub_optimized/mediapipe_pose-posedetector.onnx
- onnx_load_ok: False
- ort_ok: False

## src/models/qaihub_optimized/mediapipe_pose-posedetector.onnx/model.onnx
- onnx_load_ok: True
- ort_ok: True
  - out: box_coords shape=[1, 896, 12]
  - out: box_scores shape=[1, 896, 1]
  - guess for box_coords: [{"type": "flat", "kps": 448, "layout": "flattened (x,y) per kp"}, {"type": "heatmap_channels", "channels": 12, "kps": 4, "layout": "channels as (x,y,score) maps"}]
  - guess for box_scores: [{"type": "flat", "kps": 448, "layout": "flattened (x,y) per kp"}]
