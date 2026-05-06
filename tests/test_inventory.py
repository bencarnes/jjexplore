"""Pure tests for Inventory and parse_item_spec."""
from src.inventory import Inventory, parse_item_spec


def test_empty_inventory():
    inv = Inventory()
    assert len(inv) == 0
    assert inv.total() == 0
    assert inv.count("gold") == 0
    assert "gold" not in inv


def test_add_item():
    inv = Inventory()
    inv.add("gold", 5)
    assert inv.count("gold") == 5
    assert "gold" in inv


def test_add_stacks_existing_item():
    inv = Inventory()
    inv.add("gold", 5)
    inv.add("gold", 3)
    assert inv.count("gold") == 8


def test_add_zero_or_empty_is_noop():
    inv = Inventory()
    inv.add("gold", 0)
    inv.add("", 5)
    assert len(inv) == 0


def test_remove_partial():
    inv = Inventory()
    inv.add("gold", 5)
    assert inv.remove("gold", 2) is True
    assert inv.count("gold") == 3


def test_remove_all_drops_key():
    inv = Inventory()
    inv.add("apple", 1)
    inv.remove("apple", 1)
    assert "apple" not in inv
    assert len(inv) == 0


def test_remove_more_than_have_fails():
    inv = Inventory()
    inv.add("gold", 2)
    assert inv.remove("gold", 5) is False
    assert inv.count("gold") == 2  # unchanged


def test_items_returns_sorted_pairs():
    inv = Inventory()
    inv.add("zinc", 1)
    inv.add("apple", 2)
    inv.add("gold", 3)
    assert inv.items() == [("apple", 2), ("gold", 3), ("zinc", 1)]


def test_total_sums_counts():
    inv = Inventory()
    inv.add("gold", 5)
    inv.add("apple", 2)
    assert inv.total() == 7


def test_parse_item_spec_with_count():
    assert parse_item_spec("gold:5") == ("gold", 5)


def test_parse_item_spec_without_count_defaults_to_one():
    assert parse_item_spec("apple") == ("apple", 1)


def test_parse_item_spec_strips_whitespace():
    assert parse_item_spec("  potion  ") == ("potion", 1)
    assert parse_item_spec("gold:7") == ("gold", 7)


def test_parse_item_spec_empty():
    assert parse_item_spec("") == ("", 0)


def test_parse_item_spec_garbage_count_falls_back_to_one():
    assert parse_item_spec("apple:abc") == ("apple", 1)
