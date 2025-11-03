# /tests/test_package_handler.py

import pytest
import package_handler as ph
import package
import hash_table

@pytest.fixture
def sample_table():
    table = hash_table.HashTable(size=5)
    packages = [
        package.Package(1, "123 Main St", "Salt Lake City", "ST", "84101", "10:30 AM", 5, "None"),
        package.Package(2, "456 Elm St", "Murray", "ST",  "84107", "EOD", 7, "None"),
        package.Package(3, "789 Oak St", "Draper", "ST",  "84020", "EOD", 2, "None"),
    ]
    for pkg in packages:
        table.insert(pkg.package_id, pkg)
    return table, packages

@pytest.fixture
def patch_get_warehouse_hash(monkeypatch, sample_table):
    table, packages = sample_table
    monkeypatch.setattr(ph, "get_warehouse_hash", lambda: table)
    return packages

@pytest.fixture
def make_packages():
    #new_package = Package(package_id, address, city, state, zip_code, delivery_deadline, weight_kilo, special_note)
    def _make_packages():
        return [
            package.Package(1, "123 Maple Street", "Springfield", "IL", "62701", "10:00 AM", 2.5, "T, 2"),
            package.Package(2, "456 Oak Avenue", "Chicago", "IL", "60614", "", 5.0, "None"),
            package.Package(3, "789 Pine Road", "Naperville", "IL", "60540", "EOD", 1.2, "D, 9:05 AM"),
            package.Package(4, "321 Birch Lane", "Peoria", "IL", "61602", "12:00 PM", 3.3, "X, 10:20 AM, 410 S State St, Salt Lake City, UT, 84111"),
            package.Package(5, "654 Cedar Street", "Champaign", "IL", "61820", "4:00 PM", 4.8, "W, 15, 19"),
        ]
    return _make_packages

def test_list_builder_returns_all_packages(patch_get_warehouse_hash):
    result = ph.list_builder()
    package_ids = [p.package_id for p in result]
    assert set(package_ids) ==  {1, 2, 3}
    assert package_ids == sorted(package_ids)

@pytest.mark.parametrize(
    "sets, results",
    [   
        ([{1, 2, 3}, {4, 5}], [{4, 5}, {1, 2, 3}]),
        ([{1, 2, 3}, {2, 3, 4}], [{1, 2, 3, 4}]),
        ([{1, 2}, {1, 2}], [{1, 2}]),
        ([{0}, {1}],[{1}, {0}]),
        ([], [])
    ]
)
def test_merge_sets_returns_correct_results(sets, results):
    test_result = ph.merge_sets(sets)
    
    assert test_result == results
    assert isinstance(test_result, list)

@pytest.mark.parametrize(
    "lists, results",
    [
        ([[1, 2, 3], [4, 5]], [1, 2, 3, 4, 5]),
        ([[1, 2, 3], [2, 3, 4]], [1, 2, 3, 4]),
        ([[1, 2], [1, 2]], [1, 2]),
        ([[], []], [])
    ]
)
def test_perform_union_on_lists_removes_duplicates(lists, results):
    list_a, list_b = lists
    test_result = ph.perform_union_on_lists(list_a, list_b)
    assert test_result == results
    assert isinstance(test_result, list)
    
def test_perform_union_on_lists_returns_sorted():
    list_a = [2, 3, 1]
    list_b = [0]
    assert ph.perform_union_on_lists(list_a, list_b) == [0, 1, 2, 3]