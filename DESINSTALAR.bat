@echo off
chcp 65001 > nul
title Desinstalar Home Network Control Center
color 0C

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║         HOME NETWORK CONTROL CENTER                 ║
echo  ║                DESINSTALADOR                        ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
echo  ATENCAO: Esta operacao ira remover o ambiente Python.
echo  Os arquivos compartilhados NAO serao excluidos.
echo.
set /p CONFIRM="Digite SIM para confirmar: "
if /i not "%CONFIRM%"=="SIM" (
    echo  Operacao cancelada.
    pause
    exit /b 0
)

echo.
echo  Parando servidor se estiver rodando...
call PARAR.bat > nul 2>&1

echo  Removendo ambiente virtual...
if exist "venv" (
    rmdir /s /q "venv"
    echo  [OK] Ambiente virtual removido.
)

echo  Removendo cache...
if exist "backend\cache" (
    rmdir /s /q "backend\cache"
    echo  [OK] Cache removido.
)

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║  Desinstalacao concluida.                           ║
echo  ║  Execute INSTALAR.bat para reinstalar.              ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
pause
