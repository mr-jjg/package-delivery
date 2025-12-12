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

@pytest.fixture
def handler_truck_package():
    handler = dh.DeliveryHandler()
    handler.previous_locations = []
    handler.previous_times = []
    handler.delivery_list = []
    handler.RATE = 60 # Avoid strange time division

    trk = truck.Truck(0)
    trk.speed_mph = 18
    trk.route_distance = 0.0

    pkg = make_pkg(0)
    pkg.address = "1702 S Grand"
    pkg.city = "Spokane"
    pkg.state = "WA"
    pkg.zip_code = 99203
    pkg.special_note = None
    pkg.address_history = []

    return handler, trk, pkg

@pytest.fixture
def fake_time_and_distance(monkeypatch):
    calls = {}

    def fake_get_previous_location(prev_list, truck_id):
        calls["get_previous_location"] = (list(prev_list), truck_id)
        return "1002 W Riverside Ave"

    def fake_get_previous_time(prev_times, truck_id):
        calls["get_previous_time"] = (list(prev_times), truck_id)
        return time(8, 0)

    def fake_get_arrival_time(last_time, last_loc, dest_addr, speed_mph):
        calls["get_arrival_time"] = (last_time, last_loc, dest_addr, speed_mph)
        return time(8, 5)

    def fake_get_travel_time_in_minutes(start, end):
        calls["get_travel_time_in_minutes"] = (start, end)
        return 5

    def fake_get_distance(start, end):
        calls["get_distance"] = (start, end)
        return 2.3

    def fake_sleep(_minutes):
        calls["sleep"] = _minutes

    def fake_update_prev_location(prev_list, truck_id, addr):
        calls["update_prev_location"] = (list(prev_list), truck_id, addr)
        prev_list.append((truck_id, addr))

    def fake_update_prev_time(prev_times, truck_id, new_time):
        calls["update_prev_time"] = (list(prev_times), truck_id, new_time)
        prev_times.append((truck_id, new_time))

    monkeypatch.setattr(dh, "get_previous_location", fake_get_previous_location)
    monkeypatch.setattr(dh, "get_previous_time", fake_get_previous_time)
    monkeypatch.setattr(dh, "get_arrival_time", fake_get_arrival_time)
    monkeypatch.setattr(dh, "get_travel_time_in_minutes", fake_get_travel_time_in_minutes)
    monkeypatch.setattr(dh, "get_distance", fake_get_distance)
    monkeypatch.setattr(dh.simulate_real_time, "sleep", fake_sleep)
    monkeypatch.setattr(dh, "update_previous_location", fake_update_prev_location)
    monkeypatch.setattr(dh, "update_previous_time", fake_update_prev_time)

    return calls

class TestBuildDeliveryList:
    def test_calls_separate_trucks_by_driver_status_with_fleet(self, monkeypatch):
        fl, tr1, tr2 = make_fleet_with_two_trucks()

        count, passed_fleet = 0, None
        def fake_separate_trucks_by_driver_status(fleet_):
            nonlocal count, passed_fleet
            count += 1
            passed_fleet = fleet_
            return [tr1], [tr2]

        monkeypatch.setattr(dh, "separate_trucks_by_driver_status", fake_separate_trucks_by_driver_status)

        handler = dh.DeliveryHandler()
        handler.build_delivery_list(fl)

        assert count == 1
        assert passed_fleet is fl

    def test_calls_generate_delivery_timeline_first_with_available_trucks(self, monkeypatch):
        fl, tr1, tr2 = make_fleet_with_two_trucks()
        tr1.driver = "Leonard"

        trucks = {"available": [], "waiting": []}
        calls = []
        def fake_generate_delivery_timeline(self, truck_list):
            if all(tr.driver for tr in truck_list):
                calls.append("available")
                trucks["available"].append(list(truck_list))
            else:
                calls.append("waiting")
                trucks["waiting"].append(list(truck_list))

        monkeypatch.setattr(dh.DeliveryHandler, "generate_delivery_timeline", fake_generate_delivery_timeline)

        handler = dh.DeliveryHandler()
        handler.build_delivery_list(fl)

        assert trucks["available"] == [[tr1]]
        assert trucks["waiting"] == [[tr2]]
        assert calls == ["available", "waiting"]

    def test_sets_departure_time_for_waiting_trucks_to_earliest_return_time(self):
        fl = fleet.Fleet(3)
        tr1, tr2, tr3 = fl.truck_list
        tr1.driver, tr2.driver = "Bill", "Ted"
        tr1.return_time, tr2.return_time = time(8, 0), time(9, 0)

        handler = dh.DeliveryHandler()
        handler.build_delivery_list(fl)

        assert tr3.departure_time == time(8, 0)

    def test_does_not_change_departure_time_for_available_trucks(self, monkeypatch):
        fl, tr1, tr2 = make_fleet_with_two_trucks()
        tr1.driver, tr2.driver = "Bill", "Ted"

        ititial_departure1 = tr1.departure_time = time(8, 0)
        ititial_departure2 = tr2.departure_time = time(9, 0)

        def fake_separate_trucks_by_driver_status(fleet_):
            return [tr1, tr2], []

        monkeypatch.setattr(dh, "separate_trucks_by_driver_status", fake_separate_trucks_by_driver_status)

        def fake_generate_delivery_timeline(self, truck_list):
            for tr in truck_list:
                tr.return_time = time(10, 0)

        monkeypatch.setattr(dh.DeliveryHandler, "generate_delivery_timeline", fake_generate_delivery_timeline)

        handler = dh.DeliveryHandler()
        handler.build_delivery_list(fl)

        assert tr1.departure_time == ititial_departure1
        assert tr2.departure_time == ititial_departure2

    def test_build_delivery_list_sorts_delivery_list_by_time_after_generating_timelines(self, monkeypatch):
        fl, tr1, tr2 = make_fleet_with_two_trucks()
        tr1.driver = "Bill"
        tr2.driver = "Ted"

        def fake_separate_trucks_by_driver_status(fleet_):
            return [tr1, tr2], []

        monkeypatch.setattr(dh, "separate_trucks_by_driver_status", fake_separate_trucks_by_driver_status)

        def fake_generate_delivery_timeline(self, truck_list):
            if not truck_list: return
            tr = truck_list[0]
            self.delivery_list.extend([
                (tr, None, time(10, 0), dh.DeliveryAction.DEPART),
                (tr, None, time(9, 0), dh.DeliveryAction.DEPART),
                (tr, None, time(11, 0), dh.DeliveryAction.DEPART),
            ])

        monkeypatch.setattr(dh.DeliveryHandler, "generate_delivery_timeline", fake_generate_delivery_timeline)

        handler = dh.DeliveryHandler()
        handler.build_delivery_list(fl)

        times = [delivery[2] for delivery in handler.delivery_list]

        assert times == [time(9, 0), time(10, 0), time(11, 0)]

class TestGenerateDeliveryTimeline:
    def test_adds_depart_deliver_and_return_events_for_single_truck_single_package(self, monkeypatch):
        tr = truck.Truck(0)
        tr.package_list = [make_pkg(0)]
        tr.departure_time = time(8, 0)
        tr.departure_address = "Departure Address"

        monkeypatch.setattr(dh, "get_arrival_time", lambda *_: time(8, 30))

        handler = dh.DeliveryHandler()
        handler.generate_delivery_timeline([tr])

        assert len(handler.delivery_list) == 3
        assert handler.delivery_list == [
            (tr, None, time(8, 0), dh.DeliveryAction.DEPART),
            (tr, tr.package_list[0], time(8, 30), dh.DeliveryAction.DELIVER),
            (tr, None, time(8, 30), dh.DeliveryAction.RETURN)
        ]

    def test_sets_truck_return_time_to_time_from_return_event(self, monkeypatch):
        tr = truck.Truck(0)
        tr.package_list = [make_pkg(0)]
        tr.departure_time = time(8, 0)
        tr.departure_address = "Departure Address"

        monkeypatch.setattr(dh, "get_arrival_time", lambda *_: time(8, 30))

        handler = dh.DeliveryHandler()
        handler.generate_delivery_timeline([tr])

        assert tr.return_time == time(8, 30)

    def test_adds_one_deliver_event_per_package_on_route(self, monkeypatch):
        tr = truck.Truck(0)
        tr.package_list = [make_pkg(i) for i in range(10)]
        tr.departure_time = time(8, 0)
        tr.departure_address = "Departure Address"

        monkeypatch.setattr(dh, "get_arrival_time", lambda *_: time(8, 30))

        handler = dh.DeliveryHandler()
        handler.generate_delivery_timeline([tr])

        delivered_total = sum([1 for delivery in handler.delivery_list if delivery[3] == dh.DeliveryAction.DELIVER])
        assert delivered_total == len(tr.package_list)

        delivered_pkgs = [delivery[1] for delivery in handler.delivery_list if delivery[3] == dh.DeliveryAction.DELIVER]
        assert delivered_pkgs == tr.package_list

    def test_calls_get_arrival_time_for_first_leg_with_departure_address_and_first_package_address(self, monkeypatch):
        tr = truck.Truck(0)
        first_pkg = make_pkg(0)
        tr.package_list = [first_pkg]
        tr.departure_time = time(8, 0)
        tr.departure_address = "Departure Address"

        calls = []
        def fake_get_arrival_time(departure_time, start_point, end_point, speed_mph):
            calls.append((departure_time, start_point, end_point, speed_mph))
            return time(9, 15)

        monkeypatch.setattr(dh, "get_arrival_time", fake_get_arrival_time)

        handler = dh.DeliveryHandler()
        handler.generate_delivery_timeline([tr])

        departure_time, start_point, end_point, speed_mph = calls[0]
        assert departure_time == tr.departure_time
        assert start_point == tr.departure_address
        assert end_point == first_pkg.address
        assert speed_mph == tr.speed_mph

        _, pkg_in_tup, timestamp, _ = handler.delivery_list[1]
        assert pkg_in_tup is first_pkg
        assert timestamp == time(9, 15)

    def test_calls_get_arrival_time_for_each_subsequent_leg_starting_from_previous_arrival_time(self, monkeypatch):
        tr = truck.Truck(0)
        tr.package_list = [make_pkg(i) for i in range(3)]
        tr.departure_time = time(8, 0)
        tr.departure_address = "Departure Address"

        calls = []
        returns = []
        sentinels = [object() for _ in range(10)]

        def fake_get_arrival_time(departure_time, start_point, end_point, speed_mph):
            idx = len(calls)
            calls.append((departure_time, start_point, end_point, speed_mph))
            ret = sentinels[idx]
            returns.append(ret)
            return ret

        monkeypatch.setattr(dh, "get_arrival_time", fake_get_arrival_time)

        handler = dh.DeliveryHandler()
        handler.generate_delivery_timeline([tr])

        assert len(calls) >= 2
        for i in range(1, len(calls)):
            departure_time, _, _, _ = calls[i]
            assert departure_time is returns[i - 1]

    def test_calls_get_arrival_time_for_each_subsequent_leg_with_previous_and_current_package_addresses(self, monkeypatch):
        tr = truck.Truck(0)
        tr.package_list = [make_pkg(i) for i in range(3)]
        tr.departure_time = time(8, 0)
        tr.departure_address = "Departure Address"
        for i, pkg in enumerate(tr.package_list):
            pkg.address = f"Address {i}"

        calls = []
        def fake_get_arrival_time(departure_time, start_point, end_point, speed_mph):
            calls.append((departure_time, start_point, end_point, speed_mph))
            return object()

        monkeypatch.setattr(dh, "get_arrival_time", fake_get_arrival_time)

        handler = dh.DeliveryHandler()
        handler.generate_delivery_timeline([tr])

        route = tr.package_list
        assert len(calls) == len(route) + 1

        for leg_index in range(1, len(route)):
            _, start_point, end_point, _ = calls[leg_index]

            prev_pkg = route[leg_index - 1]
            curr_pkg = route[leg_index]

            assert start_point == prev_pkg.address
            assert end_point == curr_pkg.address

    def test_calls_get_arrival_time_for_return_leg_with_last_package_address_and_departure_address(self, monkeypatch):
        tr = truck.Truck(0)
        tr.package_list = [make_pkg(0), make_pkg(1)]
        tr.departure_time = time(8, 0)
        tr.departure_address = "Warehouse"
        for i, pkg in enumerate(tr.package_list):
            pkg.address = f"Address {i}"

        calls = []
        def fake_get_arrival_time(departure_time, start_point, end_point, speed_mph):
            calls.append((departure_time, start_point, end_point, speed_mph))
            return time(9, 0)

        monkeypatch.setattr(dh, "get_arrival_time", fake_get_arrival_time)

        handler = dh.DeliveryHandler()
        handler.generate_delivery_timeline([tr])

        assert len(calls) > 1
        _, last_pkg_addr, departure_address, _ = calls[-1]
        assert last_pkg_addr == "Address 1"
        assert departure_address == "Warehouse"
        assert tr.return_time == time(9, 0)

    def test_appends_events_to_existing_delivery_list_without_clearing_it(self, monkeypatch):
        tr = truck.Truck(0)
        tr.package_list = [make_pkg(0)]
        tr.departure_time = time(8, 0)
        tr.departure_address = "Warehouse"
        tr.package_list[0].address = "Pkg Address"

        calls = []
        def fake_get_arrival_time(departure_time, start_point, end_point, speed_mph):
            calls.append((departure_time, start_point, end_point, speed_mph))
            return object()

        monkeypatch.setattr(dh, "get_arrival_time", fake_get_arrival_time)

        handler = dh.DeliveryHandler()
        sentinal = ("truck", "Package", "Arrival time", "Action")
        handler.delivery_list.append(sentinal)
        handler.generate_delivery_timeline([tr])

        assert handler.delivery_list[0] is sentinal
        assert len(handler.delivery_list) == 4

    def test_does_not_modify_truck_departure_time_values(self, monkeypatch):
        tr0 = truck.Truck(0)
        tr1 = truck.Truck(1)
        tr0.package_list = [make_pkg(0), make_pkg(1)]
        tr1.package_list = [make_pkg(2), make_pkg(3)]
        test_departure_time = time(8, 0)
        tr0.departure_time = test_departure_time
        tr1.departure_time = test_departure_time

        def fake_get_arrival_time(departure_time, start_point, end_point, speed_mph):
            return time(9, 0)

        monkeypatch.setattr(dh, "get_arrival_time", fake_get_arrival_time)

        handler = dh.DeliveryHandler()
        handler.generate_delivery_timeline([tr0, tr1])

        assert tr0.departure_time is test_departure_time
        assert tr1.departure_time is test_departure_time

class TestActionHandlers:
    def test_handle_delivery_action_departed_sets_all_packages_en_route(self):
        tr = truck.Truck(0)
        tr.package_list = [make_pkg(i) for i in range(10)]

        handler = dh.DeliveryHandler()
        handler.handle_delivery_action_departed(tr)

        assert all([pkg.delivery_status == 'en_route' for pkg in tr.package_list])

    def test_handle_delivery_action_departed_updates_previous_location_with_departure_address(self):
        tr = truck.Truck(0)
        tr.departure_address = "5018 W. Montrose Ave"

        handler = dh.DeliveryHandler()
        handler.handle_delivery_action_departed(tr)

        assert handler.previous_locations[0] == (tr.truck_id, "5018 W. Montrose Ave")

    def test_handle_delivery_action_departed_updates_previous_time_with_departure_time(self):
        tr = truck.Truck(0)
        tr.departure_time = time(11, 30)

        handler = dh.DeliveryHandler()
        handler.handle_delivery_action_departed(tr)

        assert handler.previous_times[0] == (tr.truck_id, time(11, 30))

    def test_handle_delivery_action_delivered_updates_truck_and_package_and_previous_state(self, handler_truck_package, fake_time_and_distance):
        handler, tr, pkg = handler_truck_package
        handler.previous_locations = [(tr.truck_id, "507 N Howard St")]
        handler.previous_times = [(tr.truck_id, time(7, 0))]

        delivery_time = time(8, 30)
        handler.handle_delivery_action_delivered(delivery_time, pkg, tr)

        calls = fake_time_and_distance

        assert calls["get_previous_location"][1] == tr.truck_id
        assert calls["get_previous_time"][1] == tr.truck_id

        last_time, last_loc, dest_addr, speed = calls["get_arrival_time"]
        assert dest_addr == pkg.address
        assert speed == tr.speed_mph

        start, end = calls["get_distance"]
        assert start == "1002 W Riverside Ave"
        assert end == pkg.address

        assert "sleep" in calls
        assert calls["sleep"] == 5 / handler.RATE

        assert tr.route_distance == 2.3

        assert handler.previous_locations[-1] == (tr.truck_id, pkg.address)
        assert handler.previous_times[-1][0] == tr.truck_id

        assert pkg.delivery_status == "delivered"
        assert pkg.time_of_delivery == delivery_time

    def test_handle_delivery_action_delivered_ignores_special_note_until_correction_time(self, handler_truck_package, fake_time_and_distance):
        handler, tr, pkg = handler_truck_package

        correction_time = time(9, 30)
        pkg.special_note = ['X', correction_time, "9711 W Charles Rd", "Nine Mile Falls", "_WA_", 99026]

        handler.delivery_list = [(tr, pkg, time(10, 0), "Before address")]
        original_delivery_list = list(handler.delivery_list)

        delivery_time = time(8, 30)
        handler.handle_delivery_action_delivered(delivery_time, pkg, tr)

        assert handler.delivery_list == original_delivery_list

        assert pkg.address == "1702 S Grand"
        assert pkg.city == "Spokane"
        assert pkg.state == "WA"
        assert pkg.zip_code == 99203
        assert pkg.address_history == []
        assert pkg.delivery_status == "delivered"
        assert pkg.time_of_delivery == delivery_time

    def test_handle_delivery_action_delivered_updates_special_note_at_correction_time(self, handler_truck_package, fake_time_and_distance):
        handler, tr, pkg = handler_truck_package

        correction_time = time(8, 0)
        pkg.special_note = ['X', correction_time, "9711 W Charles Rd", "Nine Mile Falls", "_WA_", 99026]

        handler.delivery_list = [(tr, pkg, time(10, 0), "Before address")]

        delivery_time = time(9, 30)
        handler.handle_delivery_action_delivered(delivery_time, pkg, tr)

        (tr_entry, pkg_entry, event_time, action) = handler.delivery_list[0]

        assert pkg_entry is pkg  # same object
        assert pkg_entry.address == "9711 W Charles Rd"
        assert pkg.city == "Nine Mile Falls"
        assert pkg.state == "_WA_"
        assert pkg.zip_code == 99026
        assert pkg.address_history == [(time(8, 0), "9711 W Charles Rd")]
        assert pkg.delivery_status == "delivered"
        assert pkg.time_of_delivery == delivery_time

    def test_handle_delivery_action_returned_updates_truck_distance_and_previous_state(self, handler_truck_package, fake_time_and_distance):
        handler, tr, _ = handler_truck_package
        tr.departure_address = "4001 South 700 East"
        
        handler.handle_delivery_action_returned(tr)
        
        assert tr.route_distance == 2.3
        assert handler.previous_locations == [(tr.truck_id, tr.departure_address), (tr.truck_id, tr.departure_address)]
        assert handler.previous_times == [(tr.truck_id, time(8, 5))]

    def test_handle_delivery_action_returned_calls_time_and_distance_helpers_with_departure_address(self, handler_truck_package, fake_time_and_distance):
        handler, tr, pkg = handler_truck_package
        tr.departure_address = "4001 South 700 East"

        handler.handle_delivery_action_returned(tr)

        calls = fake_time_and_distance

        assert calls["get_previous_location"] == ([], tr.truck_id)
        assert calls["get_previous_time"] == ([], tr.truck_id)
        assert calls["get_arrival_time"] == (time(8, 0), "1002 W Riverside Ave", tr.departure_address, tr.speed_mph)
        assert calls["get_distance"] == ("1002 W Riverside Ave", tr.departure_address)
        assert calls["get_travel_time_in_minutes"] == (time(8, 0), time(8, 5))
        assert calls["sleep"] == pytest.approx(5/60)

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

    def test_copy_package_creates_new_package_with_copied_fields_and_overrides(self):
        def snapshot(pkg):
            return (pkg.address, pkg.city, pkg.state, pkg.zip_code, pkg.delivery_deadline, pkg.weight_kilo, pkg.special_note, pkg.group, pkg.priority)

        pkg = make_pkg(0)
        pkg.delivery_status = 'X'
        pkg.time_of_delivery = 'X'
        pkg.truck = '0'
        before = snapshot(pkg)

        new_pkg = dh.copy_package(pkg, 1)

        after = snapshot(new_pkg)

        assert new_pkg is not pkg
        assert before == after
        assert new_pkg.delivery_status == 'at_the_hub'
        assert new_pkg.time_of_delivery is None
        assert new_pkg.truck == 1

    def test_copy_package_uses_separate_address_history_list(self):
        pkg = make_pkg(0)
        pkg.address_history = [(time(9, 0), "First Address"), (time(9, 30), "Second Address")]

        new_pkg = dh.copy_package(pkg, 1)

        assert new_pkg.address_history == pkg.address_history
        assert id(new_pkg.address_history) != id(pkg.address_history)

        new_pkg.address_history.append((time(10, 0), "Third Address"))
        assert (time(10, 0), "Third Address") not in pkg.address_history

    def test_copy_package_handles_empty_address_history(self):
        pkg = make_pkg(0)
        pkg.address_history = []

        new_pkg = dh.copy_package(pkg, 1)

        assert new_pkg.address_history == []
        assert id(new_pkg.address_history) != id(pkg.address_history)

    def test_get_address_at_time_returns_first_address_when_time_before_first_timestamp(self):
        pkg = make_pkg(0)
        pkg.address_history = [
            (time(9, 0), "First Address"),
            (time(10, 0), "Second Address"),
            (time(11, 0), "Third Address"),
        ]

        address = dh.get_address_at_time(pkg, time(8, 30))

        assert address == "First Address"

    def test_get_address_at_time_returns_matching_address_for_exact_timestamp(self):
        pkg = make_pkg(0)
        pkg.address_history = [
            (time(9, 0), "First Address"),
            (time(10, 0), "Second Address"),
            (time(11, 0), "Third Address"),
        ]

        address = dh.get_address_at_time(pkg, time(10, 0))

        assert address == "Second Address"

    def test_get_address_at_time_returns_most_recent_address_before_time_input(self):
        pkg = make_pkg(0)
        pkg.address_history = [
            (time(9, 0), "First Address"),
            (time(10, 0), "Second Address"),
            (time(11, 0), "Third Address"),
        ]

        address = dh.get_address_at_time(pkg, time(10, 30))

        assert address == "Second Address"

    def test_get_address_at_time_returns_last_address_when_time_after_last_timestamp(self):
        pkg = make_pkg(0)
        pkg.address_history = [
            (time(9, 0), "First Address"),
            (time(10, 0), "Second Address"),
            (time(11, 0), "Third Address"),
        ]

        address = dh.get_address_at_time(pkg, time(11, 30))

        assert address == "Third Address"

    def test_get_address_at_time_uses_first_address_when_first_timestamp_is_none(self):
        pkg = make_pkg(0)
        pkg.address_history = [
            (None, "First Address"),
            (time(10, 0), "Second Address"),
            (time(11, 0), "Third Address"),
        ]

        address = dh.get_address_at_time(pkg, time(9, 30))

        assert address == "First Address"