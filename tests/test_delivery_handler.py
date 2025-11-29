# /tests/test_delivery_handler.py

import pytest
from datetime import time
import delivery_handler as dh
import fleet
import package
import truck

def make_fleet_with_two_trucks():
    fl = fleet.Fleet(0)
    tr1, tr2 = truck.Truck(0), truck.Truck(1)
    fl.add_truck(tr1)
    fl.add_truck(tr2)
    return fl, tr1, tr2
    
def make_fleet_four_trucks_even_ids_have_drivers():
    fl = fleet.Fleet(4)
    for tr in fl.truck_list:
        if tr.truck_id % 2 == 0:
            tr.driver = f"Driver-{tr.truck_id}"
    return fl

def make_pkg(id_):
    return package.Package(id_, "Address", "City", "ST", 99999, None, 1.0, None, "at_the_hub", None, None, 0, 0)

#class TestBuildDeliveryList:

#class TestGenerateDeliveryTimeline:

#class TestDeliverPackages:

#class TestPrintDeliveryList:

#class TestPrintPackageStatusesAt:

class TestHelper:
    def test_separate_trucks_by_driver_status_places_trucks_with_drivers_in_available(self, monkeypatch):
        fl, tr1, tr2 = make_fleet_with_two_trucks()
        tr1.driver, tr2.driver = "Leonard", "Mary"
        
        monkeypatch.setattr(dh, "get_route_departure_time", lambda t: None)
        
        available, _ = dh.separate_trucks_by_driver_status(fl)
        
        assert len(available) == 2
        assert available == [tr1, tr2]
        
    def test_separate_trucks_by_driver_status_places_trucks_without_drivers_in_waiting(self, monkeypatch):
        fl, tr1, tr2 = make_fleet_with_two_trucks()
        
        monkeypatch.setattr(dh, "get_route_departure_time", lambda t: None)
        
        _, waiting = dh.separate_trucks_by_driver_status(fl)
        
        assert len(waiting) == 2
        assert waiting == [tr1, tr2]
        
    def test_separate_trucks_by_driver_status_sets_departure_time_for_available_trucks(self, monkeypatch):
        fl, tr1, tr2 = make_fleet_with_two_trucks()
        tr1.driver, tr2.driver = "Leonard", "Mary"
        
        monkeypatch.setattr(dh, "get_route_departure_time", lambda t: time(8, 0))
        
        dh.separate_trucks_by_driver_status(fl)
        
        assert tr1.departure_time == time(8, 0)
        assert tr2.departure_time == time(8, 0)

    def test_separate_trucks_by_driver_status_does_not_set_departure_time_for_waiting_trucks(self, monkeypatch):
        fl, tr1, tr2 = make_fleet_with_two_trucks()
        
        monkeypatch.setattr(dh, "get_route_departure_time", lambda t: time(8, 0))
        
        dh.separate_trucks_by_driver_status(fl)
        
        assert tr1.departure_time is None
        assert tr2.departure_time is None
        
    def test_separate_trucks_by_driver_status_returns_lists_in_original_order(self, monkeypatch):
        fl = make_fleet_four_trucks_even_ids_have_drivers()
        
        monkeypatch.setattr(dh, "get_route_departure_time", lambda t: time(8, 0))
        
        available, waiting = dh.separate_trucks_by_driver_status(fl)
        
        av_ids = [t.truck_id for t in available]
        wa_ids = [t.truck_id for t in waiting]
        
        assert av_ids == [0, 2]
        assert wa_ids == [1, 3]
        
    def test_separate_trucks_by_driver_status_handles_empty_fleet(self, monkeypatch):
        fl = fleet.Fleet(0)
        
        monkeypatch.setattr(dh, "get_route_departure_time", lambda t: time(8, 0))
        
        available, waiting = dh.separate_trucks_by_driver_status(fl)
        
        assert available == [] and waiting == []
        
    def test_separate_trucks_by_driver_status_invokes_get_route_departure_time_once_per_available_truck(self, monkeypatch):
        fl = make_fleet_four_trucks_even_ids_have_drivers()
                
        call_count = {"count": 0}
        def fake_get_route_departure_time(package_list):
            call_count["count"] += 1
            return time(8, 0)
            
        monkeypatch.setattr(dh, "get_route_departure_time", fake_get_route_departure_time)
        
        dh.separate_trucks_by_driver_status(fl)
        
        assert call_count["count"] == 2

    def test_set_packages_en_route_sets_all_packages_to_en_route(self):
        packages = [make_pkg(0), make_pkg(1), make_pkg(2)]

        dh.set_packages_en_route(packages)

        for pkg in packages:
            assert pkg.delivery_status == "en_route"

    def test_set_packages_en_route_overwrites_existing_status_values(self):
        pkg = make_pkg(0)
        before = pkg.delivery_status

        dh.set_packages_en_route([pkg])

        assert before != "en_route"
        assert pkg.delivery_status == "en_route"

    def test_set_packages_en_route_handles_empty_package_list(self):
        empty_list = []

        dh.set_packages_en_route(empty_list)

        assert empty_list == []

    def test_set_packages_en_route_does_not_modify_other_package_fields(self):
        def snapshot(pkg):
            return (pkg.address, pkg.city, pkg.state, pkg.zip_code, pkg.delivery_deadline, pkg.weight_kilo, pkg.special_note, pkg.time_of_delivery, pkg.truck, pkg.group, pkg.priority)

        pkg = make_pkg(0)
        before = snapshot(pkg)

        dh.set_packages_en_route([pkg])

        after = snapshot(pkg)
        assert before == after

    def test_update_previous_location_appends_new_entry_when_list_is_empty(self):
        previous_locations = []
        truck_id = 0
        address = "Address"

        dh.update_previous_location(previous_locations, truck_id, address)

        assert len(previous_locations) == 1
        assert previous_locations == [(truck_id, address)]

    def test_update_previous_location_appends_new_entry_for_new_truck_id(self):
        previous_locations = [(0, "Address1")]
        truck_id = 1
        address = "Address2"

        dh.update_previous_location(previous_locations, truck_id, address)

        assert len(previous_locations) == 2
        assert previous_locations[1] == (truck_id, address)

    def test_update_previous_location_updates_existing_entry_for_same_truck_id(self):
        previous_locations = [(0, "OldAddress")]
        truck_id = 0
        address = "NewAddress"

        dh.update_previous_location(previous_locations, truck_id, address)

        assert len(previous_locations) == 1
        assert previous_locations[0] == (truck_id, address)

    def test_update_previous_location_preserves_order_when_updating_existing_entry(self):
        first = (0, "First")
        second = (1, "Second")
        previous_locations = [first, second]
        truck_id = 1
        address = "NewSecond"

        dh.update_previous_location(previous_locations, truck_id, address)

        assert len(previous_locations) == 2
        assert previous_locations[0] == first
        assert previous_locations[1] == (truck_id, address)

    def test_update_previous_location_mutates_list_in_place(self):
        original = (0, "Address1")
        previous_locations = [original]
        truck_id = 1
        address = "Address2"

        before_id = id(previous_locations)
        dh.update_previous_location(previous_locations, truck_id, address)

        assert id(previous_locations) == before_id

    @pytest.mark.parametrize("truck_id", [
        "String",
        1.0,
        (True, False),
        frozenset([1, 2]),
        None,
        [1, 2, 3],
        {"id": 5},
    ])
    def test_update_previous_location_accepts_any_truck_id_type(self, truck_id):
        previous_locations = []

        dh.update_previous_location(previous_locations, truck_id, "Address")

        assert previous_locations == [(truck_id, "Address")]

    def test_get_previous_location_returns_address_when_truck_id_exists(self):
        previous_locations = [(0, "Address1"), (1, "Address2")]

        address = dh.get_previous_location(previous_locations, 1)

        assert address == "Address2"

    def test_get_previous_location_returns_none_when_truck_id_not_present(self):
        previous_locations = [(0, "Address1"), (1, "Address2")]

        address = dh.get_previous_location(previous_locations, 2)

        assert address is None

    def test_get_previous_location_returns_none_when_prev_locations_list_empty(self):
        previous_locations = []

        address = dh.get_previous_location(previous_locations, 1)

        assert address is None

    def test_update_previous_time_appends_new_entry_when_list_is_empty(self):
        previous_times = []
        truck_id = 0
        timestamp = time(8, 0)

        dh.update_previous_time(previous_times, truck_id, timestamp)

        assert len(previous_times) == 1
        assert previous_times == [(truck_id, timestamp)]

    def test_update_previous_time_appends_new_entry_for_new_truck_id(self):
        previous_times = [(0, time(8, 0))]
        truck_id = 1
        timestamp = time(8, 30)

        dh.update_previous_time(previous_times, truck_id, timestamp)

        assert len(previous_times) == 2
        assert previous_times[1] == (truck_id, timestamp)

    def test_update_previous_time_updates_existing_entry_for_same_truck_id(self):
        previous_times = [(0, time(8, 30))]
        truck_id = 0
        timestamp = time(18, 30)

        dh.update_previous_time(previous_times, truck_id, timestamp)

        assert len(previous_times) == 1
        assert previous_times[0] == (truck_id, timestamp)

    def test_update_previous_time_preserves_order_when_updating_existing_entry(self):
        first = (0, time(1, 0))
        second = (1, time(2, 0))
        previous_times = [first, second]
        truck_id = 1
        timestamp = time(3, 0)

        dh.update_previous_time(previous_times, truck_id, timestamp)

        assert len(previous_times) == 2
        assert previous_times[0] == first
        assert previous_times[1] == (truck_id, timestamp)

    def test_update_previous_time_mutates_list_in_place(self):
        original = (0, time(8, 0))
        previous_times = [original]
        truck_id = 1
        timestamp = time(9, 30)

        before_id = id(previous_times)
        dh.update_previous_time(previous_times, truck_id, timestamp)

        assert id(previous_times) == before_id

    @pytest.mark.parametrize("truck_id", [
        "String",
        1.0,
        (True, False),
        frozenset([1, 2]),
        None,
        [1, 2, 3],
        {"id": 5},
    ])
    def test_update_previous_time_accepts_any_truck_id_type(self, truck_id):
        previous_times = []

        dh.update_previous_time(previous_times, truck_id, time(8, 30))
        assert previous_times == [(truck_id, time(8, 30))]

    def test_get_previous_time_returns_time_when_truck_id_exists(self):
        previous_times = [(0, time(1, 0)), (1, time(2, 0))]

        timestamp = dh.get_previous_time(previous_times, 1)

        assert timestamp == time(2, 0)

    def test_get_previous_time_returns_none_when_truck_id_not_present(self):
        previous_times = [(0, time(1, 0)), (1, time(2, 0))]

        timestamp = dh.get_previous_time(previous_times, 2)

        assert timestamp is None

    def test_get_previous_time_returns_none_when_prev_times_list_empty(self):
        previous_times = []

        timestamp = dh.get_previous_time(previous_times, 1)

        assert timestamp is None

    #def test_copy_package(self):

    #def test_get_address_at_time(self):
