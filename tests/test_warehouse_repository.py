# tests/test_warehouse_repository.py

import pytest
import warehouse_repository as wr
import package
import hash_table

@pytest.fixture(autouse=True)
def reset_repository_state(monkeypatch):
    monkeypatch.setattr(wr, "warehouse_hash", None, raising=False)
    monkeypatch.setattr(wr, "warehouse_base", None, raising=False)

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

def test_initial_state_is_none():
	assert wr.get_warehouse_hash() is None

def test_set_then_get_returns_same_object_identity(sample_table):
    table, _ = sample_table
    wr.set_warehouse_hash(table)
    assert wr.get_warehouse_hash() is table
    
def test_set_overwrites_previous_value(sample_table):
    table1, _ = sample_table
    table2 = hash_table.HashTable(size=2)
    packages = [
        package.Package(4, "321 Birch Lane", "Peoria", "IL", "61602", "12:00 PM", 3.3, "None"),
        package.Package(5, "654 Cedar Street", "Champaign", "IL", "61820", "4:00 PM", 4.8, "None")
    ]
    for pkg in packages:
        table2.insert(pkg.package_id, pkg)
    
    wr.set_warehouse_hash(table1)
    assert wr.get_warehouse_hash() is table1
    wr.set_warehouse_hash(table2)
    assert wr.get_warehouse_hash() is table2

@pytest.mark.parametrize("bad", ["BAD_DATA", 123, 3.14, object()])
def test_only_accepts_hash_table_type(bad):
    with pytest.raises(ValueError) as exc_info:
        wr.set_warehouse_hash(bad)

def test_mutating_original_object_reflects_in_repository(sample_table):
    table, _ = sample_table
    wr.set_warehouse_hash(table)
    mutant = package.Package(6, "987 Elm Street", "Decatur", "IL", "62521", "3:00 PM", 2.0, "None")
    table.insert(mutant.package_id, mutant)
    assert wr.get_warehouse_hash().search(6) is mutant

def test_cannot_set_to_none_explicitly(sample_table):
    table, _ = sample_table
    wr.set_warehouse_hash(table)
    with pytest.raises(ValueError) as exc_info:
        wr.set_warehouse_hash(None)

@pytest.mark.parametrize("bad", ["BAD_DATA", 123, 3.14, object(), None])
def test_set_warehouse_base_only_accepts_hash_table_type(bad):
    with pytest.raises(ValueError):
        wr.set_warehouse_base(bad)

def test_set_warehouse_base_stores_deep_copy_not_same_identity(sample_table):
    table, _ = sample_table
    wr.set_warehouse_base(table)

    assert wr.warehouse_base is not None
    assert wr.warehouse_base is not table

def test_set_warehouse_base_is_immune_to_mutations_of_original_input(sample_table):
    table, _ = sample_table
    wr.set_warehouse_base(table)

    # mutate original after snapshot
    mutant = package.Package(99, "999 Z St", "Nowhere", "NA", "00000", "EOD", 1, "None")
    table.insert(mutant.package_id, mutant)

    # base should not see the mutant
    assert wr.warehouse_base.search(99) is None

def test_set_warehouse_base_overwrites_previous_value(sample_table):
    table1, _ = sample_table

    table2 = hash_table.HashTable(size=2)
    p4 = package.Package(4, "321 Birch Lane", "Peoria", "IL", "61602", "12:00 PM", 3.3, "None")
    table2.insert(p4.package_id, p4)

    wr.set_warehouse_base(table1)
    base1 = wr.warehouse_base

    wr.set_warehouse_base(table2)
    base2 = wr.warehouse_base

    assert base1 is not base2
    assert base2.search(4) is not None
    assert base2.search(1) is None  # from table1 snapshot should not be present

def test_reset_warehouse_raises_if_base_not_set():
    with pytest.raises(RuntimeError):
        wr.reset_warehouse()

def test_reset_warehouse_sets_hash_to_deep_copy_of_base(sample_table):
    table, _ = sample_table
    wr.set_warehouse_base(table)

    wr.reset_warehouse()

    assert wr.get_warehouse_hash() is not None
    assert wr.get_warehouse_hash() is not wr.warehouse_base  # not same identity
    assert wr.get_warehouse_hash().search(1) is not None     # has expected content

def test_reset_warehouse_produces_independent_copy(sample_table):
    table, _ = sample_table
    wr.set_warehouse_base(table)

    wr.reset_warehouse()
    wh = wr.get_warehouse_hash()

    # mutate warehouse_hash
    mutant = package.Package(77, "77 Reset Rd", "Resetville", "RS", "77777", "EOD", 1, "None")
    wh.insert(mutant.package_id, mutant)

    # base should not see this mutation
    assert wr.warehouse_base.search(77) is None

def test_multiple_resets_produce_new_instances(sample_table):
    table, _ = sample_table
    wr.set_warehouse_base(table)

    wr.reset_warehouse()
    wh1 = wr.get_warehouse_hash()

    wr.reset_warehouse()
    wh2 = wr.get_warehouse_hash()

    assert wh1 is not wh2