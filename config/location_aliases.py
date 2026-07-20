LOCATION_ALIASES = {
    "isar_aerospace": ["Ottobrunn", "Munich", "München"],
    # Airbus Defence and Space's Munich-area presence is Ottobrunn/Taufkirchen,
    # not literally "Munich" - same lesson as Isar Aerospace and SAP's Garching.
    "airbus_ds": ["Ottobrunn", "Taufkirchen", "Munich", "München"],
    # IBM's own listings spell it "Muenchen" (ASCII transliteration), which
    # doesn't substring-match "München" - confirmed live, not guessed.
    "ibm": ["Muenchen", "Munich", "München"],
    "default": ["Munich", "München"],
}


def matches_location(location: str, company: str) -> bool:
    if not location:
        return False
    aliases = LOCATION_ALIASES.get(company, LOCATION_ALIASES["default"])
    location_lower = location.lower()
    return any(alias.lower() in location_lower for alias in aliases)
