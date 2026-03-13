"""
Translations for Luxtronik Heat Pump Plugin

Structure:
- DEVICE_TRANSLATIONS: Device names and descriptions keyed by spec_id
- SELECTOR_OPTIONS: Selector switch level names
- WORKING_MODE_STATUSES: Working mode text strings

Notes on gating:
- GATED devices only update during steady-state compressor operation
- This prevents meaningless readings from skewing statistics when idle
- Gate checks: compressor frequency >= minimum target frequency

Device Groups (matching plugin.py structure):
═══════════════════════════════════════════════════
Group 1:  Status Overview (Unit 1)
Group 2:  User Controls (Units 10-16) - ALL WRITABLE
Group 3:  Power Input (Units 30-32)
Group 4:  Heat Output (Units 40-42)
Group 5:  Efficiency (Units 50-52)
Group 6:  Heating Circuit (Units 60-67)
Group 7:  DHW (Unit 80)
Group 8:  Environment (Units 90-93)
Group 9:  Source Circuit (Units 100-106)
Group 10: Mixing Circuits (Units 120-131)
Group 11: Compressor (Units 140-144)
Group 12: Refrigerant Circuit (Units 160-167)
Group 13: Statistics & Counters (Units 180-185)
Group 14: Diagnostics (Units 200-201)
"""

from enum import Enum, auto
from typing import Dict


__all__ = [
    'Language',
    'DEVICE_TRANSLATIONS',
    'SELECTOR_OPTIONS',
    'WORKING_MODE_STATUSES',
]


class Language(Enum):
    """Supported languages"""
    ENGLISH = auto()
    POLISH = auto()
    DUTCH = auto()
    GERMAN = auto()
    FRENCH = auto()


# =============================================================================
# DEVICE TRANSLATIONS
# =============================================================================
# Keyed by spec_id for direct lookup from plugin.py
# Each device has 'name' (max ~20 characters) and optionally 'description' translations
# =============================================================================

DEVICE_TRANSLATIONS: Dict[str, Dict[str, Dict[Language, str]]] = {

    # =========================================================================
    # GROUP 1: STATUS OVERVIEW (Unit 1)
    # =========================================================================
    'working_mode': {
            'name': {
                Language.ENGLISH: 'Working mode',
                Language.POLISH: 'Tryb pracy',
                Language.DUTCH: 'Bedrijfsmodus',
                Language.GERMAN: 'Betriebsart',
                Language.FRENCH: 'Mode actif',
            },
            'description': {
                Language.ENGLISH: 'Current operating state.\nShows: Heating, DHW, Cooling, or Idle.\nDerived from working mode register and power consumption.',
                Language.POLISH: 'Aktualny stan pracy.\nPokazuje: Grzanie, CWU, Chłodzenie lub Bezczynność.\nNa podstawie rejestru trybu i poboru mocy.',
                Language.DUTCH: 'Huidige bedrijfsstatus.\nToont: Verwarmen, Tapwater, Koelen of Rust.\nAfgeleid van modusregister en stroomverbruik.',
                Language.GERMAN: 'Aktueller Betriebszustand.\nZeigt: Heizen, Warmwasser, Kühlen oder Ruhe.\nAbgeleitet aus Modusregister und Stromverbrauch.',
                Language.FRENCH: 'État de fonctionnement actuel.\nAffiche: Chauffage, ECS, Refroidissement ou Repos.\nDérivé du registre de mode et consommation.',
            },
        },

    # =========================================================================
    # GROUP 2: USER CONTROLS (Units 10-16) - ALL WRITABLE
    # =========================================================================
    'heating_mode': {
            'name': {
                Language.ENGLISH: 'Heating mode',
                Language.POLISH: 'Tryb grzania',
                Language.DUTCH: 'Verwarmmode',
                Language.GERMAN: 'Heizmodus',
                Language.FRENCH: 'Mode chauffage',
            },
            'description': {
                Language.ENGLISH: 'Heating operation mode selector.\nAutomatic, Party, Holidays, or Off.\n\n✏️ WRITABLE: Changes are sent to heat pump.',
                Language.POLISH: 'Selektor trybu pracy ogrzewania.\nAutomatyczny, Impreza, Urlop lub Wył.\n\n✏️ ZAPISYWALNY: Zmiany wysyłane do pompy ciepła.',
                Language.DUTCH: 'Verwarmingsmodus selector.\nAutomatisch, Feest, Vakantie of Uit.\n\n✏️ SCHRIJFBAAR: Wijzigingen worden naar warmtepomp gestuurd.',
                Language.GERMAN: 'Heizmodus-Auswahl.\nAutomatisch, Party, Urlaub oder Aus.\n\n✏️ SCHREIBBAR: Änderungen werden zur Wärmepumpe gesendet.',
                Language.FRENCH: 'Sélecteur mode chauffage.\nAutomatique, Fête, Vacances ou Arrêt.\n\n✏️ MODIFIABLE: Les changements sont envoyés à la PAC.',
            },
        },
    'hot_water_mode': {
            'name': {
                Language.ENGLISH: 'Hot water mode',
                Language.POLISH: 'Tryb CWU',
                Language.DUTCH: 'Warmwatermode',
                Language.GERMAN: 'Warmwassermodus',
                Language.FRENCH: 'Mode ECS',
            },
            'description': {
                Language.ENGLISH: 'Hot water operation mode selector.\nAutomatic, Party, Holidays, or Off.\n\n✏️ WRITABLE: Changes are sent to heat pump.',
                Language.POLISH: 'Selektor trybu pracy CWU.\nAutomatyczny, Impreza, Urlop lub Wył.\n\n✏️ ZAPISYWALNY: Zmiany wysyłane do pompy ciepła.',
                Language.DUTCH: 'Tapwatermodus selector.\nAutomatisch, Feest, Vakantie of Uit.\n\n✏️ SCHRIJFBAAR: Wijzigingen worden naar warmtepomp gestuurd.',
                Language.GERMAN: 'Warmwassermodus-Auswahl.\nAutomatisch, Party, Urlaub oder Aus.\n\n✏️ SCHREIBBAR: Änderungen werden zur Wärmepumpe gesendet.',
                Language.FRENCH: 'Sélecteur mode ECS.\nAutomatique, Fête, Vacances ou Arrêt.\n\n✏️ MODIFIABLE: Les changements sont envoyés à la PAC.',
            },
        },
    'dhw_power_mode': {
            'name': {
                Language.ENGLISH: 'DHW Power Mode',
                Language.POLISH: 'Tryb mocy CWU',
                Language.DUTCH: 'Tapwater modus',
                Language.GERMAN: 'WW Leistungsmodus',
                Language.FRENCH: 'Mode puiss. ECS',
            },
            'description': {
                Language.ENGLISH: 'Hot water power mode selector.\nLuxury mode increases compressor speed for faster heating.\n\n✏️ WRITABLE: Changes are sent to heat pump.',
                Language.POLISH: 'Selektor trybu mocy CWU.\nTryb Luksusowy zwiększa obroty sprężarki dla szybszego nagrzewania.\n\n✏️ ZAPISYWALNY: Zmiany wysyłane do pompy ciepła.',
                Language.DUTCH: 'Tapwater vermogensmodus selector.\nLuxe modus verhoogt compressorsnelheid voor sneller verwarmen.\n\n✏️ SCHRIJFBAAR: Wijzigingen worden naar warmtepomp gestuurd.',
                Language.GERMAN: 'Warmwasser-Leistungsmodus-Auswahl.\nLuxus-Modus erhöht Verdichterdrehzahl für schnelleres Aufheizen.\n\n✏️ SCHREIBBAR: Änderungen werden zur Wärmepumpe gesendet.',
                Language.FRENCH: 'Sélecteur mode puissance ECS.\nMode Luxe augmente la vitesse du compresseur pour un chauffage plus rapide.\n\n✏️ MODIFIABLE: Les changements sont envoyés à la PAC.',
            },
        },
    'cooling_enabled': {
            'name': {
                Language.ENGLISH: 'Cooling',
                Language.POLISH: 'Chłodzenie',
                Language.DUTCH: 'Koeling',
                Language.GERMAN: 'Kühlung',
                Language.FRENCH: 'Refroidissement',
            },
            'description': {
                Language.ENGLISH: 'Cooling mode enable/disable switch.\nWhen enabled, allows passive or active cooling.\n\n✏️ WRITABLE: Changes are sent to heat pump.',
                Language.POLISH: 'Przełącznik włączenia/wyłączenia chłodzenia.\nGdy włączony, pozwala na chłodzenie pasywne lub aktywne.\n\n✏️ ZAPISYWALNY: Zmiany wysyłane do pompy ciepła.',
                Language.DUTCH: 'Koeling aan/uit schakelaar.\nIngeschakeld staat passief of actief koelen toe.\n\n✏️ SCHRIJFBAAR: Wijzigingen worden naar warmtepomp gestuurd.',
                Language.GERMAN: 'Kühlung Ein/Aus-Schalter.\nAktiviert erlaubt passives oder aktives Kühlen.\n\n✏️ SCHREIBBAR: Änderungen werden zur Wärmepumpe gesendet.',
                Language.FRENCH: 'Interrupteur activation/désactivation refroidissement.\nActivé permet le refroidissement passif ou actif.\n\n✏️ MODIFIABLE: Les changements sont envoyés à la PAC.',
            },
        },
    'temp_offset': {
            'name': {
                Language.ENGLISH: 'Temp adjust',
                Language.POLISH: 'Korekta temp',
                Language.DUTCH: 'Temp correctie',
                Language.GERMAN: 'Temp. Korrektur',
                Language.FRENCH: 'Ajust. temp.',
            },
            'description': {
                Language.ENGLISH: 'Manual temperature offset.\nAdjusts heating curve up or down (-5 to +5°C).\n\n✏️ WRITABLE: Changes are sent to heat pump.',
                Language.POLISH: 'Ręczna korekta temperatury.\nPrzesuwa krzywą grzania w górę lub w dół (-5 do +5°C).\n\n✏️ ZAPISYWALNY: Zmiany wysyłane do pompy ciepła.',
                Language.DUTCH: 'Handmatige temperatuurcorrectie.\nVerschuift stooklijn omhoog of omlaag (-5 tot +5°C).\n\n✏️ SCHRIJFBAAR: Wijzigingen worden naar warmtepomp gestuurd.',
                Language.GERMAN: 'Manuelle Temperaturkorrektur.\nVerschiebt Heizkurve nach oben oder unten (-5 bis +5°C).\n\n✏️ SCHREIBBAR: Änderungen werden zur Wärmepumpe gesendet.',
                Language.FRENCH: 'Décalage manuel de température.\nAjuste la courbe de chauffe vers le haut ou le bas (-5 à +5°C).\n\n✏️ MODIFIABLE: Les changements sont envoyés à la PAC.',
            },
        },
    'dhw_temp_target': {
            'name': {
                Language.ENGLISH: 'DHW temp target',
                Language.POLISH: 'Temp CWU cel',
                Language.DUTCH: 'Tapwater inst',
                Language.GERMAN: 'Soll Warmw.',
                Language.FRENCH: 'Cible ECS',
            },
            'description': {
                Language.ENGLISH: 'Hot water target temperature setpoint.\nAdjustable via this control (30-65°C).\n\n✏️ WRITABLE: Changes are sent to heat pump.',
                Language.POLISH: 'Nastawa docelowej temperatury CWU.\nRegulowana tym sterowaniem (30-65°C).\n\n✏️ ZAPISYWALNY: Zmiany wysyłane do pompy ciepła.',
                Language.DUTCH: 'Tapwater doeltemperatuur instelling.\nAanpasbaar via deze regelaar (30-65°C).\n\n✏️ SCHRIJFBAAR: Wijzigingen worden naar warmtepomp gestuurd.',
                Language.GERMAN: 'Warmwasser-Solltemperatur Einstellung.\nEinstellbar über diese Steuerung (30-65°C).\n\n✏️ SCHREIBBAR: Änderungen werden zur Wärmepumpe gesendet.',
                Language.FRENCH: 'Consigne de température cible ECS.\nRéglable via cette commande (30-65°C).\n\n✏️ MODIFIABLE: Les changements sont envoyés à la PAC.',
            },
        },
    'room_temp_setpoint': {
            'name': {
                Language.ENGLISH: 'Room temp setpoint',
                Language.POLISH: 'Nastawa temp pokoju',
                Language.DUTCH: 'Kamer temp instelling',
                Language.GERMAN: 'Raum Sollwert',
                Language.FRENCH: 'Consigne temp. pièce',
            },
            'description': {
                Language.ENGLISH: 'Room temperature setpoint control.\nAdjustable target for room-based regulation (15-30°C).\n\n✏️ WRITABLE: Changes are sent to heat pump.',
                Language.POLISH: 'Sterowanie nastawą temperatury pokoju.\nRegulowany cel dla regulacji pokojowej (15-30°C).\n\n✏️ ZAPISYWALNY: Zmiany wysyłane do pompy ciepła.',
                Language.DUTCH: 'Kamertemperatuur setpoint regeling.\nAanpasbaar doel voor kamerregeling (15-30°C).\n\n✏️ SCHRIJFBAAR: Wijzigingen worden naar warmtepomp gestuurd.',
                Language.GERMAN: 'Raumtemperatur-Sollwert-Steuerung.\nEinstellbares Ziel für Raumregelung (15-30°C).\n\n✏️ SCHREIBBAR: Änderungen werden zur Wärmepumpe gesendet.',
                Language.FRENCH: 'Contrôle consigne température pièce.\nCible ajustable pour régulation pièce (15-30°C).\n\n✏️ MODIFIABLE: Les changements sont envoyés à la PAC.',
            },
        },

    # =========================================================================
    # GROUP 3: POWER INPUT (Units 30-32)
    # =========================================================================
    'power_total': {
            'name': {
                Language.ENGLISH: 'Power total',
                Language.POLISH: 'Moc całkowita',
                Language.DUTCH: 'Vermogen totaal',
                Language.GERMAN: 'Leistung gesamt',
                Language.FRENCH: 'Puissance totale',
            },
            'description': {
                Language.ENGLISH: 'Total electrical power consumption.\nIncludes compressor, pumps, and controls.\nUsed as denominator for COP calculation.',
                Language.POLISH: 'Całkowity pobór mocy elektrycznej.\nObejmuje sprężarkę, pompy i sterowanie.\nUżywany jako mianownik do obliczania COP.',
                Language.DUTCH: 'Totaal elektrisch vermogen.\nOmvat compressor, pompen en regeling.\nGebruikt als noemer voor COP-berekening.',
                Language.GERMAN: 'Gesamte elektrische Leistungsaufnahme.\nInkl. Verdichter, Pumpen und Steuerung.\nAls Nenner für COP-Berechnung.',
                Language.FRENCH: 'Consommation électrique totale.\nInclut compresseur, pompes et contrôle.\nUtilisée comme dénominateur pour le COP.',
            },
        },
    'power_heating': {
            'name': {
                Language.ENGLISH: 'Power heating',
                Language.POLISH: 'Moc grzanie',
                Language.DUTCH: 'Vermogen verwarmen',
                Language.GERMAN: 'Leistung Heizen',
                Language.FRENCH: 'Puissance chauffage',
            },
            'description': {
                Language.ENGLISH: 'Electrical consumption during heating mode.\nUsed for heating COP calculation.\n\n🔀 MODE SPLIT: Only logs when in heating mode (mode 0).\nShows 0W in other modes.',
                Language.POLISH: 'Pobór prądu w trybie grzania.\nUżywany do obliczania COP grzania.\n\n🔀 PODZIAŁ TRYBÓW: Loguje tylko w trybie grzania (tryb 0).\nPokazuje 0W w innych trybach.',
                Language.DUTCH: 'Elektrisch verbruik tijdens verwarmen.\nGebruikt voor COP verwarming berekening.\n\n🔀 MODE SPLIT: Alleen log bij verwarmingsmodus (mode 0).\nToont 0W in andere modi.',
                Language.GERMAN: 'Stromverbrauch im Heizbetrieb.\nFür Heizungs-COP-Berechnung.\n\n🔀 MODUS-TRENNUNG: Protokolliert nur im Heizmodus (Modus 0).\nZeigt 0W in anderen Modi.',
                Language.FRENCH: 'Consommation électrique en mode chauffage.\nUtilisée pour le calcul du COP chauffage.\n\n🔀 SÉPARATION MODE: Enregistre uniquement en mode chauffage (mode 0).\nAffiche 0W dans autres modes.',
            },
        },
    'power_dhw': {
            'name': {
                Language.ENGLISH: 'Power DHW',
                Language.POLISH: 'Moc CWU',
                Language.DUTCH: 'Vermogen tapwater',
                Language.GERMAN: 'Leistung WW',
                Language.FRENCH: 'Puissance ECS',
            },
            'description': {
                Language.ENGLISH: 'Electrical consumption during hot water mode.\nUsed for DHW COP calculation.\n\n🔀 MODE SPLIT: Only logs when in DHW mode (mode 1).\nShows 0W in other modes.',
                Language.POLISH: 'Pobór prądu w trybie CWU.\nUżywany do obliczania COP CWU.\n\n🔀 PODZIAŁ TRYBÓW: Loguje tylko w trybie CWU (tryb 1).\nPokazuje 0W w innych trybach.',
                Language.DUTCH: 'Elektrisch verbruik tijdens tapwater.\nGebruikt voor COP tapwater berekening.\n\n🔀 MODE SPLIT: Alleen log bij tapwatermodus (mode 1).\nToont 0W in andere modi.',
                Language.GERMAN: 'Stromverbrauch bei Warmwasserbereitung.\nFür Warmwasser-COP-Berechnung.\n\n🔀 MODUS-TRENNUNG: Protokolliert nur im WW-Modus (Modus 1).\nZeigt 0W in anderen Modi.',
                Language.FRENCH: 'Consommation électrique en mode ECS.\nUtilisée pour le calcul du COP ECS.\n\n🔀 SÉPARATION MODE: Enregistre uniquement en mode ECS (mode 1).\nAffiche 0W dans autres modes.',
            },
        },

    # =========================================================================
    # GROUP 4: HEAT OUTPUT (Units 40-42)
    # =========================================================================
    'heat_out_total': {
            'name': {
                Language.ENGLISH: 'Heat out total',
                Language.POLISH: 'Ciepło całkowite',
                Language.DUTCH: 'Warmte totaal',
                Language.GERMAN: 'Wärme gesamt',
                Language.FRENCH: 'Chaleur totale',
            },
            'description': {
                Language.ENGLISH: 'Thermal power output (heat delivered).\nCalculated from flow rate and temperature difference.\nUsed as numerator for COP calculation.',
                Language.POLISH: 'Moc cieplna (dostarczone ciepło).\nObliczona z przepływu i różnicy temperatur.\nUżywana jako licznik do obliczania COP.',
                Language.DUTCH: 'Thermisch vermogen (geleverde warmte).\nBerekend uit debiet en temperatuurverschil.\nGebruikt als teller voor COP-berekening.',
                Language.GERMAN: 'Thermische Leistung (abgegebene Wärme).\nBerechnet aus Durchfluss und Temperaturdifferenz.\nAls Zähler für COP-Berechnung.',
                Language.FRENCH: 'Puissance thermique (chaleur fournie).\nCalculée à partir du débit et de l\'écart de temp.\nUtilisée comme numérateur pour le COP.',
            },
        },
    'heat_out_heating': {
            'name': {
                Language.ENGLISH: 'Heat out heating',
                Language.POLISH: 'Ciepło grzanie',
                Language.DUTCH: 'Warmte verwarmen',
                Language.GERMAN: 'Wärme Heizen',
                Language.FRENCH: 'Chaleur chauffage',
            },
            'description': {
                Language.ENGLISH: 'Heat output during heating mode.\nUsed for heating COP calculation.\n\n🔀 MODE SPLIT: Only logs when in heating mode (mode 0).\nShows 0W in other modes.',
                Language.POLISH: 'Moc cieplna w trybie grzania.\nUżywana do obliczania COP grzania.\n\n🔀 PODZIAŁ TRYBÓW: Loguje tylko w trybie grzania (tryb 0).\nPokazuje 0W w innych trybach.',
                Language.DUTCH: 'Warmteafgifte tijdens verwarmen.\nGebruikt voor COP verwarming berekening.\n\n🔀 MODE SPLIT: Alleen log bij verwarmingsmodus (mode 0).\nToont 0W in andere modi.',
                Language.GERMAN: 'Wärmeleistung im Heizbetrieb.\nFür Heizungs-COP-Berechnung.\n\n🔀 MODUS-TRENNUNG: Protokolliert nur im Heizmodus (Modus 0).\nZeigt 0W in anderen Modi.',
                Language.FRENCH: 'Puissance thermique en mode chauffage.\nUtilisée pour le calcul du COP chauffage.\n\n🔀 SÉPARATION MODE: Enregistre uniquement en mode chauffage (mode 0).\nAffiche 0W dans autres modes.',
            },
        },
    'heat_out_dhw': {
            'name': {
                Language.ENGLISH: 'Heat out DHW',
                Language.POLISH: 'Ciepło CWU',
                Language.DUTCH: 'Warmte tapwater',
                Language.GERMAN: 'Wärme WW',
                Language.FRENCH: 'Chaleur ECS',
            },
            'description': {
                Language.ENGLISH: 'Heat output during hot water mode.\nUsed for DHW COP calculation.\n\n🔀 MODE SPLIT: Only logs when in DHW mode (mode 1).\nShows 0W in other modes.',
                Language.POLISH: 'Moc cieplna w trybie CWU.\nUżywana do obliczania COP CWU.\n\n🔀 PODZIAŁ TRYBÓW: Loguje tylko w trybie CWU (tryb 1).\nPokazuje 0W w innych trybach.',
                Language.DUTCH: 'Warmteafgifte tijdens tapwater.\nGebruikt voor COP tapwater berekening.\n\n🔀 MODE SPLIT: Alleen log bij tapwatermodus (mode 1).\nToont 0W in andere modi.',
                Language.GERMAN: 'Wärmeleistung bei Warmwasserbereitung.\nFür Warmwasser-COP-Berechnung.\n\n🔀 MODUS-TRENNUNG: Protokolliert nur im WW-Modus (Modus 1).\nZeigt 0W in anderen Modi.',
                Language.FRENCH: 'Puissance thermique en mode ECS.\nUtilisée pour le calcul du COP ECS.\n\n🔀 SÉPARATION MODE: Enregistre uniquement en mode ECS (mode 1).\nAffiche 0W dans autres modes.',
            },
        },

    # =========================================================================
    # GROUP 5: EFFICIENCY (Units 50-52)
    # =========================================================================
    'cop_total': {
            'name': {
                Language.ENGLISH: 'COP total',
                Language.POLISH: 'COP całkowity',
                Language.DUTCH: 'COP totaal',
                Language.GERMAN: 'COP gesamt',
                Language.FRENCH: 'COP total',
            },
            'description': {
                Language.ENGLISH: 'Coefficient of Performance (heat out ÷ power in).\nCombined efficiency for heating and hot water.\nHigher values indicate better efficiency.\n\n⚡ GATED: Only updates during steady-state operation.\nFilters: Heating/DHW modes only, power >10W, heat >100W.\nPrevents idle/transient values from skewing averages.',
                Language.POLISH: 'Współczynnik wydajności (ciepło ÷ prąd).\nŁączna wydajność ogrzewania i CWU.\nWyższe wartości = lepsza wydajność.\n\n⚡ BRAMKOWANY: Aktualizuje tylko w stanie ustalonym.\nFiltry: Tylko tryby Grzanie/CWU, moc >10W, ciepło >100W.\nZapobiega zafałszowaniu średnich przez wartości bezczynności.',
                Language.DUTCH: 'Coëfficiënt of Performance (warmte ÷ stroom).\nGecombineerde efficiëntie verwarming en tapwater.\nHogere waarden = betere efficiëntie.\n\n⚡ GATED: Alleen updates tijdens stabiele werking.\nFilters: Alleen Verwarmen/Tapwater modi, vermogen >10W, warmte >100W.\nVoorkomt vervuiling van gemiddelden.',
                Language.GERMAN: 'Leistungszahl (Wärme ÷ Strom).\nGesamteffizienz Heizung und Warmwasser.\nHöhere Werte = bessere Effizienz.\n\n⚡ GATED: Aktualisiert nur im stabilen Betrieb.\nFilter: Nur Heiz-/WW-Modi, Leistung >10W, Wärme >100W.\nVerhindert Verfälschung der Durchschnitte.',
                Language.FRENCH: 'Coefficient de Performance (chaleur ÷ électricité).\nEfficacité combinée chauffage et ECS.\nValeurs plus élevées = meilleure efficacité.\n\n⚡ GATED: Mises à jour uniquement en régime établi.\nFiltres: Modes Chauffage/ECS uniquement, puissance >10W, chaleur >100W.\nÉvite de fausser les moyennes.',
            },
        },
    'cop_heating': {
            'name': {
                Language.ENGLISH: 'COP heating',
                Language.POLISH: 'COP grzanie',
                Language.DUTCH: 'COP verwarmen',
                Language.GERMAN: 'COP Heizen',
                Language.FRENCH: 'COP chauffage',
            },
            'description': {
                Language.ENGLISH: 'Efficiency during space heating mode only.\nHigher with low-temperature systems (floor heating).\nVaries with source temperature and demand.\n\n⚡ GATED: Only updates during steady-state heating operation.\nMode filter: Only mode 0 (heating).\nPrevents DHW cycles from affecting heating statistics.',
                Language.POLISH: 'Wydajność tylko w trybie ogrzewania pomieszczeń.\nWyższa przy systemach niskotemperaturowych (podłogówka).\nZmienia się z temperaturą źródła i zapotrzebowaniem.\n\n⚡ BRAMKOWANY: Aktualizuje tylko podczas stabilnego grzania.\nFiltr trybu: Tylko tryb 0 (grzanie).\nZapobiega wpływowi cykli CWU na statystyki grzania.',
                Language.DUTCH: 'Efficiëntie alleen tijdens verwarmingsmodus.\nHoger bij lage temperatuur systemen (vloerverwarming).\nVarieert met brontemperatuur en vraag.\n\n⚡ GATED: Alleen updates tijdens stabiele verwarming.\nModefilter: Alleen mode 0 (verwarmen).\nVoorkomt invloed van tapwatercycli op verwarmingsstatistieken.',
                Language.GERMAN: 'Effizienz nur im Raumheizbetrieb.\nHöher bei Niedertemperatursystemen (Fußbodenheizung).\nVariiert mit Quellentemperatur und Bedarf.\n\n⚡ GATED: Aktualisiert nur während stabilem Heizbetrieb.\nModusfilter: Nur Modus 0 (Heizen).\nVerhindert Einfluss von WW-Zyklen auf Heizstatistiken.',
                Language.FRENCH: 'Efficacité en mode chauffage uniquement.\nPlus élevée avec systèmes basse température (plancher chauffant).\nVarie avec la température source et la demande.\n\n⚡ GATED: Mises à jour uniquement pendant chauffage stable.\nFiltre mode: Mode 0 (chauffage) uniquement.\nÉvite l\'influence des cycles ECS sur les statistiques.',
            },
        },
    'cop_dhw': {
            'name': {
                Language.ENGLISH: 'COP DHW',
                Language.POLISH: 'COP CWU',
                Language.DUTCH: 'COP tapwater',
                Language.GERMAN: 'COP Warmwasser',
                Language.FRENCH: 'COP ECS',
            },
            'description': {
                Language.ENGLISH: 'Efficiency during hot water production only.\nTypically lower than heating (higher target temp 50-60°C).\nDepends on tank and source temperatures.\n\n⚡ GATED: Only updates during steady-state DHW operation.\nMode filter: Only mode 1 (DHW).\nPrevents heating cycles from affecting DHW statistics.',
                Language.POLISH: 'Wydajność tylko podczas produkcji ciepłej wody.\nZwykle niższa niż ogrzewanie (wyższa temp. 50-60°C).\nZależy od temp. zasobnika i źródła.\n\n⚡ BRAMKOWANY: Aktualizuje tylko podczas stabilnej produkcji CWU.\nFiltr trybu: Tylko tryb 1 (CWU).\nZapobiega wpływowi cykli grzania na statystyki CWU.',
                Language.DUTCH: 'Efficiëntie alleen bij warmwaterproductie.\nTypisch lager dan verwarmen (hogere temp. 50-60°C).\nAfhankelijk van boiler- en brontemperatuur.\n\n⚡ GATED: Alleen updates tijdens stabiele tapwaterproductie.\nModefilter: Alleen mode 1 (tapwater).\nVoorkomt invloed van verwarmcycli op tapwaterstatistieken.',
                Language.GERMAN: 'Effizienz nur bei Warmwasserbereitung.\nTypisch niedriger als Heizen (höhere Temp. 50-60°C).\nAbhängig von Speicher- und Quellentemperatur.\n\n⚡ GATED: Aktualisiert nur während stabiler WW-Bereitung.\nModusfilter: Nur Modus 1 (WW).\nVerhindert Einfluss von Heizzyklen auf WW-Statistiken.',
                Language.FRENCH: 'Efficacité en production d\'eau chaude uniquement.\nTypiquement inférieure au chauffage (cible 50-60°C).\nDépend des températures ballon et source.\n\n⚡ GATED: Mises à jour uniquement pendant production ECS stable.\nFiltre mode: Mode 1 (ECS) uniquement.\nÉvite l\'influence des cycles chauffage sur les statistiques ECS.',
            },
        },

    # =========================================================================
    # GROUP 6: HEATING CIRCUIT (Units 60-67)
    # =========================================================================
    'heat_supply_temp': {
            'name': {
                Language.ENGLISH: 'Heat supply temp',
                Language.POLISH: 'Temp zasilania',
                Language.DUTCH: 'Aanvoertemp',
                Language.GERMAN: 'Vorlauftemp.',
                Language.FRENCH: 'Temp. départ',
            },
            'description': {
                Language.ENGLISH: 'Water temperature leaving heat pump.\nController target based on outside temperature.\nUsed with return temp for heat output calculation.',
                Language.POLISH: 'Temperatura wody opuszczającej pompę ciepła.\nCel sterownika zależny od temp. zewnętrznej.\nUżywana z temp. powrotu do obliczania mocy cieplnej.',
                Language.DUTCH: 'Watertemperatuur vanuit warmtepomp.\nSetpoint gebaseerd op buitentemperatuur.\nGebruikt met retourtemp voor warmteberekening.',
                Language.GERMAN: 'Wassertemperatur aus Wärmepumpe.\nSollwert basiert auf Außentemperatur.\nMit Rücklauftemp. für Wärmeleistungsberechnung.',
                Language.FRENCH: 'Température de l\'eau sortant de la PAC.\nCible basée sur la température extérieure.\nUtilisée avec retour pour calcul puissance.',
            },
        },
    'heat_return_temp': {
            'name': {
                Language.ENGLISH: 'Heat return temp',
                Language.POLISH: 'Temp powrotu',
                Language.DUTCH: 'Retourtemp',
                Language.GERMAN: 'Rücklauftemp.',
                Language.FRENCH: 'Temp. retour',
            },
            'description': {
                Language.ENGLISH: 'Water temperature returning from heating system.\nDifference from supply indicates heat delivered.\nUsed for thermal power calculation.',
                Language.POLISH: 'Temperatura wody wracającej z instalacji.\nRóżnica od zasilania wskazuje oddane ciepło.\nUżywana do obliczania mocy cieplnej.',
                Language.DUTCH: 'Watertemperatuur terug van cv-systeem.\nVerschil met aanvoer toont geleverde warmte.\nGebruikt voor thermisch vermogen berekening.',
                Language.GERMAN: 'Wassertemperatur vom Heizsystem zurück.\nDifferenz zum Vorlauf zeigt abgegebene Wärme.\nFür Wärmeleistungsberechnung.',
                Language.FRENCH: 'Température de l\'eau retournant du système.\nDifférence avec départ indique chaleur fournie.\nUtilisée pour calcul puissance thermique.',
            },
        },
    'return_temp_target': {
            'name': {
                Language.ENGLISH: 'Return temp target',
                Language.POLISH: 'Temp powr cel',
                Language.DUTCH: 'Retour doel',
                Language.GERMAN: 'Soll-Rückl.t',
                Language.FRENCH: 'Cible retour',
            },
            'description': {
                Language.ENGLISH: 'Target return temperature calculated by controller.\nBased on heating curve and outside temperature.\nCompressor modulates to achieve this target.',
                Language.POLISH: 'Docelowa temp. powrotu obliczona przez sterownik.\nNa podstawie krzywej grzania i temp. zewnętrznej.\nSprężarka moduluje aby osiągnąć cel.',
                Language.DUTCH: 'Doel retourtemperatuur berekend door regelaar.\nGebaseerd op stooklijn en buitentemperatuur.\nCompressor moduleert om doel te bereiken.',
                Language.GERMAN: 'Soll-Rücklauftemperatur vom Regler berechnet.\nBasiert auf Heizkurve und Außentemperatur.\nVerdichter moduliert zum Erreichen des Ziels.',
                Language.FRENCH: 'Température retour cible calculée par le régulateur.\nBasée sur courbe de chauffe et temp. ext.\nLe compresseur module pour atteindre cette cible.',
            },
        },
    'heating_temp_diff': {
            'name': {
                Language.ENGLISH: 'Heating ΔT',
                Language.POLISH: 'ΔT grzania',
                Language.DUTCH: 'Verwarming ΔT',
                Language.GERMAN: 'Heizung ΔT',
                Language.FRENCH: 'ΔT chauffage',
            },
            'description': {
                Language.ENGLISH: 'Temperature difference across heating circuit (supply - return).\nIndicates heat delivery to the building.\n\n⚡ GATED: Only updates during steady-state operation.\nWhen idle, ΔT approaches zero as loop equilibrates.',
                Language.POLISH: 'Różnica temperatur w obiegu grzewczym (zasilanie - powrót).\nWskazuje ilość ciepła dostarczonego do budynku.\n\n⚡ BRAMKOWANY: Aktualizuje tylko w stanie ustalonym.\nGdy bezczynny, ΔT zbliża się do zera.',
                Language.DUTCH: 'Temperatuurverschil over verwarmingscircuit (aanvoer - retour).\nIndicatie van warmtelevering aan gebouw.\n\n⚡ GATED: Alleen updates tijdens stabiele werking.\nBij rust nadert ΔT nul door evenwicht.',
                Language.GERMAN: 'Temperaturdifferenz im Heizkreis (Vorlauf - Rücklauf).\nZeigt Wärmeabgabe an das Gebäude.\n\n⚡ GATED: Aktualisiert nur im stabilen Betrieb.\nIm Ruhezustand nähert sich ΔT Null.',
                Language.FRENCH: 'Différence de température circuit chauffage (départ - retour).\nIndique la chaleur fournie au bâtiment.\n\n⚡ GATED: Mises à jour uniquement en régime établi.\nAu repos, ΔT tend vers zéro par équilibrage.',
            },
        },
    'heating_spread_target': {
            'name': {
                Language.ENGLISH: 'Heating ΔT target',
                Language.POLISH: 'ΔT grzania cel',
                Language.DUTCH: 'Verw. ΔT doel',
                Language.GERMAN: 'Heizung ΔT Soll',
                Language.FRENCH: 'ΔT chauff. cible',
            },
            'description': {
                Language.ENGLISH: 'Controller\'s target temperature spread for heating circuit.\nHeating pump speed adjusts to achieve this ΔT.\nLarger spread = more heat delivery per liter of flow.',
                Language.POLISH: 'Docelowy rozrzut temperatur dla obiegu grzewczego.\nPrędkość pompy grzewczej dostosowuje się do tego ΔT.\nWiększy rozrzut = więcej ciepła na litr przepływu.',
                Language.DUTCH: 'Doeltemperatuurverschil voor verwarmingscircuit.\nCv-pomp snelheid past aan om dit ΔT te bereiken.\nGroter verschil = meer warmte per liter debiet.',
                Language.GERMAN: 'Soll-Temperaturspreizung für Heizkreis.\nHeizungspumpen-Drehzahl passt sich an dieses ΔT an.\nGrößere Spreizung = mehr Wärme pro Liter Durchfluss.',
                Language.FRENCH: 'Écart de température cible pour circuit chauffage.\nVitesse pompe chauffage s\'ajuste à ce ΔT.\nÉcart plus grand = plus de chaleur par litre de débit.',
            },
        },
    'heating_spread_actual': {
            'name': {
                Language.ENGLISH: 'Heating ΔT actual',
                Language.POLISH: 'ΔT grzania akt',
                Language.DUTCH: 'Verw. ΔT actueel',
                Language.GERMAN: 'Heizung ΔT Ist',
                Language.FRENCH: 'ΔT chauff. réel',
            },
            'description': {
                Language.ENGLISH: 'Controller\'s measured temperature spread for heating circuit.\nCompare to target to assess pump performance.\nShould closely track the target value.',
                Language.POLISH: 'Zmierzony rozrzut temperatur obiegu grzewczego.\nPorównaj z celem aby ocenić pracę pompy.\nPowinien być zbliżony do wartości docelowej.',
                Language.DUTCH: 'Gemeten temperatuurverschil voor verwarmingscircuit.\nVergelijk met doel voor pompprestatiecheck.\nZou dicht bij doelwaarde moeten liggen.',
                Language.GERMAN: 'Gemessene Temperaturspreizung für Heizkreis.\nMit Sollwert vergleichen für Pumpenleistung.\nSollte dem Sollwert folgen.',
                Language.FRENCH: 'Écart de température mesuré pour circuit chauffage.\nComparer à la cible pour évaluer la pompe.\nDevrait suivre la valeur cible.',
            },
        },
    'heating_pump_speed': {
            'name': {
                Language.ENGLISH: 'Heating pump',
                Language.POLISH: 'Pompa grzewcza',
                Language.DUTCH: 'Cv-pomp',
                Language.GERMAN: 'Heizungspumpe',
                Language.FRENCH: 'Pompe chauffage',
            },
            'description': {
                Language.ENGLISH: 'Heating circuit circulation pump speed.\nController adjusts to match demand.\nVaries between heating and DHW modes.',
                Language.POLISH: 'Prędkość pompy obiegu grzewczego.\nSterownik dostosowuje do zapotrzebowania.\nRóżna w trybie grzania i CWU.',
                Language.DUTCH: 'Cv-circulatiepomp snelheid.\nRegeling past aan op vraag.\nVarieert tussen verwarmen en tapwater.',
                Language.GERMAN: 'Heizkreis-Umwälzpumpe Drehzahl.\nRegler passt an Bedarf an.\nVariiert zwischen Heiz- und WW-Betrieb.',
                Language.FRENCH: 'Vitesse pompe circuit chauffage.\nLe régulateur ajuste selon la demande.\nVarie entre chauffage et ECS.',
            },
        },
    'heating_flow': {
            'name': {
                Language.ENGLISH: 'Heating flow',
                Language.POLISH: 'Przepływ grzewczy',
                Language.DUTCH: 'Verwarmingsdebiet',
                Language.GERMAN: 'Heizungsdurchfluss',
                Language.FRENCH: 'Débit chauffage',
            },
            'description': {
                Language.ENGLISH: 'Water flow rate through heating circuit.\nMeasured by heat meter (WMZ) on HUP pump circuit.\nUsed for thermal power calculation.',
                Language.POLISH: 'Przepływ wody przez obieg grzewczy.\nMierzony przez ciepłomierz (WMZ) na pompie HUP.\nUżywany do obliczania mocy cieplnej.',
                Language.DUTCH: 'Waterdebiet door verwarmingscircuit.\nGemeten door warmtemeter (WMZ) op HUP-pompcircuit.\nGebruikt voor thermisch vermogen berekening.',
                Language.GERMAN: 'Wasserdurchfluss im Heizkreis.\nGemessen durch Wärmemengenzähler (WMZ) am HUP-Pumpenkreis.\nFür Wärmeleistungsberechnung verwendet.',
                Language.FRENCH: 'Débit d\'eau dans le circuit chauffage.\nMesuré par compteur de chaleur (WMZ) sur circuit pompe HUP.\nUtilisé pour le calcul de puissance thermique.',
            },
        },

    # =========================================================================
    # GROUP 7: DHW (Unit 80)
    # =========================================================================
    'dhw_temp': {
            'name': {
                Language.ENGLISH: 'DHW temp',
                Language.POLISH: 'Temp CWU',
                Language.DUTCH: 'Tapwater temp',
                Language.GERMAN: 'Warmw. temp.',
                Language.FRENCH: 'Temp. ECS',
            },
            'description': {
                Language.ENGLISH: 'Hot water tank temperature.\nTarget typically 45-55°C for domestic use.\nHigher targets reduce COP due to larger temperature lift.',
                Language.POLISH: 'Temperatura zasobnika CWU.\nCel zwykle 45-55°C do użytku domowego.\nWyższe cele obniżają COP przez większy skok temperatur.',
                Language.DUTCH: 'Boilertemperatuur.\nSetpoint typisch 45-55°C voor huishoudelijk gebruik.\nHogere doelen verlagen COP door grotere temperatuurlift.',
                Language.GERMAN: 'Warmwasserspeicher-Temperatur.\nSollwert typisch 45-55°C für Haushaltsnutzung.\nHöhere Ziele verringern COP durch größeren Temperaturhub.',
                Language.FRENCH: 'Température du ballon ECS.\nCible typiquement 45-55°C pour usage domestique.\nCibles plus élevées réduisent le COP.',
            },
        },

    # =========================================================================
    # GROUP 8: ENVIRONMENT (Units 90-93)
    # =========================================================================
    'outside_temp': {
            'name': {
                Language.ENGLISH: 'Outside temp',
                Language.POLISH: 'Temp zewnętrzna',
                Language.DUTCH: 'Buitentemp',
                Language.GERMAN: 'Außentemp.',
                Language.FRENCH: 'Temp. ext.',
            },
            'description': {
                Language.ENGLISH: 'Ambient temperature sensor.\nUsed for heating curve calculation.\nPrimary input for automatic temperature control.',
                Language.POLISH: 'Czujnik temperatury zewnętrznej.\nUżywany do obliczania krzywej grzania.\nGłówne wejście do automatycznej regulacji.',
                Language.DUTCH: 'Buitentemperatuursensor.\nGebruikt voor stooklijnberekening.\nPrimaire input voor automatische regeling.',
                Language.GERMAN: 'Außentemperaturfühler.\nFür Heizkurvenberechnung.\nPrimärer Eingang für automatische Regelung.',
                Language.FRENCH: 'Sonde de température extérieure.\nUtilisée pour le calcul de la courbe de chauffe.\nEntrée principale pour le contrôle automatique.',
            },
        },
    'outside_temp_avg': {
            'name': {
                Language.ENGLISH: 'Outside temp avg',
                Language.POLISH: 'Temp zewn. śred',
                Language.DUTCH: 'Buitent. gem',
                Language.GERMAN: 'Ø Außentemp.',
                Language.FRENCH: 'Moy. temp. ext.',
            },
            'description': {
                Language.ENGLISH: 'Averaged outside temperature.\nFilters short-term fluctuations for stable control.\nUsed by controller for demand anticipation.',
                Language.POLISH: 'Uśredniona temperatura zewnętrzna.\nFiltruje krótkotrwałe wahania.\nUżywana przez sterownik do przewidywania zapotrzebowania.',
                Language.DUTCH: 'Gemiddelde buitentemperatuur.\nFiltert korte schommelingen voor stabiele regeling.\nGebruikt door regelaar voor vraagvoorspelling.',
                Language.GERMAN: 'Gemittelte Außentemperatur.\nFiltert kurzfristige Schwankungen.\nVom Regler für Bedarfsvorhersage verwendet.',
                Language.FRENCH: 'Température extérieure moyennée.\nFiltre les fluctuations pour un contrôle stable.\nUtilisée par le régulateur pour anticipation.',
            },
        },
    'room_temp': {
            'name': {
                Language.ENGLISH: 'Room temp',
                Language.POLISH: 'Temp pokoju',
                Language.DUTCH: 'Kamertemp',
                Language.GERMAN: 'Raumtemp.',
                Language.FRENCH: 'Temp. pièce',
            },
            'description': {
                Language.ENGLISH: 'Reference room temperature sensor.\nOptional input for room-based control.\nCan be used with room influence setting.',
                Language.POLISH: 'Czujnik temperatury pomieszczenia referencyjnego.\nOpcjonalne wejście do regulacji pokojowej.\nMoże być używany z nastawą wpływu pokoju.',
                Language.DUTCH: 'Referentie kamertemperatuursensor.\nOptionele input voor kamerregeling.\nKan worden gebruikt met kamerinvloed instelling.',
                Language.GERMAN: 'Referenz-Raumtemperaturfühler.\nOptionaler Eingang für Raumregelung.\nKann mit Raumeinfluss-Einstellung verwendet werden.',
                Language.FRENCH: 'Sonde température de référence.\nEntrée optionnelle pour régulation pièce.\nPeut être utilisée avec le réglage d\'influence pièce.',
            },
        },
    'room_temp_target': {
            'name': {
                Language.ENGLISH: 'Room temp target',
                Language.POLISH: 'Temp pokoju cel',
                Language.DUTCH: 'Kamer doel',
                Language.GERMAN: 'Raum Soll',
                Language.FRENCH: 'Cible pièce',
            },
            'description': {
                Language.ENGLISH: 'Room temperature setpoint from controller.\nRead-only display of current target.\nActual setpoint controlled via room_temp_setpoint.',
                Language.POLISH: 'Nastawa temperatury pokoju ze sterownika.\nWyświetlanie aktualnego celu (tylko odczyt).\nRzeczywista nastawa przez room_temp_setpoint.',
                Language.DUTCH: 'Kamertemperatuur setpoint van regelaar.\nAlleen-lezen weergave van huidige doel.\nWerkelijke setpoint via room_temp_setpoint.',
                Language.GERMAN: 'Raumtemperatur-Sollwert vom Regler.\nNur-Lesen-Anzeige des aktuellen Ziels.\nTatsächlicher Sollwert über room_temp_setpoint.',
                Language.FRENCH: 'Consigne température pièce du régulateur.\nAffichage lecture seule de la cible actuelle.\nConsigne réelle via room_temp_setpoint.',
            },
        },

    # =========================================================================
    # GROUP 9: SOURCE CIRCUIT (Units 100-106)
    # =========================================================================
    'source_in_temp': {
            'name': {
                Language.ENGLISH: 'Source inlet temp',
                Language.POLISH: 'Temp źródła wej',
                Language.DUTCH: 'Bron inlaat',
                Language.GERMAN: 'Quelle Einl.',
                Language.FRENCH: 'Source entrée',
            },
            'description': {
                Language.ENGLISH: 'Brine/water entering from ground loop or air.\nSource temperature affects system efficiency.\nHigher source temp = better COP.',
                Language.POLISH: 'Solanka/woda z kolektora gruntowego lub powietrza.\nTemperatura źródła wpływa na wydajność.\nWyższa temp. źródła = lepszy COP.',
                Language.DUTCH: 'Brine/water vanuit bodemcollector of lucht.\nBrontemperatuur beïnvloedt efficiëntie.\nHogere brontemp = betere COP.',
                Language.GERMAN: 'Sole/Wasser aus Erdkollektor oder Luft.\nQuellentemperatur beeinflusst Effizienz.\nHöhere Quellentemp. = besserer COP.',
                Language.FRENCH: 'Saumure/eau du capteur ou de l\'air.\nTempérature source affecte l\'efficacité.\nTemp. source plus élevée = meilleur COP.',
            },
        },
    'source_out_temp': {
            'name': {
                Language.ENGLISH: 'Source outlet temp',
                Language.POLISH: 'Temp źródła wyj',
                Language.DUTCH: 'Bron uitlaat',
                Language.GERMAN: 'Quelle Ausl.',
                Language.FRENCH: 'Source sortie',
            },
            'description': {
                Language.ENGLISH: 'Brine/water returning to ground loop.\nCooler than inlet during heating mode.\nWarmer than inlet during passive cooling.',
                Language.POLISH: 'Solanka/woda wracająca do kolektora.\nChłodniejsza niż wlot w trybie grzania.\nCieplejsza niż wlot w chłodzeniu pasywnym.',
                Language.DUTCH: 'Brine/water terug naar bodemcollector.\nKouder dan inlaat tijdens verwarmen.\nWarmer dan inlaat bij passief koelen.',
                Language.GERMAN: 'Sole/Wasser zurück zum Erdkollektor.\nKälter als Einlass im Heizbetrieb.\nWärmer als Einlass bei passiver Kühlung.',
                Language.FRENCH: 'Saumure/eau retournant au capteur.\nPlus froid qu\'à l\'entrée en mode chauffage.\nPlus chaud en refroidissement passif.',
            },
        },
    'brine_temp_diff': {
            'name': {
                Language.ENGLISH: 'Source ΔT',
                Language.POLISH: 'ΔT źródła',
                Language.DUTCH: 'Bron ΔT',
                Language.GERMAN: 'Quelle ΔT',
                Language.FRENCH: 'ΔT source',
            },
            'description': {
                Language.ENGLISH: 'Temperature difference across source loop (inlet - outlet).\nPositive: extracting heat (heating mode).\nNegative: rejecting heat (passive cooling).\n\n⚡ GATED: Only updates during steady-state operation.\nWhen idle, ΔT approaches zero as loop equilibrates.',
                Language.POLISH: 'Różnica temperatur w obiegu źródłowym (wlot - wylot).\nDodatnia: pobór ciepła (grzanie).\nUjemna: oddawanie ciepła (chłodzenie pasywne).\n\n⚡ BRAMKOWANY: Aktualizuje tylko w stanie ustalonym.\nGdy bezczynny, ΔT zbliża się do zera.',
                Language.DUTCH: 'Temperatuurverschil over bronlus (inlaat - uitlaat).\nPositief: warmte onttrekken (verwarmen).\nNegatief: warmte afvoeren (passief koelen).\n\n⚡ GATED: Alleen updates tijdens stabiele werking.\nBij rust nadert ΔT nul door evenwicht.',
                Language.GERMAN: 'Temperaturdifferenz über Quellkreis (Einlass - Auslass).\nPositiv: Wärmeaufnahme (Heizen).\nNegativ: Wärmeabgabe (passive Kühlung).\n\n⚡ GATED: Aktualisiert nur im stabilen Betrieb.\nIm Ruhezustand nähert sich ΔT Null.',
                Language.FRENCH: 'Différence de température boucle source (entrée - sortie).\nPositif: extraction de chaleur (chauffage).\nNégatif: rejet de chaleur (refroidissement passif).\n\n⚡ GATED: Mises à jour uniquement en régime établi.\nAu repos, ΔT tend vers zéro par équilibrage.',
            },
        },
    'source_spread_target': {
            'name': {
                Language.ENGLISH: 'Source ΔT target',
                Language.POLISH: 'ΔT źródła cel',
                Language.DUTCH: 'Bron ΔT doel',
                Language.GERMAN: 'Quelle ΔT Soll',
                Language.FRENCH: 'ΔT source cible',
            },
            'description': {
                Language.ENGLISH: 'Controller\'s target temperature spread for source circuit.\nBrine pump speed adjusts to achieve this ΔT.\nLarger spread = more heat extraction per liter of flow.',
                Language.POLISH: 'Docelowy rozrzut temperatur dla obiegu źródłowego.\nPrędkość pompy solanki dostosowuje się do tego ΔT.\nWiększy rozrzut = więcej ciepła na litr przepływu.',
                Language.DUTCH: 'Doeltemperatuurverschil voor broncircuit.\nBrinepomp snelheid past aan om dit ΔT te bereiken.\nGroter verschil = meer warmte per liter debiet.',
                Language.GERMAN: 'Soll-Temperaturspreizung für Quellkreis.\nSolepumpen-Drehzahl passt sich an dieses ΔT an.\nGrößere Spreizung = mehr Wärme pro Liter Durchfluss.',
                Language.FRENCH: 'Écart de température cible pour circuit source.\nVitesse pompe saumure s\'ajuste à ce ΔT.\nÉcart plus grand = plus de chaleur par litre de débit.',
            },
        },
    'source_spread_actual': {
            'name': {
                Language.ENGLISH: 'Source ΔT actual',
                Language.POLISH: 'ΔT źródła akt',
                Language.DUTCH: 'Bron ΔT actueel',
                Language.GERMAN: 'Quelle ΔT Ist',
                Language.FRENCH: 'ΔT source réel',
            },
            'description': {
                Language.ENGLISH: 'Controller\'s measured temperature spread for source circuit.\nCompare to target to assess pump performance.\nShould closely track the target value.',
                Language.POLISH: 'Zmierzony rozrzut temperatur obiegu źródłowego.\nPorównaj z celem aby ocenić pracę pompy.\nPowinien być zbliżony do wartości docelowej.',
                Language.DUTCH: 'Gemeten temperatuurverschil voor broncircuit.\nVergelijk met doel voor pompprestatiecheck.\nZou dicht bij doelwaarde moeten liggen.',
                Language.GERMAN: 'Gemessene Temperaturspreizung für Quellkreis.\nMit Sollwert vergleichen für Pumpenleistung.\nSollte dem Sollwert folgen.',
                Language.FRENCH: 'Écart de température mesuré pour circuit source.\nComparer à la cible pour évaluer la pompe.\nDevrait suivre la valeur cible.',
            },
        },
    'brine_pump_speed': {
            'name': {
                Language.ENGLISH: 'Source pump',
                Language.POLISH: 'Pompa źródła',
                Language.DUTCH: 'Bronpomp',
                Language.GERMAN: 'Solepumpe',
                Language.FRENCH: 'Pompe source',
            },
            'description': {
                Language.ENGLISH: 'Source circuit circulation pump speed.\nCirculates brine through ground loop.\nAdjusts to optimize heat extraction.',
                Language.POLISH: 'Prędkość pompy obiegu źródłowego.\nPrzepompowuje solankę przez kolektor gruntowy.\nDostosowuje się do optymalnego poboru ciepła.',
                Language.DUTCH: 'Broncircuit circulatiepomp snelheid.\nCirculeert brine door bodemcollector.\nPast aan voor optimale warmteonttrekking.',
                Language.GERMAN: 'Quellkreis-Umwälzpumpe Drehzahl.\nZirkuliert Sole durch Erdkollektor.\nOptimiert für Wärmeentzug.',
                Language.FRENCH: 'Vitesse pompe circuit source.\nFait circuler la saumure dans le capteur.\nAjuste pour optimiser l\'extraction.',
            },
        },
    'source_flow': {
            'name': {
                Language.ENGLISH: 'Source flow',
                Language.POLISH: 'Przepływ źródła',
                Language.DUTCH: 'Brondebiet',
                Language.GERMAN: 'Quellendurchfluss',
                Language.FRENCH: 'Débit source',
            },
            'description': {
                Language.ENGLISH: 'Brine flow rate through source circuit.\nMeasured by flow sensor on VBO pump circuit.\nHigher flow during increased heat extraction.',
                Language.POLISH: 'Przepływ solanki przez obieg źródłowy.\nMierzony przez czujnik przepływu na pompie VBO.\nWyższy przepływ przy zwiększonym poborze ciepła.',
                Language.DUTCH: 'Pekelstroom door broncircuit.\nGemeten door flowsensor op VBO-pompcircuit.\nHoger debiet bij verhoogde warmteonttrekking.',
                Language.GERMAN: 'Sole-Durchfluss im Quellenkreis.\nGemessen am Durchflusssensor im VBO-Pumpenkreis.\nHöherer Durchfluss bei erhöhter Wärmeentnahme.',
                Language.FRENCH: 'Débit de saumure dans le circuit source.\nMesuré par capteur de débit sur circuit pompe VBO.\nDébit plus élevé lors d\'une extraction accrue.',
            },
        },

    # =========================================================================
    # GROUP 10: MIXING CIRCUITS (Units 120-131)
    # =========================================================================
    'mc1_temp': {
            'name': {
                Language.ENGLISH: 'Circuit 1 temp',
                Language.POLISH: 'Temp obieg 1',
                Language.DUTCH: 'Groep 1 temp',
                Language.GERMAN: 'Kreis 1 Temp.',
                Language.FRENCH: 'Circuit 1 temp',
            },
            'description': {
                Language.ENGLISH: 'Mixing circuit 1 supply temperature.\nControlled by mixing valve for zone.\nIndependent temperature control for separate areas.',
                Language.POLISH: 'Temperatura zasilania obiegu mieszającego 1.\nSterowana zaworem mieszającym strefy.\nNiezależna regulacja temperatury dla oddzielnych stref.',
                Language.DUTCH: 'Mengcircuit 1 aanvoertemperatuur.\nGeregeld door mengklep voor zone.\nOnafhankelijke temperatuurregeling voor aparte zones.',
                Language.GERMAN: 'Mischkreis 1 Vorlauftemperatur.\nGeregelt durch Mischventil für Zone.\nUnabhängige Temperaturregelung für separate Bereiche.',
                Language.FRENCH: 'Température départ circuit de mélange 1.\nContrôlée par vanne de mélange pour la zone.\nContrôle indépendant pour zones séparées.',
            },
        },
    'mc1_temp_target': {
            'name': {
                Language.ENGLISH: 'Circuit 1 target',
                Language.POLISH: 'Obieg 1 cel',
                Language.DUTCH: 'Groep 1 doel',
                Language.GERMAN: 'Kreis 1 Soll',
                Language.FRENCH: 'Circuit 1 cible',
            },
            'description': {
                Language.ENGLISH: 'Mixing circuit 1 target temperature.\nCalculated based on zone heating curve.\nMixing valve adjusts to achieve this target.',
                Language.POLISH: 'Temperatura docelowa obiegu 1.\nObliczona na podstawie krzywej grzania strefy.\nZawór mieszający reguluje aby osiągnąć cel.',
                Language.DUTCH: 'Mengcircuit 1 doeltemperatuur.\nBerekend op basis van zone stooklijn.\nMengklep regelt om doel te bereiken.',
                Language.GERMAN: 'Mischkreis 1 Solltemperatur.\nBerechnet nach Zonen-Heizkurve.\nMischventil regelt zum Erreichen des Ziels.',
                Language.FRENCH: 'Température cible circuit 1.\nCalculée selon courbe de chauffe de zone.\nVanne de mélange ajuste pour atteindre la cible.',
            },
        },
    'mc2_temp': {
            'name': {
                Language.ENGLISH: 'Circuit 2 temp',
                Language.POLISH: 'Temp obieg 2',
                Language.DUTCH: 'Groep 2 temp',
                Language.GERMAN: 'Kreis 2 Temp.',
                Language.FRENCH: 'Circuit 2 temp',
            },
            'description': {
                Language.ENGLISH: 'Mixing circuit 2 supply temperature.\nControlled by mixing valve for zone.\nIndependent temperature control for separate areas.',
                Language.POLISH: 'Temperatura zasilania obiegu mieszającego 2.\nSterowana zaworem mieszającym strefy.\nNiezależna regulacja temperatury dla oddzielnych stref.',
                Language.DUTCH: 'Mengcircuit 2 aanvoertemperatuur.\nGeregeld door mengklep voor zone.\nOnafhankelijke temperatuurregeling voor aparte zones.',
                Language.GERMAN: 'Mischkreis 2 Vorlauftemperatur.\nGeregelt durch Mischventil für Zone.\nUnabhängige Temperaturregelung für separate Bereiche.',
                Language.FRENCH: 'Température départ circuit de mélange 2.\nContrôlée par vanne de mélange pour la zone.\nContrôle indépendant pour zones séparées.',
            },
        },
    'mc2_temp_target': {
            'name': {
                Language.ENGLISH: 'Circuit 2 target',
                Language.POLISH: 'Obieg 2 cel',
                Language.DUTCH: 'Groep 2 doel',
                Language.GERMAN: 'Kreis 2 Soll',
                Language.FRENCH: 'Circuit 2 cible',
            },
            'description': {
                Language.ENGLISH: 'Mixing circuit 2 target temperature.\nCalculated based on zone heating curve.\nMixing valve adjusts to achieve this target.',
                Language.POLISH: 'Temperatura docelowa obiegu 2.\nObliczona na podstawie krzywej grzania strefy.\nZawór mieszający reguluje aby osiągnąć cel.',
                Language.DUTCH: 'Mengcircuit 2 doeltemperatuur.\nBerekend op basis van zone stooklijn.\nMengklep regelt om doel te bereiken.',
                Language.GERMAN: 'Mischkreis 2 Solltemperatur.\nBerechnet nach Zonen-Heizkurve.\nMischventil regelt zum Erreichen des Ziels.',
                Language.FRENCH: 'Température cible circuit 2.\nCalculée selon courbe de chauffe de zone.\nVanne de mélange ajuste pour atteindre la cible.',
            },
        },

    # =========================================================================
    # GROUP 11: COMPRESSOR (Units 140-144)
    # =========================================================================
    'compressor_freq': {
            'name': {
                Language.ENGLISH: 'Compressor freq',
                Language.POLISH: 'Częst. sprężarki',
                Language.DUTCH: 'Compressor freq',
                Language.GERMAN: 'Verdichterfreq.',
                Language.FRENCH: 'Fréq. compress.',
            },
            'description': {
                Language.ENGLISH: 'Inverter compressor speed.\nHigher frequency = more capacity.\nModulates based on heating demand.\n0 Hz = compressor off.',
                Language.POLISH: 'Prędkość sprężarki inwerterowej.\nWyższa częstotliwość = większa moc.\nModuluje wg zapotrzebowania.\n0 Hz = sprężarka wyłączona.',
                Language.DUTCH: 'Inverter compressorsnelheid.\nHogere frequentie = meer capaciteit.\nModuleert op basis van warmtevraag.\n0 Hz = compressor uit.',
                Language.GERMAN: 'Inverter-Verdichterdrehzahl.\nHöhere Frequenz = mehr Leistung.\nModuliert nach Wärmebedarf.\n0 Hz = Verdichter aus.',
                Language.FRENCH: 'Vitesse du compresseur inverter.\nFréquence plus élevée = plus de capacité.\nModule selon la demande.\n0 Hz = compresseur arrêté.',
            },
        },
    'target_frequency': {
            'name': {
                Language.ENGLISH: 'Compressor target freq',
                Language.POLISH: 'Sprężarka cel częst',
                Language.DUTCH: 'Compressor doel freq',
                Language.GERMAN: 'Verdichter Sollfreq',
                Language.FRENCH: 'Compr. fréq. cible',
            },
            'description': {
                Language.ENGLISH: 'Controller target compressor frequency.\nCompare to actual frequency to see controller tracking.',
                Language.POLISH: 'Docelowa częstotliwość sprężarki.\nPorównaj z rzeczywistą, aby zobaczyć śledzenie sterownika.',
                Language.DUTCH: 'Doelfrequentie compressor van regelaar.\nVergelijk met actueel om tracking te zien.',
                Language.GERMAN: 'Soll-Verdichterfrequenz des Reglers.\nVergleich mit Ist-Frequenz zeigt Regelverhalten.',
                Language.FRENCH: 'Fréquence cible du compresseur.\nComparer à la fréquence réelle pour voir le suivi.',
            },
        },
    'min_frequency': {
            'name': {
                Language.ENGLISH: 'Compressor min freq',
                Language.POLISH: 'Sprężarka min częst',
                Language.DUTCH: 'Compressor min freq',
                Language.GERMAN: 'Verdichter min Freq',
                Language.FRENCH: 'Compr. fréq. min',
            },
            'description': {
                Language.ENGLISH: 'Minimum compressor frequency target.\nActual frequency at this value indicates steady-state operation.',
                Language.POLISH: 'Minimalna docelowa częstotliwość sprężarki.\nRzeczywista częstotliwość równa tej wartości oznacza pracę ustaloną.',
                Language.DUTCH: 'Minimale compressor doelfrequentie.\nActuele frequentie op deze waarde duidt op stabiele werking.',
                Language.GERMAN: 'Minimale Verdichter-Zielfrequenz.\nIst-Frequenz auf diesem Wert zeigt stationären Betrieb an.',
                Language.FRENCH: 'Fréquence cible minimale du compresseur.\nFréquence réelle à cette valeur indique un fonctionnement stable.',
            },
        },
    'max_frequency': {
            'name': {
                Language.ENGLISH: 'Compressor max freq',
                Language.POLISH: 'Sprężarka max częst',
                Language.DUTCH: 'Compressor max freq',
                Language.GERMAN: 'Verdichter max Freq',
                Language.FRENCH: 'Compr. fréq. max',
            },
            'description': {
                Language.ENGLISH: 'Maximum compressor frequency limit.\nSystem capacity ceiling.\nUsed for capacity utilization calculation.',
                Language.POLISH: 'Maksymalna częstotliwość sprężarki.\nGórny limit wydajności systemu.\nUżywana do obliczania wykorzystania mocy.',
                Language.DUTCH: 'Maximale compressorfrequentie.\nSysteemcapaciteitsplafond.\nGebruikt voor capaciteitsbenutting berekening.',
                Language.GERMAN: 'Maximale Verdichterfrequenz.\nSystemkapazitätsgrenze.\nFür Kapazitätsauslastungsberechnung verwendet.',
                Language.FRENCH: 'Fréquence maximale du compresseur.\nPlafond de capacité du système.\nUtilisée pour le calcul d\'utilisation de capacité.',
            },
        },
    'compressor_capacity': {
            'name': {
                Language.ENGLISH: 'Compressor capacity',
                Language.POLISH: 'Obciążenie sprężarki',
                Language.DUTCH: 'Compressor capaciteit',
                Language.GERMAN: 'Verdichterauslastung',
                Language.FRENCH: 'Capacité compresseur',
            },
            'description': {
                Language.ENGLISH: 'Compressor capacity utilization.\nShows current load vs maximum capability.\nSustained >80% may indicate undersizing.\n\n⚡ GATED: Only updates during steady-state operation.',
                Language.POLISH: 'Wykorzystanie mocy sprężarki.\nPokazuje aktualne obciążenie vs maksimum.\nCiągłe >80% może wskazywać niedowymiarowanie.\n\n⚡ BRAMKOWANY: Aktualizuje tylko w stanie ustalonym.',
                Language.DUTCH: 'Compressor capaciteitsbenutting.\nToont huidige belasting vs maximum.\nContinu >80% kan wijzen op onderdimensionering.\n\n⚡ GATED: Alleen updates tijdens stabiele werking.',
                Language.GERMAN: 'Verdichter-Kapazitätsauslastung.\nZeigt aktuelle Last vs Maximum.\nDauerhaft >80% kann auf Unterdimensionierung hindeuten.\n\n⚡ GATED: Aktualisiert nur im stabilen Betrieb.',
                Language.FRENCH: 'Utilisation de la capacité du compresseur.\nAffiche charge actuelle vs maximum.\n>80% soutenu peut indiquer sous-dimensionnement.\n\n⚡ GATED: Mises à jour uniquement en régime établi.',
            },
        },

    # =========================================================================
    # GROUP 12: REFRIGERANT CIRCUIT (Units 160-167)
    # =========================================================================
    'hot_gas_temp': {
            'name': {
                Language.ENGLISH: 'Hot gas temp',
                Language.POLISH: 'Temp gazu gorac',
                Language.DUTCH: 'Heetgas temp',
                Language.GERMAN: 'Heißgastemp.',
                Language.FRENCH: 'Temp. gaz chaud',
            },
            'description': {
                Language.ENGLISH: 'Compressor discharge temperature.\nRises with compression ratio and load.\nProtection limit typically around 100°C.\nHigh values may indicate low refrigerant or high demand.',
                Language.POLISH: 'Temperatura tłoczenia sprężarki.\nRośnie ze stopniem sprężania i obciążeniem.\nLimit ochronny zwykle ok. 100°C.\nWysokie wartości mogą wskazywać niski czynnik lub duże obciążenie.',
                Language.DUTCH: 'Compressor perstemperatuur.\nStijgt met compressieverhouding en belasting.\nBeveiligingslimiet typisch rond 100°C.\nHoge waarden kunnen wijzen op laag koudemiddel of hoge vraag.',
                Language.GERMAN: 'Verdichter-Austrittstemperatur.\nSteigt mit Verdichtungsverhältnis und Last.\nSchutzgrenze typisch bei ca. 100°C.\nHohe Werte können niedrigen Kältemittelstand anzeigen.',
                Language.FRENCH: 'Température de refoulement du compresseur.\nAugmente avec le taux de compression.\nLimite de protection typiquement 100°C.\nValeurs élevées peuvent indiquer manque de réfrigérant.',
            },
        },
    'suction_temp': {
            'name': {
                Language.ENGLISH: 'Suction temp',
                Language.POLISH: 'Temp ssania',
                Language.DUTCH: 'Zuigtemp',
                Language.GERMAN: 'Saugtemp.',
                Language.FRENCH: 'Temp. aspiration',
            },
            'description': {
                Language.ENGLISH: 'Refrigerant temperature entering compressor.\nUsed with evaporator temp to calculate superheat.\nMust be above evaporator temp to prevent liquid slugging.',
                Language.POLISH: 'Temperatura czynnika wchodzącego do sprężarki.\nUżywana z temp. parownika do obliczania przegrzania.\nMusi być wyższa od temp. parownika.',
                Language.DUTCH: 'Koudemiddeltemperatuur naar compressor.\nGebruikt met verdampertemp voor oververhitting.\nMoet boven verdampertemp zijn tegen vloeistofslag.',
                Language.GERMAN: 'Kältemitteltemperatur zum Verdichter.\nMit Verdampfertemp. für Überhitzungsberechnung.\nMuss über Verdampfertemp. liegen gegen Flüssigkeitsschlag.',
                Language.FRENCH: 'Température du réfrigérant entrant au compresseur.\nUtilisée avec temp. évaporateur pour la surchauffe.\nDoit être au-dessus de temp. évaporateur.',
            },
        },
    'discharge_temp': {
            'name': {
                Language.ENGLISH: 'Discharge temp',
                Language.POLISH: 'Temp tłoczenia',
                Language.DUTCH: 'Perstemp',
                Language.GERMAN: 'Druckgastemp.',
                Language.FRENCH: 'Temp. refoulement',
            },
            'description': {
                Language.ENGLISH: 'Refrigerant temperature at discharge line.\nDownstream of compressor, after initial cooling.\nLower than hot gas temp due to heat rejection.',
                Language.POLISH: 'Temperatura czynnika w linii tłocznej.\nZa sprężarką, po wstępnym schłodzeniu.\nNiższa od temp. gazu gorącego.',
                Language.DUTCH: 'Koudemiddeltemperatuur bij persleiding.\nNa compressor, na eerste koeling.\nLager dan heetgastemp door warmteafgifte.',
                Language.GERMAN: 'Kältemitteltemperatur an der Druckleitung.\nNach Verdichter, nach erster Kühlung.\nNiedriger als Heißgastemperatur durch Wärmeabgabe.',
                Language.FRENCH: 'Température du réfrigérant à la ligne de refoulement.\nEn aval du compresseur, après refroidissement initial.\nPlus basse que temp. gaz chaud.',
            },
        },
    'evaporating_temp': {
            'name': {
                Language.ENGLISH: 'Evaporating temp',
                Language.POLISH: 'Temp parowania',
                Language.DUTCH: 'Verdampingstemp',
                Language.GERMAN: 'Verdampfungstemp.',
                Language.FRENCH: 'Temp. évaporation',
            },
            'description': {
                Language.ENGLISH: 'Refrigerant evaporation point (dew point calculation).\nIndicates source-side heat transfer.\nLow pressure corresponds to this saturation temp.\n\n⚡ GATED: Only updates during steady-state operation.\nStale readings when idle would corrupt operating averages.',
                Language.POLISH: 'Punkt parowania czynnika chłodniczego (obliczenie punktu rosy).\nWskazuje transfer ciepła po stronie źródłowej.\nNiskie ciśnienie odpowiada tej temp. nasycenia.\n\n⚡ BRAMKOWANY: Aktualizuje tylko w stanie ustalonym.\nNieaktualne odczyty podczas bezczynności zafałszowałyby średnie.',
                Language.DUTCH: 'Verdampingspunt van koudemiddel (dauwpuntberekening).\nIndicatie van warmteoverdracht bronzijde.\nLage druk correspondeert met deze verzadigingstemp.\n\n⚡ GATED: Alleen updates tijdens stabiele werking.\nVerouderde metingen bij rust zouden gemiddelden verstoren.',
                Language.GERMAN: 'Verdampfungspunkt des Kältemittels (Taupunktberechnung).\nZeigt Wärmeübertragung quellenseitig.\nNiederdruck entspricht dieser Sättigungstemperatur.\n\n⚡ GATED: Aktualisiert nur im stabilen Betrieb.\nVeraltete Messwerte würden Durchschnitte verfälschen.',
                Language.FRENCH: 'Point d\'évaporation du réfrigérant (calcul point de rosée).\nIndique le transfert de chaleur côté source.\nBasse pression correspond à cette temp. de saturation.\n\n⚡ GATED: Mises à jour uniquement en régime établi.\nLectures obsolètes fausseraient les moyennes.',
            },
        },
    'liquid_line_temp': {
            'name': {
                Language.ENGLISH: 'Liquid line temp',
                Language.POLISH: 'Temp linii cieczy',
                Language.DUTCH: 'Vloeistoflijntemp',
                Language.GERMAN: 'Flüssigkeitstemp.',
                Language.FRENCH: 'Temp. ligne liquide',
            },
            'description': {
                Language.ENGLISH: 'Liquid refrigerant temperature before expansion valve (TFL).\nMeasured between condenser outlet and EEV inlet.\n\n⚡ GATED: Only updates during steady-state operation.\nStale readings when idle would corrupt operating averages.',
                Language.POLISH: 'Temperatura ciekłego czynnika przed zaworem rozprężnym (TFL).\nMierzona między wyjściem skraplacza a wlotem EEV.\n\n⚡ BRAMKOWANY: Aktualizuje tylko w stanie ustalonym.\nNieaktualne odczyty podczas bezczynności zafałszowałyby średnie.',
                Language.DUTCH: 'Vloeibaar koudemiddeltemperatuur vóór expansieventiel (TFL).\nGemeten tussen condensoruitgang en EEV-inlaat.\n\n⚡ GATED: Alleen updates tijdens stabiele werking.\nVerouderde metingen bij rust zouden gemiddelden verstoren.',
                Language.GERMAN: 'Flüssiges Kältemittel vor Expansionsventil (TFL).\nGemessen zwischen Kondensatorausgang und EEV-Einlass.\n\n⚡ GATED: Aktualisiert nur im stabilen Betrieb.\nVeraltete Messwerte würden Durchschnitte verfälschen.',
                Language.FRENCH: 'Température du réfrigérant liquide avant détendeur (TFL).\nMesurée entre sortie condenseur et entrée EEV.\n\n⚡ GATED: Mises à jour uniquement en régime établi.\nLectures obsolètes fausseraient les moyennes.',
            },
        },
    'superheat': {
            'name': {
                Language.ENGLISH: 'Superheat',
                Language.POLISH: 'Przegrzanie',
                Language.DUTCH: 'Oververhitting',
                Language.GERMAN: 'Überhitzung',
                Language.FRENCH: 'Surchauffe',
            },
            'description': {
                Language.ENGLISH: 'Temperature above refrigerant evaporation point.\nExpansion valve control parameter.\nPrevents liquid entering compressor.\n\n⚡ GATED: Only updates during steady-state operation.\nStale readings when idle would corrupt operating averages.',
                Language.POLISH: 'Temperatura powyżej punktu parowania czynnika.\nParametr sterowania zaworem rozprężnym.\nZapobiega przedostawaniu się cieczy do sprężarki.\n\n⚡ BRAMKOWANY: Aktualizuje tylko w stanie ustalonym.\nNieaktualne odczyty podczas bezczynności zafałszowałyby średnie.',
                Language.DUTCH: 'Temperatuur boven verdampingspunt.\nRegelparameter expansieventiel.\nVoorkomt vloeistof in compressor.\n\n⚡ GATED: Alleen updates tijdens stabiele werking.\nVerouderde metingen bij rust zouden gemiddelden verstoren.',
                Language.GERMAN: 'Temperatur über Verdampfungspunkt.\nRegelparameter für Expansionsventil.\nVerhindert Flüssigkeit im Verdichter.\n\n⚡ GATED: Aktualisiert nur im stabilen Betrieb.\nVeraltete Messwerte würden Durchschnitte verfälschen.',
                Language.FRENCH: 'Température au-dessus du point d\'évaporation.\nParamètre de contrôle du détendeur.\nÉvite le liquide dans le compresseur.\n\n⚡ GATED: Mises à jour uniquement en régime établi.\nLectures obsolètes fausseraient les moyennes.',
            },
        },
    'high_pressure': {
            'name': {
                Language.ENGLISH: 'Pressure high',
                Language.POLISH: 'Ciśnienie wys',
                Language.DUTCH: 'Hogedruk',
                Language.GERMAN: 'Hochdruck',
                Language.FRENCH: 'Haute pression',
            },
            'description': {
                Language.ENGLISH: 'Refrigerant pressure at condenser (hot side).\nRises with compressor load and heating demand.\nReflects heat transfer to heating circuit.\n\n⚡ GATED: Only updates during steady-state operation.\nEquilibrates to ambient when idle - not operationally meaningful.',
                Language.POLISH: 'Ciśnienie czynnika w skraplaczu (strona gorąca).\nRośnie z obciążeniem sprężarki i zapotrzebowaniem.\nOdzwierciedla transfer ciepła do obiegu grzewczego.\n\n⚡ BRAMKOWANY: Aktualizuje tylko w stanie ustalonym.\nWyrównuje się do otoczenia gdy bezczynny.',
                Language.DUTCH: 'Koudemiddeldruk bij condensor (hete zijde).\nStijgt met compressorbelasting en warmtevraag.\nWeerspiegelt warmteoverdracht naar cv-circuit.\n\n⚡ GATED: Alleen updates tijdens stabiele werking.\nEvenwijcht met omgeving bij rust - niet operationeel relevant.',
                Language.GERMAN: 'Kältemitteldruck am Kondensator (Hochdruckseite).\nSteigt mit Verdichterlast und Wärmebedarf.\nZeigt Wärmeübertragung zum Heizkreis.\n\n⚡ GATED: Aktualisiert nur im stabilen Betrieb.\nGleicht sich im Stillstand an Umgebung an.',
                Language.FRENCH: 'Pression du réfrigérant au condenseur (côté chaud).\nAugmente avec la charge et la demande.\nReflète le transfert de chaleur vers le circuit.\n\n⚡ GATED: Mises à jour uniquement en régime établi.\nS\'équilibre avec l\'ambiant au repos.',
            },
        },
    'low_pressure': {
            'name': {
                Language.ENGLISH: 'Pressure low',
                Language.POLISH: 'Ciśnienie nis',
                Language.DUTCH: 'Lagedruk',
                Language.GERMAN: 'Niederdruck',
                Language.FRENCH: 'Basse pression',
            },
            'description': {
                Language.ENGLISH: 'Refrigerant pressure at evaporator (cold side).\nRelates to source temperature (ground/air).\nIndicates heat absorption from source.\n\n⚡ GATED: Only updates during steady-state operation.\nEquilibrates to ambient when idle - not operationally meaningful.',
                Language.POLISH: 'Ciśnienie czynnika w parowniku (strona zimna).\nZwiązane z temperaturą źródła (grunt/powietrze).\nWskazuje absorpcję ciepła ze źródła.\n\n⚡ BRAMKOWANY: Aktualizuje tylko w stanie ustalonym.\nWyrównuje się do otoczenia gdy bezczynny.',
                Language.DUTCH: 'Koudemiddeldruk bij verdamper (koude zijde).\nGerelateerd aan brontemperatuur (bodem/lucht).\nIndicatie van warmteopname uit bron.\n\n⚡ GATED: Alleen updates tijdens stabiele werking.\nEvenwijcht met omgeving bij rust - niet operationeel relevant.',
                Language.GERMAN: 'Kältemitteldruck am Verdampfer (Niederdruckseite).\nAbhängig von Quellentemperatur (Sole/Luft).\nZeigt Wärmeaufnahme aus der Quelle.\n\n⚡ GATED: Aktualisiert nur im stabilen Betrieb.\nGleicht sich im Stillstand an Umgebung an.',
                Language.FRENCH: 'Pression du réfrigérant à l\'évaporateur (côté froid).\nLiée à la température source (sol/air).\nIndique l\'absorption de chaleur.\n\n⚡ GATED: Mises à jour uniquement en régime établi.\nS\'équilibre avec l\'ambiant au repos.',
            },
        },

    'condensing_temp': {
            'name': {
                Language.ENGLISH: 'Condensing temp',
                Language.DUTCH: 'Condensatietemp',
                Language.GERMAN: 'Kondensationstemp.',
                Language.FRENCH: 'Temp. condensation',
                Language.POLISH: 'Temp skraplania',
            },
            'description': {
                Language.ENGLISH: 'Refrigerant condensation temperature (hot side).\nDerived from firmware calculation at condenser.\nUsed with liquid line temp to calculate subcooling.\n\n⚡ GATED: Only updates during steady-state operation.',
            },
    },
    'subcooling': {
            'name': {
                Language.ENGLISH: 'Subcooling',
                Language.DUTCH: 'Onderkoeling',
                Language.GERMAN: 'Unterkühlung',
                Language.FRENCH: 'Sous-refroidissement',
                Language.POLISH: 'Dochłodzenie',
            },
            'description': {
                Language.ENGLISH: 'Difference between condensing temp and liquid line temp.\nIndicates refrigerant charge health.\nTrending changes may signal refrigerant loss or restriction.\n\n⚡ GATED: Only updates during steady-state operation.',
            },
    },
    'condensing_pressure': {
            'name': {
                Language.ENGLISH: 'Condensing pressure',
                Language.DUTCH: 'Condensatiedruk',
                Language.GERMAN: 'Kondensationsdruck',
                Language.FRENCH: 'Pression condensation',
                Language.POLISH: 'Ciśnienie skraplania',
            },
            'description': {
                Language.ENGLISH: 'Condensing pressure from firmware calculation.\nCompanion to high pressure (LIN bus transducer).\n\n⚡ GATED: Only updates during steady-state operation.\nEquilibrates to ambient when idle.',
            },
    },
    'cooling_release_timer': {
            'name': {
                Language.ENGLISH: 'Cooling release',
                Language.DUTCH: 'Vrijgave koeling',
                Language.GERMAN: 'Kühlfreigabe',
                Language.FRENCH: 'Libération refroid.',
                Language.POLISH: 'Zwolnienie chłodz.',
            },
            'description': {
                Language.ENGLISH: 'Countdown timer showing when cooling mode will be permitted.\nDisplays remaining time in minutes.',
            },
    },

    # =========================================================================
    # GROUP 13: STATISTICS & COUNTERS (Units 180-185)
    # =========================================================================
    'compressor_runtime': {
            'name': {
                Language.ENGLISH: 'Compressor hours',
                Language.POLISH: 'Godz. sprężarki',
                Language.DUTCH: 'Compressor uren',
                Language.GERMAN: 'Verdichterstd.',
                Language.FRENCH: 'Heures compress.',
            },
            'description': {
                Language.ENGLISH: 'Lifetime compressor operating hours.\nUseful for maintenance scheduling.\nDivide by starts to get average cycle length.',
                Language.POLISH: 'Całkowity czas pracy sprężarki.\nPrzydatne do planowania konserwacji.\nPodziel przez starty aby uzyskać średnią długość cyklu.',
                Language.DUTCH: 'Totale bedrijfsuren compressor.\nNuttig voor onderhoudsplanning.\nDeel door starts voor gemiddelde cycluslengte.',
                Language.GERMAN: 'Betriebsstunden Verdichter gesamt.\nNützlich für Wartungsplanung.\nDurch Starts teilen für durchschnittliche Zykluslänge.',
                Language.FRENCH: 'Heures de fonctionnement du compresseur.\nUtile pour la planification de maintenance.\nDiviser par démarrages pour durée moyenne de cycle.',
            },
        },
    'compressor_starts': {
            'name': {
                Language.ENGLISH: 'Compressor starts',
                Language.POLISH: 'Starty sprężarki',
                Language.DUTCH: 'Compressor starts',
                Language.GERMAN: 'Verdichterstarts',
                Language.FRENCH: 'Démarrages compr.',
            },
            'description': {
                Language.ENGLISH: 'Total compressor start count.\nIndicates cycling behavior and wear.\nHigh starts/hour suggests oversizing or short-cycling.',
                Language.POLISH: 'Całkowita liczba startów sprężarki.\nWskazuje zachowanie cykliczne i zużycie.\nDużo startów/godz. sugeruje przewymiarowanie.',
                Language.DUTCH: 'Totaal aantal compressorstarts.\nIndicatie van cyclusgedrag en slijtage.\nVeel starts/uur suggereert oversizing.',
                Language.GERMAN: 'Anzahl Verdichterstarts gesamt.\nZeigt Taktverhalten und Verschleiß.\nViele Starts/Std. deuten auf Überdimensionierung.',
                Language.FRENCH: 'Nombre total de démarrages compresseur.\nIndique le comportement cyclique et l\'usure.\nBeaucoup de démarrages/h suggère surdimensionnement.',
            },
        },
    'last_cycle': {
            'name': {
                Language.ENGLISH: 'Compressor last cycle',
                Language.POLISH: 'Sprężarka ost. cykl',
                Language.DUTCH: 'Compressor laatste cyclus',
                Language.GERMAN: 'Verdichter letzter Zyklus',
                Language.FRENCH: 'Compr. dernier cycle',
            },
            'description': {
                Language.ENGLISH: 'Duration of last completed compressor cycle.\nLong cycles (>30 min) indicate good modulation.\nShort cycles (<10 min) may indicate issues.\n\n📊 SPARSE: Updates only when cycles complete.',
                Language.POLISH: 'Czas trwania ostatniego cyklu sprężarki.\nDługie cykle (>30 min) oznaczają dobrą modulację.\nKrótkie cykle (<10 min) mogą wskazywać problemy.\n\n📊 RZADKI: Aktualizuje tylko po zakończeniu cyklu.',
                Language.DUTCH: 'Duur van laatste voltooide compressorcyclus.\nLange cycli (>30 min) wijzen op goede modulatie.\nKorte cycli (<10 min) kunnen problemen aangeven.\n\n📊 SPARSE: Updates alleen bij cyclusvoltooiing.',
                Language.GERMAN: 'Dauer des letzten Verdichterzyklus.\nLange Zyklen (>30 min) zeigen gute Modulation.\nKurze Zyklen (<10 min) können Probleme anzeigen.\n\n📊 SPARSE: Aktualisiert nur bei Zyklusende.',
                Language.FRENCH: 'Durée du dernier cycle compresseur terminé.\nLongs cycles (>30 min) indiquent bonne modulation.\nCycles courts (<10 min) peuvent indiquer des problèmes.\n\n📊 SPARSE: Mises à jour uniquement à la fin des cycles.',
            },
        },
    'heating_runtime': {
            'name': {
                Language.ENGLISH: 'Heating runtime',
                Language.POLISH: 'Czas pracy grzania',
                Language.DUTCH: 'Verwarmingstijd',
                Language.GERMAN: 'Heizlaufzeit',
                Language.FRENCH: 'Durée chauffage',
            },
            'description': {
                Language.ENGLISH: 'Total operating hours in heating mode.\nUseful for seasonal efficiency tracking.',
                Language.POLISH: 'Całkowity czas pracy w trybie grzania.\nPrzydatny do śledzenia wydajności sezonowej.',
                Language.DUTCH: 'Totale bedrijfsuren in verwarmingsmodus.\nNuttig voor seizoensefficiëntie tracking.',
                Language.GERMAN: 'Gesamtbetriebsstunden im Heizbetrieb.\nNützlich für saisonale Effizienzüberwachung.',
                Language.FRENCH: 'Heures totales de fonctionnement en mode chauffage.\nUtile pour le suivi de l\'efficacité saisonnière.',
            },
        },
    'dhw_runtime': {
            'name': {
                Language.ENGLISH: 'DHW runtime',
                Language.POLISH: 'Czas pracy CWU',
                Language.DUTCH: 'Tapwatertijd',
                Language.GERMAN: 'Warmwasserlaufzeit',
                Language.FRENCH: 'Durée ECS',
            },
            'description': {
                Language.ENGLISH: 'Total operating hours in hot water mode.\nUseful for DHW efficiency analysis.',
                Language.POLISH: 'Całkowity czas pracy w trybie CWU.\nPrzydatny do analizy wydajności CWU.',
                Language.DUTCH: 'Totale bedrijfsuren in tapwatermodus.\nNuttig voor tapwater efficiëntie analyse.',
                Language.GERMAN: 'Gesamtbetriebsstunden im Warmwasserbetrieb.\nNützlich für Warmwasser-Effizienzanalyse.',
                Language.FRENCH: 'Heures totales de fonctionnement en mode ECS.\nUtile pour l\'analyse de l\'efficacité ECS.',
            },
        },
    'cooling_runtime': {
            'name': {
                Language.ENGLISH: 'Cooling runtime',
                Language.POLISH: 'Czas pracy chłodzenia',
                Language.DUTCH: 'Koeltijd',
                Language.GERMAN: 'Kühllaufzeit',
                Language.FRENCH: 'Durée refroidissement',
            },
            'description': {
                Language.ENGLISH: 'Total operating hours in passive cooling mode.\nHeat rejected to ground without compressor.',
                Language.POLISH: 'Całkowity czas pracy w trybie chłodzenia pasywnego.\nCiepło oddawane do gruntu bez sprężarki.',
                Language.DUTCH: 'Totale bedrijfsuren in passieve koelmodus.\nWarmte afgevoerd naar bodem zonder compressor.',
                Language.GERMAN: 'Gesamtbetriebsstunden im passiven Kühlbetrieb.\nWärmeabgabe an Erdreich ohne Verdichter.',
                Language.FRENCH: 'Heures totales en mode refroidissement passif.\nChaleur rejetée au sol sans compresseur.',
            },
        },

    # =========================================================================
    # GROUP 14: DIAGNOSTICS (Units 200-201)
    # =========================================================================
    'error_count': {
            'name': {
                Language.ENGLISH: 'Error count',
                Language.POLISH: 'Liczba błędów',
                Language.DUTCH: 'Foutenteller',
                Language.GERMAN: 'Fehleranzahl',
                Language.FRENCH: 'Nombre d\'erreurs',
            },
            'description': {
                Language.ENGLISH: 'Number of errors stored in memory.\nQuick health indicator.\nCheck heat pump logs if count increases.',
                Language.POLISH: 'Liczba błędów zapisanych w pamięci.\nSzybki wskaźnik stanu.\nSprawdź logi pompy ciepła, jeśli liczba rośnie.',
                Language.DUTCH: 'Aantal fouten in geheugen.\nSnelle gezondheidscheck.\nControleer logs als aantal stijgt.',
                Language.GERMAN: 'Anzahl gespeicherter Fehler.\nSchneller Gesundheitscheck.\nLogs prüfen wenn Anzahl steigt.',
                Language.FRENCH: 'Nombre d\'erreurs en mémoire.\nIndicateur de santé rapide.\nVérifier les logs si le nombre augmente.',
            },
        },
    'cooling_permitted': {
            'name': {
                Language.ENGLISH: 'Cooling permitted',
                Language.POLISH: 'Chłodzenie dozwolone',
                Language.DUTCH: 'Koeling vrijgegeven',
                Language.GERMAN: 'Kühlung freigegeben',
                Language.FRENCH: 'Refroid. autorisé',
            },
            'description': {
                Language.ENGLISH: 'Indicates if passive cooling is currently permitted.\nBased on outdoor temperature and settings.\nRead-only status indicator.',
                Language.POLISH: 'Wskazuje, czy chłodzenie pasywne jest aktualnie dozwolone.\nNa podstawie temperatury zewnętrznej i ustawień.\nWskaźnik statusu tylko do odczytu.',
                Language.DUTCH: 'Geeft aan of passieve koeling is toegestaan.\nGebaseerd op buitentemperatuur en instellingen.\nAlleen-lezen statusindicator.',
                Language.GERMAN: 'Zeigt ob passive Kühlung derzeit erlaubt ist.\nBasiert auf Außentemperatur und Einstellungen.\nNur-Lesen Statusanzeige.',
                Language.FRENCH: 'Indique si le refroidissement passif est autorisé.\nBasé sur la température extérieure et les paramètres.\nIndicateur d\'état en lecture seule.',
            },
        },
}

# =============================================================================
# SELECTOR SWITCH OPTIONS
# =============================================================================
# Translations for selector switch level names
# =============================================================================

SELECTOR_OPTIONS: Dict[str, Dict[Language, str]] = {
    'Automatic': {
        Language.ENGLISH: 'Automatic',
        Language.POLISH: 'Automatyczny',
        Language.DUTCH: 'Automatisch',
        Language.GERMAN: 'Automatisch',
        Language.FRENCH: 'Automatique',
    },
    '2nd heat source': {
        Language.ENGLISH: '2nd heat source',
        Language.POLISH: 'II źr. ciepła',
        Language.DUTCH: '2e warmtebron',
        Language.GERMAN: '2. Wärmequelle',
        Language.FRENCH: '2e source',
    },
    'Party': {
        Language.ENGLISH: 'Party',
        Language.POLISH: 'Impreza',
        Language.DUTCH: 'Feest',
        Language.GERMAN: 'Party',
        Language.FRENCH: 'Fête',
    },
    'Holidays': {
        Language.ENGLISH: 'Holidays',
        Language.POLISH: 'Urlop',
        Language.DUTCH: 'Vakantie',
        Language.GERMAN: 'Urlaub',
        Language.FRENCH: 'Vacances',
    },
    'Off': {
        Language.ENGLISH: 'Off',
        Language.POLISH: 'Wył',
        Language.DUTCH: 'Uit',
        Language.GERMAN: 'Aus',
        Language.FRENCH: 'Arrêt',
    },
    'Normal': {
        Language.ENGLISH: 'Normal',
        Language.POLISH: 'Normalny',
        Language.DUTCH: 'Normaal',
        Language.GERMAN: 'Normal',
        Language.FRENCH: 'Normal',
    },
    'Luxury': {
        Language.ENGLISH: 'Luxury',
        Language.POLISH: 'Luksusowy',
        Language.DUTCH: 'Luxe',
        Language.GERMAN: 'Luxus',
        Language.FRENCH: 'Luxe',
    },
}


# =============================================================================
# WORKING MODE STATUS STRINGS
# =============================================================================
# Text displayed in the Working Mode text device
# =============================================================================

WORKING_MODE_STATUSES: Dict[str, Dict[Language, str]] = {
    'Heating': {
        Language.ENGLISH: 'Heating',
        Language.POLISH: 'Ogrzewanie',
        Language.DUTCH: 'Verwarmen',
        Language.GERMAN: 'Heizen',
        Language.FRENCH: 'Chauffage',
    },
    'DHW': {
        Language.ENGLISH: 'DHW',
        Language.POLISH: 'CWU',
        Language.DUTCH: 'Tapwater',
        Language.GERMAN: 'Warmwasser',
        Language.FRENCH: 'ECS',
    },
    'Swimming pool': {
        Language.ENGLISH: 'Pool / PV mode',
        Language.POLISH: 'Basen / PV',
        Language.DUTCH: 'Zwembad / PV',
        Language.GERMAN: 'Pool / PV',
        Language.FRENCH: 'Piscine / PV',
    },
    'EVU': {
        Language.ENGLISH: 'EVU',
        Language.POLISH: 'EVU',
        Language.DUTCH: 'EVU',
        Language.GERMAN: 'EVU',
        Language.FRENCH: 'EVU',
    },
    'Defrost': {
        Language.ENGLISH: 'Defrost',
        Language.POLISH: 'Odszranianie',
        Language.DUTCH: 'Ontdooien',
        Language.GERMAN: 'Abtauen',
        Language.FRENCH: 'Dégivrage',
    },
    'No requirement': {
        Language.ENGLISH: 'No requirement',
        Language.POLISH: 'Brak zapotrzeb.',
        Language.DUTCH: 'Geen vraag',
        Language.GERMAN: 'Kein Bedarf',
        Language.FRENCH: 'Pas de demande',
    },
    'Heating ext.': {
        Language.ENGLISH: 'Heating ext.',
        Language.POLISH: 'Ogrzewanie zew.',
        Language.DUTCH: 'Verw. ext.',
        Language.GERMAN: 'Heizen ext.',
        Language.FRENCH: 'Chauff. ext.',
    },
    'Cooling': {
        Language.ENGLISH: 'Cooling',
        Language.POLISH: 'Chłodzenie',
        Language.DUTCH: 'Koeling',
        Language.GERMAN: 'Kühlung',
        Language.FRENCH: 'Refroidissement',
    },
    'Idle': {
        Language.ENGLISH: 'Idle',
        Language.POLISH: 'Bezczynny',
        Language.DUTCH: 'Inactief',
        Language.GERMAN: 'Inaktiv',
        Language.FRENCH: 'Repos',
    },
}