# tests/test_hash_table.py
import hash_table
import package
import pytest

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

def test_init():
    table = hash_table.HashTable(20)
    assert len(table.table) == table.size

def test_init_invalid_size_raises():
    with pytest.raises(ValueError):
        hash_table.HashTable(-1)

@pytest.mark.parametrize("size, key, expected", [
    (5,  0, 0),
    (5,  1, 1),
    (5,  7, 2),
    (5, -1, 4),
    (8, 16, 0),
    (8, -9, 7),
])
def test_hash_with_valid_integer_key(size, key, expected):
    table = hash_table.HashTable(size)
    assert table.hash(key) == expected

def test_hash_with_non_integer_key_raises():
    table = hash_table.HashTable(5)
    with pytest.raises(ValueError):
        table.hash("One")


@pytest.mark.parametrize("key, obj", [
    (1, 'obj1'),
    (2, 'obj2'),
    (3, 'obj3'),
    (4, 'obj4'),
    (5, 'obj5'),
])
def test_insert_adds_package_to_correct_bucket(key, obj, sample_table):
    table = hash_table.HashTable(size=5)
    table.insert(key, obj)
    expected_index = table.hash(key)
    assert obj in table.table[expected_index]

def test_insert_duplicate_key_does_not_duplicate_object(sample_table):
    table, packages = sample_table
    obj = packages[0]
    idx = table.hash(obj.package_id)

    before_len = len(table.table[idx])
    table.insert(obj.package_id, obj)
    after_len  = len(table.table[idx])

    assert after_len == before_len
    assert table.table[idx].count(obj) == 1

@pytest.mark.parametrize("index", [0, 1, 2])
def test_search_returns_correct_package(index, sample_table):
    table, packages = sample_table
    assert table.search(packages[index].package_id) == packages[index]

@pytest.mark.parametrize("key", [4, 5, 6])
def test_search_returns_none_for_missing_key(key, sample_table):
    table, _ = sample_table
    assert table.search(key) is None
    
def test_lookup_function_returns_correct_tuple(sample_table):
    table, packages = sample_table
    for item in packages:
        assert table.lookup_function(item.package_id) == (item.address, item.delivery_deadline, item.city, item.zip_code, item.weight_kilo, item.delivery_status)

@pytest.mark.parametrize("key", [4, 5, 6])
def test_lookup_function_returns_none_for_invalid_key(key, sample_table):
    table, _ = sample_table
    assert table.lookup_function(key) is None

def test_remove_existing_object_returns_true(sample_table):
    table, packages = sample_table
    for pkg in packages:
        assert table.remove(pkg.package_id, pkg) is True

@pytest.mark.parametrize("key", [101, 102, 103])
def test_remove_nonexistent_object_returns_false(sample_table, key):
    table, _ = sample_table
    ghost = package.Package(key, "Z Rd", "Nowhere", "ST", "00000", "EOD", 1, "None")
    assert table.remove(key, ghost) is False
    
def test_print_hash_table_outputs_only_nonempty_buckets(sample_table, capsys):
    table, _ = sample_table
    table.print_hash_table()
    out = capsys.readouterr().out
    
    assert "  Bucket 1:" in out
    assert "  Bucket 2:" in out
    assert "  Bucket 3:" in out
    assert "  Bucket 4:" not in out    
    assert "  Bucket 4:" not in out     

def test_collision_handling_all_items_retrievable(sample_table):
    _, packages = sample_table
    table = hash_table.HashTable(2)
    
    for package in packages:
        table.insert(package.package_id, package)
    
    assert table.search(1) == packages[0]
    assert table.search(2) == packages[1]
    assert table.search(3) == packages[2]

def test_empty_table_iteration_yields_nothing():
    empty_table = hash_table.HashTable(5)
    for empty_bucket in empty_table:
        assert len(empty_bucket) == 0

def test_overwrite_behavior_replaces_existing_entry(sample_table):
    table, package_list= sample_table
    ghost1 = package.Package(1, "Z Rd", "Nowhere", "ST", "00000", "EOD", 1, "None")
    ghost2 = package.Package(2, "Z Rd", "Nowhere", "ST", "00000", "EOD", 1, "None")
    ghost3 = package.Package(3, "Z Rd", "Nowhere", "ST", "00000", "EOD", 1, "None")
    
    table.insert(ghost1.package_id, ghost1)
    table.insert(ghost2.package_id, ghost2)
    table.insert(ghost3.package_id, ghost3)
    
    assert table.search(1).address != "Z Rd"
    assert table.search(2).address != "Z Rd"
    assert table.search(3).address != "Z Rd"