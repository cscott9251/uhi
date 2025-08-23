-- Create volume per building table
CREATE TABLE volume_per_building AS
SELECT 
    f.building_objectid,
    f.total_floor_area,
    h.building_height,
    (f.total_floor_area * h.building_height) AS total_building_volume
FROM 
    citydb.floor_area_per_building f
INNER JOIN 
    height_per_building h ON f.building_objectid = h.building_objectid
WHERE 
    f.total_floor_area IS NOT NULL 
    AND h.building_height IS NOT NULL
    AND f.total_floor_area > 0
    AND h.building_height > 0;

-- Add primary key constraint
ALTER TABLE volume_per_building
ADD CONSTRAINT volume_per_building_pk PRIMARY KEY (building_objectid);

