# tests/test_route_optimizer.py
from datetime import time
import package
import pytest
import route_optimizer as ro

def make_pkg(id_):
    return package.Package(id_, "Address", "City", "ST", 99999, None, 1.0, None, "at_the_hub", None, None, 0, 0)
    
def fake_get_route_departure_time(_route):
    return time(8, 0)

class TestRouteOptimizer:
    def test_check_route_feasibility_returns_true_when_no_deadlines(self):
        route = [make_pkg(i) for i in range(5)]
        for pkg in route: pkg.delivery_deadline = package.Package.EOD_TIME

        feasibility = ro.check_route_feasibility(route, speed_mph=18, verbosity=0)

        assert feasibility is True

    def test_check_route_feasibility_returns_false_when_first_stop_misses_deadline(self, monkeypatch):
        pkg = make_pkg(0)
        pkg.delivery_deadline = time(8, 30)

        def fake_get_arrival_time(*args):
            return time(8, 31)

        monkeypatch.setattr(ro, "get_arrival_time", fake_get_arrival_time)
        monkeypatch.setattr(ro, "get_route_departure_time", fake_get_route_departure_time)

        feasibility = ro.check_route_feasibility([pkg], speed_mph=18, verbosity=0)

        assert feasibility is False

    def test_check_route_feasibility_returns_false_when_any_stop_misses_deadline(self, monkeypatch):
        route = [make_pkg(i) for i in range(5)]
        for n, pkg in enumerate(route):
            pkg.delivery_deadline = time(8+n, 30)
            pkg.address = f"Address{n}"

        times = [time(8,30), time(9,30), time(10,30), time(11,30), time(12,31)]
        it = iter(times)
        monkeypatch.setattr(ro, "get_arrival_time", lambda *args: next(it))
        monkeypatch.setattr(ro, "get_route_departure_time", fake_get_route_departure_time)

        feasibility = ro.check_route_feasibility(route, speed_mph=18, verbosity=0)

        assert feasibility is False

    def test_check_route_feasibility_skips_consecutive_same_address(self, monkeypatch):
        pkg0, pkg1 = make_pkg(0), make_pkg(1)
        pkg0.address = pkg1.address = "3318 W Northwest Blvd"
        pkg0.delivery_deadline = time(9, 1)
        pkg1.delivery_deadline = time(0, 1)

        calls = []
        def fake_get_arrival_time(*args):
            calls.append((args))
            return time(9, 0)

        monkeypatch.setattr(ro, "get_arrival_time", fake_get_arrival_time)
        monkeypatch.setattr(ro, "get_route_departure_time", fake_get_route_departure_time)

        feasibility = ro.check_route_feasibility([pkg0, pkg1], speed_mph=18, verbosity=0)

        assert len(calls) == 1
        assert feasibility is True

    def test_check_route_feasibility_returns_true_when_all_deadlines_met(self, monkeypatch):
        route = [make_pkg(i) for i in range(5)]
        for n, pkg in enumerate(route):
            pkg.delivery_deadline = time(8+n, 31)
            pkg.address = f"Address{n}"

        times = [time(8,30), time(9,30), time(10,30), time(11,30), time(12,30)]
        it = iter(times)
        monkeypatch.setattr(ro, "get_arrival_time", lambda *args: next(it))
        monkeypatch.setattr(ro, "get_route_departure_time", fake_get_route_departure_time)

        feasibility = ro.check_route_feasibility(route, speed_mph=18, verbosity=0)

        assert feasibility is True

    def test_convert_route_to_package_list_looks_up_packages_by_id_and_skips_none(self, monkeypatch):
        route = [
            (None if n == 0 or n == 4 else n, '_') 
            for n in range(5)
        ]

        class FakeWarehouseHash:
            def search(self, package_id):
                return make_pkg(package_id)

        monkeypatch.setattr(ro, "get_warehouse_hash", lambda: FakeWarehouseHash())

        package_list = ro.convert_route_to_package_list(route)

        ids = [pkg.package_id for pkg in package_list]

        assert len(package_list) == 3
        assert ids == [1, 2, 3]