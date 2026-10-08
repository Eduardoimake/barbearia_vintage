"""Serialização e validação dos dados da Barbearia Vintage & Co.

Este módulo contém serializers públicos e administrativos.

Os serializers públicos expõem apenas informações necessárias ao visitante.
Os serializers administrativos permitem criação, leitura e atualização dos
recursos pelo painel frontend.

Os nomes dos campos JSON foram definidos em português para manter o contrato
da API alinhado ao produto e à documentação do frontend.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers, status

from .models import (
    Barber,
    Promotion,
    Service,
    ServiceCategory,
    StoreConfiguration,
)

from .slugs import AutoSlugMixin

from .validators import (
    validate_non_negative_price,
    validate_positive_duration,
    validate_uploaded_image,
    validate_whatsapp_input,
    validate_whatsapp_number as validate_whatsapp_number_value,
)


def run_model_validator(
    validator: Any,
    value: Any,
) -> Any:
    """Executa um validador do Django e converte o erro para o DRF.

    Args:
        validator: Função validadora do Django.
        value: Valor que será validado.

    Raises:
        serializers.ValidationError: Quando o validador do Django rejeita o
            valor recebido.

    Returns:
        Valor validado.
    """
    try:
        validator(value)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(
            exc.messages
        ) from exc

    return value


class ValidatedImageField(serializers.ImageField):
    """Valida imagem enviada pelo usuário."""

    def to_internal_value(self, data):
        return super().to_internal_value(data)


class PublicCategorySerializer(serializers.ModelSerializer):
    """Serializa uma categoria ativa para exibição pública."""

    nome = serializers.CharField(
        source="name",
        read_only=True,
    )

    descricao_curta = serializers.CharField(
        source="short_description",
        read_only=True,
    )

    ordem_exibicao = serializers.IntegerField(
        source="display_order",
        read_only=True,
    )

    class Meta:
        """Configurações do serializer público de categorias."""

        model: type[ServiceCategory] = ServiceCategory
        fields: tuple[str, ...] = (
            "id",
            "nome",
            "slug",
            "descricao_curta",
            "ordem_exibicao",
        )
        read_only_fields: tuple[str, ...] = fields


class AdminCategorySerializer(AutoSlugMixin, serializers.ModelSerializer):
    """Serializa categorias para leitura e edição administrativa."""

    nome = serializers.CharField(
        source="name",
    )

    descricao_curta = serializers.CharField(
        source="short_description",
        required=False,
        allow_blank=True,
    )

    ordem_exibicao = serializers.IntegerField(
        source="display_order",
        required=False,
        min_value=0,
    )

    ativa = serializers.BooleanField(
        source="is_active",
        required=False,
    )

    data_criacao = serializers.DateTimeField(
        source="created_at",
        read_only=True,
    )

    data_atualizacao = serializers.DateTimeField(
        source="updated_at",
        read_only=True,
    )

    class Meta:
        """Configurações do serializer administrativo de categorias."""

        model: type[ServiceCategory] = ServiceCategory
        fields: tuple[str, ...] = (
            "id",
            "nome",
            "slug",
            "descricao_curta",
            "ordem_exibicao",
            "ativa",
            "data_criacao",
            "data_atualizacao",
        )
        read_only_fields: tuple[str, ...] = (
            "id",
            "data_criacao",
            "data_atualizacao",
        )


class PublicServiceListSerializer(serializers.ModelSerializer):
    """Serializa um serviço publicado para listagem pública."""

    categoria = PublicCategorySerializer(
        source="category",
        read_only=True,
    )

    nome = serializers.CharField(
        source="name",
        read_only=True,
    )

    descricao_curta = serializers.CharField(
        source="short_description",
        read_only=True,
    )

    preco = serializers.DecimalField(
        source="price",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )

    duracao_minutos = serializers.IntegerField(
        source="duration_minutes",
        read_only=True,
    )

    imagem_principal = serializers.ImageField(
        source="main_image",
        read_only=True,
        use_url=True,
    )

    destaque_pagina_inicial = serializers.BooleanField(
        source="is_featured",
        read_only=True,
    )

    status_published = serializers.BooleanField(
        source="is_published",
        read_only=True,
    )

    ordem_exibicao = serializers.IntegerField(
        source="display_order",
        read_only=True,
    )

    class Meta:
        """Configurações do serializer público de listagem de serviços."""

        model: type[Service] = Service
        fields: tuple[str, ...] = (
            "id",
            "categoria",
            "nome",
            "slug",
            "descricao_curta",
            "preco",
            "duracao_minutos",
            "imagem_principal",
            "alt_text",
            "destaque_pagina_inicial",
            "status_published",
            "ordem_exibicao",
        )
        read_only_fields: tuple[str, ...] = fields


class PublicServiceDetailSerializer(PublicServiceListSerializer):
    """Serializa um serviço publicado com descrição completa."""

    descricao_completa = serializers.CharField(
        source="full_description",
        read_only=True,
    )

    class Meta(PublicServiceListSerializer.Meta):
        """Configurações do serializer público de detalhe do serviço."""

        fields: tuple[str, ...] = (
            "id",
            "categoria",
            "nome",
            "slug",
            "descricao_curta",
            "descricao_completa",
            "preco",
            "duracao_minutos",
            "imagem_principal",
            "alt_text",
            "destaque_pagina_inicial",
            "status_published",
            "ordem_exibicao",
        )
        read_only_fields: tuple[str, ...] = fields


class AdminServiceSerializer(AutoSlugMixin, serializers.ModelSerializer):
    """Serializa serviços para leitura, criação e edição administrativa."""

    categoria = serializers.PrimaryKeyRelatedField(
        source="category",
        queryset=ServiceCategory.objects.all(),
    )

    nome = serializers.CharField(
        source="name",
        max_length=150,
    )

    descricao_curta = serializers.CharField(
        source="short_description",
    )

    descricao_completa = serializers.CharField(
        source="full_description",
    )

    preco = serializers.DecimalField(
        source="price",
        max_digits=10,
        decimal_places=2,
    )

    duracao_minutos = serializers.IntegerField(
        source="duration_minutes",
        min_value=1,
    )

    imagem_principal = ValidatedImageField(
        source="main_image",
        required=False,
        allow_null=True,
        use_url=True,
    )

    destaque_pagina_inicial = serializers.BooleanField(
        source="is_featured",
        required=False,
    )

    status_published = serializers.BooleanField(
        source="is_published",
        required=False,
    )

    ordem_exibicao = serializers.IntegerField(
        source="display_order",
        required=False,
        min_value=0,
    )

    data_criacao = serializers.DateTimeField(
        source="created_at",
        read_only=True,
    )

    data_atualizacao = serializers.DateTimeField(
        source="updated_at",
        read_only=True,
    )

    class Meta:
        """Configurações do serializer administrativo de serviços."""

        model: type[Service] = Service
        fields: tuple[str, ...] = (
            "id",
            "categoria",
            "nome",
            "slug",
            "descricao_curta",
            "descricao_completa",
            "preco",
            "duracao_minutos",
            "imagem_principal",
            "alt_text",
            "destaque_pagina_inicial",
            "status_published",
            "ordem_exibicao",
            "data_criacao",
            "data_atualizacao",
        )
        read_only_fields: tuple[str, ...] = (
            "id",
            "data_criacao",
            "data_atualizacao",
        )

    def validate_preco(
        self,
        value: Decimal,
    ) -> Decimal:
        """Valida se o preço informado é não negativo.

        Args:
            value: Preço enviado pelo administrador.

        Raises:
            serializers.ValidationError: Quando o preço é negativo.

        Returns:
            Preço validado.
        """
        return run_model_validator(
            validate_non_negative_price,
            value,
        )

    def validate_duracao_minutos(
        self,
        value: int,
    ) -> int:
        """Valida se a duração do serviço é positiva.

        Args:
            value: Duração em minutos.

        Raises:
            serializers.ValidationError: Quando a duração não é positiva.

        Returns:
            Duração validada.
        """
        return run_model_validator(
            validate_positive_duration,
            value,
        )

    def validate_imagem_principal(
        self,
        value: Any,
    ) -> Any:
        """Valida a imagem principal do serviço.

        Args:
            value: Arquivo de imagem enviado.

        Raises:
            serializers.ValidationError: Quando o arquivo é inválido.

        Returns:
            Arquivo validado.
        """
        return run_model_validator(
            validate_uploaded_image,
            value,
        )


class PublicBarberListSerializer(serializers.ModelSerializer):
    """Serializa um barbeiro ativo para listagem pública."""

    nome = serializers.CharField(
        source="name",
        read_only=True,
    )

    especialidade = serializers.CharField(
        source="specialty",
        read_only=True,
    )

    descricao_curta = serializers.CharField(
        source="short_description",
        read_only=True,
    )

    foto_principal = serializers.ImageField(
        source="main_photo",
        read_only=True,
        use_url=True,
    )

    ordem_exibicao = serializers.IntegerField(
        source="display_order",
        read_only=True,
    )

    ativo = serializers.BooleanField(
        source="is_active",
        read_only=True,
    )

    class Meta:
        """Configurações do serializer público de listagem de barbeiros."""

        model: type[Barber] = Barber
        fields: tuple[str, ...] = (
            "id",
            "nome",
            "slug",
            "especialidade",
            "descricao_curta",
            "foto_principal",
            "alt_text",
            "ordem_exibicao",
            "ativo",
        )
        read_only_fields: tuple[str, ...] = fields


class PublicBarberDetailSerializer(PublicBarberListSerializer):
    """Serializa um barbeiro ativo para o detalhe público."""

    data_criacao = serializers.DateTimeField(
        source="created_at",
        read_only=True,
    )

    data_atualizacao = serializers.DateTimeField(
        source="updated_at",
        read_only=True,
    )

    class Meta(PublicBarberListSerializer.Meta):
        """Configurações do serializer público de detalhe do barbeiro."""

        fields: tuple[str, ...] = (
            "id",
            "nome",
            "slug",
            "especialidade",
            "descricao_curta",
            "foto_principal",
            "alt_text",
            "ordem_exibicao",
            "ativo",
            "data_criacao",
            "data_atualizacao",
        )
        read_only_fields: tuple[str, ...] = fields


class AdminBarberSerializer(AutoSlugMixin, serializers.ModelSerializer):
    """Serializa barbeiros para leitura, criação e edição administrativa."""

    nome = serializers.CharField(
        source="name",
        max_length=100,
    )

    especialidade = serializers.CharField(
        source="specialty",
        max_length=150,
    )

    descricao_curta = serializers.CharField(
        source="short_description",
    )

    foto_principal = ValidatedImageField(
        source="main_photo",
        required=False,
        allow_null=True,
        use_url=True,
    )

    ordem_exibicao = serializers.IntegerField(
        source="display_order",
        required=False,
        min_value=0,
    )

    ativo = serializers.BooleanField(
        source="is_active",
        required=False,
    )

    data_criacao = serializers.DateTimeField(
        source="created_at",
        read_only=True,
    )

    data_atualizacao = serializers.DateTimeField(
        source="updated_at",
        read_only=True,
    )

    class Meta:
        """Configurações do serializer administrativo de barbeiros."""

        model: type[Barber] = Barber
        fields: tuple[str, ...] = (
            "id",
            "nome",
            "slug",
            "especialidade",
            "descricao_curta",
            "foto_principal",
            "alt_text",
            "ordem_exibicao",
            "ativo",
            "data_criacao",
            "data_atualizacao",
        )
        read_only_fields: tuple[str, ...] = (
            "id",
            "data_criacao",
            "data_atualizacao",
        )

    def validate_foto_principal(
        self,
        value: Any,
    ) -> Any:
        """Valida a foto enviada pelo administrador.

        Args:
            value: Arquivo de imagem.

        Raises:
            serializers.ValidationError: Quando o arquivo é inválido.

        Returns:
            Arquivo validado.
        """
        return run_model_validator(
            validate_uploaded_image,
            value,
        )


class PublicStoreSerializer(serializers.ModelSerializer):
    """Dados públicos da configuração da barbearia."""

    nome_da_barbearia = serializers.CharField(
        source="name",
        read_only=True,
    )
    descricao_apresentacao = serializers.CharField(
        source="presentation_description",
        read_only=True,
    )
    numero_whatsapp = serializers.CharField(
        source="whatsapp_number",
        read_only=True,
    )
    endereco_demo = serializers.CharField(
        source="demo_address",
        read_only=True,
    )
    horario_atendimento = serializers.CharField(
        source="opening_hours",
        read_only=True,
    )
    imagem_capa_banner = serializers.ImageField(
        source="banner_image",
        read_only=True,
        use_url=True,
    )
    texto_banner = serializers.CharField(
        source="banner_text",
        read_only=True,
    )
    texto_botao_principal = serializers.CharField(
        source="primary_button_text",
        read_only=True,
    )

    class Meta:
        model = StoreConfiguration
        fields = (
            "nome_da_barbearia",
            "slogan",
            "descricao_apresentacao",
            "numero_whatsapp",
            "endereco_demo",
            "horario_atendimento",
            "imagem_capa_banner",
            "texto_banner",
            "texto_botao_principal",
        )
        read_only_fields = fields


class AdminStoreSerializer(serializers.ModelSerializer):
    """Serializa a configuração administrativa da barbearia."""

    nome_da_barbearia = serializers.CharField(
        source="name",
        required=False,
        max_length=150,
    )
    descricao_apresentacao = serializers.CharField(
        source="presentation_description",
        required=False,
    )
    numero_whatsapp = serializers.CharField(
        source="whatsapp_number",
        required=False,
        max_length=15,
    )
    endereco_demo = serializers.CharField(
        source="demo_address",
        required=False,
    )
    horario_atendimento = serializers.CharField(
        source="opening_hours",
        required=False,
    )
    imagem_capa_banner = ValidatedImageField(
        source="banner_image",
        required=False,
        allow_null=True,
        use_url=True,
    )
    texto_banner = serializers.CharField(
        source="banner_text",
        required=False,
    )
    texto_botao_principal = serializers.CharField(
        source="primary_button_text",
        required=False,
    )
    data_criacao = serializers.DateTimeField(
        source="created_at",
        read_only=True,
    )
    data_atualizacao = serializers.DateTimeField(
        source="updated_at",
        read_only=True,
    )

    class Meta:
        model = StoreConfiguration
        fields = (
            "id",
            "nome_da_barbearia",
            "slogan",
            "descricao_apresentacao",
            "numero_whatsapp",
            "endereco_demo",
            "horario_atendimento",
            "imagem_capa_banner",
            "texto_banner",
            "texto_botao_principal",
            "data_criacao",
            "data_atualizacao",
        )
        read_only_fields = (
            "id",
            "data_criacao",
            "data_atualizacao",
        )

    def validate_numero_whatsapp(self, value: str) -> str:
        return run_model_validator(
            validate_whatsapp_number_value,
            value,
        )

    def validate_imagem_capa_banner(self, value: Any) -> Any:
        return run_model_validator(
            validate_uploaded_image,
            value,
        )


class PublicPromotionSerializer(serializers.ModelSerializer):
    """Promoção elegível exibida no site público."""

    titulo = serializers.CharField(
        source="title",
        read_only=True,
    )
    descricao = serializers.CharField(
        source="description",
        read_only=True,
    )
    imagem = serializers.ImageField(
        source="image",
        read_only=True,
        use_url=True,
    )
    servico_vinculado = PublicServiceListSerializer(
        source="linked_service",
        read_only=True,
    )
    data_inicio = serializers.DateTimeField(
        source="start_date",
        read_only=True,
    )
    data_fim = serializers.DateTimeField(
        source="end_date",
        read_only=True,
    )
    ativa = serializers.BooleanField(
        source="is_active",
        read_only=True,
    )
    ordem_exibicao = serializers.IntegerField(
        source="display_order",
        read_only=True,
    )

    class Meta:
        model = Promotion
        fields = (
            "id",
            "titulo",
            "descricao",
            "imagem",
            "servico_vinculado",
            "data_inicio",
            "data_fim",
            "ativa",
            "ordem_exibicao",
        )
        read_only_fields = fields


class AdminPromotionSerializer(serializers.ModelSerializer):
    """Criação e edição administrativa de promoções."""

    titulo = serializers.CharField(
        source="title",
        required=False,
        max_length=150,
    )
    descricao = serializers.CharField(
        source="description",
        required=False,
    )
    imagem = ValidatedImageField(
        source="image",
        required=False,
        allow_null=True,
        use_url=True,
    )
    servico_vinculado = serializers.PrimaryKeyRelatedField(
        source="linked_service",
        queryset=Service.objects.all(),
        required=False,
        allow_null=True,
    )
    data_inicio = serializers.DateTimeField(
        source="start_date",
        required=False,
        allow_null=True,
    )
    data_fim = serializers.DateTimeField(
        source="end_date",
        required=False,
        allow_null=True,
    )
    ativa = serializers.BooleanField(
        source="is_active",
        required=False,
    )
    ordem_exibicao = serializers.IntegerField(
        source="display_order",
        required=False,
        min_value=0,
    )
    data_criacao = serializers.DateTimeField(
        source="created_at",
        read_only=True,
    )
    data_atualizacao = serializers.DateTimeField(
        source="updated_at",
        read_only=True,
    )

    class Meta:
        model = Promotion
        fields = (
            "id",
            "titulo",
            "descricao",
            "imagem",
            "servico_vinculado",
            "data_inicio",
            "data_fim",
            "ativa",
            "ordem_exibicao",
            "data_criacao",
            "data_atualizacao",
        )
        read_only_fields = (
            "id",
            "data_criacao",
            "data_atualizacao",
        )

    def validate(self, attrs):
        """Valida campos obrigatórios na criação e o período da promoção.

        Na criação, ``titulo`` e ``descricao`` são obrigatórios. Na edição
        parcial, continuam opcionais.

        Args:
            attrs: Dados já convertidos pelos campos do serializer.

        Raises:
            serializers.ValidationError: Quando faltam campos obrigatórios
                na criação ou quando o período é inválido.

        Returns:
            Dados validados.
        """
        if self.instance is None:
            missing: dict[str, list[str]] = {}

            if "title" not in attrs:
                missing["titulo"] = ["Este campo é obrigatório."]

            if "description" not in attrs:
                missing["descricao"] = ["Este campo é obrigatório."]

            if missing:
                raise serializers.ValidationError(missing)

        start_date = attrs.get(
            "start_date",
            self.instance.start_date if self.instance else None,
        )
        end_date = attrs.get(
            "end_date",
            self.instance.end_date if self.instance else None,
        )

        if (
            start_date is not None
            and end_date is not None
            and start_date > end_date
        ):
            raise serializers.ValidationError(
                {
                    "data_fim": [
                        "A data final não pode ser anterior "
                        "à data inicial."
                    ]
                }
            )

        return attrs


class AdminUserSerializer(serializers.Serializer):
    """Serializa informações seguras do usuário administrador autenticado."""

    id = serializers.IntegerField(
        read_only=True,
    )

    username = serializers.CharField(
        read_only=True,
    )

    is_staff = serializers.BooleanField(
        read_only=True,
    )

    class Meta:
        """Configurações do serializer de usuário administrador."""

        fields: tuple[str, ...] = (
            "id",
            "username",
            "is_staff",
        )