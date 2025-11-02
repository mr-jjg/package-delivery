# tests/test_address_repository.py

import pytest
import address_repository as ar

@pytest.fixture(autouse=True)
def reset_repository_state(monkeypatch):
    monkeypatch.setattr(ar, "address_list", None, raising=False)

@pytest.fixture
def sample_table():
    addresses = [
        [1, "The Spokane Club", "1002 W Riverside Ave"],
        [2, "Davenport Hotel", "10 S Post St"],
        [3, "Manito Park", "1702 S Grand Blvd"],
        [4, "Joe Albi Stadium", "5701 N Assembly St"],
        [5, "Gonzaga University", "502 E Boone Ave"]        
    ]
    return addresses

def test_initial_state_is_none():
	assert ar.get_address_list() is None
    
def test_accepts_empty_list():
    ar.set_address_list([])
    assert ar.get_address_list() == []

def test_set_then_get_returns_same_object_identity(sample_table):
    addresses = sample_table
    ar.set_address_list(addresses)
    assert ar.get_address_list() is addresses

def test_set_overwrites_previous_value(sample_table):
    addresses1 = sample_table
    addresses2 = [
        [6, "Riverfront Park", "507 N Howard St"],
        [7, "Spokane Falls", "3410 W Whistalks Wy"],
    ]
    
    ar.set_address_list(addresses1)
    assert ar.get_address_list() is addresses1
    ar.set_address_list(addresses2)
    assert ar.get_address_list() is addresses2

@pytest.mark.parametrize("bad", ["BAD_DATA", 123, 3.14, object()])
def test_only_accepts_list_type(bad):
    with pytest.raises(ValueError) as exc_info:
        ar.set_address_list(bad)

def test_mutating_original_object_reflects_in_repository(sample_table):
    addresses = sample_table
    ar.set_address_list(addresses)
    mutant = [6, "Super Wash Laundromat", "1632 W 2nd Ave"]
    addresses.append(mutant)
    assert ar.get_address_list()[5] is mutant

def test_cannot_set_to_none_explicitly(sample_table):
    addresses = sample_table
    ar.set_address_list(addresses)
    with pytest.raises(ValueError) as exc_info:
        ar.set_address_list(None)

def test_address_to_index_returns_correct_address(sample_table):
    addresses = sample_table
    ar.set_address_list(addresses)
    for i, address in enumerate(addresses):
        assert ar.address_to_index(address[2]) == i + 1

@pytest.mark.parametrize("bad", ["1001 W Sprague Ave", "720 W Mallon Ave", "2810 S Regal St", "3401 W Woodland Blvd"])
def test_address_to_index_returns_none_on_not_found(sample_table, bad):
    addresses = sample_table
    ar.set_address_list(addresses)
    assert ar.address_to_index(bad) is None

def test_index_to_address_returns_correct_index(sample_table):
    addresses = sample_table
    ar.set_address_list(addresses)
    for i, address in enumerate(addresses):
        assert ar.index_to_address(i + 1) == address[2]

@pytest.mark.parametrize("bad", ["BAD_DATA", 123, 3.14, object()])
def test_index_to_address_returns_none_on_not_found(sample_table, bad):
    addresses = sample_table
    ar.set_address_list(addresses)
    assert ar.index_to_address(bad) is None