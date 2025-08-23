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
    Load a GEE asset, calculate NDVI, and convert to GeoDataFrame

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

    #sys.exit()

    # 3. Calculate NDVI
    # For Sentinel-2: (B8 - B4) / (B8 + B4)
    # For Landsat: (SR_B5 - SR_B4) / (SR_B5 + SR_B4)

    # Check if it's Sentinel-2 or Landsat based on band names
    band_names = image.bandNames().getInfo()

    if 'B8' in band_names and 'B4' in band_names:
        # Sentinel-2
        print("Detected Sentinel-2 image")
        ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
        nir_band = 'B8'
        red_band = 'B4'
    elif 'SR_B5' in band_names and 'SR_B4' in band_names:
        # Landsat
        print("Detected Landsat image")
        ndvi = image.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
        nir_band = 'SR_B5'
        red_band = 'SR_B4'
    else:
        raise ValueError("Cannot determine sensor type from band names")

    #sys.exit()


    # 4. Get the image geometry for sampling
    geometry = image.geometry()

    # 5. Sample the image to get pixel values with coordinates
    # This converts raster to points
    sample = ndvi.addBands(image.select([nir_band, red_band])).sample(
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

        row = {
            'longitude': coords[0],
            'latitude': coords[1],
            'NDVI': props.get('NDVI'),
            'NIR': props.get(nir_band),
            'Red': props.get(red_band)
        }
        rows.append(row)

    # 8. Create DataFrame
    df = pd.DataFrame(rows)

    # 9. Remove any rows with null values
    df = df.dropna()

    print(f"Created DataFrame with {len(df)} valid pixels")
    print(f"NDVI range: {df['NDVI'].min():.3f} to {df['NDVI'].max():.3f}")

    # 10. Create Point geometries from coordinates
    geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]

    # 11. Create GeoDataFrame
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')

    # 12. Reproject to match your study area (EPSG:25832)
    gdf = gdf.to_crs('EPSG:25832')

    print(f"GeoDataFrame created with CRS: {gdf.crs}")

    return gdf

def save_and_visualize_gdf(gdf, output_path):
    """
    Save GeoDataFrame and create a simple visualization
    """

    # Save to file
    gdf.to_file(output_path, driver='GPKG')  # GeoPackage format
    print(f"GeoDataFrame saved to: {output_path}")

    # Simple visualization
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))

    gdf.plot(column='NDVI',
             cmap='RdYlGn',  # Red-Yellow-Green colormap
             legend=True,
             ax=ax,
             markersize=1)

    ax.set_title('NDVI Values from GEE Asset')
    ax.set_xlabel('Easting (m)')
    ax.set_ylabel('Northing (m)')

    plt.tight_layout()
    plt.show()

    # Print statistics
    print("\nNDVI Statistics:")
    print(gdf['NDVI'].describe())

# Example usage
if __name__ == "__main__":


    # Initialise

    initialise_gee()

    # Your GEE asset path (change this to your actual asset)
    asset_id = "users/christopherscott925/raster/Sentinel2_2023_Summer_Coburg_EPSG25832"

    try:
        # Load and process the asset
        gdf = load_gee_asset_to_geodataframe(
            asset_id=asset_id,
            sample_scale=30,  # 10m for Sentinel-2, 30m for Landsat
            max_pixels=10000   # Adjust based on your area size and memory
        )

        # Save and visualize
        output_path = f"{PROCESSED_DATA_DIR}\\coburg_ndvi_sample.gpkg"
        save_and_visualize_gdf(gdf, output_path)

        # Example of accessing the data
        print(f"\nFirst 5 rows:")
        print(gdf[['NDVI', 'NIR', 'Red']].head())

        # Example analysis
        high_vegetation = gdf[gdf['NDVI'] > 0.5]
        print(f"\nPixels with high vegetation (NDVI > 0.5): {len(high_vegetation)}")

    except Exception as e:
        print(f"Error: {e}")
        print("Make sure:")
        print("1. You're authenticated with Earth Engine")
        print("2. The asset exists and you have access")
        print("3. The asset has the expected band names")



# initialise_gee()
#
# ndvi_gdf = load_gee_asset_to_geodataframe("users/christopherscott925/raster/Sentinel2_2021_Summer_Coburg_EPSG25832")
# print(ndvi_gdf.head())