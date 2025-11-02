from package import Package

address_list = None

def set_address_list(data):
    global address_list
    if not isinstance(data, list):
        raise ValueError("address_list must be a list")
    else:
        address_list = data
    #for row in data:
        #Do something with the row to validate it, amirite?
        #Should be in the form [int, str, str]
    

def get_address_list():
    return address_list
    

def address_to_index(address):
    for addr in address_list:
        if addr[2] == address:
            return int(addr[0])
    return None
    

def index_to_address(index):
    for addr in address_list:
        if addr[0] == index:
            return addr[2]
    return None
    

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