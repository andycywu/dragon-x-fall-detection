# 🐉 Qualcomm Device Cloud 連接指南

## 🔑 SSH隧道連接方法

Qualcomm Device Cloud需要通過SSH隧道進行連接，我們提供了兩個腳本來幫助你輕鬆連接：

### 1. 設置SSH隧道

使用 `qdc_tunnel.sh` 腳本設置SSH隧道：

```bash
# 啟動SSH隧道
./qdc_tunnel.sh

# 這將創建從本地端口2222到Qualcomm Device Cloud的隧道
# ssh.qdc.qualcomm.com -> sa296481.sa.svc.cluster.local:22
```

### 2. 直接部署到設備

使用 `connect_device_cloud.sh` 腳本一鍵部署：

```bash
# 設置隧道並部署
./connect_device_cloud.sh
```

## 🧠 連接細節說明

### SSH隧道設置
```
ssh -i qdc_id_2025-8-11_62.pem -L 2222:sa296481.sa.svc.cluster.local:22 -N sshtunnel@ssh.qdc.qualcomm.com
```

這個命令做了以下工作：
- `-i qdc_id_2025-8-11_62.pem`: 使用SSH密鑰進行身份驗證
- `-L 2222:sa296481.sa.svc.cluster.local:22`: 將本地端口2222轉發到目標設備的22端口
- `-N`: 不執行遠程命令，僅設置隧道
- `sshtunnel@ssh.qdc.qualcomm.com`: 通過QDC的SSH閘道連接

### 通過隧道連接設備
```bash
ssh -i qdc_id_2025-8-11_62.pem -o StrictHostKeychecking=no -o UserKnownHostsFile=/dev/null -p 2222 hcktest@localhost
```

這個命令使用隧道連接到設備：
- `-i qdc_id_2025-8-11_62.pem`: 使用SSH密鑰進行身份驗證
- `-o StrictHostKeychecking=no -o UserKnownHostsFile=/dev/null`: 忽略主機密鑰檢查和主機記錄
- `-p 2222`: 使用本地端口2222（隧道入口）
- `hcktest@localhost`: 使用hcktest用戶連接到隧道另一端的設備

## 🚀 GitHub部署工作流程

我們現在使用GitHub作為代碼源，這使得部署和更新更加高效：

### 初始部署
1. 運行部署腳本：`./connect_device_cloud.sh`
2. 腳本會自動：
   - 設置SSH隧道
   - 創建部署腳本
   - 在設備上克隆GitHub倉庫
   - 設置運行環境

### 更新流程
當你的代碼有更新時：
1. 提交更改到GitHub：
   ```bash
   git add .
   git commit -m "更新描述"
   git push
   ```
2. 在設備上更新代碼：
   ```bash
   ssh -i qdc_id_2025-8-11_62.pem -p 2222 hcktest@localhost
   cd /opt/dragon_x_fall_detection
   git pull
   ```

這種方法比逐個文件上傳要高效得多，特別是在頻繁更新的情況下。

## 📋 常見問題

### 端口已被占用
如果2222端口已被使用，可以選擇其他端口：
```bash
ssh -i qdc_id_2025-8-11_62.pem -L 2223:sa296481.sa.svc.cluster.local:22 -N sshtunnel@ssh.qdc.qualcomm.com -f
```

然後使用新端口連接：
```bash
ssh -i qdc_id_2025-8-11_62.pem -p 2223 root@localhost
```

### 連接被拒絕
1. 確認SSH密鑰權限正確：`chmod 600 qdc_id_2025-8-11_62.pem`
2. 確認隧道正在運行：`lsof -i:2222`
3. 嘗試重新啟動隧道：`kill $(lsof -ti:2222) && ./qdc_tunnel.sh`

### GitHub克隆失敗
1. 確認網絡連接
2. 確認倉庫是公開的或你有適當的訪問權限
3. 可以嘗試手動克隆：
   ```bash
   cd /opt
   sudo rm -rf dragon_x_fall_detection # 小心使用此命令
   sudo git clone https://github.com/andycywu/dragon-x-fall-detection.git dragon_x_fall_detection
   ```

---

🏆 準備好在Snapdragon X Elite上征服黑客松！
