FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies (including GIS libraries for PostGIS support)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        sqlite3 \
        python3-dev \
        build-essential \
        libpq-dev \
        # PostGIS/GIS dependencies
        libgdal-dev \
        libgeos-dev \
        libproj-dev \
        gdal-bin \
        proj-bin \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create data directory for SQLite
RUN mkdir -p /data

# Collect static files
RUN python manage.py collectstatic --noinput --settings=resource_directory.staging_settings

# Expose port
EXPOSE 8000

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "resource_directory.wsgi:application"]
