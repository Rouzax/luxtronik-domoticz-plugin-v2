-- ============================================================================
-- Luxtronik Plugin Migration - Discovery Script
-- ============================================================================
-- This script previews what will be migrated from the legacy plugin (v1.x)
-- to the new DomoticzEx plugin (v2.x). It's read-only and makes no changes.
-- 
-- Usage: sqlite3 domoticz.db < migration/discover.sql
--
-- What migrate.sql will do:
--   ✓ Copy all historical data (temperatures, meters, percentages)
--   ✓ Sync energy counters to preserve "Today/Week/Month" calculations
--   ✓ Transfer calendar data for long-term graphs
--   ✓ Copy KWHStats for usage pattern analysis
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
-- kWh DEVICE COUNTER COMPARISON
-- ============================================================================
-- For kWh devices, Domoticz stores cumulative energy in sValue as:
--   "instant_power;cumulative_energy_wh"
-- 
-- The migrate.sql script automatically handles:
--   ✓ Syncing counters from old to new devices
--   ✓ Copying historical Meter and Meter_Calendar data
--   ✓ Transferring KWHStats for usage patterns
--   ✓ Aligning counters with calendar data (prevents negative "Today" values)
-- ============================================================================

SELECT '' AS '';
SELECT '=== kWh DEVICE COUNTER STATUS ===' AS Info;
SELECT 'migrate.sql will sync these counters automatically' AS Note;
SELECT '' AS '';

SELECT 
    um.description AS Device,
    um.old_unit AS OldU,
    um.new_unit AS NewU,
    old_dev.ID AS OldIdx,
    new_dev.ID AS NewIdx,
    SUBSTR(old_dev.sValue, INSTR(old_dev.sValue, ';') + 1) AS OldEnergy_Wh,
    CASE 
        WHEN new_dev.sValue IS NULL THEN '(device missing)'
        ELSE SUBSTR(new_dev.sValue, INSTR(new_dev.sValue, ';') + 1)
    END AS NewEnergy_Wh,
    CASE 
        WHEN old_dev.sValue = new_dev.sValue THEN 'Already synced'
        WHEN new_dev.sValue IS NULL THEN 'New device needed'
        ELSE 'Will be synced'
    END AS Action
FROM _unit_map um
INNER JOIN _hw_ids hw ON 1=1
LEFT JOIN DeviceStatus old_dev ON old_dev.Unit = um.old_unit AND old_dev.HardwareID = hw.old_hw_id
LEFT JOIN DeviceStatus new_dev ON new_dev.Unit = um.new_unit AND new_dev.HardwareID = hw.new_hw_id
WHERE um.device_type = 'kwh'
ORDER BY um.old_unit;

-- Check for KWHStats that will be copied
SELECT '' AS '';
SELECT '=== KWHStats (Usage Patterns) ===' AS Info;
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN 'Found ' || COUNT(*) || ' entries - will be copied to preserve usage patterns'
        ELSE 'No KWHStats entries (this is normal for newer installations)'
    END AS Status
FROM KWHStats k
INNER JOIN _unit_map um ON 1=1
INNER JOIN _hw_ids hw ON 1=1
INNER JOIN DeviceStatus d ON d.ID = k.DeviceRowID 
    AND d.Unit = um.old_unit 
    AND d.HardwareID = hw.old_hw_id
WHERE um.device_type = 'kwh';

-- ============================================================================
-- HISTORICAL DATA SUMMARY
-- ============================================================================

SELECT '' AS '';
SELECT '=== Short-term Data (will be migrated) ===' AS Info;

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
-- CALENDAR DATA SUMMARY
-- ============================================================================

SELECT '' AS '';
SELECT '=== Calendar Data (will be migrated) ===' AS Info;

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
SELECT '=== DISCOVERY COMPLETE ===' AS Info;
SELECT '' AS '';
SELECT 'Ready to migrate! Follow these steps:' AS NextSteps;
SELECT '  1. Stop Domoticz:  sudo systemctl stop domoticz' AS Step1;
SELECT '  2. Backup database: cp domoticz.db domoticz.db.backup' AS Step2;
SELECT '  3. Run migration:  sqlite3 domoticz.db < migration/migrate.sql' AS Step3;
SELECT '  4. Start Domoticz: sudo systemctl start domoticz' AS Step4;

DROP TABLE IF EXISTS _unit_map;
DROP TABLE IF EXISTS _hw_ids;