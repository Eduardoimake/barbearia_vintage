"""Configuração WSGI para o projeto Barbearia Vintage & Co."""

from __future__ import annotations

import os

from django.core.wsgi import get_wsgi_application


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "barbearia_backend.settings",
)


application = get_wsgi_application()