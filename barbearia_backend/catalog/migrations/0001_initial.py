"""Migração inicial dos modelos da Barbearia Vintage & Co.

Esta migração cria as tabelas de categorias, serviços, barbeiros,
configuração única da barbearia e promoções.

Ela também cria os índices utilizados pelas consultas públicas e as
restrições de integridade definidas nos modelos.
"""

from __future__ import annotations

from decimal import Decimal

import catalog.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """Primeira migração da aplicação ``catalog``."""

    initial: bool = True

    dependencies: list[tuple[str, str]] = []

    operations: list[migrations.Operation] = [
        migrations.CreateModel(
            name="ServiceCategory",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        max_length=100,
                        verbose_name="nome",
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        max_length=100,
                        unique=True,
                        verbose_name="slug",
                    ),
                ),
                (
                    "short_description",
                    models.TextField(
                        blank=True,
                        default="",
                        verbose_name="descrição curta",
                    ),
                ),
                (
                    "display_order",
                    models.PositiveIntegerField(
                        default=0,
                        verbose_name="ordem de exibição",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        verbose_name="ativa",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="data de criação",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name="data de atualização",
                    ),
                ),
            ],
            options={
                "verbose_name": "categoria de serviço",
                "verbose_name_plural": "categorias de serviço",
                "ordering": ("display_order", "name"),
            },
        ),
        migrations.CreateModel(
            name="StoreConfiguration",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        max_length=150,
                        verbose_name="nome da barbearia",
                    ),
                ),
                (
                    "slogan",
                    models.CharField(
                        max_length=200,
                        verbose_name="slogan",
                    ),
                ),
                (
                    "presentation_description",
                    models.TextField(
                        verbose_name="descrição de apresentação",
                    ),
                ),
                (
                    "whatsapp_number",
                    models.CharField(
                        max_length=15,
                        validators=[
                            catalog.validators.validate_whatsapp_number,
                        ],
                        verbose_name="número de WhatsApp",
                    ),
                ),
                (
                    "demo_address",
                    models.TextField(
                        verbose_name="endereço demonstrativo",
                    ),
                ),
                (
                    "opening_hours",
                    models.TextField(
                        verbose_name="horário de atendimento",
                    ),
                ),
                (
                    "banner_image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to=catalog.validators.store_image_upload_path,
                        validators=[
                            catalog.validators.validate_uploaded_image,
                        ],
                        verbose_name="imagem de capa do banner",
                    ),
                ),
                (
                    "banner_text",
                    models.CharField(
                        max_length=200,
                        verbose_name="texto do banner",
                    ),
                ),
                (
                    "primary_button_text",
                    models.CharField(
                        default="Agendar pelo WhatsApp",
                        max_length=50,
                        verbose_name="texto do botão principal",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="data de criação",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name="data de atualização",
                    ),
                ),
            ],
            options={
                "verbose_name": "configuração da barbearia",
                "verbose_name_plural": "configuração da barbearia",
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(id=1),
                        name="store_configuration_singleton_id",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="Service",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        max_length=150,
                        verbose_name="nome",
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        max_length=150,
                        unique=True,
                        verbose_name="slug",
                    ),
                ),
                (
                    "short_description",
                    models.TextField(
                        verbose_name="descrição curta",
                    ),
                ),
                (
                    "full_description",
                    models.TextField(
                        verbose_name="descrição completa",
                    ),
                ),
                (
                    "price",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        validators=[
                            catalog.validators.validate_non_negative_price,
                        ],
                        verbose_name="preço",
                    ),
                ),
                (
                    "duration_minutes",
                    models.PositiveIntegerField(
                        validators=[
                            catalog.validators.validate_positive_duration,
                        ],
                        verbose_name="duração em minutos",
                    ),
                ),
                (
                    "main_image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to=catalog.validators.service_image_upload_path,
                        validators=[
                            catalog.validators.validate_uploaded_image,
                        ],
                        verbose_name="imagem principal",
                    ),
                ),
                (
                    "alt_text",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=200,
                        verbose_name="texto alternativo",
                    ),
                ),
                (
                    "is_featured",
                    models.BooleanField(
                        default=False,
                        verbose_name="destaque na página inicial",
                    ),
                ),
                (
                    "is_published",
                    models.BooleanField(
                        default=True,
                        verbose_name="publicado",
                    ),
                ),
                (
                    "display_order",
                    models.PositiveIntegerField(
                        default=0,
                        verbose_name="ordem de exibição",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="data de criação",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name="data de atualização",
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="services",
                        to="catalog.servicecategory",
                        verbose_name="categoria",
                    ),
                ),
            ],
            options={
                "verbose_name": "serviço",
                "verbose_name_plural": "serviços",
                "ordering": ("display_order", "name"),
            },
        ),
        migrations.CreateModel(
            name="Barber",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        max_length=100,
                        verbose_name="nome",
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        max_length=100,
                        unique=True,
                        verbose_name="slug",
                    ),
                ),
                (
                    "specialty",
                    models.CharField(
                        max_length=150,
                        verbose_name="especialidade",
                    ),
                ),
                (
                    "short_description",
                    models.TextField(
                        verbose_name="descrição curta",
                    ),
                ),
                (
                    "main_photo",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to=catalog.validators.barber_image_upload_path,
                        validators=[
                            catalog.validators.validate_uploaded_image,
                        ],
                        verbose_name="foto principal",
                    ),
                ),
                (
                    "alt_text",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=200,
                        verbose_name="texto alternativo",
                    ),
                ),
                (
                    "display_order",
                    models.PositiveIntegerField(
                        default=0,
                        verbose_name="ordem de exibição",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        verbose_name="ativo",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="data de criação",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name="data de atualização",
                    ),
                ),
            ],
            options={
                "verbose_name": "barbeiro",
                "verbose_name_plural": "barbeiros",
                "ordering": ("display_order", "name"),
            },
        ),
        migrations.CreateModel(
            name="Promotion",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "title",
                    models.CharField(
                        max_length=150,
                        verbose_name="título",
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        verbose_name="descrição",
                    ),
                ),
                (
                    "image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to=catalog.validators.promotion_image_upload_path,
                        validators=[
                            catalog.validators.validate_uploaded_image,
                        ],
                        verbose_name="imagem",
                    ),
                ),
                (
                    "start_date",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="data de início",
                    ),
                ),
                (
                    "end_date",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="data de fim",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        verbose_name="ativa",
                    ),
                ),
                (
                    "display_order",
                    models.PositiveIntegerField(
                        default=0,
                        verbose_name="ordem de exibição",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="data de criação",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name="data de atualização",
                    ),
                ),
                (
                    "linked_service",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="promotions",
                        to="catalog.service",
                        verbose_name="serviço vinculado",
                    ),
                ),
            ],
            options={
                "verbose_name": "promoção",
                "verbose_name_plural": "promoções",
                "ordering": ("display_order", "title"),
            },
        ),
        migrations.AddIndex(
            model_name="servicecategory",
            index=models.Index(
                fields=["is_active", "display_order", "name"],
                name="category_public_order_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="service",
            index=models.Index(
                fields=["is_published", "display_order", "name"],
                name="service_public_order_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="service",
            index=models.Index(
                fields=["category", "is_published"],
                name="service_category_pub_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="service",
            index=models.Index(
                fields=["is_featured", "is_published"],
                name="service_featured_pub_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="service",
            index=models.Index(
                fields=["price"],
                name="service_price_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="barber",
            index=models.Index(
                fields=["is_active", "display_order", "name"],
                name="barber_public_order_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="promotion",
            index=models.Index(
                fields=["is_active", "start_date", "end_date"],
                name="promotion_period_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="promotion",
            index=models.Index(
                fields=["linked_service", "is_active"],
                name="promotion_service_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="promotion",
            index=models.Index(
                fields=["display_order", "title"],
                name="promotion_order_idx",
            ),
        ),
    ]