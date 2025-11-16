# /tests/test_package_loader.py
# Test for shape, state changes, branching/conditions, interactions

import pytest
import package
import package_loader as pl
import truck

def make_pkg(id_, group=None, priority=None):
    return package.Package(id_, "Address", "City", "ST", 99999, None, 1.0, None, "at_the_hub", None, None, group, priority)

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

'''   
    def test_remove_empty_groups():
        
    def test_load_optimal_truck():
        
    def test_print_loading_packages():

class TestLoadAssignedTrucks:
    
class TestLoadEmptyTrucksWithDrivers:

class TestLoadPackages:
'''