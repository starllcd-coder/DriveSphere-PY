FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gettext \
    && rm -rf /var/lib/apt/lists/*

COPY web/requirements /app/requirements
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r /app/requirements/prod.txt

COPY web /app/web

WORKDIR /app/web

CMD python manage.py migrate --settings=config.settings.prod && \
    python manage.py collectstatic --noinput --settings=config.settings.prod && \
    gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
