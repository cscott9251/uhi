"""
Simple extraction of LST, NDVI, NDWI, NDBI from Landsat-8 for Coburg
Saves CSV files for each time period
"""
import sys

from UHI.config import *
from UHI.gee_init import gee_init

import ee
import geemap
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Point
import matplotlib.pyplot as plt

def initialise_gee():

    gee_init()


def load_gee_asset_to_geodataframe(asset_id, sample_scale=30, max_pixels=100000):

    """
    Load a GEE asset with pre-calculated indices and convert to GeoDataFrame

    Parameters:
    - asset_id: Path to your GEE asset
    - sample_scale: Pixel size for sampling (meters)
    - max_pixels: Maximum number of pixels to sample (for memory management)
    """

    print(f"Loading asset: {asset_id}")

    # 1. Load the image from GEE
    image = ee.Image(asset_id)

    # 2. Print image info
    print("Image bands:", image.bandNames().getInfo())
    print("Image projection:", image.projection().getInfo())

    # 3. Check what type of asset this is based on available bands
    band_names = image.bandNames().getInfo()

    if 'LST_Celsius' in band_names:
        # This is a Landsat asset with LST
        print("Detected Landsat asset with LST")
        bands_to_sample = ['LST_Celsius']
        sample_image = image.select(bands_to_sample)

    elif 'NDVI' in band_names:
        # This is a Sentinel-2 asset with pre-calculated indices
        print("Detected Sentinel-2 asset with pre-calculated indices")

        # Get all available index bands
        available_indices = []
        index_bands = ['NDVI', 'NDBI', 'MNDWI', 'EVI', 'NDMI']

        for band in index_bands:
            if band in band_names:
                available_indices.append(band)

        print(f"Available indices: {available_indices}")
        bands_to_sample = available_indices
        sample_image = image.select(bands_to_sample)

    else:
        raise ValueError(f"Cannot determine asset type from band names: {band_names}")

    # 4. Get the image geometry for sampling
    geometry = image.geometry()

    # 5. Sample the image to get pixel values with coordinates
    sample = sample_image.sample(
        region=geometry,
        scale=sample_scale,
        numPixels=max_pixels,
        geometries=True  # Include coordinates
    )

    print(f"Sampling {sample.size().getInfo()} pixels...")

    # 6. Convert to Python data structure
    sample_data = sample.getInfo()

    # 7. Extract coordinates and values
    rows = []
    for feature in sample_data['features']:
        coords = feature['geometry']['coordinates']
        props = feature['properties']

        # Create row with coordinates and all available bands
        row = {
            'longitude': coords[0],
            'latitude': coords[1]
        }

        # Add all sampled bands to the row
        for band in bands_to_sample:
            row[band] = props.get(band)

        rows.append(row)

    # 8. Create DataFrame
    df = pd.DataFrame(rows)

    # 9. Remove any rows with null values
    df = df.dropna()

    print(f"Created DataFrame with {len(df)} valid pixels")

    # Print statistics for each band
    for band in bands_to_sample:
        if band in df.columns:
            print(f"{band} range: {df[band].min():.3f} to {df[band].max():.3f}")

    # 10. Create Point geometries from coordinates
    geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]

    # 11. Create GeoDataFrame
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')

    # 12. Reproject to match your study area (EPSG:25832)
    gdf = gdf.to_crs('EPSG:25832')

    print(f"GeoDataFrame created with CRS: {gdf.crs}")

    return gdf

def save_and_visualize_gdf(gdf, output_path, value_column='NDVI'):

    """
    Save GeoDataFrame and create a simple visualization
    """

    # Save to file
    gdf.to_file(output_path, driver='GPKG')  # GeoPackage format
    print(f"GeoDataFrame saved to: {output_path}")

    # Simple visualization
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))

    # Check if the column exists
    if value_column in gdf.columns:

        # Choose colormap based on the variable
        if value_column == 'LST_Celsius':
            # For LST: Blue (cool) to Red (hot)
            colormap = 'jet'
            title_suffix = '(°C)'
        elif value_column in ['NDVI', 'EVI']:
            # For vegetation: Red (low) to Green (high)
            colormap = 'RdYlGn'
            title_suffix = ''
        elif value_column in ['NDBI']:
            # For built-up: Green (low) to Red (high)
            colormap = 'RdYlGn_r'  # Reversed
            title_suffix = ''
        else:
            # Default colormap
            colormap = 'viridis'
            title_suffix = ''


        gdf.plot(column=value_column,
                 cmap=colormap,  # Red-Yellow-Green colormap
                 legend=True,
                 ax=ax,
                 markersize=1)
        ax.set_title(f'{value_column} Values from GEE Asset')

        # Print statistics
        print(f"\n{value_column} Statistics:")
        print(gdf[value_column].describe())
    else:
        # Just plot points if no specific column
        gdf.plot(ax=ax, markersize=1, color='blue')
        ax.set_title('Sample Points from GEE Asset')
        print(f"\nAvailable columns: {list(gdf.columns)}")

    ax.set_xlabel('Easting (m)')
    ax.set_ylabel('Northing (m)')

    plt.tight_layout()
    plt.show()



# Example usage
if __name__ == "__main__":


    # Initialise

    initialise_gee()

    #

    s2_asset_id = "users/christopherscott925/raster/Sentinel2_2023_Summer_Coburg_EPSG25832"

    try:
        # Load Sentinel-2 asset
        print("=== Loading Sentinel-2 Asset ===")
        s2_gdf = load_gee_asset_to_geodataframe(
            asset_id=s2_asset_id,
            sample_scale=30,  # 30m to match Landsat resolution
            max_pixels=10000   # Adjust based on your area size and memory
        )

        # Save and visualize NDVI
        save_and_visualize_gdf(s2_gdf, f"{PROCESSED_DATA_DIR}\\coburg_sentinel2_indices.gpkg", 'NDVI')

        print(f"\nFirst 5 rows of Sentinel-2 data:")
        print(s2_gdf.head())

    except Exception as e:
        print(f"Error loading Sentinel-2 asset: {e}")

    # Example: Load Landsat asset with LST
    landsat_asset_id = "users/christopherscott925/raster/Landsat_2023_Summer_Coburg_EPSG25832"

    try:
        print("\n=== Loading Landsat Asset ===")
        landsat_gdf = load_gee_asset_to_geodataframe(
            asset_id=landsat_asset_id,
            sample_scale=30,
            max_pixels=5000
        )

        # Save and visualize LST
        save_and_visualize_gdf(landsat_gdf, "coburg_landsat_lst.gpkg", 'LST_Celsius')

        print(f"\nFirst 5 rows of Landsat data:")
        print(landsat_gdf.head())

    except Exception as e:
        print(f"Error loading Landsat asset: {e}")

# Alternative: Load multiple assets and combine them
def load_and_combine_assets(landsat_asset_id, sentinel2_asset_id):
    """
    Load both Landsat (LST) and Sentinel-2 (indices) assets and combine them
    """

    print("=== Loading and Combining Assets ===")

    # Load LST data
    lst_gdf = load_gee_asset_to_geodataframe(landsat_asset_id, sample_scale=30, max_pixels=5000)

    # Load indices data
    indices_gdf = load_gee_asset_to_geodataframe(sentinel2_asset_id, sample_scale=30, max_pixels=5000)

    # For combining, you'd need to spatially join or match coordinates
    # This is a simple example - in practice you might need more sophisticated spatial matching
    print(f"LST data: {len(lst_gdf)} points")
    print(f"Indices data: {len(indices_gdf)} points")

    return lst_gdf, indices_gdf

# Test the combination function
# lst_data, indices_data = load_and_combine_assets(landsat_asset_id, s2_asset_id)