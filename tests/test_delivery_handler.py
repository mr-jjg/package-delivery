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

    #def test_unpack_delivery_tuple(self):

    #def test_update_previous_location(self):

    #def test_get_previous_location(self):

    #def test_update_previous_time(self):

    #def test_get_previous_time(self):

    #def test_copy_package(self):

    #def test_get_address_at_time(self):
