FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies if you ever need to build C-extensions (like psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run collectstatic during image build phase
# We provide a dummy SECRET_KEY so Django can initialize settings safely without environmental dependency
RUN DATABASE_URL=sqlite:///:memory: SECRET_KEY=build-time-dummy-key python manage.py collectstatic --noinput

EXPOSE 8000

# Make our entrypoint script executable
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]