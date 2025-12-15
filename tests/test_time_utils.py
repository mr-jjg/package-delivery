# tests/test_time_utils.py

from datetime import time
import package
import pytest
import time_utils as tu

def make_pkg(id_):
    return package.Package(id_, "Address", "City", "ST", 99999, None, 1.0, None, "at_the_hub", None, None, 0, 0)

class TestTimeUtils:
    def test_float_to_time_rounds_minutes_correctly(self):
        ret_time = tu.float_to_time(8.49)
        assert ret_time == time(8, 29)

    def test_float_to_time_rolls_over_when_rounds_to_60(self):
        ret_time = tu.float_to_time(8.999)
        assert ret_time == time(9, 0)

    def test_float_to_time_handles_zero_minutes(self):
        ret_time = tu.float_to_time(8.0)
        assert ret_time == time(8, 0)

    def test_get_route_departure_time_defaults_to_0800_when_no_delays(self):
        pkg1, pkg2 = make_pkg(1), make_pkg(2)
        pkg_list = [pkg1, pkg2]

        departure = tu.get_route_departure_time(pkg_list)

        assert departure == time(8, 0)

    def test_get_route_departure_time_uses_latest_delayed_time(self):
        pkg1, pkg2 = make_pkg(1), make_pkg(2)
        pkg1.special_note = ["D", time(8, 30)]
        pkg2.special_note = ["D", time(8, 31)]
        pkg_list = [pkg1, pkg2]

        departure = tu.get_route_departure_time(pkg_list)

        assert departure == time(8, 31)

    def test_get_arrival_time_uses_distance_and_speed(self, monkeypatch):
        departure = time(9, 0)
        start, end = "Here", "There"
        speed = 10.0

        def fake_get_distance(start, end):
            return 30

        monkeypatch.setattr(tu, "get_distance", fake_get_distance)

        arrival = tu.get_arrival_time(departure, start, end, speed)

        assert arrival == time(12, 0)

    def test_calculate_travel_time_adds_minutes_correctly(self):
        now, travel = time(8, 0), time(1, 30)
        ret_time = tu.calculate_travel_time(now, travel)
        assert ret_time == time(9, 30)

    def test_calculate_travel_time_crosses_hour_boundary(self):
        now, travel = time(8, 30), time(0, 40)
        ret_time = tu.calculate_travel_time(now, travel)
        assert ret_time == time(9, 10)

    def test_get_travel_time_in_minutes_returns_delta_minutes(self):
        now, travel = time(8, 40), time(9, 30)
        ret_minutes = tu.get_travel_time_in_minutes(now, travel)
        assert ret_minutes == 50