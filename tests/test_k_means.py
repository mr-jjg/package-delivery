# /tests/test_k_means.py
import k_means as km
import package
import pytest
import random

def make_pkg(id_, address):
    pkg = package.Package(id_, address, "City", "ST", 99999, None, 1.0, None, "at_the_hub", None, None, 0, 0)
    return pkg

class DummyTruck:
    def __init__(self, current_capacity):
        self.current_capacity = current_capacity

@pytest.fixture
def fake_world(monkeypatch):
    address_list = [
        [0, "_", "Address0"],
        [1, "_", "Address1"],
        [2, "_", "Address2"],
        [3, "_", "Address3"],
        [4, "_", "Address4"],
    ]

    distance_matrix = [
        [0, 1, 2, 3, 4],
        [1, 0, 1, 2, 3],
        [2, 1, 0, 1, 2],
        [3, 2, 1, 0, 1],
        [4, 3, 2, 1, 0],
    ]

    def fake_get_address_list():
        return address_list

    def fake_get_distance_matrix():
        return distance_matrix

    def fake_address_to_index(address, addr_list):
        for row in addr_list:
            if row[2] == address:
                return int(row[0])
        raise KeyError(f"Unknown address: {address}")

    monkeypatch.setattr(km, "get_address_list", fake_get_address_list)
    monkeypatch.setattr(km, "get_distance_matrix", fake_get_distance_matrix)
    monkeypatch.setattr(km, "address_to_index", fake_address_to_index)
    monkeypatch.setattr(km, "print_group_list", lambda *_: None)

    return {
        "address_list": address_list,
        "distance_matrix": distance_matrix,
        "address_to_index": fake_address_to_index,
    }

class TestSelectUniquePackage:
    def test_select_unique_package_address_returns_k_unique_addresses(self, monkeypatch):
        pkgs = [
            make_pkg(0, "Address0"),
            make_pkg(1, "Address1"),
            make_pkg(2, "Address2"),
            make_pkg(3, "Address3"),
        ]

        chosen = km.select_unique_package_address(pkgs, 3)
        addresses = [p.address for p in chosen]

        assert len(chosen) == 3
        assert len(set(addresses)) == 3

    def test_select_unique_package_address_retires_until_unique(self, monkeypatch):
        pkgs = [
            make_pkg(0, "Address0"),
            make_pkg(1, "Address0"),
            make_pkg(2, "Address1"),
            make_pkg(3, "Address2"),
        ]

        # Force collisions first: Address0 twice, then unique ones
        seq = [pkgs[0], pkgs[1], pkgs[2], pkgs[3]]
        calls = {"count": 0}

        def fake_choice(_list):
            calls["count"] += 1
            return seq.pop(0)

        monkeypatch.setattr(random, "choice", fake_choice)

        chosen = km.select_unique_package_address(pkgs, 3)
        addresses = [p.address for p in chosen]

        assert len(chosen) == 3
        assert set(addresses) == {"Address0", "Address1", "Address2"}
        assert calls["count"] >= 4


class TestFindNewCentroid:
    def test_find_new_centroid_picks_candidate_with_min_total_distance(self, monkeypatch):
        # Custom world for precise centroid selection
        address_list = [
            [0, "_", "A0"],
            [1, "_", "A1"],
            [2, "_", "A2"],
        ]

        # Candidate sums:
        # A0: 0->A1=5, 0->A2=1 => 6
        # A1: 1->A0=5, 1->A2=1 => 6
        # A2: 2->A0=1, 2->A1=1 => 2  (minimum)
        distance_matrix = [
            [0, 5, 1],
            [5, 0, 1],
            [1, 1, 0],
        ]

        def fake_get_address_list():
            return address_list

        def fake_get_distance_matrix():
            return distance_matrix

        def fake_address_to_index(address, addr_list):
            for row in addr_list:
                if row[2] == address:
                    return int(row[0])
            raise KeyError(address)

        monkeypatch.setattr(km, "get_address_list", fake_get_address_list)
        monkeypatch.setattr(km, "get_distance_matrix", fake_get_distance_matrix)
        monkeypatch.setattr(km, "address_to_index", fake_address_to_index)

        p0 = make_pkg(0, "A0")
        p1 = make_pkg(1, "A1")
        p2 = make_pkg(2, "A2")

        centroid = km.find_new_centroid([p0, p1, p2])

        assert centroid is p2


class TestKMeansClustering:
    def test_k_means_clustering_returns_k_clusters_and_partitions_all_packages(self, monkeypatch, fake_world):
        pkgs = [
            make_pkg(0, "Address0"),
            make_pkg(1, "Address1"),
            make_pkg(2, "Address2"),
            make_pkg(3, "Address3"),
        ]

        # Deterministic initial centroids: pick Address0 and Address3
        monkeypatch.setattr(km, "select_unique_package_address", lambda _pkgs, k: [pkgs[0], pkgs[3]])

        clusters = km.k_means_clustering(pkgs, 2)

        assert len(clusters) == 2

        flattened = [p for cluster in clusters for p in cluster]
        assert len(flattened) == len(pkgs)
        assert set(flattened) == set(pkgs)

        assert len(flattened) == len(set(flattened))

    def test_k_means_clusteringsorts_clusters_by_size_desc(self, monkeypatch, fake_world):
        pkgs = [
            make_pkg(0, "Address0"),
            make_pkg(1, "Address1"),
            make_pkg(2, "Address2"),
            make_pkg(3, "Address3"),
            make_pkg(4, "Address4"),
        ]

        # Centroids force 4 items near Address0, 1 item near Address4
        monkeypatch.setattr(km, "select_unique_package_address", lambda _pkgs, k: [pkgs[0], pkgs[4]])

        clusters = km.k_means_clustering(pkgs, 2)

        sizes = [len(c) for c in clusters]
        assert sizes == sorted(sizes, reverse=True)

    def test_k_means_clustering_converges_with_deterministic_centroids(self, monkeypatch, fake_world):
        pkgs = [
            make_pkg(0, "Address0"),
            make_pkg(1, "Address1"),
            make_pkg(2, "Address2"),
            make_pkg(3, "Address3"),
        ]

        calls = {"select": 0, "centroid": 0}

        def fake_select_unique(_pkgs, k):
            calls["select"] += 1
            return [pkgs[0], pkgs[3]]

        def wrapped_find_new_centroid(cluster):
            calls["centroid"] += 1
            return km.find_new_centroid.__wrapped__(cluster)  # will fail if not set below

        # Preserve original function so we can count calls without changing behavior
        original_find_new_centroid = km.find_new_centroid

        def counting_find_new_centroid(cluster):
            calls["centroid"] += 1
            return original_find_new_centroid(cluster)

        monkeypatch.setattr(km, "select_unique_package_address", fake_select_unique)
        monkeypatch.setattr(km, "find_new_centroid", counting_find_new_centroid)

        clusters = km.k_means_clustering(pkgs, 2)

        assert calls["select"] == 1
        assert calls["centroid"] >= 2
        assert len(clusters) == 2


class TestSplitPackageList:
    def test_split_package_list_case1_first_group_fits(self, monkeypatch):
        truck = DummyTruck(current_capacity=3)
        package_groups = []

        p0 = make_pkg(0, "Address0")
        p1 = make_pkg(1, "Address1")
        p2 = make_pkg(2, "Address2")
        p3 = make_pkg(3, "Address3")
        package_list = [p0, p1, p2, p3]

        group0 = [p0, p1, p2]  # fits capacity 3
        group1 = [p3]          # returned
        monkeypatch.setattr(km, "k_means_clustering", lambda pkgs, k: [group0, group1])

        result = km.split_package_list(truck, package_groups, package_list)

        assert result == group0
        assert package_groups[0] == group1

    def test_split_package_list_case2_second_group_fits(self, monkeypatch):
        truck = DummyTruck(current_capacity=2)
        package_groups = []

        p0 = make_pkg(0, "Address0")
        p1 = make_pkg(1, "Address1")
        p2 = make_pkg(2, "Address2")
        p3 = make_pkg(3, "Address3")
        package_list = [p0, p1, p2, p3]

        group0 = [p0, p1, p2]  # does not fit
        group1 = [p3, p2]      # fits
        monkeypatch.setattr(km, "k_means_clustering", lambda pkgs, k: [group0, group1])

        result = km.split_package_list(truck, package_groups, package_list)

        assert result == group1
        assert package_groups[0] == group0

    def test_split_package_list_case3_neither_fits_repeats_and_returns_smaller_group(self, monkeypatch):
        truck = DummyTruck(current_capacity=1)
        package_groups = []

        p0 = make_pkg(0, "Address0")
        p1 = make_pkg(1, "Address1")
        p2 = make_pkg(2, "Address2")
        p3 = make_pkg(3, "Address3")
        package_list = [p0, p1, p2, p3]

        # First call: neither group fits (both size 2)
        # Second call: first group fits (size 1)
        groups = [
            ([p0, p1], [p2, p3]),
            ([p0], [p1]),
        ]
        calls = {"count": 0}

        def fake_k_means(pkgs, k):
            calls["count"] += 1
            g0, g1 = groups.pop(0)
            return [g0, g1]

        monkeypatch.setattr(km, "k_means_clustering", fake_k_means)

        result = km.split_package_list(truck, package_groups, package_list)

        assert calls["count"] == 2
        assert result == [p0]
        assert package_groups[0] == [p2, p3, p1]