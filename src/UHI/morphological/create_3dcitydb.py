# src/UHI/create_3dcitydb.py

import sys
from osgeo import gdal


from UHI.config import *
import UHI.pyqgis.pyqgis_init
from UHI.pyqgis.pyqgis_init import (qgs, QgsVectorLayer, QgsProcessingFeedback, QgsProject, QgsCoordinateReferenceSystem,
                             QgsVectorFileWriter, project)

from pathlib import Path
# import processing
# import ogr2ogr
# import gdaltools
import os
import subprocess
import shutil
#from osgeo import ogr
import fiona
import psycopg2
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy import create_engine
import sqlite3

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

engine = create_engine(f'postgresql+psycopg2://{PGCITYDBUSER}:{PGCITYDBUSER_PASSWORD}@{PGHOST}/{PGCITYDB}')
psql_string = f"postgresql://{PGADMIN}:{PGCITYDBUSER_PASSWORD}@{PGHOST}:5432/{PGCITYDB}"

if not database_exists(engine.url):
    print(f"[INFO] Database {PGCITYDB} does not exist, creating it with the following parameters:\n")
    print(f"[INFO] Owner: {PGCITYDBUSER}")
    print(f"[INFO] Password: 1234")
    print(f"[INFO] Host: {PGHOST}")



    subprocess.run([
        "psql",
        "-U", PGADMIN,
        "-c", f"CREATE USER {PGCITYDBUSER} PASSWORD '{PGCITYDBUSER_PASSWORD}'"
    ], check=True, text=True)

    subprocess.run([
        "psql",
        "-U", PGADMIN,
        "-c", f"CREATE DATABASE {PGCITYDB} OWNER {PGCITYDBUSER}"
    ], check=True)

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

    print("Done creating database and setting connection details")

elif database_exists(engine.url):

    subprocess.run([
        "psql", psql_string,
        "-v", "srid=25832",
        "-v", "srs_name=urn:adv:crs:ETRS89_UTM32*DE_DHHN2016_NH",
        "-v", "changelog=YES",
        "-v", f"DBNAME={PGCITYDB}",
        "-f", str(CITY_DB_SQL_DIR / "create-db.sql")
    ], check=True)

