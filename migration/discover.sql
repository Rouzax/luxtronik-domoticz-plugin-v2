-- ============================================================================
-- Luxtronik Plugin Migration - Discovery Script
-- ============================================================================
-- Run this to verify plugin detection and preview the migration mapping
-- 
-- Usage: sqlite3 domoticz.db < plugins/luxtronik-domoticz-plugin-v2/migration/discover.sql
-- ============================================================================

.headers on
.mode column
.width auto

-- ============================================================================
-- AUTO-DETECT HARDWARE IDs FROM PLUGIN KEY
-- ============================================================================

DROP TABLE IF EXISTS _hw_ids;

CREATE TEMPORARY TABLE _hw_ids AS
SELECT 
    (SELECT ID FROM Hardware WHERE Extra = 'luxtronik' LIMIT 1) AS old_hw_id,
    (SELECT Name FROM Hardware WHERE Extra = 'luxtronik' LIMIT 1) AS old_name,
    (SELECT ID FROM Hardware WHERE Extra = 'luxtronikex' LIMIT 1) AS new_hw_id,
    (SELECT Name FROM Hardware WHERE Extra = 'luxtronikex' LIMIT 1) AS new_name;

SELECT '=== AUTO-DETECTED LUXTRONIK HARDWARE ===' AS Info;

SELECT 
    'Old plugin (luxtronik)' AS Plugin,
    old_name AS Name,
    old_hw_id AS HW_ID
FROM _hw_ids
UNION ALL
SELECT 
    'New plugin (luxtronikex)' AS Plugin,
    new_name AS Name,
    new_hw_id AS HW_ID
FROM _hw_ids;

SELECT '' AS '';

-- Check for errors
SELECT CASE 
    WHEN old_hw_id IS NULL THEN 'WARNING: Old plugin (luxtronik) not found!'
    WHEN new_hw_id IS NULL THEN 'WARNING: New plugin (luxtronikex) not found!'
    ELSE 'OK: Both plugins detected successfully'
END AS Status FROM _hw_ids;

SELECT '' AS '';

SELECT '=== OLD PLUGIN DEVICES ===' AS Info;

SELECT 
    d.ID AS Idx,
    d.Unit,
    d.Name,
    CASE 
        WHEN d.Type = 80 THEN 'Temperature'
        WHEN d.Type = 242 THEN 'Setpoint'
        WHEN d.Type = 243 AND d.SubType = 6 THEN 'Percentage'
        WHEN d.Type = 243 AND d.SubType = 19 THEN 'Text'
        WHEN d.Type = 243 AND d.SubType = 29 THEN 'kWh'
        WHEN d.Type = 243 AND d.SubType = 31 THEN 'Custom'
        WHEN d.Type = 244 AND d.SubType = 62 THEN 'Selector'
        WHEN d.Type = 244 THEN 'Switch'
        ELSE 'T' || d.Type || '/S' || d.SubType
    END AS DevType,
    SUBSTR(d.sValue, 1, 20) AS Value
FROM DeviceStatus d
INNER JOIN _hw_ids hw ON d.HardwareID = hw.old_hw_id
ORDER BY d.Unit;

SELECT '' AS '';

SELECT '=== NEW PLUGIN DEVICES ===' AS Info;

SELECT 
    d.ID AS Idx,
    d.Unit,
    d.Name,
    CASE 
        WHEN d.Type = 80 THEN 'Temperature'
        WHEN d.Type = 242 THEN 'Setpoint'
        WHEN d.Type = 243 AND d.SubType = 6 THEN 'Percentage'
        WHEN d.Type = 243 AND d.SubType = 19 THEN 'Text'
        WHEN d.Type = 243 AND d.SubType = 29 THEN 'kWh'
        WHEN d.Type = 243 AND d.SubType = 31 THEN 'Custom'
        WHEN d.Type = 244 AND d.SubType = 62 THEN 'Selector'
        WHEN d.Type = 244 THEN 'Switch'
        ELSE 'T' || d.Type || '/S' || d.SubType
    END AS DevType,
    SUBSTR(d.sValue, 1, 20) AS Value
FROM DeviceStatus d
INNER JOIN _hw_ids hw ON d.HardwareID = hw.new_hw_id
ORDER BY d.Unit;

SELECT '' AS '';

-- ============================================================================
-- HISTORICAL DATA COUNTS (what will be migrated)
-- ============================================================================

SELECT '' AS '';
SELECT '=== HISTORICAL DATA TO MIGRATE ===' AS Info;

SELECT 
    d.ID AS Idx,
    d.Unit,
    d.Name,
    COALESCE(t.cnt, 0) AS Temp,
    COALESCE(m.cnt, 0) AS Meter,
    COALESCE(p.cnt, 0) AS Pct,
    COALESCE(l.cnt, 0) AS Light
FROM DeviceStatus d
INNER JOIN _hw_ids hw ON d.HardwareID = hw.old_hw_id
LEFT JOIN (SELECT DeviceRowID, COUNT(*) AS cnt FROM Temperature GROUP BY DeviceRowID) t ON d.ID = t.DeviceRowID
LEFT JOIN (SELECT DeviceRowID, COUNT(*) AS cnt FROM Meter GROUP BY DeviceRowID) m ON d.ID = m.DeviceRowID
LEFT JOIN (SELECT DeviceRowID, COUNT(*) AS cnt FROM Percentage GROUP BY DeviceRowID) p ON d.ID = p.DeviceRowID
LEFT JOIN (SELECT DeviceRowID, COUNT(*) AS cnt FROM LightingLog GROUP BY DeviceRowID) l ON d.ID = l.DeviceRowID
WHERE (COALESCE(t.cnt, 0) + COALESCE(m.cnt, 0) + COALESCE(p.cnt, 0) + COALESCE(l.cnt, 0)) > 0
ORDER BY d.Unit;

SELECT '' AS '';
SELECT '=== READY TO MIGRATE ===' AS Info;
SELECT 'Run: sqlite3 domoticz.db < plugins/luxtronik-domoticz-plugin-v2/migration/migrate.sql' AS Command;

DROP TABLE IF EXISTS _hw_ids;