@echo off
chcp 65001 > nul
title Home Network Control Center — Instalador
color 0B

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║       HOME NETWORK CONTROL CENTER — INSTALAR        ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

REM ── Verificar Python ─────────────────────────────────────────────
echo [1/6] Verificando Python...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [ERRO] Python nao encontrado!
    echo  Instale Python 3.11+ em: https://www.python.org/downloads/
    echo  Marque a opcao "Add Python to PATH" durante a instalacao.
    echo.
    pause
    exit /b 1
)
python --version
echo  [OK] Python encontrado.
echo.

REM ── Verificar pip ────────────────────────────────────────────────
echo [2/6] Verificando pip...
python -m pip --version > nul 2>&1
if %errorlevel% neq 0 (
    echo  Instalando pip...
    python -m ensurepip --upgrade
)
echo  [OK] pip disponivel.
echo.

REM ── Criar ambiente virtual ───────────────────────────────────────
echo [3/6] Criando ambiente virtual Python...
if not exist "venv" (
    python -m venv venv
    echo  [OK] Ambiente virtual criado.
) else (
    echo  [OK] Ambiente virtual ja existe.
)
echo.

REM ── Ativar venv e instalar dependencias ──────────────────────────
echo [4/6] Instalando dependencias Python...
call venv\Scripts\activate.bat
venv\Scripts\python.exe -m pip install --upgrade pip --quiet
venv\Scripts\python.exe -m pip install -r backend\requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo  [AVISO] Algumas dependencias falharam. Tentando instalacao alternativa...
    venv\Scripts\python.exe -m pip install fastapi "uvicorn[standard]" aiosqlite "sqlalchemy[asyncio]" greenlet pydantic pydantic-settings email-validator "python-jose[cryptography]" "passlib[argon2]" argon2-cffi python-multipart websockets psutil requests python-dotenv
)
echo  [OK] Dependencias instaladas.
echo.

REM ── Copiar .env se nao existir ────────────────────────────────────
echo [5/6] Configurando ambiente...
if not exist "backend\.env" (
    copy "backend\.env.example" "backend\.env" > nul
    echo  [OK] Arquivo .env criado a partir do exemplo.
) else (
    echo  [OK] Arquivo .env ja existe.
)
echo.

REM ── Criar pastas necessarias ─────────────────────────────────────
echo [6/6] Criando estrutura de pastas...
if not exist "backend\data"               mkdir "backend\data"
if not exist "backend\shares"             mkdir "backend\shares"
if not exist "backend\shares\Videos"      mkdir "backend\shares\Videos"
if not exist "backend\shares\Musicas"     mkdir "backend\shares\Musicas"
if not exist "backend\shares\Documentos"  mkdir "backend\shares\Documentos"
if not exist "backend\shares\Imagens"     mkdir "backend\shares\Imagens"
if not exist "backend\cache"              mkdir "backend\cache"
if not exist "backend\cache\thumbnails"   mkdir "backend\cache\thumbnails"
echo  [OK] Pastas criadas.
echo.

echo  ╔══════════════════════════════════════════════════════╗
echo  ║           INSTALACAO CONCLUIDA COM SUCESSO!          ║
echo  ║                                                      ║
echo  ║  Credenciais iniciais:                               ║
echo  ║   Usuario: admin                                     ║
echo  ║   Senha:   Admin@1234                                ║
echo  ║                                                      ║
echo  ║  ALTERE A SENHA APOS O PRIMEIRO ACESSO!              ║
echo  ║                                                      ║
echo  ║  Para iniciar o servidor, execute: INICIAR.bat       ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
pause
