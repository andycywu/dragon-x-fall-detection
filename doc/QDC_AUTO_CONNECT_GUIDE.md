# QDC 自動連接與設置指南

本指南提供了使用自動化腳本來快速連接和設置 Qualcomm Device Cloud (QDC) 環境的方法。

## 重要更新：QDC 主機名動態變更與 Windows 環境支持

**每天的 QDC session 主機名都會變動**，例如從 `sa296481.sa.svc.cluster.local` 變為 `sa297036.sa.svc.cluster.local`。最新版腳本現在支持手動輸入主機名。

**重要：QDC 環境為 Windows 系統**，已更新所有腳本以支持 Windows 環境。

## 自動化腳本說明

在本項目中，我們提供了以下自動化腳本：

### MacOS/Linux 腳本

1. **`qdc_auto_connect.sh`** - 負責在 Mac 上建立 SSH 隧道並連接到 QDC
   - 支持輸入當天的 QDC 主機名
   - 記住上次使用的主機名作為默認值
   - 自動檢測 QDC 環境類型（Windows/Linux）
   
2. **`qdc_setup.sh`** - 在 QDC 上設置環境和必要配置
   - 由 `qdc_auto_connect.sh` 自動生成和上傳

3. **`qdc_setup_all.sh`** - 一鍵完成連接和設置
   - 自動識別 QDC 環境並使用適當的腳本

4. **`qdc_ssh.sh`** - 快速 SSH 連接到 QDC
   - 使用上次設置的主機名自動連接
   - 負責建立隧道並直接進入 SSH

### Windows 批處理腳本

1. **`qdc_auto_connect.bat`** - Windows 版本的自動連接腳本
2. **`qdc_ssh.bat`** - Windows 版本的快速連接腳本
3. **`qdc_setup.bat`** - Windows 版本的環境設置腳本
4. **`qdc_setup_all.bat`** - Windows 版本的一鍵設置腳本

## 使用方法

### 首次設置或主機名變更時

當 QDC session 重啟或主機名變更時，請執行：

#### MacOS/Linux

```bash
./qdc_auto_connect.sh
```

#### Windows

```batch
qdc_auto_connect.bat
```

腳本會提示您輸入當天的主機名，格式如：`sa297036.sa.svc.cluster.local`

### 日常快速連接

設置好主機名後，日常使用只需執行：

#### MacOS/Linux

```bash
./qdc_ssh.sh
```

#### Windows

```batch
qdc_ssh.bat
```

此腳本會自動使用上次設置的主機名建立隧道並連接。

### 一次性完整設置

如果需要全新設置環境：

#### MacOS/Linux

```bash
./qdc_setup_all.sh
```

#### Windows

```batch
qdc_setup_all.bat
```

## 獲取當天的主機名

每天的 QDC 主機名可以通過以下方式獲取：

1. 從 QDC 網頁界面查看連接資訊
2. 從提供的 SSH 連接命令中提取：
   ```bash
   ssh -i <PRIVATE_KEY_FILE_PATH> -L 2222:sa297036.sa.svc.cluster.local:22 -N sshtunnel@ssh.qdc.qualcomm.com
   ```
   在這個例子中，主機名是 `sa297036.sa.svc.cluster.local`

## 注意事項

1. QDC 上的 session 每天都會重啟，主機名也會變更
2. QDC 環境為 Windows 系統，腳本已適配 Windows 命令語法
3. SSH 隧道會在背景運行，要停止隧道，可以執行：
   ```bash
   # MacOS/Linux
   kill $(lsof -ti:2222)
   
   # Windows
   # 使用任務管理器結束 SSH 進程
   ```
4. 腳本會自動保存最近使用的主機名到配置文件中：
   - MacOS/Linux: `~/.qdc_config`
   - Windows: `%USERPROFILE%\.qdc_config.txt`

## QAI Hub 相關配置

如果在 Windows ARM 平台上使用 QAI Hub，需要注意：

1. 使用 x64 版本的 Python 3.10，而不是 ARM64 版本
2. 確保 protobuf 版本為 4.25.3
3. QAI Hub 配置文件應如下所示：

```ini
[default]
api_token = pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
api_key = pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
base_api_url = https://app.aihub.qualcomm.com
web_url = https://app.aihub.qualcomm.com
```

## 自動化腳本的優勢

使用這些自動化腳本的主要優勢：

1. 簡化了連接過程
2. 自動處理 SSH 隧道設置
3. 自動安裝和配置所需的軟件
4. 處理 QDC session 每日重啟和主機名變更的問題
5. 自動檢測並適配 Windows 環境
6. 確保 QAI Hub 配置正確
