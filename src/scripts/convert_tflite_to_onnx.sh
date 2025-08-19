#!/bin/bash
# MediaPipe tflite → ONNX 自動轉換腳本
# 需安裝 tf2onnx, tensorflow, onnx

set -e
MODEL_DIR="$(dirname "$0")/../models/original"
ONNX_DIR="$(dirname "$0")/../models/onnx"
mkdir -p "$ONNX_DIR"

# 轉換函式
convert_tflite_to_onnx() {
  tflite_file="$1"
  onnx_file="$2"
  echo "\n🔄 轉換 $tflite_file → $onnx_file ..."
  python3 -m tf2onnx.convert --tflite "$tflite_file" --output "$onnx_file" || echo "⚠️  轉換失敗: $tflite_file"
}

# 對 models/original 目錄下所有 tflite 進行轉換
for tflite in "$MODEL_DIR"/*.tflite; do
  base=$(basename "$tflite" .tflite)
  onnx="$ONNX_DIR/$base.onnx"
  convert_tflite_to_onnx "$tflite" "$onnx"
done

echo "\n✅ ONNX 轉換完成，儲存於 $ONNX_DIR"
