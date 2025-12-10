# src/UHI/lod2_proc_qgis.py

import sys
from osgeo import gdal


from UHI.config import *
import UHI.pyqgis.pyqgis_init
from UHI.pyqgis.pyqgis_init import qgs, QgsVectorLayer, QgsProcessingFeedback, QgsProject, QgsCoordinateReferenceSystem, QgsVectorFileWriter, project

from pathlib import Path
import processing
import ogr2ogr
import gdaltools
import os
import subprocess
import shutil
from osgeo import ogr

#gdaltools.Wrapper.BASEPATH = "C/OSGEO4W/bin"


def strip_fields(input_dir, output_dir="memory:"):

    #output_dir.mkdir(exist_ok=True)
    gmlfiles = Path(input_dir).glob("*.gml")
    cleaned_layers = []



    for gml_file in gmlfiles:
        layer = QgsVectorLayer(str(gml_file), "layer", "ogr")
        if layer.isValid():
            print(f"Layer is valid, deleting columns from {gml_file}...")

            if isinstance(output_dir, Path):
                output_dir.mkdir(exist_ok=True)
                print("Isinstance Path")
                # Create output filename based on input filename
                output_file = output_dir / f"{gml_file.stem}_stripped.gml"
                output_str = str(output_file)
            else:
                output_str = output_dir


            result = processing.run("native:deletecolumn", {
                'INPUT': layer,
                'COLUMN': ['ThoroughfareName','informationSystem','name_','LocalityName'],
                'OUTPUT': output_str
            })
            cleaned_layer = result["OUTPUT"]
            cleaned_layers.append(cleaned_layer)

    return cleaned_layers








def merge_cleaned_files(cleanedfiles=strip_fields(LOD2_DIR_ORIG)):

    mergeddir = LOD2_DIR / "merged"
    mergeddir.mkdir(exist_ok=True)

    print(f"Layer is valid, merging and saving to {str(mergeddir / 'pycharm_merged.gml')}...")
    result = processing.run("native:mergevectorlayers", {
        'LAYERS': cleanedfiles,
        'CRS': "EPSG:25832",
        'OUTPUT': f"{str(mergeddir / 'pycharm_merged.gml')}",
    })


    return result


def fix_until_fixed(merged_dict, max_attempts = 5):

    print("Now fixing geometries until all geometries are valid")

    out = LOD2_DIR / 'fixed'
    out.mkdir(exist_ok=True)

    attempt = 0
    layerpath = merged_dict["OUTPUT"]
    current_layer = QgsVectorLayer(layerpath, "fixed_layer", "ogr")

    while attempt < max_attempts:
        print(f"[INFO] Checking geometry validity (attempt {attempt + 1})...")

        validity_result = processing.run("qgis:checkvalidity", {
            "INPUT_LAYER": current_layer,
            "METHOD": 2,  # 1 = Geometry validity using QGIS
            "VALID_OUTPUT": "memory:",
            "INVALID_OUTPUT": "memory:",
            "ERROR_OUTPUT": "memory:"
        })

        invalid_layer = validity_result["INVALID_OUTPUT"]
        invalid_count = invalid_layer.featureCount()
        print(f"[INFO] {invalid_count} invalid geometries detected.")

        if invalid_count == 0:

            print(f"[INFO] All geometries valid after {attempt} attempt(s).")

            #gmlexportpath = out / "pycharm_merged_fixed_final.gml"

            qgs_save_options = QgsVectorFileWriter.SaveVectorOptions()
            qgs_save_options.driverName = "GML"
            qgs_save_options.fileEncoding = "utf-8"

            gmlexport = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer=current_layer,
                fileName=str(out / "pycharm_merged_fixed_final.gml"),
                transformContext=project.transformContext(),
                options=qgs_save_options

            )

            if gmlexport[0] == QgsVectorFileWriter.NoError:
                print(f"[INFO] GML saved successfully to: {str(out / "pycharm_merged_fixed_final.gml")}")
            else:
                print(f"[ERROR] Failed to save GML: {str(out / "pycharm_merged_fixed_final.gml")}")

            return current_layer

        print(f"[INFO] Found {invalid_count} invalid geometries. Attempting fix...")

        fixed = processing.run("native:fixgeometries", {
            "INPUT": current_layer,
            "METHOD": 1,  # Structure
            "OUTPUT": "memory:"
        })

        current_layer = fixed["OUTPUT"]
        attempt += 1


    print(f"[WARNING] Maximum attempts ({max_attempts}) reached. Some geometries may still be invalid.")

    return current_layer




def fix_geometry(merged, output_path=None):

    out = LOD2_DIR / 'fixed'
    out.mkdir(exist_ok=True)

    print(f"Fixing geometry of merged layer and saving to {str(out / 'pycharm_cleaned.gml')}...")
    result = processing.run("native:fixgeometries", {
        "INPUT": merged,
        "METHOD": 1,
        "OUTPUT": f"{str(out / 'pycharm_merged_fixed.gml')}"
    })

    return result["OUTPUT"]


def fix_geometry2(fixed, output_path=None):

    out = LOD2_DIR / 'fixed'
    out.mkdir(exist_ok=True)

    print(f"Fixing geometry again of merged layer and saving to {str(out / 'pycharm_merged_fixed_final.gml')}...")
    result = processing.run("native:fixgeometries", {
        "INPUT": fixed,
        "METHOD": 1,
        "OUTPUT": f"{str(out / 'pycharm_merged_fixed_final.gml')}"
    })

    return result["OUTPUT"]


def clip_merged(fixed2, clip):

    out = LOD2_DIR / "pycharm_clipped"
    out.mkdir(exist_ok=True)

    print(f"Clipping merged LoD2 to extent and saving to {str(out)}...")
    result = processing.run("native:clip", {
        'INPUT': fixed2,
        'OVERLAY': str(clip),
        'OUTPUT': f"{str(out / 'pycharm_fixed_clipped.gml')}",
    })

    return result["OUTPUT"]

def spatial_join_lod2_hausumringe(lod2_input, hausumringe_input):
    joined = processing.run("native:joinattributesbylocation", {
        'INPUT': lod2_input,
        'JOIN': hausumringe_input,
        'PREDICATE': [0],  # intersects
        'JOIN_FIELDS': [],  # add all or only specific fields
        'METHOD': 1,        # take the first matching feature
        'DISCARD_NONMATCHING': False,
        'PREFIX': 'haus_',
        'OUTPUT': 'memory:'

    })





cleaned_dir = LOD2_DIR / "cleaned"
cleaned_dir.mkdir(exist_ok=True)

# Pipeline

# cleanedfiles_global = strip_fields(LOD2_DIR, cleaned_dir)
#
# mergedfile_global = merge_cleaned_files(cleanedfiles_global)
#
# fixed_global = fix_until_fixed(mergedfile_global)
#
# #fix_geometry_global = fix_geometry(mergedfile_global)
#
# #fix_geometry2_global = fix_geometry2(fix_geometry_global)
#
# clip_merged_global = clip_merged(fixed_global, BOUNDARY_PATH)
































# output_path = Path(f"{LOD2_DIR}\\test4_srs_flattened.gpkg")
# output_path.parent.mkdir(parents=True, exist_ok=True)
# input_path = Path(f"{LOD2_DIR}\\634_5566.gml")
#
#
#
# print(f"GMLAS:{LOD2_DIR}\\634_5566.gml")
#
#
# def flatten_gml_files(input_dir, boundary):
#
#     lod2_dir = input_dir
#     gml_files = sorted(lod2_dir.glob("*.gml"))
#     flattened_dir = lod2_dir / "flattened"
#     flattened_dir.mkdir(exist_ok=True)
#
#
#
#     for gml in gml_files:
#         output_gpkg = flattened_dir / (gml.stem + "_flat.gpkg")
#
#
#         command = [
#
#         "ogr2ogr",
#         "-f", "GPKG",
#         "-oo", "REMOVE_UNUSED_FIELDS=YES",
#         str(output_gpkg),
#         f"GMLAS:{str(gml)}",
#         "-nlt", "POLYGON",
#         "-dim", "2",
#         "-a_srs", "EPSG:25832"
#
#         ]
#
#         layer_uri = f"{str(output_gpkg)}|layername=Building"
#         layer = QgsVectorLayer(layer_uri, "Building", "ogr")
#
#         print("Running:", " ".join(command))
#
#         subprocess.run(command, check=True)
#
#
#
# #flatten_gml_files(LOD2_DIR, BOUNDARY_PATH)
#
#
#
# def clip_flattened_gml_files(flattened_layer_path, boundary_layer_path):
#
#     gml_files = sorted(flattened_layer_path.glob("*.gpkg"))
#
#     clipped_dir = LOD2_DIR / "clipped"
#     clipped_dir.mkdir(exist_ok=True)
#
#     clipped_gpkg = []
#
#     for gml in gml_files:
#
#         output_gpkg = clipped_dir / (gml.stem + "_clipped.gpkg")
#
#
#         print(f"Running subprocess clip on {gml}:")
#
#         command = [
#
#         "ogr2ogr",
#         "-f", "GPKG",
#         "-clipsrc", str(boundary_layer_path),
#         str(output_gpkg),
#         str(gml),
#         "-a_srs", "EPSG:25832",
#         "-nlt", "POLYGON",
#         "-dim", "2",
#
#
#         ]
#
#         print("Running:", " ".join(command))
#
#         subprocess.run(command)
#
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
