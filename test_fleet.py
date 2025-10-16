# tests/test_fleet.py
from fleet import Fleet
from truck import Truck

def test_add_truck():
    f = Fleet(3)
    t = Truck(truck_id=10)
    f.add_truck(t)
    assert len(f.truck_list) == 4
    assert f.num_trucks == 4
    assert f.truck_list[3].truck_id == 10
    
def test_assign_drivers_to_trucks():
    f = Fleet(4)
    driver_list = ['Larry', 'Moe', 'Curly']
    f.assign_drivers_to_trucks(driver_list)
    assert f.truck_list[0].driver == 'Larry'
    assert f.truck_list[1].driver == 'Moe'
    assert f.truck_list[2].driver == 'Curly'
    assert f.truck_list[3].driver is None   
    
def test_print_fleet(capsys):
    f = Fleet(2)
    t1 = Truck(package_list = ['Merry Prime Day from St. Bezos'])
    t2 = Truck()
    
    f.add_truck(t1)
    f.add_truck(t2)
    
    f.print_fleet()
    captured = capsys.readouterr().out
    assert "Fleet status:" in captured
    assert "  Truck 1 | Load 0" in captured
    assert "    Empty" in captured
    assert "  Total packages loaded on trucks: 1" in captured
    
    
def test_get_empty_trucks():
    f = Fleet(2)
    f.truck_list[0].package_list.append('Merry Prime Day from St. Bezos')
    empty_ids = f.get_empty_trucks()
    
    assert empty_ids == [1]
    
def test_assign_too_many_drivers_is_safe():
    f = Fleet(3)
    driver_list = ['Leonardo', 'Michaelangelo', 'Donatelo', 'Raphael']
    f.assign_drivers_to_trucks(driver_list)
    
    assigned = [t.driver for t in f.truck_list]
    assert assigned == driver_list[:3]
    assert all(d is not None for d in assigned)
    
def test_fleet_is_iterable():
    f = Fleet(3)
    collected_ids = [t.truck_id for t in f]
    assert collected_ids == [0, 1, 2]