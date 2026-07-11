FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY web/requirements /app/requirements
RUN pip install --no-cache-dir -r /app/requirements/base.txt

COPY web /app

CMD ["celery", "-A", "config", "worker", "-l", "info"]
