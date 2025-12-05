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
            if not route:
                continue
            
            #print(f"Truck {truck.truck_id + 1} route distance: {truck.route_distance}") # DEBUG ONLY
            
            first_pkg = route[0]
            
            # Truck leaving the warehouse
            self.delivery_list.append((truck, None, truck.departure_time, DeliveryAction.DEPART))
            
            # Delivery of first package departing from the warehouse
            arr_time = get_arrival_time(truck.departure_time, truck.departure_address, first_pkg.address, truck.speed_mph)
            self.delivery_list.append((truck, first_pkg, arr_time, DeliveryAction.DELIVER))

            last_address = first_pkg.address
            
            # Delivery of the remaining packages on the truck
            for pkg in route[1:]:
                arr_time = get_arrival_time(arr_time, last_address, pkg.address, truck.speed_mph)
                self.delivery_list.append((truck, pkg, arr_time, DeliveryAction.DELIVER))
                last_address = pkg.address
            
            # Truck returning to the warehouse
            arr_time = get_arrival_time(arr_time, last_address, truck.departure_address, truck.speed_mph)
            truck.return_time = arr_time
            self.delivery_list.append((truck, None, arr_time, DeliveryAction.RETURN))
            
            #print(f"Truck {truck.truck_id + 1} arriving back at the warehouse at {arr_time}") # DEBUG ONLY
        
    
    # This delivers the packages, and simulated accelerated real time. Trucks are updated dynamically by storing updated values in the previous_locations and previous_times lists, and recalculating mid-method. Packages with the wrong addresses are handled by dynamically checking for corrected addresses at the end of each while loop.
    def deliver_packages(self, fleet):
        free_driver = None
        self.previous_locations = []  # List of tuples for updating route_distances per truck: (truck_id, last_address)
        self.previous_times = []      # List of tuples for tracking last_time per truck: (truck_id, last_time)

        # Iterate over a copy of the list so that the state of the delivery_list can be saved (and corrected)
        delivery_queue = self.delivery_list.copy()
        
        while delivery_queue:
            delivery_tuple = delivery_queue.pop(0)
            truck, package, time, action = delivery_tuple
            time_str = time.strftime("%H:%M")
            
            # Truck leaving the warehouse
            if action == DeliveryAction.DEPART:
                # Availabe driver is assigned to empty truck
                if truck.driver is None:
                    truck.driver = free_driver
                
                self.handle_delivery_action_departed(truck)
                
                print(f"{action.value:<9} {time_str} | Truck ID: {truck.truck_id + 1} | From: {truck.departure_address:<40}")
            
            # Delivery of the packages
            elif action == DeliveryAction.DELIVER:
                self.handle_delivery_action_delivered(time, package, truck)
                
                # Prepare strings for output
                deadline_str = package.delivery_deadline.strftime("%H:%M") if package.delivery_deadline != package.EOD_TIME else 'EOD'
                met_deadline_str = f" Met deadline: {time < package.delivery_deadline}" if package.delivery_deadline != package.EOD_TIME else ''
                
                # Output
                print(f"{action.value:<9} {time_str} | Package: {package.package_id:<2} | Address: {package.address:<40} | Delivery Deadline: {deadline_str:<7} | {met_deadline_str}")
            
            # Truck returning to the warehouse
            elif action == DeliveryAction.RETURN:
                self.handle_delivery_action_returned(truck)
                
                # Driver has completed the route - add to available driver pool.
                free_driver = truck.driver
                
                # Output
                print(f"{action.value:<9} {time_str} | Truck ID: {truck.truck_id + 1} | From: {truck.departure_address:<40}")
        
        self.previous_locations = []
        self.previous_times = []

        print()
        for truck in fleet:
            print(f"Truck ID: {truck.truck_id + 1}, Final Route Distance: {truck.route_distance}")
        
    def handle_delivery_action_departed(self, truck):
        # Update the deliver_status of each package to 'en_route'
        set_packages_en_route(truck.package_list)

        # Set starting point and starting time for tracking distance/real-time
        update_previous_location(self.previous_locations, truck.truck_id, truck.departure_address)
        update_previous_time(self.previous_times, truck.truck_id, truck.departure_time)

    def handle_delivery_action_delivered(self, time, package, truck):
        last_location = get_previous_location(self.previous_locations, truck.truck_id)
        last_time = get_previous_time(self.previous_times, truck.truck_id)

        # Check if package has a special note 'X' to correct address and compare with current time
        if package.special_note and package.special_note[0] == 'X':
            correction_time = package.special_note[1]
            # A corrected address would likely be passed to the truck at the time of correction. A more realistic approach would include a corrected_addresses_list of tuples (package_id, corrected_address), which would then update the package dynamically. For the purposes of the project, I'm simply included the corrected address as part of the special note.
            correct_address = package.special_note[2]
            correct_city = package.special_note[3]
            correct_state = package.special_note[4]
            correct_zip_code = package.special_note[5]

            last_time = get_previous_time(self.previous_times, truck.truck_id)

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
                        self.delivery_list[i] = (truck_, package_, event_time, action_)

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
        update_previous_location(self.previous_locations, truck.truck_id, package.address)
        update_previous_time(self.previous_times, truck.truck_id, new_time)

        # Update the package's delivery attributes
        package.delivery_status = 'delivered'
        package.time_of_delivery = time

    def handle_delivery_action_returned(self, truck):
        last_location = get_previous_location(self.previous_locations, truck.truck_id)
        last_time = get_previous_time(self.previous_times, truck.truck_id)

        # Recalculate arrival time back to hub to account for any changes mid-route
        new_time = get_arrival_time(last_time, last_location, truck.departure_address, truck.speed_mph)
        time_str = new_time.strftime("%H:%M")

        distance = get_distance(last_location, truck.departure_address)

        truck.route_distance += distance
        update_previous_location(self.previous_locations, truck.truck_id, truck.departure_address)
        #print(f"Distance from {last_location} to {truck.departure_address}: {distance}") # DEBUG ONLY

        # Simulate accelerated real-time
        travel_minutes = get_travel_time_in_minutes(last_time, new_time)
        simulate_real_time.sleep(travel_minutes / self.RATE)

        # Update truck's previous time and location
        update_previous_time(self.previous_times, truck.truck_id, new_time)
        update_previous_location(self.previous_locations, truck.truck_id, truck.departure_address)
    
    def print_delivery_list(self):
        #print(f"Length: {len(self.delivery_list)}") # DEBUG ONLY
        for delivery_tuple in self.delivery_list:
            truck, package, time, action = delivery_tuple
            
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
        for delivery_tuple in self.delivery_list:
            truck, package, time, action = delivery_tuple
            
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

def update_previous_time(previous_times_list, truck_id, timestamp):
    for i, (id, _) in enumerate(previous_times_list):
        if id == truck_id:
            previous_times_list[i] = (truck_id, timestamp)
            return
    previous_times_list.append((truck_id, timestamp))

def get_previous_time(previous_times_list, truck_id):
    for id, timestamp in previous_times_list:
        if id == truck_id:
            return timestamp
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
    
    for timestamp, address in package.address_history:
        if timestamp is not None and timestamp <= time_input:
            address_at_time_input = address
        elif timestamp is not None and timestamp > time_input:
            break
    return address_at_time_input
#jjg