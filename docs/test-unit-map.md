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
