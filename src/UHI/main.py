#from src.pyqgis_init import *
from UHI.ss.lod2_proc_qgis import flatten_gml_files
#from UHI.hausumringe import overlay_to_grid_global_main
#from UHI.qgs_to_geopandas import qgs_layer_to_gdf

import pandas as pd

#### CURRENTLY JUST READS FROM GEODATAFRAME IN JSON FORMAT. ASSUMING ALL FILES FROM HAUSUMRINGE.PY ARE ALREADY PRESENT ###
#### TODO ADD LOGIC TO SKIP FUNCTIONS IF FILES ALREADY EXIST. LOADING FROM WIP GEODATAFRAME FOR NOW ####


def main():
    #print("🔧 Generating 100m grid over Coburg...")
    #grid = generate_grid(boundary_path=BOUNDARY_PATH, cell_size=CELL_SIZE, output_path=GRID_PATH)
    #print(f"✅ Grid created with {len(grid)} cells. Saved to {GRID_PATH}")
    #print("🔧 Adding grid to QGIS project")
    #add_grid_to_project()
    #building_areas_to_grid = overlay_to_grid_global_main()

    #gdf = qgs_layer_to_gdf(input_file=f"{PROCESSED_DATA_DIR}\\clipped_hausumringe_25832_areas_to_grid.shp")

    #gdf.to_file(f"{PROCESSED_DATA_DIR}\\geodataframe_wip.json")

    #cell_2020 = gdf.loc[gdf['grid_id'] == "cell_2020", "floor_area"].values[0] ### This value corresponds to the QGIS
                                                                               ### value for the same object, correct!
    #print(pd.options.display.max_colwidth)

    pd.options.display.max_colwidth = 10000

    #print(cell_2020)










    # Continue with ETL pipeline...
    # grid = dgm_processing.add_dgm_features(grid, dgm_path)
    # grid = lod2_processing.add_building_features(grid, lod2_path)
    # ...

if __name__ == "__main__":
    main()


