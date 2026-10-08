"""Popula o banco com dados demonstrativos da barbearia.

Este comando cria ou atualiza dados fictícios para facilitar o desenvolvimento
e a validação manual do frontend.

O comando não cria usuários, senhas, imagens externas, depoimentos reais,
endereços reais ou dados de pessoas e empresas existentes.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from catalog.models import (
    Barber,
    Promotion,
    Service,
    ServiceCategory,
    StoreConfiguration,
)


@dataclass(frozen=True)
class CategorySeed:
    """Representa os dados iniciais de uma categoria fictícia."""

    name: str
    slug: str
    short_description: str
    display_order: int


@dataclass(frozen=True)
class ServiceSeed:
    """Representa os dados iniciais de um serviço fictício."""

    category_slug: str
    name: str
    slug: str
    short_description: str
    full_description: str
    price: Decimal
    duration_minutes: int
    is_featured: bool
    is_published: bool
    display_order: int


@dataclass(frozen=True)
class BarberSeed:
    """Representa os dados iniciais de um barbeiro fictício."""

    name: str
    slug: str
    specialty: str
    short_description: str
    display_order: int
    is_active: bool


class Command(BaseCommand):
    """Executa a carga idempotente de dados demonstrativos."""

    help: str = (
        "Cria ou atualiza dados fictícios da Barbearia Vintage & Co."
    )

    def handle(
        self,
        *args: Any,
        **options: Any,
    ) -> None:
        """Executa o comando de carga de dados.

        Os argumentos posicionais e as opções são aceitos pelo padrão do
        Django, mas não são necessários para esta carga.

        Args:
            *args: Argumentos posicionais recebidos do Django.
            **options: Opções recebidas da linha de comando.
        """
        del args
        del options

        with transaction.atomic():
            store, store_created = self._seed_store()
            categories = self._seed_categories()
            services = self._seed_services(categories)
            barbers = self._seed_barbers()
            promotion = self._seed_promotion(services)

        self.stdout.write(
            self.style.SUCCESS(
                "Dados demonstrativos processados com sucesso."
            )
        )

        self.stdout.write(
            f"Configuração da barbearia: "
            f"{'criada' if store_created else 'atualizada'} "
            f"({store.name})"
        )

        self.stdout.write(
            f"Categorias processadas: {len(categories)}"
        )

        self.stdout.write(
            f"Serviços processados: {len(services)}"
        )

        self.stdout.write(
            f"Barbeiros processados: {len(barbers)}"
        )

        self.stdout.write(
            f"Promoção processada: {promotion.title}"
        )

        self.stdout.write(
            self.style.WARNING(
                "Nenhum usuário administrador foi criado. "
                "Use 'python manage.py createsuperuser' "
                "para criar um acesso local."
            )
        )

    def _seed_store(
        self,
    ) -> tuple[StoreConfiguration, bool]:
        """Cria ou atualiza a configuração única da barbearia.

        Returns:
            Tupla contendo a configuração persistida e um booleano que
            informa se o registro acabou de ser criado.
        """
        defaults: dict[str, Any] = {
            "name": "Barbearia Vintage & Co.",
            "slogan": "Estilo clássico, cuidado contemporâneo.",
            "presentation_description": (
                "A Barbearia Vintage & Co. é uma marca fictícia criada "
                "para demonstrar um catálogo digital de serviços "
                "masculinos, cuidados de barba e tratamentos capilares."
            ),
            "whatsapp_number": "5521999999999",
            "demo_address": (
                "Endereço fictício para demonstração — "
                "não utilizar em produção."
            ),
            "opening_hours": (
                "Segunda a sexta, das 9h às 19h. "
                "Sábados, das 9h às 16h. "
                "Horários fictícios."
            ),
            "banner_image": None,
            "banner_text": (
                "Seu estilo merece um atendimento com personalidade."
            ),
            "primary_button_text": "Agendar pelo WhatsApp",
        }

        store, created = StoreConfiguration.objects.update_or_create(
            pk=1,
            defaults=defaults,
        )

        return store, created

    def _seed_categories(self) -> dict[str, ServiceCategory]:
        """Cria ou atualiza as categorias demonstrativas.

        Returns:
            Dicionário que relaciona cada slug à categoria persistida.
        """
        category_seeds: tuple[CategorySeed, ...] = (
            CategorySeed(
                name="Cortes",
                slug="cortes",
                short_description=(
                    "Cortes clássicos e contemporâneos para diferentes "
                    "estilos."
                ),
                display_order=1,
            ),
            CategorySeed(
                name="Barba",
                slug="barba",
                short_description=(
                    "Serviços de barba com acabamento cuidadoso e preciso."
                ),
                display_order=2,
            ),
            CategorySeed(
                name="Tratamentos",
                slug="tratamentos",
                short_description=(
                    "Cuidados complementares para cabelo, couro cabeludo "
                    "e barba."
                ),
                display_order=3,
            ),
        )

        categories: dict[str, ServiceCategory] = {}

        for seed in category_seeds:
            category, _ = ServiceCategory.objects.update_or_create(
                slug=seed.slug,
                defaults={
                    "name": seed.name,
                    "short_description": seed.short_description,
                    "display_order": seed.display_order,
                    "is_active": True,
                },
            )

            categories[seed.slug] = category

        return categories

    def _seed_services(
        self,
        categories: dict[str, ServiceCategory],
    ) -> dict[str, Service]:
        """Cria ou atualiza os serviços demonstrativos.

        Args:
            categories: Categorias previamente persistidas, indexadas pelo
                slug.

        Returns:
            Dicionário que relaciona cada slug ao serviço persistido.
        """
        service_seeds: tuple[ServiceSeed, ...] = (
            ServiceSeed(
                category_slug="cortes",
                name="Corte Vintage",
                slug="corte-vintage",
                short_description=(
                    "Corte clássico com acabamento moderno e personalizado."
                ),
                full_description=(
                    "Serviço demonstrativo que combina referências "
                    "clássicas com acabamento contemporâneo. O formato "
                    "final deve ser definido durante a consulta fictícia."
                ),
                price=Decimal("55.00"),
                duration_minutes=45,
                is_featured=True,
                is_published=True,
                display_order=1,
            ),
            ServiceSeed(
                category_slug="cortes",
                name="Corte Executivo",
                slug="corte-executivo",
                short_description=(
                    "Visual alinhado para uma apresentação elegante."
                ),
                full_description=(
                    "Corte demonstrativo de linhas discretas e acabamento "
                    "organizado, indicado para quem prefere um visual "
                    "prático e sofisticado."
                ),
                price=Decimal("65.00"),
                duration_minutes=50,
                is_featured=True,
                is_published=True,
                display_order=2,
            ),
            ServiceSeed(
                category_slug="cortes",
                name="Corte Infantil",
                slug="corte-infantil",
                short_description=(
                    "Corte demonstrativo pensado para o público infantil."
                ),
                full_description=(
                    "Serviço fictício com proposta de atendimento acolhedor "
                    "e acabamento simples, adequado para demonstração "
                    "de catálogo."
                ),
                price=Decimal("45.00"),
                duration_minutes=35,
                is_featured=False,
                is_published=True,
                display_order=3,
            ),
            ServiceSeed(
                category_slug="barba",
                name="Barba Tradicional",
                slug="barba-tradicional",
                short_description=(
                    "Aparação e acabamento tradicional da barba."
                ),
                full_description=(
                    "Serviço demonstrativo de cuidado com a barba, incluindo "
                    "aparação, definição das linhas e acabamento final."
                ),
                price=Decimal("40.00"),
                duration_minutes=30,
                is_featured=True,
                is_published=True,
                display_order=1,
            ),
            ServiceSeed(
                category_slug="barba",
                name="Barba Premium",
                slug="barba-premium",
                short_description=(
                    "Experiência completa de cuidado e acabamento da barba."
                ),
                full_description=(
                    "Serviço fictício com preparação, modelagem, acabamento "
                    "e cuidados complementares para uma experiência mais "
                    "detalhada."
                ),
                price=Decimal("60.00"),
                duration_minutes=45,
                is_featured=True,
                is_published=True,
                display_order=2,
            ),
            ServiceSeed(
                category_slug="barba",
                name="Combo Corte e Barba",
                slug="combo-corte-e-barba",
                short_description=(
                    "Combinação demonstrativa de corte e cuidado da barba."
                ),
                full_description=(
                    "Pacote fictício que reúne dois serviços do catálogo "
                    "em uma única apresentação comercial."
                ),
                price=Decimal("90.00"),
                duration_minutes=75,
                is_featured=True,
                is_published=True,
                display_order=3,
            ),
            ServiceSeed(
                category_slug="tratamentos",
                name="Hidratação Capilar",
                slug="hidratacao-capilar",
                short_description=(
                    "Tratamento demonstrativo para melhorar o cuidado "
                    "dos fios."
                ),
                full_description=(
                    "Tratamento fictício para demonstração de catálogo, "
                    "com foco em hidratação e cuidado geral dos cabelos."
                ),
                price=Decimal("50.00"),
                duration_minutes=40,
                is_featured=False,
                is_published=True,
                display_order=1,
            ),
        )

        services: dict[str, Service] = {}

        for seed in service_seeds:
            category = categories.get(seed.category_slug)

            if category is None:
                raise RuntimeError(
                    "Categoria não encontrada para o serviço "
                    f"'{seed.slug}'."
                )

            service, _ = Service.objects.update_or_create(
                slug=seed.slug,
                defaults={
                    "category": category,
                    "name": seed.name,
                    "short_description": seed.short_description,
                    "full_description": seed.full_description,
                    "price": seed.price,
                    "duration_minutes": seed.duration_minutes,
                    "main_image": None,
                    "alt_text": "",
                    "is_featured": seed.is_featured,
                    "is_published": seed.is_published,
                    "display_order": seed.display_order,
                },
            )

            services[seed.slug] = service

        return services

    def _seed_barbers(self) -> dict[str, Barber]:
        """Cria ou atualiza os barbeiros fictícios.

        Returns:
            Dicionário que relaciona cada slug ao barbeiro persistido.
        """
        barber_seeds: tuple[BarberSeed, ...] = (
            BarberSeed(
                name="Arthur Valença",
                slug="arthur-valenca",
                specialty="Cortes clássicos e acabamento tradicional",
                short_description=(
                    "Perfil fictício especializado em cortes de inspiração "
                    "clássica."
                ),
                display_order=1,
                is_active=True,
            ),
            BarberSeed(
                name="Caio Montenegro",
                slug="caio-montenegro",
                specialty="Barba e modelagem masculina",
                short_description=(
                    "Perfil fictício dedicado a cuidados e modelagem "
                    "de barba."
                ),
                display_order=2,
                is_active=True,
            ),
            BarberSeed(
                name="Miguel Bastos",
                slug="miguel-bastos",
                specialty="Cortes contemporâneos e tratamentos",
                short_description=(
                    "Perfil fictício com foco em estilos atuais e tratamentos "
                    "capilares."
                ),
                display_order=3,
                is_active=True,
            ),
        )

        barbers: dict[str, Barber] = {}

        for seed in barber_seeds:
            barber, _ = Barber.objects.update_or_create(
                slug=seed.slug,
                defaults={
                    "name": seed.name,
                    "specialty": seed.specialty,
                    "short_description": seed.short_description,
                    "main_photo": None,
                    "alt_text": "",
                    "display_order": seed.display_order,
                    "is_active": seed.is_active,
                },
            )

            barbers[seed.slug] = barber

        return barbers

    def _seed_promotion(
        self,
        services: dict[str, Service],
    ) -> Promotion:
        """Cria ou atualiza a promoção demonstrativa.

        A promoção é criada sem imagem e vinculada ao serviço fictício
        ``combo-corte-e-barba``. O período é iniciado alguns dias antes da
        execução e termina no futuro, mantendo a promoção elegível na
        demonstração.

        Args:
            services: Serviços persistidos, indexados pelo slug.

        Returns:
            Promoção demonstrativa persistida.
        """
        linked_service = services.get("combo-corte-e-barba")

        if linked_service is None:
            raise RuntimeError(
                "O serviço 'combo-corte-e-barba' não foi encontrado."
            )

        current_time = timezone.now()

        promotion, _ = Promotion.objects.update_or_create(
            title="Combo Vintage de Demonstração",
            defaults={
                "description": (
                    "Promoção fictícia para demonstrar um destaque "
                    "comercial vinculado a um serviço publicado."
                ),
                "image": None,
                "linked_service": linked_service,
                "start_date": current_time,
                "end_date": current_time.replace(
                    year=current_time.year + 1,
                ),
                "is_active": True,
                "display_order": 1,
            },
        )

        return promotion