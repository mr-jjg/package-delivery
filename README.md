# WGU C950 Package Delivery Project

## Overview
This project is an implementation of the Western Governors University (WGU) C950 Data Structures and Algorithms II capstone.  
It simulates a package delivery system with multiple trucks, drivers, and constraints.  
The goal is to optimize delivery routes while handling deadlines, special notes, and real-time events.

The program begins execution from `main.py`, which orchestrates data loading, package handling, truck loading, and delivery execution.

---

## Key Features
- **Automated delivery system**: Once the CSV files are provided, the program ingests, prioritizes, loads, and delivers packages with no manual input.
- **Constraint handling**: Accounts for package deadlines, co-delivery rules, truck restrictions, and delayed packages.
- **K-means clustering**: Splits large package groups across trucks intelligently, based on geographic proximity.
- **Nearest neighbor routing**: Builds efficient delivery routes greedily, one stop at a time.
- **2-opt optimization (planned)**: Implementation written but not fully integrated; would improve global route optimality.
- **Dynamic delivery simulation**: Delivery statuses and arrival times update in real-time, including address corrections at specified times.
- **Custom data structures**: Implements a custom hash table for package storage, enabling O(1) lookups during route execution.
- **Modular organization**: Program logic separated into focused modules like `PackageHandler`, `PackageLoader`, `Fleet`, and `DeliveryHandler` for clarity and maintainability.
- **Threading support**: Multithreaded delivery simulation and UI responsiveness.

---

## Algorithm Choices

### Nearest Neighbor (Core Routing)
- Simple, greedy approach that selects the next closest unvisited address.
- Fast and effective at this scale, ensuring packages are delivered on time.
- Does not guarantee a globally optimal route but satisfies project requirements.

### K-Means Clustering
- Groups packages geographically to reduce route complexity.
- Helps split large delivery sets across multiple trucks.
- On its own, it does not enforce business constraints, which is why it’s paired with PackageHandler rules before routing.

### 2-Opt Optimization (Future Work)
- Route improvement algorithm that can shorten total mileage by swapping stops.
- Would reduce travel distance but at the cost of more compute time.
- Implementation exists but was not integrated due to time constraints.

---

## File Structure
```text
package_delivery/
├── address_repository.py       # Manages address data and lookup helpers  
├── delivery_handler.py         # Builds and executes the delivery timeline  
├── distance_repository.py      # Stores and queries the distance matrix  
├── fleet.py                    # Fleet object containing all trucks  
├── hash_table.py               # Custom hash table for package storage  
├── k_means.py                  # K-means clustering for splitting package groups  
├── main.py                     # Entry point – orchestrates the simulation  
├── nearest_neighbor.py         # Nearest neighbor algorithm for route planning  
├── package.py                  # Package object and helpers  
├── package_handler.py          # Handles package constraints, priorities, and grouping  
├── package_loader.py           # Decides how packages are loaded onto trucks  
├── project_data.py             # Reads package, address, and distance data from CSV  
├── route_optimizer.py          # Route feasibility checks and helpers  
├── time_utils.py               # Utility functions for time and scheduling  
├── truck.py                    # Truck object with attributes for capacity, speed, and route  
├── two_opt.py                  # Advanced route optimization (2-opt algorithm)  
├── user_interface.py           # Interactive user interface (optional, threading-enabled)  
├── warehouse_repository.py     # Stores the warehouse package hash table  
├── addressCSV.csv              # Address dataset  
├── distanceCSV.csv             # Distance dataset  
└── packageCSV.csv              # Package dataset  
```

---

## How to Run
### Prerequisites
- Python 3.11+
- Install dependencies (if required):
```bash
pip install -r requirements.txt
```

### Run the simulation
```bash
python main.py
```

You will be prompted for verbosity level:
- `0` = quiet (minimal output)
- `1` = verbose (detailed logs of each step)

---

## Lessons Learned
- The importance of code organization and early commenting — later refactoring was smoother thanks to thorough documentation.
- Keeping consistent backups would have prevented lost progress when experimenting with 2-opt integration.
- Alternative data structures (like dictionaries or BSTs) could have simplified some logic, though the custom hash table met requirements efficiently.