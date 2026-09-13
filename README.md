# VoxterFlix

Catálogo de filmes e séries com experiência inspirada em plataformas de streaming, desenvolvido como teste técnico de Desenvolvedor(a) Web Full Stack para a Voxter.

> **Aviso:** VoxterFlix é um projeto fictício, sem qualquer afiliação com a Netflix ou com os serviços de terceiros integrados (OMDb, SuperFlixAPI, Resend). A identidade visual usa uma paleta de cores inspirada na Voxter, mas não reproduz nenhum material oficial da marca.

## Sumário

- [VoxterFlix](#voxterflix)
  - [Sumário](#sumário)
  - [Sobre o projeto](#sobre-o-projeto)
  - [Tecnologias](#tecnologias)
  - [Requisitos](#requisitos)
  - [Executar](#executar)
  - [Instalação manual](#instalação-manual)
    - [Windows](#windows)
    - [Linux/macOS](#linuxmacos)
  - [Instalação automática](#instalação-automática)
    - [Windows](#windows-1)
    - [Linux/macOS](#linuxmacos-1)
  - [Ambiente virtual](#ambiente-virtual)
  - [Variáveis de ambiente](#variáveis-de-ambiente)
  - [OMDb](#omdb)
  - [Resend](#resend)
  - [SuperFlixAPI](#superflixapi)
  - [SQLite](#sqlite)
  - [PostgreSQL](#postgresql)
  - [Migrações](#migrações)
  - [Superusuário](#superusuário)
  - [Executar o projeto](#executar-o-projeto)
  - [Testes](#testes)
  - [Estrutura do projeto](#estrutura-do-projeto)
  - [Segurança](#segurança)
  - [Rate limiting](#rate-limiting)
  - [APIs externas](#apis-externas)
  - [E-mails](#e-mails)
  - [Decisões arquiteturais](#decisões-arquiteturais)
  - [Decisões técnicas](#decisões-técnicas)
  - [Limitações](#limitações)
  - [Licença](#licença)

## Sobre o projeto

VoxterFlix é uma plataforma de catálogo de filmes e séries: cadastro e login com confirmação de e-mail, múltiplos perfis por conta (incluindo perfil infantil com restrição de conteúdo), busca com filtros avançados, página de detalhes, lista de favoritos, histórico com "continuar assistindo" e um player de streaming. O catálogo é alimentado em tempo real pela OMDb API; o player usa a SuperFlixAPI; os e-mails transacionais são enviados via Resend.

O projeto foi construído para que qualquer pessoa com conhecimento básico de programação consiga clonar, configurar e rodar localmente em poucos minutos — sem Docker, sem Node.js e sem precisar instalar PostgreSQL (o banco padrão é o SQLite).

## Tecnologias

- Python 3.13+
- Django 6.x
- SQLite (desenvolvimento) / PostgreSQL (produção, opcional)
- Django Templates + Bootstrap 5 + Bootstrap Icons
- JavaScript moderno (sem framework de frontend)
- `requests` (integração HTTP com a OMDb)
- SDK oficial Python do Resend (e-mails transacionais)
- `django-environ` (variáveis de ambiente)
- Testes com `django.test.TestCase` (compatível com `pytest-django`, incluído no `requirements.txt`)

## Requisitos

- Python 3.13 ou superior
- pip
- Git

Não é necessário instalar PostgreSQL, Docker, Node.js ou Redis para rodar a versão padrão do projeto.

## Executar

Caso já tenha tudo instalado, apenas execute:

```bash
#se o ambiente virtual ainda não estiver ativado
venv\Scripts\activate


python manage.py runserver
```

## Instalação manual

### Windows

```bash
git clone <url-do-repositorio> voxterflix
cd voxterflix

python -m venv venv
venv\Scripts\activate

python -m pip install --upgrade pip
pip install -r requirements.txt

copy .env.example .env
python scripts\generate_secret_key.py

python manage.py migrate
python manage.py seed_catalog
python manage.py createsuperuser

python manage.py runserver
```

### Linux/macOS

```bash
git clone <url-do-repositorio> voxterflix
cd voxterflix

python3 -m venv venv
source venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env
python scripts/generate_secret_key.py

python manage.py migrate
python manage.py seed_catalog
python manage.py createsuperuser

python manage.py runserver
```

Depois de configurar o `.env` (veja [Variáveis de ambiente](#variáveis-de-ambiente)), acesse **http://127.0.0.1:8000/**.

## Instalação automática

Os scripts abaixo executam exatamente os mesmos passos da instalação manual, com verificações extras (Python instalado, reaproveitamento de `venv`/`.env`/banco existentes, mensagens de erro claras). Eles **não substituem** a instalação manual — ambas continuam funcionando e documentadas.

### Windows

```bash
setup.bat
```

O script:
1. Verifica se o Python está instalado e qual versão;
2. Cria o `venv` (ou reaproveita se já existir);
3. Instala as dependências;
4. Cria o `.env` a partir do `.env.example` (só se ainda não existir — nunca sobrescreve);
5. Executa as migrações;
6. Popula o catálogo inicial (`seed_catalog`) e pergunta se você quer criar um superusuário agora;
7. Gera uma `SECRET_KEY` aleatória e grava no `.env` — só quando ele ainda está com o valor padrão de desenvolvimento (nunca sobrescreve uma chave que você já tenha configurado);
8. Pergunta se você quer iniciar o servidor agora.

É seguro executar `setup.bat` mais de uma vez: ele nunca apaga `venv/`, `.env` ou `db.sqlite3` já existentes.

### Linux/macOS

```bash
chmod +x setup.sh
./setup.sh
```

O `setup.sh` segue exatamente os mesmos passos do `setup.bat`, adaptados para bash.

## Ambiente virtual

O ambiente virtual (`venv/`) isola as dependências Python deste projeto do restante do sistema. Ele nunca é versionado (está no `.gitignore`). Para reativá-lo em uma sessão futura do terminal:

```bash
# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

## Variáveis de ambiente

Todas as configurações sensíveis ficam em um arquivo `.env` (nunca versionado), criado a partir do `.env.example`:

| Variável | Descrição |
|---|---|
| `SECRET_KEY` | Chave secreta do Django. Gerada automaticamente por `scripts/generate_secret_key.py` (chamado tanto pela instalação manual quanto pelos scripts `setup.bat`/`setup.sh`) — só se ainda estiver vazia ou com o valor padrão de desenvolvimento. |
| `DEBUG` | `True` em desenvolvimento, `False` em produção. |
| `ALLOWED_HOSTS` | Hosts permitidos, separados por vírgula. |
| `DATABASE_URL` | String de conexão do banco (SQLite por padrão, PostgreSQL opcional). |
| `OMDB_API_KEY` | Chave da OMDb API (catálogo). |
| `OMDB_BASE_URL` | URL base da OMDb (raramente precisa mudar). |
| `OMDB_TIMEOUT` | Timeout (segundos) das requisições à OMDb. |
| `OMDB_CACHE_TTL` | Tempo (segundos) de cache das respostas da OMDb. |
| `SUPERFLIX_API_BASE_URL` | URL base da SuperFlixAPI (player). Sem ela, o player exibe uma mensagem informativa em vez de quebrar. |
| `RESEND_API_KEY` | Chave da API do Resend (e-mails). Sem ela, os e-mails são apenas registrados como "não enviados". |
| `RESEND_FROM_EMAIL` / `RESEND_FROM_NAME` | Remetente usado nos e-mails. |
| `MAX_PROFILES_PER_USER` | Limite de perfis por conta (padrão: 5). |
| `LOGIN_RATE_LIMIT` | Limite de tentativas de login, formato `N/Xm` (padrão: `3/15m`). |
| `SITE_URL` | URL pública do site (usada em links de e-mail). |

## OMDb

1. Crie uma chave gratuita em https://www.omdbapi.com/apikey.aspx (chega por e-mail).
2. Coloque a chave em `OMDB_API_KEY` no `.env`.

Sem essa chave, o catálogo, a busca e os detalhes não funcionam — a aplicação mostra uma mensagem explicando o problema em vez de quebrar.

## Resend

1. Crie uma conta em https://resend.com e gere uma API key.
2. Configure `RESEND_API_KEY`, `RESEND_FROM_EMAIL` e `RESEND_FROM_NAME` no `.env`.
3. Em contas gratuitas do Resend, o remetente geralmente precisa ser `onboarding@resend.dev` ou um domínio verificado por você.

Sem essa chave, a aplicação **não finge que enviou** o e-mail: ela registra a tentativa como "não enviada" em `apps.notifications.models.EmailLog` e segue funcionando normalmente (cadastro, recuperação de senha etc. continuam completando o fluxo).

## SuperFlixAPI

1. Obtenha a URL base do provedor da SuperFlixAPI que você for utilizar.
2. Configure `SUPERFLIX_API_BASE_URL` no `.env` (ex.: `https://exemplo-superflix.com`).

Sem essa variável, o player exibe a mensagem "O player ainda não está configurado neste ambiente" — o restante da aplicação (catálogo, busca, favoritos, histórico) continua funcionando normalmente.

## SQLite

Banco de dados padrão, usado automaticamente quando `DATABASE_URL=sqlite:///db.sqlite3`. Não exige nenhuma instalação — o arquivo `db.sqlite3` é criado na raiz do projeto pela própria aplicação. Ideal para desenvolvimento e para avaliar o projeto localmente.

## PostgreSQL

Opcional, recomendado para produção. Basta trocar a `DATABASE_URL` no `.env`:

```env
DATABASE_URL=postgresql://usuario:senha@localhost:5432/voxterflix
```

O projeto já inclui o driver `psycopg` no `requirements.txt` — não é necessário instalar mais nada além do próprio servidor PostgreSQL.

## Migrações

```bash
python manage.py makemigrations   # gerar novas migrações (após alterar models)
python manage.py migrate          # aplicar migrações pendentes
```

## Superusuário

```bash
python manage.py createsuperuser
```

Acesse a administração em **http://127.0.0.1:8000/admin/**.

## Executar o projeto

```bash
python manage.py runserver
```

Acesse **http://127.0.0.1:8000/**.

## Testes

```bash
python manage.py test tests
```

Os testes cobrem cadastro, login, rate limiting, confirmação de e-mail, perfis (criação/edição/exclusão/limite/infantil), favoritos (adicionar/remover/duplicidade/isolamento por perfil), catálogo (busca/detalhes/erros da OMDb) e streaming (validação de IMDb ID, autorização, indisponibilidade). Todas as chamadas a APIs externas são simuladas (`unittest.mock`) — os testes não fazem requisições reais à internet.

## Estrutura do projeto

```text
voxterflix/
├── manage.py
├── requirements.txt
├── setup.bat / setup.sh        # instalação automatizada
├── scripts/
│   └── generate_secret_key.py  # usado pela instalação manual e pelos setup.*
├── .env.example
│
├── config/                     # settings, urls, wsgi/asgi
│
├── apps/
│   ├── core/                   # utilitários compartilhados: rate limit,
│   │                           # log de segurança, context processor
│   ├── accounts/                # cadastro, login, confirmação de e-mail, senha
│   ├── profiles/                 # múltiplos perfis, perfil infantil
│   ├── catalog/                  # integração OMDb, busca, home, detalhes
│   │   └── services/omdb.py
│   ├── favorites/                # "Minha Lista"
│   ├── history/                  # histórico e "continuar assistindo"
│   ├── streaming/                # integração SuperFlixAPI e player
│   │   └── services/superflix.py
│   └── notifications/            # ResendEmailService e templates de e-mail
│
├── templates/                  # templates Django (um diretório por app)
├── static/css/ e static/js/    # CSS e JS organizados por responsabilidade
├── tests/                       # testes automatizados
└── media/, logs/                # gerados em tempo de execução (não versionados)
```

## Segurança

- **CSRF**: proteção padrão do Django ativa em todos os formulários.
- **XSS**: escaping automático dos templates Django; nenhum `|safe` é usado com dados de usuário.
- **SQL Injection**: todo acesso a dados usa o ORM do Django (sem SQL cru).
- **Clickjacking**: `X_FRAME_OPTIONS = "DENY"`.
- **Cookies**: `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SAMESITE=Lax`; `SESSION_COOKIE_SECURE`/`CSRF_COOKIE_SECURE` ativados automaticamente quando `DEBUG=False`.
- **HSTS/SSL redirect**: ativados automaticamente em produção (`DEBUG=False`), configuráveis via `.env`.
- **Segredos**: `SECRET_KEY`, chaves de API e credenciais de banco vêm sempre de variáveis de ambiente, nunca do código.
- **Senhas**: hashing via `django.contrib.auth` (PBKDF2), nunca texto puro.
- **Autorização**: perfis só acessam seus próprios favoritos/histórico; um usuário não ativa perfil de outro (`profiles.views.activate_profile` valida o dono); restrição de perfil infantil é sempre reforçada no backend.
- **Player**: nunca aceita URL arbitrária — apenas IMDb ID validado por regex (`^tt\d+$`), usado para montar a URL de embed no backend (mitiga SSRF, open redirect e proxy arbitrário).
- **Mensagens genéricas**: login sempre responde "Usuário ou senha inválidos.", sem revelar se a conta existe, está inativa ou a senha está errada.
- **Logs de segurança**: eventos de login, bloqueios, confirmação de e-mail e acesso ao player ficam em `logs/security.log`, sem nunca registrar senha, token ou API key.

Validação com `python manage.py check --deploy` (rodando com `DEBUG=False`): nenhum alerta pendente.

## Rate limiting

Implementado em `apps/core/security.py`, usando o cache do Django (LocMemCache em desenvolvimento — troque por um backend compartilhado como Redis se rodar múltiplos processos em produção).

| Ação | Limite padrão |
|---|---|
| Login | `LOGIN_RATE_LIMIT` no `.env` (padrão `3/15m`), contando apenas tentativas **falhas** |
| Cadastro | 5 por hora, por IP |
| Recuperação de senha | 3 por hora, por IP |
| Busca no catálogo | 30 por minuto, por usuário |
| Endpoints do player | 60 por minuto, por usuário |

Ao exceder o limite, a resposta é sempre genérica (nunca revela detalhes internos) e o evento é registrado em `logs/security.log`.

## APIs externas

- **OMDb** (`apps/catalog/services/omdb.py`): busca (`s=`) e detalhes (`i=`) de filmes/séries. Trata timeout, erro HTTP, limite de requisições e "não encontrado" separadamente. Respostas de sucesso são cacheadas (`OMDB_CACHE_TTL`).
- **SuperFlixAPI** (`apps/streaming/services/superflix.py`): monta a URL de embed do player (`/filme/{imdb_id}` ou `/serie/{imdb_id}/{temporada}/{episodio}`), com validação estrita de entrada. Nunca proxeia ou faz chamadas arbitrárias.
- **Resend** (`apps/notifications/services.py`): envio de e-mails transacionais via SDK oficial, com idempotência (`idempotency_key`) para confirmação/boas-vindas e registro de auditoria em `EmailLog`.

## E-mails

Quatro e-mails transacionais, todos com o layout visual do VoxterFlix (`templates/notifications/email/`):

1. **Confirmação de cadastro** — link de ativação da conta.
2. **Boas-vindas** — enviado após a confirmação do e-mail.
3. **Recuperação de senha** — reaproveita o gerador de token oficial do Django (`PasswordResetTokenGenerator`); só o transporte do e-mail é o Resend.
4. **Senha alterada** — aviso de segurança após troca de senha (por recuperação ou pela tela de conta).

## Decisões arquiteturais

- **Django Templates em vez de SPA**: o teste técnico pede uma aplicação simples de instalar e rodar; um frontend separado (React/Vue) exigiria Node.js e um segundo processo de build, contrariando o requisito de "mínimo de dependências externas".
- **Services isolando APIs externas**: `OMDbService`, `SuperFlixService` e `ResendEmailService` são os únicos pontos do código que conhecem a API de cada provedor. Views nunca fazem `requests.get`/chamadas diretas — isso facilita testar (mock de uma classe) e trocar de provedor no futuro.
- **Favoritos e histórico por Perfil, não por User**: replica a experiência real de plataformas de streaming (cada perfil de uma conta tem sua própria lista e histórico).
- **Curadoria própria para a Home** (`apps.catalog.models.Category`/`CuratedTitle`): a OMDb não tem endpoint de "em alta" ou "por gênero" — só busca por título/ID. A Home usa uma lista própria de IDs do IMDb por categoria (comando `seed_catalog`), sempre buscando os dados reais (poster, nota, sinopse) na OMDb, nunca inventados.

## Decisões técnicas

- **`django-environ`** para variáveis de ambiente: parsing de tipos (bool, int, lista) e suporte nativo a `DATABASE_URL` (SQLite/PostgreSQL) sem código extra.
- **Rate limiting via cache do Django** em vez de uma biblioteca externa: o volume do projeto não justifica uma dependência a mais; a lógica cabe em ~30 linhas e é facilmente substituível por Redis trocando só o `CACHES["default"]["BACKEND"]`.
- **Token de confirmação de e-mail sem tabela própria**: `EmailConfirmationTokenGenerator` reaproveita o mesmo mecanismo assinado (`PasswordResetTokenGenerator`) que o Django já usa para recuperação de senha, incluindo `is_active` no hash para invalidar o link automaticamente após o primeiro uso.
- **Bootstrap via CDN**: evita precisar de Node.js/bundler para um projeto que não tem CSS customizado o suficiente para justificar isso.

## Limitações

- **Filtros avançados de busca** (gênero, ator, diretor, país, idioma, nota, ano) não são suportados nativamente pela OMDb — ela só filtra por `type` e `y` (ano exato). Por isso, ao usar esses filtros, o VoxterFlix busca por título e refina os primeiros resultados no backend (buscando o detalhe de cada um), o que é mais lento e limitado às primeiras posições da busca. Isso está documentado na própria tela de busca quando filtros avançados estão ativos.
- **Progresso do player é uma estimativa**: o player roda em um `<iframe>` de outro domínio (SuperFlixAPI) e não existe um mecanismo documentado (`postMessage` etc.) para ler o tempo real de reprodução de dentro dele. O progresso salvo em "Continuar assistindo" é calculado pelo tempo decorrido desde que o player carregou, comparado à duração informada pela OMDb — não detecta pausas ou avanços manuais dentro do player de terceiros.
- **Trailer**: a OMDb não fornece links de trailer, então a página de detalhes não exibe um (em vez de simular ou usar uma fonte não confirmada).
- **SuperFlixAPI**: a URL base já mudou de domínio algumas vezes historicamente (aggregators desse tipo trocam de TLD com frequência); por isso ela é 100% configurável via `.env` e nunca hardcoded. Se a URL configurada ficar fora do ar, o player informa isso claramente em vez de travar a aplicação.
- **Cache em memória (`LocMemCache`)**: adequado para um único processo (desenvolvimento/avaliação). Rodar múltiplos workers em produção exigiria um cache compartilhado (Redis), trocando apenas a configuração — o código não precisaria mudar.

## Licença

Distribuído sob a licença MIT — veja [LICENSE](LICENSE).
