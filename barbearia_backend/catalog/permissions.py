"""Permissões da API da Barbearia Vintage & Co."""

from __future__ import annotations

from typing import Any

from rest_framework.permissions import BasePermission


class IsStaffAuthenticated(BasePermission):
    """Permite acesso somente a usuários autenticados que sejam staff.

    Esta permissão é utilizada pelas rotas administrativas da API. O frontend
    não é responsável por garantir a segurança: a verificação é feita no
    backend em todas as requisições protegidas.

    Usuários anônimos são rejeitados. Usuários autenticados sem
    ``is_staff=True`` também são rejeitados.
    """

    message: str = (
        "É necessário estar autenticado como administrador "
        "para acessar este recurso."
    )

    def has_permission(
        self,
        request: Any,
        view: Any,
    ) -> bool:
        """Verifica se o usuário da requisição é um administrador staff.

        Args:
            request: Requisição HTTP atual.
            view: View responsável pelo processamento da requisição.

        Returns:
            ``True`` somente quando o usuário está autenticado, ativo e possui
            ``is_staff=True``.
        """
        del view

        user: Any = getattr(request, "user", None)

        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and user.is_staff
        )