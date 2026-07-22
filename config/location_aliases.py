from targets.loader import load_target

_cfg = load_target("location_aliases") or {}

LOCATION_ALIASES = _cfg


def matches_location(location: str, company: str) -> bool:
    if not location:
        return False
    aliases = LOCATION_ALIASES.get(company, LOCATION_ALIASES.get("default", []))
    location_lower = location.lower()
    return any(alias.lower() in location_lower for alias in aliases)
