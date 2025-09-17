import time as simulate_real_time
from datetime import time as dt_time
from warehouse_repository import get_warehouse_hash  # your package hash table
from package import Package

def launch_ui(fleet, delivery_handler):
    warehouse_hash = get_warehouse_hash()
    
    print("\n--- PACKAGE TRACKING INTERFACE ---")
    print("\n-----------------------------------")
    print("\nCheck status while trucks are out for delivery.")
    
    while True:
        print("Options:")
        print("1 - Lookup package by ID")
        print("2 - View all packages")
        print("3 - View all packages at time hh:mm")
        print("4 - View total mileage traveled")
        print("0 - Exit interface")
        
        choice = input("Enter your choice: ").strip()
        
        if choice == "1":
            package_id = int(input("Enter package ID: ").strip())
            package = warehouse_hash.search(package_id)
            if package:
                print_package_status(package)
            else:
                print(f"Package ID {package_id} not found.")

        elif choice == "2":
            print("\nAll Packages:")
            for bucket in warehouse_hash:
                for package in bucket:
                    print_package_status(package)
        
        elif choice == "3":
            time_input_str = input("  Please input time in hh:mm: ").strip()
            try:
                hour_minute = time_input_str.split(":")
                
                hour = int(hour_minute[0])
                minute = int(hour_minute[1])
                
                check_time = dt_time(hour, minute)
                
                delivery_handler.print_package_statuses_at(check_time, fleet)
            except (ValueError, IndexError):
                print("Invalid time format. Please enter in hh:mm format.")
            

        elif choice == "4":
            total_miles = 0
            for truck in fleet.truck_list:
                total_miles += truck.route_distance
                
            print(f"Total miles traveled so far: {total_miles:.2f}")

        elif choice == "0":
            print("Exiting interface...")
            break
        else:
            print("Invalid choice. Try again.")
        
        print("\n-----------------------------------")

        simulate_real_time.sleep(0.5)


def print_package_status(package):
    if package.time_of_delivery:
        delivery_time = package.time_of_delivery.strftime("%H:%M")
        truck = "None"
    else:
        delivery_time = "NA"
        truck = package.truck
    
    print(f"Package ID: {package.package_id:<2} | Truck ID: {truck:<4} | Status: {package.delivery_status:<10} | Delivered at: {delivery_time}")

#jjg