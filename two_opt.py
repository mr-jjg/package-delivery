def two_opt(package_list, start_point='4001 South 700 East'):
    best_route = build_vertices_list(package_list, start_point)
    
    print_package_list(package_list)
    departure_time = get_route_departure_time(package_list)
    
    shortest_distance = get_route_distance(best_route)
    improved = True 
    MAX_ITERATION = 100
    iteration = 1
    
    while improved and iteration < MAX_ITERATION:
        improved = False
        for i in range(1, len(package_list) - 2):
            for j in range(i + 1, len(package_list) - 1):
                test_route = two_opt_swap(best_route, i, j)
                test_shortest_distance = get_route_distance(test_route)
                
                feasible = is_feasible_route(test_route, departure_time)
                
                if not feasible:
                    continue
                
                if is_feasible_route(test_route) and test_shortest_distance < shortest_distance:
                    #viable_routes_list.append(
                    best_route = test_route
                    shortest_distance = test_shortest_distance
                    improved = True
                    iteration += 1
    print(f"RETURNING FROM TWO_OPT LAND. HOW EXCITING! hella route: {shortest_distance}")
    return convert_route_to_package_list(best_route), shortest_distance
    

def two_opt_swap(route, i, k):
    return route[:i] + route[i:k+1][::-1] + route[k+1:]
    

#jjg