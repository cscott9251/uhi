#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"


echo "Running gcloud docker initialisation"

set -e 

PROJECT_ID="uhi-postgis-proj3"

echo "Creating new gcloud project..."
gcloud projects create ${PROJECT_ID} --name="coburg-uhi"

echo "Setting active project..."
gcloud config set project ${PROJECT_ID}

echo "Initialising Docker authentication..."
gcloud auth configure-docker ${REGION}-docker.pkg.dev

echo "Linking billing..."
gcloud billing projects link ${PROJECT_ID} --billing-account=${BILLING_ACCOUNT}


echo "Registering with Artifact Registry... "
gcloud artifacts repositories create ${REPOSITORY_NAME} --repository-format=docker --location=${REGION} --project=${PROJECT_ID}

#sudo docker ps

echo "Pulling kartoza postgis Docker image..."
docker pull kartoza/${IMAGE_NAME}:${IMAGE_TAG}

echo "Tagging Docker image..."
docker tag kartoza/postgis:${IMAGE_TAG} ${FULL_IMAGE_PATH}

echo "Pushing to Artifact Registry..."
docker push ${FULL_IMAGE_PATH}

echo "Verifying..."
gcloud artifacts docker images list ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY_NAME}

echo "Enabling Compute Engine API..."
gcloud services enable compute.googleapis.com --project=${PROJECT_ID}



###! The create-with-container command is deprecated! Old method below for reference

# echo "Creating VM and deploying container..."
# gcloud compute instances create-with-container ${VM_NAME} \
#   --project=${PROJECT_ID} \
#   --zone=${ZONE} \
#   --machine-type=e2-micro \
#   --container-image=${FULL_IMAGE_PATH} \
#   --container-env=POSTGRES_USER=docker,POSTGRES_PASS=docker,POSTGRES_DBNAME=coburg_uhi \
#   --boot-disk-size=20GB \
#   --boot-disk-type=pd-standard \
#   --tags=postgis-server


