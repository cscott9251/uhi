#from src.pyqgis_init import *
from src.gridgen import generate_grid, add_grid_to_project
from src.config import BOUNDARY_PATH, GRID_PATH, CELL_SIZE


def main():
    print("🔧 Generating 100m grid over Coburg...")
    grid = generate_grid(boundary_path=BOUNDARY_PATH, cell_size=CELL_SIZE, output_path=GRID_PATH)
    print(f"✅ Grid created with {len(grid)} cells. Saved to {GRID_PATH}")
    print("🔧 Adding grid to QGIS project")
    add_grid_to_project()

    # Continue with ETL pipeline...
    # grid = dgm_processing.add_dgm_features(grid, dgm_path)
    # grid = lod2_processing.add_building_features(grid, lod2_path)
    # ...

if __name__ == "__main__":
    main()


