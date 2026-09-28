"""Centralized (source, reliability_status) tagging -- data-adapter-build-
guide.md Phase 8, item 1.

The naive version of this ("assign_reliability(source) -> status") doesn't
hold up: OpenAQ readings are 'official' or 'sensor' depending on the
individual location's `isMonitor` flag (see app.adapters.openaq), not on
the source name alone. So instead of deriving a status, this centralizes
what pairings are *valid* and checks every reading against it at the one
place all of them pass through -- insert_normalized_reading -- so a future
adapter mistake (e.g. tagging a low-cost sensor 'official') fails loudly
instead of quietly corrupting the reliability signal the frontend relies on.
"""
VALID_SOURCE_RELIABILITY = {
    "waqi": {"official"},
    "openaq": {"official", "sensor"},
    "openweathermap": {"modelled"},
    "community": {"community"},
    "opendata_nepal_historical": {"official"},
}


def check_reliability(source: str, reliability_status: str) -> None:
    allowed = VALID_SOURCE_RELIABILITY.get(source)
    if allowed is None:
        raise ValueError(f"unknown reading source: {source!r}")
    if reliability_status not in allowed:
        raise ValueError(
            f"source {source!r} cannot be tagged reliability_status "
            f"{reliability_status!r}; allowed: {sorted(allowed)}"
        )
