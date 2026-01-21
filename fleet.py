from truck import Truck

class Fleet:
    def __init__(self, num_trucks, truck_list=None):
        if truck_list is None:
            self.truck_list = [Truck() for _ in range(num_trucks)]
            for i, truck in enumerate(self.truck_list):
                truck.truck_id = i
        else:
            self.truck_list = truck_list
        self.num_trucks = num_trucks
        
    def add_truck(self, truck):
        self.truck_list.append(truck)
        self.num_trucks += 1
        
    def assign_drivers_to_trucks(self, driver_list):
        for driver in driver_list:
            for truck in self.truck_list:
                if not truck.driver:
                    truck.driver = driver
                    break
    
    # Make fleet iterable
    def __iter__(self):
        return iter(self.truck_list)
    
    def print_fleet(self):
        package_count = 0
        print("\nFleet status:")
        for i, truck in enumerate(self.truck_list):
            package_count += len(truck.package_list)
            print(f"  Truck {i+1} | Load {truck.maximum_capacity - truck.current_capacity}")
            if not truck.package_list:
                print("    Empty")
            else:
                for package in truck.package_list:
                    print(f"    {package}")
        print(f"  Total packages loaded on trucks: {package_count}")
        
    def get_empty_trucks(self):
        # Iterate through the fleet and track the empty trucks in a list.
        empty_truck_list = []
        for truck in self.truck_list:
            if not truck.package_list:
                empty_truck_list.append(truck.truck_id)
        
        return empty_truck_list

    def get_truck_ids(self):
        # Iterate through the fleet and return a list of truck IDs
        if not self.truck_list or self.num_trucks == 0:
            raise ValueError("Fleet has no truck")
        return[t.truck_id for t in self.truck_list]
#jjg