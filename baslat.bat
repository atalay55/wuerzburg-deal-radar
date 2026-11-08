@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================================
echo   Wuerzburg Black Friday Deal Radar (@Indirim_black_bot)
echo ========================================================
python -m src.main --loop
pause

