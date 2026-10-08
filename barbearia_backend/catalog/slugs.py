"""Geração automática de slugs para os serializers administrativos."""

from __future__ import annotations

from typing import Any

from django.db.models import Model
from django.utils.text import slugify


def generate_unique_slug(
    model: type[Model],
    value: str,
    max_length: int,
) -> str:
    """Gera um slug único para um modelo a partir de um texto.

    O texto é convertido para minúsculas, sem acentos e com hífens. Quando
    o slug já existe, é acrescentado um sufixo numérico (``-2``, ``-3``...),
    respeitando o tamanho máximo do campo.

    Args:
        model: Modelo que possui o campo ``slug`` único.
        value: Texto de origem, normalmente o nome do registro.
        max_length: Tamanho máximo permitido para o slug.

    Returns:
        Slug que ainda não existe no banco de dados.
    """
    base: str = slugify(value or "")[:max_length].strip("-") or "item"
    candidate: str = base
    counter: int = 2

    while model.objects.filter(slug=candidate).exists():
        suffix: str = f"-{counter}"
        trimmed: str = base[: max_length - len(suffix)].rstrip("-")
        candidate = f"{trimmed}{suffix}"
        counter += 1

    return candidate


class AutoSlugMixin:
    """Torna o slug opcional na criação e o gera a partir do nome.

    Deve ser colocado antes de ``serializers.ModelSerializer`` na lista de
    classes base. O slug só é gerado na criação. Na edição, o valor atual é
    mantido para não quebrar URLs já publicadas.
    """

    slug_source: str = "name"

    def get_fields(self) -> dict[str, Any]:
        """Marca o campo ``slug`` como opcional.

        Returns:
            Campos do serializer com ``slug`` não obrigatório.
        """
        fields: dict[str, Any] = super().get_fields()  # type: ignore[misc]
        slug_field = fields.get("slug")

        if slug_field is not None:
            slug_field.required = False

        return fields

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Gera o slug na criação quando ele não foi informado.

        Args:
            attrs: Dados já validados pelos campos do serializer.

        Returns:
            Dados validados, com ``slug`` preenchido na criação.
        """
        attrs = super().validate(attrs)  # type: ignore[misc]

        if self.instance is None and not attrs.get("slug"):  # type: ignore[attr-defined]
            model = self.Meta.model  # type: ignore[attr-defined]
            max_length: int = model._meta.get_field("slug").max_length
            attrs["slug"] = generate_unique_slug(
                model,
                str(attrs.get(self.slug_source, "")),
                max_length,
            )

        return attrs