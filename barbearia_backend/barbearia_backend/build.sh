#!/usr/bin/env bash
# Build do backend no Render. Executado com: bash build.sh
# (rodar com "bash" evita depender do bit de execução; localmente,
#  opcionalmente: git update-index --chmod=+x barbearia_backend/build.sh)
set -o errexit
set -o nounset
set -o pipefail

echo ">> Instalando dependências"
python -m pip install --upgrade pip
pip install -r requirements.txt

echo ">> Validando configuração (falha somente em ERROS)"
python manage.py check --deploy --fail-level ERROR

echo ">> Coletando arquivos estáticos"
python manage.py collectstatic --noinput

echo ">> Aplicando migrations (idempotente)"
python manage.py migrate --noinput

echo ">> Build concluído"