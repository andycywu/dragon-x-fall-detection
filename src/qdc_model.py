import streamlit as st
import onnxruntime as ort
import numpy as np
from PIL import Image
import os

st.title("QAI Model Streamlit Demo")

# 模型選擇
model_files = [f for f in os.listdir('.') if f.endswith('.onnx')]
if not model_files:
    st.error("找不到任何 .onnx 模型檔案，請放入模型檔於本目錄！")
    st.stop()
model_path = st.selectbox("請選擇模型檔案：", model_files)

# 載入模型（優先 QNN，失敗自動 fallback CPU）
so = ort.SessionOptions()
so.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
try:
    sess = ort.InferenceSession(
        model_path,
        sess_options=so,
        providers=["QNNExecutionProvider"],
        provider_options=[{"backend_path": "QnnHtp.dll"}],
    )
except Exception:
    sess = ort.InferenceSession(
        model_path,
        sess_options=so,
        providers=["CPUExecutionProvider"],
    )
input_name = sess.get_inputs()[0].name
input_shape = sess.get_inputs()[0].shape

# 影像來源選擇
input_mode = st.radio("選擇影像來源：", ("上傳圖片", "攝影機拍照"))
img_file = None
if input_mode == "上傳圖片":
    img_file = st.file_uploader("請選擇一張圖片", type=["jpg", "jpeg", "png"])
elif input_mode == "攝影機拍照":
    img_file = st.camera_input("請拍攝一張照片")

if img_file is not None:
    img = Image.open(img_file)
    img = img.resize((input_shape[3], input_shape[2]))
    img_np = np.array(img).astype(np.float32)
    if img_np.ndim == 2:
        img_np = np.stack([img_np]*3, axis=-1)
    if img_np.shape[2] == 4:  # RGBA
        img_np = img_np[:, :, :3]
    img_np = img_np.transpose(2, 0, 1) / 255.0
    img_np = np.expand_dims(img_np, axis=0)
    out = sess.run(None, {input_name: img_np})
    st.image(img, caption=f"推論結果 shape: {[o.shape for o in out]}")
    st.write("推論結果 shape:", [o.shape for o in out])