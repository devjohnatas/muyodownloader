@echo off
title Muyo Download
cls
echo ========================================================
echo   Iniciando o sistema MUYO DOWNLOAD...
echo ========================================================
python main.py
if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Falha ao executar o Muyo Download. Certifique-se de que as dependencias (pip install -r requirements.txt) foram instaladas.
    pause
)
