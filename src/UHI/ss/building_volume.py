# src/UHI/building_volume.py

import sys
import geopandas as gpd
import pandas as pd

import UHI.config
import UHI.pyqgis.pyqgis_init
from UHI.pyqgis.pyqgis_init import QgsVectorLayer, QgsVectorFileWriter
from UHI.config import *
#import processing
from pathlib import Path

# Load grid, load field-stripped merged, LoD2 (which contains building height), load floor area
# Calculate building volume from floor area and height
# Aggregate building volume to grid in the same way as floor area
# Use versions of these BEFORE aggregation

grid = gpd.read_file(GRID_PATH)

mergedpath = LOD2_DIR  / "pycharm_merged" / "pycharm_merged.gml"

temp_path = LOD2_DIR  / "pycharm_merged" / "pycharm_merged.gpkg"

layer = QgsVectorLayer(str(mergedpath), "pycharm_merged", "ogr")

print(layer.fields())

QgsVectorFileWriter.writeAsVectorFormat(
        layer,
        str(temp_path),
        "utf-8",
        driverName="GPKG"
    )

lod2 = gpd.read_file(temp_path, driver="GPKG")

#floor_area =