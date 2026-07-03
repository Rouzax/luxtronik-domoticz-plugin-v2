from name_ownership import claim, is_owned, key


def test_key_qualifies_by_device_id():
    assert key("devA", 5) == "devA:5"
    assert key("devA", 5) != key("devB", 5)


def test_provenance_owned_when_current_matches_stored():
    auto = {"d:1": {"name": "HP - Working mode"}}
    # heuristic_result is ignored when an entry exists
    assert is_owned(auto, "d:1", "name", "HP - Working mode", False, False) is True


def test_provenance_not_owned_when_user_renamed():
    auto = {"d:1": {"name": "HP - Working mode"}}
    assert is_owned(auto, "d:1", "name", "My Custom Name", True, False) is False


def test_cross_language_footgun_fixed():
    # plugin owns the English name; user renamed to the DUTCH translation text.
    # The old all-languages heuristic would say "known" and clobber it.
    # Provenance: current != stored -> NOT owned -> preserved.
    auto = {"d:1": {"name": "HP - Working mode"}}
    assert is_owned(auto, "d:1", "name", "HP - Bedrijfsmodus", True, False) is False


def test_no_entry_not_owned_when_not_migrating():
    assert is_owned({}, "d:1", "name", "anything", True, False) is False


def test_no_entry_owned_only_when_migrating_and_heuristic():
    assert is_owned({}, "d:1", "name", "HP - Working mode", True, True) is True
    assert is_owned({}, "d:1", "name", "user name", False, True) is False


def test_partial_entry_uses_migration_logic_for_unclaimed_attr():
    # The key has a claimed name but no claimed description. For the description
    # attr there is no provenance, so it falls back to the bootstrap rule exactly
    # as if the key were absent (this pins the `attr in entry` guard).
    auto = {"d:1": {"name": "HP - Working mode"}}
    # not migrating -> not owned regardless of the heuristic
    assert is_owned(auto, "d:1", "description", "anything", True, False) is False
    # migrating + heuristic matched -> owned (bootstrap claims the sibling attr)
    assert is_owned(auto, "d:1", "description", "Some description", True, True) is True
    # migrating but heuristic did not match -> not owned
    assert is_owned(auto, "d:1", "description", "user description", False, True) is False


def test_claim_records_per_attr_and_key():
    auto = {}
    claim(auto, "d:1", "name", "N")
    claim(auto, "d:1", "description", "D")
    claim(auto, "d:2", "options", "O")
    assert auto == {"d:1": {"name": "N", "description": "D"}, "d:2": {"options": "O"}}
