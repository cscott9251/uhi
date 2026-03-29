  -- Create a new table with the aggregated floor area per building
  DROP TABLE IF EXISTS floor_area_per_building_30m;

  CREATE TABLE floor_area_per_building_30m AS
  SELECT
      b.objectid AS building_objectid,
      SUM(CAST(p.val_string AS numeric)) AS total_floor_area
  FROM citydb.feature f
  JOIN citydb.property p 
      ON f.id = p.feature_id
      AND p.name = 'Flaeche'
  JOIN citydb.feature b 
      ON b.objectid = regexp_replace(f.objectid, 
          '_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}.*$', 
          '')
      AND b.objectclass_id = 901
  WHERE f.objectclass_id = 710
  GROUP BY b.objectid;

  -- Add primary key constraint with correct name
  ALTER TABLE floor_area_per_building_30m
  ADD CONSTRAINT floor_area_30m_pk PRIMARY KEY (building_objectid);
