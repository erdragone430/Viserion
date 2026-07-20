LOCATION_ALIASES = {
    "isar_aerospace": ["Ottobrunn", "Munich", "München"],
    # Airbus Defence and Space's Munich-area presence is Ottobrunn/Taufkirchen,
    # not literally "Munich" - same lesson as Isar Aerospace and SAP's Garching.
    # NOTE: WorkdayScraper.filter_location() bypasses this check entirely
    # (see scrapers/direct_json.py) - its applied_facets already do exact
    # location-ID filtering, more precise than this text match. Kept here
    # for reference / in case that override is ever reverted.
    "airbus_ds": ["Ottobrunn", "Taufkirchen", "Munich", "München"],
    # IBM's own listings spell it "Muenchen" (ASCII transliteration), which
    # doesn't substring-match "München" - confirmed live, not guessed.
    "ibm": ["Muenchen", "Munich", "München"],
    # Multi-location postings render as a single "Multiple Locations" span
    # with no per-city breakdown (confirmed live, 32/113 results) - the
    # search itself is already scoped to /Munich/, so trust that label
    # rather than dropping these postings for lack of a parseable city.
    # NOTE: SiemensScraper.filter_location() now bypasses this check
    # entirely (see scrapers/companies/siemens.py) - its exact City facet
    # ID (Avature 42388=[912803]) already does precise server-side
    # filtering, more precise than this text match. Kept here for
    # reference / in case that override is ever reverted.
    "siemens": ["Munich", "München", "Multiple Locations"],
    # Same shape of issue as Siemens: rsCity=Munich already scopes the
    # search server-side, but multi-location postings show City/region
    # as "Multiple" instead of a city name (confirmed live, 6/106 results).
    "rohde_schwarz": ["Munich", "München", "Multiple"],
    "default": ["Munich", "München"],
}


def matches_location(location: str, company: str) -> bool:
    if not location:
        return False
    aliases = LOCATION_ALIASES.get(company, LOCATION_ALIASES["default"])
    location_lower = location.lower()
    return any(alias.lower() in location_lower for alias in aliases)
