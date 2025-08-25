from ultralytics import YOLO
import os
import zipfile

def export_yolo_model(model_name, output_dir):
    """
    將 YOLO 模型導出為 ONNX 格式。

    Args:
        model_name (str): YOLO 模型名稱（例如 'yolo11n', 'yolo11s', 'yolo11m'）。
        output_dir (str): 輸出目錄。

    Returns:
        None
    """
    try:
        model = YOLO(f"{model_name}.pt")  # 使用正確的 YOLO 模型名稱
        model.export(format="onnx", imgsz=640, dynamic=True, simplify=True, device="cpu")
        print(f"✅ 成功導出 {model_name} 為 ONNX 格式")
    except Exception as e:
        print(f"❌ 導出 {model_name} 失敗: {str(e)}")

def mp_task_url(task, variant=None, quant="float16", version="latest"):
    """
    生成 MediaPipe 模型的下載 URL。

    Args:
        task (str): 模型任務名稱，例如 "pose_landmarker"。
        variant (str): 模型變體，例如 "pose_landmarker_lite"。
        quant (str): 量化類型，例如 "float16"。
        version (str): 模型版本，例如 "latest"。

    Returns:
        str: 生成的下載 URL。
    """
    if task == "pose_landmarker":
        assert variant in ("pose_landmarker_lite", "pose_landmarker_full", "pose_landmarker_heavy"), f"Invalid variant for {task}: {variant}"
        bundle = variant
    elif task in ("hand_landmarker", "face_landmarker"):
        bundle = task  # 這些任務不需要變體
    else:
        raise ValueError(f"unknown task: {task}")

    return f"https://storage.googleapis.com/mediapipe-models/{task}/{bundle}/{quant}/{version}/{bundle}.task"

# 確保 subprocess 在函數內正確使用
import subprocess

def download_mediapipe_model(task, output_path, variant=None):
    """
    下載 MediaPipe 模型。

    Args:
        task (str): MediaPipe 主任務名稱（例如 'pose_landmarker'）。
        output_path (str): 輸出模型的完整路徑。
        variant (str): 模型變體名稱（例如 'pose_landmarker_lite'）。

    Returns:
        None
    """
    if os.path.exists(output_path):
        print(f"✅ 模型已存在，跳過下載: {output_path}")
        return

    try:
        model_url = mp_task_url(task, variant=variant, quant="float16", version="latest")
        subprocess.run([
            "curl", "-f", "-o", output_path, model_url
        ], check=True)
        print(f"✅ 成功下載 {variant or task} 模型到 {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ 使用 curl 下載 {variant or task} 模型失敗: {e}")
    except AssertionError as e:
        print(f"❌ 無效的參數: {e}")

def convert_mediapipe_to_onnx(task, variant=None, quant="float16", version="latest", output_dir="/Users/andycyw/mvp_fall_detection_starter/src/models/raw"):
    """
    將 MediaPipe 模型下載並轉換為 ONNX 格式。

    Args:
        task (str): 模型任務名稱，例如 "pose_landmarker"。
        variant (str): 模型變體，例如 "pose_landmarker_lite"。
        quant (str): 量化類型，例如 "float16"。
        version (str): 模型版本，例如 "latest"。
        output_dir (str): 輸出目錄。

    Returns:
        None
    """
    import subprocess
    import os

    # 生成下載 URL
    model_url = mp_task_url(task, variant=variant, quant=quant, version=version)
    task_name = variant if variant else task
    task_path = os.path.join(output_dir, f"{task_name}.task")
    onnx_path = os.path.join(output_dir, f"{task_name}.onnx")

    # 下載 .task 文件
    try:
        # 使用 curl 下載文件
        import subprocess
        subprocess.run([
            "curl", "-f", "-o", task_path, model_url
        ], check=True)
        print(f"✅ 成功下載 {task_name} 模型到 {task_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ 下載 {task_name} 模型失敗: {e}")
        return

def extract_tflite_from_task(task_path, output_dir):
    """
    從 .task ZIP 包中提取 .tflite 模型。

    Args:
        task_path (str): .task 文件的路徑。
        output_dir (str): 解壓縮後的輸出目錄。

    Returns:
        str: 提取的 .tflite 模型的路徑。
    """
    if not os.path.exists(task_path):
        print(f"❌ 文件不存在，無法解壓縮: {task_path}")
        return None

    try:
        with zipfile.ZipFile(task_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
            for file_name in zip_ref.namelist():
                if file_name.endswith('.tflite'):
                    tflite_path = os.path.join(output_dir, file_name)
                    print(f"✅ 成功提取 {tflite_path}")
                    return tflite_path
        print(f"❌ 未找到 .tflite 文件於 {task_path}")
    except Exception as e:
        print(f"❌ 解壓縮 {task_path} 失敗: {str(e)}")
    return None

# 確保 subprocess 已正確導入
import subprocess

# 更新主程式邏輯
if __name__ == "__main__":
    output_dir = "/Users/andycyw/mvp_fall_detection_starter/src/models/raw"  # 修正為絕對路徑
    os.makedirs(output_dir, exist_ok=True)

    # 導出 YOLO 模型
    export_yolo_model("yolo11n", output_dir)
    export_yolo_model("yolo11s", output_dir)
    export_yolo_model("yolo11m", output_dir)

    # 下載 MediaPipe 模型
    tasks_and_variants = [
        ("pose_landmarker", "pose_landmarker_lite"),
        ("pose_landmarker", "pose_landmarker_full"),
        ("pose_landmarker", "pose_landmarker_heavy"),
        ("hand_landmarker", None),
        ("face_landmarker", None)
    ]

    for task, variant in tasks_and_variants:
        output_path = os.path.join(output_dir, f"{variant or task}.task")
        download_mediapipe_model(task, output_path, variant=variant)

    # 解壓縮 .task 文件並提取 .tflite 模型
    for task, variant in tasks_and_variants:
        task_path = os.path.join(output_dir, f"{variant or task}.task")
        tflite_path = extract_tflite_from_task(task_path, output_dir)
        if tflite_path:
            convert_mediapipe_to_onnx(task, variant=variant)
