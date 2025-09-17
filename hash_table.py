#Part A. Develop a hash table, without using any additional libraries or classes, that has an insertion function that takes the package ID as input and inserts each of the following data components into the hash table:
#   delivery address
#   delivery deadline
#   delivery city
#   delivery zip code
#   package weight
#   delivery status (i.e., at the hub, en route, or delivered), including the delivery time

class HashTable:
    def __init__(self, size):
        self.size = size
        self.table = [[] for _ in range(size)]
    
    
    # Adding magic methods so that the HashTable object is iterable
    #https://www.toppr.com/guides/python-guide/tutorials/python-advanced-topics/python-iterators/
    def __iter__(self):
        self.iteration = 0
        return self
    def __next__(self):
        #
        #print("from hash_table.py: __next__ function # DEBUG ONLY
        #print(f"{self.iteration} of {self.size}") # DEBUG ONLY
        #
        
        if self.iteration < self.size:
            bucket_index = self.hash(self.iteration)
            bucket_list = self.table[bucket_index]
            self.iteration += 1
            return bucket_list
        else:
            raise StopIteration
    
    
    def hash(self, key):
        if isinstance(key, int):
            return key % self.size
        else:
            raise ValueError("Hash failed: non integer passed as key")
    
    
    def insert(self, key, obj):
        bucket_index = self.hash(key)
        bucket_list = self.table[bucket_index]
        
        if obj not in bucket_list:
            bucket_list.append(obj)
    
    
    def search(self, key):
        bucket_index = self.hash(key)
        bucket_list = self.table[bucket_index]
        
        for item in bucket_list:
            if item.package_id == key:
                return item
        return None
    
    # Part B of the project.
    def lookup_function(self, key):
        bucket_index = self.hash(key)
        bucket_list = self.table[bucket_index]
        
        for item in bucket_list:
            if item.package_id == key:
                
                # Return a tuple containing each of the required data components.
                return (item.address, item.delivery_deadline, item.city, item.zip_code, item.weight_kilo, item.delivery_status)
        return None
    
    
    def remove(self, key, obj):
        bucket_index = self.hash(key)
        bucket_list = self.table[bucket_index]
        
        if obj in bucket_list:
            bucket_list.remove(obj)
            return True
        else:
            return False
    
    
    def iterate(self, key):
        bucket_index = self.hash(key)
    
    
    def print_hash_table(self):
        for index, bucket in enumerate(self.table):
            if bucket: # Only print non-empty buckets
                print(f"  Bucket {index}:")
                for data in bucket:
                    print(f"    {data}")
    
# jjg