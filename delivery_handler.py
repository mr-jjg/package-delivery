from enum import Enum
import time as simulate_real_time
from time_utils import get_route_departure_time, get_arrival_time, get_travel_time_in_minutes
from distance_repository import get_distance
from package import Package

class DeliveryHandler:
    RATE = 8 # Set the rate of accelerated real-time
    
    def __init__(self, delivery_list=None):
        if delivery_list is None:
            delivery_list = []
        self.delivery_list = delivery_list
    
    def build_delivery_list(self, fleet):
        available_trucks, waiting_trucks = separate_trucks_by_driver_status(fleet)
        
        # Handle trucks with drivers
        self.generate_delivery_timeline(available_trucks )
        
        # Set attributes for return_time and departure_time. A truck without a driver has a departure time that depends upon the first driver to return to the warehouse.
        driver_return_times = []
        for truck in available_trucks :
            #print(f"{truck.truck_id + 1} truck.return_time: {truck.return_time}") # DEBUG ONLY
            driver_return_times.append(truck.return_time)
        for truck in waiting_trucks :
            truck.departure_time = min(driver_return_times)
            #print(f"{truck.truck_id + 1} truck.departure_time: {truck.departure_time}") # DEBUG ONLY
        
        # Handle trucks without drivers
        self.generate_delivery_timeline(waiting_trucks )
        
        # Sort the list based on 'time'
        self.delivery_list.sort(key=lambda tuple: tuple[2])
        
    
    def generate_delivery_timeline(self, truck_list):
        for truck in truck_list:
            route = truck.package_list
            
            #print(f"Truck {truck.truck_id + 1} route distance: {truck.route_distance}") # DEBUG ONLY
            
            curr_pkg = route[0]
            
            # Truck leaving the warehouse
            departure_tuple = (truck, None, truck.departure_time, DeliveryAction.DEPART)
            self.delivery_list.append(departure_tuple)
            
            
            # Delivery of first package departing from the warehouse
            arr_time = get_arrival_time(truck.departure_time, truck.departure_address, curr_pkg.address, truck.speed_mph)
            delivery_tuple = (truck, curr_pkg, arr_time, DeliveryAction.DELIVER)
            self.delivery_list.append(delivery_tuple)
            
            # Delivery of the remaining packages on the truck
            for i in range(1, len(route)):
                curr_pkg = route[i]
                next_pkg = route[i - 1]
                
                arr_time = get_arrival_time(arr_time, curr_pkg.address, next_pkg.address, truck.speed_mph)
                delivery_tuple = (truck, curr_pkg, arr_time, DeliveryAction.DELIVER)
                self.delivery_list.append(delivery_tuple)
            
            # Truck returning to the warehouse
            arr_time = get_arrival_time(arr_time, next_pkg.address, truck.departure_address, truck.speed_mph)
            return_tuple = (truck, None, arr_time, DeliveryAction.RETURN)
            truck.return_time = arr_time
            self.delivery_list.append(return_tuple)
            
            #print(f"Truck {truck.truck_id + 1} arriving back at the warehouse at {arr_time}") # DEBUG ONLY
        
    
    # This delivers the packages, and simulated accelerated real time. Trucks are updated dynamically by storing updated values in the previous_locations and previous_times lists, and recalculating mid-method. Packages with the wrong addresses are handled by dynamically checking for corrected addresses at the end of each while loop.
    def deliver_packages(self, fleet):
        free_driver = None
        previous_locations = []  # List of tuples for updating route_distances per truck: (truck_id, last_address)
        previous_times = []      # List of tuples for tracking last_time per truck: (truck_id, last_time)
        
        # Iterate over a copy of the list so that the state of the delivery_list can be saved (and corrected)
        delivery_queue = self.delivery_list.copy()
        
        while delivery_queue:
            delivery_tuple = delivery_queue.pop(0)
            truck, package, time, action = unpack_delivery_tuple(delivery_tuple)
            time_str = time.strftime("%H:%M")
            
            # Truck leaving the warehouse
            if action == DeliveryAction.DEPART:
                # Availabe driver is assigned to empty truck
                if truck.driver is None:
                    truck.driver = free_driver
                
                # Update the deliver_status of each package to 'en_route'
                set_packages_en_route(truck.package_list)
                
                # Set starting point and starting time for tracking distance/real-time
                update_previous_location(previous_locations, truck.truck_id, truck.departure_address)
                update_previous_time(previous_times, truck.truck_id, truck.departure_time)
                
                print(f"{action.value:<9} {time_str} | Truck ID: {truck.truck_id + 1} | From: {truck.departure_address:<40}")
            
            # Delivery of the packages
            elif action == DeliveryAction.DELIVER:
                last_location = get_previous_location(previous_locations, truck.truck_id)
                last_time = get_previous_time(previous_times, truck.truck_id)
                
                # Check if package has a special note 'X' to correct address and compare with current time
                if package.special_note and package.special_note[0] == 'X':
                    correction_time = package.special_note[1]
                    # A corrected address would likely be passed to the truck at the time of correction. A more realistic approach would include a corrected_addresses_list of tuples (package_id, corrected_address), which would then update the package dynamically. For the purposes of the project, I'm simply included the corrected address as part of the special note.
                    correct_address = package.special_note[2]
                    correct_city = package.special_note[3]
                    correct_state = package.special_note[4]
                    correct_zip_code = package.special_note[5]
                    
                    last_time = get_previous_time(previous_times, truck.truck_id)
                    
                    if last_time >= correction_time:
                        print(f"  Address correction for package {package.package_id}. Old address: {package.address}")
                        package.address = correct_address
                        package.address_history.append((last_time, correct_address))
                        package.city = correct_city
                        package.state = correct_state
                        package.zip_code = correct_zip_code
                        print(f"  Rerouting to new address: {package.address}")
                        
                        for i, (truck_, package_, event_time, action_) in enumerate(self.delivery_list):
                            if package_ and package_.package_id == package.package_id:
                                package_.address = correct_address
                                package_.city = correct_city
                                package_.state = correct_state
                                package_.zip_code = correct_zip_code
                                self.delivery_list[i] = (truck_, package_, event_time, action)
                
                # Recalculate arrival time to account for any changes mid-route
                new_time = get_arrival_time(last_time, last_location, package.address, truck.speed_mph)
                time_str = new_time.strftime("%H:%M")
                
                # Simulate accelerated real-time
                travel_minutes = get_travel_time_in_minutes(last_time, new_time)
                simulate_real_time.sleep(travel_minutes / self.RATE)
                #print(travel_time) # DEBUG ONLY
                
                # Update the truck's route distance
                distance = get_distance(last_location, package.address)
                truck.route_distance += distance
                #print(f"Distance from {last_location} to {package.address}: {distance}") # DEBUG ONLY
                
                # Update truck's previous time and location
                update_previous_location(previous_locations, truck.truck_id, package.address)
                update_previous_time(previous_times, truck.truck_id, new_time)
                
                # Update the package's delivery attributes
                package.delivery_status = 'delivered'
                package.time_of_delivery = time
                
                # Prepare strings for output
                deadline_str = package.delivery_deadline.strftime("%H:%M") if package.delivery_deadline != package.EOD_TIME else 'EOD'
                met_deadline_str = f" Met deadline: {time < package.delivery_deadline}" if package.delivery_deadline != package.EOD_TIME else ''
                
                # Output
                print(f"{action.value:<9} {time_str} | Package: {package.package_id:<2} | Address: {package.address:<40} | Delivery Deadline: {deadline_str:<7} | {met_deadline_str}")
            
            # Truck returning to the warehouse
            elif action == DeliveryAction.RETURN:
                last_location = get_previous_location(previous_locations, truck.truck_id)
                last_time = get_previous_time(previous_times, truck.truck_id)
                
                # Recalculate arrival time back to hub to account for any changes mid-route
                new_time = get_arrival_time(last_time, last_location, truck.departure_address, truck.speed_mph)
                time_str = new_time.strftime("%H:%M")
                
                distance = get_distance(last_location, truck.departure_address)
                
                truck.route_distance += distance
                update_previous_location(previous_locations, truck.truck_id, truck.departure_address)
                #print(f"Distance from {last_location} to {truck.departure_address}: {distance}") # DEBUG ONLY
                
                # Simulate accelerated real-time
                travel_minutes = get_travel_time_in_minutes(last_time, new_time)
                simulate_real_time.sleep(travel_minutes / self.RATE)
                
                # Update truck's previous time and location
                update_previous_time(previous_times, truck.truck_id, new_time)
                update_previous_location(previous_locations, truck.truck_id, truck.departure_address)
                
                # Driver has completed the route - add to available driver pool.
                free_driver = truck.driver
                
                # Output
                print(f"{action.value:<9} {time_str} | Truck ID: {truck.truck_id + 1} | From: {truck.departure_address:<40}")
        
        print()
        for truck in fleet:
            print(f"Truck ID: {truck.truck_id + 1}, Final Route Distance: {truck.route_distance}")
        
    
    def print_delivery_list(self):
        #print(f"Length: {len(self.delivery_list)}") # DEBUG ONLY
        for tuple in self.delivery_list:
            truck, package, time, action = unpack_delivery_tuple(tuple)
            
            time_str = time.strftime("%H:%M")
            truck_id = f"{truck.truck_id + 1}"
            pkg_id = f"{str(package.package_id) if package else 'NA':<2}"
            address = package.address if package else truck.departure_address
            
            print(f"{action.value:<7} {time_str} | Truck ID: {truck_id} | Package ID: {pkg_id} | Address: {address}")
        
    
    def print_package_statuses_at(self, time_input, fleet):
        copied_packages = []
        
        # Make copies of all package objects to maintain the integrity of the data
        for truck in fleet.truck_list:
            for package in truck.package_list:
                copied_pkg = copy_package(package, truck.truck_id)
                copied_packages.append(copied_pkg)
        
        # Iterate through the copied_packages and set attributes
        for tuple in self.delivery_list:
            truck, package, time, action = unpack_delivery_tuple(tuple)
            
            if time > time_input:
                break
            
            if action == DeliveryAction.DEPART:
                for package_ in copied_packages:
                    if package_.truck == truck.truck_id and package_.delivery_status == 'at_the_hub':
                        package_.delivery_status = 'en_route'
            
            # Only add packages to the copied_packages list
            elif action == DeliveryAction.DELIVER and package:
                for package_ in copied_packages:
                    if package_.package_id == package.package_id:
                        package_.delivery_status = 'delivered'
                        package_.time_of_delivery = time
                        
        # Print each package
        for package in copied_packages: #sorted(copied_packages, key=lambda package: package.package_id):
            time_of_delivery_str = package.time_of_delivery.strftime('%H:%M') if package.time_of_delivery else 'NA'
            delivery_deadline_str = package.delivery_deadline.strftime('%H:%M') if package.delivery_deadline != package.EOD_TIME else 'EOD'
            address_at_time = get_address_at_time(package, time_input)
            
            # Address, deadline, truck_no, delivery_time
            print(f"Package ID: {package.package_id:<2} | Truck ID: {package.truck:<4} | Address: {address_at_time:<40} | Delivery Deadline: {delivery_deadline_str:<5} | Delivery Status: {package.delivery_status:<10} | Time of Delivery: {time_of_delivery_str}")
        
    

# https://www.geeksforgeeks.org/enum-in-python/
class DeliveryAction(Enum):
    DEPART = 'Departed'
    DELIVER = 'Delivered'
    RETURN = 'Returned'

# Helper

def separate_trucks_by_driver_status(fleet):
    available_trucks  = []
    waiting_trucks  = []
    
    for truck in fleet.truck_list:
        if truck.driver:
            truck.departure_time = get_route_departure_time(truck.package_list)
            available_trucks.append(truck)
        else:
            waiting_trucks.append(truck)
    
    return available_trucks, waiting_trucks

def set_packages_en_route(package_list):
    for package in package_list:
        package.delivery_status = 'en_route'

def unpack_delivery_tuple(tuple):
    truck, package, time, action = tuple
    return truck, package, time, action
    
def update_previous_location(prev_locations_list, truck_id, address):
    for i, (id, _) in enumerate(prev_locations_list):
        if id == truck_id:
            prev_locations_list[i] = (truck_id, address)
            return
    prev_locations_list.append((truck_id, address))

def get_previous_location(prev_locations_list, truck_id):
    for id, address in prev_locations_list:
        if id == truck_id:
            return address
    return None

def update_previous_time(previous_times_list, truck_id, time):
    for i, (id, _) in enumerate(previous_times_list):
        if id == truck_id:
            previous_times_list[i] = (truck_id, time)
            return
    previous_times_list.append((truck_id, time))

def get_previous_time(previous_times_list, truck_id):
    for id, time in previous_times_list:
        if id == truck_id:
            return time
    return None

def copy_package(original_package, truck_id):
    new_package = Package(package_id = original_package.package_id,
                          address = original_package.address,
                          city = original_package.city,
                          state = original_package.state,
                          zip_code = original_package.zip_code,
                          delivery_deadline = original_package.delivery_deadline,
                          weight_kilo = original_package.weight_kilo,
                          special_note = original_package.special_note,
                          delivery_status = 'at_the_hub',
                          time_of_delivery = None,
                          truck = truck_id,
                          group = original_package.group,
                          priority = original_package.priority)
    new_package.address_history = list(original_package.address_history)
    return new_package
    
def get_address_at_time(package, time_input):
    # Return address at time of input
    address_at_time_input = package.address_history[0][1]
    
    for time, address in package.address_history:
        if time is not None and time <= time_input:
            address_at_time_input = address
        elif time is not None and time > time_input:
            break
    return address_at_time_input
#jjg