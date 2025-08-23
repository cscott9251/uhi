import rioxarray as rxr

raster_path = "C:/Users/Chris/OneDrive/GIS_Work/Personal_Projects/UrbanHeatIsland_LST_Prediction_Analysis/Raster/landsat_lst.tif"

# Open raster with rioxarray
lst = rxr.open_rasterio(raster_path, masked=True)  # masked=True handles NoData automatically

# Print basic info
print(f"Original CRS: {lst.rio.crs}")
print(f"Raster shape: {lst.shape}")
print(f"Data type: {lst.dtype}")

# Reproject to EPSG:32632 (ETRS89 / UTM zone 32N – Coburg)
lst_utm = lst.rio.reproject("EPSG:32632")


# Export reprojected raster (optional, for QGIS use)
lst_utm.rio.to_raster("C:/Users/Chris/OneDrive/GIS_Work/Personal_Projects/UrbanHeatIsland_LST_Prediction_Analysis/Raster/lst_reprojected_32632.tif")