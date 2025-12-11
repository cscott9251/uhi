# Urban Heat Island (UHI) model for Coburg, Bayern

An integrated geospatial analysis tool combining satellite-derived spatial indices with 3D urban morphology as input variables for the analysis of Urban Heat Islands (UHI).
A remote sensing-based exploration of UHI, using a number of input variables to determine Land Surface Temperature. UHIs and rising temperatures in urban spaces have myriad impacts on human health and quality of life, and with an ever-increasing population density in these spaces, it is vitally important understand the influencing factors of UHIs so that they may be mitigated in the future.

## Introduction

Due to the rapid urbanization, natural land surfaces are being replaced by anthropogenic materials, which negatively impacts ecosystems and resuls in Urban Heat Island (UHI) effect. Land surface temperature (LST) is the primary target variable in relation to the UHI effect. 

## Ultimate objective

To build a Machine Learning model that is trained on temporally-similar summer/winter pairs of Sentinel-2 and Landsat 8/9 raster data (the below spectral indices) plus the urban morphological variables for multiple years, and predicts Land Surface Temperature for future years. 

The Machine Learning model will comprise input variables that are both spatial, such and spectral and morphological quantities, and socioeconomic, such as population density, number of households, and mean income.

Understanding the connections between LST and the input variables helps provide insight into urban planning policy and decisions, in terms of which physical urban characteristics are the most important to control or change in order to mitigate the UHI effect, and into the social impact of UHI and current urban planning policy, in terms of which sections of the population may be most at risk from UHI and climate change. 

The data ETL, pre-processing, and deployment pipeliens, as well as the ML model, will be integrated into a single Python tool, an installable package, which will be able to be used with other locations around the world.

## Current state

The tool can undertake complex ETL / automation tasks, albeit in a semi-automated way.
Some further work is still to be done to streamline / further rationalise the pipelines.
ML model is yet to be built.

## Input variables and data sources - spectral

### From Sentinel-2 (10m resolution)

- NDVI 
- MNDWI 
- NDMI
- NDBI 
- NDMI 

### From Landsat 8 (30m resolutiob)

- EVI

## Input variables and data sources - urban morphological

### From LoD2 CityGML ALKIS (Geodaten Bayern)

- Building envelope 
- Building roof area
- Builsind height 
- Building volume (calculated from building envelope and building height)

These were calculated using PostGIS and SQL, after loading the CityGML files into a PostgreSQL database with the 3DCityDB schema installed. 
More info on 3DCityDB here: https://github.com/3dcitydb. 

## Target variable - spectral

### From Landsat 8/9

- LST (30m resolution)

## 

## Method

- Establishment of 30m resolution grid (matching Landsat 8/9 resolution).
- Acquisition of raw morphological data.
- Loading it into PostgreSQL database with 3DCityDB, calculation of geometric quantities using SQL, using PostGIS to determine weighted intersection and to allocate / aggregate quantities to grid cells based on their proportional allocation, saving as new table in database.
- Converting Postgres variable table 
- Use of Google Earth Engine to obtain suitable summer/winter pairs of Sentinel-2 and Landsat 8/9 images for 2021-2024.
- Select temporally similar pairs of Sentinel-2 and Landsat 8/9 images with acceptable proportions of cloud cover for each year (GEE).
- Perform cloud masking, manually assess results (GEE).
- Perform Raster sampling fishnet at grid centroids to convert spectral indices to decimal (vector) values.
- Push 

## Technical Challenges & Solutions

### Different Spatial Resolutions
- **Problem**: Landsat (30m raster), Sentinel-2 (10m raster), building data (object-specific vector), how to bring these variables into a single Geodataframe with uniform resolution.
- **Solution**: Grid-based aggregation approach - created 30×30m fishnet aligned with Landsat resolution and aggregated all input variables to it. Upsampled Sentinel-2 data to from 10m to 30m. The rasters were aggregated to the grid by raster sampling at centroids, and the morphological quantities were aggregated to the grid using overlap / intersection proportion analysis using PostGIS ST_ methods and SQL (essentially "cutting" the objects with the grid cell boundaries).

### Need to change grid resolution from 100m to 30m
- **Problem**: A grid resolution of 100m was originally used in line with the original group project. However, the resolution of Landsat 8/9 images obtained from GEE is 30m. Many of the variables were already in 100m resolution, because of the need for all data to be aggregated to the grid. 
- **Solution**: Resampling the 100m grid to 30m using Shapely. Re-running the morphological and spectral pipelines to aggregate using 30m cells instead of 100m.
  
### Cloud Cover
- **Problem**: Limited cloud-free Sentinel-2 summer imagery
- **Solution**: Experiment with different cloud masking techniques.

### CityGML Processing
- **Problem**: Complex 3D building models with performance issues
- **Solution**: 3DCityDB for efficient spatial queries, aggregation at grid level

### Data Integration
- **Problem**: Multiple coordinate systems and formats
- **Solution**: Standardized to EPSG:25832 (ETRS89/UTM zone 32N), PostGIS for transformations

### GEE payload limits when sampling raster data using Python
- **Problem**: Error: Request payload size exceeds the limit: 10485760 bytes. When accessing rasters on GEE from Python IDE. GEE limits requests.
- **Solution**: Write a for loop to process features in batches, from the raster during the sampling process.

### Finding winter / summer pairs of images that aren't too far apart in time, and have an acceptable cloud cover



## Lessons learnt

### The importance of consistency of data source for variables
- For example, trying to join LoD2 and building footprint (Hausumringe) data (separate data sources) was onerous because of tiny spatial differences in the datasets.
- Calculating the floor area from the Hausumringe, and the roof area and height from LoD2, when all three variables were needed to calculate the fourth variable, building volunme (so calculating the variables from seperate data sources) led to a very complex, convoluted and time consuming solution involving using geospatial Python packages, performing many joins, dealing with unrecognised geometry formats, geometry incompatibility issues with certain geospatial python libraries, and a generally confusing and error-prone pipeline.
- Originally it was thought that this would be simpler, but using a single data source (LoD2) for the building floor area, roof area, height and volume was much simpler and better.

### PostgreSQL + PostGIS + 3DCityDB efficiency with performing spatial operation on 3D building data
- Performing the building morphological variable calculations with GeoPandas AND performing the building data grid aggregation using Python still ran into efficiency issues, and the code was not very readable.
- Using PostGIS to perform the aggregation using ST_Area and ST_Intersection. This is MUCH faster due to the calculations being performed on a database structure instead of disparate object-oriented data.

### Sophistication vs simplicity when deriving morphological variables and in general
- Python and its geospatial libraries are very powerful for spatial operations and geospatial analysis, but they're not always the right tools for the job.
- When deriving the building floor area, roof area, height and calculating the building volume, from their original LoD2 CityGML format, using Python and GeoPandas proved unexpectedly convoluted. It's always good to remember that these tools, whilst powerful, cannot be used for everything!
- Deriving and calculating these variables using only SQL and PostGIS spatial functions proved led to a much simpler, and much faster, solution. 
	

GeoPandas spatial join (sjoin) is far more efficient than PyQGIS overlap analysis algorithm...


...BUT Geopandas still fails of there are any geometries it doesn't recognise. Now I see the power of PostGIS! Its function ST_Intersection is built to compute the intersections of geometry.


The EVI formula is **fundamentally unsuitable for winter conditions** with snow/ice. When BLUE reflectance is very high (snow), the denominator `NIR + 6×RED - 7.5×BLUE + 1` becomes negative.

## Future improvements

- Increase the degree of automation.
- Link up / streamline / rationalise different pipelines, for example pushing the local Postgres database containing the input variables straight to Google Cloud in a customised Docker image.
- Change raster sampling pipeline so that instead of saving to a file, it pushes straight to the Google Cloud Postgres database which is already linked to CARTO.
- 

