# src/UHI/extract_roof_areas.py

import sys
from osgeo import gdal


from UHI.config import *
import UHI.pyqgis_init
from UHI.pyqgis_init import (qgs, QgsVectorLayer, QgsProcessingFeedback, QgsProject, QgsCoordinateReferenceSystem,
                             QgsVectorFileWriter, project)

from pathlib import Path
import processing
import ogr2ogr
import gdaltools
import os
import subprocess
import shutil
from osgeo import ogr
import fiona
import psycpg2

########## ##############################

# Create a fresh Postgres database with proper owner:
#
#     Use psycopg2 or subprocess running createdb and psql commands
#
# Enable PostGIS & SFCGAL extensions:
#
#     Run CREATE EXTENSION postgis; and CREATE EXTENSION sfcgal; via SQL execution
#
# Load your CityGML files into the database:
#
#     Use subprocess to call the 3dcitydb command line importer, passing your GML files and DB connection details
#
# Preprocess/clean GML files if needed (e.g., strip unnecessary attributes)
#
# Merge the loaded GML layers into one layer programmatically in PyQGIS:
#
#     Use PyQGIS vector layer merging utilities or SQL to aggregate spatial data
#
# Run your aggregation SQL query (like the roof area sum per building) through Python DB connection:
#
#     psycopg2 or sqlalchemy to execute your queries and create tables/views with summaries
#
# Load the spatial layer and join the aggregated table in PyQGIS:
#
#     Use PyQGIS API to add the join to your building layer attributes
#
# Use or export the joined layer as needed for analysis or visualization


# Create postgres database



subprocess.run([
    "psql",
    "-U", PGADMIN,
    "-c", f"CREATE USER {PGCITYDBUSER} PASSWORD {PGCITYDBUSER_PASSWORD}"
], check=True)

subprocess.run([
    "psql",
    "-U", PGADMIN,
    "-c", f"CREATE DATABASE {PGCITYDB} OWNER {PGCITYDBUSER}"
], check=True)


psql_string = f"postgresql://{PGADMIN}@{PGHOST}:5432/{PGCITYDB}?password={PGCITYDBUSER_PASSWORD}"

subprocess.run([
    "psql", psql_string,
    "-c", f"CREATE EXTENSION postgis;"
], check=True)

subprocess.run([
    "psql", psql_string,
    "-c", f"CREATE EXTENSION postgis_sfcgal;"
], check=True)


with open(F"{CITYDB_SCRIPT_DIR}/connection-details_pycharmtest.bat", "w") as f:
    f.write("set PGBIN=C:\\Program Files\\PostgreSQL\\17\\bin\\\n"
            f"set PGHOST={PGHOST}\n"
            f"set PGPORT=5432\n"
            f"set CITYDB={PGCITYDB}\n"
            f"set PGUSER={PGCITYDBUSER}\n")




conn = psycopg2.connect(
    dbname=PGCITYDB,
    user="postgres",
    password="1234",
    host=PGHOST
)