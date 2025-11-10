from hash_table import HashTable
from warehouse_repository import get_warehouse_hash
from package import Package, print_package_list, print_group_list
from truck import Truck
from datetime import time

class PackageHandler:
    def __init__(self):
        pass
        
    
    def merge_addresses(self):
        warehouse_hash = get_warehouse_hash()
        package_list = list_builder()
        
        for i_package in package_list[:]:
            for j_package in package_list[:]:
                # Skip if comparing the same package
                if i_package.package_id == j_package.package_id:
                    continue
                # Skip if addresses don't match
                if i_package.address != j_package.address:
                    continue
                
                earliest_deadline = min(i_package.delivery_deadline, j_package.delivery_deadline)
                
                # i_package has a special note (not 'X') and j_package does not
                tag = i_package.special_note[0] if i_package.special_note else None
                if tag and tag != 'X' and j_package.special_note is None:
                    j_package.special_note = i_package.special_note
                    i_package.delivery_deadline = j_package.delivery_deadline = earliest_deadline
                    
                # neither has a special note
                elif i_package.special_note is None and j_package.special_note is None:
                    i_package.special_note = f'W, {j_package.package_id}'
                    i_package.parse_special_note()
                    j_package.special_note = f'W, {i_package.package_id}'
                    j_package.parse_special_note()
                    i_package.delivery_deadline = j_package.delivery_deadline = earliest_deadline
        
    
    # Returns the priority_list, which is the union of packages with special notes and delivery deadlines    
    def build_constraints_list(self):
        # The list of packages that have special notes for delivery. Per project specifications, there is a package with an incorrect address. This package, denoted with a special note of 'X' will be handled at the very last and is thus excluded from the special_notes_list.
        special_note_list = list_builder('special_note', 'special_note', 'X')
        
        # The list of packages that have delivery deadlines
        delivery_deadline_list = list_builder('delivery_deadline', 'delivery_deadline', Package.EOD_TIME)
        
        ''' DEBUG ONLY
        print(f"\nspecial_note_list of length {len(special_note_list)}:")
        print_package_list(special_note_list)
        
        print(f"\ndelivery_deadline_list of length {len(delivery_deadline_list)}:")
        print_package_list(delivery_deadline_list)
        '''
        
        # priority_list is the union of special_note_list and delivery_deadline_list
        priority_list = perform_union_on_lists(special_note_list, delivery_deadline_list)
        
        ''' DEBUG ONLY
        print(f"\npriority_list of length {len(priority_list)}:")
        print_package_list(priority_list)
        '''
        
        return priority_list
        
    
    def set_package_priorities(self, ungrouped_list):
        warehouse_hash = get_warehouse_hash()
        
        for package in ungrouped_list:
            #modified_package = hash_table.search(package.package_id)
            
            # Priority 0:    delivery deadline and     delayed
            if package.delivery_deadline != Package.EOD_TIME and (package.special_note and package.special_note[0] == 'D'):
                #print(f"Adding package {package.package_id} to Priority 0 group.") # DEBUG ONLY
                package.priority = 0
                
            # Priority 1:    delivery deadline and not delayed
            elif package.delivery_deadline != Package.EOD_TIME and (not package.special_note or package.special_note[0] != 'D'):
                #print(f"Adding package {package.package_id} to Priority 1 group.") # DEBUG ONLY
                package.priority = 1
                
            # Priority 2: no delivery deadline and not delayed
            elif package.delivery_deadline == Package.EOD_TIME and (not package.special_note or package.special_note[0] != 'D'):
                #print(f"Adding package {package.package_id} to Priority 2 group.") # DEBUG ONLY
                package.priority = 2
                
            # Priority 3: no delivery deadline and     delayed
            elif package.delivery_deadline == Package.EOD_TIME and (package.special_note and package.special_note[0] == 'D'):
                #print(f"Adding package {package.package_id} to Priority 3 group.") # DEBUG ONLY
                package.priority = 3
        
    
    def handle_with_truck_note(self, package_list):
        warehouse_hash = get_warehouse_hash()
        
        for package in package_list[:]:
            if package.special_note and package.special_note[0] == 'T':
                #modified_package = warehouse_hash.search(package.package_id)
                # Truck minus one, because this will be the index of the fleet.
                #modified_package.truck = package.special_note[1] - 1
                package.truck = package.special_note[1] - 1
        
    
    def handle_delayed_without_deadline_note(self, package_list, fleet):
        if fleet.num_trucks == 0:
            raise ValueError("Fleet is empty")
        warehouse_hash = get_warehouse_hash()
        
        for package in package_list:
            # Have to remember that 'EOD' is represented as Package.EOD_TIME in the package object.
            if package.special_note and package.special_note[0] == 'D' and package.delivery_deadline == Package.EOD_TIME:
                empty_truck_found = False
                for i, truck in enumerate(fleet):
                    # Add package to first empty truck in fleet
                    if truck.driver is None:
                        package.truck = i
                        empty_truck_found = True
                        break
                if not empty_truck_found:
                    package.truck = len(fleet.truck_list) - 1
                #print(f"Package {package.package_id} has a D note: {package.special_note}, and deadline is not EOD: {package.delivery_deadline}")
        
    
    def handle_with_package_note(self, package_list):
        warehouse_hash = get_warehouse_hash()
        set_list = []
        
        # Populate the set_list with the special note 'W'. For example, say package 14 has a special note: 'W, 15, 19'. The new_set is first initialized with {14}. Then 15 and 19 are added {14, 15, 19}. Finally this set is appended to the set_list.
        for package in package_list:
            if package.special_note and package.special_note[0] == 'W':
                new_set = {package.package_id}
                new_set.update(package.special_note[1:])
                set_list.append(new_set)
        
        ''' # DEBUG ONLY
        print('\n'.join(f"{set}" for set in set_list)) # Sometimes I just feel like getting fancy with my prints.
        '''
        
        # Compare each set with each other set for intersections and merge until only disjoint sets remain.
        disjoint_sets = merge_sets(set_list)
        
        # Build the result_groups_list from our disjoint sets, so that the priorities can be set and associated on the constraints_list.
        result_groups_list = []
        for id_sets in disjoint_sets:
            group_list = []
            for id in id_sets:
                pkg = warehouse_hash.search(id)
                if not pkg:
                    raise ValueError(f"Package with id {id} not in warehouse!")
                group_list.append(pkg)
            result_groups_list.append(group_list)
        
        '''# DEBUG ONLY
        print("\nGrouped packages:")
        print_group_list(result_groups_list)
        '''
        
        # Set the group attribute of each package based on index of their parent container in result_groups_list
        for i, group in enumerate(result_groups_list):
            for package in group:
                package.group = i
        
        # Find the minimum priority in each package group, and assign each other package in that group with that priority.
        for package_group in result_groups_list:
            min_priority = float('inf')
            for package in package_group:
                #hashed_package = hash_table.search(package.package_id)
                if package.priority is not None:
                    min_priority = min(min_priority, package.priority)
                else:
                    min_priority = 4
                
                # We're adding to the package list so that this can be returned and update the constraints list.
                if package not in package_list:
                    package_list.append(package)
            
            # Finally, reiterate through the group and update the priority.
            for package in package_group:
                #modified_package = hash_table.search(package.package_id)
                package.priority = min_priority
        
        return package_list
        
    
    def add_and_prioritize_remaining_packages(self, package_list):
        warehouse_hash = get_warehouse_hash()
        
        remaining_list = anti_list_builder(package_list)
        
        for package in remaining_list:
            if package.special_note is None:
                package.priority = 4
                package_list.append(package)
            else:
                package.priority = 5
                package_list.append(package)
        
    
    def group_and_sort_list(self, unsorted_list):
        return_list = [[] for _ in range(6)]
        
        # Group packages by priority
        for package in unsorted_list:
            #print(f"  Priority: {package.priority}", end=", ") # DEBUG ONLY
            if 0 <= package.priority <= 5:
                #print(f"adding to group {package.priority}") # DEBUG ONLY
                return_list[package.priority].append(package)
        
        '''# DEBUG ONLY
        print("Prior to sorting by group frequency")
        print_group_list(return_list)
        '''#
        
        # Sort the return_list is place by group attribute frequency.    
        for group in return_list:
            # Build a list of all of the group attribute values in the group
            group_attr_vals = [package.group for package in group if package.group is not None]
            
            # A list of tuples: (group_attr_vals, and the frequency of the group_attr_vals)
            group_attr_and_freq = []
            
            # Check each tuple in the list for 
            for group_number in group_attr_vals:
                found = False
                for pair in group_attr_and_freq:
                    if pair[0] == group_number:
                        #print(f" Found a pair: {pair[0]} and {attr}. pair[0]++") # DEBUG ONLY
                        pair[1] += 1
                        found = True
                        break
                if not found:
                    # Append the first instance of that particular group_attr.
                    group_attr_and_freq.append([group_number, 1])
            
            '''# DEBUG ONLY
            print("\nThe tuples:")
            print(group_attr_and_freq)
            '''#
            
            def get_frequency(group):
                for pair in group_attr_and_freq:
                    if pair[0] == group:
                        return pair[1]
                return 0
        
            group.sort(
                key=lambda package: (
                    -get_frequency(package.group),  # First: frequency (descending)
                    package.group if package.group is not None else float('inf')  # Second: group number
                )

            )
        return return_list
        
    
# Private functions

# Helper function that takes an attribute as input and returns a sorted list of packages with that attribute.
# There are two optional arguments that can exclude an attribute with a target value
def list_builder(attr=None, ex_attr=None, ex_val=None):
    warehouse_hash = get_warehouse_hash()
    
    package_list = []
    
    #print(f"Building package_list based on following input parameters: {attr}, {ex_attr}, {ex_val}") # DEBUG ONLY
    
    # Abbreviated variables to improve readability with the attr method.
    for bucket in warehouse_hash:
        for package in bucket:
            if attr is None:
                package_list.append(package)
            else:
                #print(f"Checking package: {package}") # DEBUG ONLY
                attr_val = getattr(package, attr, None)
                ex_attr_val = getattr(package, ex_attr, None) if ex_attr is not None else None
                
                #print(f"attr_val: {attr_val}, ex_attr_val: {ex_attr_val}") # DEBUG ONLY
                
                if attr_val is not None:
                    # If no exclusion attribute, or exclusion passes
                    if ex_attr_val is None:
                        package_list.append(package)
                    else:
                        # Handle if ex_attr_val is a list
                        if isinstance(ex_attr_val, list):
                            if ex_val not in ex_attr_val:
                                package_list.append(package)
                        else:
                            if ex_attr_val != ex_val:
                                package_list.append(package)

    return sorted(package_list)


def anti_list_builder(package_list=[]):
    warehouse_hash = get_warehouse_hash()
    anti_list = []
    
    for bucket in warehouse_hash:
        for package in bucket:
            if package not in package_list:
                anti_list.append(package)
    
    return sorted(anti_list)
    

# Based partly on KruskalsMinimumSpanningTree algorithm from zyBook 5.12. I had originally included it in the 'handle_with_package_note' function, but the logic was so useful that I decided to keep it as helper function.
def merge_sets(set_list):
    result_list = []
    if not set_list:
        return result_list
    
    while set_list:
        current_set = set_list.pop()
        merged = True
        
        while merged:
            merged = False
            for other_set in set_list[:]:
                if current_set.intersection(other_set):
                    current_set = current_set.union(other_set)
                    set_list.remove(other_set)
                    merged = True
        result_list.append(current_set)
    #
    #print('\n'.join(f"{set}" for set in result_list)) # DEBUG ONLY
    #
    
    return result_list
    

# Helper function performs a union on two lists to exclude duplicate values.
def perform_union_on_lists(list1, list2):
    set1 = set(list1)
    set2 = set(list2)
    
    union_list = list(set1.union(set2))
    
    #'''DEBUG ONLY
    #print("Union of sets 1 and 2:\n")
    #print_package_list(union_list)
    #'''
    
    return sorted(union_list)
    

#jjg