#!/usr/bin/env python
"""Utilitário de linha de comando para tarefas administrativas do Django."""

from __future__ import annotations

import os
import sys
from typing import NoReturn


def main() -> NoReturn:
    """Executa tarefas administrativas do projeto Django.

    Esta função configura o módulo de configurações do projeto e encaminha
    os argumentos recebidos no terminal para o mecanismo de comandos do Django.

    Raises:
        SystemExit: Quando o Django não consegue ser carregado ou quando um
            comando termina solicitando o encerramento do processo.
    """
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        "barbearia_backend.settings",
    )

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Não foi possível importar o Django. "
            "Verifique se as dependências foram instaladas "
            "e se o ambiente virtual está ativado."
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()