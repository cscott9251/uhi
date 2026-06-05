from UHI.config import *
import subprocess

from UHI.morphological import create_3dcitydb, citydb_load_gml_files
from UHI.morphological.citydb_main import calculate_building_metrics_pipeline
from UHI.etl.citydb_aggregate_building_metrics_to_grid import run_aggregated_metrics_pipeline

def main():

    # Create the empty PostgreSQL database if it doesn't exist and create the citydb schema within it using the 3DCityDB scripts.

    create_3dcitydb.create_3dcitydb() 

    # Load the CityGML files into the citydb schema within the PostgreSQL database.

    citydb_load_gml_files.load_citygml_files()

    # Calculate floor area, roof area, extract building height from GML metadata, and calculate building volume as separate tables in the database.
    # Collect all building metric data into a single table.
    # Building metric data is ordered by object, with object_id as its unique / primary key.

    calculate_building_metrics_pipeline()

    # Using the PostGIS ST_Area and ST_Intersection functions, the weighted intersections are computed for building overlaps with the 30m grid.
    # The proportion of builing floor area, roof area, and volume that fall within each grid cell are applied to that grid cell.
    # The result is the transformation of a table of per-object metric data into a table of per-grid-cell metric data, with cell_id as the unique / primary key.
    # This enables the building metrics to be explored in a city-wide context, and used as input variables for the UHI analysis.

    run_aggregated_metrics_pipeline(
        grid_path=GRID_30M_PATH,
        output_dir=PROCESSED_DATA_DIR
        )


if __name__ == "__main__":

    main()