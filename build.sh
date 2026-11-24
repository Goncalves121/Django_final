#!/usr/bin/env bash
# Script de build do Render
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput

# Cria o administrador se as variáveis DJANGO_SUPERUSER_* estiverem definidas.
# Se ele já existir, o comando falha de forma inofensiva.
if [ -n "$DJANGO_SUPERUSER_USERNAME" ]; then
  python manage.py createsuperuser --noinput || true
fi
