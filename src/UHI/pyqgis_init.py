from qgis.core import (
    QgsApplication,
    QgsVectorLayer,
    QgsProject,
    QgsRectangle,
    QgsCoordinateReferenceSystem,
    QgsFeature,
    QgsGeometry,
    QgsVectorFileWriter,
    QgsFields,
    QgsField,
    QgsFeatureSink,
    QgsVectorLayerSimpleLabeling
)

from PyQt5.QtCore import QVariant
import os

# Set up the QGIS prefix path
QgsApplication.setPrefixPath("C:/OSGeo4W/apps/qgis-ltr", True)



# Create a reference to the QgsApplication / start QGIS with no GUI
qgs = QgsApplication([], False)
qgs.initQgis()

# Load project
project = QgsProject.instance()
project_path = "C:/Users/chris/OneDrive/GIS_Work/Personal_Projects/UrbanHeatIsland_LST_Prediction_Analysis/UHI.qgz"
project.read(project_path)



# Access layers
layers = project.mapLayers().values()
# for layer in layers:
#     print(f"Layer name: {layer.name()}")

