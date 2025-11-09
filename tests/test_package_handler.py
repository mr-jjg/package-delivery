# /tests/test_package_handler.py

import datetime
import fleet
import pytest
import package_handler as ph
import package
import hash_table
import truck
import warehouse_repository as wr
from datetime import time

@pytest.fixture
def warehouse_reset():
    prev = wr.get_warehouse_hash() if hasattr(wr, "get_warehouse_hash") else None
    try:
        yield
    finally:
        if prev is not None:
            wr.set_warehouse_hash(prev)

@pytest.fixture
def sample_table():
    table = hash_table.HashTable(size=8)
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

def make_pkg(pid=1, deadline=None, note=None):
    p = package.Package(pid, "address", "city", "state", 99999, None, 0.0, None)
    p.delivery_deadline = deadline if deadline is not None else package.Package.EOD_TIME
    p.special_note = note
    return p

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

def test_merge_addresses_when_both_none_sets_W_links_and_earliest_deadline_for_both(warehouse_reset):
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
    
def test_build_constraints_list_baseline_union(warehouse_reset):
    # Order via Package.__lt__ -> package_id
    table = hash_table.HashTable(size=5)
    packages = [
        package.Package(1, "123 Maple Street", "Springfield", "IL", 62701, "EOD", 2.5, "T, 2"),
        package.Package(2, "456 Oak Avenue", "Chicago", "IL", 60614, "10:30 AM", 5.0, None),
        package.Package(3, "789 Pine Road", "Naperville", "IL", 60540, "EOD", 1.2, "X, 10:20 AM, 410 S State St, Salt Lake City, UT, 84111"),
        package.Package(4, "321 Birch Lane", "Peoria", "IL", 61602, "EOD", 3.3, None),
        package.Package(5, "654 Cedar Street", "Champaign", "IL", 61820, "4:00 PM", 4.8, "W, 15, 19"),
    ]
    for pkg in packages:
        pkg.special_note = pkg.parse_special_note()
        table.insert(pkg.package_id, pkg)
    warehouse_hash = wr.set_warehouse_hash(table)
    handler = ph.PackageHandler()
    constraints_list = handler.build_constraints_list()
    assert len(constraints_list) == 3
    assert packages[2] not in constraints_list
    assert packages[3] not in constraints_list
    assert len(set(constraints_list)) == len(constraints_list)
    assert constraints_list[0].package_id == 1
    assert constraints_list[1].package_id == 2
    assert constraints_list[2].package_id == 5

def test_build_constraints_list_excludes_eod_plus_special_note_x(warehouse_reset):
    table = hash_table.HashTable(size=5)
    packages = [
        package.Package(1, "123 Maple Street", "Springfield", "IL", 62701, "EOD", 2.5, "X, 10:20 AM, 410 S State St, Salt Lake City, UT, 84111"),
        package.Package(2, "456 Oak Avenue", "Chicago", "IL", 60614, "EOD", 5.0, "X, 10:20 AM, 410 S State St, Salt Lake City, UT, 84111"),
        package.Package(3, "789 Pine Road", "Naperville", "IL", 60540, "EOD", 1.2, "X, 10:20 AM, 410 S State St, Salt Lake City, UT, 84111"),
        package.Package(4, "321 Birch Lane", "Peoria", "IL", 61602, "EOD", 3.3, "X, 10:20 AM, 410 S State St, Salt Lake City, UT, 84111"),
        package.Package(5, "654 Cedar Street", "Champaign", "IL", 61820, "EOD", 4.8, "X, 10:20 AM, 410 S State St, Salt Lake City, UT, 84111"),
    ]
    for pkg in packages:
        pkg.special_note = pkg.parse_special_note()
        table.insert(pkg.package_id, pkg)
    warehouse_hash = wr.set_warehouse_hash(table)
    handler = ph.PackageHandler()
    constraints_list = handler.build_constraints_list()
    assert len(constraints_list) == 0
    assert constraints_list == []

def test_build_constraints_list_includes_delivery_deadline_with_special_note_x(warehouse_reset):
    table = hash_table.HashTable(size=5)
    packages = [
        package.Package(1, "123 Maple Street", "Springfield", "IL", 62701, "9:00 AM", 2.5, "X, 10:20 AM, 410 S State St, Salt Lake City, UT, 84111"),
        package.Package(2, "456 Oak Avenue", "Chicago", "IL", 60614, "10:00 AM", 5.0, "X, 10:20 AM, 410 S State St, Salt Lake City, UT, 84111"),
        package.Package(3, "789 Pine Road", "Naperville", "IL", 60540, "11:00 AM", 1.2, "X, 10:20 AM, 410 S State St, Salt Lake City, UT, 84111"),
        package.Package(4, "321 Birch Lane", "Peoria", "IL", 61602, "12:00 PM", 3.3, "X, 10:20 AM, 410 S State St, Salt Lake City, UT, 84111"),
        package.Package(5, "654 Cedar Street", "Champaign", "IL", 61820, "1:00 PM", 4.8, "X, 10:20 AM, 410 S State St, Salt Lake City, UT, 84111"),
    ]
    for pkg in packages:
        pkg.special_note = pkg.parse_special_note()
        table.insert(pkg.package_id, pkg)
    warehouse_hash = wr.set_warehouse_hash(table)
    handler = ph.PackageHandler()
    constraints_list = handler.build_constraints_list()
    assert len(constraints_list) == 5
    assert constraints_list == packages
    assert [p.package_id for p in constraints_list] == [1, 2, 3, 4, 5]

def test_build_constraints_removes_dupes(warehouse_reset):
    table = hash_table.HashTable(size=5)
    packages = [
        package.Package(6, "123 Maple Street", "Springfield", "IL", 62701, "11:00 AM", 2.5, "T, 2"),
        package.Package(7, "456 Oak Avenue", "Chicago", "IL", 60614, "12:00 AM", 5.0, "W, 15, 19"),
        package.Package(6, "123 Maple Street", "Springfield", "IL", 62701, "11:00 AM", 2.5, "T, 2"),
        package.Package(7, "456 Oak Avenue", "Chicago", "IL", 60614, "12:00 AM", 5.0, "W, 15, 19")
    ]
    for pkg in packages:
        pkg.special_note = pkg.parse_special_note()
        table.insert(pkg.package_id, pkg)
    warehouse_hash = wr.set_warehouse_hash(table)
    handler = ph.PackageHandler()
    constraints_list = handler.build_constraints_list()
    ids = [p.package_id for p in constraints_list]
    assert len(ids) == len(set(ids)) == 2
    assert sorted(ids) == [6, 7]

def test_build_constraints_list_uses_identity_semantics(patch_get_warehouse_hash):
    handler = ph.PackageHandler()
    constraints_list = handler.build_constraints_list()
    src = {p.package_id: p for p in patch_get_warehouse_hash}
    for p in constraints_list:
        assert p is src[p.package_id]

def test_build_constraints_list_does_not_mutate(patch_get_warehouse_hash):
    handler = ph.PackageHandler()
    constraints_list = handler.build_constraints_list()
    assert constraints_list[0].package_id == 1
    assert constraints_list[0].address == "123 Maple Street"
    assert constraints_list[0].city == "Springfield"
    assert constraints_list[0].state == "IL"
    assert constraints_list[0].zip_code == 62701
    assert constraints_list[0].delivery_deadline == time(10, 0)
    
@pytest.mark.parametrize(
    "expected, deadline, note",
    [
        # Priority 0:    delivery deadline and     delayed
        (0, datetime.time(0, 0), ['D', datetime.time(12, 0)]),
        (0, datetime.time(11, 59), ['D', datetime.time(12, 0)]),
        # Priority 1:    delivery deadline and not delayed
        (1, datetime.time(0, 0), None),
        (1, datetime.time(0, 0), ['X', "Address"]),
        (1, datetime.time(11, 0), ['T', 2]),
        (1, datetime.time(11, 0), ['W', 2]),
        # Priority 2: no delivery deadline and not delayed
        (2, package.Package.EOD_TIME, None),
        (2, package.Package.EOD_TIME, ['X', "Address"]),
        (2, package.Package.EOD_TIME, ['T', 2]),
        (2, package.Package.EOD_TIME, ['W', 2]),
        # Priority 3: no delivery deadline and     delayed
        (3, package.Package.EOD_TIME, ['D', datetime.time(12, 0)]),
        (3, package.Package.EOD_TIME, ['D', datetime.time(12, 0)])
    ]
)
def test_set_package_priorities_single(expected, deadline, note):
    table = hash_table.HashTable(size=1)
    pkg = make_pkg(1, deadline, note)
    table.insert(pkg.package_id, pkg)
    handler = ph.PackageHandler()
    handler.set_package_priorities([pkg])
    assert pkg.delivery_deadline == deadline
    assert pkg.special_note == note
    assert pkg.priority == expected
    
def test_set_package_priorities_multiple():
    handler = ph.PackageHandler()
    packages = [
        make_pkg(1, datetime.time(9, 0), ['D', datetime.time(13, 0)]),
        make_pkg(2, datetime.time(13, 0), None),
        make_pkg(3, package.Package.EOD_TIME, None),
        make_pkg(4, package.Package.EOD_TIME, ['D', datetime.time(13, 0)])
    ]
    handler.set_package_priorities(packages)
    priorities = [p.priority for p in packages]
    assert priorities == [0, 1, 2, 3]
    
def test_note_lowercase_d_is_not_delayed():
    handler = ph.PackageHandler()
    pkg1 = make_pkg(1, datetime.time(9, 0), ['d', datetime.time(13, 0)])
    pkg2 = make_pkg(2, package.Package.EOD_TIME, ['d', datetime.time(13, 0)])
    handler.set_package_priorities([pkg1, pkg2])
    assert pkg1.priority == 1
    assert pkg2.priority == 2

def test_note_leading_space_then_D_is_not_delayed_currently():
    handler = ph.PackageHandler()
    pkg1 = make_pkg(1, datetime.time(9, 0), [' D', datetime.time(13, 0)])
    pkg2 = make_pkg(2, package.Package.EOD_TIME, [' D', datetime.time(13, 0)])
    handler.set_package_priorities([pkg1, pkg2])
    assert pkg1.priority == 1
    assert pkg2.priority == 2

def test_note_whitespace_only_is_not_delayed():
    handler = ph.PackageHandler()
    pkg1 = make_pkg(1, datetime.time(9, 0), [' ', datetime.time(13, 0)])
    pkg2 = make_pkg(2, package.Package.EOD_TIME, [' ', datetime.time(13, 0)])
    handler.set_package_priorities([pkg1, pkg2])
    assert pkg1.priority == 1
    assert pkg2.priority == 2

@pytest.fixture
def sample_special_notes(monkeypatch):
    table = hash_table.HashTable(size=5)
    # Package values cleaned as though they were ran through project_data's clean_value helper function
    packages = [
        package.Package(1, "123 Maple Street", "Springfield", "IL", 62701, "10:00 AM", 2.5, "T, 1"),
        package.Package(2, "456 Oak Avenue", "Chicago", "IL", 60614, "EOD", 5.0, "T, 2"),
        package.Package(3, "789 Pine Road", "Naperville", "IL", 60540, "10:00 AM", 1.2, "D, 9:05 AM"),
        package.Package(4, "321 Birch Lane", "Peoria", "IL", 61602, "EOD", 3.3, "D, 9:30 AM"),
        package.Package(5, "654 Cedar Street", "Champaign", "IL", 61820, "4:00 PM", 4.8, "W, 6"),
        package.Package(6, "123 Maple Street", "Springfield", "IL", 62701, "11:00 AM", 2.5, "W, 7"),
        package.Package(7, "456 Oak Avenue", "Chicago", "IL", 60614, "12:00 AM", 5.0, None),
        package.Package(8, "321 Birch Lane", "Peoria", "IL", 61602, "1:00 PM", 3.3, None),
        package.Package(9, "789 Pine Road", "Naperville", "IL", 60540, "EOD", 1.2, None),
    ]
    for pkg in packages:
        pkg.special_note = pkg.parse_special_note()
        table.insert(pkg.package_id, pkg)
    monkeypatch.setattr(ph, "get_warehouse_hash", lambda: table)
    return packages

def test_handle_with_truck_note_sets_truck(sample_special_notes):
    handler = ph.PackageHandler()
    handler.handle_with_truck_note(sample_special_notes)
    modified = [pkg.package_id for pkg in sample_special_notes if pkg.truck is not None]
    assert len(modified) == 2
    assert modified == [1, 2]
    assert sample_special_notes[0].truck == 0
    assert sample_special_notes[1].truck == 1

def test_handle_with_truck_does_not_mutate_other_packages(sample_special_notes):
    handler = ph.PackageHandler()
    handler.handle_with_truck_note(sample_special_notes)
    not_modified = [pkg.package_id for pkg in sample_special_notes if pkg.truck is None]
    assert len(not_modified) == 7
    assert not_modified == [3, 4, 5, 6, 7, 8, 9]

def test_handle_with_truck_idempotence(sample_special_notes):
    handler = ph.PackageHandler()
    handler.handle_with_truck_note(sample_special_notes)
    assert sample_special_notes[0].truck == 0
    assert sample_special_notes[1].truck == 1
    for i in range(10):
        handler.handle_with_truck_note(sample_special_notes)
        assert sample_special_notes[0].truck == 0
        assert sample_special_notes[1].truck == 1

@pytest.mark.parametrize(
    "t_note, expected",
    [
        ("t, 1", "t, 1"),
        ("t, 2", "t, 2"),
        (" T, 1", " T, 1"),
        (" T, 2", " T, 2"),
        (" , 1", " , 1"),
        (" , 2", " , 2")
    ]
)
def test_handle_with_truck_incorrect_input_is_not_set(t_note, expected):
    pkg = package.Package(1, "123 Maple Street", "Springfield", "IL", 62701, "10:00 AM", 2.5, t_note)
    table = hash_table.HashTable(size=1)
    table.insert(pkg.package_id, pkg)
    handler = ph.PackageHandler()
    handler.handle_with_truck_note([pkg])
    assert pkg.truck is None
    assert pkg.special_note == t_note

def test_handle_delayed_without_deadline_note_does_not_handle_packages_with_deadlines(sample_special_notes):
    fl = fleet.Fleet(1)
    handler = ph.PackageHandler()
    handler.handle_delayed_without_deadline_note(sample_special_notes, fl)
    assert sample_special_notes[2].truck is None

def test_handle_delayed_without_deadline_note_handles_packages_without_deadlines(sample_special_notes):
    fl = fleet.Fleet(1)
    handler = ph.PackageHandler()
    handler.handle_delayed_without_deadline_note(sample_special_notes, fl)
    assert sample_special_notes[3].truck is 0
    
def test_handle_delayed_without_deadline_note_adds_to_first_empty_truck(sample_special_notes):
    fl = fleet.Fleet(4)
    fl.truck_list[0].driver = "William"
    fl.truck_list[1].driver = "Keekus"
    pkg = package.Package(1, "123 Maple Street", "Springfield", "IL", 62701, "EOD", 2.5, ["D", datetime.time(13, 0)])
    handler = ph.PackageHandler()
    handler.handle_delayed_without_deadline_note([pkg], fl)
    assert pkg.truck == 2

@pytest.mark.parametrize(
    "d_note, current, expected",
    [
        (["D", datetime.time(13, 0)], None, 0),
        (["D", datetime.time(13, 0)], 0, 0),
        (["D", datetime.time(13, 0)], 1, 0)
    ]
)
def test_handle_delayed_without_deadline_note_overwrites_existing_truck_field(d_note, current, expected):
    fl = fleet.Fleet(1)
    pkg = package.Package(1, "123 Maple Street", "Springfield", "IL", 62701, "EOD", 2.5, d_note)
    pkg.truck = current
    table = hash_table.HashTable(size=1)
    table.insert(pkg.package_id, pkg)
    handler = ph.PackageHandler()
    handler.handle_delayed_without_deadline_note([pkg], fl)
    assert pkg.truck == expected

def test_handle_delayed_without_deadline_note_no_empty_trucks():
    fl = fleet.Fleet(2)
    fl.truck_list[0].driver = "William"
    fl.truck_list[1].driver = "Keekus"
    pkg = package.Package(1, "123 Maple Street", "Springfield", "IL", 62701, "EOD", 2.5, ["D", datetime.time(13, 0)])
    table = hash_table.HashTable(size=1)
    table.insert(pkg.package_id, pkg)
    handler = ph.PackageHandler()
    handler.handle_delayed_without_deadline_note([pkg], fl)
    assert pkg.truck == 1

def test_handle_delayed_without_deadline_note_handles_empty_fleet():
    fl = fleet.Fleet(0)
    pkg = package.Package(1, "123 Maple Street", "Springfield", "IL", 62701, "EOD", 2.5, ["D", datetime.time(13, 0)])
    table = hash_table.HashTable(size=1)
    table.insert(pkg.package_id, pkg)
    handler = ph.PackageHandler()
    with pytest.raises(ValueError):
        handler.handle_delayed_without_deadline_note([pkg], fl)
    assert pkg.truck != -1

def test_handle_delayed_without_deadline_note_is_idempotent():
    fl = fleet.Fleet(1)
    pkg = package.Package(1, "123 Maple Street", "Springfield", "IL", 62701, "EOD", 2.5, ["D", datetime.time(13, 0)])
    table = hash_table.HashTable(size=1)
    table.insert(pkg.package_id, pkg)
    handler = ph.PackageHandler()
    handler.handle_delayed_without_deadline_note([pkg], fl)
    assert pkg.truck == 0
    for i in range(10):
        handler.handle_delayed_without_deadline_note([pkg], fl)
        assert pkg.truck == 0

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