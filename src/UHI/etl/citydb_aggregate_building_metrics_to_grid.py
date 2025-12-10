from UHI.config import *
from sqlalchemy import create_engine
from sqlalchemy.sql import text
#import geoalchemy2
import pandas as pd
import geopandas as gpd


"""
This module :
Queries the Postgres database for the building morphological data (floor area, roof area, building height, building volume), which was calculated for each object.
Transfers this data into a GeoDataframe using GeoPandas.
Calculates weighted intersections of objects with reference to the 30m resolution grid (cuts the objects by the grid lines), 
and then allocates the building metrics to each cell according to its intersection proportion with each cell
Aggregates / applies 
"""


def create_db_engine():
    """
    Create SQLAlchemy engine for database connection
    """
    connection_string = f"postgresql://{PGADMIN}:{PGADMIN_PASSWORD}@{PGHOST}:5432/{PGCITYDB}"
    engine = create_engine(connection_string)

    return engine


def fetch_building_metrics_with_geometry():
    """
    Fetch building metrics along with their actual geometries from Postgres database
    """

    sql_query = """
    SELECT 
        bm.building_objectid,
        bm.total_roof_area,
        bm.total_floor_area,
        bm.total_building_volume,
        f.envelope as geometry  -- Get geometry directly (already in EPSG:25832)
    FROM 
        building_metrics bm
    JOIN 
        citydb.feature f ON f.objectid = bm.building_objectid
    WHERE 
        bm.building_objectid IS NOT NULL
        AND f.envelope IS NOT NULL;
    """

    engine = create_db_engine()

    # Use geopandas to read spatial data directly from PostGIS
    building_gdf = gpd.read_postgis(
        sql_query,
        engine,
        geom_col='geometry',
        crs='EPSG:25832'
    )


    print(f"✅ Fetched {len(building_gdf)} buildings with geometries")
    return building_gdf


# def calculate_weighted_intersections_postgis(grid_gdf):
#     """
#     Use PostGIS to calculate weighted intersections directly in the database
#     Much more efficient than doing overlay operations in Python
#     """

#     print("🔧 Uploading grid to PostGIS for spatial operations...")

#     engine = create_db_engine()

#     # Upload grid to temporary PostGIS table
#     grid_gdf.to_postgis('temp_grid', engine, if_exists='replace', index=False) ### Takes the passed grid_gdf and uploads
#                                                                                 ### to PostGIS, so that the below query
#                                                                                 ### can reference it

#     print("🔧 Calculating weighted intersections using PostGIS...")

#     # Use PostGIS for efficient spatial intersection and area calculations

#     sql_query = """
#     WITH weighted_intersections AS (
#         SELECT 
#             b.building_objectid,
#             g.grid_id,
#             b.total_roof_area,
#             b.total_floor_area,
#             b.total_building_volume,
#             -- Calculate intersection geometry and area
#             ST_Intersection(b.geometry, g.geometry) as intersection_geom, -- Returns geometry representing the point-set intersection of two geometries (portion of geometry A and geometry B that is shared) 
#             ST_Area(ST_Intersection(b.geometry, g.geometry)) as intersection_area, -- Returns the area of the intersection between b objects and the grid
#             ST_Area(b.geometry) as total_building_area
#         FROM 
#             (SELECT 
#                 bm.building_objectid,
#                 bm.total_roof_area,
#                 bm.total_floor_area,
#                 bm.building_height,
#                 bm.total_building_volume,
#                 f.envelope as geometry
#              FROM building_metrics bm
#              JOIN citydb.feature f ON f.objectid = bm.building_objectid
#              WHERE bm.building_objectid IS NOT NULL 
#                AND f.envelope IS NOT NULL
#             ) b
#         JOIN 
#             temp_grid g ON ST_Intersects(b.geometry, g.geometry)  -- temp_grid injected into database from grid_gdf param of function
#         WHERE 
#             ST_Area(ST_Intersection(b.geometry, g.geometry)) > 0
#     )
#     SELECT 
#         building_objectid,
#         grid_id,
#         total_roof_area,
#         total_floor_area,
#         total_building_volume,
#         intersection_area,
#         total_building_area,
#         -- Calculate area percentage
#         intersection_area / total_building_area as area_percentage,
#         -- Calculate allocated metrics
#         total_roof_area * (intersection_area / total_building_area) as allocated_roof_area,
#         total_floor_area * (intersection_area / total_building_area) as allocated_floor_area,
#         total_building_volume * (intersection_area / total_building_area) as allocated_volume,
#         ST_Transform(intersection_geom, 25832) as geometry
#     FROM weighted_intersections
#     WHERE intersection_area > 0;
#     """

#     # Execute the spatial query and get results as GeoDataFrame
#     intersections_gdf = gpd.read_postgis(
#         sql_query,
#         engine,
#         geom_col='geometry',
#         crs='EPSG:25832'
#     )

#     # Clean up temporary table

#     statement = text("""DROP TABLE IF EXISTS temp_grid""")

#     with engine.connect() as conn:
#         conn.execute(statement)
#         conn.commit()

#     engine.dispose()

#     print(f"✅ PostGIS calculated {len(intersections_gdf)} weighted intersections")

#     return intersections_gdf

# grid_gdf = gpd.read_file(GRID_PATH)
# engine = create_db_engine()
# grid_gdf.to_postgis('temp_grid', engine, schema='citydb', if_exists='replace', index=False)
#

# building_gdf = fetch_building_metrics_with_geometry()

# def aggregate_weighted_metrics(intersections_gdf, grid_gdf):
#     """
#     Aggregate the weighted metrics by grid cell
#     """

#     print("🔧 Aggregating weighted metrics by grid cell...")

#     # Group by grid_id and sum the allocated metrics
#     grid_aggregates = intersections_gdf.groupby('grid_id').agg({
#         'allocated_roof_area': 'sum',
#         'allocated_floor_area': 'sum',
#         'allocated_volume': 'sum',
#         'allocated_height_weighted': 'sum',
#         'area_percentage': 'sum',  # This shows how much "building coverage" per grid
#         'building_objectid': 'count'  # Number of building intersections (can be > buildings if split)
#     }).reset_index()

#     # Calculate weighted average height per grid cell
#     grid_aggregates['weighted_avg_height'] = (
#         grid_aggregates['allocated_height_weighted'] / grid_aggregates['area_percentage']
#     ).fillna(0)

#     # Rename columns for clarity
#     grid_aggregates = grid_aggregates.rename(columns={
#         'allocated_roof_area': 'grid_weighted_roof_area',
#         'allocated_floor_area': 'grid_weighted_floor_area',
#         'allocated_volume': 'grid_weighted_volume',
#         'area_percentage': 'total_building_coverage',
#         'building_objectid': 'building_intersection_count'
#     })

#     # Join back to original grid to maintain all grid cells
#     result = grid_gdf.merge(grid_aggregates, on='grid_id', how='left')

#     # Fill NaN values with 0 for grid cells with no buildings
#     result = result.fillna({
#         'grid_weighted_roof_area': 0,
#         'grid_weighted_floor_area': 0,
#         'grid_weighted_volume': 0,
#         'weighted_avg_height': 0,
#         'total_building_coverage': 0,
#         'building_intersection_count': 0
#     })

#     print(f"✅ Aggregated to {len(result)} grid cells")
#     print(f"   Grid cells with buildings: {(result['building_intersection_count'] > 0).sum()}")

#     return result

def create_aggregated_building_metrics_table(grid_gdf):
    """
    Create aggregated_building_metrics table in PostGIS with grid_id as primary key
    Sums all building metrics (which were previously calculated by object) by grid for each grid cell
    """

    print("🔧 Creating aggregated building metrics table in PostGIS...")

    engine = create_db_engine()

    # Upload grid to temporary PostGIS table in citydb schema
    grid_gdf.to_postgis('temp_grid', engine, schema='citydb', if_exists='replace', index=False)

    print("🔧 Calculating aggregated metrics by grid cell...")

    # SQL to create the aggregated table
    sql_create_table = text("""
    -- Drop table if it exists
    DROP TABLE IF EXISTS citydb.aggregated_building_metrics_30m;
    
    -- Create aggregated building metrics table
    CREATE TABLE citydb.aggregated_building_metrics_30m AS
    WITH weighted_intersections AS (
        SELECT 
            g.grid_id,
            bm.total_roof_area,
            bm.total_floor_area,
            bm.building_height,
            bm.total_building_volume,
            -- Calculate intersection area and percentage
            ST_Area(ST_Intersection(f.envelope, g.geometry)) as intersection_area,
            ST_Area(f.envelope) as total_building_area
        FROM 
            citydb.building_metrics bm
        JOIN 
            citydb.feature f ON f.objectid = bm.building_objectid 
                             AND f.objectclass_id = 901  -- CRITICAL: Only join to Building features!
        JOIN 
            citydb.temp_grid g ON ST_Intersects(f.envelope, g.geometry)
        WHERE 
            bm.building_objectid IS NOT NULL 
            AND f.envelope IS NOT NULL
            AND ST_Area(ST_Intersection(f.envelope, g.geometry)) > 0
    ),
    allocated_metrics AS (
        SELECT 
            grid_id,
            -- Calculate allocated metrics using area percentage
            total_roof_area * (intersection_area / total_building_area) as allocated_roof_area,
            total_floor_area * (intersection_area / total_building_area) as allocated_floor_area,
            total_building_volume * (intersection_area / total_building_area) as allocated_volume,
            building_height * (intersection_area / total_building_area) as allocated_height_weighted,
            intersection_area / total_building_area as area_percentage
        FROM weighted_intersections
    )
    SELECT 
        grid_id,
        SUM(allocated_roof_area) as grid_total_roof_area,
        SUM(allocated_floor_area) as grid_total_floor_area,
        SUM(allocated_volume) as grid_total_building_volume,
        AVG(allocated_height_weighted / NULLIF(area_percentage, 0)) as grid_avg_building_height,
        SUM(area_percentage) as total_building_coverage,
        COUNT(*) as building_intersection_count
    FROM allocated_metrics
    GROUP BY grid_id;
    
    -- Add primary key constraint
    ALTER TABLE citydb.aggregated_building_metrics_30m
    ADD CONSTRAINT aggregated_building_metrics_30m_pk PRIMARY KEY (grid_id);
    
    -- Create index for performance
    CREATE INDEX idx_aggregated_building_metrics_grid_30m_id 
    ON citydb.aggregated_building_metrics_30m (grid_id);
    
    -- Add grid cells with no buildings (zero values)
    INSERT INTO citydb.aggregated_building_metrics_30m (
        grid_id, 
        grid_total_roof_area, 
        grid_total_floor_area, 
        grid_total_building_volume,
        grid_avg_building_height,
        total_building_coverage,
        building_intersection_count
    )
    SELECT 
        g.grid_id,
        0 as grid_total_roof_area,
        0 as grid_total_floor_area,
        0 as grid_total_building_volume,
        0 as grid_avg_building_height,
        0 as total_building_coverage,
        0 as building_intersection_count
    FROM citydb.temp_grid g
    WHERE g.grid_id NOT IN (
        SELECT grid_id FROM citydb.aggregated_building_metrics_30m
    );
    """
    )


    # Execute the SQL
    with engine.connect() as conn:
        conn.execute(sql_create_table)
        conn.commit()


    sql_query = text("""
    SELECT 
        grid_id,
        grid_total_roof_area,
        grid_total_floor_area,
        grid_total_building_volume,
        grid_avg_building_height,
        total_building_coverage,
        building_intersection_count
    FROM citydb.aggregated_building_metrics_30m
    ORDER BY grid_id;
    """)

    aggregated_df = pd.read_sql_query(sql_query, engine)

    # Clean up temporary table
    # with engine.connect() as conn:
    #     conn.execute(text("""DROP TABLE IF EXISTS citydb.temp_grid"""))
    #     conn.commit()
    #
    # engine.dispose()

    print("✅ Created citydb.aggregated_building_metrics_30m table")
    print(f"✅ Fetched aggregated metrics for {len(aggregated_df)} grid cells")

    # Return the table as GeoDataFrame for immediate use
    return aggregated_df


def run_aggregated_metrics_pipeline(grid_path, output_dir):
    """
    Create aggregated building metrics table and save results
    """

    print("🚀 Starting Aggregated Building Metrics Pipeline...")

    # Step 1: Load existing grid
    print(f"🔧 Loading existing grid from {grid_path}")
    grid_gdf = gpd.read_file(grid_path)
    grid_gdf = grid_gdf.to_crs('EPSG:25832')
    print(f"   Loaded grid with {len(grid_gdf)} cells")

    grid_gdf = grid_gdf[["cell_id","geometry"]]
    grid_gdf = grid_gdf.rename(columns={"cell_id":"grid_id"})

    # Step 2: Create aggregated metrics table in PostGIS
    aggregated_df = create_aggregated_building_metrics_table(grid_gdf)

    # Step 3: Join back to grid geometry for saving
    grid_result = grid_gdf.merge(aggregated_df, on='grid_id', how='left')

    # Step 4: Save results
    output_gpkg = f"{output_dir}/aggregated_building_metrics_30m.gpkg"
    output_json = f"{output_dir}/aggregated_building_metrics_30m.json"

    grid_result.to_file(output_gpkg, driver="GPKG")
    grid_result.to_file(output_json, driver="GeoJSON")

    # Print summary statistics
    print("🎉 Aggregated Building Metrics Pipeline completed!")
    print(f"   Output GPKG: {output_gpkg}")
    print(f"   Output JSON: {output_json}")
    print(f"   Database table: citydb.aggregated_building_metrics_30m")
    print(f"\n📊 Summary Statistics:")
    print(f"   Total grid cells: {len(aggregated_df)}")
    print(f"   Grid cells with buildings: {(aggregated_df['building_intersection_count'] > 0).sum()}")
    print(f"   Total floor area: {aggregated_df['grid_total_floor_area'].sum():,.0f} m²")
    print(f"   Total roof area: {aggregated_df['grid_total_roof_area'].sum():,.0f} m²")
    print(f"   Total building volume: {aggregated_df['grid_total_building_volume'].sum():,.0f} m³")

    return grid_result


# def run_weighted_aggregation_pipeline(grid_path, output_dir):
#     """
#     Complete weighted spatial aggregation pipeline
#     """
#
#     print("🚀 Starting Weighted Spatial Aggregation Pipeline...")
#
#     # Step 1: Load existing grid
#     print(f"🔧 Loading existing grid from {grid_path}")
#     grid_gdf = gpd.read_file(grid_path)
#     grid_gdf = grid_gdf.to_crs('EPSG:25832')
#     print(f"   Loaded grid with {len(grid_gdf)} cells")
#
#     grid_gdf = grid_gdf[["cell_id","geometry"]]
#     grid_gdf = grid_gdf.rename(columns={"cell_id":"grid_id"})
#
#     # Step 2: For volume conservation comparison
#     building_gdf = fetch_building_metrics_with_geometry()  # Not needed anymore
#
#     # Step 3: Calculate weighted intersections using PostGIS (no building_gdf needed)
#     intersections_gdf = calculate_weighted_intersections_postgis(grid_gdf)
#
#     if len(intersections_gdf) == 0:
#         print("❌ No intersections found - check CRS and spatial overlap")
#         return None
#
#     # Step 4: Aggregate weighted metrics
#     grid_result = aggregate_weighted_metrics(intersections_gdf, grid_gdf)
#
#     # Step 5: Save results
#     output_gpkg = f"{output_dir}/grid_weighted_building_metrics_30m.gpkg"
#     output_json = f"{output_dir}/grid_weighted_building_metrics_30m.json"
#     intersections_gpkg = f"{output_dir}/building_grid_intersections_30m.gpkg"
#
#     grid_result.to_file(output_gpkg, driver="GPKG")
#     grid_result.to_file(output_json, driver="GeoJSON")
#     intersections_gdf.to_file(intersections_gpkg, driver="GPKG")  # Save detailed intersections
#
#     # Print summary statistics
#     total_original_volume = building_gdf['total_building_volume'].sum()
#     total_allocated_volume = grid_result['grid_weighted_volume'].sum()
#
#     print("🎉 Weighted Aggregation Pipeline completed!")
#     print(f"   Output GPKG: {output_gpkg}")
#     print(f"   Output JSON: {output_json}")
#     print(f"   Detailed intersections: {intersections_gpkg}")
#     print(f"\n📊 Volume Conservation Check:")
#     print(f"   Original total volume: {total_original_volume:,.0f} m³")
#     print(f"   Allocated total volume: {total_allocated_volume:,.0f} m³")
#     print(f"   Difference: {abs(total_original_volume - total_allocated_volume):,.0f} m³")
#     print(f"   Conservation: {(total_allocated_volume/total_original_volume)*100:.2f}%")
#
#     return grid_result, intersections_gdf
#
#
# def analyze_building_splits(intersections_gdf):
#     """
#     Analyze how buildings are split across grid cells
#     """
#
#     print("\n📈 Building Split Analysis:")
#
#     # Count how many grid cells each building intersects
#     building_grid_counts = intersections_gdf.groupby('building_objectid').size()
#
#     print(f"   Buildings intersecting 1 grid cell: {(building_grid_counts == 1).sum()}")
#     print(f"   Buildings intersecting 2 grid cells: {(building_grid_counts == 2).sum()}")
#     print(f"   Buildings intersecting 3+ grid cells: {(building_grid_counts >= 3).sum()}")
#     print(f"   Maximum grid cells per building: {building_grid_counts.max()}")
#
#     # Show examples of split buildings
#     multi_grid_buildings = building_grid_counts[building_grid_counts > 1].head(5)
#     for building_id, grid_count in multi_grid_buildings.items():
#         building_splits = intersections_gdf[
#             intersections_gdf['building_objectid'] == building_id
#         ][['grid_id', 'area_percentage']].round(3)
#         print(f"\n   Building {building_id} splits:")
#         for _, row in building_splits.iterrows():
#             print(f"     Grid {row['grid_id']}: {row['area_percentage']*100:.1f}%")
#
#
# def create_weighted_aggregation_sql():
#     """
#     SQL query to do weighted aggregation entirely in PostGIS
#     This avoids loading large geometries into Python
#     """
#
#     sql = """
#     -- Create weighted grid aggregation table in PostGIS
#     CREATE TABLE grid_weighted_metrics_30m AS
#     WITH building_intersections AS (
#         SELECT
#             g.grid_id,
#             bm.building_objectid,
#             bm.total_roof_area,
#             bm.total_floor_area,
#             bm.building_height,
#             bm.total_building_volume,
#             -- Calculate intersection area
#             ST_Area(ST_Intersection(g.geom, f.envelope)) as intersection_area,
#             -- Calculate total building area
#             ST_Area(f.envelope) as total_building_area,
#             -- Calculate percentage
#             ST_Area(ST_Intersection(g.geom, f.envelope)) / ST_Area(f.envelope) as area_percentage
#         FROM
#             citydb.temp_grid g
#         JOIN
#             citydb.feature f ON ST_Intersects(g.geom, f.envelope)
#         JOIN
#             building_metrics bm ON f.objectid = bm.building_objectid
#         WHERE
#             ST_Area(ST_Intersection(g.geom, f.envelope)) > 0
#     )
#     SELECT
#         grid_id,
#         COUNT(*) as building_intersection_count,
#         SUM(total_roof_area * area_percentage) as grid_weighted_roof_area,
#         SUM(total_floor_area * area_percentage) as grid_weighted_floor_area,
#         SUM(total_building_volume * area_percentage) as grid_weighted_volume,
#         AVG(building_height) as weighted_avg_height,
#         SUM(area_percentage) as total_building_coverage
#     FROM
#         building_intersections
#     GROUP BY
#         grid_id;
#     """
#
#     return sql


if __name__ == "__main__":
    # Create aggregated building metrics table with your existing grid
    grid_result = run_aggregated_metrics_pipeline(
        grid_path=GRID_30M_PATH,
        output_dir=PROCESSED_DATA_DIR
    )