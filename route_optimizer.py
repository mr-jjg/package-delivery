from warehouse_repository import get_warehouse_hash
from distance_repository import get_distance
from package import Package
from datetime import time
from time_utils import float_to_time, get_route_departure_time, get_arrival_time, calculate_travel_time

def check_route_feasibility(route, speed_mph, verbosity, start_address='4001 South 700 East'):
    has_delivery_deadline = False
    # Route is feasible if no packages have delivery deadlines
    for package in route:
        if package.delivery_deadline != Package.EOD_TIME:
            has_delivery_deadline = True
    if not has_delivery_deadline:
        if verbosity == "1":
            print("Route has no delivery deadlines. Is feasible.")
        return True
    
    departure_time = get_route_departure_time(route)
    #print(f"  Leaving the starting point at {departure_time}") # DEBUG ONLY
    
    # First calculate the arrival time from the starting point to the address of the first delivered package.
    curr_pkg = route[0]
    
    
    arr_time = get_arrival_time(departure_time, start_address, curr_pkg.address, speed_mph)
    
    # print(f"    Truck left {start_address} and arrived at {curr_pkg.address} at: {arr_time}")
    if arr_time > curr_pkg.delivery_deadline:
            if verbosity == "1":
                print(f"ERROR: Route is not feasible: {arr_time} > {curr_pkg.delivery_deadline}")
            return False
            
    for i in range(len(route) - 1):
        curr_pkg = route[i]
        next_pkg = route[i + 1]
        
        # Skip the iteration if the addresses of subsequent packages are the same.
        if curr_pkg.address == next_pkg.address:
            continue
        
        arr_time = get_arrival_time(arr_time, curr_pkg.address, next_pkg.address, speed_mph)
        end_address_deadline = route[i + 1].delivery_deadline
        # print(f"    Arrival time: {arr_time} | Truck left {curr_pkg.address} and arrived at {next_pkg.address}")
        if arr_time > end_address_deadline:
            if verbosity == "1":
                print(f"ERROR: Route is not feasible: {arr_time} > {end_address_deadline}")
            return False
    
    if verbosity == "1":
        print(f"SUCCESS: Route is feasible. Arrival time at {arr_time}")
    return True
    

def convert_route_to_package_list(route):
    warehouse_hash = get_warehouse_hash()
    
    package_list = []
    
    for tuple in route:
        package_id = tuple[0]
        if package_id is not None:
            package = warehouse_hash.search(package_id)
            package_list.append(package)
    
    '''#
    print("\nReturning this package list:")
    print_package_list(package_list
    '''#
    
    return package_list
    

#jjg