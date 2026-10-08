"""Testes de validação de preços, datas, telefone e imagens."""

from __future__ import annotations

import io
from datetime import timedelta
from decimal import Decimal
from typing import Any

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from catalog.models import (
    Promotion,
    Service,
    ServiceCategory,
    StoreConfiguration,
)


class ValidationTests(TestCase):
    """Testa as validações dos serializers administrativos."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Cria dados comuns aos testes de validação."""
        user_model = get_user_model()

        cls.staff = user_model.objects.create_user(
            username="staff_validacao",
            password="SenhaDeTesteForte-456!",
            is_staff=True,
        )

        cls.category = ServiceCategory.objects.create(
            name="Cortes",
            slug="cortes-validacao",
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
            banner_text="Banner fictício.",
            primary_button_text="Agendar pelo WhatsApp",
        )

    def setUp(self):
        """Inicializa cliente autenticado sem repropagar exceções."""
        self.client = APIClient(
            raise_request_exception=False,
        )
        self.client.force_login(self.staff)

    def service_payload(self, **overrides):
        """Retorna payload válido e permite sobrescrever campos."""
        payload = {
            "categoria": self.category.pk,
            "nome": "Serviço de Validação",
            "slug": "servico-de-validacao",
            "descricao_curta": "Serviço fictício.",
            "descricao_completa": "Descrição fictícia.",
            "preco": "50.00",
            "duracao_minutos": 30,
            "destaque_pagina_inicial": False,
            "status_published": True,
            "ordem_exibicao": 0,
        }

        payload.update(overrides)

        return payload

    def make_valid_image(
        self,
        filename: str = "imagem.png",
        image_format: str = "PNG",
    ) -> SimpleUploadedFile:
        """Cria uma imagem válida em memória.

        Args:
            filename: Nome usado no upload.
            image_format: Formato que será gravado pelo Pillow.

        Returns:
            Arquivo carregado em memória.
        """
        image = Image.new(
            "RGB",
            (10, 10),
            color="black",
        )

        buffer = io.BytesIO()
        image.save(buffer, format=image_format)
        buffer.seek(0)

        return SimpleUploadedFile(
            name=filename,
            content=buffer.getvalue(),
            content_type=f"image/{image_format.lower()}",
        )

    def make_invalid_image(self) -> SimpleUploadedFile:
        """Cria arquivo com extensão de imagem, mas conteúdo inválido.

        Returns:
            Arquivo que deve ser rejeitado pelo Pillow.
        """
        return SimpleUploadedFile(
            name="imagem.jpg",
            content=b"isto nao e uma imagem",
            content_type="image/jpeg",
        )

    def test_preco_negativo_e_rejeitado(self) -> None:
        """Verifica que preço negativo não é salvo."""
        response = self.client.post(
            "/api/v1/admin/services/",
            self.service_payload(
                preco="-0.01",
            ),
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("preco", response.data)
        self.assertFalse(
            Service.objects.filter(
                slug="servico-de-validacao",
            ).exists()
        )

    def test_duracao_zero_e_rejeitada(self) -> None:
        """Verifica que duração zero é inválida."""
        response = self.client.post(
            "/api/v1/admin/services/",
            self.service_payload(
                duracao_minutos=0,
            ),
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("duracao_minutos", response.data)

    def test_whatsapp_invalido_e_rejeitado(self) -> None:
        """Verifica o formato internacional do WhatsApp."""
        response = self.client.patch(
            "/api/v1/admin/store/",
            {
                "numero_whatsapp": "55 (21) 99999-9999",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("numero_whatsapp", response.data)

        self.store.refresh_from_db()
        self.assertEqual(
            self.store.whatsapp_number,
            "5521999999999",
        )

    def test_imagem_invalida_e_rejeitada(self) -> None:
        """Verifica validação real do conteúdo da imagem."""
        payload = self.service_payload()
        payload["imagem_principal"] = self.make_invalid_image()

        response = self.client.post(
            "/api/v1/admin/services/",
            payload,
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("imagem_principal", response.data)

    def test_imagem_valida_e_aceita(self) -> None:
        """Verifica o upload de uma imagem válida."""
        payload = self.service_payload()
        payload["imagem_principal"] = self.make_valid_image()

        response = self.client.post(
            "/api/v1/admin/services/",
            payload,
            format="multipart",
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertIsNotNone(response.data["imagem_principal"])

        service = Service.objects.get(
            slug="servico-de-validacao",
        )

        self.assertTrue(service.main_image.name.startswith("services/"))

    def test_promocao_com_fim_antes_do_inicio_e_rejeitada(self) -> None:
        """Verifica a validação de intervalo de promoção."""
        current_time = timezone.now()

        response = self.client.post(
            "/api/v1/admin/promotions/",
            {
                "titulo": "Promoção inválida",
                "descricao": "Intervalo inválido.",
                "data_inicio": (
                    current_time + timedelta(days=5)
                ).isoformat(),
                "data_fim": (
                    current_time + timedelta(days=1)
                ).isoformat(),
                "ativa": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("data_fim", response.data)
        self.assertFalse(
            Promotion.objects.filter(
                title="Promoção inválida",
            ).exists()
        )

    def test_preco_decimal_nao_e_float(self) -> None:
        """Verifica que o preço persistido continua sendo Decimal."""
        response = self.client.post(
            "/api/v1/admin/services/",
            self.service_payload(
                slug="servico-decimal",
                preco="39.90",
            ),
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        service = Service.objects.get(
            slug="servico-decimal",
        )

        self.assertIsInstance(service.price, Decimal)
        self.assertEqual(service.price, Decimal("39.90"))