class Truck:
    def __init__(self, 
                 truck_id=None, 
                 current_capacity=16, 
                 maximum_capacity=16, 
                 speed_mph=18, 
                 gas=float('inf'), 
                 driver=None, 
                 departure_time=None,
                 return_time=None,
                 departure_address='4001 South 700 East',
                 package_list=None, 
                 route_distance=0.0,):
        if truck_id is not None:
            if type(truck_id) is not int or truck_id < 0:
                raise ValueError(f"Invalid truck_id: {truck_id}")
        if package_list is None:
            package_list = []
        self.truck_id = truck_id
        self.current_capacity = current_capacity if current_capacity < maximum_capacity else maximum_capacity
        self.maximum_capacity = maximum_capacity
        self.speed_mph = speed_mph
        self.gas = gas
        self.departure_time = departure_time
        self.return_time = return_time
        self.departure_address = departure_address
        self.driver = driver
        self.package_list = package_list
        self.route_distance = route_distance
        
    
    def __str__(self):
        # Handling parsed list of packages:
        package_list_str = ', '.join(str(pkg) for pkg in self.package_list) if self.package_list else 'None'
        departure_time_str = self.get_time_str(self.departure_time)
        return_time_str = self.get_time_str(self.return_time)
        
        return (
            f"Truck ID: {self.truck_id + 1 if self.truck_id is not None else 'None':<3}"
            f"Current Capacity: {self.current_capacity:<5}"
            f"Maximum Capacity: {self.maximum_capacity:<5}"
            #f"Speed (mph): {self.speed_mph:<5}"
            #f"Gas: {self.gas:<10}"
            f"Departure Time: {departure_time_str:<10}"
            f"Return Time: {return_time_str:<10}"
            f"Departure Address: {self.departure_address:<40}"
            f"Driver: {self.driver if self.driver is not None else 'None':<10}"
            f"Packages: {package_list_str:<20}"
            #f"Route Distance: {route_distance:<6}"
        )
        
    
    # Adding magic method so that packages can be compared by package_id
    def __lt__(self, other):
        return self.truck_id < other.truck_id
        
    
    def get_time_str(self, time_object):
        if time_object is None:
            return 'None'
        else:
            return time_object.strftime("%I:%M %p")
# jjg