"""Rotas principais do projeto Barbearia Vintage & Co."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from .health import health_check


urlpatterns: list[Any] = [
    path("health/", health_check, name="health"),
    path("django-admin/", admin.site.urls),
    path("api/v1/", include("catalog.urls")),
]


# Mídia servida pelo Django somente quando o armazenamento é local
# (desenvolvimento ou Persistent Disk). Com S3, a URL já é externa.
if settings.MEDIA_SERVE_LOCAL:
    urlpatterns += [
        re_path(
            r"^media/(?P<path>.*)$",
            serve,
            {"document_root": settings.MEDIA_ROOT},
        ),
    ]