@echo off
REM ==========================================================================
REM VoxterFlix - instalador automatizado para Windows (CMD, sem PowerShell)
REM
REM Este script e seguro para executar mais de uma vez: ele reaproveita o
REM ambiente virtual, o banco de dados e o arquivo .env caso ja existam,
REM em vez de apagar ou sobrescrever o que voce ja configurou.
REM ==========================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ========================================
echo         VOXTERFLIX - INSTALADOR
echo ========================================
echo.

REM --------------------------------------------------------------------
REM [1/8] Verifica se o Python esta instalado e acessivel no PATH.
REM --------------------------------------------------------------------
echo [1/8] Verificando Python...
where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo ERRO: Python nao foi encontrado no PATH.
    echo.
    echo Instale o Python 3.13 ou superior em https://www.python.org/downloads/
    echo e marque a opcao "Add Python to PATH" durante a instalacao.
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYTHON_VERSION=%%v
echo OK - Python %PYTHON_VERSION% encontrado.
echo.

REM --------------------------------------------------------------------
REM [2/8] Cria o ambiente virtual somente se ele ainda nao existir.
REM --------------------------------------------------------------------
echo [2/8] Preparando ambiente virtual...
if exist "venv\Scripts\python.exe" (
    echo Ambiente virtual ja existe. Reutilizando...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo.
        echo ERRO: Nao foi possivel criar o ambiente virtual.
        exit /b 1
    )
    echo OK - Ambiente virtual criado.
)
echo.

REM --------------------------------------------------------------------
REM [3/8] Atualiza o pip e instala as dependencias do requirements.txt.
REM --------------------------------------------------------------------
echo [3/8] Instalando dependencias...
call "venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo.
    echo ERRO: Falha ao atualizar o pip.
    exit /b 1
)
call "venv\Scripts\pip.exe" install -r requirements.txt --quiet
if errorlevel 1 (
    echo.
    echo ERRO: Falha ao instalar as dependencias do requirements.txt.
    echo Verifique sua conexao com a internet e tente novamente.
    exit /b 1
)
echo OK - Dependencias instaladas.
echo.

REM --------------------------------------------------------------------
REM [4/8] Cria o .env a partir do .env.example, sem nunca sobrescrever
REM um .env que ja exista (evita apagar configuracoes do usuario).
REM --------------------------------------------------------------------
echo [4/8] Configurando ambiente...
if exist ".env" (
    echo .env ja existe. Mantendo configuracao atual...
) else (
    copy /y ".env.example" ".env" >nul
    echo .env criado a partir de .env.example.
    echo IMPORTANTE: edite o arquivo .env e configure OMDB_API_KEY, RESEND_API_KEY
    echo e SUPERFLIX_API_BASE_URL conforme necessario.
)
echo.

REM --------------------------------------------------------------------
REM [5/8] Executa as migracoes (idempotente: nao recria o que ja existe).
REM --------------------------------------------------------------------
echo [5/8] Executando migracoes...
call "venv\Scripts\python.exe" manage.py migrate
if errorlevel 1 (
    echo.
    echo ERRO: Falha ao executar as migracoes do banco de dados.
    exit /b 1
)
echo OK - Banco de dados atualizado.
echo.

REM --------------------------------------------------------------------
REM [6/8] Popula o catalogo inicial e pergunta se deseja criar um admin.
REM --------------------------------------------------------------------
echo [6/8] Populando catalogo inicial...
call "venv\Scripts\python.exe" manage.py seed_catalog
echo.

set /p CRIAR_ADMIN="Deseja criar um usuario administrador agora? [S/N]: "
if /i "%CRIAR_ADMIN%"=="S" (
    call "venv\Scripts\python.exe" manage.py createsuperuser
)
echo.

REM --------------------------------------------------------------------
REM [7/8] Gera uma SECRET_KEY aleatoria e grava no .env, caso ele ainda 
REM esteja com o valor inseguro padrao (ou vazio). Feito em Python (nao
REM inline no .bat) porque a chave tem caracteres especiais ($, &, !, %,
REM parenteses...) que o CMD interpretaria incorretamente.
REM --------------------------------------------------------------------
echo [7/8] Gerando SECRET_KEY...
call "venv\Scripts\python.exe" scripts\generate_secret_key.py
if errorlevel 1 (
    echo.
    echo AVISO: Nao foi possivel gerar a SECRET_KEY automaticamente.
    echo Gere uma manualmente com:
    echo   venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
    echo e cole o resultado em SECRET_KEY= no arquivo .env.
)
echo.

echo [8/8] Instalacao concluida!
echo.
echo ========================================
echo.

set /p INICIAR="Deseja iniciar o servidor agora? [S/N]: "
if /i "%INICIAR%"=="S" (
    echo.
    echo Servidor iniciado em:
    echo http://127.0.0.1:8000/
    echo.
    echo Pressione CTRL+C para encerrar o servidor.
    echo.
    call "venv\Scripts\python.exe" manage.py runserver
)

endlocal
