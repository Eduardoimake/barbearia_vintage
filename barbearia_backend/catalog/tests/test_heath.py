"""Testes da rota de health check."""

from django.test import SimpleTestCase


class HealthCheckTests(SimpleTestCase):
    """Garante o contrato público de GET /health/."""

    def test_health_retorna_ok(self) -> None:
        resposta = self.client.get("/health/")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json(), {"status": "ok"})

    def test_health_rejeita_post(self) -> None:
        self.assertEqual(self.client.post("/health/").status_code, 405)