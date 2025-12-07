import sys

import geopandas as gpd
from sqlalchemy import create_engine

from UHI.config import *


def create_db_engine():
    """
    Create SQLAlchemy engine for database connection
    """
    connection_string = f"postgresql://{PGADMIN}:{PGADMIN_PASSWORD}@{PGHOST}:5432/{PGCITYDB}"
    engine = create_engine(connection_string)

    return engine

def combine_morphological_spectral():


    fishnet = FISHNETS_DATA_DIR / "coburg_fishnet_summer_2024_20250810_110839.gpkg"
    building_metrics = PROCESSED_DATA_DIR / "aggregated_building_metrics_30m.gpkg"
    out = DATA_DIR / "final_join"

    # Load both geopackages
    morphological = gpd.read_file(building_metrics)
    spectral = gpd.read_file(fishnet)

    morphological.rename(columns={"grid_id":"cell_id"}, inplace=True)

    print(morphological.keys())
    print(spectral.keys())

    # Check if they have the same number of features
    print(f"Morphological features: {len(morphological)}")
    print(f"Spectral features: {len(spectral)}")

    # Check bounding boxes
    print(f"\nMorphological bounds: {morphological.total_bounds}")
    print(f"Spectral bounds: {spectral.total_bounds}")

    # Sort both by a consistent order (e.g., by centroid coordinates)
    morphological_sorted = morphological.sort_values('cell_id').reset_index(drop=True)
    spectral_sorted = spectral.sort_values('cell_id').reset_index(drop=True)

    # Check if geometries are exactly equal
    geometries_equal = morphological_sorted.geometry.equals(spectral_sorted.geometry)
    print(f"All geometries identical: {geometries_equal}")

    if geometries_equal:
        # Convert spectral to regular DataFrame (drops geometry)
        spectral_no_geom = spectral.drop(columns='geometry')


    #sys.exit()

        # Join on cell_id
        print("Merging spectral and morphological dataframes...")
        combined = morphological.merge(spectral_no_geom, on='cell_id', how='inner')

        # Save combined dataset
        print("Saving combined dataframe to file...")

        combined.to_file(f"{out}/coburg_uhi_complete.gpkg", driver='GPKG')

        return combined


def load_conbined_to_postgres():

    combined_gpkg = DATA_DIR / "final_join" / "coburg_uhi_complete.gpkg"

    engine = create_db_engine()

    gdf_combined = gpd.read_file(combined_gpkg)

    gdf_combined.to_postgis(

        'coburg_uhi_complete',
        engine,
        if_exists='replace',
        index=False

    )


#def postgres_dump():

    

load_conbined_to_postgres()