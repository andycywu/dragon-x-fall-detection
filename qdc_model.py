import streamlit as st
import onnxruntime as ort
import numpy as np
from PIL import Image

# 載入模型
so = ort.SessionOptions()
so.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
sess = ort.InferenceSession(
    "model.onnx",
    sess_options=so,
    providers=["QNNExecutionProvider"],
    provider_options=[{"backend_path": "QnnHtp.dll"}],
)
input_name = sess.get_inputs()[0].name
input_shape = sess.get_inputs()[0].shape

st.title("QAI Model Streamlit Demo")
img_file = st.camera_input("請拍攝或上傳一張照片")

if img_file is not None:
    img = Image.open(img_file)
    img = img.resize((input_shape[3], input_shape[2]))
    img_np = np.array(img).astype(np.float32)
    if img_np.shape[2] == 4:  # RGBA
        img_np = img_np[:, :, :3]
    img_np = img_np.transpose(2, 0, 1) / 255.0
    img_np = np.expand_dims(img_np, axis=0)
    out = sess.run(None, {input_name: img_np})
    st.image(img, caption=f"推論結果 shape: {[o.shape for o in out]}")
    st.write("推論結果 shape:", [o.shape for o in out])