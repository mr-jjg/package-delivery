# tests/test_warehouse_repository.py

import pytest
import warehouse_repository as wr
import package
import hash_table

@pytest.fixture(autouse=True)
def reset_repository_state(monkeypatch):
    monkeypatch.setattr(wr, "warehouse_hash", None, raising=False)

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
    with pytest.raises(Exception) as exc_info:
        wr.set_warehouse_hash(None)