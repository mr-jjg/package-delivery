# package-delivery

A Python simulation of a multi-truck package delivery system with constraint-based routing, live at [projects.jjg.dev](https://projects.jjg.dev).

---

## Stack

| Layer | Technology |
|---|---|
| Core simulation | Python 3.12, stdlib only |
| API | FastAPI, uvicorn |
| Transport | WebSocket (asyncio subprocess I/O) |
| Package generation | Custom CLI tool (`tools/package_data_generator.py`) |
| Testing | pytest |
| Deployment | Self-hosted Linux server, nginx reverse proxy |

---

## What This Is

This project started as a WGU C950 performance assessment: implement a package delivery simulation in Python, satisfy a fixed set of logistics constraints, and demonstrate understanding of custom data structures and routing algorithms. The academic version is done. What's here is the version I kept building afterward.

The simulation takes a set of packages with addresses, deadlines, weights, and special notes, then plans truck loads, sequences routes, and executes delivery in accelerated real-time. The full pipeline runs automatically from a single entry point: load data, resolve constraints, load trucks, build a delivery timeline, deliver. Every decision the system makes is logged and inspectable at three verbosity levels.

The deployed version wraps the simulation in a FastAPI backend with a WebSocket endpoint. A browser connects, the server spawns `main.py` as a subprocess, and stdout streams back to the client line by line. A separate `/generate` endpoint calls a parameterized package data generator and returns a fresh CSV. Users can adjust package count, deadline density, and constraint density before running the simulation, then watch the output in a terminal-style console on the page.

The core package data structure is a custom hash table implemented from scratch, which the project required as a demonstration of understanding. All lookups during route execution go through it. The routing algorithm is nearest neighbor, chosen for its simplicity and adequacy at this scale. K-means clustering handles the case where a group of packages is too large to fit on a single available truck: it partitions the group geographically so the split produces loads that stay close together on the map rather than splitting arbitrarily.

---

## Repository Structure

```
package-delivery/
├── main.py                     # Entry point; orchestrates the full pipeline
├── package_handler.py          # Constraint resolution: deadlines, delays, co-delivery, truck assignment
├── package_loader.py           # Truck loading decisions; calls nearest neighbor and k-means
├── delivery_handler.py         # Builds the delivery timeline; executes in accelerated real-time
├── nearest_neighbor.py         # Core routing algorithm
├── k_means.py                  # Geographic clustering used to split oversized load groups
├── route_optimizer.py          # Feasibility checks: validates that a route meets all deadlines
├── hash_table.py               # Custom hash table (project-required data structure)
├── package.py                  # Package object and helpers
├── truck.py                    # Truck object
├── fleet.py                    # Fleet container; driver assignment
├── address_repository.py       # Global address list; string-to-index and index-to-string lookups
├── distance_repository.py      # Global distance matrix; symmetry validation on load
├── warehouse_repository.py     # Global package hash; deep-copy reset between simulation runs
├── project_data.py             # CSV ingestion for packages, addresses, distances
├── time_utils.py               # Time arithmetic helpers (departure, arrival, travel duration)
├── api/
│   └── app.py                  # FastAPI app; WebSocket subprocess stream, /generate endpoint
├── tools/
│   ├── reporter.py             # Verbosity-gated output (NONE / PROG / INFO)
│   └── package_data_generator.py  # Parameterized package list generator; CLI and API-callable
├── tests/                      # pytest suite; one file per module
├── docs/
│   └── test-unit-map.md        # Unit test planning notes
├── addressCSV.csv              # 27-address Salt Lake City dataset
├── distanceCSV.csv             # 27x27 lower-triangular distance matrix
├── default.csv                 # Default 40-package dataset
└── tmp/                        # Generated CSVs (gitignored); 30-minute TTL enforced by API
```

---

## Design Notes

**Why nearest neighbor for routing?**
The scale here is small enough that a greedy algorithm works well in practice. Nearest neighbor produces routes that satisfy all deadlines across the default and generated datasets. A globally optimal solver would add implementation complexity without meaningfully improving outcomes at 20-40 packages across 27 addresses. The `route_optimizer.py` feasibility check runs after every candidate route is built; if a route would miss a deadline, it gets rejected and the loader tries a different truck or splits the load.

**Why k-means for load splitting?**
When a group of packages is too large to fit on the truck with the most remaining capacity, the system has to split it. A naive split (first N packages go here, rest go elsewhere) produces loads that may be geographically scattered. K-means partitions by address proximity, so each resulting sub-group stays in a geographic cluster. The clusters don't respect business constraints on their own, which is why constraint resolution (`package_handler.py`) runs before any loading decisions are made.

**Why a retry loop in `main.py`?**
The constraint resolution and loading pipeline can fail if the combination of truck-specific requirements, co-delivery groups, and delayed packages produces an infeasible assignment given the current fleet size. Rather than tuning a fixed fleet configuration, `main.py` catches `SystemExit` from the loader and retries with one additional truck or driver, alternating between them. This makes the simulation self-correcting for harder generated datasets without requiring the user to pre-configure the fleet.

**Why three verbosity levels instead of a boolean flag?**
During development, the difference between "I want to see what step just ran" and "I want to see every intermediate data structure" was significant enough that a binary quiet/verbose flag wasn't enough. `VerbosityLevel.PROG` shows pipeline progress; `VerbosityLevel.INFO` additionally prints intermediate package tables, group lists, and fleet state at each step. The API always runs at level 0 or 1; level 2 is for local debugging.

**Why a subprocess stream instead of importing the simulation directly into the API?**
The simulation uses module-level global state (the warehouse hash, address list, distance matrix) that isn't safe to run in multiple concurrent threads or async tasks sharing the same process. Spawning `main.py` as a subprocess per WebSocket connection gives each session its own isolated interpreter state and eliminates any concurrency concern. stdout from the subprocess is pumped line by line over the WebSocket. The tradeoff is that there's no structured return value from the simulation; everything the client sees is console output.

**Why does the API accept only `"enter"` as a command?**
The simulation uses `input()` calls at key steps when running at verbosity 1 or higher, so the user can step through the pipeline. The WebSocket accepts a controlled command set (`ALLOWED_CMDS`) and writes only known byte sequences to the subprocess stdin. This prevents arbitrary command injection while still letting the demo UI's Enter button advance the simulation.

---

## How to Run

### Prerequisites

Python 3.11+. Install dependencies:

```bash
pip install -r requirements.txt
```

### Run the simulation

```bash
python main.py
```

Optional flags:

```bash
python main.py -v 1 -p path/to/packages.csv
```

| Flag | Values | Default |
|---|---|---|
| `-v` / `--verbosity` | `0` (quiet), `1` (progress), `2` (info) | `0` |
| `-p` / `--package_csv` | Path to a CSV package file | `default.csv` |

### Run tests

```bash
pytest
```

### Run the API

```bash
cd api
uvicorn app:app --reload
```

---

## Honest Scope

This is a portfolio and academic project. It is not hardened for production use.

The routing algorithm is nearest neighbor, which is greedy and produces good-enough routes at this scale, not optimal ones. The planned 2-opt improvement (which would post-process routes to reduce total distance by swapping stop pairs) was written but not integrated; it has since been removed from the codebase.

The simulation runs synchronously in a single process. The API spawns one subprocess per WebSocket connection with no concurrency limits or resource caps. This is fine for demo use with occasional traffic; it is not designed to handle simultaneous sessions at scale.

The distance and address datasets are fixed to a 27-location Salt Lake City grid from the original WGU assignment. Generated package lists draw from those same addresses.

The package data generator is parameterized but produces scenarios randomly, which means some combinations of deadline density and constraint density will produce infeasible delivery plans. The live demo notes this; the retry loop in `main.py` handles the common cases automatically.
