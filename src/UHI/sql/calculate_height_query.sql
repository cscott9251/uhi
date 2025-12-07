create table height_per_building_30m as
SELECT 
    f.objectid AS building_objectid,
    (CAST(roof.val_string AS numeric) - CAST(ground.val_string AS numeric)) AS building_height
FROM 
    citydb.feature f
-- Join to get HoheDach (roof height)
LEFT JOIN citydb.property roof ON f.id = roof.feature_id 
    AND roof.name = 'HoeheDach'
-- Join to get HoheGrund (ground height)  
LEFT JOIN citydb.property ground ON f.id = ground.feature_id 
    AND ground.name = 'HoeheGrund'
WHERE 
    f.objectclass_id = 901  -- Building objects
    AND roof.val_string IS NOT NULL 
    AND ground.val_string IS NOT NULL
    AND CAST(roof.val_string AS numeric) > CAST(ground.val_string AS numeric); -- Sanity check
	
	-- Add primary key constraint on building_objectid
ALTER TABLE height_per_building_30m
ADD CONSTRAINT height_30m_pk PRIMARY KEY (building_objectid);