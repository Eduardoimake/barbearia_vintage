"""Configuração ASGI para o projeto Barbearia Vintage & Co."""

from __future__ import annotations

import os

from django.core.asgi import get_asgi_application


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "barbearia_backend.settings",
)


application = get_asgi_application()