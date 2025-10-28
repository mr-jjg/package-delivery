# tests/test_project_data.py
import csv
import pytest
import project_data as pd

@pytest.fixture
def make_package_csv(tmp_path):
    default_rows = [
        ["1", "Disneyland", "Anaheim", "CA", "92802", "EOD", "2", "Happy place"],
        ["2", "The White House", "Washington", "DC", "20500", "10:30 AM", "1", "Presidential package"],
        ["3", "The Alamo", "San Antonio", "TX", "78205", "EOD", "3", "Historic site"],
        ["4", "Niagara Falls", "Niagara Falls", "NY", "14301", "5:00 PM", "4", "Scenic delivery"],
        ["5", "Peter Griffin's House", "Quahog", "RI", "02860", "EOD", "6", "Family package"]
    ]
    
    def _make(rows=None, name="packages.csv"):
        if rows is None:
            rows = default_rows
        path = tmp_path / name
        with path.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerows(rows)
        return path
    return _make

@pytest.fixture
def patch_fakes(monkeypatch):
    class FakePackage:
        def __init__(self, package_id, address, city, state, zip_code, 
                     delivery_deadline, weight_kilo, special_note):
            self.package_id = package_id
            self.address = address
            self.city = city
            self.state = state
            self.zip_code = zip_code
            self.delivery_deadline = delivery_deadline
            self.weight_kilo = weight_kilo
            self.special_note = special_note
            self._parse_called = False
            
        def parse_special_note(self):
            self._parse_called = True
            return self.special_note
    
    class FakeHashTable:
        def __init__(self, size):
            self.size = size
            self.items = {}
        def insert(self, key, value):
            self.items[key] = value
        
    monkeypatch.setattr(pd, "Package", FakePackage)
    monkeypatch.setattr(pd, "HashTable", FakeHashTable)
    
    return {"FakePackage": FakePackage, "FakeHashTable": FakeHashTable}

def test_read_package_data_initializes_hashtable_with_csv_line_count(make_package_csv, patch_fakes):
    csv_path = make_package_csv()
    FakeHashTable = patch_fakes["FakeHashTable"]
    
    table = pd.read_package_data(csv_path)
    
    assert isinstance(table, FakeHashTable)
    assert table.size == 5
    assert len(table.items) == 5
    

def test_read_package_data_inserts_each_row_with_cleaned_keys(make_package_csv, patch_fakes):
    csv_path = make_package_csv([
        ["1", "Disneyland", "Anaheim", "CA", "92802", "EOD", "2", "None"],
        ["2", "The White House", "Washington", "DC", "20500", "10:30 AM", "1", ""],
    ])
    
    table = pd.read_package_data(csv_path)
    values = list(table.items.values())
    
    assert isinstance(values[0].package_id, int)
    assert isinstance(values[0].weight_kilo, int)
    assert isinstance(values[1].package_id, int)
    assert isinstance(values[1].weight_kilo, int)
    assert values[0].special_note is None
    assert values[1].special_note is None
    
def test_read_package_data_calls_parse_special_note_and_reassigns(make_package_csv, patch_fakes):
    csv_path = make_package_csv()
    
    table = pd.read_package_data(csv_path)
    values = list(table.items.values())
    
    for pkg in values:
        assert pkg._parse_called is True
    assert values[0].special_note == "Happy place"
    assert values[1].special_note == "Presidential package"
    assert values[2].special_note == "Historic site"
    assert values[3].special_note == "Scenic delivery"
    assert values[4].special_note == "Family package"
    
def test_read_package_data_applies_clean_value_across_columns(make_package_csv, patch_fakes):
    csv_path = make_package_csv([
        ["1", "2", "3", "4", "5", "6", "7", "8"],
        ["9", "A", "B", "C", "D", "E", "F", "G"],
        ["10", "None", "None", "None", "None", "None", "None", "None"],
        ["11", "    ", "    ", "    ", "    ", "    ", "    ", "    "],
    ])
    
    table = pd.read_package_data(csv_path)
    packages = list(table.items.values())
    assert len(packages) == 4
    
    for pkg in packages:
        for name, value in vars(pkg).items():
            if name == "_parse_called":
                continue
            assert (
                isinstance(value, (int, str)) or value is None
            ), f"{name} had unexpected type {type(value)} and value {value}"

def test_read_package_data_survives_whitespace_and_extra_spaces(make_package_csv, patch_fakes):
    csv_path = make_package_csv([
        ["  1  ", "  2  ", "  3  ", "  4  ", "  5  ", "  6  ", "  7  ", "  8  "],
        ["  9  ", "  A  ", "  B  ", "  C  ", "  D  ", "  E  ", "  F  ", "  G  "],
        ["  10  ", "  None  ", "  None  ", "  None  ", "  None  ", "  None  ", "  None  ", "  None  "],
        ["  11  ", "    ", "    ", "    ", "    ", "    ", "    ", "    "],
    ])
    
    table = pd.read_package_data(csv_path)
    packages = list(table.items.values())
    assert len(packages) == 4
    
    for pkg in packages:
        for name, value in vars(pkg).items():
            if name == "_parse_called":
                continue
            assert (
                isinstance(value, (int, str)) or value is None
            ), f"{name} expected type {type(value)} got unstripped {type(value)}"


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
    
    address_list = pd.read_address_data(csv_path)
    
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
        bad_list = pd.read_address_data(path)
    
    assert "invalid literal" in str(exc_info.value) or "int" in str(exc_info.value)

def test_read_distance_data_upper_triangle_is_mirrored_symmetrically(tmp_path):
    test_distance_data = [[0,'',''],
                          [1,0,''],
                          [2,3,0]]
    expected_distance_data = [[0,1,2],
                              [1,0,3],
                              [2,3,0]]
    path = tmp_path / "distances.csv"
    with path.open("w", newline='') as f:
        w = csv.writer(f)
        w.writerows(test_distance_data)
    
    mirrored_matrix = pd.read_distance_data(path)
    
    assert mirrored_matrix == expected_distance_data

def test_read_distance_data_blank_cells_become_inf(tmp_path):
    test_distance_data = [['','',''],
                          ['','',''],
                          ['','','']]
    inf = float('inf')
    expected_distance_data = [[inf,inf,inf],
                              [inf,inf,inf],
                              [inf,inf,inf]]
    path = tmp_path / "distances.csv"
    with path.open("w", newline='') as f:
        w = csv.writer(f)
        w.writerows(test_distance_data)
    
    mirrored_matrix = pd.read_distance_data(path)
    
    for row in mirrored_matrix:
        for v in row:
            assert v == inf
    
def test_read_distance_data_singleton(tmp_path):
    test_distance_data = [[0]]
    path = tmp_path / "distances.csv"
    with path.open("w", newline='') as f:
        w = csv.writer(f)
        w.writerows(test_distance_data)
    
    mirrored_matrix = pd.read_distance_data(path)
    
    assert mirrored_matrix == [[0.0]] or mirrored_matrix == [[0]]

def test_csv_line_count_empty_file(tmp_path):
    path = tmp_path / "empty_file.csv"
    path.touch()
    
    empty_count = pd.csv_line_count(path)
    assert empty_count == 0
    
@pytest.mark.parametrize(
    "raw, expected",
    [
        ("5", 5),
        (42, 42),
        ("None", None),
        (" none ", None),
        ("", None),
        ("   ", None),
        ("abc", "abc"),
        ("123abc", "123abc"),
        (" 7 ", 7),
    ],
)
def test_clean_value_conversions_parametrized(raw, expected):
    assert pd.clean_value(raw) == expected
    