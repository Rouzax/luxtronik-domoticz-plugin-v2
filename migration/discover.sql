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
-- UNIT ID MAPPING TABLE
-- ============================================================================

DROP TABLE IF EXISTS _unit_map;

CREATE TEMPORARY TABLE _unit_map (
    old_unit INTEGER PRIMARY KEY,
    new_unit INTEGER,
    device_type TEXT,
    description TEXT
);

INSERT INTO _unit_map (old_unit, new_unit, device_type, description) VALUES
    -- Temperature devices
    (1,  60,  'temp', 'Heat supply temp'),
    (2,  61,  'temp', 'Heat return temp'),
    (3,  62,  'temp', 'Return temp target'),
    (4,  90,  'temp', 'Outside temp'),
    (5,  91,  'temp', 'Outside temp avg'),
    (6,  80,  'temp', 'DHW temp'),
    (8,  100, 'temp', 'Source inlet temp'),
    (9,  101, 'temp', 'Source outlet temp'),
    (10, 120, 'temp', 'Circuit 1 temp'),
    (11, 121, 'temp', 'Circuit 1 target'),
    (12, 130, 'temp', 'Circuit 2 temp'),
    (13, 131, 'temp', 'Circuit 2 target'),
    (21, 92,  'temp', 'Room temp'),
    (22, 93,  'temp', 'Room temp target'),
    (32, 160, 'temp', 'Hot gas temp'),
    (33, 161, 'temp', 'Suction temp'),
    -- Setpoint devices
    (7,  15,  'setpoint', 'DHW temp target'),
    (17, 14,  'setpoint', 'Temp adjust'),
    (40, 16,  'setpoint', 'Room temp setpoint'),
    -- kWh devices (need counter sync!)
    (23, 30,  'kwh', 'Power total'),
    (24, 31,  'kwh', 'Power heating'),
    (25, 32,  'kwh', 'Power DHW'),
    (26, 40,  'kwh', 'Heat out total'),
    (27, 41,  'kwh', 'Heat out heating'),
    (28, 42,  'kwh', 'Heat out DHW'),
    -- Percentage devices
    (30, 66,  'pct', 'Heating pump'),
    (31, 105, 'pct', 'Source pump'),
    -- Custom sensors (stored in Percentage table)
    (19, 106, 'pct', 'Source flow'),
    (20, 140, 'pct', 'Compressor freq'),
    (29, 50,  'pct', 'COP total'),
    (34, 165, 'pct', 'Superheat'),
    (35, 166, 'pct', 'Pressure high'),
    (36, 167, 'pct', 'Pressure low'),
    (37, 102, 'pct', 'Source ΔT'),
    (38, 63,  'pct', 'Heating ΔT'),
    (41, 51,  'pct', 'COP heating'),
    (42, 52,  'pct', 'COP DHW'),
    -- Switch/Text devices
    (16, 13,  'light', 'Cooling'),
    (18, 1,   'light', 'Working mode'),
    -- Selector switches
    (14, 10,  'light', 'Heating mode'),
    (15, 11,  'light', 'Hot water mode'),
    (39, 12,  'light', 'DHW Power Mode');

-- ============================================================================
-- kWh DEVICE COUNTER COMPARISON (CRITICAL FOR MIGRATION!)
-- ============================================================================
-- For kWh devices, Domoticz stores cumulative energy in sValue as:
--   "instant_power;cumulative_energy_wh"
-- 
-- After migration, the new device's counter MUST match the old device's
-- counter, otherwise daily/monthly calculations will show huge negative values.
-- ============================================================================

SELECT '' AS '';
SELECT '=== kWh DEVICE COUNTER COMPARISON (CRITICAL!) ===' AS Info;
SELECT 'These counters must match after migration for correct graphs' AS Note;
SELECT '' AS '';

SELECT 
    um.description AS Device,
    um.old_unit AS OldU,
    um.new_unit AS NewU,
    old_dev.ID AS OldIdx,
    new_dev.ID AS NewIdx,
    old_dev.sValue AS OldCounter,
    new_dev.sValue AS NewCounter,
    CASE 
        WHEN old_dev.sValue = new_dev.sValue THEN 'OK'
        WHEN new_dev.sValue IS NULL THEN 'MISSING'
        ELSE 'MISMATCH - will be fixed by migrate.sql'
    END AS Status
FROM _unit_map um
INNER JOIN _hw_ids hw ON 1=1
LEFT JOIN DeviceStatus old_dev ON old_dev.Unit = um.old_unit AND old_dev.HardwareID = hw.old_hw_id
LEFT JOIN DeviceStatus new_dev ON new_dev.Unit = um.new_unit AND new_dev.HardwareID = hw.new_hw_id
WHERE um.device_type = 'kwh'
ORDER BY um.old_unit;

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

-- ============================================================================
-- CALENDAR DATA COUNTS
-- ============================================================================

SELECT '' AS '';
SELECT '=== CALENDAR DATA TO MIGRATE ===' AS Info;

SELECT 
    d.ID AS Idx,
    d.Unit,
    SUBSTR(d.Name, 1, 25) AS Name,
    COALESCE(tc.cnt, 0) AS TempCal,
    COALESCE(mc.cnt, 0) AS MeterCal,
    COALESCE(pc.cnt, 0) AS PctCal
FROM DeviceStatus d
INNER JOIN _hw_ids hw ON d.HardwareID = hw.old_hw_id
LEFT JOIN (SELECT DeviceRowID, COUNT(*) AS cnt FROM Temperature_Calendar GROUP BY DeviceRowID) tc ON d.ID = tc.DeviceRowID
LEFT JOIN (SELECT DeviceRowID, COUNT(*) AS cnt FROM Meter_Calendar GROUP BY DeviceRowID) mc ON d.ID = mc.DeviceRowID
LEFT JOIN (SELECT DeviceRowID, COUNT(*) AS cnt FROM Percentage_Calendar GROUP BY DeviceRowID) pc ON d.ID = pc.DeviceRowID
WHERE (COALESCE(tc.cnt, 0) + COALESCE(mc.cnt, 0) + COALESCE(pc.cnt, 0)) > 0
ORDER BY d.Unit;

SELECT '' AS '';
SELECT '=== READY TO MIGRATE ===' AS Info;
SELECT 'Run: sqlite3 domoticz.db < plugins/luxtronik-domoticz-plugin-v2/migration/migrate.sql' AS Command;

DROP TABLE IF EXISTS _unit_map;
DROP TABLE IF EXISTS _hw_ids;