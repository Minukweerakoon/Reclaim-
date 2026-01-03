@echo off
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
echo Starting TrackBehavior Backend Server...
python app.py
pause
