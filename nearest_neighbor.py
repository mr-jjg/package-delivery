from address_repository import get_address_list, address_to_index
from distance_repository import get_distance_matrix
from route_optimizer import convert_route_to_package_list
from package import print_package_list

# Sourced from: https://en.wikipedia.org/wiki/Nearest_neighbour_algorithm
def nearest_neighbor(package_list, start_point='4001 South 700 East'): # Optional argument defaults to WGU address  
    address_list = get_address_list()
    distance_matrix = get_distance_matrix()
    
    '''# DEBUG ONLY
    print(f"\nPrior to adding to lists, here is the package_list of length: {len(package_list)}")
    print_package_list(package_list)
    '''#
    
    start_index = address_to_index(start_point)
    #print(f"\n{start_point} indexes to {start_index} in addresss_list")  # DEBUG ONLY
    
    # A list of tuples to store unvisited vertices: ( package_id, address_index )
    unvisited_tuples_list = build_vertices_list(package_list, start_point)
    
    '''#
    print("\nA check prior to iterating:")
    print(f"  This is the package_id_set: {package_id_set}")
    print(f"  This is the unvisited_list: {unvisited_list}")
    print("\nBegin iterating:") # DEBUG ONLY
    '''#
    
    # A list of tuples to store the route: (package_id, address_index). Initialized with the start_point in mind.
    visited_tuples_list = [(None, start_index)]
    route_sum = 0
    
    current_index = visited_tuples_list[0][1]
    while unvisited_tuples_list:
        #print(f"Current address: {address_list[current_index][2] if current_index is not None else 'Home'}") # DEBUG ONLY
        min_distance = float('inf')
        min_index = -1
        
        # Iterate through each tuple in the unvisited_list to find the minimum distance between current_index and test_distance
        for i, address in enumerate(unvisited_tuples_list):
            connecting_index = address[1]
            test_distance = distance_matrix[current_index][connecting_index]
            #print(f"    Checking against Package ID {address[0]}: distance from current: {test_distance}")
            
            if test_distance < min_distance:
                min_distance = test_distance
                min_index = i
                #print(f"        Found min_distance {min_distance} at index Package ID {address[0]}") # DEBUG ONLY
        
        # Add minimum tuple to visited_tuples_list and prepare for next iteration
        if min_index != -1:
            #print(f"  Adding {unvisited_tuples_list[min_index]}") # DEBUG ONLY
            min_tuple = unvisited_tuples_list.pop(min_index)
            visited_tuples_list.append(min_tuple)
            route_sum += min_distance
            
            current_index = min_tuple[1]
        else:
            break
        
        '''#
        print(f"Length of unvisited_tuples_list: {len(unvisited_tuples_list)}")
        print(unvisited_tuples_list)
        '''#
    
    # Include the distance for returning to the start point
    to_home_distance = distance_matrix[current_index][start_index]
    route_sum += to_home_distance
    
    # A route is an ordered package list
    route = convert_route_to_package_list(visited_tuples_list)
    
    '''# DEBUG ONLY
    print(f"nearest_neighbor -- Sum of route: {route_sum}")
    print(f"Result route length: {len(route)}")
    print_package_list(route)
    '''#
    
    return route_sum, route
    

# A list of tuples to store unvisited vertices: ( package_id, address_index )
def build_vertices_list(package_list, start_point):
    vertices_list = []

    for package in package_list:
        if package.address != start_point:
            address_index = address_to_index(package.address)
            vertices_list.append((package.package_id, address_index))
            #print(f"{package.address} with Package ID {package.package_id} indexes to {address_index} in address_list") # DEBUG ONLY
    return vertices_list


#jjg