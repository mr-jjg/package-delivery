import copy
import hash_table

warehouse_hash = None
warehouse_base = None

def set_warehouse_hash(data):
    global warehouse_hash
    if not isinstance(data, hash_table.HashTable):
        raise ValueError("warehouse_hash must be a HashTable")
    warehouse_hash = data

def get_warehouse_hash():
    return warehouse_hash

def set_warehouse_base(data):
    global warehouse_base
    if not isinstance(data, hash_table.HashTable):
        raise ValueError("warehouse_base must be a HashTable")
    warehouse_base = copy.deepcopy(data)

def reset_warehouse():
    global warehouse_hash
    if warehouse_base is None:
        raise RuntimeError("warehouse_base not set")
    warehouse_hash = copy.deepcopy(warehouse_base)

#jjg