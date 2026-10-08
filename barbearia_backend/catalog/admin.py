"""Configuração do Django Admin para a Barbearia Vintage & Co.

O Django Admin é uma ferramenta auxiliar de desenvolvimento e configuração
inicial. Ele não substitui o painel administrativo personalizado, que deve
consumir a API REST em ``/api/v1/admin/``.
"""

from __future__ import annotations

from typing import Any

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db.models import Count, QuerySet
from django.http import HttpRequest

from .models import (
    Barber,
    Promotion,
    Service,
    ServiceCategory,
    StoreConfiguration,
)


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    """Administração das categorias de serviço."""

    list_display: tuple[str, ...] = (
        "name",
        "slug",
        "is_active",
        "display_order",
        "service_count",
        "updated_at",
    )

    list_filter: tuple[str, ...] = (
        "is_active",
    )

    search_fields: tuple[str, ...] = (
        "name",
        "slug",
        "short_description",
    )

    ordering: tuple[str, ...] = (
        "display_order",
        "name",
    )

    readonly_fields: tuple[str, ...] = (
        "created_at",
        "updated_at",
    )

    fieldsets: tuple[tuple[str | None, dict[str, Any]], ...] = (
        (
            None,
            {
                "fields": (
                    "name",
                    "slug",
                    "short_description",
                )
            },
        ),
        (
            "Exibição e publicação",
            {
                "fields": (
                    "display_order",
                    "is_active",
                )
            },
        ),
        (
            "Registro",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(
        description="Serviços vinculados",
    )
    def service_count(
        self,
        obj: ServiceCategory,
    ) -> int:
        """Retorna a quantidade de serviços vinculados à categoria.

        Args:
            obj: Categoria exibida na listagem.

        Returns:
            Quantidade de serviços relacionados.
        """
        return obj.service_count

    def get_queryset(
        self,
        request: HttpRequest,
    ) -> QuerySet[ServiceCategory]:
        """Otimiza a listagem de categorias.

        Args:
            request: Requisição atual do Django Admin.

        Returns:
            QuerySet com contagem otimizada de serviços.
        """
        return (
            super()
            .get_queryset(request)
            .annotate(
                service_count=Count("services", distinct=True),
            )
        )


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Administração dos serviços do catálogo."""

    list_display: tuple[str, ...] = (
        "name",
        "category",
        "price",
        "duration_minutes",
        "is_featured",
        "is_published",
        "display_order",
        "updated_at",
    )

    list_filter: tuple[str, ...] = (
        "category",
        "is_featured",
        "is_published",
    )

    search_fields: tuple[str, ...] = (
        "name",
        "slug",
        "short_description",
        "full_description",
    )

    ordering: tuple[str, ...] = (
        "display_order",
        "name",
    )

    readonly_fields: tuple[str, ...] = (
        "created_at",
        "updated_at",
    )

    autocomplete_fields: tuple[str, ...] = (
        "category",
    )

    list_select_related: tuple[str, ...] = (
        "category",
    )

    fieldsets: tuple[tuple[str | None, dict[str, Any]], ...] = (
        (
            "Informações principais",
            {
                "fields": (
                    "category",
                    "name",
                    "slug",
                    "short_description",
                    "full_description",
                )
            },
        ),
        (
            "Preço e duração",
            {
                "fields": (
                    "price",
                    "duration_minutes",
                )
            },
        ),
        (
            "Imagem",
            {
                "fields": (
                    "main_image",
                    "alt_text",
                )
            },
        ),
        (
            "Publicação e exibição",
            {
                "fields": (
                    "is_featured",
                    "is_published",
                    "display_order",
                )
            },
        ),
        (
            "Registro",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(Barber)
class BarberAdmin(admin.ModelAdmin):
    """Administração dos barbeiros do catálogo."""

    list_display: tuple[str, ...] = (
        "name",
        "specialty",
        "is_active",
        "display_order",
        "updated_at",
    )

    list_filter: tuple[str, ...] = (
        "is_active",
    )

    search_fields: tuple[str, ...] = (
        "name",
        "slug",
        "specialty",
        "short_description",
    )

    ordering: tuple[str, ...] = (
        "display_order",
        "name",
    )

    readonly_fields: tuple[str, ...] = (
        "created_at",
        "updated_at",
    )

    fieldsets: tuple[tuple[str | None, dict[str, Any]], ...] = (
        (
            "Informações principais",
            {
                "fields": (
                    "name",
                    "slug",
                    "specialty",
                    "short_description",
                )
            },
        ),
        (
            "Foto",
            {
                "fields": (
                    "main_photo",
                    "alt_text",
                )
            },
        ),
        (
            "Exibição",
            {
                "fields": (
                    "display_order",
                    "is_active",
                )
            },
        ),
        (
            "Registro",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(StoreConfiguration)
class StoreConfigurationAdmin(admin.ModelAdmin):
    """Administração da configuração única da barbearia."""

    list_display: tuple[str, ...] = (
        "name",
        "whatsapp_number",
        "updated_at",
    )

    search_fields: tuple[str, ...] = (
        "name",
        "slogan",
        "whatsapp_number",
    )

    readonly_fields: tuple[str, ...] = (
        "id",
        "created_at",
        "updated_at",
    )

    fieldsets: tuple[tuple[str | None, dict[str, Any]], ...] = (
        (
            "Identificação",
            {
                "fields": (
                    "id",
                    "name",
                    "slogan",
                    "presentation_description",
                )
            },
        ),
        (
            "Contato e informações",
            {
                "fields": (
                    "whatsapp_number",
                    "demo_address",
                    "opening_hours",
                )
            },
        ),
        (
            "Banner inicial",
            {
                "fields": (
                    "banner_image",
                    "banner_text",
                    "primary_button_text",
                )
            },
        ),
        (
            "Registro",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def has_add_permission(
        self,
        request: HttpRequest,
    ) -> bool:
        """Impede a criação de uma segunda configuração.

        Args:
            request: Requisição atual do Django Admin.

        Returns:
            ``True`` somente quando ainda não existe configuração.
        """
        return not StoreConfiguration.objects.exists()

    def has_delete_permission(
        self,
        request: HttpRequest,
        obj: StoreConfiguration | None = None,
    ) -> bool:
        """Impede a exclusão da configuração singleton.

        Args:
            request: Requisição atual do Django Admin.
            obj: Configuração selecionada, quando aplicável.

        Returns:
            Sempre ``False``.
        """
        del request
        del obj

        return False


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    """Administração das promoções e destaques promocionais."""

    list_display: tuple[str, ...] = (
        "title",
        "linked_service",
        "is_active",
        "start_date",
        "end_date",
        "display_order",
        "updated_at",
    )

    list_filter: tuple[str, ...] = (
        "is_active",
        "linked_service",
    )

    search_fields: tuple[str, ...] = (
        "title",
        "description",
    )

    ordering: tuple[str, ...] = (
        "display_order",
        "title",
    )

    readonly_fields: tuple[str, ...] = (
        "created_at",
        "updated_at",
    )

    autocomplete_fields: tuple[str, ...] = (
        "linked_service",
    )

    list_select_related: tuple[str, ...] = (
        "linked_service",
    )

    fieldsets: tuple[tuple[str | None, dict[str, Any]], ...] = (
        (
            "Informações principais",
            {
                "fields": (
                    "title",
                    "description",
                )
            },
        ),
        (
            "Imagem e serviço",
            {
                "fields": (
                    "image",
                    "linked_service",
                )
            },
        ),
        (
            "Período e exibição",
            {
                "fields": (
                    "start_date",
                    "end_date",
                    "is_active",
                    "display_order",
                )
            },
        ),
        (
            "Registro",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )