"""Validadores reutilizáveis da aplicação de catálogo.

Este módulo concentra regras de validação que precisam ser aplicadas em
modelos, serializers e campos de upload.

As validações de imagem não confiam somente na extensão do arquivo ou no
cabeçalho Content-Type. O conteúdo é aberto pelo Pillow para confirmar que
o arquivo é realmente uma imagem válida.
"""

from __future__ import annotations

import os
import uuid
import re
from decimal import Decimal
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from rest_framework import serializers
from PIL import Image, UnidentifiedImageError


def validate_non_negative_price(value: Decimal) -> None:
    """Valida se um preço é maior ou igual a zero.

    Args:
        value: Valor decimal que representa o preço.

    Raises:
        ValidationError: Caso o valor seja negativo.
    """
    if value < Decimal("0.00"):
        raise ValidationError(
            "O preço não pode ser negativo."
        )


def validate_positive_duration(value: int) -> None:
    """Valida se a duração de um serviço é positiva.

    Args:
        value: Duração do serviço em minutos.

    Raises:
        ValidationError: Caso a duração seja menor ou igual a zero.
    """
    if value <= 0:
        raise ValidationError(
            "A duração deve ser maior que zero minuto."
        )



def validate_whatsapp_input(value):
    """Valida WhatsApp antes de aplicar outras regras."""
    if not isinstance(value, str):
        raise serializers.ValidationError(
            "Informe o WhatsApp como texto."
        )

    if not re.fullmatch(r"[1-9][0-9]{9,14}", value):
        raise serializers.ValidationError(
            (
                "Informe o WhatsApp com 10 a 15 dígitos, "
                "sem espaços, sinais ou pontuação."
            )
        )

    return value


def validate_whatsapp_number(value: str) -> None:
    """Valida um número de WhatsApp no formato internacional simplificado.

    O formato aceito possui de 10 a 15 dígitos, sem sinal de mais, espaços,
    parênteses, hífens ou qualquer outro caractere.

    Exemplos aceitos:

    - ``5521999999999``
    - ``5511999999999``

    Exemplos rejeitados:

    - ``+5521999999999``
    - ``(21) 99999-9999``
    - ``552199999999``

    Args:
        value: Número textual a ser validado.

    Raises:
        ValidationError: Caso o valor não tenha entre 10 e 15 dígitos.
    """
    if not value.isdigit() or not 10 <= len(value) <= 15:
        raise ValidationError(
            "O número de WhatsApp deve conter de 10 a 15 dígitos, "
            "sem sinal de mais, espaços ou pontuação."
        )


def validate_date_range(
    start_date: Any,
    end_date: Any,
) -> None:
    """Valida a coerência entre uma data inicial e uma data final.

    Datas nulas são permitidas. Quando as duas datas existem, a data final
    deve ser maior ou igual à data inicial.

    Args:
        start_date: Data inicial da promoção.
        end_date: Data final da promoção.

    Raises:
        ValidationError: Caso a data final seja anterior à data inicial.
    """
    if (
        start_date is not None
        and end_date is not None
        and end_date < start_date
    ):
        raise ValidationError(
            "A data final não pode ser anterior à data inicial."
        )


def get_allowed_image_extensions() -> tuple[str, ...]:
    """Retorna as extensões de imagem permitidas pela configuração.

    Returns:
        Tupla com extensões sem ponto e em letras minúsculas.
    """
    configured_extensions: tuple[str, ...] = tuple(
        extension.lower().lstrip(".")
        for extension in getattr(
            settings,
            "ALLOWED_IMAGE_EXTENSIONS",
            ("jpg", "jpeg", "png", "webp"),
        )
    )

    return configured_extensions


def get_max_upload_size() -> int:
    """Retorna o limite máximo configurado para arquivos enviados.

    Returns:
        Limite em bytes.
    """
    return int(
        getattr(
            settings,
            "MAX_UPLOAD_SIZE",
            5 * 1024 * 1024,
        )
    )


def validate_uploaded_image(uploaded_file: UploadedFile | None) -> None:
    """Valida um arquivo de imagem enviado pelo usuário.

    A validação verifica:

    - existência do arquivo;
    - tamanho máximo;
    - extensão permitida;
    - leitura real do conteúdo pelo Pillow;
    - formato detectado pelo conteúdo;
    - confirmação de que a imagem pode ser aberta e verificada.

    A extensão e o Content-Type não são considerados suficientes para
    confirmar que um arquivo é uma imagem válida.

    Args:
        uploaded_file: Arquivo recebido pela API.

    Raises:
        ValidationError: Caso o arquivo seja inválido, exceda o tamanho
            permitido ou não pertença a um formato aceito.
    """
    if uploaded_file is None:
        return

    if not isinstance(uploaded_file, UploadedFile):
        raise ValidationError(
            "O arquivo enviado não possui um formato de upload válido."
        )

    max_size: int = get_max_upload_size()

    if uploaded_file.size is None:
        raise ValidationError(
            "Não foi possível determinar o tamanho da imagem."
        )

    if uploaded_file.size > max_size:
        max_size_megabytes: float = max_size / (1024 * 1024)
        raise ValidationError(
            "A imagem excede o tamanho máximo permitido de "
            f"{max_size_megabytes:.2f} MB."
        )

    filename: str = uploaded_file.name or ""
    extension: str = Path(filename).suffix.lower().lstrip(".")

    if extension not in get_allowed_image_extensions():
        allowed_extensions: str = ", ".join(
            get_allowed_image_extensions()
        )
        raise ValidationError(
            "Formato de imagem não permitido. "
            f"Formatos aceitos: {allowed_extensions}."
        )

    try:
        uploaded_file.seek(0)

        with Image.open(uploaded_file) as image:
            detected_format: str = (image.format or "").lower()
            image.verify()

        allowed_formats: set[str] = {
            "jpg",
            "jpeg",
            "png",
            "webp",
        }

        if detected_format not in allowed_formats:
            raise ValidationError(
                "O conteúdo da imagem não possui um formato permitido."
            )

    except (UnidentifiedImageError, OSError, SyntaxError) as exc:
        raise ValidationError(
            "O arquivo enviado não é uma imagem válida."
        ) from exc
    finally:
        uploaded_file.seek(0)


def image_upload_path(
    folder: str,
    filename: str,
) -> str:
    """Gera um caminho de upload com nome aleatório e seguro.

    O nome original não é preservado para evitar colisões, sobrescrita
    acidental e possíveis problemas causados por nomes controlados pelo
    usuário.

    Args:
        folder: Pasta lógica do tipo de imagem.
        filename: Nome original do arquivo enviado.

    Returns:
        Caminho relativo para armazenamento da imagem.
    """
    original_extension: str = Path(filename).suffix.lower()

    if not original_extension:
        original_extension = ".bin"

    safe_extension: str = "".join(
        character
        for character in original_extension
        if character.isalnum() or character == "."
    )

    unique_name: str = f"{uuid.uuid4()}{safe_extension}"

    return os.path.join(folder, unique_name)


def service_image_upload_path(
    instance: Any,
    filename: str,
) -> str:
    """Gera o caminho de upload de uma imagem de serviço.

    Args:
        instance: Instância do modelo Serviço.
        filename: Nome original do arquivo.
    
    Returns:
        Caminho relativo dentro da pasta ``services``.
    """
    del instance
    return image_upload_path("services", filename)


def barber_image_upload_path(
    instance: Any,
    filename: str,
) -> str:
    """Gera o caminho de upload de uma foto de barbeiro.

    Args:
        instance: Instância do modelo Barbeiro.
        filename: Nome original do arquivo.
    
    Returns:
        Caminho relativo dentro da pasta ``barbers``.
    """
    del instance
    return image_upload_path("barbers", filename)


def store_image_upload_path(
    instance: Any,
    filename: str,
) -> str:
    """Gera o caminho de upload da imagem de capa da loja.

    Args:
        instance: Instância do modelo Configuração da Barbearia.
        filename: Nome original do arquivo.
    
    Returns:
        Caminho relativo dentro da pasta ``store``.
    """
    del instance
    return image_upload_path("store", filename)


def promotion_image_upload_path(
    instance: Any,
    filename: str,
) -> str:
    """Gera o caminho de upload de uma imagem promocional.

    Args:
        instance: Instância do modelo Promoção.
        filename: Nome original do arquivo.
    
    Returns:
        Caminho relativo dentro da pasta ``promotions``.
    """
    del instance
    return image_upload_path("promotions", filename)