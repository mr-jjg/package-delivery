from hash_table import HashTable
from warehouse_repository import get_warehouse_hash
from package import Package, print_package_list
from truck import Truck
from fleet import Fleet
from k_means import split_package_list
from nearest_neighbor import nearest_neighbor
from route_optimizer import check_route_feasibility

class PackageLoader:
    pass
    
    def vprint(self, msg, level):
        if level == "1":
            print(msg)

    def load_assigned_trucks(self, fleet, package_groups, verbosity):
        warehouse_hash = get_warehouse_hash()
        
        for i, group in enumerate(package_groups):
            for package in group[:]:
                truck_to_load = package.truck
                if (
                    truck_to_load is not None
                    and 0 <= truck_to_load < len(fleet.truck_list)
                ):
                    truck = fleet.truck_list[truck_to_load]
                    self.vprint(f"  -LOADING Package {package.package_id} ONTO Truck {truck.truck_id + 1}", verbosity)
                    truck.package_list.append(package)
                    truck.current_capacity -= 1
                    package_groups[i].remove(package)
                    
        remove_empty_groups(package_groups)
        
    
    def load_empty_trucks_with_drivers(self, fleet, package_groups, verbosity, drivers):
        warehouse_hash = get_warehouse_hash()
        
        # Highest priority packages need to go onto empty trucks that have drivers (Ready to roll).
        empty_trucks_with_drivers_list = []
        for truck in fleet.truck_list:
            if truck.driver in drivers and truck.current_capacity == 16:
                empty_trucks_with_drivers_list.append(truck.truck_id)
        
        while empty_trucks_with_drivers_list:
            # Find the highest priority set of packages in the package_groups list and move to the working_package_list.
            working_package_list = build_working_package_list(package_groups)
            
            # Find the first empty truck in the fleet and pop from the list so that the while loop will terminate.
            truck_index = empty_trucks_with_drivers_list.pop(0)
            empty_truck = fleet.truck_list[truck_index]
            
            # Check for special note 'W', as these cannot be split
            w_note = has_w_note(working_package_list)
            
            # If the working_package_list does not have any 'W' notes, then we can check to see if the capacity is sufficient to load the entire list.
            if empty_truck.maximum_capacity < len(working_package_list) and not w_note:
                # New working package list based on capacity checks on empty trucks
                working_package_list = split_package_list(empty_truck, package_groups, working_package_list)
                
            # Now add each package in the working_package_list to the empty_truck.
            for package in working_package_list:
                package.empty_truck = empty_truck.truck_id
                empty_truck.package_list.append(package)
                empty_truck.current_capacity -= 1
            
            print_loading_packages(empty_truck, working_package_list, verbosity)
            
            remove_empty_groups(package_groups)
        
    
    # This method is the heart of the package_loader, and is quite huge. It has gone through several refactors, and in this final version I have done my best to clarify what's going on throughout.
    def load_packages(self, fleet, package_groups, verbosity, drivers=None):
        
        warehouse_hash = get_warehouse_hash()
        
        # We can call this method for trucks with specific drivers, or trucks without drivers.
        truck_list = []
        if drivers:
            for truck in fleet.truck_list:
                if truck.driver in drivers and truck.current_capacity > 0:
                    truck_list.append(truck)
        else:
            for truck in fleet.truck_list:
                if truck.driver is None and truck.current_capacity > 0:
                    truck_list.append(truck)
        
        # Calculate the nearest_neighbor on each truck's package_list to in preparation for later comparisons.
        for truck in truck_list:
            truck.route_distance, truck.package_list = nearest_neighbor(truck.package_list)
            
        count = 0 # Exists simply for printing the iteration count of the loop and error handling.
        
        # Load the packages
        while package_groups and truck_list:
            count += 1
            self.vprint(f"\nIteration: {count} -----------------------------------------------------------------------------------------------", verbosity)
            
            # From the package_groups, build a working_package_list based upon the package at the top of the priority list, aka the 'zero_package'.
            working_package_list = build_working_package_list(package_groups) # This method pops from package_groups
            
            '''# DEBUG ONLY
            print(f"\n'working_package_list' at the beginning of an iteration\n")
            print_package_list(working_package_list)
            '''
            self.vprint(f"\ncurrent_capacity of each truck:", verbosity)
            if verbosity == 1:
                for truck in truck_list:
                    print(f"  {truck.truck_id }: {truck.current_capacity}")
            
            available_trucks = get_trucks_with_available_capacity(truck_list, working_package_list)
            
            # If adding the working_package_list exceeds current_capacity for all trucks, packages will need to be split up using k_means
            if not available_trucks:
                w_note = has_w_note(working_package_list) # Checking for 'W' note packages, as these cannot be separated.
                
                if not w_note:
                    for truck in available_trucks:
                        if truck.maximum_capacity < len(working_package_list) and not w_note:
                            # New working package list based on capacity checks on empty trucks
                            working_package_list = split_package_list(truck, package_groups, working_package_list)
                else:
                    # TODO: If no truck can fit the 'W' note, then we could move priority packages that are not 'T' notes back to the package_groups at position 0 until there is capacity.
                    self.vprint(f"\nThere is not enough capacity on avaible trucks, and package list cannot be split. Exiting at 'load_packages' at iteration {count}.", verbosity)
                    raise SystemExit(1)
            
            # Testing the routes with each truck with available capacity. We want to find the best outcome for adding the working package list to one of the trucks.
            
            # Step 1: First build a list of feasible routes
            feasible_routes_list = []
            for truck in available_trucks:
                self.vprint(f"\nTesting Truck {truck.truck_id + 1} for feasibility", verbosity)
                test_package_list =  truck.package_list + working_package_list
                
                # Generate the test route and the total distance traveled on that route. This includes the distance from the hub to the address of the first package on the list.
                test_route_distance, test_route = nearest_neighbor(test_package_list)
                
                # Check the route again delivery deadlines for feasibility. Again, this includes the delivery deadline of the first package on the list when leaving the hub.
                route_feasibility = check_route_feasibility(test_route, truck.speed_mph, verbosity)
                
                # Add the feasible route to the list
                if route_feasibility:
                    #print("Route is feasible. Appending to feasible_routes_list...")
                    feasible_routes_list.append((truck, test_route, test_route_distance))
            
            if not feasible_routes_list:
                # TODO: Add functionality to add driver and/or add truck.
                self.vprint(f"\nThere are no feasible routes. Exiting at 'load_packages' at iteration {count}.", verbosity)
                raise SystemExit(1)
                
            
            # Step 2: Determine which feasible route minimizes the total distance when replacing a truck's current route.
            if len(feasible_routes_list) > 1:
                current_distances = [truck.route_distance for truck, _, _ in feasible_routes_list]
                total_current_distance = sum(current_distances)
                
                min_total_distance = float('inf')
                best_option = None # Tuple: (truck, test_route, test_route_distance)
                
                for i, (truck, test_route, test_distance) in enumerate(feasible_routes_list):
                    test_total_distance = total_current_distance - current_distances[i] + test_distance
                    
                    if test_total_distance < min_total_distance:
                        min_total_distance = test_total_distance
                        best_option = (truck, test_route, test_distance)
                        #print(f"\nTruck {best_option[0].truck_id} has a route with the minimum total distance of {min_total_distance} by ") # DEBUG ONLY
                    #else: # DEBUG ONLY
                        #print(f"\nTruck {truck.truck_id + 1} failed to produce a minimum total distance with distance {test_total_distance}") # DEBUG ONLY
            else: # Handles the case where there is only one feasible route
                best_option = feasible_routes_list[0]
                #print(f"\nTruck {best_option[0].truck_id} is the only feasible route.") # DEBUG ONLY
                
            # Step 3: Load the optimal truck by fixing the package_list, current_capacity, and route_distance attributes
            optimal_truck = best_option[0]
            
            self.vprint(f"\nTruck {optimal_truck.truck_id + 1} produced the optimal feasible route with a minimum distances of {best_option[2]:.1f}", verbosity)
            load_optimal_truck(best_option)
            print_loading_packages(optimal_truck, working_package_list, verbosity)
            # Remove the optimal truck if it is at capacity.
            if optimal_truck.current_capacity == 0:
                truck_list.remove(optimal_truck)
        
        # Now that the packages have been loaded, the route distance needs to be reset so that the distance can be tracked in real time when delivering.
        for truck in fleet:
            truck.route_distance = 0
    

# Helper functions

def build_working_package_list(package_groups):
    zero_package = package_groups[0][0]
    highest_group, highest_priority = zero_package.group, zero_package.priority
    
    # From the package_groups, build a working_package_list based upon the package at the top of the priority list, aka the 'zero_package'.
    working_package_list = []
    
    # Add packages that share those attributes to the working package list.
    if highest_group is not None or highest_priority == 0:
        for package in package_groups[0][:]:
            if package.group == highest_group and package.priority == highest_priority:
                working_package_list.append(package)
                package_groups[0].remove(package)
    else: # Handle packages with no group individually.
        working_package_list.append(zero_package)
        package_groups[0].remove(zero_package)
        
    # If that package group is empty, remove it from the groups_list
    if not package_groups[0]:
        package_groups.pop(0)
    
    return working_package_list
    

def get_trucks_with_available_capacity(truck_list, package_list):
    trucks_with_available_capacity = []
    
    for truck in truck_list:
        if truck.current_capacity >= len(package_list):
            trucks_with_available_capacity.append(truck)
    
    return trucks_with_available_capacity
    

def has_w_note(package_list):
    for package in package_list:
        if package.special_note and package.special_note[0] == 'W':
            return True
        else:
            return False
    

def remove_empty_groups(groups_list):
    for group in groups_list:
        if not group:
            groups_list.remove(group)
    

def load_optimal_truck(tuple):
                truck = tuple[0]
                route = tuple[1]
                distance = tuple[2]
                
                truck.package_list = route
                truck.current_capacity = truck.maximum_capacity - len(route)
                truck.route_distance = distance
                
                for package in truck.package_list:
                    package.truck = truck.truck_id
    

def print_loading_packages(truck, package_list, verbosity):
    if verbosity == "0":
        return
    
    print (f"verbosity: {verbosity}")
    
    for package in package_list:
        print(f"  -LOADING Package {package.package_id} ONTO Truck {truck.truck_id + 1}")
    

#jjg