from package import Package

address_list = None

def set_address_list(data):
    global address_list
    address_list = data
    

def get_address_list():
    return address_list
    

# Helper function that prints the address list. Simply saves space in main.
def print_address_list(list):
    for address in list:
        print(address)
    

def address_to_index(address):
    for sublist in address_list:
        if sublist[2] == address:
            return int(sublist[0])
    
    print(f"{address} not found! Returning -1")
    return -1
    

def index_to_address(index):
    for sublist in address_list:
        if sublist[0] == index:
            return sublist[2]
    

# A list of tuples to store unvisited vertices: ( package_id, address_index )
def build_vertices_list(package_list, start_point):
    vertices_list = [(None, address_to_index(start_point))]
    
    for package in package_list:
        if package.address != start_point:
            address_index = address_to_index(package.address)
            vertices_list.append((package.package_id, address_index))
            #print(f"{package.address} with Package ID {package.package_id} indexes to {address_index} in address_list") # DEBUG ONLY
    return vertices_list
#jjg