import os
import sys
import importlib.util

### NEEDS TO BE RUN WITHIN PYQGIS-INITIALISED ENVIRONEMNT VIA A SCRIPT IN ORDER TO SET CORRECT
### ENVIRONMENTAL VARIABLES, PATHS, ETC, POINTING TO OSGEO4W FOLDER, AND OTHER QGIS/PYQGIS SPECIFIC STUFF. 
### WILL NOT WORK WITHOUT 

QGIS_PREFIX_PATH = os.environ['QGIS_PREFIX_PATH']
QGIS_PYTHON_PATH = os.environ['PYTHONPATH']
O4W_QT_PLUGINS = os.environ['O4W_QT_PLUGINS']
QGIS_PLUGINS_PATH = os.environ['QGIS_PLUGINS_PATH']
print(QGIS_PLUGINS_PATH)
print(O4W_QT_PLUGINS)
print(QGIS_PYTHON_PATH)
print(QGIS_PREFIX_PATH)


sys.path.append(QGIS_PREFIX_PATH)
sys.path.append(QGIS_PYTHON_PATH)
sys.path.append(O4W_QT_PLUGINS)
sys.path.append(QGIS_PLUGINS_PATH)


#print(sys.path)
cleaned = [os.path.normpath(p) for p in sys.path]
print("🔧 Cleaning up PATH environmental variable for consistency 🔧")
sys.path = cleaned
print(f"ℹ️  System PATH: {sys.path}")
#print(QGIS_PLUGINS_PATH)

from qgis.core import *
#from PyQt5.QtGui import *
from PyQt5.QtCore import QVariant
from qgis.analysis import QgsNativeAlgorithms



# Set up the QGIS prefix path and set variable
QgsApplication.setPrefixPath("C:/OSGeo4W/apps/qgis-ltr", True)




# Create a reference to the QgsApplication / start QGIS with no GUI
qgs = QgsApplication([], False)
qgs.initQgis()

# Load project
project = QgsProject.instance()
project_path = "C:/Users/chris/OneDrive/GIS_Work/Personal_Projects/UrbanHeatIsland_LST_Prediction_Analysis/UHI.qgz"
#project.read(project_path)


# Import processing plugin
import qgis.analysis
import qgis.processing

# Fix processing module not found. This is necessary, otherwise PyCharm gives a module not found error?
print("Looking for processing in:", [p for p in sys.path if os.path.exists(os.path.join(p, "processing"))])
print("\n")

spec = importlib.util.spec_from_file_location("processing", os.path.join(os.path.join(QGIS_PLUGINS_PATH, "processing"), "__init__.py"))
processing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(processing)

# Then initialize processing
from processing.core.Processing import Processing
Processing.initialize()

# Register native (built-in) algorithms like "native:mergevectorlayers" # This is necessary otherwise
#                                                                       # native:mergevectorlayers not found error

QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

# Access layers
#layers = project.mapLayers().values()
# for layer in layers:
#     print(f"Layer name: {layer.name()}")

