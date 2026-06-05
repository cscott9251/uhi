from UHI.config import *
import subprocess

from UHI.morphological import citydb_sql_calculate_floor_area as floor, \
    citydb_sql_calculate_height as height, citydb_sql_calculate_roof_area as roof, citydb_sql_calculate_volumes as volumes, \
          citydb_sql_total_building_data as total

def calculate_building_metrics_pipeline():

    floor.floor_area()
    height.height()
    roof.roof_area()
    volumes.volumes()
    total.total_building_data()


#calculate_building_metrics_pipeline()