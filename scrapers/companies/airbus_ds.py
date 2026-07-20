from ..direct_json import WorkdayScraper

# Facet IDs reverse-engineered live from ag.wd3.myworkdayjobs.com/en-US/Airbus's own
# search UI (Workday facet values, not guessed): the two Munich-area location facets
# ("Taufkirchen / Ottobrunn" and "München Area") plus the Defence and Space legal
# entity, so this scraper only covers that division, not Airbus Helicopters/Commercial
# Aircraft/Atlantic who share the same Workday tenant.
SCRAPER = WorkdayScraper(
    company="airbus_ds",
    host="ag.wd3.myworkdayjobs.com",
    tenant="ag",
    site="Airbus",
    applied_facets={
        "locations": ["f5811cef9cb50199bf69196b4c0a674b", "f5811cef9cb501a49eac0a694c0a8244"],
        "hiringCompany": ["f5811cef9cb501060f750c134e0aa55d"],
    },
)
