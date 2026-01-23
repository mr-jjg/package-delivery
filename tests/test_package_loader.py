# /tests/test_package_loader.py
# Test for shape, state changes, branching/conditions, interactions

import pytest
import package
import package_loader as pl
import truck
import fleet

class NullReporter:
    def __init__(self, verbosity=0):
        self.verbosity = verbosity

    def report(self, level, msg):
        pass

@pytest.fixture
def fake_split(monkeypatch):
    """
    Provides a deterministic fake split_package_list for tests that 
    need to avoid k-means and the distance matrix.
    """
    def _fake_split(truck, groups, working_list):
        keep = working_list[:truck.current_capacity]
        leftover = working_list[truck.current_capacity:]
        groups.insert(0, leftover)

        return keep

    monkeypatch.setattr(pl, "split_package_list", _fake_split)
    return _fake_split

def fake_nearest_neighbor(monkeypatch, distance=42.0, route=None):
    def _fake(pkg_list):
        return distance, route or pkg_list

    monkeypatch.setattr(pl, "nearest_neighbor", _fake)
    return _fake

def make_pkg(id_, group=None, priority=None):
    return package.Package(id_, "Address", "City", "ST", 99999, None, 1.0, None, "at_the_hub", None, None, group, priority)

def make_truck_route_dist(route_len=4, dist=99.0):
        tr = truck.Truck(1)
        route = [make_pkg(i) for i in range(1, route_len + 1)]
        return tr, route, dist

class TestHelpers:
    def test_adjust_working_list_for_capacity_truck_can_fit_full_list(self, monkeypatch):
        t1, t2 = truck.Truck(), truck.Truck()
        t1.truck_id, t2.truck_id = 1, 2
        t1.current_capacity, t2.current_capacity = 4, 3
        truck_list = [t1, t2]

        working_package_list = [make_pkg(n) for n in range(4)]
        package_groups = []

        def _should_not_be_called(*args, **kwargs):
            raise AssertionError("split_package_list should not be called on full-fit path")
        monkeypatch.setattr(pl, "split_package_list", _should_not_be_called)

        new_working_package_list, available_trucks = pl.adjust_working_list_for_capacity(truck_list, package_groups, working_package_list, "0")

        assert new_working_package_list == working_package_list
        assert [pkg.package_id for pkg in new_working_package_list] == [0, 1, 2, 3]
        assert len(package_groups) == 0
        assert t1 in available_trucks
        assert len(available_trucks) == 1
        assert available_trucks[0].current_capacity >= len(new_working_package_list)

    def test_adjust_working_list_for_capacity_splits_when_no_truck_can_fit_full_list(self, monkeypatch, fake_split):
        t1, t2 = truck.Truck(), truck.Truck()
        t1.truck_id, t2.truck_id = 1, 2
        t1.current_capacity, t2.current_capacity = 2, 3
        truck_list = [t1, t2]

        working_package_list = [make_pkg(n) for n in range(4)]
        package_groups = []

        monkeypatch.setattr(pl, "has_w_note", lambda pkg_list: False)

        new_working_package_list, available_trucks = pl.adjust_working_list_for_capacity(truck_list, package_groups, working_package_list, "0")

        assert new_working_package_list == working_package_list[: t2.current_capacity]
        assert [pkg.package_id for pkg in new_working_package_list] == [0, 1, 2]
        assert package_groups[0][0].package_id == 3
        assert t2 in available_trucks
        assert available_trucks[0].current_capacity >= len(new_working_package_list)

    def test_adjust_working_list_for_capacity_fails_on_has_w_note(self):
        t1, t2 = truck.Truck(), truck.Truck()
        t1.truck_id, t2.truck_id = 1, 2
        t1.current_capacity, t2.current_capacity = 2, 3
        truck_list = [t1, t2]

        working_package_list = [make_pkg(n) for n in range(4)]
        working_package_list[0].special_note = ["W", 1]
        working_package_list[1].special_note = ["W", 0]
        package_groups = []

        with pytest.raises(SystemExit):
            new_working_package_list, available_trucks = pl.adjust_working_list_for_capacity(truck_list, package_groups, working_package_list, "0")

    def test_adjust_working_list_for_capacity_fails_on_all_trucks_with_zero_capacity(self):
        t1, t2 = truck.Truck(), truck.Truck()
        t1.truck_id, t2.truck_id = 1, 2
        t1.current_capacity, t2.current_capacity = 0, 0
        truck_list = [t1, t2]

        working_package_list = [make_pkg(n) for n in range(4)]
        package_groups = []

        with pytest.raises(SystemExit):
            new_working_package_list, available_trucks = pl.adjust_working_list_for_capacity(truck_list, package_groups, working_package_list, "0")

    def test_build_working_package_list_happy_path(self):
        package_groups = [
            [
                make_pkg(1, 2, 0), 
                make_pkg(2, 2, 0), 
                make_pkg(3, 1, 0), 
                make_pkg(4, None, 0)
            ]
        ]
        wpl = pl.build_working_package_list(package_groups)
        ids = [pkg.package_id for pkg in wpl]
        assert ids == [1, 2]

    def test_build_working_package_list_first_group_emptied_and_popped(self):
        package_groups = [
            [
                make_pkg(1, 3, 1), 
                make_pkg(2, 3, 1), 
                make_pkg(3, 3, 1)
            ],
            [
                make_pkg(4, 4, 2)
            ]
        ]
        second = package_groups[1]
        wpl = pl.build_working_package_list(package_groups)
        ids = [pkg.package_id for pkg in wpl]
        assert ids == [1, 2, 3]
        assert package_groups == [second]

    def test_build_working_package_list_no_group_priority_not_zero(self):
        package_groups = [
            [
                make_pkg(1, None, 2), 
                make_pkg(2, 4, 2), 
                make_pkg(3, 5, 2)
            ]
        ]
        len_before = len(package_groups)
        expected = package_groups[0][1:]
        wpl = pl.build_working_package_list(package_groups)
        len_after = len(package_groups)
        ids = [pkg.package_id for pkg in wpl]
        assert ids == [1]
        assert len_before == len_after
        assert package_groups[0] == expected
        
    def test_build_working_package_list_no_group_priority_zero(self):
        package_groups = [
            [
                make_pkg(1, None, 0), 
                make_pkg(2, None, 0), 
                make_pkg(3, None, 0), 
                make_pkg(4, 1, 0)
            ]
        ]
        wpl = pl.build_working_package_list(package_groups)
        ids = [pkg.package_id for pkg in wpl]
        assert [pkg.package_id for pkg in package_groups[0]] == [4]
        for pkg in wpl:
            assert pkg.group is None

    def test_get_trucks_with_available_capacity_happy_path(self):
        truck_list = [
            truck.Truck(1),
            truck.Truck(2)
        ]
        truck_list[0].current_capacity = 0
        truck_list[1].current_capacity = 2
        twac = pl.get_trucks_with_available_capacity(truck_list, 1)
        ids = [t.truck_id for t in twac]
        assert ids == [2]

    def test_get_trucks_with_available_capacity_unhappy_path(self):
        truck_list = [
            truck.Truck(1),
            truck.Truck(2)
        ]
        truck_list[0].current_capacity = 0
        truck_list[1].current_capacity = 0
        twac = pl.get_trucks_with_available_capacity(truck_list, 1)
        ids = [t.truck_id for t in twac]
        assert ids == []

    def test_get_trucks_with_available_capacity_current_capacity_equals_list_length(self):
        truck_list = [
            truck.Truck(1)
        ]
        truck_list[0].current_capacity = 2
        twac = pl.get_trucks_with_available_capacity(truck_list, 2)
        ids = [t.truck_id for t in twac]
        assert ids == [1]

    def test_get_trucks_with_available_capacity_empty_truck_list_throws_value_error(self):
        truck_list = []
        twac = pl.get_trucks_with_available_capacity(truck_list, 2)
        assert twac == []

    def test_get_trucks_with_available_capacity_no_packages_returns_all_trucks(self):
        truck_list = [truck.Truck(n) for n in range(3)]
        twac = pl.get_trucks_with_available_capacity(truck_list, 0)
        ids = [t.truck_id for t in twac]
        assert ids == [0, 1, 2]

    def test_get_trucks_with_available_capacity_preserves_identity_order(self):
        truck_list = [truck.Truck(n) for n in range(3)]
        twac = pl.get_trucks_with_available_capacity(truck_list, 2)
        for i in range(3):
            assert truck_list[i] is twac[i]

    def test_build_feasible_routes_returns_single_feasible_route(self, monkeypatch):
        t1 = truck.Truck(0)
        t1.package_list = [make_pkg(1)]
        t1.speed_mph = 18
        working_package_list = [make_pkg(2), make_pkg(3)]

        fake_nearest_neighbor(monkeypatch, distance=10.0, route=["r1", "r2"])
        monkeypatch.setattr(pl, "check_route_feasibility", lambda route, speed, v: True)

        result = pl.build_feasible_routes([t1], working_package_list, verbosity="0", count=1)

        assert len(result) == 1
        test_truck, test_route, test_distance = result[0]
        assert test_truck is t1
        assert test_route == ["r1", "r2"]
        assert test_distance == 10.0

    def test_build_feasible_routes_returns_multiple_feasible_routes(self, monkeypatch):
        t1, t2 = truck.Truck(0), truck.Truck(1)
        t1.package_list = [make_pkg(1)]
        t2.package_list = [make_pkg(2)]
        t1.speed_mph = t2.speed_mph = 18
        working_package_list = [make_pkg(3)]

        fake_nearest_neighbor(monkeypatch, distance=10.0, route=["_"])
        monkeypatch.setattr(pl, "check_route_feasibility", lambda route, speed, v: True)

        result = pl.build_feasible_routes([t1, t2], working_package_list, verbosity="0", count=1)
        assert len(result) == 2
        trucks_in_result = {t.truck_id for t, _, _ in result}
        assert trucks_in_result == {0, 1}

    def test_build_feasible_routes_filters_out_infeasible_routes(self, monkeypatch):
        t1, t2 = truck.Truck(0), truck.Truck(1)
        t1.package_list = [make_pkg(1)]
        t2.package_list = [make_pkg(2)]
        t1.speed_mph = t2.speed_mph = 18
        working_package_list = [make_pkg(3)]

        fake_nearest_neighbor(monkeypatch, distance=10.0, route=["r1"])
        calls = {"count": 0}
        def fake_check_route_feasibility(route, speed, v):
            calls["count"] += 1
            return calls["count"] == 1
        monkeypatch.setattr(pl, "check_route_feasibility", fake_check_route_feasibility)

        result = pl.build_feasible_routes([t1, t2], working_package_list, verbosity="0", count=1)

        assert len(result) == 1
        assert result[0][0] is t1

    def test_build_feasible_routes_raises_when_no_feasible_routes(self, monkeypatch):
        t1 = truck.Truck(0)
        working_package_list = [make_pkg(1)]

        fake_nearest_neighbor(monkeypatch, distance=10.0, route=["r1"])
        monkeypatch.setattr(pl, "check_route_feasibility", lambda route, speed, v: False)

        with pytest.raises(SystemExit):
            result = pl.build_feasible_routes([t1], working_package_list, verbosity="0", count=1)

    def test_choose_best_option_returns_the_only_route_when_exactly_one_feasible_route_exists(self):
        t1, wpl, dist = truck.Truck(0), [make_pkg(1), make_pkg(2)], 10.0
        feasible_routes = [(t1, wpl, dist)]

        result = pl.choose_best_option(feasible_routes)

        assert result == (t1, wpl, dist)
        res_truck, res_wpl, res_dist = result
        assert res_truck is t1
        packages_in_result = {p.package_id for p in res_wpl}
        assert packages_in_result == {1, 2}
        assert res_dist == 10.0

    def test_choose_best_option_selects_route_that_minimizes_distance_when_multiple_feasible_routes_exist(self):
        t1, wpl1, dist1 = truck.Truck(0), [make_pkg(1)], 15.0
        t2, wpl2, dist2 = truck.Truck(1), [make_pkg(2)], 10.0
        t1.route_distance = t2.route_distance = 0

        feasible_routes = [(t1, wpl1, dist1), (t2, wpl2, dist2)]

        result = pl.choose_best_option(feasible_routes)

        res_truck, res_wpl, res_dist = result
        assert res_truck is t2
        packages_in_result = {p.package_id for p in res_wpl}
        assert packages_in_result == {2}
        assert res_dist == 10.0

    def test_choose_best_option_handles_ties_by_choosing_first_minimum_distance_option(self):
        t1, wpl1, dist1 = truck.Truck(0), [make_pkg(1)], 10.0
        t2, wpl2, dist2 = truck.Truck(1), [make_pkg(2)], 10.0
        t1.route_distance = t2.route_distance = 0

        feasible_routes = [(t1, wpl1, dist1), (t2, wpl2, dist2)]

        result_truck, _, _ = pl.choose_best_option(feasible_routes)

        assert result_truck is t1

    def test_choose_best_option_correctly_computes_total_distance_using_existing_truck_route_distance_values(self):
        t1, wpl, dist = truck.Truck(0), [make_pkg(1), make_pkg(2)], 15.0
        t1.route_distance = 10.0
        feasible_routes = [(t1, wpl, dist)]

        _, _, result_distance = pl.choose_best_option(feasible_routes)

        assert result_distance == 15.0

    def test_get_candidate_trucks_returns_trucks_assigned_to_specified_drivers_when_drivers_list_is_provided(self):
        drivers = ["Ren", "Stimpy"]
        test_fleet = fleet.Fleet(2)
        for i, t in enumerate(test_fleet.truck_list):
            t.driver = drivers[i]

        candidates = pl.get_candidate_trucks(test_fleet, drivers)
        candidate_drivers = [t.driver for t in candidates]

        assert len(candidates) == 2
        assert set(candidate_drivers) == set(drivers)

    def test_get_candidate_trucks_excludes_trucks_with_zero_capacity_when_drivers_list_is_provided(self):
        drivers = ["Ren", "Stimpy"]
        test_fleet = fleet.Fleet(2)
        for i, t in enumerate(test_fleet.truck_list):
            t.driver = drivers[i]
        full_truck = test_fleet.truck_list[0]
        full_truck.current_capacity = 0

        candidates = pl.get_candidate_trucks(test_fleet, drivers)

        assert full_truck not in candidates
        assert len(candidates) == 1
        assert candidates[0].driver == "Stimpy"

    def test_get_candidate_trucks_returns_only_unassigned_trucks_when_no_drivers_list_is_provided(self):
        drivers = ["Ren", "Stimpy"]
        test_fleet = fleet.Fleet(5)
        for i, t in enumerate(test_fleet.truck_list[:-3]):
            t.driver = drivers[i]

        candidates = pl.get_candidate_trucks(test_fleet)

        assert len(candidates) == 3
        assert all(t.driver is None for t in candidates)

    def test_get_candidate_trucks_excludes_unassigned_trucks_with_zero_capacity_when_no_drivers_list_is_provided(self):
        drivers = ["Ren", "Stimpy"]
        test_fleet = fleet.Fleet(4)
        for i, t in enumerate(test_fleet.truck_list[2:]):
            t.driver = drivers[i]
        full_truck = test_fleet.truck_list[0]
        full_truck.current_capacity = 0

        candidates = pl.get_candidate_trucks(test_fleet)

        assert len(candidates) == 1
        assert full_truck not in candidates
        assert any(t.driver is None for t in candidates)

    def test_get_candidate_trucks_returns_empty_list_when_drivers_list_provided_but_no_trucks_match(self):
        drivers = ["Ren", "Stimpy"]
        test_fleet = fleet.Fleet(4)
        full_truck = test_fleet.truck_list[0]
        full_truck.current_capacity = 0

        candidates = pl.get_candidate_trucks(test_fleet, drivers)

        assert candidates == []

    def test_get_candidate_trucks_returns_empty_list_when_no_drivers_list_provided_and_no_unassigned_trucks_available(self):
        test_fleet = fleet.Fleet(4)
        for t in test_fleet.truck_list:
            t.current_capacity = 0

        candidates = pl.get_candidate_trucks(test_fleet)

        assert candidates == []

    def test_has_w_note_returns_true_when_first_package_has_w(self):
        package_list = [
            make_pkg(1),
            make_pkg(2)
        ]
        package_list[0].special_note = ["W", 2]
        assert pl.has_w_note(package_list) == True

    def test_has_w_note_returns_false_when_first_package_has_no_special_note(self):
        package_list = [
            make_pkg(1)
        ]
        
        assert pl.has_w_note(package_list) == False

    def test_has_w_note_returns_false_when_first_package_special_note_not_w(self):
        package_list = [
            make_pkg(1),
            make_pkg(2)
        ]
        package_list[0].special_note = ["T", 2]
        
        assert pl.has_w_note(package_list) == False

    def test_has_w_note_returns_true_when_any_package_has_w(self):
        package_list = [
            make_pkg(1),
            make_pkg(2),
            make_pkg(3)
        ]
        package_list[1].special_note = ["W", 3]
        assert pl.has_w_note(package_list) == True

    def test_has_w_note_empty_list_returns_false(self):
        assert pl.has_w_note([]) == False

    def test_remove_empty_groups_removes_single_empty_group(self):
        groups_list = [[] for _ in range(3)]
        groups_list[0].append(make_pkg(1))
        groups_list[2].append(make_pkg(2))
        pl.remove_empty_groups(groups_list)
        assert len(groups_list) == 2
        assert groups_list[1][0].package_id == 2

    def test_remove_empty_groups_removes_multiple_empty_groups(self):
        groups_list = [[] for _ in range(10)]
        pl.remove_empty_groups(groups_list)
        assert len(groups_list) == 0

    def test_remove_empty_groups_leaves_non_empty_groups_untouched(self):
        groups_list = [[] for _ in range(3)]
        groups_list[0].append(make_pkg(1))
        groups_list[2].append(make_pkg(2))
        pkg1 = groups_list[0][0]
        pkg2 = groups_list[2][0]
        pl.remove_empty_groups(groups_list)
        assert groups_list[0][0] is pkg1
        assert groups_list[1][0] is pkg2

    def test_remove_empty_groups_preserves_order_of_remaining_groups(self):
        groups_list = [[] for _ in range(5)]
        groups_list[0].append(make_pkg(1))
        groups_list[2].append(make_pkg(2))
        groups_list[2].append(make_pkg(3))
        ids = [p.package_id for g in groups_list for p in g]
        pl.remove_empty_groups(groups_list)
        assert ids == [1, 2, 3]

    def test_remove_empty_groups_no_empty_groups_no_change(self):
        groups_list = [[] for _ in range(3)]
        groups_list[0].append(make_pkg(1))
        groups_list[1].append(make_pkg(2))
        groups_list[2].append(make_pkg(3))
        pl.remove_empty_groups(groups_list)
        assert len(groups_list) == 3

    def test_remove_empty_groups_all_groups_empty_returns_empty_list(self):
        groups_list = [[] for _ in range(5)]
        groups_list[1].append(make_pkg(1))
        groups_list[3].append(make_pkg(2))
        pl.remove_empty_groups(groups_list)
        assert len(groups_list) == 2

    def test_load_optimal_truck_sets_truck_package_list_to_given_route(self):
        tr, rte, dist = make_truck_route_dist()
        pl.load_optimal_truck((tr, rte, dist))
        assert tr.package_list == rte

    def test_load_optimal_truck_updates_current_capacity_based_on_route_length(self):
        tr, rte, dist = make_truck_route_dist()
        pl.load_optimal_truck((tr, rte, dist))
        assert tr.current_capacity == tr.maximum_capacity - len(rte)

    def test_load_optimal_truck_sets_route_distance_to_given_distance(self):
        tr, rte, dist = make_truck_route_dist()
        pl.load_optimal_truck((tr, rte, dist))
        assert tr.route_distance == dist

    def test_load_optimal_truck_sets_truck_id_on_all_packages_in_route(self):
        tr, rte, dist = make_truck_route_dist()
        pl.load_optimal_truck((tr, rte, dist))
        for pkg in rte:
            assert pkg.truck == tr.truck_id

    def test_load_optimal_truck_overwrites_existing_truck_state(self):
        tr, rte, dist = make_truck_route_dist()
        before = [tr.package_list, tr.current_capacity, tr.route_distance]
        pl.load_optimal_truck((tr, rte, dist))
        after = [tr.package_list, tr.current_capacity, tr.route_distance]
        for i in range(3):
            assert before[i] != after[i]

    def test_print_loading_packages_returns_immediately_when_verbosity_is_zero(self, capsys):
        tr, rte, _ = make_truck_route_dist()
        pl.print_loading_packages(tr, rte, 0)
        out = capsys.readouterr().out
        assert out == ""

    def test_print_loading_packages_prints_header_and_lines_when_verbosity_is_nonzero(self, capsys):
        tr, rte, _ = make_truck_route_dist()
        pl.print_loading_packages(tr, rte, 1)
        out = capsys.readouterr().out
        for i in range(1, len(rte)+1):
            assert f"-LOADING Package {i} ONTO Truck {tr.truck_id+1}" in out

    def test_print_loading_packages_handles_empty_package_list(self, capsys):
        tr = truck.Truck(1)
        pl.print_loading_packages(tr, [], 1)
        out = capsys.readouterr().out
        assert "-LOADING Package" not in out

    def test_print_loading_packages_uses_truck_id_plus_one_in_output(self, capsys):
        tr, rte, _ = make_truck_route_dist()
        pl.print_loading_packages(tr, rte, "1")
        out = capsys.readouterr().out
        assert f"ONTO Truck {tr.truck_id + 1}" in out

class TestLoadAssignedTrucks:
    def test_load_assigned_trucks_loads_assigned_package_onto_truck_and_updates_state(self):
        test_fleet = fleet.Fleet(2)
        package_groups = [
            [
                make_pkg(1, 2, 0),
                make_pkg(2, 2, 0),
                make_pkg(3, 1, 0),
                make_pkg(4, None, 0)
            ],
            [
                make_pkg(5, 3, 1),
                make_pkg(6, 4, 1),
                make_pkg(7, 4, 1),
                make_pkg(8, None, 1)
            ]
        ]
        for pkg in package_groups[0]:
            pkg.truck = 0
        package_groups[1][0].truck = 1

        loader = pl.PackageLoader()
        loader.load_assigned_trucks(test_fleet, package_groups, NullReporter())

        tr0, tr1 = test_fleet.truck_list[0], test_fleet.truck_list[1]
        ids = [pkg.package_id for group in package_groups for pkg in group]

        assert len(tr0.package_list) == 4
        assert len(tr1.package_list) == 1

        assert tr0.current_capacity == tr0.maximum_capacity - 4
        assert tr1.current_capacity == tr1.maximum_capacity - 1

        assert len(package_groups) == 1
        assert ids == [6, 7, 8]

    def test_load_assigned_trucks_does_not_load_when_truck_capacity_is_zero(self):
        test_fleet = fleet.Fleet(1)
        package_groups = [
            [
                make_pkg(1, 2, 0),
                make_pkg(2, 2, 0),
                make_pkg(3, 1, 0),
                make_pkg(4, None, 0)
            ]
        ]
        for pkg in package_groups[0]:
            pkg.truck = 0

        tr0 = test_fleet.truck_list[0]
        tr0.current_capacity = 0

        loader = pl.PackageLoader()
        loader.load_assigned_trucks(test_fleet, package_groups, "0")
        ids = [pkg.package_id for group in package_groups for pkg in group]

        assert len(tr0.package_list) == 0
        assert tr0.current_capacity == 0
        assert len(package_groups) == 1
        assert ids == [1, 2, 3, 4]

    def test_load_assigned_trucks_does_not_load_when_pkg_truck_is_none(self):
        test_fleet = fleet.Fleet(1)
        package_groups = [
            [
                make_pkg(1, 2, 0),
                make_pkg(2, 2, 0),
                make_pkg(3, 1, 0),
                make_pkg(4, None, 0)
            ]
        ]

        loader = pl.PackageLoader()
        loader.load_assigned_trucks(test_fleet, package_groups, "0")

        tr0 = test_fleet.truck_list[0]
        ids = [pkg.package_id for group in package_groups for pkg in group]

        assert len(tr0.package_list) == 0
        assert tr0.current_capacity == tr0.maximum_capacity
        assert len(package_groups) == 1
        assert ids == [1, 2, 3, 4]

    def test_load_assigned_trucks_does_not_load_when_truck_id_is_out_of_range(self):
        test_fleet = fleet.Fleet(1)
        package_groups = [
            [
                make_pkg(1, 2, 0),
                make_pkg(2, 2, 0),
                make_pkg(3, 1, 0),
                make_pkg(4, None, 0)
            ]
        ]
        for pkg in package_groups[0]:
            pkg.truck = 99

        loader = pl.PackageLoader()
        loader.load_assigned_trucks(test_fleet, package_groups, "0")

        tr0 = test_fleet.truck_list[0]
        ids = [pkg.package_id for group in package_groups for pkg in group]

        assert len(tr0.package_list) == 0
        assert tr0.current_capacity == tr0.maximum_capacity
        assert len(package_groups) == 1
        assert ids == [1, 2, 3, 4]

class TestLoadEmptyTrucksWithDrivers:
    def test_loads_highest_priority_packages_onto_empty_truck_with_driver(self):
        test_fleet = fleet.Fleet(2)
        test_truck = test_fleet.truck_list[0]
        test_truck.driver = "Timmy"
        package_groups = [
            [make_pkg(1, 3, 1), make_pkg(2, 3, 1), make_pkg(3, 3, 1)],
            [make_pkg(4, 4, 2)]
        ]
        loader = pl.PackageLoader()
        loader.load_empty_trucks_with_drivers(test_fleet, package_groups, NullReporter(), ["Timmy"])

        assert len(package_groups) == 1
        assert [pkg.package_id for pkg in package_groups[0]] == [4]

        ids = [pkg.package_id for pkg in test_truck.package_list]
        assert ids == [1, 2, 3]
        assert test_truck.current_capacity == test_truck.maximum_capacity - 3  
        assert all(pkg.truck == test_truck.truck_id for pkg in test_truck.package_list)

    def test_does_not_load_when_no_empty_trucks_have_drivers(self):
        test_fleet = fleet.Fleet(2)
        package_groups = [[make_pkg(1, 3, 1)]]

        loader = pl.PackageLoader()
        loader.load_empty_trucks_with_drivers(test_fleet, package_groups, "0", ["Timmy"])

        assert len(package_groups) == 1
        assert package_groups[0][0].truck is None
        for truck in test_fleet.truck_list:
            assert not truck.package_list

    def test_ignores_trucks_that_are_not_empty(self):
        test_fleet = fleet.Fleet(2)
        truck_a, truck_b = test_fleet.truck_list[0], test_fleet.truck_list[1]
        truck_a.driver = "Timmy"
        truck_a.package_list = [make_pkg(2, 4, 2)]
        truck_a.current_capacity -= 1
        truck_b.driver = "Jimmy"
        truck_b.package_list = [make_pkg(3, 4, 2)]
        truck_b.current_capacity -= 1

        package_groups = [[make_pkg(1, 3, 1)]]

        loader = pl.PackageLoader()
        loader.load_empty_trucks_with_drivers(test_fleet, package_groups, "0", ["Timmy", "Jimmy"])

        assert len(package_groups) == 1
        assert package_groups[0][0].package_id == 1
        assert len(truck_a.package_list) == 1
        assert truck_a.package_list[0].package_id == 2
        assert len(truck_b.package_list) == 1
        assert truck_b.package_list[0].package_id == 3

    def test_splits_and_returns_leftover_packages_to_front_of_package_groups_when_capacity_exceeded(self, fake_split):
        test_fleet = fleet.Fleet(1)
        test_truck = test_fleet.truck_list[0]
        test_truck.driver = "Timmy"
        test_truck.current_capacity = test_truck.maximum_capacity = 2
        package_groups = [[make_pkg(1, 3, 1), make_pkg(2, 3, 1), make_pkg(3, 3, 1)]]

        loader = pl.PackageLoader()
        loader.load_empty_trucks_with_drivers(test_fleet, package_groups, NullReporter(), ["Timmy"])

        ids = [pkg.package_id for pkg in test_truck.package_list]
        assert ids == [1, 2]
        assert test_truck.current_capacity == 0
        assert len(package_groups) == 1
        assert [pkg.package_id for pkg in package_groups[0]] == [3]

    def test_does_not_split_package_list_when_w_note_present_and_it_fits(self):
        test_fleet = fleet.Fleet(1)
        test_truck = test_fleet.truck_list[0]
        test_truck.driver = "Timmy"
        test_truck.current_capacity = test_truck.maximum_capacity = 3
        w_package_a = make_pkg(1, 3, 1)
        w_package_a.special_note = ['W', 2]
        w_package_b = make_pkg(2, 3, 1)
        w_package_b.special_note = ['W', 1]
        package_groups = [[w_package_a, w_package_b, make_pkg(3, 3, 1)]]

        loader = pl.PackageLoader()
        loader.load_empty_trucks_with_drivers(test_fleet, package_groups, NullReporter(), ["Timmy"])

        ids = [pkg.package_id for pkg in test_truck.package_list]
        assert ids == [1, 2, 3]
        assert test_truck.current_capacity == 0
        assert len(package_groups) == 0

    def test_raises_when_w_note_present_and_it_doesnt_fit(self):
        test_fleet = fleet.Fleet(1)
        test_truck = test_fleet.truck_list[0]
        test_truck.driver = "Timmy"
        test_truck.current_capacity = test_truck.maximum_capacity = 2
        w_package_a = make_pkg(1, 3, 1)
        w_package_a.special_note = ['W', 2]
        w_package_b = make_pkg(2, 3, 1)
        w_package_b.special_note = ['W', 1]
        package_groups = [[w_package_a, w_package_b, make_pkg(3, 3, 1)]]

        loader = pl.PackageLoader()
        with pytest.raises(SystemExit):
            loader.load_empty_trucks_with_drivers(test_fleet, package_groups, NullReporter(), ["Timmy"])
        assert test_truck.package_list == []
        assert test_truck.current_capacity == 2

    def test_removes_empty_groups_after_loading(self):
        test_fleet = fleet.Fleet(1)
        test_truck = test_fleet.truck_list[0]
        test_truck.driver = "Timmy"
        package_groups = [[make_pkg(1, 3, 1)], []]

        loader = pl.PackageLoader()
        loader.load_empty_trucks_with_drivers(test_fleet, package_groups, NullReporter(), ["Timmy"])

        assert len(package_groups) == 0

    def test_processes_multiple_empty_trucks_in_order(self):
        test_fleet = fleet.Fleet(2)
        truck_a, truck_b = test_fleet.truck_list[0], test_fleet.truck_list[1]
        truck_a.driver = "Timmy"
        truck_b.driver = "Jimmy"
        package_groups = [
            [make_pkg(1, 3, 1), make_pkg(2, 3, 1), make_pkg(3, 3, 1)],
            [make_pkg(4, 4, 2)]
        ]
        loader = pl.PackageLoader()
        loader.load_empty_trucks_with_drivers(test_fleet, package_groups, NullReporter(), ["Timmy", "Jimmy"])

        assert len(package_groups) == 0

        assert [pkg.package_id for pkg in truck_a.package_list] == [1, 2, 3]
        assert truck_a.current_capacity == truck_a.maximum_capacity - 3
        assert all(pkg.truck is not None for pkg in truck_a.package_list)

        assert truck_b.package_list[0].package_id == 4
        assert truck_b.current_capacity == truck_b.maximum_capacity - 1
        assert truck_b.package_list[0].truck == 1

@pytest.fixture
def load_packages_world_factory(monkeypatch):
    def _make_world(num_trucks=1):
        test_fleet = fleet.Fleet(num_trucks)

        for tr in test_fleet.truck_list:
            tr = test_fleet.truck_list[0]
            tr.maximum_capacity = 10
            tr.current_capacity = 10
            tr.route_distance = 123.45

        monkeypatch.setattr(pl, "get_candidate_trucks", lambda fleet_obj, drivers=None: fleet_obj.truck_list,)
        monkeypatch.setattr(pl, "get_trucks_with_available_capacity", lambda trucks, needed: trucks,)
        monkeypatch.setattr(pl, "adjust_working_list_for_capacity", lambda truck_list, groups, working_list, verbosity: (working_list, truck_list),)

        def fake_build_working_package_list(groups):
            return groups.pop(0)

        monkeypatch.setattr(pl, "build_working_package_list", fake_build_working_package_list,)
        monkeypatch.setattr(pl, "nearest_neighbor", lambda pkg_list: (0.0, pkg_list),)

        def fake_build_feasible_routes(available_trucks, working_package_list, verbosity, count):
            t = available_trucks[0]
            return [(t, working_package_list, 10.0)]

        monkeypatch.setattr(pl, "build_feasible_routes", fake_build_feasible_routes,)
        monkeypatch.setattr(pl, "choose_best_option", lambda routes: routes[0],)

        def fake_load_optimal_truck(option):
            t, route, distance = option
            t.package_list = route
            t.current_capacity = t.maximum_capacity - len(route)
            t.route_distance = distance

        monkeypatch.setattr(pl, "load_optimal_truck", fake_load_optimal_truck,)

        loader = pl.PackageLoader()

        class World:
            pass

        world = World()
        world.loader = loader
        world.fleet = test_fleet
        world.truck = test_fleet.truck_list[0] if test_fleet.truck_list else None
        return world

    return _make_world

class TestLoadPackages:
    def test_stops_when_package_groups_empty(self, load_packages_world_factory):
        world = load_packages_world_factory(num_trucks=1)

        package_groups = [[make_pkg(1, 0 , 0), make_pkg(2, 0, 0)]]

        world.loader.load_packages(world.fleet, package_groups, NullReporter(0))

        assert package_groups == []
        assert len(world.truck.package_list) == 2
        assert world.truck.route_distance == 0

    def test_load_packages_stops_when_no_trucks_available(self, load_packages_world_factory):
        world = load_packages_world_factory(num_trucks=1)
        world.fleet = fleet.Fleet(0)

        package_groups = [[make_pkg(1, 0 , 0), make_pkg(2, 0, 0)]]

        world.loader.load_packages(world.fleet, package_groups, NullReporter(0))

        assert len(package_groups) == 1

    def test_load_packages_removes_truck_when_capacity_hits_zero(self, load_packages_world_factory):
        world = load_packages_world_factory(num_trucks=1)
        tr = world.fleet.truck_list[0]
        tr.current_capacity = 2
        tr.maximum_capacity = 2

        package_groups = [[make_pkg(1, 0 , 0), make_pkg(2, 0, 0)]]

        world.loader.load_packages(world.fleet, package_groups, NullReporter(0))

        assert package_groups == []
        assert tr.current_capacity == 0

    def test_load_packages_resets_route_distance_for_entire_fleet(self, load_packages_world_factory):
        world = load_packages_world_factory(num_trucks=1)
        tr = world.fleet.truck_list[0]
        tr.route_distance = 123

        package_groups = [[make_pkg(1, 0 , 0), make_pkg(2, 0, 0)]]

        world.loader.load_packages(world.fleet, package_groups, NullReporter(0))

        assert tr.route_distance == 0

    def test_load_packages_no_candidate_trucks_does_not_process_any_groups(self, load_packages_world_factory, monkeypatch):
        world = load_packages_world_factory(num_trucks=1)

        package_groups = [[make_pkg(1, 0 , 0), make_pkg(2, 0, 0)]]

        monkeypatch.setattr(pl, "get_candidate_trucks", lambda fleet_obj, drivers=None: [],)

        world.loader.load_packages(world.fleet, package_groups, NullReporter(0))

        assert len(package_groups) == 1

    def test_load_packages_propagates_systemexit_when_no_feasible_routes(self, load_packages_world_factory, monkeypatch):
        world = load_packages_world_factory(num_trucks=1)

        package_groups = [[make_pkg(1, 0 , 0), make_pkg(2, 0, 0)]]

        def exit_build_feasible_routes(*args, **kwargs):
            raise SystemExit(1)

        monkeypatch.setattr(pl, "build_feasible_routes", exit_build_feasible_routes,)

        with pytest.raises(SystemExit):
            world.loader.load_packages(world.fleet, package_groups, NullReporter(0))

    def test_load_packages_loads_packages_into_optimal_truck(self, load_packages_world_factory):
        world = load_packages_world_factory(num_trucks=1)
        tr = world.fleet.truck_list[0]
        packages = [make_pkg(1, 0 , 0), make_pkg(2, 0, 0)]

        package_groups = [packages]

        world.loader.load_packages(world.fleet, package_groups, NullReporter(0))

        assert tr.package_list == packages

    def test_load_packages_widens_to_all_trucks_when_no_deadlines_remain(self, load_packages_world_factory, monkeypatch):
        world = load_packages_world_factory(num_trucks=3)

        # Start narrow: only truck 0 is considered a candidate
        monkeypatch.setattr(pl, "get_candidate_trucks", lambda fleet_obj, drivers=None: [fleet_obj.truck_list[0]])

        seen = {"available_truck_ids": None}

        def spy_build_feasible_routes(available_trucks, working_package_list, verbosity, count):
            seen["available_truck_ids"] = [t.truck_id for t in available_trucks]
            return [(available_trucks[0], working_package_list, 10.0)]

        monkeypatch.setattr(pl, "build_feasible_routes", spy_build_feasible_routes)

        # No deadlines in any remaining groups (check runs before pop)
        package_groups = [
            [make_pkg(1, group=0, priority=2)],
            [make_pkg(2, group=1, priority=3)],
        ]

        world.loader.load_packages(world.fleet, package_groups, NullReporter(0))

        assert seen["available_truck_ids"] == [0, 1, 2]

    def test_load_packages_does_not_widen_when_deadlines_remain(self, load_packages_world_factory, monkeypatch):
        world = load_packages_world_factory(num_trucks=3)

        monkeypatch.setattr(pl, "get_candidate_trucks", lambda fleet_obj, drivers=None: [fleet_obj.truck_list[0]])

        seen = {"available_truck_ids": None}

        def spy_build_feasible_routes(available_trucks, working_package_list, verbosity, count):
            seen["available_truck_ids"] = [t.truck_id for t in available_trucks]
            return [(available_trucks[0], working_package_list, 10.0)]

        monkeypatch.setattr(pl, "build_feasible_routes", spy_build_feasible_routes)

        # Deadline exists in unassigned groups at loop-start
        package_groups = [
            [make_pkg(1, group=0, priority=2)],
            [make_pkg(2, group=1, priority=1)],  # deadline-like
        ]

        world.loader.load_packages(world.fleet, package_groups, NullReporter(0))

        assert seen["available_truck_ids"] == [0]
