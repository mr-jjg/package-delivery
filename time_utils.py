from datetime import time
from distance_repository import get_distance

# Takes a float object representing hours and returns a time object of h:m. Source utilized: https://timeanalyticssoftware.com/decimal-hours-converter/#:~:text=If%20the%20decimal%20hours%20have,45%20minutes%2C%20and%200%20seconds.
def float_to_time(h_float):
    h = int(h_float)
    
    m_float = (h_float - h) * 60
    #m = int(m_float)
    m = round(m_float)
    
    if m == 60:
        h += 1
        m = 0

    # Return a time object
    return time(h, m)
    

def get_route_departure_time(package_list):
    # Per project instruction: 'Drivers leave the hub no earlier than 8:00 a.m'
    earliest_departure = time(8, 0)
    # Check for delayed packages or delivery deadlines
    for package in package_list:
        if package.special_note and package.special_note[0] == 'D':
            delayed_time = package.special_note[1]
            earliest_departure = max(earliest_departure, delayed_time)
    
    return earliest_departure
    

def get_arrival_time(departure_time, start_point, end_point, speed_mph):
    distance = get_distance(start_point, end_point)
    travel_time = float_to_time(distance / speed_mph)
    #print(f"DEBUG: travel_time: {travel_time}, travel_time type {type(travel_time)}")
    return calculate_travel_time(departure_time, travel_time)
    

def calculate_travel_time(now_time, travel_time):
    
    now_minutes = now_time.hour * 60 + now_time.minute
    travel_minutes = travel_time.hour * 60 + travel_time.minute
    
    arrival_minutes = now_minutes + travel_minutes
    #print(f"arrival_time_minutes: {arrival_minutes}")
    
    # Convert minutes to h:m. Source utilized: https://www.youtube.com/watch?v=ugXLIlM7PW0
    h_float = arrival_minutes / 60
    h = int(h_float)
    
    m_float = (h_float - h) * 60
    m = int(m_float)
    
    #print(f"DEBUG: h: {h}, m type {type(m)}")
    #print(f"DEBUG: h: {m}, m type {type(m)}")
    
    return time(h, m)
    
    
def get_travel_time_in_minutes(now_time, travel_time):
    now_minutes = now_time.hour * 60 + now_time.minute
    travel_minutes = travel_time.hour * 60 + travel_time.minute
    
    return travel_minutes - now_minutes
    

#jjg