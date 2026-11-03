@echo off
chcp 65001 > nul
title Home Network Control Center — Servidor
color 0A

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║        HOME NETWORK CONTROL CENTER — INICIANDO      ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

REM ── Verificar instalacao ─────────────────────────────────────────
if not exist "venv\Scripts\activate.bat" (
    echo  [ERRO] Ambiente virtual nao encontrado.
    echo  Execute INSTALAR.bat primeiro.
    echo.
    pause
    exit /b 1
)

REM ── Ativar ambiente virtual ───────────────────────────────────────
call venv\Scripts\activate.bat

REM ── Detectar IP local ─────────────────────────────────────────────
for /f "tokens=2 delims=:" %%i in ('ipconfig ^| findstr /C:"IPv4"') do (
    set LOCAL_IP=%%i
    goto :ip_found
)
:ip_found
set LOCAL_IP=%LOCAL_IP: =%

echo  Detectando endereco IP local...
echo.
echo  ┌──────────────────────────────────────────────────────┐
echo  │  Acesse pelo navegador de qualquer dispositivo       │
echo  │  conectado a mesma rede Wi-Fi:                       │
echo  │                                                      │
echo  │   http://%LOCAL_IP%:8000                         
echo  │   http://localhost:8000 (somente neste PC)           │
echo  │                                                      │
echo  │  Credenciais:  admin / Admin@1234                    │
echo  │  (Altere a senha apos o primeiro acesso)             │
echo  │                                                      │
echo  │  Pressione Ctrl+C para parar o servidor              │
echo  └──────────────────────────────────────────────────────┘
echo.

REM ── Iniciar o servidor ───────────────────────────────────────────
cd backend
..\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info

echo.
echo  Servidor encerrado.
pause
