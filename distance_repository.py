import math
from address_repository import address_to_index

distance_matrix = None

def set_distance_matrix(data):
    global distance_matrix
    if not data or len(data) < 2:
        raise ValueError("distance matrix must have at least two addresses")

    n = len(data)
    if any(len(row) != n for row in data):
        raise ValueError("distance matrix must be symmetrical")

    for i in range(n):
        for j in range(n):
            v = data[i][j]
            if not isinstance(v, (int, float)):
                raise ValueError(f"row {i} id must be numerica")
            if not math.isinf(v) and v < 0:
                raise ValueError("distances must be non-negative")
    for i in range(n):
        if not math.isinf(data[i][i]) and data[i][i] != 0:
            raise ValueError("diagonal must be zero")
            for j in range(i + 1, n):
                a, b = data[i][j], data[j][i]
                if math.isinf(a) and math.isinf(b):
                    continue
                if a != b:
                    raise ValueError("distance matrix must be symmetric")

    distance_matrix = data
    

def get_distance_matrix():
    if distance_matrix is None:
        raise RuntimeError("distance_matrix is not set; call set_distance_matrix(...) first")
    return distance_matrix
    

# Helper function that prints a formatted matrix.
def print_distance_matrix(matrix):
    for row in matrix:
        formatted_row = " | ".join(f"{value:>4.1f}" for value in row)  # Using 1 decimal places
        print(formatted_row)
    

def get_distance(addr_a, addr_b):
    index_a = address_to_index(addr_a)
    index_b = address_to_index(addr_b)
    
    return distance_matrix[index_a][index_b]

#jjg