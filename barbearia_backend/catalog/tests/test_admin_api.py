"""Testes das operações administrativas da API."""

from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from catalog.models import (
    Barber,
    Promotion,
    Service,
    ServiceCategory,
    StoreConfiguration,
)


class AdminAPITests(TestCase):
    """Testa autenticação administrativa e operações CRUD."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Cria usuários e entidades iniciais dos testes administrativos."""
        user_model = get_user_model()

        cls.staff = user_model.objects.create_user(
            username="gestor_teste",
            password="SenhaDeTesteForte-456!",
            is_staff=True,
        )

        cls.common_user = user_model.objects.create_user(
            username="usuario_comum_teste",
            password="SenhaDeTesteForte-456!",
            is_staff=False,
        )

        cls.category = ServiceCategory.objects.create(
            name="Cortes",
            slug="cortes-admin",
            short_description="Categoria fictícia.",
            is_active=True,
        )

        cls.store = StoreConfiguration.objects.create(
            name="Barbearia Vintage & Co.",
            slogan="Slogan fictício.",
            presentation_description="Descrição fictícia.",
            whatsapp_number="5521999999999",
            demo_address="Endereço fictício.",
            opening_hours="Horário fictício.",
            banner_text="Banner inicial.",
            primary_button_text="Agendar pelo WhatsApp",
        )

    def setUp(self):
        """Inicializa cliente administrativo."""
        self.client = APIClient()
        self.client.raise_request_exception = False

    def login_staff(self) -> None:
        """Autentica o cliente diretamente para testes autorizados."""
        self.client.force_login(self.staff)

    def service_payload(
        self,
        **overrides: object,
    ) -> dict[str, object]:
        """Monta dados válidos para criação de serviço.

        Args:
            **overrides: Campos que substituirão os valores padrão.

        Returns:
            Payload administrativo de serviço.
        """
        payload: dict[str, object] = {
            "categoria": self.category.pk,
            "nome": "Serviço Demonstrativo",
            "slug": "servico-demonstrativo",
            "descricao_curta": "Serviço fictício.",
            "descricao_completa": "Descrição completa fictícia.",
            "preco": "75.00",
            "duracao_minutos": 45,
            "status_published": True,
            "destaque_pagina_inicial": False,
            "ordem_exibicao": 1,
        }

        payload.update(overrides)

        return payload

    def test_anonymous_nao_acessa_rotas_administrativas(self) -> None:
        """Verifica o bloqueio de visitante."""
        response = self.client.get(
            "/api/v1/admin/services/",
        )

        self.assertEqual(response.status_code, 403)

    def test_usuario_comum_nao_acessa_rotas_administrativas(self) -> None:
        """Verifica o bloqueio de usuário sem staff."""
        self.client.force_login(self.common_user)

        response = self.client.get(
            "/api/v1/admin/services/",
        )

        self.assertEqual(response.status_code, 403)

    def test_anonymous_nao_cria_servico(self) -> None:
        """Verifica o bloqueio de escrita para visitante."""
        response = self.client.post(
            "/api/v1/admin/services/",
            self.service_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Service.objects.count(), 0)

    def test_staff_cria_servico(self) -> None:
        """Verifica a criação administrativa de serviço."""
        self.login_staff()

        response = self.client.post(
            "/api/v1/admin/services/",
            self.service_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["preco"], "75.00")
        self.assertTrue(
            Service.objects.filter(
                slug="servico-demonstrativo",
            ).exists()
        )

    def test_servico_criado_aparece_publicamente(self) -> None:
        """Verifica que serviço publicado fica visível na API pública."""
        self.login_staff()

        self.client.post(
            "/api/v1/admin/services/",
            self.service_payload(),
            format="json",
        )

        response = self.client.get(
            "/api/v1/public/services/",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["slug"],
            "servico-demonstrativo",
        )

    def test_staff_edita_e_oculta_servico(self) -> None:
        """Verifica edição e mudança de publicação."""
        service = Service.objects.create(
            category=self.category,
            name="Serviço Original",
            slug="servico-original",
            short_description="Descrição original.",
            full_description="Detalhes originais.",
            price=Decimal("60.00"),
            duration_minutes=30,
            is_published=True,
        )

        self.login_staff()

        detail_url = (
            f"/api/v1/admin/services/{service.pk}/"
        )

        update_response = self.client.patch(
            detail_url,
            {
                "nome": "Serviço Editado",
                "preco": "80.00",
            },
            format="json",
        )

        hide_response = self.client.patch(
            detail_url,
            {
                "status_published": False,
            },
            format="json",
        )

        public_response = self.client.get(
            "/api/v1/public/services/servico-original/",
        )

        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.data["preco"], "80.00")
        self.assertEqual(hide_response.status_code, 200)
        self.assertEqual(public_response.status_code, 404)

    def test_staff_exclui_servico(self) -> None:
        """Verifica exclusão administrativa de serviço."""
        service = Service.objects.create(
            category=self.category,
            name="Serviço Excluível",
            slug="servico-excluivel",
            short_description="Descrição fictícia.",
            full_description="Detalhes fictícios.",
            price=Decimal("30.00"),
            duration_minutes=20,
            is_published=False,
        )

        self.login_staff()

        response = self.client.delete(
            f"/api/v1/admin/services/{service.pk}/",
        )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            Service.objects.filter(pk=service.pk).exists()
        )

    def test_categoria_com_servico_retorna_409(self) -> None:
        """Verifica a proteção contra exclusão de categoria vinculada."""
        Service.objects.create(
            category=self.category,
            name="Serviço Vinculado",
            slug="servico-vinculado",
            short_description="Descrição fictícia.",
            full_description="Detalhes fictícios.",
            price=Decimal("30.00"),
            duration_minutes=20,
        )

        self.login_staff()

        response = self.client.delete(
            f"/api/v1/admin/categories/{self.category.pk}/",
        )

        self.assertEqual(response.status_code, 409)
        self.assertIn("detail", response.data)
        self.assertTrue(
            ServiceCategory.objects.filter(
                pk=self.category.pk,
            ).exists()
        )

    def test_dashboard_retorna_contagens_reais(self) -> None:
        """Verifica o dashboard sem métricas inventadas."""
        Barber.objects.create(
            name="Barbeiro Fictício",
            slug="barbeiro-ficticio",
            specialty="Especialidade fictícia",
            short_description="Descrição fictícia.",
            is_active=True,
        )

        self.login_staff()

        response = self.client.get(
            "/api/v1/admin/dashboard/",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["categories_count"], 1)
        self.assertEqual(response.data["barbers_count"], 1)
        self.assertNotIn("sales", response.data)
        self.assertNotIn("revenue", response.data)

    def test_staff_atualiza_store(self) -> None:
        """Verifica a edição da configuração única."""
        self.login_staff()

        response = self.client.patch(
            "/api/v1/admin/store/",
            {
                "texto_banner": "Banner atualizado.",
            },
            format="json",
        )

        public_response = self.client.get(
            "/api/v1/public/store/",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(public_response.status_code, 200)
        self.assertEqual(
            public_response.data["texto_banner"],
            "Banner atualizado.",
        )

    def test_staff_cria_e_edita_barbeiro(self) -> None:
        """Verifica o CRUD básico de barbeiros."""
        self.login_staff()

        created = self.client.post(
            "/api/v1/admin/barbers/",
            {
                "nome": "Barbeiro Novo",
                "slug": "barbeiro-novo",
                "especialidade": "Cortes demonstrativos",
                "descricao_curta": "Perfil fictício.",
                "ativo": True,
                "ordem_exibicao": 1,
            },
            format="json",
        )

        self.assertEqual(created.status_code, 201, created.data)

        updated = self.client.patch(
            f"/api/v1/admin/barbers/{created.data['id']}/",
            {
                "ativo": False,
            },
            format="json",
        )

        self.assertEqual(updated.status_code, 200)
        self.assertFalse(updated.data["ativo"])

    def test_staff_cria_e_desativa_promocao(self) -> None:
        """Verifica o CRUD básico de promoções."""
        self.login_staff()

        created = self.client.post(
            "/api/v1/admin/promotions/",
            {
                "titulo": "Promoção Demonstrativa",
                "descricao": "Promoção fictícia.",
                "ativa": True,
                "ordem_exibicao": 1,
            },
            format="json",
        )

        self.assertEqual(created.status_code, 201, created.data)

        updated = self.client.patch(
            f"/api/v1/admin/promotions/{created.data['id']}/",
            {
                "ativa": False,
            },
            format="json",
        )

        self.assertEqual(updated.status_code, 200)
        self.assertFalse(updated.data["ativa"])