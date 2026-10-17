#!/usr/bin/env bash
# Script de construcción que ejecuta Render en cada despliegue.
# Si cualquier paso falla, el despliegue se detiene y la versión anterior sigue en línea.
set -o errexit

echo "── 1/5 Dependencias de Python"
pip install -r requirements.txt

echo "── 2/5 Frontend: Tailwind, HTMX y React (Vite)"
npm ci --include=dev          # devDependencies incluidas: Vite y Tailwind se necesitan para compilar
npm run css:build
npm run htmx:copiar
npm run build

echo "── 3/5 Estáticos"
python manage.py collectstatic --no-input

echo "── 4/5 Base de datos"
python manage.py migrate --no-input
python manage.py createcachetable

echo "── 5/5 Datos iniciales (solo si se piden)"
# En el plan gratuito de Render no hay consola, así que los datos de demostración y el
# superusuario se crean aquí. Después del primer despliegue: CARGAR_DEMO=False.
if [ "$CARGAR_DEMO" = "True" ]; then
  python manage.py cargar_catalogo_demo
  python manage.py cargar_habitos_demo
fi
if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py createsuperuser --no-input || echo "El superusuario ya existe: no se crea de nuevo."
fi
