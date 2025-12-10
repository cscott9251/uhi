from UHI.config import *
from UHI.pyqgis.pyqgis_init import QgsDataSourceUri, QgsVectorFileWriter
from UHI.ss.lod2_proc_qgis import strip_fields
from UHI.pyqgis.pyqgis_init import QgsVectorLayer
from UHI.citydb_sql_calculate_roof_area import connect_to_3dcitydb
from UHI.gridgen import generate_grid
import processing

import geopandas as gpd
import pandas as pd
import fiona

def merge_layers(layers, merged_layer_name="merged_gml_pycharm", output_path="memory:"):

    #output_path.mkdir(exist_ok=True)

    if not layers:
        raise ValueError("No layers provided for merging.")

    layer_sources = [layer.source() if isinstance(layer, QgsVectorLayer) else layer for layer in layers]

    print("Merging...")

    result = processing.run("native:mergevectorlayers", {
        'LAYERS': layers,
        'CRS': CRS,             # Set CRS explicitly if you want to force reprojection
        'OUTPUT': str(output_path)
    })

    merged_layer_object = result

    print("Done!")

    return merged_layer_object





def fetch_roof_area_mapping():

    sql_string = "SELECT building_objectid, total_roof_area FROM citydb.roof_area_per_building;"

    conn = connect_to_3dcitydb()

    cur = conn.cursor()

    cur.execute(sql_string)

    rows = cur.fetchall()

    conn.close()

    # Convert to dictionary: {building_object_id: roof_area}
    roof_area_dict = {str(gmlid): float(total_roof_area) for gmlid, total_roof_area in rows if total_roof_area is not None}

    return roof_area_dict


def join_roof_area_to_layer(merged_layer: QgsVectorLayer, gml_id_field="gml_id",
                            roof_table_key="building_objectid", roof_area_field="total_roof_area", output_path=None):

    out = LOD2_DIR / "pycharm_roof_areas_qgs_merged"
    out.mkdir(exist_ok=True)

    uri = QgsDataSourceUri()
    uri.setConnection("localhost", "5432", "citydbtestpycharm", "postgres", "1234")
    uri.setDataSource("citydb", "roof_area_per_building", "", "", "building_objectid")  # Adjust geom field name

    pg_layer = QgsVectorLayer(uri.uri(False), "roof_area_per_building", "postgres")
    if not pg_layer.isValid():
        raise RuntimeError("Failed to load PostGIS layer")

    pg_layer = QgsVectorLayer(uri.uri(False), "roof_area_per_building", "postgres")

    # Join using QGIS algorithm
    result = processing.run("native:joinattributestable", {
        'INPUT': merged_layer,
        'FIELD': "gml_id",
        'INPUT_2': pg_layer,
        'FIELD_2': "building_objectid",
        'FIELDS_TO_COPY': [roof_area_field],
        'METHOD': 1,  # Take attributes of first matching feature
        'DISCARD_NONMATCHING': False,
        'OUTPUT': output_path,
    })

    return result


def roofs_to_gdf(layer: QgsVectorLayer, fields=None):
    """Convert QGIS vector layer to GeoDataFrame in memory."""
    features = layer.getFeatures()
    data = []

    for feat in layer.getFeatures():
        record = {field: feat[field] for field in fields}
        data.append(record)


    return gpd.GeoDataFrame(data)



stripped_dir = LOD2_DIR / "pycharm_stripped"

cleaned_layers_global = strip_fields(LOD2_DIR_ORIG)

merged_layer_global = merge_layers(cleaned_layers_global)["OUTPUT"]

QgsVectorFileWriter.writeAsVectorFormat(
    merged_layer_global,
    f"{LOD2_DIR}/merged_layer.gpkg",
    "utf-8",
    driverName="GPKG"
)

with fiona.Env():
    with fiona.open(f"{LOD2_DIR}/merged_layer.gpkg") as src:
        # Optional: inspect geometry types
        print(set(feat["geometry"]["type"] for feat in src))


merged_gdf = gpd.read_file(f"{LOD2_DIR}/merged_layer.gpkg", engine="fiona")

merged_gdf.set_crs("EPSG:25832", inplace=True)

merged_gdf = merged_gdf[["gml_id", "geometry"]]

roofs = join_roof_area_to_layer(merged_layer_global, output_path="memory:")["OUTPUT"]

roofs_gdf = roofs_to_gdf(roofs, fields=["gml_id", "total_roof_area"])

roof_gdf = roofs_gdf[["gml_id", "total_roof_area"]]

roof_with_geom_df = pd.merge(roofs_gdf, merged_gdf, on="gml_id", how="left")

roof_with_geom_gdf = gpd.GeoDataFrame(roof_with_geom_df, geometry='geometry', crs=merged_gdf.crs)

roof_with_geom_gdf.set_crs("EPSG:25832", inplace=True)


print(roofs_gdf.columns)
#print(roofs_gdf.geometry.name)
print(roofs_gdf.head())

grid_gdf = generate_grid(BOUNDARY_PATH)

print(grid_gdf.head())

joined = gpd.sjoin(roof_with_geom_gdf, grid_gdf, how="inner", predicate="intersects")

roof_area_per_grid = joined.groupby("grid_id")["total_roof_area"].sum().reset_index()

wipgdf = gpd.read_file(f"{PROCESSED_DATA_DIR}\\geodataframe_newwip.json")

wipgdf = wipgdf.drop(columns=['floor_area'])

print(wipgdf.columns)


if 'fid' in wipgdf.columns:
    wipgdf = wipgdf.rename(columns={'fid': 'original_fid'})
    print("🔄 Renamed fid column to original_fid to preserve it")

wipgdf.to_file(f"{PROCESSED_DATA_DIR}\\geodataframe_newwip_cleaned.gpkg", driver="GPKG")


print(wipgdf.head())

newwipgdf = wipgdf.merge(roof_area_per_grid, on="grid_id", how="left")

#newwipgdf.to_file(f"{PROCESSED_DATA_DIR}\\geodataframe_newwip.json", driver="GeoJSON")

#newwipgdf['fid'] = pd.to_numeric(newwipgdf['fid'], downcast='integer', errors='coerce')

newwipgdf.to_file(f"{PROCESSED_DATA_DIR}\\geodataframe_newwip_cleaned_roof_grid.gpkg", driver="GPKG")




