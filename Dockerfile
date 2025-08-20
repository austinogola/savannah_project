FROM python:3.12-slim

WORKDIR /app

# System deps (psycopg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 gcc && rm -rf /var/lib/apt/lists/*

# Install requirements first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static in the image
# Make sure env vars exist at build time if settings import apps.
# For build-time, we can bypass DB by telling Django DEBUG=True temporarily:
ENV DJANGO_DEBUG=True
RUN python manage.py collectstatic --noinput
ENV DJANGO_DEBUG=False

EXPOSE 8000
CMD ["gunicorn", "savannah_project.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "60"]
