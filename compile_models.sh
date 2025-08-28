#!/usr/bin/env bash
# compile_models.sh - small wrapper to run qai_hub_optimize_full.py with common flags
# Usage:
#   ./compile_models.sh [--upload] [--submit] [--profile] [--export_local]

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_CMD="${PYTHON_CMD:-python3}"
SCRIPT="$PROJECT_DIR/src/qaihub_optimize/qai_hub_optimize_full.py"
REPORTS_DIR="$PROJECT_DIR/reports"

# Ensure reports dir exists
mkdir -p "$REPORTS_DIR"

# logfile for this run
STAMP="$(date +%Y%m%d_%H%M%S)"
LOGFILE="$REPORTS_DIR/compile_run_${STAMP}.log"

echo "Running model compile script: $SCRIPT"
if [ ! -f "$SCRIPT" ]; then
  echo "找不到 $SCRIPT，請確認檔案存在。"
  exit 1
fi

# Determine whether interactive confirmation is required for upload/submit
NEEDS_CONFIRM=0
FORCE_YES=0
for a in "$@"; do
  if [ "$a" = "--upload" ] || [ "$a" = "--submit" ]; then
    NEEDS_CONFIRM=1
  fi
  if [ "$a" = "--yes" ] || [ "$a" = "-y" ]; then
    FORCE_YES=1
  fi
done

if [ $NEEDS_CONFIRM -eq 1 ]; then
  if [ -z "${QAI_HUB_API_TOKEN:-}" ]; then
    echo "Warning: QAI_HUB_API_TOKEN is not set but --upload/--submit requested. Aborting." | tee -a "$LOGFILE"
    exit 1
  fi
  if [ $FORCE_YES -eq 0 ]; then
    # list candidate files to upload (best-effort)
    CAND_DIRS=("$PROJECT_DIR/src/models/qaihub_optimized" "$PROJECT_DIR/src/models/deploy" "$PROJECT_DIR/models/qaihub_optimized")
    echo "About to upload/submit models to QAI Hub. Candidate files:" | tee -a "$LOGFILE"
    ANY=0
    for d in "${CAND_DIRS[@]}"; do
      if [ -d "$d" ]; then
        echo "  $d:" | tee -a "$LOGFILE"
        ls -1 "$d" | sed 's/^/    /' | tee -a "$LOGFILE"
        ANY=1
      fi
    done
    if [ $ANY -eq 0 ]; then
      echo "  (no local optimized models found under candidate dirs)" | tee -a "$LOGFILE"
    fi
    read -p "Proceed with upload/submit? [y/N] " RESP
    case "$RESP" in
      [yY]|[yY][eE][sS]) ;;
      *) echo "Aborted by user" | tee -a "$LOGFILE"; exit 1 ;;
    esac
  else
    echo "--yes provided; skipping interactive confirmation." | tee -a "$LOGFILE"
  fi
fi

echo "Running model compile script: $SCRIPT" | tee -a "$LOGFILE"
echo "Logging to: $LOGFILE" | tee -a "$LOGFILE"

# Run script and capture stdout/stderr to logfile
set +e
$PYTHON_CMD "$SCRIPT" "$@" >>"$LOGFILE" 2>&1
RC=$?
set -e

if [ $RC -eq 0 ]; then
  echo "Compile script finished successfully (exit 0)." | tee -a "$LOGFILE"
else
  echo "Compile script failed with exit code $RC. See $LOGFILE for details." | tee -a "$LOGFILE"
fi

exit $RC
