"""Gera uma SECRET_KEY aleatória e grava no arquivo .env.

Usado pelos instaladores automatizados (setup.bat / setup.sh), logo após
a criação do ambiente virtual, do .env e a instalação das dependências.

Fazemos essa etapa em Python (em vez de um comando inline no .bat/.sh)
porque a chave gerada contém caracteres especiais (`$`, `&`, `!`, `%`,
`(`, `)` etc.) que quebram ou são interpretados de formas diferentes pelo
CMD e pelo Bash — editar o arquivo aqui evita todo esse problema de
escaping entre shells.

É seguro reexecutar: se o .env já tiver uma SECRET_KEY própria (diferente
do valor inseguro de desenvolvimento usado como fallback em
config/settings.py), o script não mexe em nada.

Uso:
    python scripts/generate_secret_key.py
"""
 
from __future__ import annotations

import re
import sys
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

# Mesmo valor usado como fallback em config/settings.py quando SECRET_KEY
# não está definida. Se o .env ainda tiver isso (ou estiver vazio), é
# seguro — e desejável — substituir por uma chave gerada de verdade.
INSECURE_DEFAULT = "django-insecure-somente-para-desenvolvimento-local-troque-em-producao"

SECRET_KEY_LINE = re.compile(r"(?m)^SECRET_KEY=(.*)$")


def main() -> int:
    if not ENV_PATH.exists():
        print("Arquivo .env não encontrado; nada a fazer.")
        return 0

    content = ENV_PATH.read_text(encoding="utf-8")
    match = SECRET_KEY_LINE.search(content)
    valor_atual = match.group(1).strip() if match else ""

    if valor_atual and valor_atual != INSECURE_DEFAULT:
        print("SECRET_KEY já configurada no .env; mantendo o valor atual.")
        return 0

    # Importado aqui (não no topo do arquivo) porque este script roda antes
    # de qualquer coisa do projeto — só precisamos do Django já instalado
    # no ambiente virtual no momento em que o instalador chama este script.
    from django.core.management.utils import get_random_secret_key

    nova_chave = get_random_secret_key()
    nova_linha = f"SECRET_KEY={nova_chave}"

    if match:
        content = content[: match.start()] + nova_linha + content[match.end():]
    else:
        separador = "\n" if content and not content.endswith("\n") else ""
        content = f"{content}{separador}{nova_linha}\n"

    ENV_PATH.write_text(content, encoding="utf-8")
    print("SECRET_KEY gerada e salva no .env.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
