"""
Configurações do projeto VoxterFlix.

Todas as informações sensíveis (chaves, credenciais, hosts permitidos)
vêm de variáveis de ambiente, nunca ficam hardcoded no código-fonte.
Isso permite que o mesmo código funcione em desenvolvimento (SQLite)
e em produção (PostgreSQL) apenas trocando o arquivo `.env`.
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# django-environ lê o arquivo .env e expõe as variáveis com conversão de tipo
# (env.bool, env.int, env.list, env.db etc.), evitando parsing manual.
env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")

# --------------------------------------------------------------------------
# Segurança básica
# --------------------------------------------------------------------------

# A SECRET_KEY nunca deve ser versionada. Em desenvolvimento, se ausente,
# geramos um valor previsível apenas para não travar o `runserver` local;
# em produção, o ideal é sempre definir SECRET_KEY no .env.
SECRET_KEY = env.str(
    "SECRET_KEY",
    default="django-insecure-somente-para-desenvolvimento-local-troque-em-producao",
)

DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])

# --------------------------------------------------------------------------
# Aplicações instaladas
# --------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Apps do domínio VoxterFlix. Cada app tem uma responsabilidade única
    # (Single Responsibility) e é isolado dos demais por serviços próprios.
    "apps.core",
    "apps.accounts",
    "apps.profiles",
    "apps.catalog",
    "apps.favorites",
    "apps.history",
    "apps.streaming",
    "apps.notifications",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Middleware próprio: garante que exista um perfil ativo na sessão
    # para as views que dependem de "qual perfil está assistindo".
    "apps.profiles.middleware.ActiveProfileMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Expõe o perfil ativo e configurações públicas em todos os templates.
                "apps.core.context_processors.voxterflix_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --------------------------------------------------------------------------
# Banco de dados
# --------------------------------------------------------------------------
# django-environ interpreta a DATABASE_URL e escolhe o backend automaticamente:
# sqlite:///db.sqlite3            -> desenvolvimento (padrão, sem dependências)
# postgresql://user:pass@host/db  -> produção (opcional)
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --------------------------------------------------------------------------
# Internacionalização
# --------------------------------------------------------------------------

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------
# Arquivos estáticos e de mídia
# --------------------------------------------------------------------------

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------------------------------
# Autenticação
# --------------------------------------------------------------------------

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "profiles:selecionar"
LOGOUT_REDIRECT_URL = "accounts:login"

# --------------------------------------------------------------------------
# Cache
# --------------------------------------------------------------------------
# LocMemCache é suficiente para desenvolvimento e para o volume de um teste
# técnico. Em produção com múltiplos processos, o ideal seria um cache
# compartilhado (ex.: Redis), mas isso não é exigido para este projeto.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "voxterflix-cache",
    }
}

# TTL (em segundos) do cache de respostas da OMDb.
OMDB_CACHE_TTL = env.int("OMDB_CACHE_TTL", default=60 * 60 * 6)  # 6 horas

# --------------------------------------------------------------------------
# Integrações externas (as chaves nunca ficam hardcoded — vêm do .env)
# --------------------------------------------------------------------------

OMDB_API_KEY = env.str("OMDB_API_KEY", default="")
OMDB_BASE_URL = env.str("OMDB_BASE_URL", default="https://www.omdbapi.com/")
OMDB_TIMEOUT = env.int("OMDB_TIMEOUT", default=10)

SUPERFLIX_API_BASE_URL = env.str("SUPERFLIX_API_BASE_URL", default="")
SUPERFLIX_TIMEOUT = env.int("SUPERFLIX_TIMEOUT", default=10)

RESEND_API_KEY = env.str("RESEND_API_KEY", default="")
RESEND_FROM_EMAIL = env.str("RESEND_FROM_EMAIL", default="onboarding@resend.dev")
RESEND_FROM_NAME = env.str("RESEND_FROM_NAME", default="VoxterFlix")

# --------------------------------------------------------------------------
# Regras de negócio configuráveis
# --------------------------------------------------------------------------

MAX_PROFILES_PER_USER = env.int("MAX_PROFILES_PER_USER", default=5)

# Formato "N/Xm" -> N tentativas falhas permitidas por janela de X minutos.
LOGIN_RATE_LIMIT = env.str("LOGIN_RATE_LIMIT", default="3/15m")

SITE_NAME = "VoxterFlix"
SITE_URL = env.str("SITE_URL", default="http://127.0.0.1:8000")

# --------------------------------------------------------------------------
# Segurança de produção
# --------------------------------------------------------------------------
# Esses cabeçalhos/flags só fazem sentido com HTTPS configurado. Ativá-los
# em desenvolvimento (HTTP puro) impediria o acesso via runserver, por isso
# ficam condicionados a DEBUG=False.
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

if not DEBUG:
    SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=True)
    CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=True)
    SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
    SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=60 * 60 * 24 * 30)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_SSL_REDIRECT = False
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False

# --------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------
# Logs de segurança (tentativas de login, bloqueios por rate limit, eventos
# de autenticação) ficam separados dos logs gerais da aplicação, e nunca
# recebem senha, token ou chave de API — apenas metadados do evento.
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "app_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "application.log",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 3,
            "formatter": "verbose",
        },
        "security_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "security.log",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 3,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "app_file"],
            "level": "INFO",
            "propagate": False,
        },
        "voxterflix": {
            "handlers": ["console", "app_file"],
            "level": "INFO",
            "propagate": False,
        },
        "voxterflix.security": {
            "handlers": ["console", "security_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
