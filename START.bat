@echo off
title PBK Stock Alerts — Starting...
color 0A
cls

echo.
echo  ██████╗ ██████╗ ██╗  ██╗    ███████╗████████╗ ██████╗  ██████╗██╗  ██╗
echo  ██╔══██╗██╔══██╗██║ ██╔╝    ██╔════╝╚══██╔══╝██╔═══██╗██╔════╝██║ ██╔╝
echo  ██████╔╝██████╔╝█████╔╝     ███████╗   ██║   ██║   ██║██║     █████╔╝
echo  ██╔═══╝ ██╔══██╗██╔═██╗     ╚════██║   ██║   ██║   ██║██║     ██╔═██╗
echo  ██║     ██████╔╝██║  ██╗    ███████║   ██║   ╚██████╔╝╚██████╗██║  ██╗
echo  ╚═╝     ╚═════╝ ╚═╝  ╚═╝    ╚══════╝   ╚═╝    ╚═════╝  ╚═════╝╚═╝  ╚═╝
echo.
echo  PBK Stock Alerts — Institutional Market Monitor
echo  ================================================
echo.

cd /d C:\PBK_STOCK

echo [1/3] בודק ספריות Python...
python -c "import streamlit, requests, pandas" >nul 2>&1
if errorlevel 1 (
    echo מתקין ספריות...
    pip install -r requirements.txt
)
echo    OK

echo [2/3] פותח מנטור רקע...
start "PBK Monitor" cmd /k "cd /d C:\PBK_STOCK && python monitor.py"
timeout /t 2 /nobreak >nul
echo    OK

echo [3/3] מפעיל דשבורד...
start "PBK Dashboard" cmd /k "cd /d C:\PBK_STOCK && python -m streamlit run dashboard.py"
timeout /t 3 /nobreak >nul
echo    OK

echo.
echo  ✅ המערכת פעילה!
echo.
echo  האתר: http://localhost:8501
echo  Telegram Bot: https://t.me/PBKStockAlertsBot
echo.
echo  סגור חלון זה — המערכת תמשיך לרוץ ברקע
echo.
timeout /t 5 /nobreak >nul
start "" "http://localhost:8501"
