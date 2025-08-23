# src/UHI/floor_areas.py

import sys
import geopandas as gpd

import UHI.config
import UHI.pyqgis_init
from UHI.pyqgis_init import QgsVectorLayer, QgsVectorFileWriter
from UHI.config import *
import processing
from pathlib import Path


hausumringe_path = str(HAUSUMRINGE_SHP_PATH)



def verify_hausumringe(footprint_path, output_path=f"{str(PROCESSED_DATA_DIR)}\\reprojected_hausumringe.gpkg"):

    print("🔧 Verifying building footprints shapefile / layer... ")

    print(f"🔧 Using footprints shapefile at {hausumringe_path}... ")

    hausumringe = QgsVectorLayer(str(footprint_path), "hausumringe", "ogr")
    crs = hausumringe.crs().authid()
    print(crs)
    print(CRS)

    #sys.exit()

    if not hausumringe.isValid():
        print("⚠️ Layer not valid, execution aborting...")
    else:

        print("✅ Shapefile / layer is valid!")
        print("ℹ️ CRS of Hausumringe:", crs)  # e.g., "EPSG:25832" or "EPSG:4326"

        if crs != CRS:
            print(f"⚠️ CRS of Hausumringe is in {crs} not in {CRS}, reprojecting... ")
            hausumringe_reproject = processing.run("native:reprojectlayer", {
                'INPUT': hausumringe,
                'TARGET CRS': CRS,
                'OUTPUT': output_path

            }
            )['OUTPUT']
            print(f"✅ CRS of Hausumringe reprojected to {CRS}, saved to {output_path}. ")

            if hausumringe_reproject is None:
                print("❌ Failed to load reprojected hausumringe layer. Exiting.")
                sys.exit(1)

            return hausumringe_reproject, False
        else:
            print(f"✅ CRS of Hausumringe matches projet CRS, {CRS}")

            if hausumringe is None:
                print("❌ Failed to load hausumringe layer. Exiting.")
                sys.exit(1)


            return hausumringe, True






def clip_hausumringe(verified_hausumringe, boundary_path, output_path="memory:"):


    if verified_hausumringe is None:
        print("⚠️ Input layer is None, cannot clip.")
        return None

    print("✅ Valid input layer!\n🔧 Clipping to boundary...")

    # Load boundary layer
    boundary_layer = QgsVectorLayer(str(boundary_path), "boundary", "ogr")
    if not boundary_layer.isValid():
        print("⚠️ Boundary layer is not valid!")
        return None

    params = {
        'INPUT': verified_hausumringe,
        'OVERLAY': boundary_layer,  # Pass layer object, not path
        'OUTPUT': str(output_path)
    }

    result = processing.run("native:clip", params)

    if result is None:
        print("❌ Failed to clip hausumringe. Exiting.")
        sys.exit(1)



    return result['OUTPUT']  # Return just the output layer



def calculate_area(clipped_buildings, output_path="memory:"):

    if clipped_buildings is None:
        print("⚠️ Input layer is None, cannot calculate area.")
        return None

    params = {

        'INPUT': clipped_buildings,
        'FIELD_NAME': 'floor_area',
        'FIELD_TYPE': 0,  # Double
        'FIELD_LENGTH': 20,
        'FIELD_PRECISION': 2,
        'FORMULA': 'area($geometry)',
        'OUTPUT': str(output_path)
    }


    result = processing.run("native:fieldcalculator", parameters=params)

    if result["OUTPUT"] is None:
        print("❌ Failed to calculate areas. Exiting.")
        sys.exit(1)

    if isinstance(result["OUTPUT"], str):
        areas_layer = QgsVectorLayer(str(result["OUTPUT"]), "areas", "ogr")
        print("Fields in areas layer:")
        #print([field.name() for field in areas_layer.fields()])
    else:
        areas_layer = result["OUTPUT"]
        print("Fields in areas layer:")
        #print(areas_layer.fields())

    print("Fields in areas layer:")
    print([field.name() for field in areas_layer.fields()])

    # Print output information
    if output_path == "memory:":
        print("✅ Area calculation completed - output stored in memory")
    else:
        print(f"✅ Area calculation completed - output saved to: {output_path}")


    return result["OUTPUT"]



def overlap_intersection_weighting(grid_path, hausumringe_areas_layer, out="memory:"):

    if hausumringe_areas_layer is None:
        print("⚠️ Hausumringe areas layer is None, cannot calculate overlaps.")
        return None

    # Load grid layer
    grid_layer = QgsVectorLayer(str(grid_path), "grid", "ogr")
    if not grid_layer.isValid():
        print("⚠️ Grid layer is not valid!")
        return None

    print("Fields in grid layer:")
    print([field.name() for field in grid_layer.fields()])
    print("Grid CRS:", grid_layer.crs().authid())

    # Check if hausumringe_areas_layer is already a QgsVectorLayer
    if isinstance(hausumringe_areas_layer, str):
        buildings_layer = QgsVectorLayer(str(hausumringe_areas_layer), "hausumringe", "ogr")
    else:
        buildings_layer = hausumringe_areas_layer

    print("Fields in buildings layer:")
    print([field.name() for field in buildings_layer.fields()])
    print("Buildings CRS:", buildings_layer.crs().authid())

    # Fixed: Pass layer objects, not paths, and use correct parameter structure
    result = processing.run("native:calculatevectoroverlaps", {
        'INPUT': grid_layer,
        'LAYERS': [buildings_layer],  # Note: this should be a list
        'OUTPUT': str(out),
        'GRID_SIZE': None
    })

    if result is None:
        print("❌ Failed to calculate overlaps. Exiting.")
        sys.exit(1)

    if isinstance(result['OUTPUT'], str):
        overlap_layer = QgsVectorLayer(str(result['OUTPUT']), "overlap", "ogr")
    else:
        overlap_layer = result['OUTPUT']

    print("Fields in overlap layer:")
    print([field.name() for field in overlap_layer.fields()])

    if out == "memory:":
        print("✅ Overlap analysis completed - output stored in memory")
    else:
        print(f"✅ Overlap analysis completed - output saved to: {out}")


    return result['OUTPUT']



def aggregate_to_grid(overlap, output_path="memory:"):

    if output_path != "memory:" and hasattr(output_path, 'parent'):
        output_path.parent.mkdir(parents=True, exist_ok=True)

    if overlap is None:
        print("⚠️ Overlap layer is None, cannot aggregate.")
        return None

    if isinstance(overlap, str):
        layer = QgsVectorLayer(str(overlap), "overlap", "ogr")
    else:
        layer = overlap

    field_names = [field.name() for field in layer.fields()]
    print(f"Available fields for aggregation: {field_names}")

    hausumringe_aggregated = processing.run("native:aggregate",{
        'INPUT': overlap,
        'GROUP_BY':'"grid_id"',
        'AGGREGATES':[{
            'aggregate': 'sum',
            'delimiter': ',',
            'input': '"output_area"',
            'length': 0,
            'name': 'floor_area_per_grid',
            'precision': 0,'sub_type': 0,
            'type': 6,
            'type_name': 'double precision'
        }],
        'OUTPUT': str(output_path)
    })

    if hausumringe_aggregated is None:
        print("❌ Failed to aggregate to grid. Exiting.")
        sys.exit(1)

    if output_path == "memory:":
        print("✅ Aggregation completed - output stored in memory")
    else:
        print(f"✅ Aggregation completed - output saved to: {output_path}")

    return hausumringe_aggregated['OUTPUT']


def join_aggregate_and_grid_ids(aggregated, grid, out="memory:"):

    if out != "memory:" and hasattr(out, 'parent'):
        out.parent.mkdir(parents=True, exist_ok=True)

    if aggregated is None:
        print("⚠️ Aggregated layer is None, cannot join.")
        return None

    if isinstance(aggregated, str):
        agg_layer = QgsVectorLayer(str(aggregated), "aggregated", "ogr")
    else:
        agg_layer = aggregated

    if not agg_layer.isValid():
        print("⚠️ Aggregated layer is not valid!")
        print(f"Aggregated layer source: {agg_layer.source() if hasattr(agg_layer, 'source') else 'Unknown'}")
        return None

    print(f"✅ Aggregated layer is valid with {agg_layer.featureCount()} features")
    print("Fields in aggregated layer:", [field.name() for field in agg_layer.fields()])

    grid_layer = QgsVectorLayer(str(grid), "grid", "ogr")
    if not grid_layer.isValid():
        print("⚠️ Grid layer is not valid!")
        print(f"Grid path: {grid}")
        return None

    print(f"✅ Grid layer is valid with {grid_layer.featureCount()} features")
    print("Fields in grid layer:", [field.name() for field in grid_layer.fields()])

    agg_fields = [field.name() for field in agg_layer.fields()]
    grid_fields = [field.name() for field in grid_layer.fields()]

    common_fields = list(set(agg_fields) & set(grid_fields))
    print(f"Common fields between layers: {common_fields}")

    possible_id_fields = ['grid_id', 'id', 'fid', 'ID', 'Grid_ID']
    join_field = None

    for field in possible_id_fields:
        if field in common_fields:
            join_field = field
            break

    if join_field:
        print(f"Using field '{join_field}' for joining")
        # Use attribute join instead of spatial join
        result = processing.run("native:joinattributestable", {
            'INPUT': grid_layer,  # Start with grid as base
            'FIELD': join_field,
            'INPUT_2': agg_layer,
            'FIELD_2': join_field,
            'FIELDS_TO_COPY': [],  # Copy all fields
            'METHOD': 1,  # Take first feature only
            'DISCARD_NONMATCHING': False,
            'PREFIX': '',
            'OUTPUT': str(out)
        })
    else:

        result = processing.run("native:joinattributesbylocation", {
            'INPUT':str(grid),
            'PREDICATE':[2],
            'JOIN':agg_layer,
            'JOIN_FIELDS':[],
            'METHOD':1,
            'DISCARD_NONMATCHING':False,
            'PREFIX':'',
            'OUTPUT':str(out)
        })

    if result is None:
        print("❌ Failed to join results. Exiting.")
        sys.exit(1)

    if out == "memory:":
        print("✅ Final join of grid floor areas completed - output stored in memory")
    else:
        print(f"✅ Final join of grid floor areas completed - output saved to: {out}")

    print("✅ Pipeline completed successfully!")

    return result['OUTPUT']





############################################ MAIN PIPELINE #############################################################





### 6 - Final result

def final_hausumringe_agg_join_pipeline():

    ### 1 - Verify building layer

    verified_hausumringe_global, is_correct_crs = verify_hausumringe(footprint_path=HAUSUMRINGE_SHP_PATH)

    ### 2 - Clip buildings to Coburg boundary

    hausumringe_clipped_global = clip_hausumringe(verified_hausumringe=verified_hausumringe_global,
                     boundary_path=BOUNDARY_PATH)

    ### 3 - Calculate floor area for each building object

    hausumringe_areas_global = calculate_area(clipped_buildings=hausumringe_clipped_global)

    ### 4 - Perform QGS overlap analysis, calculate the percentage of each building occupying grid cell

    overlap_result = overlap_intersection_weighting(GRID_PATH, hausumringe_areas_global)

    ### 5 - Aggregate calculated areas to grid, group previous result by unique grid cell

    aggregated_result = aggregate_to_grid(overlap_result)


    final_result = join_aggregate_and_grid_ids(
        aggregated_result,
        GRID_PATH
    )



    return final_result

def save_to_gdf():

    final_result = final_hausumringe_agg_join_pipeline()

    temp_path = f"{PROCESSED_DATA_DIR}\\temp_floor_area.gpkg"
    QgsVectorFileWriter.writeAsVectorFormat(
        final_result,
        temp_path,
        "utf-8",
        driverName="GPKG"
    )

    floor_area_gdf = gpd.read_file(temp_path)

    floor_area_gdf.set_crs("EPSG:25832", inplace=True)

    floor_area_gdf.to_file(f"{PROCESSED_DATA_DIR}\\floor_area.gpkg", driver="GPKG")

    print("✅ Floor area geodataframe saved!")


save_to_gdf()





######################### TODO: ADD FUNCTIONALITY TO AUTOMATICALLY ADD THE LAYERS TO QGIS ############################

def add_aggregated_hausumringe_to_qgis():

    pass