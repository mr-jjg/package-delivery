# tests/test_nearest_neighbor.py
import pytest
import nearest_neighbor as nn
import package

@pytest.fixture
def pkg_list():
    pkgs = []
    for i in range(4):
        pkgs.append(package.Package(i, f"Address{i}", "City", "ST", 99999, None, 1.0, None, "at_the_hub", None, None, 0, 0))
    return pkgs

@pytest.fixture
def fake_world():
    address_list = [
        [0, "_", "Address0"],
        [1, "_", "Address1"],
        [2, "_", "Address2"],
        [3, "_", "Address3"],
    ]
    distance_matrix = [
        [0, 1, 2, 3],
        [1, 0, 3, 2],
        [2, 3, 0, 1],
        [3, 2, 1, 0],
    ]

    def address_to_index(address: str):
        for row in address_list:
            if row[2] == address:
                return int(row[0])
        raise KeyError(f"Unknown address: {address}")

    return {
        "address_list": address_list,
        "distance_matrix": distance_matrix,
        "address_to_index": address_to_index,
    }

@pytest.fixture
def patch_nn(monkeypatch, fake_world, pkg_list):
    monkeypatch.setattr(nn, "get_address_list", lambda: fake_world["address_list"])
    monkeypatch.setattr(nn, "get_distance_matrix", lambda: fake_world["distance_matrix"])
    monkeypatch.setattr(nn, "address_to_index", fake_world["address_to_index"])

    def convert_route_to_package_list(route):
        by_id = {p.package_id: p for p in pkg_list}
        out = []
        for package_id, _addr_index in route:
            if package_id is not None:
                out.append(by_id[package_id])
        return out

    monkeypatch.setattr(nn, "convert_route_to_package_list", convert_route_to_package_list)
    return True

def test_build_vertices_list_excludes_start_point_packages(pkg_list, monkeypatch, fake_world):
    start_point = "Address0"
    monkeypatch.setattr(nn, "address_to_index", fake_world["address_to_index"])

    v_list = nn.build_vertices_list(pkg_list, start_point)

    assert len(v_list) == 3
    package_ids = [pkg_id for (pkg_id, _idx) in v_list]
    assert 0 not in package_ids

def test_nearest_neighbor_returns_sum_and_route_in_expected_order_simple_case(pkg_list, patch_nn):
    route_sum, route = nn.nearest_neighbor(pkg_list, "Address0")

    assert route_sum == 6
    assert [p.address for p in route] == ["Address1", "Address3", "Address2"]

def test_nearest_neighbor_includes_return_to_start_in_route_sum(pkg_list, monkeypatch, fake_world):
    monkeypatch.setattr(nn, "get_address_list", lambda: fake_world["address_list"])
    monkeypatch.setattr(nn, "address_to_index", fake_world["address_to_index"])

    distance_matrix = [
        [0, 1, 1, 1],
        [1, 0, 1, 1],
        [1, 1, 0, 1],
        [50, 1, 1, 0],
    ]
    monkeypatch.setattr(nn, "get_distance_matrix", lambda: distance_matrix)

    by_id = {p.package_id: p for p in pkg_list}
    monkeypatch.setattr(
        nn,
        "convert_route_to_package_list",
        lambda visited: [by_id[i] for (i, _idx) in visited if i is not None],
    )

    route_sum, _route = nn.nearest_neighbor(pkg_list, "Address0")

    assert route_sum >= 50

def test_nearest_neighbor_handles_empty_package_list(monkeypatch, fake_world):
    empty_pkg_list = []

    monkeypatch.setattr(nn, "get_address_list", lambda: fake_world["address_list"])
    monkeypatch.setattr(nn, "get_distance_matrix", lambda: fake_world["distance_matrix"])
    monkeypatch.setattr(nn, "address_to_index", fake_world["address_to_index"])
    monkeypatch.setattr(nn, "convert_route_to_package_list", lambda visited: [])

    route_sum, route = nn.nearest_neighbor(empty_pkg_list, "Address0")

    assert route_sum == 0
    assert route == []

def test_nearest_neighbor_all_packages_included_even_if_addresses_repeat(pkg_list, patch_nn):
    pkg_list[2].address = "Address1"

    route_sum, route = nn.nearest_neighbor(pkg_list, "Address0")

    ids = [p.package_id for p in route]
    assert sorted(ids) == [1, 2, 3]
    assert len(ids) == len(set(ids))