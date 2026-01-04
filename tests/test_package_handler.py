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

def make_delayed_deadline_pkg(pid, deadline, delay, group=None, truck=None):
    p = make_pkg(pid=pid, deadline=deadline, note=["D", delay])
    p.priority = 0
    p.delay_time = None
    p.group = group
    p.truck = truck
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

def test_handle_delayed_with_deadline_note_empty_fleet_raises():
    fl = fleet.Fleet(0)
    handler = ph.PackageHandler()
    pkg = make_delayed_deadline_pkg(
        pid=1,
        deadline=datetime.time(10, 30),
        delay=datetime.time(9, 0)
    )
    with pytest.raises(ValueError):
        handler.handle_delayed_with_deadline_note([pkg], fl)


def test_handle_delayed_with_deadline_note_no_candidates_noop():
    fl = fleet.Fleet(1)
    handler = ph.PackageHandler()

    # Not priority 0, so should be ignored
    pkg = make_pkg(pid=1, deadline=datetime.time(10, 30), note=["D", datetime.time(9, 0)])
    pkg.priority = 1
    pkg.group = 99
    pkg.truck = None
    pkg.delay_time = None

    handler.handle_delayed_with_deadline_note([pkg], fl)

    assert pkg.group == 99
    assert pkg.truck is None
    assert pkg.delay_time is None


def test_handle_delayed_with_deadline_note_delay_after_deadline_raises():
    fl = fleet.Fleet(1)
    handler = ph.PackageHandler()

    pkg = make_delayed_deadline_pkg(
        pid=1,
        deadline=datetime.time(10, 0),
        delay=datetime.time(10, 1)  # arrives after deadline
    )

    with pytest.raises(ValueError):
        handler.handle_delayed_with_deadline_note([pkg], fl)


def test_handle_delayed_with_deadline_note_assigns_groups_after_existing_groups():
    fl = fleet.Fleet(1)
    handler = ph.PackageHandler()

    # Existing groups already present in the list, so new ones should start after max(existing)
    existing_a = make_pkg(pid=90, deadline=package.Package.EOD_TIME, note=None)
    existing_a.group = 5
    existing_a.priority = 2

    existing_b = make_pkg(pid=91, deadline=package.Package.EOD_TIME, note=None)
    existing_b.group = 12
    existing_b.priority = 2

    p1 = make_delayed_deadline_pkg(pid=1, deadline=datetime.time(10, 30), delay=datetime.time(9, 0))
    p2 = make_delayed_deadline_pkg(pid=2, deadline=datetime.time(10, 15), delay=datetime.time(9, 0))

    handler.handle_delayed_with_deadline_note([existing_a, existing_b, p1, p2], fl)

    assert p1.group == 13
    assert p2.group == 13


def test_handle_delayed_with_deadline_note_splits_clusters_when_infeasible():
    fl = fleet.Fleet(1)
    handler = ph.PackageHandler()

    # These two cannot share a cluster:
    early_deadline = make_delayed_deadline_pkg(
        pid=1,
        deadline=datetime.time(9, 30),
        delay=datetime.time(9, 0)
    )
    late_arrival = make_delayed_deadline_pkg(
        pid=2,
        deadline=datetime.time(10, 0),
        delay=datetime.time(9, 50)
    )

    handler.handle_delayed_with_deadline_note([early_deadline, late_arrival], fl)

    assert early_deadline.group != late_arrival.group
    assert early_deadline.group == 0
    assert late_arrival.group == 1


def test_handle_delayed_with_deadline_note_skips_truck_assigned_packages():
    fl = fleet.Fleet(1)
    handler = ph.PackageHandler()

    # Truck already set, so this pkg should be ignored by the method
    trucked = make_delayed_deadline_pkg(
        pid=1,
        deadline=datetime.time(10, 30),
        delay=datetime.time(9, 0),
        truck=0
    )

    handler.handle_delayed_with_deadline_note([trucked], fl)

    assert trucked.group is None


def test_handle_delayed_with_deadline_note_is_idempotent():
    fl = fleet.Fleet(1)
    handler = ph.PackageHandler()

    p1 = make_delayed_deadline_pkg(pid=0, deadline=datetime.time(10, 30), delay=datetime.time(9, 0))
    p2 = make_delayed_deadline_pkg(pid=1, deadline=datetime.time(10, 15), delay=datetime.time(9, 0))

    handler.handle_delayed_with_deadline_note([p1, p2], fl)
    first_g1 = p1.group
    first_g2 = p2.group

    for _ in range(10):
        handler.handle_delayed_with_deadline_note([p1, p2], fl)
        assert p1.group == first_g1
        assert p2.group == first_g2

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

@pytest.fixture
def sample_w_notes(monkeypatch):
    table = hash_table.HashTable(size=8)
    packages = [
        package.Package(1, "123 Maple Street", "Springfield", "IL", 62701, "1:00 PM", 2.5, "D, 10:30 AM"),
        package.Package(2, "456 Oak Avenue", "Chicago", "IL", 60614, "12:00 PM", 5.0, None),
        package.Package(3, "789 Pine Road", "Naperville", "IL", 60540, "EOD", 1.2, "W, 7"),
        package.Package(4, "321 Birch Lane", "Peoria", "IL", 61602, "EOD", 3.3, "D, 9:30 AM"),
        package.Package(5, "654 Cedar Street", "Champaign", "IL", 61820, "4:00 PM", 4.8, "W, 1, 2"),
        package.Package(6, "987 Yew Boulevard", "Rockford", "IL", 61020, "EOD", 4.8, "W, 2"),
        package.Package(7, "123 Maple Street", "Springfield", "IL", 62701, "11:00 AM", 2.5, "W, 3"),
        package.Package(8, "456 Oak Avenue", "Chicago", "IL", 60614, "12:00 AM", 5.0, "W, 4")
    ]
    for pkg in packages:
        pkg.special_note = pkg.parse_special_note()
        table.insert(pkg.package_id, pkg)
    handler = ph.PackageHandler()
    handler.set_package_priorities(packages)
    monkeypatch.setattr(ph, "get_warehouse_hash", lambda: table)
    return packages

def test_handle_with_package_note_sets_correct_group(sample_w_notes):
    handler = ph.PackageHandler()
    packages = handler.handle_with_package_note(sample_w_notes)
    assert packages[7].group == 0
    assert packages[3].group == 0
    assert packages[6].group == 1
    assert packages[2].group == 1
    assert packages[5].group == 2
    assert packages[1].group == 2
    assert packages[4].group == 2
    assert packages[0].group == 2

def test_handle_with_package_note_sets_correct_priority(sample_w_notes):
    handler = ph.PackageHandler()
    packages = handler.handle_with_package_note(sample_w_notes)
    assert packages[7].priority == 1
    assert packages[3].priority == 1
    assert packages[6].priority == 1
    assert packages[2].priority == 1
    assert packages[5].priority == 0
    assert packages[1].priority == 0
    assert packages[4].priority == 0
    assert packages[0].priority == 0

def test_handle_with_package_note_unknown_id_raises(monkeypatch):
    pkg = package.Package(1, "123 Maple Street", "Springfield", "IL", 62701, "EOD", 2.5, ["W", 9999])
    table = hash_table.HashTable(size=1)
    monkeypatch.setattr(ph, "get_warehouse_hash", lambda: table)
    table.insert(pkg.package_id, pkg)
    handler = ph.PackageHandler()
    with pytest.raises(ValueError):
        packages = handler.handle_with_package_note([pkg])

def test_handle_with_package_note_none_packages_set_to_priority_4(sample_w_notes):
    for package in sample_w_notes:
        package.priority = None
    handler = ph.PackageHandler()
    packages = handler.handle_with_package_note(sample_w_notes)
    for pkg in packages:
        assert pkg.priority == 4

def test_handle_with_package_note_adds_package_not_in_list(monkeypatch):
    monkeypatch.setattr(ph, "get_warehouse_hash", lambda: table)
    pkg = package.Package(1, "123 Maple Street", "Springfield", "IL", 62701, "EOD", 2.5, ["W", 2])
    missing = package.Package(2, "456 Oak Avenue", "Chicago", "IL", 60614, "12:00 PM", 5.0, None)
    table = hash_table.HashTable(size=2)
    table.insert(pkg.package_id, pkg)
    table.insert(missing.package_id, missing)
    handler = ph.PackageHandler()
    packages = handler.handle_with_package_note([pkg])
    ids = [p.package_id for p in packages]
    assert set(ids) == {1, 2}
    assert len(ids) == len(set(ids))

@pytest.mark.parametrize(
    "id, addr, city, state, zip_code, delivery_deadline, weight, special_note",
    [
        (1, "123 Maple Street", "Springfield", "IL", 62701, datetime.time(13, 0), 2.5, ["W", 9]),
        (2, "456 Oak Avenue", "Chicago", "IL", 60614, datetime.time(12, 0), 5.0, ["W", 9]),
        (3, "789 Pine Road", "Naperville", "IL", 60540, package.Package.EOD_TIME, 1.2, ["W", 9]),
        (4, "321 Birch Lane", "Peoria", "IL", 61602, package.Package.EOD_TIME, 3.3, ["W", 9]),
        (5, "654 Cedar Street", "Champaign", "IL", 61820, datetime.time(16, 0), 4.8, ["W", 9]),
        (6, "987 Yew Boulevard", "Rockford", "IL", 61020, package.Package.EOD_TIME, 4.8, ["W", 9]),
        (7, "123 Maple Street", "Springfield", "IL", 62701, datetime.time(11, 0), 2.5, ["W", 9]),
        (8, "456 Oak Avenue", "Chicago", "IL", 60614, datetime.time(0, 0), 5.0, ["W", 9])
    ]
)
def test_handle_with_package_note_only_modifies_group_and_priority(id, addr, city, state, zip_code, delivery_deadline, weight, special_note, monkeypatch):
    pkg9 = package.Package(9, "0", "0", "0", 0, datetime.time(13,0), 2.5, None)
    pkg = package.Package(id, addr, city, state, zip_code, delivery_deadline, weight, special_note)
    table = hash_table.HashTable(size=2)
    monkeypatch.setattr(ph, "get_warehouse_hash", lambda: table)
    pkg.special_note = pkg.parse_special_note()
    table.insert(pkg9.package_id, pkg9)
    table.insert(pkg.package_id, pkg)
    handler = ph.PackageHandler()
    before = (pkg.package_id, pkg.address, pkg.city, pkg.state, pkg.zip_code, pkg.delivery_deadline, pkg.weight_kilo, pkg.special_note, pkg.delivery_status, pkg.time_of_delivery, pkg.truck is None)
    packages = handler.handle_with_package_note([pkg])
    after = (pkg.package_id, pkg.address, pkg.city, pkg.state, pkg.zip_code, pkg.delivery_deadline, pkg.weight_kilo, pkg.special_note, pkg.delivery_status, pkg.time_of_delivery, pkg.truck is None)
    assert before == after

def test_handle_with_package_note_is_idempotent(sample_w_notes):
    handler = ph.PackageHandler()
    packages = handler.handle_with_package_note(sample_w_notes)
    assert packages[7].priority == 1
    assert packages[3].priority == 1
    assert packages[6].priority == 1
    assert packages[2].priority == 1
    assert packages[5].priority == 0
    assert packages[1].priority == 0
    assert packages[4].priority == 0
    assert packages[0].priority == 0
    assert packages[7].group == 0
    assert packages[3].group == 0
    assert packages[6].group == 1
    assert packages[2].group == 1
    assert packages[5].group == 2
    assert packages[1].group == 2
    assert packages[4].group == 2
    assert packages[0].group == 2
    packages = handler.handle_with_package_note(sample_w_notes)
    assert packages[7].priority == 1
    assert packages[3].priority == 1
    assert packages[6].priority == 1
    assert packages[2].priority == 1
    assert packages[5].priority == 0
    assert packages[1].priority == 0
    assert packages[4].priority == 0
    assert packages[0].priority == 0
    assert packages[7].group == 3
    assert packages[3].group == 3
    assert packages[6].group == 4
    assert packages[2].group == 4
    assert packages[5].group == 5
    assert packages[1].group == 5
    assert packages[4].group == 5
    assert packages[0].group == 5

def test_handle_with_package_note_offsets_groups_when_existing_groups_present(monkeypatch):
    table = hash_table.HashTable(size=4)

    # Pre-existing grouped package in the list (simulates earlier grouping stage)
    already_grouped = package.Package(99, "x", "x", "x", 0, "EOD", 1.0, None)
    already_grouped.special_note = already_grouped.parse_special_note()
    already_grouped.group = 10
    already_grouped.priority = 2

    # Two W-linked packages (1 with W note pointing to 2)
    p1 = package.Package(1, "a", "b", "c", 0, "EOD", 1.0, "W, 2")
    p2 = package.Package(2, "a2", "b2", "c2", 0, "EOD", 1.0, None)
    p1.special_note = p1.parse_special_note()
    p2.special_note = p2.parse_special_note()

    # Must be in warehouse_hash for lookup by id inside handle_with_package_note
    table.insert(already_grouped.package_id, already_grouped)
    table.insert(p1.package_id, p1)
    table.insert(p2.package_id, p2)
    monkeypatch.setattr(ph, "get_warehouse_hash", lambda: table)

    handler = ph.PackageHandler()
    pkgs = [already_grouped, p1]  # p2 will be discovered via lookup and appended

    pkgs = handler.handle_with_package_note(pkgs)

    # Group ids should start after existing max group (10), so next should be 11
    assert p1.group == 11
    assert p2.group == 11

def test_add_and_prioritize_remaining_packages_sets_special_note_none_to_4(patch_get_warehouse_hash):
    remaining_packages = []
    handler = ph.PackageHandler()
    handler.add_and_prioritize_remaining_packages(remaining_packages)
    ids = [pkg.package_id for pkg in remaining_packages if pkg.priority == 4]
    for pkg in remaining_packages:
        if not pkg.special_note:
            assert pkg.priority == 4

def test_add_and_prioritize_remaining_packages_sets_special_note_to_5(patch_get_warehouse_hash):
    remaining_packages = []
    handler = ph.PackageHandler()
    handler.add_and_prioritize_remaining_packages(remaining_packages)
    ids = [pkg.package_id for pkg in remaining_packages if pkg.priority == 5]
    for pkg in remaining_packages:
        if pkg.special_note:
            assert pkg.priority == 5

def test_add_and_prioritize_remaining_packages_overwrites_priority_value(patch_get_warehouse_hash):
    for pkg in patch_get_warehouse_hash:
        pkg.priority = -1
    remaining_packages = []
    handler = ph.PackageHandler()
    handler.add_and_prioritize_remaining_packages(remaining_packages)
    ids = [pkg.package_id for pkg in remaining_packages if pkg.priority != -1]
    for pkg in remaining_packages:
        assert pkg.priority != -1
        assert pkg.priority == 4 or pkg.priority == 5

def test_add_and_prioritize_remaining_packages_all_packages_in_warehouse_in_package_list(patch_get_warehouse_hash):
    remaining_packages = patch_get_warehouse_hash[4:]
    handler = ph.PackageHandler()
    handler.add_and_prioritize_remaining_packages(remaining_packages)
    ids = [pkg.package_id for pkg in remaining_packages]
    for pkg in patch_get_warehouse_hash:
        assert pkg.package_id in ids
    assert len(remaining_packages) == len(patch_get_warehouse_hash)

def test_add_and_prioritize_remaining_packages_raises_on_duplicate_packages(patch_get_warehouse_hash):
    remaining_packages = list(patch_get_warehouse_hash)
    remaining_packages.append(patch_get_warehouse_hash[0])
    assert len(set(remaining_packages)) != len(remaining_packages)
    handler = ph.PackageHandler()
    with pytest.raises(Exception):
        handler.add_and_prioritize_remaining_packages(remaining_packages)

def test_add_and_prioritize_does_not_mutate_existing_items(patch_get_warehouse_hash):
    handler = ph.PackageHandler()
    existing = [patch_get_warehouse_hash[0]]
    existing[0].priority = 99
    handler.add_and_prioritize_remaining_packages(existing)
    assert existing[0].priority == 99

def test_add_and_prioritize_remaining_packages_is_idempotent_when_called_twice(patch_get_warehouse_hash):
    packages = []
    handler = ph.PackageHandler()
    handler.add_and_prioritize_remaining_packages(packages)
    snapshot_ids = [p.package_id for p in packages]
    snapshot_priorities = [p.priority for p in packages]
    assert len(packages) == len(patch_get_warehouse_hash)
    handler.add_and_prioritize_remaining_packages(packages)
    assert [p.package_id for p in packages] == snapshot_ids
    assert [p.priority for p in packages] == snapshot_priorities
    assert len(packages) == len(patch_get_warehouse_hash)

@pytest.fixture
def sample_unsorted_list(monkeypatch):
    table = hash_table.HashTable(size=8)
    packages = [
        package.Package(1, "195 W Oakland Ave", "Salt Lake City", "UT", 84115, datetime.time(10, 30), 21, None),
        package.Package(2, "2530 S 500 E", "Salt Lake City", "UT", 84106, package.Package.EOD_TIME, 44, None),
        package.Package(3, "233 Canyon Rd", "Salt Lake City", "UT", 84103, package.Package.EOD_TIME, 2, "T, 2"),
        package.Package(4, "380 W 2880 S", "Salt Lake City", "UT", 84115, package.Package.EOD_TIME, 4, None),
        package.Package(5, "410 S State St", "Salt Lake City", "UT", 84111, package.Package.EOD_TIME, 5, None),
        package.Package(6, "3060 Lester St", "West Valley City", "UT", 84119, datetime.time(10, 30), 88, "D, 9:05 am"),
        package.Package(7, "1330 2100 S", "Salt Lake City", "UT", 84106, package.Package.EOD_TIME, 8, None),
        package.Package(8, "300 State St", "Salt Lake City", "UT", 84103, package.Package.EOD_TIME, 9, None),
        package.Package(9, "300 State St", "Salt Lake City", "UT", 84103, package.Package.EOD_TIME, 2, "X, 10:20 am, 410 S State St, Salt Lake City, UT, 84111"),
        package.Package(10, "600 E 900 South", "Salt Lake City", "UT", 84105, package.Package.EOD_TIME, 1, None),
        package.Package(11, "2600 Taylorsville Blvd", "Salt Lake City", "UT", 84118, package.Package.EOD_TIME, 1, None),
        package.Package(12, "3575 W Valley Central Station bus Loop", "West Valley City", "UT", 84119, package.Package.EOD_TIME, 1, None),
        package.Package(13, "2010 W 500 S", "Salt Lake City", "UT", 84104, datetime.time(10, 30), 2, None),
        package.Package(14, "4300 S 1300 E", "Millcreek", "UT", 84117, datetime.time(10, 30), 88, "W, 15, 19"),
        package.Package(15, "4580 S 2300 E", "Holladay", "UT", 84117, datetime.time(9, 0), 4, None),
        package.Package(16, "4580 S 2300 E", "Holladay", "UT", 84117, datetime.time(10, 30), 88, "W, 13, 19"),
        package.Package(17, "3148 S 1100 W", "Salt Lake City", "UT", 84119, package.Package.EOD_TIME, 2, None),
        package.Package(18, "1488 4800 S", "Salt Lake City", "UT", 84123, package.Package.EOD_TIME, 6, "T, 2"),
        package.Package(19, "177 W Price Ave", "Salt Lake City", "UT", 84115, package.Package.EOD_TIME, 37, None),
        package.Package(20, "3595 Main St", "Salt Lake City", "UT", 84115, datetime.time(10, 30), 37, "W, 13, 15"),
    ]
    for pkg in packages:
        pkg.special_note = pkg.parse_special_note()
        table.insert(pkg.package_id, pkg)
    handler = ph.PackageHandler()
    handler.merge_addresses()
    constraints_list = handler.build_constraints_list()
    handler.set_package_priorities(constraints_list)
    handler.handle_with_truck_note(constraints_list)
    fl = fleet.Fleet(2)
    handler.handle_delayed_without_deadline_note(constraints_list, fl)
    constraints_list = handler.handle_with_package_note(constraints_list)
    handler.add_and_prioritize_remaining_packages(constraints_list)
    monkeypatch.setattr(ph, "get_warehouse_hash", lambda: table)
    return constraints_list

def test_group_and_sort_list_creates_six_priority_groups(sample_unsorted_list):
    handler = ph.PackageHandler()
    ready_list = handler.group_and_sort_list(sample_unsorted_list)
    assert len(ready_list) == 6

def test_group_and_sort_list_ignores_packages_with_invalid_priority(sample_unsorted_list):
    invalid_priorities_list = sample_unsorted_list
    for pkg in invalid_priorities_list[:10]:
        pkg.priority = -1
    for pkg in invalid_priorities_list[10:]:
        pkg.priority = 6
    handler = ph.PackageHandler()
    ready_list = handler.group_and_sort_list(sample_unsorted_list)
    assert ready_list == [[] for i in range(6)]

@pytest.mark.parametrize(
    "priority, expected_index",
    [
        (0, 0),
        (1, 1),
        (2, 2),
        (3, 3),
        (4, 4),
        (5, 5)
    ]
)
def test_group_and_sort_list_places_packages_into_correct_priority_lists(priority, expected_index, sample_unsorted_list):
    for pkg in sample_unsorted_list:
        pkg.priority = priority
    handler = ph.PackageHandler()
    ready_list = handler.group_and_sort_list(sample_unsorted_list)
    assert len(ready_list[expected_index]) == len(sample_unsorted_list)

def test_group_and_sort_list_sorts_by_group_number_ascending(monkeypatch):
    table = hash_table.HashTable(size=8)
    monkeypatch.setattr(ph, "get_warehouse_hash", lambda: table)
    packages = [
        package.Package(1, "195 W Oakland Ave", "Salt Lake City", "UT", 84115, datetime.time(10, 30), 21, None),
        package.Package(2, "2530 S 500 E", "Salt Lake City", "UT", 84106, package.Package.EOD_TIME, 44, None),
        package.Package(3, "233 Canyon Rd", "Salt Lake City", "UT", 84103, package.Package.EOD_TIME, 2, "T, 2"),
        package.Package(4, "380 W 2880 S", "Salt Lake City", "UT", 84115, package.Package.EOD_TIME, 4, None),
        package.Package(5, "410 S State St", "Salt Lake City", "UT", 84111, package.Package.EOD_TIME, 5, None),
        package.Package(6, "3060 Lester St", "West Valley City", "UT", 84119, datetime.time(10, 30), 88, "D, 9:05 am"),
    ]
    for i, pkg in enumerate(packages):
        pkg.group = i
        pkg.priority = 0
    handler = ph.PackageHandler()
    ready_list = handler.group_and_sort_list(packages)[0]
    for i, curr_pkg in enumerate(ready_list[:-1]):
        next_pkg = ready_list[i+1]
        assert curr_pkg.group < next_pkg.group

def test_group_and_sort_list_sorts_by_group_number_when_frequencies_equal(monkeypatch):
    table = hash_table.HashTable(size=8)
    monkeypatch.setattr(ph, "get_warehouse_hash", lambda: table)
    packages = [
        package.Package(1, "195 W Oakland Ave", "Salt Lake City", "UT", 84115, datetime.time(10, 30), 21, None),
        package.Package(2, "2530 S 500 E", "Salt Lake City", "UT", 84106, package.Package.EOD_TIME, 44, None),
        package.Package(3, "233 Canyon Rd", "Salt Lake City", "UT", 84103, package.Package.EOD_TIME, 2, "T, 2"),
        package.Package(4, "380 W 2880 S", "Salt Lake City", "UT", 84115, package.Package.EOD_TIME, 4, None),
        package.Package(5, "410 S State St", "Salt Lake City", "UT", 84111, package.Package.EOD_TIME, 5, None),
        package.Package(6, "3060 Lester St", "West Valley City", "UT", 84119, datetime.time(10, 30), 88, "D, 9:05 am"),
    ]
    groups = [3, 1, 3, 1, None, None]
    for pkg, grp in zip(packages, groups):
        pkg.group = grp
        pkg.priority = 0
    handler = ph.PackageHandler()
    ready_list = handler.group_and_sort_list(packages)[0]
    group = [pkg.group for pkg in ready_list]
    assert group[:2] == [1, 1]
    assert group[2:4] == [3, 3]
    assert all(g is None for g in group[4:])

def test_group_and_sort_list_handles_none_group_values_last(monkeypatch):
    table = hash_table.HashTable(size=8)
    monkeypatch.setattr(ph, "get_warehouse_hash", lambda: table)
    packages = [
        package.Package(1, "195 W Oakland Ave", "Salt Lake City", "UT", 84115, datetime.time(10, 30), 21, None),
        package.Package(2, "2530 S 500 E", "Salt Lake City", "UT", 84106, package.Package.EOD_TIME, 44, None),
        package.Package(3, "233 Canyon Rd", "Salt Lake City", "UT", 84103, package.Package.EOD_TIME, 2, "T, 2"),
        package.Package(4, "380 W 2880 S", "Salt Lake City", "UT", 84115, package.Package.EOD_TIME, 4, None),
        package.Package(5, "410 S State St", "Salt Lake City", "UT", 84111, package.Package.EOD_TIME, 5, None),
        package.Package(6, "3060 Lester St", "West Valley City", "UT", 84119, datetime.time(10, 30), 88, "D, 9:05 am"),
    ]
    for pkg in packages[:]:
        pkg.group = None
        pkg.priority = 0
    packages[-1].group = 1
    handler = ph.PackageHandler()
    ready_list = handler.group_and_sort_list(packages)[0]
    assert ready_list[0].group is not None
    for pkg in ready_list[1:]:
        assert pkg.group is None

@pytest.mark.parametrize(
    "priority, expected_index",
    [
        (0, 0),
        (1, 1),
        (2, 2),
        (3, 3),
        (4, 4),
        (5, 5)
    ]
)
def test_group_and_sort_list_returns_empty_groups_when_no_packages_in_priority(priority, expected_index, sample_unsorted_list):
    for pkg in sample_unsorted_list:
        pkg.priority = priority
    handler = ph.PackageHandler()
    ready_list = handler.group_and_sort_list(sample_unsorted_list)
    ready_list.pop(expected_index)
    for group in ready_list:
        assert group == []

def test_group_and_sort_list_returns_empty_lists_for_empty_input(monkeypatch):
    table = hash_table.HashTable(size=8)
    monkeypatch.setattr(ph, "get_warehouse_hash", lambda: table)
    packages = []
    handler = ph.PackageHandler()
    ready_list = handler.group_and_sort_list(packages)
    assert len(ready_list) == 6
    assert all (group == [] for group in ready_list)

def test_group_and_sort_list_does_not_mutate_original_list(sample_unsorted_list):
    handler = ph.PackageHandler()
    before_ids = [pkg.package_id for pkg in sample_unsorted_list]
    before_objs = list(sample_unsorted_list)
    ready_list = handler.group_and_sort_list(sample_unsorted_list)
    after_ids = [pkg.package_id for pkg in sample_unsorted_list]
    after_objs = list(sample_unsorted_list)
    assert before_ids == after_ids
    assert before_objs == after_objs

def test_group_and_sort_list_handles_duplicate_group_numbers_correctly(monkeypatch):
    table = hash_table.HashTable(size=8)
    monkeypatch.setattr(ph, "get_warehouse_hash", lambda: table)
    packages = [
        package.Package(1, "195 W Oakland Ave", "Salt Lake City", "UT", 84115, datetime.time(10, 30), 21, None),
        package.Package(2, "2530 S 500 E", "Salt Lake City", "UT", 84106, package.Package.EOD_TIME, 44, None),
        package.Package(3, "233 Canyon Rd", "Salt Lake City", "UT", 84103, package.Package.EOD_TIME, 2, "T, 2"),
        package.Package(4, "380 W 2880 S", "Salt Lake City", "UT", 84115, package.Package.EOD_TIME, 4, None),
        package.Package(5, "410 S State St", "Salt Lake City", "UT", 84111, package.Package.EOD_TIME, 5, None),
        package.Package(6, "3060 Lester St", "West Valley City", "UT", 84119, datetime.time(10, 30), 88, "D, 9:05 am"),
    ]
    groups = [2, 1, 2, 1, 2, None]
    for pkg, grp in zip(packages, groups):
        pkg.group = grp
        pkg.priority = 0
    handler = ph.PackageHandler()
    ready_list = handler.group_and_sort_list(packages)[0]
    group = [pkg.group for pkg in ready_list]
    assert group[:3] == [2, 2, 2]
    assert group[3:5] == [1, 1]
    assert group[5] is None

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