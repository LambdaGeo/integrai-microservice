#!/bin/bash
set -e

echo "⏳ Aguardando o banco de dados estar disponível..."
until pg_isready -h db -p 5432 -U "$DB_USER"; do
  sleep 1
done
echo "✅ Banco de dados pronto!"

echo "🚀 Executando migrações..."
python manage.py migrate --noinput

echo "🛠 Criando superusuário Django se não existir..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
import os

User = get_user_model()

cpf = os.environ.get('DJANGO_SUPERUSER_CPF')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if cpf and password and not User.objects.filter(username=cpf).exists():
    User.objects.create_superuser(
        username=cpf,
        email=email,
        password=password
    )
    print('Superusuário criado!')
else:
    print('Superusuário já existe ou variáveis faltando.')
"
echo "📦 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "🔥 Iniciando Gunicorn (modo produção)..."
exec gunicorn setup.wsgi:application \
    --bind 0.0.0.0:8001 \
    --workers 3 \
    --timeout 120 \
    --access-logfile '-' \
    --error-logfile '-'
