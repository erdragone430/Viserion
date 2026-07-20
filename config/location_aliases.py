LOCATION_ALIASES = {
    "isar_aerospace": ["Ottobrunn", "Munich", "München"],
    "default": ["Munich", "München"],
}


def matches_location(location: str, company: str) -> bool:
    if not location:
        return False
    aliases = LOCATION_ALIASES.get(company, LOCATION_ALIASES["default"])
    location_lower = location.lower()
    return any(alias.lower() in location_lower for alias in aliases)
