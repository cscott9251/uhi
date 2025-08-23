import sys

from UHI.config import *

import datetime
import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point, Polygon
import ee

from UHI.gee_init import gee_init


def sample_gee_rasters_at_centroids(grid_file_path, gee_raster_dict, output_path, _to_file_driver="GPKG", scale=30, _batch_size=200):
    """
    Simple function to sample GEE rasters at grid centroids

    Parameters:
    grid_file_path: path to your existing grid GPKG file
    gee_raster_dict: dictionary with raster names and their GEE image objects
                    e.g., {'LST': ee.Image('your/lst/asset'), 'NDVI': ee.Image('your/ndvi/asset')}
    output_path: where to save the result

    Returns:
    GeoDataFrame with sampled values
    """

    # Load existing grid
    print(f"Loading grid from: {grid_file_path}")
    grid_gdf = gpd.read_file(grid_file_path)
    grid_gdf = grid_gdf[["cell_id", "geometry"]]
    print(f"***Grid CRS***: {grid_gdf.crs}")
    print("Columns:", grid_gdf.columns.tolist())
    print("Sample cell_id:", grid_gdf['cell_id'].iloc[0] if 'cell_id' in grid_gdf.columns else "No cell_id column")
    print("Shape:", grid_gdf.shape)

    print(f"Loaded grid with {len(grid_gdf)} cells")

    # Calculate centroids
    print("Calculating centroids...")

    # Calculate centroids in the original CRS (which should be projected)
    grid_gdf['centroid_projected'] = grid_gdf.geometry.centroid

    # Convert to WGS84 for GEE

    if grid_gdf.crs == 'EPSG:4326':

        centroids_utm = grid_gdf.copy()

        #centroids_wgs84 = grid_gdf.to_crs('EPSG:4326')
        # Transform the projected centroids to WGS84
        # centroid_gdf = gpd.GeoDataFrame(
        #     geometry=grid_gdf['centroid_projected'],
        #     crs=grid_gdf.crs
        # ).to_crs('EPSG:4326')
        # centroids_wgs84['centroid'] = centroid_gdf.geometry
    else:
        centroids_utm = grid_gdf.to_crs('EPSG:25832')

    centroids_utm['centroid'] = centroids_utm.geometry.centroid

        # centroids_wgs84 = grid_gdf.copy()
        # centroids_wgs84['centroid'] = centroids_wgs84.geometry.centroid


    # Convert centroids to GEE points
    coords = [[point.x, point.y] for point in centroids_utm['centroid']]


    # Sample each raster
    result_gdf = grid_gdf.copy()

    # Remove extra geometry columns to avoid saving issues

    geometry_cols = [col for col in result_gdf.columns if col.startswith('centroid')]
    if geometry_cols:
        result_gdf = result_gdf.drop(columns=geometry_cols)

    # Process in batches to avoid payload size limits
    batch_size = _batch_size  # Process 100 points at a time by default



    for raster_name, gee_image in gee_raster_dict.items():
        print(f"Sampling {raster_name}...")

        try:

            values = [np.nan] * len(grid_gdf)


            valid_count = len([v for v in values if not np.isnan(v)])
            running_total = valid_count + batch_size

            # Process points in batches
            for batch_start in range(0, len(coords), batch_size):
                batch_end = min(batch_start + batch_size, len(coords))
                batch_coords = coords[batch_start:batch_end]

                print(f"  - Processing batch {batch_start//batch_size + 1}/{(len(coords)-1)//batch_size + 1} ({len(batch_coords)} points)")

                ##
                # print(f"Grid CRS: {grid_gdf.crs}")
                # print(f"Sample coordinates (first 3): {coords[:3]}")
                # print(f"Coordinate bounds:")
                # print(f"  X: [{min(c[0] for c in coords):.1f}, {max(c[0] for c in coords):.1f}]")
                # print(f"  Y: [{min(c[1] for c in coords):.1f}, {max(c[1] for c in coords):.1f}]")


                # Create batch points
                batch_points = ee.FeatureCollection([
                    ee.Feature(ee.Geometry(
                {'type': 'Point', 'coordinates': coord},
                        proj='EPSG:25832'                           ### MUST EXPLICITLY SET 25832 PROJECTION BECAUSE
                    ), {'cell_id': batch_start + i})        # ee methods always work in WGS84 unless instructed otherwise
                    for i, coord in enumerate(batch_coords)
                ])

                ## Debug the points
                # print(f"    Created {batch_points.size().getInfo()} points")
                # print(f"    First point info: {batch_points.first().getInfo()}")

                ## Check if points are valid
                # try:
                #     bounds = batch_points.geometry().bounds().getInfo()
                #     print(f"    Batch bounds: {bounds}")
                # except Exception as e:
                #     print(f"    Error getting batch bounds: {e}")


                # Sample the batch
                sampled = gee_image.sampleRegions(
                    collection=batch_points,
                    scale=scale,
                    geometries=False,
                    tileScale=1
                )


                # Get batch results
                sampled_list = sampled.getInfo()['features']
                print(f"    Batch returned {len(sampled_list)} features")

                # Extract values and assign for this batch

                for feature in sampled_list:
                    cell_idx = feature['properties']['cell_id']
                    # Get the raster value (first property that's not cell_id)
                    raster_props = {k: v for k, v in feature['properties'].items() if k != 'cell_id'}
                    if raster_props:
                        value = list(raster_props.values())[0]
                        values[cell_idx] = value if value is not None else np.nan


                print(f"    Running total: {running_total} valid values so far")

            result_gdf[raster_name] = values
            print(f"✓ Successfully sampled {raster_name}")

            valid_data = [v for v in values if not np.isnan(v)]
            print(f"✓ {raster_name}: {len(valid_data)} valid values")
            if valid_data:
                print(f"  Sample values: {valid_data[:5]}")  # Show first 5 values
                print(f"  Range: {min(valid_data):.3f} to {max(valid_data):.3f}")

        except Exception as e:
            print(f"✗ Error sampling {raster_name}: {e}")
            result_gdf[raster_name] = np.nan

    # Save result with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    _output_path = output_path.with_stem(f"{output_path.stem}_{timestamp}")

    result_gdf.to_file(str(_output_path), driver=_to_file_driver)

    #output_path = output_path.replace('.gpkg', f'_{timestamp}.gpkg')

    print(f"Saved result to: {str(_output_path)}")

    return result_gdf

def check_raster_crs(gee_raster_dict):
    """Check the CRS of all GEE rasters"""

    print("Checking CRS of all rasters...")
    print("=" * 50)

    for raster_name, gee_image in gee_raster_dict.items():
        try:
            # Get image info
            img_info = gee_image.getInfo()

            # Extract CRS from the first band
            if 'bands' in img_info and len(img_info['bands']) > 0:
                crs = img_info['bands'][0].get('crs', 'Unknown')
                crs_transform = img_info['bands'][0].get('crs_transform', 'Unknown')
                dimensions = img_info['bands'][0].get('dimensions', 'Unknown')

                print(f"{raster_name}:")
                print(f"  CRS: {crs}")
                print(f"  Transform: {crs_transform}")
                print(f"  Dimensions: {dimensions}")
                print()
            else:
                print(f"{raster_name}: No band information available")
                print()

        except Exception as e:
            print(f"{raster_name}: Error getting info - {e}")
            print()

def sample_summer_2024():
    """
    Sample your existing GEE rasters for summer 2024
    """

    # Your existing grid file
    grid_file = DATA_DIR / "boundaries" / "coburg_30m_grid_from_gee.gpkg"

    # Your multi-band GEE assets
    # For summer 2024, you would use the appropriate Sentinel and Landsat assets
    sentinel_asset = ee.Image('users/christopherscott925/raster/Sentinel2_2024_Summer_Coburg_EPSG25832')
    landsat_asset = ee.Image('users/christopherscott925/raster/Landsat_2024_Summer_Coburg_EPSG25832')

    # Extract specific bands from your multi-band assets
    gee_rasters = {
        'NDVI': sentinel_asset.select([0],['NDVI']),      # Band 0
        'NDBI': sentinel_asset.select([1],['NDBI']),      # Band 1
        'MNDWI': sentinel_asset.select([2],['MNDWI']),    # Band 2
        'EVI': sentinel_asset.select([3],['EVI']),        # Band 3
        'NDMI': sentinel_asset.select([4],['NDMI']),      # Band 4
        'LST': landsat_asset.select([0],['LST_Celsius'])          # LST from Landsat asset
    }

    # Output path
    output_file = DATA_DIR / "fishnets" / "coburg_fishnet_summer_2024.gpkg"
    output_file.mkdir(exist_ok=True)

    # Sample rasters at grid centroids
    result = sample_gee_rasters_at_centroids(
        grid_file_path=grid_file,
        gee_raster_dict=gee_rasters,
        output_path=output_file,
        scale=30
    )

    # Print summary
    print(f"\nSummary for {len(result)} grid cells:")
    for col in ['NDVI', 'NDBI', 'MNDWI', 'EVI', 'NDMI', 'LST']:
        if col in result.columns:
            valid_data = result[col].dropna()
            if len(valid_data) > 0:
                print(f"{col}: {len(valid_data)} valid values, "
                      f"mean={valid_data.mean():.3f}, "
                      f"range=[{valid_data.min():.3f}, {valid_data.max():.3f}]")

    return result

def sample_winter_2021(grid_path, scale=30):
    """
    Example for winter 2021 (as shown in your screenshot)
    """



    # Using the asset from your screenshot
    sentinel_asset = ee.Image('users/christopherscott925/raster/Sentinel2_2021_Winter_Coburg_EPSG25832')
    landsat_asset = ee.Image('users/christopherscott925/raster/Landsat_2021_Winter_Coburg_EPSG25832')

    gee_rasters = {
        'NDVI': sentinel_asset.select([0],['NDVI']),      # Band 0
        'NDBI': sentinel_asset.select([1],['NDBI']),      # Band 1
        'MNDWI': sentinel_asset.select([2],['MNDWI']),    # Band 2
        'EVI': sentinel_asset.select([3],['EVI']),        # Band 3
        'NDMI': sentinel_asset.select([4],['NDMI']),      # Band 4
        'LST': landsat_asset.select([0],['LST_Celsius'])          # LST from Landsat asset
    }

    output_file = Path(f"{DATA_DIR}/fishnets/coburg_fishnet_winter_2021.gpkg")
    output_file.mkdir(exist_ok=True, parents=True)

    result = sample_gee_rasters_at_centroids(
        grid_file_path=grid_path,
        gee_raster_dict=gee_rasters,
        output_path=output_file,
        scale=scale
    )

    return result

if __name__ == "__main__":

    gee_init()

    # Run the sampling
    fishnet_result = sample_summer_2024()

# gee_init()
#
# sentinel_asset = ee.Image('users/christopherscott925/raster/Sentinel2_2021_Winter_Coburg_EPSG25832')
# landsat_asset = ee.Image('users/christopherscott925/raster/Landsat_2021_Winter_Coburg_EPSG25832_CORRECTED')
#
# gee_rasters = {
#         'LST': landsat_asset.select([0],['LST_Celsius']),
#         # 'NDVI': sentinel_asset.select([0],['NDVI']),      # Band 0
#         # 'NDBI': sentinel_asset.select([1],['NDBI']),      # Band 1
#         # 'MNDWI': sentinel_asset.select([2],['MNDWI']),    # Band 2 (you have MNDWI, not MNDWI)
#         # 'EVI': sentinel_asset.select([3],['EVI']),        # Band 3
#         # 'NDMI': sentinel_asset.select([4],['NDMI']),      # Band 4
#         #           # LST from Landsat
#     }
#
#
# grid_file = DATA_DIR / "boundaries" / "coburg_30m_grid_from_gee.gpkg"
# output_file = Path(f"{DATA_DIR}/fishnets/coburg_fishnet_winter_2021.gpkg")
# output_file.mkdir(exist_ok=True, parents=True)
#
# check_raster_crs(gee_rasters)
#
#
# result = sample_gee_rasters_at_centroids(
#     grid_file_path=grid_file,
#     gee_raster_dict=gee_rasters,
#     output_path=output_file,
#     scale=30
# )

# gee_init()


# sentinel_asset = ee.Image('users/christopherscott925/raster/Sentinel2_2021_Winter_Coburg_EPSG25832')
# landsat_asset = ee.Image('users/christopherscott925/raster/Landsat_2021_Winter_Coburg_EPSG25832')
#
# gee_rasters = {
#         'LST': landsat_asset.select(['LST_Celsius']),
#         'NDVI': sentinel_asset.select(['NDVI']),      # Band 0
#         'NDBI': sentinel_asset.select(['NDBI']),      # Band 1
#         'MNDWI': sentinel_asset.select(['MNDWI']),    # Band 2 (you have MNDWI, not MNDWI)
#         'EVI': sentinel_asset.select(['EVI']),        # Band 3
#         'NDMI': sentinel_asset.select(['NDMI']),      # Band 4
#                   # LST from Landsat
#     }
#
# studyArea = ee.Geometry.Rectangle([10.8, 50.2, 11.1, 50.3]);
#
# landsat_collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2').merge(
#     ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')
# ).filterBounds(studyArea).filterDate('2021-12-01', '2022-02-28').filter(ee.Filter.lt('CLOUD_COVER', 20))
#
# landsat_median = landsat_collection.median()
# lst_processed = landsat_median.select('ST_B10').multiply(0.00341802).add(149.0).subtract(273.15)
#
# gee_rasters['LST_Celsius'] = lst_processed
#
# print(gee_rasters['LST_Celsius'])