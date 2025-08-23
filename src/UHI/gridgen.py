# src/UHI/gridgen.py

from UHI.pyqgis_init import *
import geopandas as gpd
from shapely.geometry import box
import numpy as np

def generate_grid(boundary_path, cell_size=100, output_path=None):
    """
    Generate a square grid (e.g., 100m x 100m) over a given boundary shapefile.

    Add the grid directly to the QGIS project file

    Parameters:
        boundary_path (str): Path to boundary shapefile or GeoPackage.
        cell_size (int): Size of the grid cells in meters.
        output_path (str): Optional path to save the grid as GeoPackage or Shapefile.

    Returns:
        GeoDataFrame: A grid clipped to the input boundary.
    """

    # Load boundary and project to EPSG:25832

    boundary = gpd.read_file(boundary_path).to_crs(epsg=25832)
    total_bounds = boundary.total_bounds  # [minx, miny, maxx, maxy]
    minx, miny, maxx, maxy = total_bounds


    # Create grid cells

    grid_cells = []
    for x0 in np.arange(minx, maxx, cell_size):
        for y0 in np.arange(miny, maxy, cell_size):
            x1, y1 = x0 + cell_size, y0 + cell_size
            cell = box(x0, y0, x1, y1)
            if cell.intersects(boundary.union_all()):
                grid_cells.append(cell)

    grid = gpd.GeoDataFrame({'geometry': grid_cells}, crs='EPSG:25832')

    # Optional: assign unique IDs
    grid["grid_id"] = [f"cell_{i}" for i in range(len(grid))]

    # Save if desired
    if output_path:
        print("GRID TO FILE")
        grid.to_file(output_path)

    return grid


def add_grid_to_project():

    #### QGIS LOGIC #######################

    # Load the existing grid GPKG

    grid_path = "../../data/processed/grid_100m_coburg.gpkg"
    layer_name = "grid_100m"
    grid_layer = QgsVectorLayer(grid_path, layer_name, "ogr")

    # print(grid_layer.isValid())
    # print(len(grid_layer))


    # Check validity and add to project
    if not grid_layer.isValid():
        print("❌ Grid layer failed to load.")
    elif len(grid_layer) != 0:
        print("❌ Layer already exists")
    else:
        project.addMapLayer(grid_layer)
        print(f"✅ Grid layer '{layer_name}' added.")

    # Save updated project
    project.write()
    print("📦 Project saved successfully.")

    # Exit QGIS
    qgs.exitQgis()

    #### END QGIS LOGIC ####################




