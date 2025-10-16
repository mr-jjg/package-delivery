## Truck

Responsibility:
Container for truck state. Tracks its capacity, packages, driver, and timing information.

Public surface:
All attributes are public. Has two special methods:
- __str__ : returns a formatted summary string
- __lt__  : allows trucks to be compared by ID

Inputs / Outputs:
Inputs – constructor parameters (id, capacity, times, etc.).
Outputs – string from __str__, boolean from __lt__, and readable attributes.

Seams:
None at present. Any time behavior (departure/return_time) can be controlled directly by setting the property.

Edge cases:
- current_capacity < 0 or > maximum_capacity  
- package_list empty or None  
- missing or invalid departure_address  

## Fleet

**Responsibility:**  
Manages a collection of `Truck` objects. Responsible for creating, tracking, iterating, and assigning drivers to trucks, as well as providing helper methods to inspect fleet status and retrieve empty trucks.

**Public surface:**  
- `__init__(num_trucks, truck_list=None)` — initializes a fleet with either a specified number of new trucks or a provided list.  
- `add_truck(truck)` — appends a new `Truck` to the fleet and increments `num_trucks`.  
- `assign_drivers_to_trucks(driver_list)` — assigns available drivers to trucks that currently have no driver.  
- `__iter__()` — makes `Fleet` iterable over its trucks.  
- `print_fleet()` — prints formatted truck and package information to console.  
- `get_empty_trucks()` — returns a list of truck IDs that have empty `package_list`s.

**Inputs / Outputs:**  
- **Inputs:** number of trucks, optional existing truck list, optional list of driver names.  
- **Outputs:**  
  - Methods return either updated internal state (`truck_list`, `num_trucks`) or helper data (`list[int]` of empty truck IDs).  
  - `print_fleet()` outputs human-readable console text.

**Seams:**  
- Depends directly on the `Truck` class. For isolated testing, a stub or mock `Truck` could be used to control attributes like `driver` or `package_list`.  
- Output to `stdout` (in `print_fleet`) can be captured for validation.  
- Driver assignment behavior depends on the order of `driver_list` and `truck_list`.

**Edge cases:**  
- `num_trucks` = 0 (empty fleet).  
- `truck_list` provided with mismatched length or non-`Truck` objects.  
- Duplicate truck IDs if custom list is provided.  
- Drivers list shorter or longer than number of trucks.  
- Trucks with `None` or empty `package_list`.

