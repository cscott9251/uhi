from UHI.config import *
import UHI.gee_init

import ee

from UHI.gee_init import gee_init

# Export to Google Drive
# task = ee.batch.Export.image.toDrive(
#     image=your_image,
#     description='my_raster_export',
#     folder='GEE_exports',
#     fileNamePrefix='my_raster',
#     region=geometry,
#     scale=30,
#     crs='EPSG:4326',
#     maxPixels=1e9
# )
# task.start()

gee_init()

folder_path = 'users/christopherscott925/raster_masked'

asset_list = ee.data.listAssets({'parent': folder_path})

print(f"Found {len(asset_list['assets'])} assets in the folder")

print(f"The following assets were found in {'/'.join(asset_list['assets'][0]['name'].split('/')[:-1])}:\n")

for asset in asset_list['assets']:

    print(asset['name'].split('/')[-1])


# test = asset_list['assets']
#
# print(type(test))
# print(test)

