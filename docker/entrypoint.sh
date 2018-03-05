#!/bin/sh

LOG_LEVEL=${LOG_LEVEL:-"info"}

cd /var/www/ideax

export DJANGO_SETTINGS_MODULE=ideax.settings

if [ ! -f /var/www/ideax/.env ]; then
  echo SECRET_KEY=my_super_secret_key > /var/www/ideax/.env
fi

if [ ! -d /var/www/ideax/static ]; then
  python manage.py collectstatic --no-input
fi

if [ ! -d /run/nginx ]; then
  mkdir /run/nginx
fi

python manage.py migrate

nginx

exec gunicorn ideax.wsgi:application \
    --name ideax_django \
    --bind 0.0.0.0:8000 \
    --workers 5 \
    --log-level=${LOG_LEVEL} \
"$@"
