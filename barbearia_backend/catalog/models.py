"""Modelos de dados da Barbearia Vintage & Co.

Este módulo contém os modelos persistentes utilizados pelo catálogo público
e pelo painel administrativo da aplicação.

As entidades principais são:

- categoria de serviço;
- serviço;
- barbeiro;
- configuração única da barbearia;
- promoção.

As regras de publicação são aplicadas principalmente nas consultas da API,
mas os modelos também realizam validações de integridade para evitar dados
incoerentes no banco.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, ClassVar

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from .validators import (
    barber_image_upload_path,
    promotion_image_upload_path,
    service_image_upload_path,
    store_image_upload_path,
    validate_date_range,
    validate_non_negative_price,
    validate_positive_duration,
    validate_uploaded_image,
    validate_whatsapp_number,
)


class ServiceCategory(models.Model):
    """Representa uma categoria de serviços da barbearia.

    Categorias organizam os serviços exibidos no catálogo público. Uma
    categoria inativa permanece armazenada para uso administrativo, mas não
    aparece para visitantes e também não libera seus serviços na API pública.
    """

    id: models.AutoField = models.AutoField(
        primary_key=True,
    )

    name: models.CharField = models.CharField(
        max_length=100,
        verbose_name="nome",
    )

    slug: models.SlugField = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name="slug",
    )

    short_description: models.TextField = models.TextField(
        blank=True,
        default="",
        verbose_name="descrição curta",
    )

    display_order: models.PositiveIntegerField = models.PositiveIntegerField(
        default=0,
        verbose_name="ordem de exibição",
    )

    is_active: models.BooleanField = models.BooleanField(
        default=True,
        verbose_name="ativa",
    )

    created_at: models.DateTimeField = models.DateTimeField(
        auto_now_add=True,
        verbose_name="data de criação",
    )

    updated_at: models.DateTimeField = models.DateTimeField(
        auto_now=True,
        verbose_name="data de atualização",
    )

    class Meta:
        """Configurações internas do modelo de categorias."""

        ordering: ClassVar[list[str]] = [
            "display_order",
            "name",
        ]

        verbose_name: str = "categoria de serviço"
        verbose_name_plural: str = "categorias de serviço"

        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=["is_active", "display_order", "name"],
                name="category_public_order_idx",
            ),
        ]

    def __str__(self) -> str:
        """Retorna o nome da categoria para exibição administrativa.

        Returns:
            Nome da categoria.
        """
        return self.name

    @property
    def nome(self) -> str:
        """Retorna o nome em português como propriedade de compatibilidade.

        Returns:
            Nome da categoria.
        """
        return self.name

    @property
    def descricao_curta(self) -> str:
        """Retorna a descrição curta da categoria.

        Returns:
            Descrição curta ou texto vazio.
        """
        return self.short_description

    @property
    def ordem_exibicao(self) -> int:
        """Retorna a ordem de exibição da categoria.

        Returns:
            Posição configurada para exibição.
        """
        return self.display_order

    @property
    def ativa(self) -> bool:
        """Informa se a categoria está ativa.

        Returns:
            ``True`` quando a categoria pode aparecer publicamente.
        """
        return self.is_active

    @property
    def data_criacao(self) -> Any:
        """Retorna o instante de criação da categoria.

        Returns:
            Data e hora de criação.
        """
        return self.created_at

    @property
    def data_atualizacao(self) -> Any:
        """Retorna o instante da última atualização.

        Returns:
            Data e hora da última atualização.
        """
        return self.updated_at


class Service(models.Model):
    """Representa um serviço oferecido pela barbearia.

    Um serviço pode ser publicado ou ocultado sem ser excluído. Mesmo que
    esteja publicado, ele somente será exibido publicamente quando sua
    categoria também estiver ativa.
    """

    id: models.AutoField = models.AutoField(
        primary_key=True,
    )

    category: models.ForeignKey = models.ForeignKey(
        ServiceCategory,
        on_delete=models.PROTECT,
        related_name="services",
        verbose_name="categoria",
    )

    name: models.CharField = models.CharField(
        max_length=150,
        verbose_name="nome",
    )

    slug: models.SlugField = models.SlugField(
        max_length=150,
        unique=True,
        verbose_name="slug",
    )

    short_description: models.TextField = models.TextField(
        verbose_name="descrição curta",
    )

    full_description: models.TextField = models.TextField(
        verbose_name="descrição completa",
    )

    price: models.DecimalField = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[validate_non_negative_price],
        verbose_name="preço",
    )

    duration_minutes: models.PositiveIntegerField = (
        models.PositiveIntegerField(
            validators=[validate_positive_duration],
            verbose_name="duração em minutos",
        )
    )

    main_image: models.ImageField = models.ImageField(
        upload_to=service_image_upload_path,
        null=True,
        blank=True,
        validators=[validate_uploaded_image],
        verbose_name="imagem principal",
    )

    alt_text: models.CharField = models.CharField(
        max_length=200,
        blank=True,
        default="",
        verbose_name="texto alternativo",
    )

    is_featured: models.BooleanField = models.BooleanField(
        default=False,
        verbose_name="destaque na página inicial",
    )

    is_published: models.BooleanField = models.BooleanField(
        default=True,
        verbose_name="publicado",
    )

    display_order: models.PositiveIntegerField = models.PositiveIntegerField(
        default=0,
        verbose_name="ordem de exibição",
    )

    created_at: models.DateTimeField = models.DateTimeField(
        auto_now_add=True,
        verbose_name="data de criação",
    )

    updated_at: models.DateTimeField = models.DateTimeField(
        auto_now=True,
        verbose_name="data de atualização",
    )

    class Meta:
        """Configurações internas do modelo de serviços."""

        ordering: ClassVar[list[str]] = [
            "display_order",
            "name",
        ]

        verbose_name: str = "serviço"
        verbose_name_plural: str = "serviços"

        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=[
                    "is_published",
                    "display_order",
                    "name",
                ],
                name="service_public_order_idx",
            ),
            models.Index(
                fields=[
                    "category",
                    "is_published",
                ],
                name="service_category_pub_idx",
            ),
            models.Index(
                fields=[
                    "is_featured",
                    "is_published",
                ],
                name="service_featured_pub_idx",
            ),
            models.Index(
                fields=["price"],
                name="service_price_idx",
            ),
        ]

    def __str__(self) -> str:
        """Retorna o nome do serviço.

        Returns:
            Nome do serviço.
        """
        return self.name

    def clean(self) -> None:
        """Executa validações adicionais do serviço.

        Além dos validators individuais dos campos, este método confirma que
        o preço e a duração continuam dentro das regras de negócio.

        Raises:
            ValidationError: Caso algum dado seja inválido.
        """
        super().clean()

        errors: dict[str, str] = {}

        if self.price is not None and self.price < Decimal("0.00"):
            errors["price"] = "O preço não pode ser negativo."

        if (
            self.duration_minutes is not None
            and self.duration_minutes <= 0
        ):
            errors["duration_minutes"] = (
                "A duração deve ser maior que zero minuto."
            )

        if errors:
            raise ValidationError(errors)

    @property
    def categoria(self) -> ServiceCategory:
        """Retorna a categoria relacionada ao serviço.

        Returns:
            Categoria do serviço.
        """
        return self.category

    @property
    def nome(self) -> str:
        """Retorna o nome do serviço.

        Returns:
            Nome do serviço.
        """
        return self.name

    @property
    def descricao_curta(self) -> str:
        """Retorna a descrição curta do serviço.

        Returns:
            Descrição curta.
        """
        return self.short_description

    @property
    def descricao_completa(self) -> str:
        """Retorna a descrição completa do serviço.

        Returns:
            Descrição completa.
        """
        return self.full_description

    @property
    def preco(self) -> Decimal:
        """Retorna o preço decimal do serviço.

        Returns:
            Preço sem conversão para float.
        """
        return self.price

    @property
    def duracao_minutos(self) -> int:
        """Retorna a duração do serviço em minutos.

        Returns:
            Duração em minutos.
        """
        return self.duration_minutes

    @property
    def imagem_principal(self) -> Any:
        """Retorna o arquivo de imagem principal.

        Returns:
            Campo de imagem do serviço.
        """
        return self.main_image

    @property
    def destaque_pagina_inicial(self) -> bool:
        """Informa se o serviço é destaque.

        Returns:
            ``True`` quando o serviço está marcado como destaque.
        """
        return self.is_featured

    @property
    def status_published(self) -> bool:
        """Informa se o serviço está publicado.

        Returns:
            ``True`` quando o serviço está publicado.
        """
        return self.is_published

    @property
    def ordem_exibicao(self) -> int:
        """Retorna a ordem de exibição do serviço.

        Returns:
            Posição configurada para exibição.
        """
        return self.display_order

    @property
    def data_criacao(self) -> Any:
        """Retorna o instante de criação do serviço.

        Returns:
            Data e hora de criação.
        """
        return self.created_at

    @property
    def data_atualizacao(self) -> Any:
        """Retorna o instante da última atualização do serviço.

        Returns:
            Data e hora de atualização.
        """
        return self.updated_at

    def is_publicly_visible(self) -> bool:
        """Verifica se o serviço pode ser exibido na área pública.

        Returns:
            ``True`` quando o serviço está publicado e sua categoria está
            ativa.
        """
        return bool(
            self.is_published
            and self.category.is_active
        )


class Barber(models.Model):
    """Representa um barbeiro exibido no catálogo público.

    Barbeiros inativos continuam disponíveis no painel administrativo, mas
    não aparecem na listagem ou no detalhe público.
    """

    id: models.AutoField = models.AutoField(
        primary_key=True,
    )

    name: models.CharField = models.CharField(
        max_length=100,
        verbose_name="nome",
    )

    slug: models.SlugField = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name="slug",
    )

    specialty: models.CharField = models.CharField(
        max_length=150,
        verbose_name="especialidade",
    )

    short_description: models.TextField = models.TextField(
        verbose_name="descrição curta",
    )

    main_photo: models.ImageField = models.ImageField(
        upload_to=barber_image_upload_path,
        null=True,
        blank=True,
        validators=[validate_uploaded_image],
        verbose_name="foto principal",
    )

    alt_text: models.CharField = models.CharField(
        max_length=200,
        blank=True,
        default="",
        verbose_name="texto alternativo",
    )

    display_order: models.PositiveIntegerField = models.PositiveIntegerField(
        default=0,
        verbose_name="ordem de exibição",
    )

    is_active: models.BooleanField = models.BooleanField(
        default=True,
        verbose_name="ativo",
    )

    created_at: models.DateTimeField = models.DateTimeField(
        auto_now_add=True,
        verbose_name="data de criação",
    )

    updated_at: models.DateTimeField = models.DateTimeField(
        auto_now=True,
        verbose_name="data de atualização",
    )

    class Meta:
        """Configurações internas do modelo de barbeiros."""

        ordering: ClassVar[list[str]] = [
            "display_order",
            "name",
        ]

        verbose_name: str = "barbeiro"
        verbose_name_plural: str = "barbeiros"

        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=[
                    "is_active",
                    "display_order",
                    "name",
                ],
                name="barber_public_order_idx",
            ),
        ]

    def __str__(self) -> str:
        """Retorna o nome do barbeiro.

        Returns:
            Nome do barbeiro.
        """
        return self.name

    @property
    def nome(self) -> str:
        """Retorna o nome do barbeiro.

        Returns:
            Nome do barbeiro.
        """
        return self.name

    @property
    def especialidade(self) -> str:
        """Retorna a especialidade do barbeiro.

        Returns:
            Especialidade do barbeiro.
        """
        return self.specialty

    @property
    def descricao_curta(self) -> str:
        """Retorna a descrição curta do barbeiro.

        Returns:
            Descrição curta.
        """
        return self.short_description

    @property
    def foto_principal(self) -> Any:
        """Retorna a foto principal do barbeiro.

        Returns:
            Campo de imagem do barbeiro.
        """
        return self.main_photo

    @property
    def ordem_exibicao(self) -> int:
        """Retorna a ordem pública de exibição.

        Returns:
            Ordem configurada.
        """
        return self.display_order

    @property
    def ativo(self) -> bool:
        """Informa se o barbeiro está ativo.

        Returns:
            ``True`` quando o barbeiro pode ser exibido publicamente.
        """
        return self.is_active

    @property
    def data_criacao(self) -> Any:
        """Retorna a data de criação do barbeiro.

        Returns:
            Data e hora da criação.
        """
        return self.created_at

    @property
    def data_atualizacao(self) -> Any:
        """Retorna a data de atualização do barbeiro.

        Returns:
            Data e hora da atualização.
        """
        return self.updated_at


class StoreConfiguration(models.Model):
    """Representa a configuração única da barbearia.

    O sistema possui uma única configuração institucional. Ela concentra os
    textos públicos, o telefone de WhatsApp, o endereço demonstrativo, os
    horários e a imagem do banner.
    """

    id: models.AutoField = models.AutoField(
        primary_key=True,
    )

    name: models.CharField = models.CharField(
        max_length=150,
        verbose_name="nome da barbearia",
    )

    slogan: models.CharField = models.CharField(
        max_length=200,
        verbose_name="slogan",
    )

    presentation_description: models.TextField = models.TextField(
        verbose_name="descrição de apresentação",
    )

    whatsapp_number: models.CharField = models.CharField(
        max_length=15,
        validators=[validate_whatsapp_number],
        verbose_name="número de WhatsApp",
    )

    demo_address: models.TextField = models.TextField(
        verbose_name="endereço demonstrativo",
    )

    opening_hours: models.TextField = models.TextField(
        verbose_name="horário de atendimento",
    )

    banner_image: models.ImageField = models.ImageField(
        upload_to=store_image_upload_path,
        null=True,
        blank=True,
        validators=[validate_uploaded_image],
        verbose_name="imagem de capa do banner",
    )

    banner_text: models.CharField = models.CharField(
        max_length=200,
        verbose_name="texto do banner",
    )

    primary_button_text: models.CharField = models.CharField(
        max_length=50,
        default="Agendar pelo WhatsApp",
        verbose_name="texto do botão principal",
    )

    created_at: models.DateTimeField = models.DateTimeField(
        auto_now_add=True,
        verbose_name="data de criação",
    )

    updated_at: models.DateTimeField = models.DateTimeField(
        auto_now=True,
        verbose_name="data de atualização",
    )

    class Meta:
        """Configurações internas da configuração da loja."""

        verbose_name: str = "configuração da barbearia"
        verbose_name_plural: str = "configuração da barbearia"

        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.CheckConstraint(
                condition=Q(id=1),
                name="store_configuration_singleton_id",
            ),
        ]

    def __str__(self) -> str:
        """Retorna o nome da barbearia configurada.

        Returns:
            Nome da barbearia.
        """
        return self.name

    def clean(self) -> None:
        """Garante que exista somente uma configuração da barbearia.

        A aplicação utiliza o ID 1 para o registro singleton. Isso permite
        uma restrição adicional no banco e simplifica o endpoint sem ID.

        Raises:
            ValidationError: Caso seja tentada a criação de um registro com
                ID diferente de 1 ou caso já exista outra configuração.
        """
        super().clean()

        if self.pk != 1:
            raise ValidationError(
                "A configuração da barbearia deve utilizar o registro único."
            )

        existing_configuration = (
            type(self)
            .objects
            .exclude(pk=self.pk)
            .first()
        )

        if existing_configuration is not None:
            raise ValidationError(
                "Já existe uma configuração da barbearia."
            )

    def save(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Salva a configuração garantindo o ID singleton.

        Args:
            *args: Argumentos posicionais do método original.
            **kwargs: Argumentos nomeados do método original.

        Raises:
            ValidationError: Caso exista outro registro ou seja utilizado um
                ID diferente de 1.
        """
        if self.pk not in (None, 1):
            raise ValidationError(
                "A configuração da barbearia deve utilizar o registro único."
            )

        if self.pk is None:
            self.pk = 1

        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def nome_da_barbearia(self) -> str:
        """Retorna o nome público da barbearia.

        Returns:
            Nome da barbearia.
        """
        return self.name

    @property
    def descricao_apresentacao(self) -> str:
        """Retorna a descrição institucional da barbearia.

        Returns:
            Descrição de apresentação.
        """
        return self.presentation_description

    @property
    def numero_whatsapp(self) -> str:
        """Retorna o número de WhatsApp sem formatação.

        Returns:
            Número internacional somente com dígitos.
        """
        return self.whatsapp_number

    @property
    def endereco_demo(self) -> str:
        """Retorna o endereço fictício da demonstração.

        Returns:
            Endereço demonstrativo.
        """
        return self.demo_address

    @property
    def horario_atendimento(self) -> str:
        """Retorna os horários de atendimento.

        Returns:
            Horários de atendimento.
        """
        return self.opening_hours

    @property
    def imagem_capa_banner(self) -> Any:
        """Retorna a imagem de capa do banner.

        Returns:
            Campo de imagem do banner.
        """
        return self.banner_image

    @property
    def texto_banner(self) -> str:
        """Retorna o texto do banner.

        Returns:
            Texto promocional ou institucional do banner.
        """
        return self.banner_text

    @property
    def texto_botao_principal(self) -> str:
        """Retorna o texto do botão principal.

        Returns:
            Texto do botão de ação principal.
        """
        return self.primary_button_text

    @property
    def data_criacao(self) -> Any:
        """Retorna a data de criação da configuração.

        Returns:
            Data e hora da criação.
        """
        return self.created_at

    @property
    def data_atualizacao(self) -> Any:
        """Retorna a data de atualização da configuração.

        Returns:
            Data e hora da atualização.
        """
        return self.updated_at


class Promotion(models.Model):
    """Representa uma promoção ou destaque promocional.

    A promoção pode ser independente ou estar vinculada a um serviço. Quando
    o serviço relacionado é excluído, o vínculo se torna nulo e a promoção
    continua preservada.
    """

    id: models.AutoField = models.AutoField(
        primary_key=True,
    )

    title: models.CharField = models.CharField(
        max_length=150,
        verbose_name="título",
    )

    description: models.TextField = models.TextField(
        verbose_name="descrição",
    )

    image: models.ImageField = models.ImageField(
        upload_to=promotion_image_upload_path,
        null=True,
        blank=True,
        validators=[validate_uploaded_image],
        verbose_name="imagem",
    )

    linked_service: models.ForeignKey = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        related_name="promotions",
        null=True,
        blank=True,
        verbose_name="serviço vinculado",
    )

    start_date: models.DateTimeField = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="data de início",
    )

    end_date: models.DateTimeField = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="data de fim",
    )

    is_active: models.BooleanField = models.BooleanField(
        default=True,
        verbose_name="ativa",
    )

    display_order: models.PositiveIntegerField = models.PositiveIntegerField(
        default=0,
        verbose_name="ordem de exibição",
    )

    created_at: models.DateTimeField = models.DateTimeField(
        auto_now_add=True,
        verbose_name="data de criação",
    )

    updated_at: models.DateTimeField = models.DateTimeField(
        auto_now=True,
        verbose_name="data de atualização",
    )

    class Meta:
        """Configurações internas do modelo de promoções."""

        ordering: ClassVar[list[str]] = [
            "display_order",
            "title",
        ]

        verbose_name: str = "promoção"
        verbose_name_plural: str = "promoções"

        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=[
                    "is_active",
                    "start_date",
                    "end_date",
                ],
                name="promotion_period_idx",
            ),
            models.Index(
                fields=[
                    "linked_service",
                    "is_active",
                ],
                name="promotion_service_idx",
            ),
            models.Index(
                fields=[
                    "display_order",
                    "title",
                ],
                name="promotion_order_idx",
            ),
        ]

    def __str__(self) -> str:
        """Retorna o título da promoção.

        Returns:
            Título da promoção.
        """
        return self.title

    def clean(self) -> None:
        """Valida o período e o vínculo da promoção.

        A data final não pode ser anterior à data inicial. Quando um serviço
        está vinculado, ele não precisa estar publicado para ser salvo
        administrativamente; essa condição é aplicada na elegibilidade
        pública. Isso permite que o administrador prepare uma promoção antes
        de publicar o serviço.

        Raises:
            ValidationError: Caso o período seja inválido.
        """
        super().clean()

        validate_date_range(
            self.start_date,
            self.end_date,
        )

    def is_currently_active(self) -> bool:
        """Verifica se a promoção está ativa no momento atual.

        A verificação considera:

        - campo ``is_active``;
        - início nulo ou já alcançado;
        - fim nulo ou ainda não ultrapassado.

        Returns:
            ``True`` quando a promoção está dentro do período configurado.
        """
        if not self.is_active:
            return False

        current_time = timezone.now()

        if (
            self.start_date is not None
            and self.start_date > current_time
        ):
            return False

        if (
            self.end_date is not None
            and self.end_date < current_time
        ):
            return False

        return True

    def is_publicly_eligible(self) -> bool:
        """Verifica se a promoção pode ser exibida ao visitante.

        Além do período e do status da promoção, um serviço vinculado precisa
        estar publicado e associado a uma categoria ativa.

        Returns:
            ``True`` quando a promoção pode aparecer na API pública.
        """
        if not self.is_currently_active():
            return False

        if self.linked_service is None:
            return True

        return self.linked_service.is_publicly_visible()

    @property
    def titulo(self) -> str:
        """Retorna o título da promoção.

        Returns:
            Título.
        """
        return self.title

    @property
    def descricao(self) -> str:
        """Retorna a descrição da promoção.

        Returns:
            Descrição.
        """
        return self.description

    @property
    def servico_vinculado(self) -> Service | None:
        """Retorna o serviço vinculado, quando existente.

        Returns:
            Serviço relacionado ou ``None``.
        """
        return self.linked_service

    @property
    def data_inicio(self) -> Any:
        """Retorna a data inicial da promoção.

        Returns:
            Data inicial ou ``None``.
        """
        return self.start_date

    @property
    def data_fim(self) -> Any:
        """Retorna a data final da promoção.

        Returns:
            Data final ou ``None``.
        """
        return self.end_date

    @property
    def ativa(self) -> bool:
        """Informa se a promoção está marcada como ativa.

        Returns:
            ``True`` quando o campo de ativação está habilitado.
        """
        return self.is_active

    @property
    def ordem_exibicao(self) -> int:
        """Retorna a ordem de exibição da promoção.

        Returns:
            Posição configurada.
        """
        return self.display_order

    @property
    def data_criacao(self) -> Any:
        """Retorna a data de criação da promoção.

        Returns:
            Data e hora da criação.
        """
        return self.created_at

    @property
    def data_atualizacao(self) -> Any:
        """Retorna a data de atualização da promoção.

        Returns:
            Data e hora da atualização.
        """
        return self.updated_at