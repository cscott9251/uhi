# src/UHI/lod2_proc_ogr.py

import sys
from osgeo import gdal


from UHI.config import LOD2_DIR, LOD2_GPKG_PATH, BOUNDARY_PATH, LOD2_FLATTENED_DIR, CRS
import UHI.pyqgis.pyqgis_init
from UHI.pyqgis.pyqgis_init import (qgs, QgsVectorLayer, QgsProcessingFeedback, QgsProject, QgsCoordinateReferenceSystem,
                             QgsVectorFileWriter, project)

from pathlib import Path
import processing
import ogr2ogr
import gdaltools
import os
import subprocess
import shutil
from osgeo import ogr
import fiona

#gdaltools.Wrapper.BASEPATH = "C/OSGEO4W/bin"


# output_path = Path(f"{LOD2_DIR}\\test4_srs_flattened.gpkg")
# output_path.parent.mkdir(parents=True, exist_ok=True)
# input_path = Path(f"{LOD2_DIR}\\634_5566.gml")


def get_shapefile_bbox(shapefile):
    """Returns (minx, miny, maxx, maxy) of the shapefile boundary"""
    with fiona.open(shapefile, 'r') as shp:

        bounds = shp.bounds

        #bounds_crs = shp.crs
        #print(f"CRS of bbox: {shp.crs}")
        #print(f"Bounding box: {bounds}")

    return bounds  # (minx, miny, maxx, maxy)

#minx, miny, maxx, maxy = get_shapefile_bbox(BOUNDARY_PATH)

#print(f"minx: {minx}, miny: {miny}, maxx: {maxx}, maxy: {maxy}")


def merge(input_dir, output_path):

    gml_files = list(input_dir.glob("*.gml"))

    print(f"[INFO] Merging {len(gml_files)} GML files into {output_path.name}...")

    merge_cmd = [
        "ogrmerge",
        "-f", "GML",  # e.g., "GPKG"
        "-o", str(output_path),
        "--overwrite_ds",
    ] + [str(gml) for gml in gml_files]

    try:
        subprocess.run(merge_cmd, check=True)
        print(f"[SUCCESS] Merged GML files into: {output_path}")
    except subprocess.CalledProcessError as e:
        print("[ERROR] Failed to merge GML files!")
        print(f"Command: {' '.join(e.cmd)}")

merge(input_dir=LOD2_DIR,
    output_path=LOD2_DIR / "merged_lod2.gml")


def clip_gml_files(input_dir, output_dir, boundary_layer_path):

    gml_files = list(input_dir.glob("*.gml"))

    output_dir.mkdir(parents=True, exist_ok=True)

    minx, miny, maxx, maxy = get_shapefile_bbox(boundary_layer_path)
    spat_filter = ["-spat", str(minx), str(miny), str(maxx), str(maxy)]




    clipped_gpkg = []

    for gml in gml_files:

        print(f"[INFO] Checking cleaning GML file: {gml.name}")


        # Step 1: Clean geometry first
        cleaned_path = output_dir / f"{gml.stem}_cleaned.gml"

        clean_cmd = [
            "ogr2ogr", "-f", "GML", str(cleaned_path), str(gml),
            "-nlt", "POLYGON",
            "-makevalid",
            "-skipfailures"
        ]

        subprocess.run(clean_cmd, check=True)

        print(f"[INFO] Checking intersection for: {gml.stem}_cleaned.gml")

        ogrinfo_cmd = [
            "ogrinfo", str(cleaned_path), "-al", "-geom=NO", "-q"
        ] + spat_filter

        result = subprocess.run(ogrinfo_cmd, capture_output=True, text=True)

        if "Feature Count: 0" in result.stdout:
            print(f"[SKIP] No intersection with clip area for: {gml.name}")
            continue  # Skip this file

        print(f"[CLIP] Intersects. Clipping: {gml.stem}_cleaned.gml")
        output_gml = output_dir / f"{gml.stem}_clipped.gml"

        ogr2ogr_cmd = [
            "ogr2ogr",
            "-f", "GML",
            str(output_gml),
            str(cleaned_path),
            "-clipsrc", str(boundary_layer_path),
            "-a_srs", "EPSG:25832",
            '-oo', 'REMOVE_UNUSED_FIELDS=YES',
        ]
        try:
            subprocess.run(ogr2ogr_cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            print("[ERROR] ogr2ogr failed!")
            print(f"Command: {' '.join(e.cmd)}")
            print("[DONE] All files processed.")
            raise

clip_gml_files(input_dir=LOD2_DIR, output_dir=LOD2_DIR / "pycharm_clipped_ogr", boundary_layer_path=BOUNDARY_PATH)

sys.exit()

        # output_gml = clipped_dir / (gml.stem + "_clipped.gml")
        #
        #
        # print(f"Running subprocess clip on {gml}:")
        #
        # command = [
        #
        # "ogr2ogr",
        # "-f", "GML",
        # str(output_gml),
        # str(gml),
        # "-clipsrc", str(boundary_layer_path),
        # "-a_srs", "EPSG:25832",
        #
        #
        # ]
        #
        # print("Running:", " ".join(command))
        #
        # subprocess.run(command)


# #clip_flattened_gml_files(LOD2_FLATTENED_DIR, BOUNDARY_PATH)
#
#
#
# def merge_clipped():
#
#     """
#     Merge multiple GPKG files (each with one layer) into a single GPKG using PyQGIS.
#     :param gpkg_folder: Path to folder containing the clipped GPKG files.
#     :param output_path: Path to the output merged GPKG file.
#     :param crs_epsg: EPSG code of the CRS for the merged layer (default: 25832).
#     :return: Path to the merged GPKG.
#     """
#
#     output_merged = LOD2_DIR / "merged_lod2.gpkg"
#     clipped_dir = LOD2_DIR / "clipped" / "*.gpkg"
#
#     command = [
#
#         "ogrmerge",
#         "-f", "GPKG",
#         "-o", str(output_merged),
#         str(clipped_dir),
#
#         ]
#
#     print(f"Running merge on files in {LOD2_DIR}/clipped, saving to {output_merged}")
#
#     print("Running:", " ".join(command))
#
#     subprocess.run(command, check=True)
#
# merge_clipped()
#
#
# def get_empty_layers(gpkg_path: Path):
#
#     pass
#
#
#
#
#
# def merge_clipped_single():
#
#     """
#     Merge multiple GPKG files (each with one layer) into a single GPKG using PyQGIS.
#     :param gpkg_folder: Path to folder containing the clipped GPKG files.
#     :param output_path: Path to the output merged GPKG file.
#     :param crs_epsg: EPSG code of the CRS for the merged layer (default: 25832).
#     :return: Path to the merged GPKG.
#     """
#
#     output_merged = LOD2_DIR / "merged_lod2_python.gpkg"
#     clipped_dir = LOD2_DIR / "clipped" / "*.gpkg"
#
#     command = [
#
#         "ogrmerge",
#         "-single"
#         "-f", "GPKG",
#         "-o", str(output_merged),
#         str(clipped_dir),
#
#         ]
#
#     print(f"Running merge on files in {LOD2_DIR}/clipped, saving to {output_merged}")
#
#     print("Running:", " ".join(command))
#
#     subprocess.run(command, check=True)
#
#
# merge_clipped_single()
#
# def merge_lod2_files():
#
#     pass
#
#
#
