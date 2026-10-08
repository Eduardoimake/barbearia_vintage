"""Testes da API pública do catálogo."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from catalog.models import (
    Barber,
    Promotion,
    Service,
    ServiceCategory,
    StoreConfiguration,
)


class PublicAPITests(TestCase):
    """Testa visibilidade, filtros, paginação e promoções públicas."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Cria o conjunto fixo de dados usado pelos testes públicos."""
        cls.active_category = ServiceCategory.objects.create(
            name="Cortes",
            slug="cortes",
            short_description="Cortes demonstrativos.",
            display_order=1,
            is_active=True,
        )

        cls.inactive_category = ServiceCategory.objects.create(
            name="Categoria Inativa",
            slug="categoria-inativa",
            short_description="Categoria não publicada.",
            display_order=2,
            is_active=False,
        )

        cls.visible_service = Service.objects.create(
            category=cls.active_category,
            name="Corte Vintage",
            slug="corte-vintage",
            short_description="Corte clássico demonstrativo.",
            full_description="Descrição completa do corte fictício.",
            price=Decimal("55.00"),
            duration_minutes=45,
            is_featured=True,
            is_published=True,
            display_order=1,
        )

        cls.hidden_service = Service.objects.create(
            category=cls.active_category,
            name="Serviço Oculto",
            slug="servico-oculto",
            short_description="Não deve aparecer.",
            full_description="Descrição de serviço oculto.",
            price=Decimal("40.00"),
            duration_minutes=30,
            is_featured=False,
            is_published=False,
            display_order=2,
        )

        cls.inactive_category_service = Service.objects.create(
            category=cls.inactive_category,
            name="Serviço de Categoria Inativa",
            slug="servico-categoria-inativa",
            short_description="Não deve aparecer.",
            full_description="Serviço pertencente a categoria inativa.",
            price=Decimal("60.00"),
            duration_minutes=40,
            is_featured=True,
            is_published=True,
            display_order=3,
        )

        cls.active_barber = Barber.objects.create(
            name="Arthur Valença",
            slug="arthur-valenca",
            specialty="Cortes clássicos",
            short_description="Barbeiro fictício ativo.",
            display_order=1,
            is_active=True,
        )

        cls.inactive_barber = Barber.objects.create(
            name="Barbeiro Inativo",
            slug="barbeiro-inativo",
            specialty="Especialidade fictícia",
            short_description="Barbeiro não publicado.",
            display_order=2,
            is_active=False,
        )

        StoreConfiguration.objects.create(
            name="Barbearia Vintage & Co.",
            slogan="Estilo clássico.",
            presentation_description="Configuração fictícia.",
            whatsapp_number="5521999999999",
            demo_address="Endereço fictício.",
            opening_hours="Horário fictício.",
            banner_text="Banner demonstrativo.",
            primary_button_text="Agendar pelo WhatsApp",
        )

    def setUp(self) -> None:
        """Inicializa um cliente sem autenticação."""
        self.client = APIClient()

    def test_store_publico_retorna_configuracao(self) -> None:
        """Verifica se a configuração pública é retornada."""
        response = self.client.get(
            "/api/v1/public/store/",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["nome_da_barbearia"],
            "Barbearia Vintage & Co.",
        )
        self.assertEqual(
            response.data["numero_whatsapp"],
            "5521999999999",
        )
        self.assertEqual(
            response.data["texto_banner"],
            "Banner demonstrativo.",
        )

    def test_store_nao_configurado_retorna_404(self) -> None:
        """Verifica o retorno quando a configuração ainda não existe."""
        StoreConfiguration.objects.all().delete()

        response = self.client.get(
            "/api/v1/public/store/",
        )

        self.assertEqual(response.status_code, 404)
        self.assertIn("detail", response.data)

    def test_categorias_publicas_mostram_apenas_ativas(self) -> None:
        """Verifica que categorias inativas não são exibidas."""
        response = self.client.get(
            "/api/v1/public/categories/",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertEqual(
            [item["slug"] for item in response.data],
            ["cortes"],
        )

    def test_servicos_publicos_mostram_apenas_publicados(self) -> None:
        """Verifica a regra de publicação dos serviços."""
        response = self.client.get(
            "/api/v1/public/services/",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["count"],
            1,
        )
        self.assertEqual(
            [
                item["slug"]
                for item in response.data["results"]
            ],
            ["corte-vintage"],
        )

    def test_servico_oculto_nao_aparece_no_detalhe(self) -> None:
        """Verifica que serviço oculto retorna 404."""
        response = self.client.get(
            "/api/v1/public/services/servico-oculto/",
        )

        self.assertEqual(response.status_code, 404)

    def test_servico_de_categoria_inativa_nao_aparece(self) -> None:
        """Verifica a regra de publicação da categoria relacionada."""
        response = self.client.get(
            "/api/v1/public/services/servico-categoria-inativa/",
        )

        self.assertEqual(response.status_code, 404)

    def test_detalhe_publico_retorna_preco_decimal(self) -> None:
        """Verifica o detalhe e a serialização decimal do preço."""
        response = self.client.get(
            "/api/v1/public/services/corte-vintage/",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["preco"], "55.00")
        self.assertEqual(
            response.data["descricao_completa"],
            "Descrição completa do corte fictício.",
        )
        self.assertEqual(
            response.data["categoria"]["slug"],
            "cortes",
        )

    def test_busca_por_nome(self) -> None:
        """Verifica a busca pública pelo nome."""
        response = self.client.get(
            "/api/v1/public/services/",
            {"search": "Vintage"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["slug"],
            "corte-vintage",
        )

    def test_busca_por_descricao_curta(self) -> None:
        """Verifica a busca pública pela descrição curta."""
        response = self.client.get(
            "/api/v1/public/services/",
            {"search": "clássico"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_filtro_por_categoria(self) -> None:
        """Verifica o filtro por slug de categoria."""
        active_response = self.client.get(
            "/api/v1/public/services/",
            {"category": "cortes"},
        )

        inactive_response = self.client.get(
            "/api/v1/public/services/",
            {"category": "categoria-inativa"},
        )

        self.assertEqual(active_response.status_code, 200)
        self.assertEqual(active_response.data["count"], 1)
        self.assertEqual(inactive_response.status_code, 200)
        self.assertEqual(inactive_response.data["count"], 0)

    def test_filtro_featured_true(self) -> None:
        """Verifica o filtro de serviços destacados."""
        response = self.client.get(
            "/api/v1/public/services/",
            {"featured": "true"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertTrue(
            response.data["results"][0]["destaque_pagina_inicial"],
        )

    def test_filtro_featured_false_e_rejeitado(self) -> None:
        """Verifica que somente featured=true é aceito."""
        response = self.client.get(
            "/api/v1/public/services/",
            {"featured": "false"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("featured", response.data)

    def test_ordenacao_permitida_por_preco(self) -> None:
        """Verifica uma ordenação autorizada."""
        Service.objects.create(
            category=self.active_category,
            name="Serviço Econômico",
            slug="servico-economico",
            short_description="Serviço mais barato.",
            full_description="Descrição fictícia.",
            price=Decimal("35.00"),
            duration_minutes=25,
            is_featured=False,
            is_published=True,
            display_order=10,
        )

        response = self.client.get(
            "/api/v1/public/services/",
            {"ordering": "price"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [
                item["slug"]
                for item in response.data["results"]
            ],
            [
                "servico-economico",
                "corte-vintage",
            ],
        )

    def test_ordenacao_nao_permitida_e_rejeitada(self) -> None:
        """Verifica que campos arbitrários não podem ordenar a consulta."""
        response = self.client.get(
            "/api/v1/public/services/",
            {"ordering": "created_at"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("ordering", response.data)

    def test_paginacao_publica(self) -> None:
        """Verifica page e page_size na listagem pública."""
        for number in range(13):
            Service.objects.create(
                category=self.active_category,
                name=f"Serviço Demonstrativo {number:02d}",
                slug=f"servico-demonstrativo-{number:02d}",
                short_description="Serviço fictício.",
                full_description="Descrição para paginação.",
                price=Decimal("25.00"),
                duration_minutes=20,
                is_featured=False,
                is_published=True,
                display_order=number + 10,
            )

        first_page = self.client.get(
            "/api/v1/public/services/",
            {
                "page": 1,
                "page_size": 5,
            },
        )

        second_page = self.client.get(
            "/api/v1/public/services/",
            {
                "page": 2,
                "page_size": 5,
            },
        )

        self.assertEqual(first_page.status_code, 200)
        self.assertEqual(second_page.status_code, 200)
        self.assertEqual(first_page.data["count"], 14)
        self.assertEqual(len(first_page.data["results"]), 5)
        self.assertEqual(len(second_page.data["results"]), 5)
        self.assertIsNotNone(first_page.data["next"])
        self.assertIsNotNone(second_page.data["previous"])

    def test_barbeiros_inativos_nao_aparecem(self) -> None:
        """Verifica a visibilidade pública dos barbeiros."""
        list_response = self.client.get(
            "/api/v1/public/barbers/",
        )

        detail_response = self.client.get(
            "/api/v1/public/barbers/barbeiro-inativo/",
        )

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(
            [
                item["slug"]
                for item in list_response.data
            ],
            ["arthur-valenca"],
        )
        self.assertEqual(detail_response.status_code, 404)

    def test_promocoes_elegiveis_aparecem(self) -> None:
        """Verifica as regras de período e publicação das promoções."""
        now = timezone.now()

        Promotion.objects.create(
            title="Promoção Atual",
            description="Promoção fictícia em vigor.",
            linked_service=self.visible_service,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=1),
            is_active=True,
            display_order=1,
        )

        Promotion.objects.create(
            title="Promoção Inativa",
            description="Não deve aparecer.",
            is_active=False,
            display_order=2,
        )

        Promotion.objects.create(
            title="Promoção Futura",
            description="Ainda não começou.",
            start_date=now + timedelta(days=1),
            is_active=True,
            display_order=3,
        )

        Promotion.objects.create(
            title="Promoção Expirada",
            description="Já terminou.",
            end_date=now - timedelta(days=1),
            is_active=True,
            display_order=4,
        )

        Promotion.objects.create(
            title="Promoção Serviço Oculto",
            description="Não deve aparecer.",
            linked_service=self.hidden_service,
            is_active=True,
            display_order=5,
        )

        response = self.client.get(
            "/api/v1/public/promotions/",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["titulo"] for item in response.data],
            ["Promoção Atual"],
        )