# tests/test_truck.py
import datetime as dt
from truck import Truck

def test_str_includes_key_fields():
    t = Truck(
        truck_id=0, 
        current_capacity=12, 
        maximum_capacity=16,
        driver="M.E. Archer", 
        departure_time=dt.datetime(2025, 1, 1, 8, 0),
        return_time=dt.datetime(2025, 1, 1, 12, 30),
        departure_address='4001 South 700 East',
        package_list=[]
    )
    s = str(t)
    
    assert "Truck ID: 1" in s
    assert "Current Capacity: 12" in s
    assert "Maximum Capacity: 16" in s
    assert "Departure Time: 08:00 AM" in s
    assert "Return Time: 12:30 PM" in s
    assert "Driver: M.E. Archer" in s
    assert "Packages: None" in s

def test_lt_sorts_by_truck_id():
    t1 = Truck(truck_id=3)
    t2 = Truck(truck_id=1)
    t3 = Truck(truck_id=2)
    ordered = sorted([t1, t2, t3])
    assert [tr.truck_id for tr in ordered] == [1, 2, 3]
    
def test_package_list_defaults_empty():
    t = Truck(package_list=None)
    assert isinstance(t.package_list, list)
    assert t.package_list == []
    # and str() should render "None" when list is empty
    assert "Packages: None" in str(t)

import pytest

@pytest.mark.xfail(reason="Design choice pending: prevent impossible capacity states.")
def test_capacity_never_exceeds_maximum_future():
    t = Truck(current_capacity=17, maximum_capacity=16)
    assert t.current_capacity <= t.maximum_capacity