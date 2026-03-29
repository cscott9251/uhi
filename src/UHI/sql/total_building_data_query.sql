DROP TABLE IF EXISTS building_metrics_30m;

-- Create comprehensive building metrics table
CREATE TABLE building_metrics_30m AS
SELECT 
    v.building_objectid,
    r.total_roof_area,
    v.total_floor_area,
    v.building_height,
    v.total_building_volume
FROM 
    citydb.volume_per_building_30m v
LEFT JOIN 
    citydb.roof_area_per_building_30m r ON v.building_objectid = r.building_objectid
WHERE 
    v.building_objectid IS NOT NULL;

-- Add primary key constraint
ALTER TABLE building_metrics_30m
ADD CONSTRAINT building_metrics_pk PRIMARY KEY (building_objectid);

-- Optional: Add index for faster queries
CREATE INDEX idx_building_metrics_objectid ON building_metrics_30m(building_objectid);