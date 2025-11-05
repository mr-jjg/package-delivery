# /tests/test_package_handler.py

import datetime
import pytest
import package_handler as ph
import package
import hash_table
import warehouse_repository as wr

@pytest.fixture
def sample_table():
    table = hash_table.HashTable(size=5)
    # Package values cleaned as though they were ran through project_data's clean_value helper function
    packages = [
        package.Package(1, "123 Maple Street", "Springfield", "IL", 62701, "10:00 AM", 2.5, "T, 2"),
        package.Package(2, "456 Oak Avenue", "Chicago", "IL", 60614, "EOD", 5.0, None),
        package.Package(3, "789 Pine Road", "Naperville", "IL", 60540, "EOD", 1.2, "D, 9:05 AM"),
        package.Package(4, "321 Birch Lane", "Peoria", "IL", 61602, "12:00 PM", 3.3, "X, 10:20 AM, 410 S State St, Salt Lake City, UT, 84111"),
        package.Package(5, "654 Cedar Street", "Champaign", "IL", 61820, "4:00 PM", 4.8, "W, 15, 19"),
        package.Package(6, "123 Maple Street", "Springfield", "IL", 62701, "11:00 AM", 2.5, None),
        package.Package(7, "456 Oak Avenue", "Chicago", "IL", 60614, "12:00 AM", 5.0, None),
        package.Package(8, "321 Birch Lane", "Peoria", "IL", 61602, "1:00 PM", 3.3, None)
    ]
    for pkg in packages:
        pkg.special_note = pkg.parse_special_note()
        table.insert(pkg.package_id, pkg)
    return table, packages

@pytest.fixture
def patch_get_warehouse_hash(monkeypatch, sample_table):
    table, packages = sample_table
    monkeypatch.setattr(ph, "get_warehouse_hash", lambda: table)
    return packages
    
def snapshot(packages):
    return [(p.package_id, p.address, p.delivery_deadline, p.special_note) for p in packages]

def test_merge_addresses_does_not_change_packages_with_different_addresses(patch_get_warehouse_hash):
    before = snapshot(patch_get_warehouse_hash[:5])
    before.pop(1)
    handler = ph.PackageHandler()
    handler.merge_addresses()
    after = snapshot(patch_get_warehouse_hash[:5])
    after.pop(1)
    assert before == after

def test_merge_addresses_copies_note_when_i_has_note_and_j_none_and_sets_earliest_deadline(patch_get_warehouse_hash):
    pkg = patch_get_warehouse_hash[5]
    assert pkg.special_note == None and pkg.delivery_deadline == datetime.time(11, 0)
    handler = ph.PackageHandler()
    handler.merge_addresses()
    assert pkg.special_note == ['T', 2] and pkg.delivery_deadline == datetime.time(10, 0)

def test_merge_addresses_does_not_copy_when_note_is_X(patch_get_warehouse_hash):
    pkg_a = patch_get_warehouse_hash[3]
    pkg_b = patch_get_warehouse_hash[7]
    handler = ph.PackageHandler()
    handler.merge_addresses()
    assert pkg_a.special_note == ['X', datetime.time(10, 20), '410 S State St', 'Salt Lake City', 'UT', 84111]
    assert pkg_b.special_note == None
    assert pkg_a.delivery_deadline == datetime.time(12, 0)
    assert pkg_b.delivery_deadline == datetime.time(13, 0)

def test_merge_addresses_when_both_none_sets_W_links_and_earliest_deadline_for_both():
    table = hash_table.HashTable(size=4)
    packages = [
        package.Package(1, "123 Maple Street", "Springfield", "IL", 62701, "10:00 AM", 2.5, None),
        package.Package(2, "456 Oak Avenue", "Chicago", "IL", 60614, "10:00 AM", 5.0, None),
        package.Package(3, "123 Maple Street", "Springfield", "IL", 62701, "11:00 PM", 2.5, None),
        package.Package(4, "456 Oak Avenue", "Chicago", "IL", 60614, "11:00 PM", 5.0, None)
    ]
    for pkg in packages:
        pkg.special_note = pkg.parse_special_note()
        table.insert(pkg.package_id, pkg)
    warehouse_hash = wr.set_warehouse_hash(table)
    handler = ph.PackageHandler()
    handler.merge_addresses()
    assert packages[0].special_note == ['W', 3]
    assert packages[2].special_note == ['W', 1]
    assert packages[0].delivery_deadline == datetime.time(10, 0)
    assert packages[2].delivery_deadline == datetime.time(10, 0)

def test_merge_addresses_is_idempotent_on_second_call(patch_get_warehouse_hash):
    handler = ph.PackageHandler()
    handler.merge_addresses()
    before = snapshot(patch_get_warehouse_hash)
    handler.merge_addresses()
    after = snapshot(patch_get_warehouse_hash)
    assert before == after

def test_list_builder_returns_all_packages(patch_get_warehouse_hash):
    result = ph.list_builder()
    package_ids = [p.package_id for p in result]
    assert set(package_ids) ==  {1, 2, 3, 4, 5, 6, 7, 8}
    assert package_ids == sorted(package_ids)

def test_list_builder_returns_only_with_attributes(patch_get_warehouse_hash):
    result = ph.list_builder('special_note')
    package_ids = [p.package_id for p in result]
    assert set(package_ids) == {1, 3, 4, 5}
    assert len(package_ids) == 4
    
def test_list_builder_excludes_values(patch_get_warehouse_hash):
    result = ph.list_builder('delivery_deadline', 'delivery_deadline', package.Package.EOD_TIME)
    package_ids = [p.package_id for p in result]
    assert set(package_ids) == {1, 4, 5, 6, 7, 8}
    assert len(package_ids) == 6
    
def test_list_builder_excludes_values_in_list(patch_get_warehouse_hash):
    result = ph.list_builder('special_note', 'special_note', 'W')
    package_ids = [p.package_id for p in result]
    assert set(package_ids) == {1, 3, 4}
    assert len(package_ids) == 3
    
def test_list_builder_uses_identity_semantics(patch_get_warehouse_hash):
    packages = patch_get_warehouse_hash
    same_packages = ph.list_builder()
    for i in range(len(packages)):
        assert packages[i] is same_packages[i]
    
def test_list_builder_empty(monkeypatch):
    monkeypatch.setattr(ph, "get_warehouse_hash", lambda: [])
    assert ph.list_builder() == []    

def test_list_builder_missing_attribute_ignored(monkeypatch):
    class Dummy:
        def __init__(self, pid): self.package_id = pid
    monkeypatch.setattr(ph, "get_warehouse_hash", lambda: [[Dummy(n) for n in range(100)]])
    assert ph.list_builder('special_note') == []

def test_anti_list_builder_returns_all(patch_get_warehouse_hash):
    result = ph.list_builder()
    packages = [
        package.Package(6, "123 Main", "Town", "ST", "00000", "EOD", 1.0, "X, 9:00 AM"),
        package.Package(7, "456 Broad Ave", "City", "TS", "11111", "10:30 AM", 2.5, None)
    ]
    anti_package_list = ph.anti_list_builder(packages)
    assert len(anti_package_list) == len(result)
    for i in range(len(anti_package_list)):
        assert anti_package_list[i].package_id == result[i].package_id
    

def test_anti_list_builder_returns_none(patch_get_warehouse_hash):
    packages = patch_get_warehouse_hash
    anti_package_list = ph.anti_list_builder(packages)
    assert len(anti_package_list) == 0
    assert anti_package_list == []

def test_anti_list_builder_returns_some(patch_get_warehouse_hash):
    packages = patch_get_warehouse_hash
    packages = [packages[0], packages[1]]
    anti_package_list = ph.anti_list_builder(packages)
    assert len(anti_package_list) == 6
    for pkg in anti_package_list:
        assert pkg not in packages

def test_anti_list_builder_uses_identity_semantics(patch_get_warehouse_hash):
    packages = patch_get_warehouse_hash
    anti_package_list = ph.anti_list_builder()
    for i in range(len(packages)):
        assert packages[i] is anti_package_list[i]

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