import pytest

from app import postcodes


@pytest.mark.parametrize(
    "raw, expected",
    [("CR0 2QQ", "CR02QQ"), ("  cr0   2qq ", "CR02QQ"), ("se17pb", "SE17PB"), (None, "")],
)
def test_normalise_removes_spaces_and_upper_cases(raw, expected):
    assert postcodes.normalise(raw) == expected


@pytest.mark.parametrize("raw", ["CR0 2QQ", "se1 7pb", "EC1A 1BB", "W1A 0AX", "M1 1AE", "B33 8TH"])
def test_accepts_full_uk_postcodes(raw):
    assert postcodes.is_valid(raw)


# "CRO 2QQ" has the letter O where the district needs a digit.
@pytest.mark.parametrize("raw", ["", "CR0", "12345", "CR0 2Q", "CRO 2QQ", "SW1A 1AAA"])
def test_rejects_partial_or_malformed_postcodes(raw):
    assert not postcodes.is_valid(raw)


@pytest.mark.parametrize(
    "raw, expected", [("CR02QQ", "CR0 2QQ"), ("se1 7pb", "SE1 7PB"), ("EC1A1BB", "EC1A 1BB")]
)
def test_formats_for_display_with_one_space(raw, expected):
    assert postcodes.format_for_display(raw) == expected
