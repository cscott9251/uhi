from UHI.config import *
from UHI.gee_init import gee_init

import ee
import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon, shape
import matplotlib.pyplot as plt

def gee_featurecollection_to_geodataframe(fc, crs='EPSG:25832'):
    """
    Convert GEE FeatureCollection to GeoDataFrame

    Parameters:
    - fc: Earth Engine FeatureCollection
    - crs: Target coordinate reference system

    Returns:
    - GeoDataFrame
    """

    # Get the geometry and properties
    fc_info = fc.getInfo()

    geometries = []
    properties_list = []

    for feature in fc_info['features']:
        # Convert GEE geometry to Shapely geometry
        geom = shape(feature['geometry'])
        geometries.append(geom)

        # Get properties (attributes)
        props = feature.get('properties', {})
        properties_list.append(props)

    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(properties_list, geometry=geometries, crs="EPSG:4326")

    # Reproject to target CRS
    if crs != "EPSG:4326":
        gdf = gdf.to_crs(crs)

    return gdf




def create_grid_from_gee_boundary(boundary_asset_id, cell_size=30, crs='EPSG:25832'):
    """
    Create a 30x30m grid from GEE boundary asset

    Parameters:
    - boundary_asset_id: GEE asset ID for boundary
    - cell_size: Grid cell size in meters (default 30m)
    - crs: Coordinate reference system

    Returns:
    - GeoDataFrame with grid cells
    """

    print(f"Loading boundary from GEE: {boundary_asset_id}")

    # Load boundary from GEE
    boundary_fc = ee.FeatureCollection(boundary_asset_id)

    # Convert to GeoDataFrame
    boundary_gdf = gee_featurecollection_to_geodataframe(boundary_fc, crs)

    print(f"Boundary loaded with {len(boundary_gdf)} features")
    print(f"Boundary CRS: {boundary_gdf.crs}")

    # Get boundary extent
    bounds = boundary_gdf.total_bounds  # [minx, miny, maxx, maxy]
    minx, miny, maxx, maxy = bounds

    print(f"Boundary extent:")
    print(f"  X: {minx:.0f} to {maxx:.0f} ({maxx-minx:.0f}m width)")
    print(f"  Y: {miny:.0f} to {maxy:.0f} ({maxy-miny:.0f}m height)")

    # Create grid coordinates
    x_coords = np.arange(minx, maxx + cell_size, cell_size)
    y_coords = np.arange(miny, maxy + cell_size, cell_size)

    print(f"Grid dimensions: {len(x_coords)-1} x {len(y_coords)-1} cells")
    print(f"Total potential cells: {(len(x_coords)-1) * (len(y_coords)-1)}")

    # Create grid polygons
    grid_cells = []
    cell_ids = []

    for i, x in enumerate(x_coords[:-1]):
        for j, y in enumerate(y_coords[:-1]):
            # Create 30x30m cell
            cell = Polygon([
                (x, y),                      # Bottom-left
                (x + cell_size, y),          # Bottom-right
                (x + cell_size, y + cell_size),  # Top-right
                (x, y + cell_size)           # Top-left
            ])

            grid_cells.append(cell)
            cell_ids.append(f"cell_{i}_{j}")

    # Create GeoDataFrame
    grid_gdf = gpd.GeoDataFrame({
        'cell_id': cell_ids,
        'x_index': [i for i in range(len(x_coords)-1) for j in range(len(y_coords)-1)],
        'y_index': [j for i in range(len(x_coords)-1) for j in range(len(y_coords)-1)],
        'geometry': grid_cells
    }, crs=crs)


    # Clip grid to boundary (only keep cells that intersect)
    print("Clipping grid to boundary...")
    grid_clipped = gpd.overlay(grid_gdf, boundary_gdf, how='intersection')

    print(f"Cells within boundary: {len(grid_clipped)}")

    return grid_clipped, boundary_gdf

def create_coburg_grid(output_file_path):
    """
    Main function to create Coburg 30x30m grid from GEE boundary
    """

    # GEE asset ID for Coburg boundary
    boundary_asset_id = 'users/christopherscott925/CoburgGrenze'

    # Create 30x30m grid
    print("Creating 30x30m grid for Coburg boundary...")
    grid, boundary = create_grid_from_gee_boundary(boundary_asset_id, cell_size=30)

    # Plot grid with boundary
    #plot_grid_with_boundary_and_points(grid, boundary)

    # Save grid

    grid.to_file(output_file_path, driver="GPKG")
    print(f"Grid saved as '{output_file_path}'")

    return grid, boundary

# Main execution
if __name__ == "__main__":

    gee_init()

    # Simple grid creation
    print("=== Creating Coburg 30x30m Grid from GEE Boundary ===")
    grid, boundary = create_coburg_grid(f"{BOUNDARY_PATH.parents[0]}\\coburg_30m_grid_from_gee.gpkg")

    print(f"\nFinal grid contains {len(grid)} cells of 30x30m each")
    print(f"Grid covers the actual Coburg municipal boundary")
