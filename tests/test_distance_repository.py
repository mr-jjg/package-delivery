# tests/test_distance_repository.py

import pytest
import distance_repository as dr

@pytest.fixture(autouse=True)
def reset_repository_state(monkeypatch):
    monkeypatch.setattr(dr, "distance_matrix", None, raising=False)

@pytest.fixture
def distances():
    return [
        [0,1,2,3,4],
        [1,0,1,2,3],
        [2,1,0,1,2],
        [3,2,1,0,1],
        [4,3,2,1,0]
    ]

@pytest.mark.parametrize("too_small", [[], [0]])
def test_set_distance_matrix_must_have_at_least_two_addresses(too_small):
    with pytest.raises(ValueError):
        dr.set_distance_matrix(too_small)

def test_set_distance_matrix_accepts_floats_and_inf():
    inf = float('inf')
    distances = [
        [0.0, 1.5, inf],
        [1.5, 0.0, 2.0],
        [inf, 2.0, 0.0]
    ]
    dr.set_distance_matrix(distances)
    assert dr.get_distance_matrix() is distances

def test_set_distance_matrix_rejects_assymetric_matrix(distances):
    bad1 = distances + [5,4,3,2,1,0]
    bad2 = [
        [0,1,2],
        [1,0],
        [2,1,0,9],
    ]
    with pytest.raises(ValueError):
        dr.set_distance_matrix(bad1)
    with pytest.raises(ValueError):
        dr.set_distance_matrix(bad2)

def test_set_distance_matrix_rejects_non_numeric_distances():
    bad = [
        [0,1,2,3,4],
        [1,0,1,2,3],
        [2,1,0,1,2],
        [3,2,1,0,1],
        [4,3,2,1,"0"]
    ]
    with pytest.raises(ValueError):
        dr.set_distance_matrix(bad)

def test_set_then_get_returns_same_object_identity(distances):
    dr.set_distance_matrix(distances)
    assert dr.get_distance_matrix() is distances

def test_set_overwrites_previous_value(distances):
    distances1 = distances
    distances2 = [[0,10],[10,0]]
    
    dr.set_distance_matrix(distances1)
    assert dr.get_distance_matrix() is distances1
    dr.set_distance_matrix(distances2)
    assert dr.get_distance_matrix() is distances2

def test_mutating_original_object_reflects_in_repository(distances):
    dr.set_distance_matrix(distances)
    distances[0][4] = 5
    distances[4][0] = 5
    repo = dr.get_distance_matrix()
    assert repo[0][4] == 5
    assert repo[4][0] == 5

def test_cannot_set_to_none_explicitly(distances):
    dr.set_distance_matrix(distances)
    with pytest.raises(ValueError):
        dr.set_distance_matrix(None)

def test_get_distance_matrix_requires_initialization():
    with pytest.raises(RuntimeError):
        dr.get_distance_matrix()

def test_print_distance_matrix(distances, capsys):
    dr.print_distance_matrix(distances)
    out = capsys.readouterr()
    
    assert any("0.0 |  1.0 |  2.0 |  3.0 |  4.0\n" in line for line in out)
    assert any("1.0 |  0.0 |  1.0 |  2.0 |  3.0\n" in line for line in out)
    assert any("2.0 |  1.0 |  0.0 |  1.0 |  2.0\n" in line for line in out)
    assert any("3.0 |  2.0 |  1.0 |  0.0 |  1.0\n" in line for line in out)
    assert any("4.0 |  3.0 |  2.0 |  1.0 |  0.0\n" in line for line in out)

def test_get_distance_returns_correct_distance(distances, monkeypatch):
    monkeypatch.setattr(dr, "address_to_index", lambda x: x)
    dr.set_distance_matrix(distances)

    for a in range(3):
        for b in range(3):
            assert dr.get_distance(a, b) == distances[a][b]

def test_get_distance_with_string_addresses(distances, monkeypatch):
    mapping = {"HUB": 0, "A": 1, "B": 2}
    monkeypatch.setattr(dr, "address_to_index", lambda x: mapping[x])
    dr.set_distance_matrix(distances)
    
    assert dr.get_distance("HUB", "B") == distances[0][2]
    assert dr.get_distance("A", "A") == distances[1][1]