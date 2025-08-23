import sys

import geopandas as gpd
import pandas as pd
import psycopg2
from UHI.gridgen import generate_grid
from UHI.config import *

def fetch_building_metrics_complete():
    """Fetch all building metrics from the comprehensive building_metrics table"""

    sql_query = """
    SELECT 
        total_roof_area,
        total_floor_area,
        total_building_volume
    FROM building_metrics
    WHERE building_objectid IS NOT NULL;
    """

    conn = psycopg2.connect(
        dbname=f"{PGCITYDB}",
        user=f"{PGADMIN}",
        password=f"{PGADMIN_PASSWORD}",
        host=f"{PGHOST}",  # or another host
        port="5432"         # default PostgreSQL port
    )

    building_metrics_df = pd.read_sql_query(sql_query, conn)
    conn.close()

    print(f"✅ Fetched {len(building_metrics_df)} buildings from building_metrics table")
    print(f"   Buildings with roof area: {building_metrics_df['total_roof_area'].notna().sum()}")
    print(f"   Buildings with floor area: {building_metrics_df['total_floor_area'].notna().sum()}")
    print(f"   Buildings with volume: {building_metrics_df['total_building_volume'].notna().sum()}")

    return building_metrics_df



def create_building_geodataframe_from_lod2(lod2_merged_gdf, building_metrics_df):
    """Join building metrics to LoD2 geometries using gml_id"""

    # Ensure we have the required columns
    building_gdf = lod2_merged_gdf[["gml_id", "geometry"]].copy()

    # Join metrics to geometries
    building_gdf = building_gdf.merge(
        building_metrics_df,
        left_on="gml_id",
        right_on="building_objectid",
        how="inner"
    )

    # Fill NaN values with 0 for calculations
    building_gdf = building_gdf.fillna({
        'total_roof_area': 0,
        'total_floor_area': 0,
        'building_height': 0,
        'total_building_volume': 0
    })

    print(f"✅ Created building GeoDataFrame with {len(building_gdf)} buildings")
    print(f"   Columns: {list(building_gdf.columns)}")

    return building_gdf

def aggregate_buildings_to_grid(building_gdf, grid_gdf):
    """Aggregate all building metrics to grid cells"""

    print("🔧 Performing spatial join of buildings to grid...")

    # Spatial join buildings to grid
    joined = gpd.sjoin(building_gdf, grid_gdf, how="inner", predicate="intersects")

    print(f"   Spatial join result: {len(joined)} building-grid intersections")

    # Aggregate all metrics by grid cell
    print("🔧 Aggregating metrics by grid cell...")
    grid_metrics = joined.groupby("grid_id").agg({
        'total_roof_area': 'sum',
        'total_floor_area': 'sum',
        'building_height': 'mean',  # Average height per grid cell
        'total_building_volume': 'sum'
    }).reset_index()

    # Rename columns for clarity
    grid_metrics = grid_metrics.rename(columns={
        'total_roof_area': 'grid_total_roof_area',
        'total_floor_area': 'grid_total_floor_area',
        'building_height': 'grid_avg_building_height',
        'total_building_volume': 'grid_total_building_volume'
    })

    # Add building count per grid cell
    building_count = joined.groupby("grid_id").size().reset_index(name='building_count')
    grid_metrics = grid_metrics.merge(building_count, on="grid_id", how="left")

    # Join back to grid geometry
    grid_result = grid_gdf.merge(grid_metrics, on="grid_id", how="left")

    # Fill NaN values with 0 for grid cells with no buildings
    grid_result = grid_result.fillna({
        'grid_total_roof_area': 0,
        'grid_total_floor_area': 0,
        'grid_avg_building_height': 0,
        'grid_total_building_volume': 0,
        'building_count': 0
    })

    print(f"✅ Aggregated to {len(grid_result)} grid cells")
    print(f"   Grid cells with buildings: {(grid_result['building_count'] > 0).sum()}")

    return grid_result

def save_results(building_gdf, grid_gdf, output_dir):
    """Save both individual and aggregated results"""

    # Define output paths
    building_gpkg = f"{output_dir}/buildings_complete_metrics.gpkg"
    building_json = f"{output_dir}/buildings_complete_metrics.json"
    grid_gpkg = f"{output_dir}/grid_building_metrics.gpkg"
    grid_json = f"{output_dir}/grid_building_metrics.json"

    # Save individual buildings
    building_gdf.to_file(building_gpkg, driver="GPKG")
    building_gdf.to_file(building_json, driver="GeoJSON")

    # Save grid aggregates
    grid_gdf.to_file(grid_gpkg, driver="GPKG")
    grid_gdf.to_file(grid_json, driver="GeoJSON")

    print(f"✅ Results saved:")
    print(f"   Individual buildings: {building_gpkg}")
    print(f"   Individual buildings JSON: {building_json}")
    print(f"   Grid aggregates: {grid_gpkg}")
    print(f"   Grid aggregates JSON: {grid_json}")

def run_complete_building_metrics_pipeline(lod2_merged_gdf, boundary_path, output_dir):
    """Complete pipeline: building_metrics table → LoD2 geometries → grid aggregation"""

    print("🚀 Starting Complete Building Metrics Pipeline...")

    # Step 1: Fetch building metrics from database
    building_metrics_df = fetch_building_metrics_complete()

    # Step 2: Create building GeoDataFrame with geometries
    building_gdf = create_building_geodataframe_from_lod2(lod2_merged_gdf, building_metrics_df)

    # Step 3: Generate grid
    print("🔧 Generating grid...")
    grid_gdf = generate_grid(boundary_path)

    # Step 4: Aggregate to grid
    grid_result = aggregate_buildings_to_grid(building_gdf, grid_gdf)

    # Step 5: Save outputs
    save_results(building_gdf, grid_result, output_dir)

    # Print summary statistics
    print("\n📊 Pipeline Summary:")
    print(f"   Total buildings processed: {len(building_gdf)}")
    print(f"   Total grid cells: {len(grid_result)}")
    print(f"   Grid cells with buildings: {(grid_result['building_count'] > 0).sum()}")
    print(f"   Total building volume: {building_gdf['total_building_volume'].sum():,.0f} m³")
    print(f"   Total floor area: {building_gdf['total_floor_area'].sum():,.0f} m²")
    print(f"   Total roof area: {building_gdf['total_roof_area'].sum():,.0f} m²")

    return building_gdf, grid_result

# Integration with your existing code
def integrate_with_existing_lod2_data():
    """How to use with your existing merged LoD2 data"""

    # Load your existing merged LoD2 data
    merged_gdf = gpd.read_file(f"{LOD2_DIR}/pycharm_merged/pycharm_merged.gml")


    merged_gdf.set_crs("EPSG:25832", inplace=True)
    merged_gdf = merged_gdf[["gml_id", "geometry"]]

    # Run the complete pipeline
    building_gdf, grid_gdf = run_complete_building_metrics_pipeline(
        lod2_merged_gdf=merged_gdf,
        boundary_path=BOUNDARY_PATH,
        output_dir=PROCESSED_DATA_DIR
    )

    return building_gdf, grid_gdf

# Quick function to just get grid aggregates
def get_grid_aggregates_only(boundary_path, output_dir):
    """Quick function to just aggregate building_metrics to grid without individual building output"""

    # Fetch building metrics
    building_metrics_df = fetch_building_metrics_complete()

    # Load LoD2 geometries
    merged_gdf = gpd.read_file(f"{LOD2_DIR}/merged_layer.gpkg")
    merged_gdf.set_crs("EPSG:25832", inplace=True)
    building_gdf = create_building_geodataframe_from_lod2(merged_gdf, building_metrics_df)

    # Generate grid and aggregate
    grid_gdf = generate_grid(boundary_path)
    grid_result = aggregate_buildings_to_grid(building_gdf, grid_gdf)

    # Save only grid results
    grid_result.to_file(f"{output_dir}/grid_building_metrics_final.gpkg", driver="GPKG")
    grid_result.to_file(f"{output_dir}/grid_building_metrics_final.json", driver="GeoJSON")

    return grid_result

# Usage
if __name__ == "__main__":
    # Run complete pipeline
    buildings, grid = integrate_with_existing_lod2_data()

    # OR just get grid aggregates
    # grid = get_grid_aggregates_only(BOUNDARY_PATH, PROCESSED_DATA_DIR)