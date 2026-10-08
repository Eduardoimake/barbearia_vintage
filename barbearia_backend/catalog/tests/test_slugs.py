"""Testes da geração automática de slug nas rotas administrativas."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from catalog.models import ServiceCategory


class AutoSlugTests(TestCase):
    """Verifica a geração, a unicidade e a estabilidade dos slugs."""

    def setUp(self) -> None:
        """Cria um administrador autenticado e uma categoria de apoio."""
        user_model = get_user_model()
        admin = user_model.objects.create_user(
            username="admin_slug",
            password="senha-de-teste-forte-123",
            is_staff=True,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=admin)
        self.category = ServiceCategory.objects.create(
            name="Categoria Base",
            slug="categoria-base",
        )

    def service_payload(self, name: str, **extra: object) -> dict[str, object]:
        """Monta o corpo mínimo para criar um serviço.

        Args:
            name: Nome do serviço.
            **extra: Campos adicionais ou substitutos.

        Returns:
            Dicionário pronto para envio em JSON.
        """
        payload: dict[str, object] = {
            "categoria": self.category.pk,
            "nome": name,
            "descricao_curta": "Descrição curta de teste.",
            "descricao_completa": "Descrição completa de teste.",
            "preco": "55.00",
            "duracao_minutos": 45,
        }
        payload.update(extra)
        return payload

    def test_service_slug_is_generated_without_accents(self) -> None:
        """Serviço sem slug recebe slug gerado, sem acentos."""
        response = self.client.post(
            "/api/v1/admin/services/",
            self.service_payload("Corte Clássico Premium"),
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["slug"], "corte-classico-premium")

    def test_repeated_names_receive_numeric_suffix(self) -> None:
        """Nomes repetidos geram slugs distintos com sufixo numérico."""
        first = self.client.post(
            "/api/v1/admin/services/",
            self.service_payload("Barba Teste"),
            format="json",
        )
        second = self.client.post(
            "/api/v1/admin/services/",
            self.service_payload("Barba Teste"),
            format="json",
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(first.json()["slug"], "barba-teste")
        self.assertEqual(second.json()["slug"], "barba-teste-2")

    def test_provided_slug_is_respected(self) -> None:
        """Um slug informado é mantido exatamente como enviado."""
        response = self.client.post(
            "/api/v1/admin/services/",
            self.service_payload("Qualquer Nome", slug="slug-escolhido"),
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["slug"], "slug-escolhido")

    def test_duplicate_provided_slug_is_rejected(self) -> None:
        """Slug informado que já existe retorna 400 no campo slug."""
        self.client.post(
            "/api/v1/admin/services/",
            self.service_payload("Primeiro", slug="meu-slug"),
            format="json",
        )
        response = self.client.post(
            "/api/v1/admin/services/",
            self.service_payload("Segundo", slug="meu-slug"),
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("slug", response.json())

    def test_patch_name_keeps_slug(self) -> None:
        """Trocar o nome na edição não altera o slug."""
        created = self.client.post(
            "/api/v1/admin/services/",
            self.service_payload("Nome Original"),
            format="json",
        )
        service_id = created.json()["id"]

        response = self.client.patch(
            f"/api/v1/admin/services/{service_id}/",
            {"nome": "Nome Novo"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["nome"], "Nome Novo")
        self.assertEqual(response.json()["slug"], "nome-original")

    def test_category_slug_is_generated(self) -> None:
        """Categoria sem slug recebe slug gerado."""
        response = self.client.post(
            "/api/v1/admin/categories/",
            {"nome": "Tratamentos Especiais"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["slug"], "tratamentos-especiais")

    def test_barber_slug_is_generated(self) -> None:
        """Barbeiro sem slug recebe slug gerado."""
        response = self.client.post(
            "/api/v1/admin/barbers/",
            {
                "nome": "João da Silva",
                "especialidade": "Cortes clássicos",
                "descricao_curta": "Barbeiro de teste.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["slug"], "joao-da-silva")

    def test_symbol_only_name_uses_fallback(self) -> None:
        """Nome sem letras ou números usa o slug base ``item``."""
        response = self.client.post(
            "/api/v1/admin/categories/",
            {"nome": "!!!"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["slug"], "item")

    def test_long_name_respects_slug_max_length(self) -> None:
        """Slugs longos e repetidos continuam dentro do limite do campo."""
        long_name = "b" * 100
        first = self.client.post(
            "/api/v1/admin/categories/",
            {"nome": long_name},
            format="json",
        )
        second = self.client.post(
            "/api/v1/admin/categories/",
            {"nome": long_name},
            format="json",
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertLessEqual(len(first.json()["slug"]), 100)
        self.assertLessEqual(len(second.json()["slug"]), 100)
        self.assertNotEqual(first.json()["slug"], second.json()["slug"])