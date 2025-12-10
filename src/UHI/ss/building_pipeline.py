from UHI.pyqgis.pyqgis_init import QgsVectorLayer, QgsVectorFileWriter
from UHI.config import *
import processing

import geopandas as gpd


class BuildingAnalysisPipeline:
    """Simplified pipeline for building footprint and LoD2 data processing"""

    def __init__(self, hausumringe_path, boundary_path, grid_path, target_crs="EPSG:25832",
                 processed_data_dir="./processed"):
        self.hausumringe_path = str(HAUSUMRINGE_SHP_PATH)
        self.lod2_path = str(LOD2_MERGED_PATH)
        self.boundary_path = str(BOUNDARY_PATH)
        self.grid_path = str(GRID_PATH)
        self.target_crs = CRS
        self.processed_data_dir = PROCESSED_DATA_DIR

    def _load_and_validate_layer(self, path, layer_name):
        """Load and validate a vector layer"""
        layer = QgsVectorLayer(str(path), layer_name, "ogr")
        if not layer.isValid():
            raise ValueError(f"❌ {layer_name} layer is not valid at path: {path}")

        feature_count = layer.featureCount()
        print(f"✅ {layer_name} layer loaded successfully ({feature_count} features)")
        return layer

    def _fix_geometries(self, layer, layer_name):
        """Fix invalid geometries in a layer"""
        print(f"🔧 Fixing geometries for {layer_name}...")

        fixed_result = processing.run("native:fixgeometries", {
            'INPUT': layer,
            'OUTPUT': "memory:"
        })

        if fixed_result is None:
            raise RuntimeError(f"❌ Failed to fix geometries for {layer_name}")

        print(f"✅ Geometries fixed for {layer_name}")
        return fixed_result['OUTPUT']

    def _reproject_if_needed(self, layer, output_path=None):
        """Reproject layer to target CRS if needed"""
        current_crs = layer.crs().authid()

        if current_crs != self.target_crs:
            print(f"⚠️ Reprojecting from {current_crs} to {self.target_crs}")

            if output_path is None:
                output_path = "memory:"

            result = processing.run("native:reprojectlayer", {
                'INPUT': layer,
                'TARGET_CRS': self.target_crs,
                'OUTPUT': output_path
            })

            if result is None:
                raise RuntimeError("❌ Failed to reproject layer")

            return result['OUTPUT']
        else:
            print(f"✅ CRS already matches {self.target_crs}")
            return layer


    def _join_lod2_with_footprints(self, footprints, lod2_data):
        """Join LoD2 data with building footprints, filtering for matching geometries only"""
        print("🔧 Performing spatial join between footprints and LoD2 data...")
        print("🔧 Using 'equals' predicate for faster matching...")

        # Use 'equals' predicate - much faster than intersection for matching footprints
        initial_join = processing.run("native:joinattributesbylocation", {
            'INPUT': footprints,
            'PREDICATE': [3],  # equals - much faster than intersects
            'JOIN': lod2_data,
            'JOIN_FIELDS': ['measuredHeight'],  # Only take height field from LoD2
            'METHOD': 0,  # Create separate feature for each match
            'DISCARD_NONMATCHING': True,  # Only keep buildings that have LoD2 data
            'PREFIX': 'lod2_',
            'OUTPUT': "memory:"
        })

        if initial_join is None:
            print("❌ 'Equals' join failed, trying 'intersects' with tolerance...")
            # Fallback to intersects if equals doesn't work
            return self._fallback_intersect_join(footprints, lod2_data)

        joined_layer = initial_join['OUTPUT']
        joined_count = joined_layer.featureCount() if hasattr(joined_layer, 'featureCount') else "unknown"
        print(f"✅ 'Equals' spatial join completed: {joined_count} matched features")

        return joined_layer




    def _fallback_intersect_join(self, footprints, lod2_data):
        """Fallback to intersects if equals doesn't work"""
        print("🔧 Using 'intersects' as fallback...")

        intersect_join = processing.run("native:joinattributesbylocation", {
            'INPUT': footprints,
            'PREDICATE': [0],  # intersects
            'JOIN': lod2_data,
            'JOIN_FIELDS': ['measuredHeight'],
            'METHOD': 0,
            'DISCARD_NONMATCHING': True,
            'PREFIX': 'lod2_',
            'OUTPUT': "memory:"
        })

        if intersect_join is None:
            raise RuntimeError("❌ Both 'equals' and 'intersects' joins failed")

        print("✅ 'Intersects' fallback join completed")
        return intersect_join['OUTPUT']

    def _filter_geometric_matches(self, joined_layer, lod2_layer):
        """Filter joined features to keep only those with similar geometry (area/shape)"""

        # Calculate area difference between footprint and LoD2 geometry
        # This helps identify buildings where footprint and LoD2 match well
        area_check = processing.run("native:fieldcalculator", {
            'INPUT': joined_layer,
            'FIELD_NAME': 'area_footprint',
            'FIELD_TYPE': 0,  # Double
            'FIELD_LENGTH': 20,
            'FIELD_PRECISION': 2,
            'FORMULA': 'area($geometry)',
            'OUTPUT': "memory:"
        })

        if area_check is None:
            raise RuntimeError("❌ Failed to calculate footprint areas")

        # For now, we'll keep all spatially intersecting features
        # You can add more sophisticated filtering here based on:
        # - Area similarity ratio
        # - Shape similarity
        # - Centroid distance
        # Example additional filter:
        '''
        filtered = processing.run("native:extractbyexpression", {
            'INPUT': area_check['OUTPUT'],
            'EXPRESSION': 'abs("area_footprint" - "lod2_area") / "area_footprint" < 0.2',  # 20% area difference tolerance
            'OUTPUT': "memory:"
        })
        '''

        print(f"✅ Geometric filtering completed")

        return area_check['OUTPUT']


    def prepare_buildings(self):
        """Step 1: Load, validate, reproject and clip buildings to boundary"""
        print("🔧 Step 1: Preparing building data...")

        # Load and validate building footprints
        footprints = self._load_and_validate_layer(self.hausumringe_path, "building_footprints")
        #footprints = self._reproject_if_needed(footprints)
        #footprints = self._fix_geometries(footprints, "building_footprints")

        # Load boundary and clip
        boundary = self._load_and_validate_layer(self.boundary_path, "boundary")

        print("🔧 Clipping building footprints to boundary...")
        clipped_footprints = processing.run("native:clip", {
            'INPUT': footprints,
            'OVERLAY': boundary,
            'OUTPUT': "memory:"
        })

        if clipped_footprints is None:
            raise RuntimeError("❌ Failed to clip footprints to boundary")

        clipped_count = clipped_footprints['OUTPUT'].featureCount() if hasattr(clipped_footprints['OUTPUT'], 'featureCount') else "unknown"
        print(f"✅ Footprints clipped to boundary: {clipped_count} features (reduced from original)")


        # Load and validate LoD2 data
        lod2_data = self._load_and_validate_layer(self.lod2_path, "LoD2_data")
        # lod2_data = self._reproject_if_needed(lod2_data)
        lod2_data = self._fix_geometries(lod2_data, "LoD2_data")

        # Join LoD2 data to footprints using spatial intersection
        print("🔧 Joining LoD2 data with building footprints...")
        joined_buildings = self._join_lod2_with_footprints(footprints, lod2_data)

        # Reproject if needed
        # buildings = self._reproject_if_needed(buildings)

        print("✅ Buildings prepared (clipped footprints + LoD2 data)")
        return joined_buildings



    def calculate_building_metrics(self, buildings_layer):
        """Step 2: Calculate floor area and building volume for each building"""
        print("🔧 Step 2: Calculating building metrics...")

        # Calculate floor area
        print("🔧 Calculating floor areas...")
        area_result = processing.run("native:fieldcalculator", {
            'INPUT': buildings_layer,
            'FIELD_NAME': 'floor_area',
            'FIELD_TYPE': 0,  # Double
            'FIELD_LENGTH': 20,
            'FIELD_PRECISION': 2,
            'FORMULA': 'area($geometry)',
            'OUTPUT': "memory:"
        })

        if area_result is None:
            raise RuntimeError("❌ Failed to calculate floor areas")

        buildings_with_area = area_result['OUTPUT']

        # Calculate building volume (floor_area × measuredHeight)
        print("🔧 Calculating building volumes...")
        volume_result = processing.run("native:fieldcalculator", {
            'INPUT': buildings_with_area,
            'FIELD_NAME': 'building_volume',
            'FIELD_TYPE': 0,  # Double
            'FIELD_LENGTH': 20,
            'FIELD_PRECISION': 2,
            'FORMULA': '"floor_area" * "measuredHeight"',
            'OUTPUT': "memory:"
        })

        if volume_result is None:
            raise RuntimeError("❌ Failed to calculate building volumes")

        print("✅ Building metrics calculated (floor_area, building_volume)")
        return volume_result['OUTPUT']


    def calculate_grid_overlaps(self, buildings_with_metrics):
        """Step 3: Calculate overlaps between buildings and grid"""
        print("🔧 Step 3: Calculating grid overlaps...")

        grid_layer = self._load_and_validate_layer(self.grid_path, "grid")

        # Calculate vector overlaps
        overlap_result = processing.run("native:calculatevectoroverlaps", {
            'INPUT': grid_layer,
            'LAYERS': [buildings_with_metrics],
            'OUTPUT': "memory:",
            'GRID_SIZE': None
        })

        if overlap_result is None:
            raise RuntimeError("❌ Failed to calculate overlaps")

        print("✅ Grid overlaps calculated")
        return overlap_result['OUTPUT']


    def aggregate_to_grid(self, overlap_layer):
        """Step 4: Aggregate building metrics to grid cells"""
        print("🔧 Step 4: Aggregating metrics to grid...")

        # Aggregate both floor area and building volume
        aggregated = processing.run("native:aggregate", {
            'INPUT': overlap_layer,
            'GROUP_BY': '"grid_id"',
            'AGGREGATES': [
                {
                    'aggregate': 'sum',
                    'delimiter': ',',
                    'input': '"output_area"',  # This is the overlapping floor area
                    'length': 0,
                    'name': 'total_floor_area',
                    'precision': 2,
                    'sub_type': 0,
                    'type': 6,
                    'type_name': 'double precision'
                },
                {
                    'aggregate': 'sum',
                    'delimiter': ',',
                    'input': '"building_volume"',  # Sum of building volumes
                    'length': 0,
                    'name': 'total_building_volume',
                    'precision': 2,
                    'sub_type': 0,
                    'type': 6,
                    'type_name': 'double precision'
                }
            ],
            'OUTPUT': "memory:"
        })

        if aggregated is None:
            raise RuntimeError("❌ Failed to aggregate to grid")

        print("✅ Metrics aggregated to grid")
        return aggregated['OUTPUT']


    def join_with_grid(self, aggregated_layer):
        """Step 5: Join aggregated results back to grid geometry"""
        print("🔧 Step 5: Joining with grid geometry...")

        grid_layer = self._load_and_validate_layer(self.grid_path, "grid")

        # Join aggregated data back to grid
        result = processing.run("native:joinattributestable", {
            'INPUT': grid_layer,
            'FIELD': 'grid_id',
            'INPUT_2': aggregated_layer,
            'FIELD_2': 'grid_id',
            'FIELDS_TO_COPY': [],  # Copy all fields
            'METHOD': 1,  # Take first feature only
            'DISCARD_NONMATCHING': False,
            'PREFIX': '',
            'OUTPUT': "memory:"
        })

        if result is None:
            raise RuntimeError("❌ Failed to join with grid")

        print("✅ Successfully joined with grid geometry")
        return result['OUTPUT']


    def save_individual_buildings(self, buildings_with_metrics):
        """Save individual building data with floor_area, building_volume, and object_id"""
        print("🔧 Saving individual building data...")

        temp_path = f"{self.processed_data_dir}/individual_buildings.gpkg"

        # Save to temporary file first
        QgsVectorFileWriter.writeAsVectorFormat(
            buildings_with_metrics,
            temp_path,
            "utf-8",
            driverName="GPKG"
        )

        # Load as GeoDataFrame and ensure proper CRS
        buildings_gdf = gpd.read_file(temp_path)
        buildings_gdf.set_crs(self.target_crs, inplace=True)

        # Save final version
        final_path = f"{self.processed_data_dir}/buildings_with_metrics.gpkg"
        buildings_gdf.to_file(final_path, driver="GPKG")

        print(f"✅ Individual buildings saved to: {final_path}")
        print(f"   Columns: {list(buildings_gdf.columns)}")

        return buildings_gdf


    def save_grid_aggregates(self, grid_with_aggregates):
        """Save grid-level aggregated data"""
        print("🔧 Saving grid aggregated data...")

        temp_path = f"{self.processed_data_dir}/temp_grid_aggregates.gpkg"

        # Save to temporary file first
        QgsVectorFileWriter.writeAsVectorFormat(
            grid_with_aggregates,
            temp_path,
            "utf-8",
            driverName="GPKG"
        )

        # Load as GeoDataFrame and ensure proper CRS
        grid_gdf = gpd.read_file(temp_path)
        grid_gdf.set_crs(self.target_crs, inplace=True)

        # Save final version
        final_path = f"{self.processed_data_dir}/grid_building_aggregates.gpkg"
        grid_gdf.to_file(final_path, driver="GPKG")

        print(f"✅ Grid aggregates saved to: {final_path}")
        print(f"   Columns: {list(grid_gdf.columns)}")

        return grid_gdf


    def run_complete_pipeline(self):
        """Run the complete pipeline from start to finish"""
        print("🚀 Starting Building Analysis Pipeline...")

        try:
            # Step 1: Prepare buildings
            prepared_buildings = self.prepare_buildings()

            # Step 2: Calculate metrics
            buildings_with_metrics = self.calculate_building_metrics(prepared_buildings)

            # Step 3: Calculate overlaps
            overlaps = self.calculate_grid_overlaps(buildings_with_metrics)

            # Step 4: Aggregate to grid
            aggregated = self.aggregate_to_grid(overlaps)

            # Step 5: Join with grid
            grid_result = self.join_with_grid(aggregated)

            # Save both individual and aggregated results
            buildings_gdf = self.save_individual_buildings(buildings_with_metrics)
            grid_gdf = self.save_grid_aggregates(grid_result)

            print("🎉 Pipeline completed successfully!")
            print(f"   Individual buildings: {len(buildings_gdf)} features")
            print(f"   Grid cells: {len(grid_gdf)} features")

            return buildings_gdf, grid_gdf

        except Exception as e:
            print(f"❌ Pipeline failed: {str(e)}")
            raise


    # Usage example:
def run_pipeline_example():
    """Example of how to run the pipeline"""

    # Initialize pipeline with your paths
    pipeline = BuildingAnalysisPipeline(
        hausumringe_path=HAUSUMRINGE_SHP_PATH,
        boundary_path=BOUNDARY_PATH,
        grid_path=GRID_PATH,
        target_crs=CRS,
        processed_data_dir=PROCESSED_DATA_DIR
    )

    # Run complete pipeline
    buildings_gdf, grid_gdf = pipeline.run_complete_pipeline()

    return buildings_gdf, grid_gdf


# Only run if this file is executed directly (not imported)
if __name__ == "__main__":
    buildings_data, grid_data = run_pipeline_example()
