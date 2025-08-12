#!/bin/bash
# 在 Qualcomm 裝置上拉取最新的程式碼
# 使用方法: ./qualcomm_pull_latest.sh

echo "===== 在 Qualcomm 裝置上拉取最新的程式碼 ====="
echo "開始更新本地存儲庫..."

# 確保我們在正確的目錄中
cd "$(dirname "$0")" || { echo "無法進入腳本目錄"; exit 1; }

# 檢查是否為 git 存儲庫
if [ ! -d ".git" ]; then
  echo "錯誤: 此目錄不是 git 存儲庫"
  echo "請在正確的存儲庫目錄中運行此腳本"
  exit 1
fi

# 檢查網絡連接
echo "檢查網絡連接..."
if ! ping -c 1 github.com &> /dev/null; then
  echo "警告: 無法連接到 GitHub，請檢查您的網絡連接"
  echo "嘗試繼續..."
fi

# 保存本地更改（如果有的話）
if [ -n "$(git status --porcelain)" ]; then
  echo "檢測到本地更改，正在保存..."
  git stash
  STASHED=true
else
  STASHED=false
fi

# 拉取最新更改
echo "正在從 GitHub 拉取最新更改..."
git pull origin main

# 檢查拉取是否成功
if [ $? -eq 0 ]; then
  echo "成功拉取最新的程式碼！"
else
  echo "拉取時出現問題，請檢查錯誤訊息"
fi

# 恢復之前的本地更改（如果有的話）
if [ "$STASHED" = true ]; then
  echo "正在恢復本地更改..."
  git stash pop
  echo "本地更改已恢復"
fi

echo "===== 完成 ====="
echo "若需要任何協助，請聯繫開發團隊"
