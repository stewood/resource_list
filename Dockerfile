FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies including GIS libraries
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        sqlite3 \
        # GIS dependencies
        libgdal-dev \
        libgeos-dev \
        libproj-dev \
        libspatialite7 \
        spatialite-bin \
        # Additional dependencies for GDAL Python bindings
        python3-dev \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set GDAL environment variables for Python GDAL bindings
ENV GDAL_CONFIG=/usr/bin/gdal-config
ENV GEOS_CONFIG=/usr/bin/geos-config
ENV PROJ_LIB=/usr/share/proj

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create data directory for SQLite
RUN mkdir -p /data

# Initialize SpatiaLite database if GIS is enabled
RUN spatialite /data/db.sqlite3 "SELECT InitSpatialMetaData(1);" || true

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "resource_directory.wsgi:application"]
