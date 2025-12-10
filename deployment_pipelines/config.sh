#!/bin/bash

export PROJECT_ID="uhi-postgis-proj3"
export #PROJECT_ID=$(gcloud config get-value project)
export REGION="europe-west3"
export ZONE="${REGION}-a"
export REPOSITORY_NAME="uhi-postgis"
export IMAGE_NAME="postgis"
export IMAGE_TAG="15-3.3"
export VM_NAME="uhi-postgis-vm"
export FULL_IMAGE_PATH="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY_NAME}/${IMAGE_NAME}:${IMAGE_TAG}"
export BILLING_ACCOUNT=$(gcloud billing accounts list | grep "True" | awk '{print $1}' 2>/dev/null)
export MACHINE_TYPE="e2-micro"
export BOOT_DISK_SIZE="20GB"
export POSTGRES_USER="docker"
export POSTGRES_PASS="docker"
export POSTGRES_DB="coburg_uhi"