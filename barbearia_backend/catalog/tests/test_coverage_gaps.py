"""Testes que cobrem lacunas da suíte: CSRF em escritas, upload e exclusões."""

from __future__ import annotations

import io
import os

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from catalog.models import Barber, Promotion, ServiceCategory


class AdminCsrfWriteTests(TestCase):
    """Garante que escritas administrativas exigem o token CSRF."""

    def setUp(self) -> None:
        """Cria um administrador e um cliente com checagem de CSRF ativa."""
        self.password = "senha-de-teste-forte-123"
        get_user_model().objects.create_user(
            username="admin_csrf",
            password=self.password,
            is_staff=True,
        )
        self.client = APIClient(enforce_csrf_checks=True)

    def login(self) -> str:
        """Executa o fluxo real: obtém o CSRF e faz login.

        Returns:
            Token CSRF renovado devolvido pelo login.
        """
        token = self.client.get("/api/v1/auth/csrf/").json()["csrfToken"]
        response = self.client.post(
            "/api/v1/auth/login/",
            {"username": "admin_csrf", "password": self.password},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["csrfToken"]

    def test_admin_post_without_csrf_is_rejected(self) -> None:
        """POST administrativo autenticado sem token CSRF retorna 403."""
        self.login()

        response = self.client.post(
            "/api/v1/admin/categories/",
            {"nome": "Sem CSRF"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(ServiceCategory.objects.count(), 0)

    def test_admin_post_with_csrf_is_accepted(self) -> None:
        """POST administrativo com token CSRF válido retorna 201."""
        token = self.login()

        response = self.client.post(
            "/api/v1/admin/categories/",
            {"nome": "Com CSRF"},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(ServiceCategory.objects.count(), 1)

    def test_admin_patch_and_delete_require_csrf(self) -> None:
        """PATCH e DELETE exigem CSRF e funcionam quando ele é enviado."""
        category = ServiceCategory.objects.create(
            name="Original",
            slug="original",
        )
        url = f"/api/v1/admin/categories/{category.pk}/"
        token = self.login()

        patch_without = self.client.patch(
            url,
            {"nome": "Alterada"},
            format="json",
        )
        self.assertEqual(patch_without.status_code, 403)

        patch_with = self.client.patch(
            url,
            {"nome": "Alterada"},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(patch_with.status_code, 200)

        delete_without = self.client.delete(url)
        self.assertEqual(delete_without.status_code, 403)
        self.assertTrue(
            ServiceCategory.objects.filter(pk=category.pk).exists()
        )

        delete_with = self.client.delete(url, HTTP_X_CSRFTOKEN=token)
        self.assertEqual(delete_with.status_code, 204)
        self.assertFalse(
            ServiceCategory.objects.filter(pk=category.pk).exists()
        )


class CoverageGapTests(TestCase):
    """Cobre barbeiro inativo no detalhe, limite de upload e exclusões."""

    def setUp(self) -> None:
        """Cria um administrador autenticado por sessão simulada."""
        admin = get_user_model().objects.create_user(
            username="admin_lacunas",
            password="senha-de-teste-forte-123",
            is_staff=True,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=admin)

    def test_inactive_barber_detail_returns_404(self) -> None:
        """O detalhe público de barbeiro inativo retorna 404."""
        Barber.objects.create(
            name="Barbeiro Inativo",
            slug="barbeiro-inativo",
            specialty="Cortes",
            short_description="Descrição de teste.",
            is_active=False,
        )

        response = APIClient().get(
            "/api/v1/public/barbers/barbeiro-inativo/"
        )

        self.assertEqual(response.status_code, 404)

    @override_settings(MAX_UPLOAD_SIZE=1024)
    def test_image_above_size_limit_is_rejected(self) -> None:
        """Imagem válida acima do limite configurado retorna 400."""
        image = Image.frombytes(
            "RGB",
            (64, 64),
            os.urandom(64 * 64 * 3),
        )
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        upload = SimpleUploadedFile(
            "foto.png",
            buffer.getvalue(),
            content_type="image/png",
        )

        response = self.client.post(
            "/api/v1/admin/barbers/",
            {
                "nome": "Barbeiro Com Foto",
                "especialidade": "Cortes",
                "descricao_curta": "Descrição de teste.",
                "foto_principal": upload,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("foto_principal", response.json())
        self.assertIn(
            "tamanho",
            " ".join(response.json()["foto_principal"]).lower(),
        )

    def test_delete_category_barber_and_promotion(self) -> None:
        """Registros sem vínculos podem ser excluídos com 204."""
        category = ServiceCategory.objects.create(
            name="Categoria Livre",
            slug="categoria-livre",
        )
        barber = Barber.objects.create(
            name="Barbeiro Livre",
            slug="barbeiro-livre",
            specialty="Cortes",
            short_description="Descrição de teste.",
        )
        promotion = Promotion.objects.create(
            title="Promoção Livre",
            description="Descrição de teste.",
        )

        for url in (
            f"/api/v1/admin/categories/{category.pk}/",
            f"/api/v1/admin/barbers/{barber.pk}/",
            f"/api/v1/admin/promotions/{promotion.pk}/",
        ):
            response = self.client.delete(url)
            self.assertEqual(response.status_code, 204)

        self.assertEqual(ServiceCategory.objects.count(), 0)
        self.assertEqual(Barber.objects.count(), 0)
        self.assertEqual(Promotion.objects.count(), 0)