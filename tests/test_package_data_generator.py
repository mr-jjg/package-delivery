#/tests/test_package_data_generator.py
import csv
import package_data_generator as pdg
import pytest
import random

class TestPackageDataGenerator:
    def test_init_sets_packages_to_num_pkgs(self):
        gen = pdg.PackageDataGenerator(13, 20, 20)

        assert len(gen.packages) == 13

    def test_init_assigns_constraints_and_deadlines_as_floats(self):
        gen = pdg.PackageDataGenerator(13, 20, 20)

        assert isinstance(gen.pct_constraints, float)
        assert isinstance(gen.pct_deadlines, float)
        assert gen.pct_constraints == pytest.approx(0.2)
        assert gen.pct_deadlines == pytest.approx(0.2)

    @pytest.mark.parametrize(
        "args, c_len, d_len",
        [
            ((20, 10, 20), 2, 4),
            ((20, 30, 40), 6, 8),
            ((20, 50, 60), 10, 12),
        ]
    )
    def test_init_constraints_and_deadlines_lists_have_expected_sizes_and_valid_ids(self, args, c_len, d_len):
        gen = pdg.PackageDataGenerator(*args)
        num_pkgs = args[0]

        assert len(gen.constraints_list) == c_len
        assert len(gen.deadlines_list) == d_len
        assert len(set(gen.constraints_list)) == c_len
        assert len(set(gen.deadlines_list)) == d_len
        assert all(0 <= i < num_pkgs for i in gen.constraints_list)
        assert all(0 <= i < num_pkgs for i in gen.deadlines_list)

    @pytest.mark.parametrize(
        "args",
        [
            ((20, 10, 20)),
            ((20, 30, 40)),
            ((20, 50, 60)),
        ]
    )
    def test_init_builds_possible_w_notes_with_constraints_list(self, args):
        gen = pdg.PackageDataGenerator(*args)
        constraints_set = set(gen.constraints_list)
        possible_w_notes_set = set(gen.possible_w_notes)

        assert possible_w_notes_set.issubset(constraints_set)

    @pytest.mark.parametrize(
        "address_row, expected_address",
        [
            ([1, "Salt Lake City", "3365 S 900 W"], "3365 S 900 W"),
            ([2, "Salt Lake City", "3060 Lester St"], "3060 Lester St"),
            ([3, "Salt Lake City", "2530 S 500 E"], "2530 S 500 E"),
        ]
    )
    def test_assign_random_address_writes_selected_address(self, address_row, expected_address, monkeypatch):
        monkeypatch.setattr(pdg, "read_address_data", lambda _: [address_row])

        gen = pdg.PackageDataGenerator(20, 0, 0)

        monkeypatch.setattr(pdg.random, "choice", lambda seq: address_row)

        pkg = [0, "Address", "", "", "", "", "", ""]
        gen.assign_random_address(pkg)

        assert pkg[1] == expected_address

@pytest.fixture
def make_address_csv(tmp_path):
    default_rows = [
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