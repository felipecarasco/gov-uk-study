"""UK postcode rules shared by the search form and the results page."""

import re

# Outward code (area letters, district digit, optional extra character) then
# inward code (sector digit, two letters), checked without spaces.
# For example CR02QQ, SE17PB, EC1A1BB.
_POSTCODE = re.compile(r"^[A-Z]{1,2}[0-9][A-Z0-9]?[0-9][A-Z]{2}$")


def normalise(raw):
    """Upper case with no spaces: the form the API and the database compare."""
    return re.sub(r"\s+", "", raw or "").upper()


def is_valid(raw):
    return bool(_POSTCODE.match(normalise(raw)))


def format_for_display(raw):
    """SE17PB becomes SE1 7PB. The inward code is always the last three characters."""
    compact = normalise(raw)
    return f"{compact[:-3]} {compact[-3:]}"
