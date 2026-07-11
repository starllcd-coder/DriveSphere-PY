FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY web/requirements /app/requirements
RUN pip install --no-cache-dir -r /app/requirements/base.txt

COPY web /app
COPY infra /app/infra

RUN mkdir -p /vol/static /vol/media

EXPOSE 8000

CMD ["gunicorn", "-c", "/app/infra/gunicorn/gunicorn.conf.py", "config.wsgi:application"]
