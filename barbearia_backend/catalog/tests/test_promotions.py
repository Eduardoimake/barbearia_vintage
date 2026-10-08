"""Testes das regras de promoções e relações com serviços."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from catalog.models import (
    Promotion,
    Service,
    ServiceCategory,
)


class PromotionTests(TestCase):
    """Testa período, publicação e SET_NULL das promoções."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Cria os dados iniciais das promoções."""
        user_model = get_user_model()

        cls.staff = user_model.objects.create_user(
            username="staff_promocoes",
            password="SenhaDeTesteForte-456!",
            is_staff=True,
        )

        cls.category = ServiceCategory.objects.create(
            name="Barba",
            slug="barba-promocoes",
            short_description="Categoria de testes.",
            is_active=True,
        )

        cls.service = Service.objects.create(
            category=cls.category,
            name="Barba Premium",
            slug="barba-premium-promocoes",
            short_description="Serviço de barba.",
            full_description="Descrição do serviço.",
            price=Decimal("60.00"),
            duration_minutes=45,
            is_published=True,
        )

    def setUp(self) -> None:
        """Inicializa o cliente da API."""
        self.client = APIClient()

    def test_promocao_atual_e_elegivel(self) -> None:
        """Verifica promoção ativa dentro do período."""
        current_time = timezone.now()

        promotion = Promotion.objects.create(
            title="Promoção Atual",
            description="Promoção vigente.",
            linked_service=self.service,
            start_date=current_time - timedelta(days=1),
            end_date=current_time + timedelta(days=1),
            is_active=True,
        )

        self.assertTrue(
            promotion.is_currently_active(),
        )
        self.assertTrue(
            promotion.is_publicly_eligible(),
        )

    def test_promocao_futura_nao_e_elegivel(self) -> None:
        """Verifica que promoção futura não aparece."""
        current_time = timezone.now()

        promotion = Promotion.objects.create(
            title="Promoção Futura",
            description="Ainda não iniciada.",
            start_date=current_time + timedelta(days=1),
            is_active=True,
        )

        self.assertFalse(
            promotion.is_currently_active(),
        )
        self.assertFalse(
            promotion.is_publicly_eligible(),
        )

    def test_promocao_expirada_nao_e_elegivel(self) -> None:
        """Verifica que promoção expirada não aparece."""
        current_time = timezone.now()

        promotion = Promotion.objects.create(
            title="Promoção Expirada",
            description="Período terminado.",
            end_date=current_time - timedelta(days=1),
            is_active=True,
        )

        self.assertFalse(
            promotion.is_currently_active(),
        )
        self.assertFalse(
            promotion.is_publicly_eligible(),
        )

    def test_promocao_de_servico_oculto_nao_e_publica(self) -> None:
        """Verifica promoção vinculada a serviço oculto."""
        hidden_service = Service.objects.create(
            category=self.category,
            name="Serviço Oculto Promoção",
            slug="servico-oculto-promocao",
            short_description="Serviço oculto.",
            full_description="Descrição.",
            price=Decimal("40.00"),
            duration_minutes=30,
            is_published=False,
        )

        promotion = Promotion.objects.create(
            title="Promoção Serviço Oculto",
            description="Não deve ser pública.",
            linked_service=hidden_service,
            is_active=True,
        )

        self.assertFalse(
            promotion.is_publicly_eligible(),
        )

    def test_promocao_de_categoria_inativa_nao_e_publica(self) -> None:
        """Verifica promoção de serviço em categoria inativa."""
        inactive_category = ServiceCategory.objects.create(
            name="Categoria Inativa",
            slug="categoria-inativa-promocao",
            short_description="Categoria inativa.",
            is_active=False,
        )

        service = Service.objects.create(
            category=inactive_category,
            name="Serviço Categoria Inativa",
            slug="servico-categoria-inativa-promocao",
            short_description="Serviço não público.",
            full_description="Descrição.",
            price=Decimal("45.00"),
            duration_minutes=30,
            is_published=True,
        )

        promotion = Promotion.objects.create(
            title="Promoção Categoria Inativa",
            description="Não deve aparecer.",
            linked_service=service,
            is_active=True,
        )

        self.assertFalse(
            promotion.is_publicly_eligible(),
        )

    def test_exclusao_do_servico_aplica_set_null(self) -> None:
        """Verifica preservação da promoção após exclusão do serviço."""
        promotion = Promotion.objects.create(
            title="Promoção com Serviço",
            description="Serviço será excluído.",
            linked_service=self.service,
            is_active=True,
        )

        service_id = self.service.pk
        self.service.delete()

        promotion.refresh_from_db()

        self.assertFalse(
            Service.objects.filter(pk=service_id).exists(),
        )
        self.assertIsNone(
            promotion.linked_service,
        )
        self.assertTrue(
            Promotion.objects.filter(pk=promotion.pk).exists(),
        )

    def test_promocao_sem_servico_pode_ser_publica(self) -> None:
        """Verifica promoção independente de serviço."""
        promotion = Promotion.objects.create(
            title="Promoção Independente",
            description="Promoção sem serviço.",
            linked_service=None,
            is_active=True,
        )

        self.assertTrue(
            promotion.is_publicly_eligible(),
        )

    def test_api_publica_retorna_somente_promocao_elegivel(self) -> None:
        """Verifica o filtro final na API pública."""
        current_time = timezone.now()

        Promotion.objects.create(
            title="Promoção API Visível",
            description="Promoção atualmente válida.",
            linked_service=self.service,
            start_date=current_time - timedelta(days=1),
            end_date=current_time + timedelta(days=1),
            is_active=True,
        )

        Promotion.objects.create(
            title="Promoção API Oculta",
            description="Promoção desativada.",
            linked_service=self.service,
            is_active=False,
        )

        response = self.client.get(
            "/api/v1/public/promotions/",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [
                item["titulo"]
                for item in response.data
            ],
            ["Promoção API Visível"],
        )

    def test_administrador_pode_atualizar_promocao(self) -> None:
        """Verifica edição administrativa de promoção."""
        promotion = Promotion.objects.create(
            title="Promoção Editável",
            description="Descrição inicial.",
            is_active=True,
        )

        self.client.force_login(self.staff)

        response = self.client.patch(
            f"/api/v1/admin/promotions/{promotion.pk}/",
            {
                "titulo": "Promoção Atualizada",
                "ativa": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        promotion.refresh_from_db()
        self.assertEqual(
            promotion.title,
            "Promoção Atualizada",
        )
        self.assertFalse(promotion.is_active)