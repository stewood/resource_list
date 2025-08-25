FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=resource_directory.production_settings

# Set work directory
WORKDIR /app

# Install system dependencies (without GIS libraries for production)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        sqlite3 \
        python3-dev \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create data directory for SQLite
RUN mkdir -p /data

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "resource_directory.wsgi:application"]
