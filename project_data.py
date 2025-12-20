import csv
from package import Package
from hash_table import HashTable

# Function that returns a hash table generated from a csv input
def read_package_data(input):
    # Initialize the hash table by calling the csv_line_count helper function
    hash_table = HashTable(csv_line_count(input))
    package_list = []
    
    with open(input, 'r') as package_file:
        csv_reader = csv.reader(package_file)
        for row in csv_reader:
            # Clean, unpack, and assign
            package_id, address, city, state, zip_code, delivery_deadline, weight_kilo, special_note = map(clean_value, row)
            
            # Create the new package
            new_package = Package(package_id, address, city, state, zip_code, delivery_deadline, weight_kilo, special_note)
            
            # Parse, clean, and reassign the special note:
            new_package.special_note = new_package.parse_special_note()
            
            # Store the package object in the hash table
            hash_table.insert(package_id, new_package)
            #
            #print(row) # DEBUG ONLY
            #
    
    #
    #hash_table.print_hash_table() # DEBUG ONLY
    #
    
    return hash_table
    

# Function that returns a 2d square matrix generated from a csv input
def read_distance_data(input):
    size = csv_line_count(input)
    
    # Initialize a squre matrix using the line count of the input    
    distance_matrix = [[float('inf')]*size for i in range(size)]
    
    #
    #print("from project_data.py: read_distance_data function # DEBUG ONLY
    #print(distance_matrix) # DEBUG ONLY
    #
    
    # Read the values from the input csv and copy into the matrix
    with open(input, 'r') as distance_file:
        csv_reader = csv.reader(distance_file)
        # The lines are stored as a list.
        for row_index, line in enumerate(csv_reader):
            for col_index in range(size):
                if line[col_index] != '':
                    #print("from project_data.py: read_distance_data function # DEBUG ONLY
                    #print(f"Adding: {line[col_index]}") # DEBUG ONLY
                    distance_matrix[row_index][col_index] = float(line[col_index])
    
    # Transpose the distance matrix: set each element at index (i, j) to the value at (j, i)
    for i, row in enumerate(distance_matrix):
        for j in range(size):
            distance_matrix[i][j] = distance_matrix[j][i]
    
    #
    #print("from project_data.py: read_distance_data function # DEBUG ONLY
    #print_distance_matrix(distance_matrix) # DEBUG ONLY
    #
    
    return distance_matrix
    

# Helper function that returns the line count of the CSV input
def csv_line_count(file):
    with open(file, 'r') as file:
        line_count = sum(1 for row in file)
    return line_count
    

# Helper function that cleans the input values prior to adding to hash table.
def clean_value(value):
    if isinstance(value, int):
        return value
    
    if value.strip() == 'None' or value.strip() == '' or value.strip() == 'none':
        #print(f"Cleaning [{value}] of type {type(value)}. Returning None") # DEBUG ONLY
        return None
    try:
        #print(f"Cleaning [{value}] of type {type(value)}. Casting as int and returning {int(value)}") # DEBUG ONLY
        return int(value)
    except ValueError:
        return value
    

#jjg