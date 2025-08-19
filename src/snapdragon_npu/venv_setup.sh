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
pip install -r requirements_snapdragon.txt
