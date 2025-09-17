from address_repository import address_to_index

distance_matrix = None

def set_distance_matrix(data):
    global distance_matrix
    distance_matrix = data
    

def get_distance_matrix():
    return distance_matrix
    

# Helper function that prints a formatted matrix.
def print_distance_matrix(matrix):
    for row in matrix:
        formatted_row = " | ".join(f"{value:>4.1f}" for value in row)  # Using 1 decimal places
        print(formatted_row)
    

def get_distance(a, b):
    index_a = address_to_index(a)
    index_b = address_to_index(b)
    
    return distance_matrix[index_a][index_b]

#jjg