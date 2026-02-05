from core.prices import get_price_map, get_price_map_asof


def test_get_price_map_empty():
    assert get_price_map([]) == {}


def test_get_price_map_asof_invalid_date():
    assert get_price_map_asof(["1234"], "not-a-date") == {}
