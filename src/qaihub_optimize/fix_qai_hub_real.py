import os
import sys

def patch_qai_hub_system():
    """修補 dragon_x_fall_detection_system.py 文件以使用環境變數"""
    
    # 檔案路徑
    file_path = "C:\\dragon-x-fall-detection\\dragon_x_fall_detection_system.py"
    
    try:
        # 讀取原始檔案
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 尋找 import qai_hub as hub 行
        import_line = "import qai_hub as hub"
        
        # 建立新的程式碼片段來使用環境變數
        new_code = """import qai_hub as hub
import os

# 設置 QAI Hub 環境變數
os.environ["QAI_API_KEY"] = "pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d"
os.environ["QAI_API_TOKEN"] = "pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d"
os.environ["QAI_HOST"] = "https://api.aihub.qualcomm.com"
os.environ["QAI_API_URL"] = "https://api.aihub.qualcomm.com"
os.environ["QAI_API_VERSION"] = "v1"

# 輸出環境變數狀態
print("QAI Hub 環境變數已設置")
"""
        
        # 取代程式碼
        modified_content = content.replace(import_line, new_code)
        
        # 寫回檔案
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(modified_content)
        
        print("成功修補 dragon_x_fall_detection_system.py 文件，使其使用環境變數。")
        return True
        
    except Exception as e:
        print(f"修補失敗: {str(e)}")
        
        # 嘗試使用不同的編碼
        try:
            encodings = ["latin1", "cp1252", "iso-8859-1"]
            
            for encoding in encodings:
                try:
                    with open(file_path, "r", encoding=encoding) as f:
                        content = f.read()
                    
                    # 取代程式碼
                    modified_content = content.replace(import_line, new_code)
                    
                    # 寫回檔案
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(modified_content)
                    
                    print(f"成功使用 {encoding} 編碼修補文件。")
                    return True
                except Exception as inner_e:
                    print(f"{encoding} 編碼嘗試失敗: {str(inner_e)}")
        except Exception as outer_e:
            print(f"所有編碼嘗試均失敗: {str(outer_e)}")
        
        return False

if __name__ == "__main__":
    success = patch_qai_hub_system()
    
    if success:
        print("修補成功！現在可以執行原始的 Dragon X 系統，使用真實的 QAI Hub。")
    else:
        print("修補失敗。請嘗試其他方法。")
    
    print("按任意鍵退出...")
    input()
