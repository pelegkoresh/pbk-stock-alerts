@echo off
title PBK Stock Alerts — Stopping...
color 0C
echo.
echo  עוצר את המערכת...
echo.
taskkill /f /im python.exe >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq PBK Monitor" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq PBK Dashboard" >nul 2>&1
echo  ✅ המערכת עצרה.
timeout /t 2 /nobreak >nul
