## Truck

Responsibility:
Container for truck state. Tracks its capacity, packages, driver, and timing information.

Public surface:
All attributes are public. Has two special methods:
- `__str__` : returns a formatted summary string
- `__lt__`  : allows trucks to be compared by ID

Inputs / Outputs:
Inputs – constructor parameters (id, capacity, times, etc.).
Outputs – string from `__str__`, boolean from `__lt__`, and readable attributes.

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

## HashTable

**Responsibility:**  
Stores and retrieves key–value pairs for package data using a fixed-size list of buckets (chaining). Provides basic CRUD and lookup operations.

**Public surface:**  
- `__init__(size)` — initializes an empty table of the given size.  
- `hash(key)` — computes a bucket index for an integer key.  
- `insert(key, value)` — adds or updates an entry.  
- `search(key)` — returns the stored value or `None`.  
- `remove(key)` — deletes a key if present.  
- `lookup_function(key)` — helper that returns the full package tuple from stored data.  
- `__iter__()` — yields each bucket’s contents.

**Inputs / Outputs:**  
- **Inputs:** integer key, arbitrary value (often a 6-tuple for package data).  
- **Outputs:** inserted, retrieved, or removed data; index integers from `hash()`.

**Seams:**  
- Purely in-memory structure; no I/O or external dependencies.  
- Hash size and key distribution can be tuned to test collisions.  
- Iteration and lookup functions expose deterministic order for testing.

**Edge cases:**  
- `hash()` called with non-integer key → raises `TypeError`.  
- Duplicate key insert → overwrites existing value.  
- `remove()` on nonexistent key → no crash, returns `None`.  
- Empty table iteration yields nothing.  
- Collision resolution verified by inserting multiple keys mapping to the same index.

**Suggested tests:**  
1. **Initialization** – verify all buckets are empty lists after creation.  
2. **Hashing** – known keys produce consistent indices; non-ints rejected.  
3. **Insert/Search/Remove round-trip** – inserted value can be found, removed value gone.  
4. **Collision handling** – multiple keys hashed to the same index still retrievable.  
5. **Overwrite behavior** – second insert with same key replaces prior value.  
6. **Iterator** – yields each bucket exactly once; all stored pairs appear.  
7. **Lookup helper** – returns correct tuple format for existing key.

## Package

**Responsibility:**  
Represents a single delivery package and its associated data, including address, city, ZIP code, delivery deadline, weight, special notes, and time-related states such as departure and delivery times.

**Public surface:**  
- `__init__(package_id, address, city, zip_code, delivery_deadline, weight, special_note)` — creates a new package instance with identifying and logistical details.  
- `__str__()` — returns a formatted summary string including ID, address, city, ZIP, deadline, delivery time, and note.  
- `__lt__(other)` — allows sorting by `package_id`.  
- `get_time_str(time_obj)` — converts a `datetime` object into a readable string.  
- `get_deadline_str()` — returns formatted string for delivery deadline.  
- `update_status(status)` — sets current delivery status (e.g., “At Hub”, “En Route”, “Delivered”).  
- `set_time_of_delivery(time_obj)` — records when the package was delivered.  
- `mark_en_route()` / `mark_delivered()` — convenience methods to set status and timestamps.

**Inputs / Outputs:**  
- **Inputs:** initialization parameters and updates via status/time setters.  
- **Outputs:** formatted strings, readable attributes, and booleans or strings from comparisons and helpers.

**Seams:**  
- Time values can be injected manually for deterministic testing.  
- String formatting functions are pure and easily testable.  
- Delivery/deadline logic can be validated with fixed datetime fixtures.

**Edge cases:**  
- Missing or invalid `delivery_deadline` (e.g., `None` or wrong type).  
- `time_of_delivery` not set but `__str__` called (should handle gracefully).  
- Invalid status updates (should be ignored or raise error depending on implementation).  
- Comparing `Package` to a non-`Package` object via `__lt__` should return `False` or raise.  
- Deadline equal to current time (boundary check).

**Suggested tests:**  
1. **Initialization** – all attributes match constructor parameters; default status is “At Hub”.  
2. **String representation** – verify expected format and inclusion of key fields.  
3. **Comparison** – packages sort by ID correctly.  
4. **Deadline formatting** – valid date returns expected string; `None` handled gracefully.  
5. **Time formatting** – `get_time_str()` converts datetime to readable string.  
6. **Status updates** – `mark_en_route()` and `mark_delivered()` set correct statuses and timestamps.  
7. **Edge deadlines** – package with EOD or missing deadline handled without error.
