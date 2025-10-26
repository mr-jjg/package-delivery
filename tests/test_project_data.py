# tests/test_project_data.py

def test_read_package_data_initializes_hashtable_with_csv_line_count(tmp_path, monkeypatch):
    import project_data as pd
    
    class FakePackage:
        def __init__(self, package_id, address, city, state, zip_code, delivery_deadline, weight_kilo, special_note):
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
            return f"PARSED({self.special_note})"
    
    class FakeHashTable:
        def __init__(self, size):
            self.size = size
            self.items = {}
        def insert(self, key, value):
            self.items[key] = value
    
    monkeypatch.setattr(pd, "Package", FakePackage)
    monkeypatch.setattr(pd, "HashTable", FakeHashTable)
    
    csv_path = tmp_path / "packages.csv"
    csv_path.write_text("1,123 Main,City,ST,11111,EOD,5,note\n")
    
    result = pd.read_package_data(csv_path)
    
    assert isinstance(result, FakeHashTable)
    assert result.size == 1
    assert len(result.items) == 1
    
'''
def test_read_package_data_inserts_each_row_with_cleaned_keys(monkeypatch, tmp_path):
    pass
    
def test_read_package_data_calls_parse_special_note_and_reassigns(monkeypatch, tmp_path):
    pass
    
def test_read_package_data_applies_clean_value_across_columns(monkeypatch, tmp_path):
    pass
    
def test_read_package_data_survives_whitespace_and_extra_spaces(monkeypatch, tmp_path):
    pass
    
def test_read_address_data_happy_path(tmp_path):
    pass

def test_read_address_data_raises_on_nonint_id(tmp_path):
    pass

def test_read_distance_data_upper_triangle_is_mirrored_symmetrically(tmp_path):
    pass
    
def test_read_distance_data_blank_cells_become_inf_and_then_get_mirrored(tmp_path):
    pass

def test_read_distance_data_singleton(tmp_path):
    pass

def test_csv_line_count_empty_file(tmp_path):
    pass
    
def test_csv_line_count_various_line_endings(tmp_path):
    pass
    
def test_clean_value_conversions_parametrized():
    pass
    
'''