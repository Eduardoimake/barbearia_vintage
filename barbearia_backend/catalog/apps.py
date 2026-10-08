"""Configuração da aplicação Django responsável pelo catálogo."""

from __future__ import annotations

from django.apps import AppConfig


class CatalogConfig(AppConfig):
    """Configura a aplicação de catálogo da barbearia.

    Esta aplicação concentra os modelos, serializers, views, permissões,
    validadores, comandos administrativos e testes relacionados aos dados
    públicos e administrativos da Barbearia Vintage & Co.
    """

    default_auto_field: str = "django.db.models.AutoField"
    name: str = "catalog"
    verbose_name: str = "Catálogo da Barbearia"