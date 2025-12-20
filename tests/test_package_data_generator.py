#/tests/test_package_data_generator.py
import csv
import package_data_generator as pdg
import pytest

class TestPackageDataGenerator:
    def test_init_sets_packages_to_num_pkgs(self):
        gen = pdg.PackageDataGenerator(13, 20, 20)

        assert len(gen.packages) == 13
        
@pytest.fixture
def make_address_csv(tmp_path):
    default_rows = default_rows = [
        ["1", "Disneyland", "Anaheim"],
        ["2", "The White House", "Washington"],
        ["3", "The Alamo", "San Antonio"],
        ["4", "Niagara Falls", "Niagara Falls"],
        ["5", "Peter Griffin's House", "Quahog"]
    ]
    
    def _make(rows=None, name="addresses.csv"):
        if rows is None:
            rows = default_rows
        path = tmp_path / name
        with path.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerows(rows)
        return path
    return _make
    
def test_read_address_data_happy_path(make_address_csv):
    csv_path = make_address_csv()
    
    address_list = pdg.read_address_data(csv_path)
    
    assert len(address_list) == 5
    for address in address_list:
        assert len(address) == 3
        assert isinstance(address[0], int)
    assert address_list[0][1] == "Disneyland"
    assert address_list[4][2] == "Quahog"

def test_read_address_data_raises_on_nonint_id(tmp_path):
    bad_row = [
        ["X", "Toronto", "Nowhere Street"]
    ]
    path = tmp_path / "bad_addresses.csv"
    with path.open('w', newline='') as f:
        w = csv.writer(f)
        w.writerows(bad_row)
    
    with pytest.raises(ValueError) as exc_info:
        bad_list = pdg.read_address_data(path)
    
    assert "invalid literal" in str(exc_info.value) or "int" in str(exc_info.value)

def test_parse_args_returns_default_values():
    argv = []
    
    NUM_PKGS, PCT_CONSTRAINTS, PCT_DEADLINES, DL_LOWER_BOUND, DL_UPPER_BOUND = pdg.parse_args(argv)

    assert NUM_PKGS == 20
    assert PCT_CONSTRAINTS == 20
    assert PCT_DEADLINES == 20
    assert DL_LOWER_BOUND == 9
    assert DL_UPPER_BOUND == 18

def test_parse_args_returns_non_default_values():
    argv = ['-n', '30', '-c', '25', '-d', '75', '-l', '13', '-u', '14']
    
    NUM_PKGS, PCT_CONSTRAINTS, PCT_DEADLINES, DL_LOWER_BOUND, DL_UPPER_BOUND = pdg.parse_args(argv)

    assert NUM_PKGS == 30
    assert PCT_CONSTRAINTS == 25
    assert PCT_DEADLINES == 75
    assert DL_LOWER_BOUND == 13
    assert DL_UPPER_BOUND == 14
    
def test_parse_args_adjusts_to_floor_for_all_low_values():
    argv = ['-n', '19', '-c', '-1', '-d', '-1', '-l', '8', '-u', '9']

    NUM_PKGS, PCT_CONSTRAINTS, PCT_DEADLINES, DL_LOWER_BOUND, DL_UPPER_BOUND = pdg.parse_args(argv)

    assert NUM_PKGS == 20
    assert PCT_CONSTRAINTS == 0
    assert PCT_DEADLINES == 0
    assert DL_LOWER_BOUND == 9
    assert DL_UPPER_BOUND == 10
    
def test_parse_args_adjusts_to_ceiling_for_all_high_values():
    argv = ['-n', '41', '-c', '100', '-d', '100', '-l', '17', '-u', '19']

    NUM_PKGS, PCT_CONSTRAINTS, PCT_DEADLINES, DL_LOWER_BOUND, DL_UPPER_BOUND = pdg.parse_args(argv)

    assert NUM_PKGS == 40
    assert PCT_CONSTRAINTS == 100
    assert PCT_DEADLINES == 100
    assert DL_LOWER_BOUND == 16
    assert DL_UPPER_BOUND == 18