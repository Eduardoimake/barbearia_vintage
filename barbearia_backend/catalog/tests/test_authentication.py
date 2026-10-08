"""Testes de sessão, login, CSRF, usuário atual e logout."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


class AuthenticationTests(TestCase):
    """Testa o ciclo de autenticação administrativa."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Cria usuários de teste."""
        user_model = get_user_model()

        cls.staff = user_model.objects.create_user(
            username="administrador_teste",
            password="SenhaDeTesteForte-456!",
            is_staff=True,
        )

        cls.common_user = user_model.objects.create_user(
            username="usuario_comum_teste",
            password="SenhaDeTesteForte-456!",
            is_staff=False,
        )

    def setUp(self):
        """Inicializa cliente com CSRF e respostas HTTP de erro."""
        self.client = APIClient(
            enforce_csrf_checks=True,
        )
        self.client.raise_request_exception = False

    def get_csrf_token(self) -> str:
        """Obtém um token CSRF pelo endpoint oficial.

        Returns:
            Token CSRF retornado pela API.
        """
        response = self.client.get(
            "/api/v1/auth/csrf/",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("csrfToken", response.data)
        self.assertIn("csrftoken", self.client.cookies)

        return str(response.data["csrfToken"])

    def login_staff(self) -> str:
        """Realiza login do usuário staff com CSRF.

        Returns:
            Novo token CSRF devolvido após o login.
        """
        csrf_token = self.get_csrf_token()

        response = self.client.post(
            "/api/v1/auth/login/",
            {
                "username": "administrador_teste",
                "password": "SenhaDeTesteForte-456!",
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn("sessionid", self.client.cookies)
        self.assertTrue(response.data["user"]["is_staff"])
        self.assertIn("csrfToken", response.data)

        return str(response.data["csrfToken"])

    def test_csrf_pode_ser_obtido(self) -> None:
        """Verifica a inicialização do token CSRF."""
        self.get_csrf_token()

    def test_login_sem_csrf_e_rejeitado(self) -> None:
        """Verifica que o login não pode ignorar CSRF."""
        self.get_csrf_token()

        response = self.client.post(
            "/api/v1/auth/login/",
            {
                "username": "administrador_teste",
                "password": "SenhaDeTesteForte-456!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertNotIn("sessionid", self.client.cookies)

    def test_login_com_credenciais_invalidas_retorna_403(self) -> None:
        """Verifica a rejeição de senha incorreta."""
        csrf_token = self.get_csrf_token()

        response = self.client.post(
            "/api/v1/auth/login/",
            {
                "username": "administrador_teste",
                "password": "senha-incorreta",
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 403)

    def test_login_de_usuario_comum_retorna_403(self) -> None:
        """Verifica que usuário sem staff não obtém sessão administrativa."""
        csrf_token = self.get_csrf_token()

        response = self.client.post(
            "/api/v1/auth/login/",
            {
                "username": "usuario_comum_teste",
                "password": "SenhaDeTesteForte-456!",
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 403)
        self.assertNotIn("sessionid", self.client.cookies)

    def test_me_retorna_usuario_staff(self) -> None:
        """Verifica o endpoint do usuário autenticado."""
        self.login_staff()

        response = self.client.get(
            "/api/v1/auth/me/",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["username"],
            "administrador_teste",
        )
        self.assertTrue(response.data["is_staff"])

    def test_me_rejeita_usuario_anonymous(self) -> None:
        """Verifica o bloqueio do endpoint me."""
        response = self.client.get(
            "/api/v1/auth/me/",
        )

        self.assertEqual(response.status_code, 403)

    def test_logout_exige_csrf(self) -> None:
        """Verifica que logout sem CSRF é rejeitado."""
        self.login_staff()

        response = self.client.post(
            "/api/v1/auth/logout/",
        )

        self.assertEqual(response.status_code, 403)

    def test_logout_encera_sessao(self) -> None:
        """Verifica o encerramento correto da sessão."""
        csrf_token = self.login_staff()

        response = self.client.post(
            "/api/v1/auth/logout/",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 204)

        me_response = self.client.get(
            "/api/v1/auth/me/",
        )

        self.assertEqual(me_response.status_code, 403)