"""Translation manager for the plugin.

Extracted from plugin.py so it can be imported without pulling in DomoticzEx.
Logs through context.logger (bridged to the live DebugLogger in plugin.onStart)
rather than plugin.py's module-level logger.
"""

from typing import Dict, List

import context
from context import DebugLevel
from translations import Language


class TranslationManager:
    """Manages translations for the plugin.

    Uses spec_id as the primary key for device translations, eliminating the
    need for separate name_key and description key mappings.
    """

    # Maps current spec_id → old spec_id for devices that were renamed.
    # Used to detect old translated names so they can be auto-renamed.
    _RENAMED_SPECS = {
        # 164: calc[233] is condensing temp (was mislabeled liquid line)
        "condensing_temp": "liquid_line_temp",
        # 162: calc[177] is compressor heating, not discharge
        "compressor_heating_temp": "discharge_temp",
        # 172: signed ΔT, not an always-positive "approach"
        "condensing_supply_delta": "condenser_approach",
    }

    LANGUAGE_MAP = {
        "0": Language.ENGLISH,
        "1": Language.POLISH,
        "2": Language.DUTCH,
        "3": Language.GERMAN,
        "4": Language.FRENCH,
    }

    def __init__(self):
        self._device_translations: Dict[str, Dict] = {}
        self._selector_options: Dict[str, Dict[Language, str]] = {}
        self._working_mode_statuses: Dict[str, Dict[Language, str]] = {}
        self._current_language = Language.ENGLISH

    def set_language(self, language_code: str) -> None:
        """Set current language from plugin parameter."""
        if language_code not in self.LANGUAGE_MAP:
            context.logger.warning(
                f"Unknown language code '{language_code}', falling back to English"
            )
            language = Language.ENGLISH
        else:
            language = self.LANGUAGE_MAP[language_code]

        self._current_language = language
        context.logger.log(f"Language set to: {language.name}", DebugLevel.BASIC)

    def load_translations(
        self, device_translations: Dict, selector_options: Dict, working_mode_statuses: Dict
    ) -> None:
        """Load translations from data dictionaries."""
        self._device_translations = device_translations
        self._selector_options = selector_options
        self._working_mode_statuses = working_mode_statuses

    def get_device_name(self, spec_id: str) -> str:
        """Get device name for current language by spec_id."""
        if spec_id not in self._device_translations:
            return spec_id

        names = self._device_translations[spec_id].get("name", {})
        return names.get(self._current_language, names.get(Language.ENGLISH, spec_id))

    def get_device_name_for_language(self, spec_id: str, language: Language) -> str:
        """Get device name for a specific language by spec_id."""
        if spec_id not in self._device_translations:
            return spec_id

        names = self._device_translations[spec_id].get("name", {})
        return names.get(language, names.get(Language.ENGLISH, spec_id))

    def get_device_description(self, spec_id: str) -> str:
        """Get device description for current language by spec_id."""
        if spec_id not in self._device_translations:
            return ""

        descs = self._device_translations[spec_id].get("description", {})
        return descs.get(self._current_language, descs.get(Language.ENGLISH, ""))

    def get_device_description_for_language(self, spec_id: str, language: Language) -> str:
        """Get device description for a specific language by spec_id."""
        if spec_id not in self._device_translations:
            return ""

        descs = self._device_translations[spec_id].get("description", {})
        return descs.get(language, descs.get(Language.ENGLISH, ""))

    def is_known_device_name(self, name: str, spec_id: str) -> bool:
        """Check if name matches any known translation for the spec_id.

        Used to determine if a device name can be safely renamed (it's a known
        translation) vs user-customized (should be left alone).
        Also checks old spec_id from _RENAMED_SPECS for rename transitions.
        """
        if spec_id in self._device_translations:
            names = self._device_translations[spec_id].get("name", {})
            if name in names.values():
                return True

        old_spec_id = self._RENAMED_SPECS.get(spec_id)
        if old_spec_id and old_spec_id in self._device_translations:
            old_names = self._device_translations[old_spec_id].get("name", {})
            if name in old_names.values():
                return True

        return False

    def is_known_description(self, description: str, spec_id: str) -> bool:
        """Check if description matches any known translation for spec_id.

        Also checks old spec_id from _RENAMED_SPECS for rename transitions.
        """
        if spec_id in self._device_translations:
            descs = self._device_translations[spec_id].get("description", {})
            if description in descs.values():
                return True

        old_spec_id = self._RENAMED_SPECS.get(spec_id)
        if old_spec_id and old_spec_id in self._device_translations:
            old_descs = self._device_translations[old_spec_id].get("description", {})
            if description in old_descs.values():
                return True

        return False

    def get_selector_option(self, option_key: str) -> str:
        """Get selector option text for current language."""
        if option_key not in self._selector_options:
            return option_key

        options = self._selector_options[option_key]
        return options.get(self._current_language, options.get(Language.ENGLISH, option_key))

    def get_selector_option_for_language(self, option_key: str, language: Language) -> str:
        """Get selector option text for a specific language."""
        if option_key not in self._selector_options:
            return option_key

        options = self._selector_options[option_key]
        return options.get(language, options.get(Language.ENGLISH, option_key))

    def translate_selector_options(self, options: List[str]) -> str:
        """Translate selector switch options and join with pipes."""
        return "|".join(self.get_selector_option(opt) for opt in options)

    def is_known_selector_option(self, text: str, option_key: str) -> bool:
        """Check if text matches any known translation for selector option."""
        if option_key not in self._selector_options:
            return False

        options = self._selector_options[option_key]
        return text in options.values()

    def get_working_mode_status(self, status_key: str) -> str:
        """Get working mode status text for current language."""
        if status_key not in self._working_mode_statuses:
            return status_key

        statuses = self._working_mode_statuses[status_key]
        return statuses.get(self._current_language, statuses.get(Language.ENGLISH, status_key))
