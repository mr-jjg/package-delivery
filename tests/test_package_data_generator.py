#/tests/test_package_data_generator.py
import csv
import package_data_generator as pdg
import pytest
import random

class TestPackageDataGenerator:
    def test_init_raises_when_lower_band_exceeds_upper_band(self):
        with pytest.raises(ValueError, match="dl_lower_band must be <= dl_upper_band"):
            pdg.PackageDataGenerator(10, 20, 30, dl_lower_band=16, dl_upper_band=9)

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

    def test_assign_random_address_never_uses_warehouse(self, monkeypatch):
        gen = pdg.PackageDataGenerator(1, 0, 0)
        gen.address_list= [
            ("WH", "Warehouse", "Warehouse Address"),
            ("A1", "Address1", "123 Main St"),
            ("A2", "Address2", "456 Oak St"),
        ]

        monkeypatch.setattr("random.choice", lambda element: element[0])

        pkg = [0, None, None, None, None, None, None, None]
        gen.assign_random_address(pkg)

        assert pkg[1] != "Warehouse Address"
        assert pkg[1] in {"123 Main St", "456 Oak St"}

    def test_assign_deadline_sets_time_when_pkg_in_deadlines_list(self, monkeypatch):
        pkg = [0, None, None, None, None, "EOD", None, None]

        not_so_random_time_string = "10:30 AM"
        before = pkg.copy()
        pkg_id = id(pkg)

        def fake_make_randome_time_string(lower, upper):
            return not_so_random_time_string

        monkeypatch.setattr(pdg, "make_random_time_string", fake_make_randome_time_string)

        gen = pdg.PackageDataGenerator(1, 0, 0)
        gen.deadlines_list = [pkg[0]]
        gen.assign_deadline(pkg)

        assert pkg[5] == not_so_random_time_string
        assert before[:5] + before[6:] == pkg[:5] + pkg[6:]
        assert id(pkg) == pkg_id

    def test_assign_deadline_noop_when_pkg_not_in_deadlines_list(self, monkeypatch):
        pkg = [999, None, None, None, None, "EOD", None, None]
        before = pkg.copy()
        pkg_id = id(pkg)

        calls = 0
        def count_make_random_time_string_calls(lower, upper):
            nonlocal calls
            calls += 1
            return "Failed Test"

        monkeypatch.setattr(pdg, "make_random_time_string", count_make_random_time_string_calls)

        gen = pdg.PackageDataGenerator(1, 0, 0)
        gen.deadlines_list = []
        gen.assign_deadline(pkg)

        assert calls == 0
        assert pkg == before
        assert id(pkg) == pkg_id

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

@pytest.mark.parametrize(
    "hour, minute, expected_time_string",
    [
        (11, 1, "11:01 AM"),
        (12, 12, "12:12 PM"),
        (13, 59, "1:59 PM"),
        (23, 0, "11:00 PM"),
    ]
)
def test_make_random_time_string_formatting_correct(hour, minute, expected_time_string, monkeypatch):
    count = 0
    def fake_randint(low, high):
        nonlocal count
        if count == 1: return minute
        count += 1
        return hour

    monkeypatch.setattr(pdg.random, "randint", fake_randint)

    time_string = pdg.make_random_time_string(0, 0)

    assert time_string == expected_time_string

def test_make_random_time_string_minute_range_is_always_valid():
    for i in range(1000):
        time_string = pdg.make_random_time_string(0, 0)
        time_part = time_string.split()[0]
        minute = time_part.split(":")[1]
        assert 0 <= int(minute) <= 59

def test_make_random_time_string_hour_is_never_0():
    lower = random.randint(9, 13)
    upper = random.randint(14, 18)
    for i in range(1000):
        time_string = pdg.make_random_time_string(lower, upper)
        hour = time_string.split(":")[0]
        assert hour != "0"