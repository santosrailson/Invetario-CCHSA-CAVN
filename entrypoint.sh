#!/bin/sh
set -e

echo "==> Aplicando migrations..."
python manage.py migrate --noinput

echo "==> Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "==> Criando superusuário (se necessário)..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
U = get_user_model()
if not U.objects.filter(username='admin').exists():
    U.objects.create_superuser('admin', 'admin@ifpb.edu.br', 'admin123')
    print('Superusuário criado: admin / admin123')
else:
    print('Superusuário já existe.')
"

echo "==> Iniciando servidor Gunicorn..."
exec gunicorn netinventory.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 300 \
    --access-logfile - \
    --error-logfile -
