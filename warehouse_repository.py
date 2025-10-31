import hash_table

warehouse_hash = None

def set_warehouse_hash(data):
    global warehouse_hash
    if not isinstance(data, hash_table.HashTable):
        raise ValueError("warehouse_hash must be a HashTable")
    else:
        warehouse_hash = data

def get_warehouse_hash():
    return warehouse_hash

#jjg