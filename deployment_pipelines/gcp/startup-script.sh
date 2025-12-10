#!/bin/bash
set -e

echo "=== VM Startup Script ==="
echo "Starting at: $(date)"

# Install Docker
echo "Installing Docker..."
apt-get update -qq
apt-get install -y docker.io

# Start and enable Docker
echo "Starting Docker service..."
systemctl start docker
systemctl enable docker

# Configure authentication for Artifact Registry
echo "Configuring Artifact Registry authentication..."
gcloud auth configure-docker europe-west3-docker.pkg.dev --quiet

# Pull the PostGIS image
echo "Pulling PostGIS image..."
docker pull europe-west3-docker.pkg.dev/uhi-postgis-proj3/uhi-postgis/postgis:15-3.3

# Create directory for PostgreSQL data persistence
echo "Creating data directory..."
mkdir -p /mnt/postgis-data
chmod 777 /mnt/postgis-data

# Run PostGIS container
echo "Starting PostGIS container..."
docker run -d \
  --name postgis \
  --restart unless-stopped \
  -e POSTGRES_USER=docker \
  -e POSTGRES_PASS=docker \
  -e POSTGRES_DBNAME=coburg_uhi \
  -e POSTGRES_MULTIPLE_EXTENSIONS=postgis,hstore,postgis_topology,postgis_raster \
  -p 5432:5432 \
  -p 5050:80 \
  -v /mnt/postgis-data:/var/lib/postgresql/data \
  

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to start..."
sleep 30

# Check if container is running
if docker ps | grep -q postgis; then
    echo "✅ PostGIS container is running!"
    docker logs postgis | tail -20
else
    echo "❌ PostGIS container failed to start"
    docker logs postgis
    exit 1
fi

echo "=== Startup complete at: $(date) ==="
