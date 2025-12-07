-- Create a new table with the aggregated roof area per building
CREATE TABLE roof_area_per_building_30m AS
SELECT
  f.objectid AS building_objectid,
  SUM(CAST(p.val_string AS numeric)) AS total_roof_area
FROM
  feature f
JOIN
  property p ON f.id = p.feature_id
WHERE
  f.objectclass_id = 712
  AND p.name = 'Flaeche'
GROUP BY
   building_objectid

-- Add primary key constraint on building_objectid
--ALTER TABLE roof_area_per_building_30m
--ADD CONSTRAINT roof_area_30m_pk PRIMARY KEY (building_objectid);