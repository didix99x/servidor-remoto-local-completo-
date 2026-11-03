@echo off
chcp 65001 > nul
title Parar Servidor
color 0C

echo.
echo  Parando o servidor Home Network Control Center...
echo.

REM Encerrar processos uvicorn/python do projeto
taskkill /F /FI "WINDOWTITLE eq Home Network Control Center*" /T > nul 2>&1
taskkill /F /IM "uvicorn.exe" /T > nul 2>&1

REM Tentar via porta
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    echo  Encerrando processo na porta 8000 (PID: %%a)...
    taskkill /F /PID %%a > nul 2>&1
)

echo  [OK] Servidor parado.
echo.
pause
