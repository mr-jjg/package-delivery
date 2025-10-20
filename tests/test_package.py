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
    
def test_parse_delayed_package_valid_time_and_none_inputs():
    assert package.parse_delayed_package("10:30 am") == time(10, 30)
    assert package.parse_delayed_package("9:05 PM") == time(21, 5)
    
    assert package.parse_delayed_package("") is None
    assert package.parse_delayed_package("None") is None
    assert package.parse_delayed_package(None) is None

def test_parse_special_note_delayed_and_x_and_mixed_casts(make_packages):
    packages = make_packages()
    #package.Package(2, "None"),
    #package.Package(3, "D, 9:05 AM"),
    #package.Package(4, "X, 10:20 AM, 410 S State St, Salt Lake City, UT, 84111")
    
    packages[2].parse_special_note()
    packages[3].parse_special_note()
    
    assert packages[1].parse_special_note() == ['None']
    assert packages[2].parse_special_note() == ['D', time(9, 5)]
    assert packages[3].parse_special_note() == ['X', time(10, 20), '410 S State St', 'Salt Lake City', 'UT', 84111]
    
def test_get_special_note_str_various_inputs(make_packages):
    packages = make_packages()
    #package.Package(1, "T, 2"),
    #package.Package(2, "None"),
    #package.Package(3, "D, 9:05 AM"),
    #package.Package(4, "X, 10:20 AM, 410 S State St, Salt Lake City, UT, 84111"),
    #package.Package(5, "W, 15, 19")
    
    assert packages[0].get_special_note_str() == "T, 2"
    assert packages[1].get_special_note_str() == "None"
    assert packages[2].get_special_note_str() == "D, 09:05 AM"
    assert packages[3].get_special_note_str() == "X, 10:20 AM, 410 S State St, Salt Lake City, UT, 84111"
    assert packages[4].get_special_note_str() == "W, 15, 19"

def test_get_deadline_str_for_none_eod_and_time(make_packages):
    packages = make_packages()
    #package.Package(1, "10:00 AM"),
    #package.Package(2, ""),
    #package.Package(3, "EOD"),
    #package.Package(4, "12:00 PM"),
    #package.Package(5, "4:00 PM"),
    
    assert packages[0].get_deadline_str() == "10:00 AM"
    assert packages[1].get_deadline_str() == "None"
    assert packages[2].get_deadline_str() == "EOD"
    assert packages[3].get_deadline_str() == "12:00 PM"
    assert packages[4].get_deadline_str() == "04:00 PM"

def test_get_time_str_for_none_and_time():    
    assert package.get_time_str(None) == "None"
    assert package.get_time_str(time(1, 1)) == "01:01 AM"
    assert package.get_time_str(time(12, 0)) == "12:00 PM"
    assert package.get_time_str(time(23, 59)) == "11:59 PM"

def test_try_casting_to_int_numeric_and_non_numeric():
    assert package.try_casting_to_int('0') == 0
    assert package.try_casting_to_int('int') == 'int'

def test_print_package_list_captures_expected_columns(capsys):
    count_columns = lambda line: line.count(" | ") + 1 if " | " in line else 0

    p1 = package.Package(1, "123 Main", "Town", "ST", "00000", "EOD", 1.0, "X, 9:00 AM")
    p2 = package.Package(2, "456 Broad Ave", "City", "TS", "11111", "10:30 AM", 2.5, None)
    p2.truck = 0

    package.print_package_list([p1, p2])
    out = capsys.readouterr().out
    lines = [ln for ln in out.strip().splitlines() if ln.strip()]

    header, sep, row1, row2 = lines[0], lines[1], lines[2], lines[3]

    assert "ID | Address" in header
    assert count_columns(header) == count_columns(row1) == count_columns(row2)
    assert len(sep) == len(header)

    assert "123 Main" in row1
    assert "11:59 PM" in row1
    assert "X" in row1

    assert "456 Broad Ave" in row2
    assert "10:30 AM" in row2
    assert "None" in row2

def test_print_group_list_shows_group_sizes_and_delegates(capsys, monkeypatch):
    calls = []
    monkeypatch.setattr(package, "print_package_list",
                        lambda groups: calls.append(groups))

    p1 = package.Package(1, "A", "C1", "S", "00001", "EOD", 1.0, None)
    p2 = package.Package(2, "B", "C2", "S", "00002", "EOD", 1.0, None)
    p3 = package.Package(3, "C", "C3", "S", "00003", "EOD", 1.0, None)

    group_list = [[p1, p2], [p3]]

    package.print_group_list(group_list)
    out = capsys.readouterr().out.strip().splitlines()

    assert any("Sum of all groups: 3" in line for line in out)

    assert any("Group 0 | Size 2" in line for line in out)
    assert any("Group 1 | Size 1" in line for line in out)

    assert len(calls) == 2
    assert calls[0] == [p1, p2]
    assert calls[1] == [p3]
