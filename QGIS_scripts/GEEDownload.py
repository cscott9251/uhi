import ee
import geemap

ee.Initialize()

#Define region of interest (e.g. Coburg bounding box)
roi = ee.Geometry.BBox(10.9, 50.2, 11.1, 50.3)

# Load Landsat 8 C2 L2 Tier 1 with LST
landsat = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
    .filterBounds(roi) \
    .filterDate("2022-06-01", "2022-06-30") \
    .map(lambda img: img.select(['ST_B10']).clip(roi))
    
#image = landsat.first()
#geemap.ee_export_image(image, filename='landsat_lst.tif', scale=100, region=roi)

imagepath = "C:/Users/chris/OneDrive/Documents/landsat_lst.tif"

raster_layer = iface.addRasterLayer(imagepath, "LST - Landsat")

if raster_layer.isValid():
    print("Raster loaded successfully.")
else:
    print("Failed to load raster.")