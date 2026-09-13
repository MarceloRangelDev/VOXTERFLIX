#!/usr/bin/env bash
# ==========================================================================
# VoxterFlix - instalador automatizado para Linux/macOS
#
# Seguro para executar mais de uma vez: reaproveita o ambiente virtual, o
# banco de dados e o .env caso ja existam, em vez de apagar/sobrescrever.
#
# Uso:
#   chmod +x setup.sh
#   ./setup.sh
# ==========================================================================

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

echo "========================================"
echo "        VOXTERFLIX - INSTALADOR"
echo "========================================"
echo

# --------------------------------------------------------------------
# [1/8] Verifica se o Python 3 esta instalado. Se nao estiver, exibe instrucoes de instalacao e encerra.
# --------------------------------------------------------------------
echo "[1/8] Verificando Python..."
if ! command -v python3 >/dev/null 2>&1; then
    echo
    echo "ERRO: Python 3 nao foi encontrado."
    echo
    echo "Instale o Python 3.13 ou superior (https://www.python.org/downloads/)"
    echo "e tente novamente."
    exit 1
fi
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "OK - Python ${PYTHON_VERSION} encontrado."
echo

# --------------------------------------------------------------------
# [2/8] Cria o ambiente virtual somente se ele ainda nao existir.
# --------------------------------------------------------------------
echo "[2/8] Preparando ambiente virtual..."
if [ -f "venv/bin/python" ]; then
    echo "Ambiente virtual ja existe. Reutilizando..."
else
    python3 -m venv venv
    echo "OK - Ambiente virtual criado."
fi
echo

# --------------------------------------------------------------------
# [3/8] Atualiza o pip e instala as dependencias do requirements.txt.
# --------------------------------------------------------------------
echo "[3/8] Instalando dependencias..."
"venv/bin/python" -m pip install --upgrade pip --quiet
"venv/bin/pip" install -r requirements.txt --quiet
echo "OK - Dependencias instaladas."
echo

# --------------------------------------------------------------------
# [4/8] Cria o .env a partir do .env.example, sem nunca sobrescrever um
# .env que ja exista.
# --------------------------------------------------------------------
echo "[4/8] Configurando ambiente..."
if [ -f ".env" ]; then
    echo ".env ja existe. Mantendo configuracao atual..."
else
    cp ".env.example" ".env"
    echo ".env criado a partir de .env.example."
    echo "IMPORTANTE: edite o arquivo .env e configure OMDB_API_KEY, RESEND_API_KEY"
    echo "e SUPERFLIX_API_BASE_URL conforme necessario."
fi
echo

# --------------------------------------------------------------------
# [5/8] Executa as migracoes (idempotente).
# --------------------------------------------------------------------
echo "[5/8] Executando migracoes..."
"venv/bin/python" manage.py migrate
echo "OK - Banco de dados atualizado."
echo

# --------------------------------------------------------------------
# [6/8] Popula o catalogo inicial e pergunta se deseja criar um admin.
# --------------------------------------------------------------------
echo "[6/8] Populando catalogo inicial..."
"venv/bin/python" manage.py seed_catalog
echo

read -r -p "Deseja criar um usuario administrador agora? [s/N]: " CRIAR_ADMIN
if [[ "${CRIAR_ADMIN}" =~ ^[Ss]$ ]]; then
    "venv/bin/python" manage.py createsuperuser
fi
echo

# --------------------------------------------------------------------
# [7/8] Gera uma SECRET_KEY aleatoria e grava no .env, caso ele ainda
# esteja com o valor inseguro padrao (ou vazio). Feito em Python (nao
# inline no shell) porque a chave tem caracteres especiais ($, &, !,
# parenteses...) que o Bash poderia interpretar incorretamente.
# --------------------------------------------------------------------
echo "[7/8] Gerando SECRET_KEY..."
if ! "venv/bin/python" scripts/generate_secret_key.py; then
    echo
    echo "AVISO: Nao foi possivel gerar a SECRET_KEY automaticamente."
    echo "Gere uma manualmente com:"
    echo '  venv/bin/python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"'
    echo "e cole o resultado em SECRET_KEY= no arquivo .env."
fi
echo

echo "[8/8] Instalacao concluida!"
echo
echo "========================================"
echo

read -r -p "Deseja iniciar o servidor agora? [s/N]: " INICIAR
if [[ "${INICIAR}" =~ ^[Ss]$ ]]; then
    echo
    echo "Servidor iniciado em:"
    echo "http://127.0.0.1:8000/"
    echo
    echo "Pressione CTRL+C para encerrar o servidor."
    echo
    "venv/bin/python" manage.py runserver
fi
