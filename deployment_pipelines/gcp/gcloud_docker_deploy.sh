#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"

echo "=== Deploying PostGIS VM ==="
echo "Project: ${PROJECT_ID}"
echo "VM Name: ${VM_NAME}"
echo "Image: ${FULL_IMAGE_PATH}"
echo ""

echo "Creating internal firewall rules on gcloud..."
echo ""
gcloud compute firewall-rules create allow-postgres \
    --allow tcp:5432 \
    --target-tags=allow-postgres \
    --description="Allow PostgreSQL connections" \
    --project=${PROJECT_ID}

gcloud compute firewall-rules create allow-pgadmin \
    --allow tcp:5050 \
    --target-tags=allow-postgres \
    --description="Allow pgAdmin web interface" \
    --project=${PROJECT_ID} \


echo "create-with-container command is deprecated, so applying startup script to deploy Docker image on VM..."
echo ""

# This startup script will be passed as a parameter during VM instance creation further below
# It installs Docker on the VM, authorises it with the artifact registry, pulls our previously pushed Docker image,...
# ... creates a directory on the VM for persistent storage, and finally spins up the image on the VM.

echo "Creating startup script..."
echo ""
cat > startup-script.sh << EOF
#!/bin/bash
set -e

echo "=== VM Startup Script ==="
echo "Starting at: \$(date)"

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
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

# Pull the PostGIS image
echo "Pulling PostGIS image..."
docker pull ${FULL_IMAGE_PATH} ## Pulls the Docker image that was previously pushed to the Artifact Registry 

# Create directory for PostgreSQL data persistence
echo "Creating data directory..."
mkdir -p /mnt/postgis-data
chmod 777 /mnt/postgis-data

# Run PostGIS container
echo "Starting PostGIS container..."
docker run -d \
  --name postgis \
  --restart unless-stopped \
  -e POSTGRES_USER=${POSTGRES_USER} \
  -e POSTGRES_PASS=${POSTGRES_PASS} \
  -e POSTGRES_DBNAME=${POSTGRES_DB} \
  -e POSTGRES_MULTIPLE_EXTENSIONS=postgis,hstore,postgis_topology,postgis_raster \
  -p 5432:5432 \
  -p 5050:80 \
  -v /mnt/postgis-data:/var/lib/postgresql/data \
  ${FULL_IMAGE_PATH}    

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

echo "=== Startup complete at: \$(date) ==="
EOF

# Create VM instance with above startup script

echo ""
echo "Creating VM instance..."
echo ""
gcloud compute instances create ${VM_NAME} \
    --project=${PROJECT_ID} \
    --zone=${ZONE} \
    --machine-type=${MACHINE_TYPE} \
    --boot-disk-size=${BOOT_DISK_SIZE} \
    --boot-disk-type=pd-standard \
    --image-family=debian-12 \
    --image-project=debian-cloud \
    --metadata-from-file=startup-script=startup-script.sh \
    --scopes=cloud-platform \
    --tags=allow-postgres \
    --no-restart-on-failure

echo ""
echo "VM creation initiated!"
echo ""
echo "Waiting for VM to be fully ready..."
sleep 20

echo ""
echo "Fetching VM details..."
VM_IP=$(gcloud compute instances describe ${VM_NAME} \
  --zone=${ZONE} \
  --project=${PROJECT_ID} \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
echo ""
echo "VM IP: ${VM_IP}"



VM_STATUS=$(gcloud compute instances describe ${VM_NAME} \
  --zone=${ZONE} \
  --project=${PROJECT_ID} \
  --format='get(status)')

echo ""
echo "VM STATUS: ${VM_STATUS}"


echo ""
echo "==================================="
echo "=== Deployment Complete ==="
echo "==================================="
echo ""
echo "VM Details:"
echo "  Name: ${VM_NAME}"
echo "  Status: ${VM_STATUS}"
echo "  External IP: ${VM_IP}"
echo "  Zone: ${ZONE}"
echo ""
echo "⏳ The VM is now installing Docker and starting PostgreSQL..."
echo "   This process takes approximately 2-3 minutes."
echo ""
echo "PostgreSQL Connection (available after ~3 minutes):"
echo "  Host: ${VM_IP}"
echo "  Port: 5432"
echo "  Database: ${POSTGRES_DB}"
echo "  Username: ${POSTGRES_USER}"
echo "  Password: ${POSTGRES_PASS}"
echo ""
echo "Test connection:"
echo "  psql -h ${VM_IP} -U ${POSTGRES_USER} -d ${POSTGRES_DB}"
echo ""
echo "Monitor startup progress:"
echo "  gcloud compute ssh ${VM_NAME} --zone=${ZONE} --command='sudo journalctl -u google-startup-scripts.service -f'"
echo ""
echo "Check if PostgreSQL is ready:"
echo "  gcloud compute ssh ${VM_NAME} --zone=${ZONE} --command='sudo docker ps'"
echo ""
echo "View PostgreSQL logs:"
echo "  gcloud compute ssh ${VM_NAME} --zone=${ZONE} --command='sudo docker logs postgis'"
echo ""