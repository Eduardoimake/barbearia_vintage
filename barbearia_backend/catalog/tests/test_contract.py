"""Testes que comparam as chaves do JSON com o contrato da API."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from catalog.models import Promotion, StoreConfiguration


PUBLIC_PROMOTION_KEYS: set[str] = {
    "id",
    "titulo",
    "descricao",
    "imagem",
    "servico_vinculado",
    "data_inicio",
    "data_fim",
    "ativa",
    "ordem_exibicao",
}

ADMIN_PROMOTION_KEYS: set[str] = {
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
}

ADMIN_STORE_KEYS: set[str] = {
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
}


class ContractKeysTests(TestCase):
    """Garante que o JSON da API usa exatamente as chaves do contrato."""

    def setUp(self) -> None:
        """Cria um administrador, um cliente autenticado e dados mínimos."""
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            username="admin_contrato",
            password="senha-de-teste-forte-123",
            is_staff=True,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

        self.store = StoreConfiguration.objects.create(
            name="Barbearia de Teste",
            slogan="Slogan de teste.",
            presentation_description="Descrição de teste.",
            whatsapp_number="5521999999999",
            demo_address="Endereço fictício.",
            opening_hours="Horário fictício.",
            banner_text="Banner de teste.",
        )
        self.promotion = Promotion.objects.create(
            title="Promoção de teste",
            description="Descrição da promoção de teste.",
        )

    def test_public_promotion_has_contract_keys(self) -> None:
        """A promoção pública inclui o campo ``ativa`` do contrato."""
        response = APIClient().get("/api/v1/public/promotions/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(
            set(response.json()[0].keys()),
            PUBLIC_PROMOTION_KEYS,
        )
        self.assertTrue(response.json()[0]["ativa"])

    def test_admin_promotion_has_contract_keys(self) -> None:
        """A promoção administrativa usa data_criacao e data_atualizacao."""
        response = self.client.get(
            f"/api/v1/admin/promotions/{self.promotion.pk}/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.json().keys()),
            ADMIN_PROMOTION_KEYS,
        )

    def test_admin_store_has_contract_keys(self) -> None:
        """A loja administrativa usa data_criacao e data_atualizacao."""
        response = self.client.get("/api/v1/admin/store/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.json().keys()),
            ADMIN_STORE_KEYS,
        )

    def test_promotion_creation_requires_title_and_description(self) -> None:
        """Criar promoção sem título ou descrição retorna 400 por campo."""
        response = self.client.post(
            "/api/v1/admin/promotions/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("titulo", response.json())
        self.assertIn("descricao", response.json())

    def test_promotion_creation_without_title_only(self) -> None:
        """Faltando só o título, o erro aponta somente para ele."""
        response = self.client.post(
            "/api/v1/admin/promotions/",
            {"descricao": "Apenas descrição."},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("titulo", response.json())
        self.assertNotIn("descricao", response.json())

    def test_promotion_creation_with_required_fields(self) -> None:
        """Com título e descrição, a criação retorna 201."""
        response = self.client.post(
            "/api/v1/admin/promotions/",
            {"titulo": "Nova promoção", "descricao": "Texto da promoção."},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            set(response.json().keys()),
            ADMIN_PROMOTION_KEYS,
        )

    def test_promotion_partial_update_keeps_fields_optional(self) -> None:
        """No PATCH, título e descrição continuam opcionais."""
        response = self.client.patch(
            f"/api/v1/admin/promotions/{self.promotion.pk}/",
            {"ativa": False},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["ativa"])
        self.assertEqual(response.json()["titulo"], "Promoção de teste")