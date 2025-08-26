@echo off
echo ========================================
echo Dragon X Fall Detection Launcher
echo ========================================

echo Adding mock QAI Hub to Python path...
set PYTHONPATH=C:\dragon-x-fall-detection;%PYTHONPATH%

echo Launching Dragon X Fall Detection System...
cd C:\dragon-x-fall-detection
python -c "import sys; sys.path.insert(0, r'C:\dragon-x-fall-detection'); from mock_qai_hub import *; import dragon_x_fall_detection_system; dragon_x_fall_detection_system.main()"

echo ========================================
echo Application execution completed
echo ========================================
