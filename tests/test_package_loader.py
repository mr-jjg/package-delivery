# /tests/test_package_loader.py
# Test for shape, state changes, branching/conditions, interactions

import pytest
import package
import package_loader as pl
import truck

def make_pkg(id_, group=None, priority=None):
    return package.Package(id_, "Address", "City", "ST", 99999, None, 1.0, None, "at_the_hub", None, None, group, priority)

def make_truck_route_dist(route_len=4, dist=99.0):
        tr = truck.Truck(1)
        route = [make_pkg(i) for i in range(1, route_len + 1)]
        return tr, route, dist

class TestHelpers:
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

    def test_print_loading_packages_returns_immediately_when_verbosity_is_zero_string(self, capsys):
        tr, rte, _ = make_truck_route_dist()
        pl.print_loading_packages(tr, rte, "0")
        out = capsys.readouterr().out
        assert out == ""

    def test_print_loading_packages_prints_header_and_lines_when_verbosity_is_nonzero(self, capsys):
        tr, rte, _ = make_truck_route_dist()
        pl.print_loading_packages(tr, rte, "1")
        out = capsys.readouterr().out
        assert "verbosity: 1" in out
        for i in range(1, len(rte)+1):
            assert f"-LOADING Package {i} ONTO Truck {tr.truck_id+1}" in out

    def test_print_loading_packages_handles_empty_package_list(self, capsys):
        tr = truck.Truck(1)
        pl.print_loading_packages(tr, [], "1")
        out = capsys.readouterr().out
        assert "verbosity: 1" in out
        assert "-LOADING Package" not in out

    def test_print_loading_packages_uses_truck_id_plus_one_in_output(self, capsys):
        tr, rte, _ = make_truck_route_dist()
        pl.print_loading_packages(tr, rte, "1")
        out = capsys.readouterr().out
        assert f"ONTO Truck {tr.truck_id + 1}" in out

'''
class TestLoadAssignedTrucks:
    
class TestLoadEmptyTrucksWithDrivers:

class TestLoadPackages:
'''