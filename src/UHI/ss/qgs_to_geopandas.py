# src/UHI/qgs_to_geopandas.py

import UHI.config
from UHI.pyqgis.pyqgis_init import *

from UHI.config import PROCESSED_DATA_DIR

import geopandas as gpd
from shapely.wkb import loads as wkb_loads
import pandas as pd

def qgs_layer_to_gdf(input_file) -> gpd.GeoDataFrame:
    # crs = vlayer.crs().authid()
    #
    # features = []
    # for f in vlayer.getFeatures():
    #     geom = f.geometry()
    #     feat = f.attributes()
    #     features.append((*feat, wkb_loads(geom.asWkb())))
    #
    # # Get field names
    # fields = [field.name() for field in vlayer.fields()] + ["geometry"]
    # df = pd.DataFrame(features, columns=fields)
    #
    # gdf = gpd.GeoDataFrame(df, geometry="geometry", crs=crs)
    # return gdf

    geodataframe = gpd.read_file(input_file)

    return geodataframe