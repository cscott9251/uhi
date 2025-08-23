-- Create a new table with the aggregated floor area per building
CREATE TABLE floor_area_per_building_30m AS
SELECT
  f.objectid AS building_objectid,
  SUM(CAST(p.val_string AS numeric)) AS total_floor_area
FROM
  feature f
JOIN
  property p ON f.id = p.feature_id
WHERE
  f.objectclass_id = 710  -- Floor surfaces instead
  AND p.name = 'Flaeche'
GROUP BY
   building_objectid

-- Add primary key constraint with correct name
ALTER TABLE floor_area_per_building_30m
ADD CONSTRAINT floor_area_30m_pk PRIMARY KEY (building_objectid);