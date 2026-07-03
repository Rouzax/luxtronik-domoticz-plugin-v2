"""Provenance-based ownership of plugin-authored device metadata.

Pure logic over a plain `auto_names` dict (keyed by device_id:unit_id -> per-attr
last-written value). No Domoticz/translation imports: callers pass a precomputed
heuristic result used only during the one-time migration bootstrap.
"""


def key(device_id: str, unit_id: int) -> str:
    return f"{device_id}:{unit_id}"


def is_owned(
    auto_names: dict, k: str, attr: str, current: str, heuristic_result: bool, migrating: bool
) -> bool:
    """Does the plugin own `current` for (key, attr)?

    - Entry recorded -> pure provenance: owned iff current equals what we wrote.
    - No entry + migrating + heuristic matched -> owned (bootstrap claims
      plugin-authored values written by an older build).
    - Otherwise -> not owned (leave user-customized values alone).
    """
    entry = auto_names.get(k)
    if entry is not None and attr in entry:
        return current == entry[attr]
    return bool(migrating and heuristic_result)


def claim(auto_names: dict, k: str, attr: str, value: str) -> None:
    auto_names.setdefault(k, {})[attr] = value
