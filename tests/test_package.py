# tests/test_package.py
from datetime import time, datetime
import package
import pytest

@pytest.fixture
def make_packages():
    #new_package = Package(package_id, address, city, state, zip_code, delivery_deadline, weight_kilo, special_note)
    def _make_packages():
        return [
            package.Package(1, "123 Maple Street", "Springfield", "IL", "62701", "10:00 AM", 2.5, "T, 2"),
            package.Package(2, "456 Oak Avenue", "Chicago", "IL", "60614", "", 5.0, "None"),
            package.Package(3, "789 Pine Road", "Naperville", "IL", "60540", "EOD", 1.2, "D, 9:05 AM"),
            package.Package(4, "321 Birch Lane", "Peoria", "IL", "61602", "12:00 PM", 3.3, "X, 10:20 AM, 410 S State St, Salt Lake City, UT, 84111"),
            package.Package(5, "654 Cedar Street", "Champaign", "IL", "61820", "4:00 PM", 4.8, "W, 15, 19"),
        ]
    return _make_packages

def test_init_sets_core_fields_and_address_history(make_packages):
    # Package(1, "123 Maple Street", "Springfield", "IL", "62701", "10:00 AM", 2.5, "T, 2")
    p1 = make_packages()[0]
    
    # Basic attributes
    assert p1.package_id == 1
    assert p1.address == "123 Maple Street"
    assert p1.city == "Springfield"
    assert p1.state == "IL"
    assert p1.zip_code == "62701"
    assert p1.weight_kilo == 2.5
    assert p1.special_note == "T, 2"

    # Derived/auto-set fields
    assert p1.address_history == [(None, "123 Maple Street")]
    assert isinstance(p1.delivery_deadline, time)
    assert p1.delivery_deadline == time(10, 0)  # parsed from "10:00 AM"
    assert p1.time_of_delivery is None  # forced to None in constructor

    # Defaults for optional fields
    assert p1.delivery_status == "at_the_hub"
    assert p1.truck is None
    assert p1.group is None
    assert p1.priority is None

def test_init_parses_deadline_strs_none_and_eod(make_packages):
    packages = make_packages()
    p2 = packages[1] # delivery_deadline: ""
    p3 = packages[2] # delivery_deadline: "EOD"
    
    assert p2.delivery_deadline == None
    assert isinstance(p3.delivery_deadline, time)
    assert p3.delivery_deadline == time(23, 59)

def test_time_of_delivery_is_forced_none_despite_ctor_arg():
    sample_package = package.Package(6, "987 Elm Street", "Decatur", "IL", "62521", "3:00 PM", 2.0, "", "at_the_hub")
    
    assert sample_package.time_of_delivery is None

def test_str_minimal_fields_no_special_note():
    p2 = package.Package(2, "456 Oak Avenue", "Chicago", "IL", "60614", "", 5.0, None)
    s = str(p2)

    assert "Package ID: 2" in s
    assert "Address: 456 Oak Avenue" in s
    assert "Delivery Deadline: None" in s
    assert "Special Note: None" in s
    assert "Delivery Status: at_the_hub" in s
    assert "Delivery Time: None" in s
    assert "Truck: None" in s
    assert "Group: None" in s
    assert "Priority: None" in s

def test_str_truck_offset_and_X_note():
    p = package.Package(7, "1 Test", "C", "S", "Z", "EOD", 1.0, ["X", "9:00 PM"])
    p.truck = 0  # should display as 1
    s = str(p)

    assert "Truck: 1" in s          # offset shown
    assert "Special Note: X" in s   # X collapses to just 'X'
    assert "Delivery Deadline: EOD" in s

def test_lt_compares_by_package_id(make_packages):
    packages = make_packages()
    p1 = packages[0]
    p2 = packages[1]
    p3 = packages[2]
    
    ordered = sorted([p3, p2, p1])
    assert [p.package_id for p in ordered] == [1, 2, 3]

def test_parse_delivery_deadline_variants_parametric():
    dl_is_none = None
    dl_ = ''
    dl_none = 'None'
    dl_eod = 'EOD'
    
    assert package.parse_delivery_deadline(dl_is_none) is None
    assert package.parse_delivery_deadline(dl_) is None
    assert package.parse_delivery_deadline(dl_none) is None
    assert package.parse_delivery_deadline(dl_eod) == time(23, 59)
    

'''
test_parse_delayed_package_valid_time_and_none_inputs

test_parse_special_note_delayed_and_x_and_mixed_casts

test_get_special_note_str_various_inputs

test_get_deadline_str_for_none_eod_and_time

test_get_time_str_for_none_and_time

test_try_casting_to_int_numeric_and_non_numeric

test_print_package_list_captures_expected_columns

test_print_group_list_shows_group_sizes_and_delegates
'''