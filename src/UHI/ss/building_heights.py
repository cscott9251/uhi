from UHI.config import *
from UHI.gridgen import generate_grid
#from UHI.roof_area import merged_layer_global

import geopandas as gpd

# 2. Convert to GeoDataFrame with only the fields we need

merged_gdf = gpd.read_file(f"{LOD2_DIR}/merged_layer.gpkg", engine="fiona")
merged_gdf.set_crs("EPSG:25832", inplace=True)

# Keep only gml_id, measuredHeight, and geometry
height_gdf = merged_gdf[["gml_id", "measuredHeight", "geometry"]].copy()

# 3. Remove any buildings without height data (optional)
#height_gdf = height_gdf.dropna(subset=["measuredHeight"])

# 4. Load your grid
grid_gdf = generate_grid(BOUNDARY_PATH)

# 5. Spatial join - each building gets assigned to grid cells it intersects
joined = gpd.sjoin(height_gdf, grid_gdf, how="inner", predicate="intersects")

# 6. Sum building heights per grid cell
# This gives each grid cell the total height of all buildings (or parts of buildings) in it
height_per_grid = joined.groupby("grid_id")["measuredHeight"].sum().reset_index()

# 7. Load your existing grid data and merge
wipgdf = gpd.read_file(f"{PROCESSED_DATA_DIR}\\geodataframe_newwip.gpkg")
final_gdf = wipgdf.merge(height_per_grid, on="grid_id", how="left")

# 8. Save the result
final_gdf.to_file(f"{PROCESSED_DATA_DIR}\\geodataframe_with_height_grid.gpkg", driver="GPKG")

print("Building height aggregation complete!")

print(final_gdf.head())