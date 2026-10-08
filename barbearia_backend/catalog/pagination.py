"""Paginação da API pública da Barbearia Vintage & Co."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class CatalogPagination(PageNumberPagination):
    """Implementa a paginação limitada dos serviços públicos.

    A API utiliza os parâmetros:

    - ``page`` para selecionar a página;
    - ``page_size`` para solicitar uma quantidade de itens.

    O tamanho padrão e o limite máximo são obtidos das configurações do
    projeto. O limite máximo impede que um cliente solicite uma quantidade
    excessiva de registros em uma única resposta.
    """

    page_query_param: str = "page"
    page_size_query_param: str = "page_size"
    page_size: int = int(
        getattr(settings, "DEFAULT_PAGE_SIZE", 12)
    )
    max_page_size: int = int(
        getattr(settings, "MAX_PAGE_SIZE", 50)
    )

    def get_paginated_response(
        self,
        data: Any,
    ) -> Any:
        """Retorna o envelope padrão de paginação da API.

        O formato da resposta será:

        ``count``
            Quantidade total de registros encontrados.

        ``next``
            URL da próxima página ou ``null``.

        ``previous``
            URL da página anterior ou ``null``.

        ``results``
            Registros da página atual.

        Args:
            data: Dados serializados da página atual.

        Returns:
            Resposta paginada do Django REST Framework.
        """
        return super().get_paginated_response(data)