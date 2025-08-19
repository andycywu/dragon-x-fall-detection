

# MediaPipe 官方子模組 tflite 模型自動下載腳本
# 下載常用 MediaPipe tflite 模型到 models/original/

set -e
MODEL_DIR="$(dirname "$0")/../models/original"
mkdir -p "$MODEL_DIR"

# face_detection
wget -O "$MODEL_DIR/face_detection_short_range.tflite" \
  https://storage.googleapis.com/mediapipe-assets/face_detection_short_range.tflite
wget -O "$MODEL_DIR/face_detection_full_range.tflite" \
  https://storage.googleapis.com/mediapipe-assets/face_detection_full_range.tflite

# face_geometry (暫無官方 tflite，僅有 calculator)

# face_landmark
wget -O "$MODEL_DIR/face_landmark.tflite" \
  https://storage.googleapis.com/mediapipe-assets/face_landmark.tflite
wget -O "$MODEL_DIR/face_landmark_with_attention.tflite" \
  https://storage.googleapis.com/mediapipe-assets/face_landmark_with_attention.tflite

# hand_landmark
wget -O "$MODEL_DIR/hand_landmark.tflite" \
  https://storage.googleapis.com/mediapipe-assets/hand_landmark.tflite
wget -O "$MODEL_DIR/hand_recrop.tflite" \
  https://storage.googleapis.com/mediapipe-assets/hand_recrop.tflite

# holistic_landmark (組合模型，需用 pose/face/hand landmark)
# 下載 pose/face/hand landmark 即可

# iris_landmark
wget -O "$MODEL_DIR/iris_landmark.tflite" \
  https://storage.googleapis.com/mediapipe-assets/iris_landmark.tflite

# palm_detection
wget -O "$MODEL_DIR/palm_detection.tflite" \
  https://storage.googleapis.com/mediapipe-assets/palm_detection.tflite

# pose_detection
wget -O "$MODEL_DIR/pose_detection.tflite" \
  https://storage.googleapis.com/mediapipe-assets/pose_detection.tflite

# pose_landmark
wget -O "$MODEL_DIR/pose_landmark_heavy.tflite" \
  https://storage.googleapis.com/mediapipe-assets/pose_landmark_heavy.tflite
wget -O "$MODEL_DIR/pose_landmark_lite.tflite" \
  https://storage.googleapis.com/mediapipe-assets/pose_landmark_lite.tflite
wget -O "$MODEL_DIR/pose_landmark_full.tflite" \
  https://storage.googleapis.com/mediapipe-assets/pose_landmark_full.tflite

# objectron (無官方 tflite，僅有 calculator)

echo "✅ MediaPipe 官方模型下載完成，儲存於 $MODEL_DIR"
