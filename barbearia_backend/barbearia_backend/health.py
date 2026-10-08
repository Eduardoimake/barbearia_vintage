"""Health check público e leve, usado pelo Render."""

from __future__ import annotations

from django.http import HttpRequest, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe


@require_safe
@never_cache
def health_check(request: HttpRequest) -> JsonResponse:
    """Responde HTTP 200 com {"status": "ok"}, sem consultar o banco."""
    return JsonResponse({"status": "ok"})