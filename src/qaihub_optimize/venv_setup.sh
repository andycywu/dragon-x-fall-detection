if [[ "$(uname -s)" == "Darwin" && "$(uname -m)" == "arm64" ]]; then
	export LDFLAGS="-L/opt/homebrew/opt/openblas/lib"
	export CPPFLAGS="-I/opt/homebrew/opt/openblas/include"
	export PKG_CONFIG_PATH="/opt/homebrew/opt/openblas/lib/pkgconfig"
fi
#!/bin/bash
cd "$(dirname "$0")"
# 若已存在 .venv，先移除
if [ -d ".venv" ]; then
	echo "移除舊有 .venv..."
	rm -rf .venv
fi
PYTHON_BIN="$(pyenv root 2>/dev/null)/versions/3.10.14/bin/python"
if [ -x "$PYTHON_BIN" ]; then
	"$PYTHON_BIN" -m venv .venv
else
	python3 -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements_qaihub.txt

# 自動設定 QAI Hub CLI 並修正 client.ini 欄位
if [ -f .env ]; then
	QAI_TOKEN=$(grep '^QAI_HUB_API_TOKEN=' .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" | xargs)
	if [ -n "$QAI_TOKEN" ]; then
		echo "\n🔑 自動設定 QAI Hub CLI..."
		qai-hub configure --api_token "$QAI_TOKEN"
		# 強制覆蓋 ~/.qai_hub/client.ini，確保格式正確
		mkdir -p "$HOME/.qai_hub"
		cat > "$HOME/.qai_hub/client.ini" <<EOF
[api]
api_token = $QAI_TOKEN
api_url = https://app.aihub.qualcomm.com
web_url = https://app.aihub.qualcomm.com
verbose = True
EOF
		echo "✅ ~/.qai_hub/client.ini 已自動修正為正確格式"
	else
		echo "⚠️  .env 未設置 QAI_HUB_API_TOKEN，請手動設定 QAI Hub CLI。"
	fi
else
	echo "⚠️  未找到 .env，請手動設定 QAI Hub CLI。"
fi
