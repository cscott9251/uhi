import sys

from UHI.config import *

import ee
import subprocess
import os

def gee_init():

    ee.Authenticate()
    ee.Initialize(project='uhigisproject')
    print("GEE initialized successfully")





def upload_shapefile_to_gee(local_shapefile_path, gcs_bucket, asset_id):
    """
    Upload shapefile to GEE using CLI command
    """
    # First upload boundary shapefile from local drive to GCS, before uploading from GCS to GEE

    print(local_shapefile_path)

    base_name = os.path.splitext(local_shapefile_path)[0]
    shapefile_components = [
        base_name + '.shp',
        base_name + '.dbf',
        base_name + '.shx',
        base_name + '.prj'  # Important for projection!
    ]

    gcs_paths = []

    for file_path in shapefile_components:
        # print(file_path)
        # print(type(file_path))
        if os.path.exists(file_path):
            filename = os.path.basename(file_path)
            # print(filename)
            # print(type(filename))

            gcs_path = f"gs://{gcs_bucket}/boundary/{filename}"

            # Upload to GCS using gsutil
            #file_path = repr(file_path)
            cmd = ["gsutil", "cp", file_path, gcs_path]
            # print(cmd)
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)

            if result.returncode == 0:
                print(f"Uploaded {filename} to GCS")
                gcs_paths.append(gcs_path)
            else:
                print(f"Failed to upload {filename}: {result.stderr}")
        else:
            print(f"Warning: {file_path} not found")


    if gcs_paths:
        main_shp_path = f"gs://{gcs_bucket}/boundary/{os.path.basename(base_name + '.shp')}"
        print(main_shp_path)
        cmd = [
            'earthengine', 'upload', 'table',
            '--asset_id', asset_id, main_shp_path
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"Upload initiated: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Upload failed: {e.stderr}")
            return False



# gee_init()
# #
# upload_shapefile_to_gee(BOUNDARY_PATH, "uhiproject", "users/christopherscott925/CoburgGrenze")