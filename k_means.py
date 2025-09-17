import random
from warehouse_repository import get_warehouse_hash
from address_repository import get_address_list, address_to_index
from distance_repository import get_distance_matrix
from package import Package, print_package_list, print_group_list

def split_package_list(truck, package_groups, package_list):
    # DEBUG ONLY - for the purposes of testing each case of the while loop
    #truck.current_capacity = 1
    #
    
    returned_to_package_groups = []
    # Check the capacity of the truck against the length of the package_list.
    while truck.current_capacity < len(package_list):
        # If the package_list is too large to add to the empty truck, use k_means to intelligently split the package_list into two groups, sorted in descending order.
        k_means_groups = k_means_clustering(package_list, 2)
        
        '''# DEBUG ONLY
        print(f"\n\nempty_truck current_capacity: {truck.current_capacity}\n")
        print(f"Length of k_means_groups[0]: {len(k_means_groups[0])}")
        print(f"Length of k_means_groups[1]: {len(k_means_groups[1])}")
        '''#
        
        if truck.current_capacity >= len(k_means_groups[0]):
            print("\nCase 1: The first group fits onto the empty truck.") # DEBUG ONLY
            package_list = k_means_groups[0]
            #package_groups.insert(0, k_means_groups[1])
            for package in k_means_groups[1]:
                returned_to_package_groups.append(package)
            break
            
        elif truck.current_capacity >= len(k_means_groups[1]):
            print("\nCase 2: The first group does not fit onto the empty truck, but the second group does.") # DEBUG ONLY
            package_list = k_means_groups[1]
            #package_groups.insert(0, k_means_groups[0])
            for package in k_means_groups[0]:
                returned_to_package_groups.append(package)
            break
        else:
            print("\nCase 3: Neither the first group nor the second group fits onto the empty truck.") # DEBUG ONLY
            package_list = k_means_groups[0]
            #package_groups.insert(0, k_means_groups[1])
            for package in k_means_groups[1]:
                returned_to_package_groups.append(package)
    
    package_groups.insert(0, returned_to_package_groups)
    return package_list
    

# K-Means Algorithm

def k_means_clustering(package_list, k):
    address_list = get_address_list()
    distance_matrix = get_distance_matrix()
    
    # Step 1: Randomly select k initial centroids (the addresses of first k packages).
    centroids = select_unique_package_address(package_list, k)
    previous_centroids = []
    
    while centroids != previous_centroids:
        centroid_address_list_index = []
        for centroid in centroids:
            index = address_to_index(centroid.address, address_list)
            centroid_address_list_index.append(index)
        
        
        # Step 2: Assign each package to the nearest centroid
        cluster_list = [[] for _ in range(k)] # Utilize list comprehension to initialize k clusters
        
        #print("for each package:")
        for package in package_list: # For each package...
            
            # ... the distances from the package address ...
            package_index = address_to_index(package.address, address_list)
            
            distances = []
            
            # ... to each centroid are calculated...
            for i in range(k):
                centroid_index = centroid_address_list_index[i]
                # ... and stored in the distances list.
                distances.append(distance_matrix[package_index][centroid_index])
            
            '''# DEBUG ONLY
            print(f"package_index: {package_index} ::: centroid_index: {centroid_index}")
            print(f"package.address: {package.address} ::: centroid.address: {centroid.address}")
            print("distances:", distances) # DEBUG ONLY
            '''#
            # The centroid with the minimum distance determines which centroid is assigned to closest_centroid...
            closest_centroid = distances.index(min(distances))
            
            #
            #print("closest_centroid:", closest_centroid) # DEBUG ONLY
            #
            
            # ... and then the package is added to the cluster that contains the closest_centroid.
            cluster_list[closest_centroid].append(package)
            
            #
            #
        
        #print("exited the for loop")
        # Step 3: Update the centroids for each cluster
        previous_centroids = centroids
        centroids = []
        
        
        for i in range(k):
            if cluster_list[i]:
                new_centroid = find_new_centroid(cluster_list[i])
                centroids.append(new_centroid)
                
    sorted_cluster_list = sorted(cluster_list, key=len, reverse=True)
    
    # DEBUG ONLY
    print("sorted_cluster_list being returned from k_means_clustering:")
    print_group_list(sorted_cluster_list)
    #
    
    return sorted_cluster_list

def find_new_centroid(cluster):
    address_list = get_address_list()
    distance_matrix = get_distance_matrix()
    
    min_sum = float('inf')
    new_centroid = None
    for candidate in cluster:
        distance_sum = 0
        candidate_index = address_to_index(candidate.address, address_list)
        for neighbor in cluster:
            neighbor_index = address_to_index(neighbor.address, address_list)
            distance_sum += distance_matrix[candidate_index][neighbor_index]
        if distance_sum < min_sum:
            min_sum = distance_sum
            new_centroid = candidate
    #print(f"min_sum: {min_sum}, new_centroid: {new_centroid}")
    return new_centroid
    
# This will make sure that the centroids have unique addresses (I was getting strange bugs for occasional indexes out of bounds.)
def select_unique_package_address(package_list, k):
    unique_package_list = []
    unique_address_list = []
    
    while len(unique_package_list) < k:
        test_package = random.choice(package_list)
        
        if test_package.address not in unique_address_list:
            unique_package_list.append(test_package)
            unique_address_list.append(test_package.address)
    
    return unique_package_list
    

def print_clusters(clusters):
    for i, cluster in enumerate(clusters):
        print(f"Cluster {i + 1}:")
        for package in cluster:
            print(f"  ID: {package.package_id}, Address: {package.address}, Delivery Deadline: {package.delivery_deadline}, Special Note: {package.special_note}")
        print()  # Add an extra newline for better readability]
    

#jjg