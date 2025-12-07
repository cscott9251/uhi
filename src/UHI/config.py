# src/UHI/config.py

from pathlib import Path

CONFIG_FILE = Path(__file__).resolve()


configdict = {}
configlist = []
configtuple = ()


# Get absolute path to the installed UHI package directory
PACKAGE_ROOT = CONFIG_FILE.parents[2]
configdict["PACKAGE_ROOT"] = PACKAGE_ROOT
configlist.append(PACKAGE_ROOT)

CODE_ROOT = CONFIG_FILE.parents[0]

DATA_DIR = PACKAGE_ROOT / "data"
configdict["DATA_DIR"] =  DATA_DIR
configlist.append(DATA_DIR)

CRS = "EPSG:25832"
configdict["CRS"] = CRS
configlist.append(CRS)

BOUNDARY_PATH = DATA_DIR / "boundaries" / "CoburgGrenze2.shp"
configdict["BOUNDARY_PATH"] = BOUNDARY_PATH
configlist.append(BOUNDARY_PATH)

GRID_PATH = DATA_DIR / "processed" / "grid_100m_coburg.gpkg"
configdict["GRID_PATH"] = GRID_PATH
configlist.append(GRID_PATH)

GRID_30M_PATH = DATA_DIR / "boundaries" / "coburg_30m_grid_from_gee.gpkg"

CELL_SIZE = 100  # meters
configdict["CELL_SIZE"] = CELL_SIZE
configlist.append(CELL_SIZE)

LOD2_DIR = DATA_DIR / "lod2"  # For LoD2 GML files
configdict["LOD2_DIR"] = LOD2_DIR
configlist.append(LOD2_DIR)

LOD2_DIR_ORIG = DATA_DIR / "lod2" / "original_gml"

LOD2_FLATTENED_DIR = LOD2_DIR / "flattened"

LOD2_GPKG_PATH = DATA_DIR / "processed" / "coburg_lod2_merged6.gpkg"
configdict["LOD2_GPKG_PATH"] = LOD2_GPKG_PATH
configlist.append(LOD2_GPKG_PATH)

LOD2_MERGED_PATH = LOD2_DIR / "pycharm_merged" / 'pycharm_merged.gml'

HAUSUMRINGE_SHP_PATH  = DATA_DIR / "Building_footprints" / "094_Oberfranken_Hausumringe" / "hausumringe.shp"
configdict["HAUSUMRINGE_SHP_PATH"] = HAUSUMRINGE_SHP_PATH
configlist.append(HAUSUMRINGE_SHP_PATH)

HAUSUMRINGE_SHP_DIR =  DATA_DIR / "Building_footprints" / "094_Oberfranken_Hausumringe"
configdict["HAUSUMRINGE_SHP_DIR"] = HAUSUMRINGE_SHP_DIR
configlist.append(HAUSUMRINGE_SHP_DIR)

PROCESSED_DATA_DIR = DATA_DIR / "processed"

FISHNETS_DATA_DIR = DATA_DIR / "fishnets"

CITY_DB_DIR = PACKAGE_ROOT / "3dcitydb"

CITYDB_SCRIPT_DIR  = CITY_DB_DIR / "postgresql" / "shell-scripts" / "windows"

CITY_DB_SQL_DIR = CITY_DB_DIR / "postgresql" / "sql-scripts"

CITY_TOOL_DIR = CITY_DB_DIR / "citydb-tool"

SQL_DIR = CODE_ROOT / "sql"

PGCITYDB = "citydbtestpycharm"
PGCITYDBUSER = "citydb_user_testpycharm"
PGCITYDBUSER_PASSWORD = "1234"
PGADMIN = "postgres"
PGADMIN_PASSWORD = PGCITYDBUSER_PASSWORD
PGPORT = "5432"
PGHOST = "localhost"

# PGCONN = {
#     CITYDB
# }







# print("\nℹ️ PROJECT PATHS & VARIABLES ℹ️\n")
# print("⚠️ PLEASE VERIFY THAT  THESE ARE CORRECT ⚠️\n")
# for name, path in configdict.items():
#     print("ℹ️" + f" {name} => {path}")