-- ============================================================================
-- Luxtronik Plugin Migration - Data Migration Script
-- ============================================================================
-- Migrates historical data from legacy plugin to DomoticzEx plugin using
-- fixed Unit ID mapping (independent of language/device names)
-- 
-- Auto-detects old/new plugins by plugin key in Hardware.Extra column:
--   Old plugin: Extra = 'luxtronik'
--   New plugin: Extra = 'luxtronikex'
--
-- BEFORE RUNNING:
-- 1. STOP Domoticz: sudo systemctl stop domoticz
-- 2. BACKUP database: cp domoticz.db domoticz.db.backup
-- 3. Run: sqlite3 domoticz.db < plugins/luxtronik-domoticz-plugin-v2/migration/migrate.sql
-- 4. Restart: sudo systemctl start domoticz
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
    (SELECT ID FROM Hardware WHERE Extra = 'luxtronikex' LIMIT 1) AS new_hw_id;

SELECT '=== AUTO-DETECTED HARDWARE ===' AS Info;

SELECT 
    'Old plugin (luxtronik)' AS Plugin,
    COALESCE(old_hw_id, 'NOT FOUND') AS HW_ID
FROM _hw_ids
UNION ALL
SELECT 
    'New plugin (luxtronikex)' AS Plugin,
    COALESCE(new_hw_id, 'NOT FOUND') AS HW_ID
FROM _hw_ids;

SELECT '' AS '';

-- Verify both plugins exist
SELECT CASE 
    WHEN old_hw_id IS NULL THEN 'ERROR: Old plugin (luxtronik) not found!'
    WHEN new_hw_id IS NULL THEN 'ERROR: New plugin (luxtronikex) not found!'
    ELSE 'OK: Both plugins found, proceeding with migration...'
END AS Status FROM _hw_ids;

-- ============================================================================
-- Unit ID Mapping: OLD PLUGIN (luxtronik) -> NEW PLUGIN (luxtronikex)
-- ============================================================================
-- This mapping is FIXED based on device creation order in code
-- It does NOT depend on device names or language settings
--
-- STORAGE NOTE: Domoticz stores Custom sensor (Type 243/SubType 31) data
-- in the Percentage table, NOT the Fan table!
--
-- NEW PLUGIN UNIT GROUPS:
--   Status (1-9)           - Working mode
--   Controls (10-29)       - All writable devices
--   Power Input (30-39)    - Power consumption meters
--   Heat Output (40-49)    - Heat production meters
--   Efficiency (50-59)     - COP values
--   Heating Circuit (60-79)- Heating temps, spreads, pump, flow
--   DHW (80-89)            - Domestic hot water
--   Environment (90-99)    - Outside and room temps
--   Source Circuit (100-119)- Source temps, spreads, pump, flow
--   Mixing Circuits (120-139)- MC1 and MC2
--   Compressor (140-159)   - Compressor metrics
--   Refrigerant (160-179)  - Refrigerant circuit
--   Statistics (180-199)   - Runtime counters
--   Diagnostics (200-209)  - Error counts, status
--
-- OLD Unit | NEW Unit | Data Table    | Description
-- ---------|----------|---------------|---------------------------
--    1     |    60    | Temperature   | Heat supply temp
--    2     |    61    | Temperature   | Heat return temp
--    3     |    62    | Temperature   | Return temp target
--    4     |    90    | Temperature   | Outside temp
--    5     |    91    | Temperature   | Outside temp avg
--    6     |    80    | Temperature   | DHW temp
--    7     |    15    | Temperature   | DHW temp target (setpoint)
--    8     |   100    | Temperature   | Source inlet temp
--    9     |   101    | Temperature   | Source outlet temp
--   10     |   120    | Temperature   | MC1 temp
--   11     |   121    | Temperature   | MC1 temp target
--   12     |   130    | Temperature   | MC2 temp
--   13     |   131    | Temperature   | MC2 temp target
--   14     |    10    | LightingLog   | Heating mode selector
--   15     |    11    | LightingLog   | Hot water mode selector
--   16     |    13    | LightingLog   | Cooling switch
--   17     |    14    | Temperature   | Temp offset (setpoint)
--   18     |     1    | LightingLog   | Working mode text
--   19     |   106    | Percentage    | Source flow rate
--   20     |   140    | Percentage    | Compressor freq
--   21     |    92    | Temperature   | Room temp
--   22     |    93    | Temperature   | Room temp target
--   23     |    30    | Meter         | Power total
--   24     |    31    | Meter         | Power heating
--   25     |    32    | Meter         | Power DHW
--   26     |    40    | Meter         | Heat out total
--   27     |    41    | Meter         | Heat out heating
--   28     |    42    | Meter         | Heat out DHW
--   29     |    50    | Percentage    | COP total
--   30     |    66    | Percentage    | Heating pump speed
--   31     |   105    | Percentage    | Brine pump speed
--   32     |   160    | Temperature   | Hot gas temp
--   33     |   161    | Temperature   | Suction temp
--   34     |   165    | Percentage    | Superheat
--   35     |   166    | Percentage    | High pressure
--   36     |   167    | Percentage    | Low pressure
--   37     |   102    | Percentage    | Brine temp diff
--   38     |    63    | Percentage    | Heating temp diff
--   39     |    12    | LightingLog   | DHW Power Mode selector
--   40     |    16    | Temperature   | Room temp setpoint
--   41     |    51    | Percentage    | COP heating
--   42     |    52    | Percentage    | COP DHW
-- ============================================================================

DROP TABLE IF EXISTS _unit_map;

CREATE TEMPORARY TABLE _unit_map (
    old_unit INTEGER PRIMARY KEY,
    new_unit INTEGER,
    device_type TEXT,
    description TEXT
);

INSERT INTO _unit_map (old_unit, new_unit, device_type, description) VALUES
    -- Temperature devices (stored in Temperature table)
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
    
    -- Setpoint devices (stored in Temperature table)
    (7,  15,  'setpoint', 'DHW temp target'),
    (17, 14,  'setpoint', 'Temp adjust'),
    (40, 16,  'setpoint', 'Room temp setpoint'),
    
    -- kWh/Meter devices (stored in Meter table)
    (23, 30,  'kwh', 'Power total'),
    (24, 31,  'kwh', 'Power heating'),
    (25, 32,  'kwh', 'Power DHW'),
    (26, 40,  'kwh', 'Heat out total'),
    (27, 41,  'kwh', 'Heat out heating'),
    (28, 42,  'kwh', 'Heat out DHW'),
    
    -- Percentage devices (stored in Percentage table)
    (30, 66,  'pct', 'Heating pump'),
    (31, 105, 'pct', 'Source pump'),
    
    -- Custom sensors - NOTE: Domoticz stores Custom (Type 243/SubType 31) 
    -- data in the Percentage table, NOT Fan table!
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
    
    -- Switch/Text devices (stored in LightingLog table)
    (16, 13,  'light', 'Cooling'),
    (18, 1,   'light', 'Working mode'),
    
    -- Selector switches (also stored in LightingLog table)
    (14, 10,  'light', 'Heating mode'),
    (15, 11,  'light', 'Hot water mode'),
    (39, 12,  'light', 'DHW Power Mode');

-- ============================================================================
-- Create mapping with actual device Idx values
-- ============================================================================

DROP TABLE IF EXISTS _migration_map;

CREATE TEMPORARY TABLE _migration_map AS
SELECT 
    old_dev.ID AS old_idx,
    new_dev.ID AS new_idx,
    um.old_unit,
    um.new_unit,
    um.device_type,
    um.description,
    old_dev.Name AS old_name,
    new_dev.Name AS new_name
FROM _unit_map um
INNER JOIN _hw_ids hw ON 1=1
INNER JOIN DeviceStatus old_dev ON old_dev.Unit = um.old_unit AND old_dev.HardwareID = hw.old_hw_id
INNER JOIN DeviceStatus new_dev ON new_dev.Unit = um.new_unit AND new_dev.HardwareID = hw.new_hw_id;

-- ============================================================================
-- Show mapping for verification
-- ============================================================================

SELECT '' AS '';
SELECT '=== DEVICE MAPPING (Unit ID based) ===' AS Info;

SELECT 
    old_idx AS OldIdx, 
    new_idx AS NewIdx, 
    old_unit AS OldU, 
    new_unit AS NewU, 
    device_type AS Type, 
    description AS Description
FROM _migration_map 
ORDER BY old_unit;

SELECT '' AS '';
SELECT 'Devices to migrate: ' || COUNT(*) AS Summary FROM _migration_map;
SELECT '' AS '';

-- ============================================================================
-- MIGRATE TEMPERATURE DATA (temp + setpoint devices)
-- ============================================================================

SELECT '=== MIGRATING TEMPERATURE DATA ===' AS Info;

INSERT OR IGNORE INTO Temperature (DeviceRowID, Temperature, Chill, Humidity, Barometer, DewPoint, SetPoint, Date)
SELECT 
    m.new_idx,
    t.Temperature,
    t.Chill,
    t.Humidity,
    t.Barometer,
    t.DewPoint,
    t.SetPoint,
    t.Date
FROM Temperature t
INNER JOIN _migration_map m ON t.DeviceRowID = m.old_idx
WHERE m.device_type IN ('temp', 'setpoint')
  AND t.Date < COALESCE(
      (SELECT MIN(Date) FROM Temperature WHERE DeviceRowID = m.new_idx),
      '9999-12-31'
  );

SELECT 'Temperature records migrated: ' || changes() AS Result;

INSERT OR IGNORE INTO Temperature_Calendar (
    DeviceRowID, Temp_Min, Temp_Max, Temp_Avg, 
    Chill_Min, Chill_Max, Humidity, Barometer, DewPoint,
    SetPoint_Min, SetPoint_Max, SetPoint_Avg, Date
)
SELECT 
    m.new_idx,
    tc.Temp_Min, tc.Temp_Max, tc.Temp_Avg,
    tc.Chill_Min, tc.Chill_Max, tc.Humidity, tc.Barometer, tc.DewPoint,
    tc.SetPoint_Min, tc.SetPoint_Max, tc.SetPoint_Avg,
    tc.Date
FROM Temperature_Calendar tc
INNER JOIN _migration_map m ON tc.DeviceRowID = m.old_idx
WHERE m.device_type IN ('temp', 'setpoint')
  AND tc.Date < COALESCE(
      (SELECT MIN(Date) FROM Temperature_Calendar WHERE DeviceRowID = m.new_idx),
      '9999-12-31'
  );

SELECT 'Temperature_Calendar records migrated: ' || changes() AS Result;

-- ============================================================================
-- MIGRATE METER DATA (kWh devices)
-- ============================================================================

SELECT '' AS '';
SELECT '=== MIGRATING METER DATA ===' AS Info;

INSERT OR IGNORE INTO Meter (DeviceRowID, Value, Usage, Date)
SELECT 
    m.new_idx,
    mt.Value,
    mt.Usage,
    mt.Date
FROM Meter mt
INNER JOIN _migration_map m ON mt.DeviceRowID = m.old_idx
WHERE m.device_type = 'kwh'
  AND mt.Date < COALESCE(
      (SELECT MIN(Date) FROM Meter WHERE DeviceRowID = m.new_idx),
      '9999-12-31'
  );

SELECT 'Meter records migrated: ' || changes() AS Result;

INSERT OR IGNORE INTO Meter_Calendar (DeviceRowID, Value, Counter, Date)
SELECT 
    m.new_idx,
    mc.Value,
    mc.Counter,
    mc.Date
FROM Meter_Calendar mc
INNER JOIN _migration_map m ON mc.DeviceRowID = m.old_idx
WHERE m.device_type = 'kwh'
  AND mc.Date < COALESCE(
      (SELECT MIN(Date) FROM Meter_Calendar WHERE DeviceRowID = m.new_idx),
      '9999-12-31'
  );

SELECT 'Meter_Calendar records migrated: ' || changes() AS Result;

-- ============================================================================
-- MIGRATE PERCENTAGE DATA (includes Custom sensors - they use Percentage table!)
-- ============================================================================

SELECT '' AS '';
SELECT '=== MIGRATING PERCENTAGE DATA ===' AS Info;

INSERT OR IGNORE INTO Percentage (DeviceRowID, Percentage, Date)
SELECT 
    m.new_idx,
    p.Percentage,
    p.Date
FROM Percentage p
INNER JOIN _migration_map m ON p.DeviceRowID = m.old_idx
WHERE m.device_type = 'pct'
  AND p.Date < COALESCE(
      (SELECT MIN(Date) FROM Percentage WHERE DeviceRowID = m.new_idx),
      '9999-12-31'
  );

SELECT 'Percentage records migrated: ' || changes() AS Result;

INSERT OR IGNORE INTO Percentage_Calendar (DeviceRowID, Percentage_Min, Percentage_Max, Percentage_Avg, Date)
SELECT 
    m.new_idx,
    pc.Percentage_Min, pc.Percentage_Max, pc.Percentage_Avg,
    pc.Date
FROM Percentage_Calendar pc
INNER JOIN _migration_map m ON pc.DeviceRowID = m.old_idx
WHERE m.device_type = 'pct'
  AND pc.Date < COALESCE(
      (SELECT MIN(Date) FROM Percentage_Calendar WHERE DeviceRowID = m.new_idx),
      '9999-12-31'
  );

SELECT 'Percentage_Calendar records migrated: ' || changes() AS Result;

-- ============================================================================
-- MIGRATE LIGHTINGLOG DATA (switches and text devices)
-- ============================================================================

SELECT '' AS '';
SELECT '=== MIGRATING LIGHTINGLOG DATA ===' AS Info;

INSERT OR IGNORE INTO LightingLog (DeviceRowID, nValue, sValue, User, Date)
SELECT 
    m.new_idx,
    l.nValue,
    l.sValue,
    l.User,
    l.Date
FROM LightingLog l
INNER JOIN _migration_map m ON l.DeviceRowID = m.old_idx
WHERE m.device_type = 'light'
  AND l.Date < COALESCE(
      (SELECT MIN(Date) FROM LightingLog WHERE DeviceRowID = m.new_idx),
      '9999-12-31'
  );

SELECT 'LightingLog records migrated: ' || changes() AS Result;

-- ============================================================================
-- CLEANUP
-- ============================================================================

DROP TABLE IF EXISTS _unit_map;
DROP TABLE IF EXISTS _migration_map;
DROP TABLE IF EXISTS _hw_ids;

SELECT '' AS '';
SELECT '=== MIGRATION COMPLETE ===' AS Info;
SELECT 'Restart Domoticz to see the migrated data!' AS Action;