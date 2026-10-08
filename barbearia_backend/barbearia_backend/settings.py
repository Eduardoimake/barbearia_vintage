"""Configurações principais do projeto Barbearia Vintage & Co.

Este módulo centraliza as configurações do Django, do Django REST Framework,
do banco de dados, dos cookies, do CSRF, do CORS, dos arquivos estáticos
e do armazenamento de mídia.

Toda configuração sensível vem de variáveis de ambiente. Nenhuma senha,
chave privada ou credencial é gravada neste arquivo.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv


BASE_DIR: Path = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def get_env(name: str, default: str = "") -> str:
    """Obtém uma variável de ambiente como texto."""
    return os.getenv(name, default).strip()


def get_bool_env(name: str, default: bool = False) -> bool:
    """Converte uma variável de ambiente para booleano."""
    raw_value: str = get_env(name, "true" if default else "false").lower()
    return raw_value in {"1", "true", "t", "yes", "y", "on"}


def get_int_env(name: str, default: int) -> int:
    """Converte uma variável de ambiente para inteiro."""
    raw_value: str = get_env(name, str(default))

    try:
        return int(raw_value)
    except ValueError:
        return default


def get_list_env(name: str, default: list[str] | None = None) -> list[str]:
    """Obtém uma lista separada por vírgulas a partir de uma variável."""
    fallback: list[str] = default or []
    raw_value: str = get_env(name)

    if not raw_value:
        return fallback

    return [
        item.strip()
        for item in raw_value.split(",")
        if item.strip()
    ]


# O Render define RENDER=true automaticamente em todos os serviços.
IS_RENDER: bool = get_bool_env("RENDER", default=False)

# Padrão seguro: fora do Render continua True (desenvolvimento local);
# no Render o padrão é False, mesmo que a variável DEBUG seja esquecida.
DEBUG: bool = get_bool_env("DEBUG", default=not IS_RENDER)

_INSECURE_DEV_KEY: str = "chave-insegura-apenas-para-desenvolvimento-local"

SECRET_KEY: str = get_env("SECRET_KEY", default=_INSECURE_DEV_KEY)

if not DEBUG and SECRET_KEY in {"", _INSECURE_DEV_KEY}:
    raise ImproperlyConfigured(
        "Defina a variável de ambiente SECRET_KEY em produção (DEBUG=false)."
    )

ALLOWED_HOSTS: list[str] = get_list_env(
    "ALLOWED_HOSTS",
    default=["localhost", "127.0.0.1"],
)

# O Render informa o host público do serviço; ele é aceito automaticamente.
_render_host: str = get_env("RENDER_EXTERNAL_HOSTNAME")
if _render_host and _render_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_render_host)


INSTALLED_APPS: list[str] = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "catalog",
]


MIDDLEWARE: list[str] = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF: str = "barbearia_backend.urls"


TEMPLATES: list[dict[str, Any]] = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


WSGI_APPLICATION: str = "barbearia_backend.wsgi.application"
ASGI_APPLICATION: str = "barbearia_backend.asgi.application"


# Banco de dados. Prioridade:
# 1) DATABASE_URL (Render/PostgreSQL); 2) DB_ENGINE=postgresql com DB_*;
# 3) SQLite local (padrão).
DB_ENGINE: str = get_env("DB_ENGINE", default="sqlite").lower()
DB_CONN_MAX_AGE: int = get_int_env("DB_CONN_MAX_AGE", default=60)
DATABASE_URL: str = get_env("DATABASE_URL")

if DATABASE_URL:
    DATABASES: dict[str, dict[str, Any]] = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=DB_CONN_MAX_AGE,
            conn_health_checks=True,
        )
    }
elif DB_ENGINE == "postgresql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": get_env("DB_DATABASE", default="barbearia_db"),
            "USER": get_env("DB_USER", default="barbearia_user"),
            "PASSWORD": get_env("DB_PASSWORD"),
            "HOST": get_env("DB_HOST", default="localhost"),
            "PORT": get_env("DB_PORT", default="5432"),
            "CONN_MAX_AGE": DB_CONN_MAX_AGE,
        }
    }
else:
    sqlite_name: str = get_env("DB_NAME", default="db.sqlite3")
    sqlite_path: Path = BASE_DIR / sqlite_name

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": sqlite_path,
        }
    }


AUTH_PASSWORD_VALIDATORS: list[dict[str, str]] = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


LANGUAGE_CODE: str = "pt-br"
TIME_ZONE: str = get_env("TIME_ZONE", default="America/Sao_Paulo")
USE_I18N: bool = True
USE_TZ: bool = True


STATIC_URL: str = "/static/"
STATIC_ROOT: Path = BASE_DIR / get_env(
    "STATIC_ROOT",
    default="staticfiles",
)
STATICFILES_DIRS: list[Path] = []

MEDIA_URL: str = "/media/"
MEDIA_ROOT: Path = BASE_DIR / get_env(
    "MEDIA_ROOT",
    default="media",
)


# Armazenamento: estáticos (WhiteNoise) e mídia (local ou S3 compatível).
MEDIA_STORAGE: str = get_env("MEDIA_STORAGE", default="local").lower()

if MEDIA_STORAGE not in {"local", "s3"}:
    raise ImproperlyConfigured("MEDIA_STORAGE deve ser 'local' ou 's3'.")

STORAGES: dict[str, dict[str, Any]] = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}

if MEDIA_STORAGE == "s3":
    _s3_required: tuple[str, ...] = (
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_STORAGE_BUCKET_NAME",
    )
    _s3_missing: list[str] = [n for n in _s3_required if not get_env(n)]

    if _s3_missing:
        raise ImproperlyConfigured(
            "MEDIA_STORAGE=s3 exige as variáveis: " + ", ".join(_s3_missing)
        )

    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "access_key": get_env("AWS_ACCESS_KEY_ID"),
            "secret_key": get_env("AWS_SECRET_ACCESS_KEY"),
            "bucket_name": get_env("AWS_STORAGE_BUCKET_NAME"),
            "endpoint_url": get_env("AWS_S3_ENDPOINT_URL") or None,
            "region_name": get_env("AWS_S3_REGION_NAME") or None,
            "custom_domain": get_env("AWS_S3_CUSTOM_DOMAIN") or None,
            "signature_version": "s3v4",
            "default_acl": None,
            "querystring_auth": False,
            "file_overwrite": False,
            "object_parameters": {
                "CacheControl": "public, max-age=31536000",
            },
        },
    }
elif not DEBUG and not MEDIA_ROOT.is_absolute():
    raise ImproperlyConfigured(
        "Em produção com MEDIA_STORAGE=local, MEDIA_ROOT deve ser o caminho "
        "absoluto de um Persistent Disk (ex.: /var/data/media). "
        "Disco efêmero perde os uploads a cada deploy."
    )

# Em modo local fora do DEBUG (Persistent Disk), o Django serve /media/.
MEDIA_SERVE_LOCAL: bool = MEDIA_STORAGE == "local"


DEFAULT_AUTO_FIELD: str = "django.db.models.AutoField"


REST_FRAMEWORK: dict[str, Any] = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
    "EXCEPTION_HANDLER": "catalog.views.api_exception_handler",
}


DEFAULT_PAGE_SIZE: int = max(get_int_env("DEFAULT_PAGE_SIZE", default=12), 1)
MAX_PAGE_SIZE: int = max(
    get_int_env("MAX_PAGE_SIZE", default=50),
    DEFAULT_PAGE_SIZE,
)


CORS_ALLOWED_ORIGINS: list[str] = get_list_env(
    "CORS_ALLOWED_ORIGINS",
    default=[],
)
CORS_ALLOW_CREDENTIALS: bool = True

CSRF_TRUSTED_ORIGINS: list[str] = get_list_env(
    "CSRF_TRUSTED_ORIGINS",
    default=[],
)

# Com credenciais, CORS aberto é proibido; em produção só origens HTTPS.
if "*" in CORS_ALLOWED_ORIGINS:
    raise ImproperlyConfigured(
        "CORS_ALLOWED_ORIGINS não pode conter '*' com "
        "CORS_ALLOW_CREDENTIALS=True."
    )

if not DEBUG:
    _origens_invalidas: list[str] = [
        origem
        for origem in CORS_ALLOWED_ORIGINS + CSRF_TRUSTED_ORIGINS
        if not origem.startswith("https://") or origem.endswith("/")
    ]
    if _origens_invalidas:
        raise ImproperlyConfigured(
            "Em produção, use origens https:// sem barra final em "
            "CORS_ALLOWED_ORIGINS e CSRF_TRUSTED_ORIGINS. Inválidas: "
            + ", ".join(_origens_invalidas)
        )


# Cookies: em produção, frontend e backend ficam em origens diferentes,
# então é necessário SameSite=None + Secure. Em desenvolvimento, Lax.
_default_samesite: str = "Lax" if DEBUG else "None"

SESSION_COOKIE_SECURE: bool = get_bool_env("SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE: bool = get_bool_env("CSRF_COOKIE_SECURE", default=False)

SESSION_COOKIE_HTTPONLY: bool = True
CSRF_COOKIE_HTTPONLY: bool = False

SESSION_COOKIE_SAMESITE: str = get_env("SESSION_COOKIE_SAMESITE", default=_default_samesite)
CSRF_COOKIE_SAMESITE: str = get_env("CSRF_COOKIE_SAMESITE", default=_default_samesite)


SECURE_SSL_REDIRECT: bool = get_bool_env("SECURE_SSL_REDIRECT", default=False)

# O health check do Render não deve ser redirecionado.
SECURE_REDIRECT_EXEMPT: list[str] = [r"^health/$"]

SECURE_PROXY_SSL_HEADER: tuple[str, str] | None = None

if get_bool_env("USE_PROXY_SSL_HEADER", default=IS_RENDER):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


SECURE_HSTS_SECONDS: int = get_int_env("SECURE_HSTS_SECONDS", default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS: bool = get_bool_env("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False)
SECURE_HSTS_PRELOAD: bool = get_bool_env("SECURE_HSTS_PRELOAD", default=False)

SECURE_CONTENT_TYPE_NOSNIFF: bool = True
X_FRAME_OPTIONS: str = "DENY"
SECURE_REFERRER_POLICY: str = "same-origin"


MAX_UPLOAD_SIZE: int = max(
    get_int_env("MAX_UPLOAD_SIZE", default=5 * 1024 * 1024),
    1,
)

ALLOWED_IMAGE_EXTENSIONS: tuple[str, ...] = tuple(
    extension.lower().lstrip(".")
    for extension in get_list_env(
        "ALLOWED_IMAGE_EXTENSIONS",
        default=["jpg", "jpeg", "png", "webp"],
    )
)


SITE_URL: str = get_env("SITE_URL", default="http://localhost:8000")


DATA_UPLOAD_MAX_MEMORY_SIZE: int = MAX_UPLOAD_SIZE
FILE_UPLOAD_MAX_MEMORY_SIZE: int = MAX_UPLOAD_SIZE


if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True