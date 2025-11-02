from package import Package

address_list = None

def set_address_list(data):
    global address_list
    if not isinstance(data, list):
        raise ValueError("address_list must be a list")

    for i, row in enumerate(data):
        if not isinstance(row, list) or len(row) != 3:
            raise ValueError(f"row {i} must be a list with 3 elements")
        id_, _, addr = row[0], row[1], row[2]
        if not isinstance(id_, int):
            raise ValueError(f"row {i} id must be an int")
        if not isinstance(addr, str):
            raise ValueError(f"row {i} address must be a string")
    address_list = data
    

def get_address_list():
    return address_list
    

def address_to_index(address):
    if address_list is None:
        raise RuntimeError("address_list is not set; call set_address_list(...) first")
    for addr in address_list:
        if addr[2] == address:
            return int(addr[0])
    return None
    

def index_to_address(index):
    if address_list is None:
        raise RuntimeError("address_list is not set; call set_address_list(...) first")
    for addr in address_list:
        if addr[0] == index:
            return addr[2]
    return None
    

#jjg