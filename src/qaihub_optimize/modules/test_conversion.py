from pathlib import Path
from conversion import ModelConverter

def test_convert_pt_to_onnx():
    converter = ModelConverter()
    pt_model_path = Path("/Users/andycyw/mvp_fall_detection_starter/src/models/raw/yolo11n-pose.pt")
    output_dir = Path("/Users/andycyw/mvp_fall_detection_starter/src/models/onnx")
    input_shape = (1, 3, 224, 224)  # 替換為模型的實際輸入形狀

    result = converter.convert_pt_to_onnx(pt_model_path, output_dir, input_shape)
    print(result)

if __name__ == "__main__":
    test_convert_pt_to_onnx()
