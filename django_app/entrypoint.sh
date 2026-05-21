#!/bin/bash
set -e

echo "Aguardando o banco de dados estar disponível..."
until pg_isready -h db -p 5432 -U "$DB_USER"; do
  sleep 1
done
echo "Banco de dados pronto!"

echo "Executando migrações..."
python manage.py migrate --noinput

echo "Superusuário gerenciado pelo users-service."

echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "Iniciando servidor Django..."
exec python manage.py runserver 0.0.0.0:8001
