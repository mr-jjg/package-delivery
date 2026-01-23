from warehouse_repository import set_warehouse_hash, get_warehouse_hash, set_warehouse_base, reset_warehouse
from address_repository import set_address_list
from distance_repository import set_distance_matrix, print_distance_matrix
from project_data import read_package_data, read_address_data, read_distance_data
from package import print_package_list, print_group_list
from truck import Truck
from fleet import Fleet
from package_handler import PackageHandler
from package_loader import PackageLoader
from delivery_handler import DeliveryHandler
from tools.reporter import Reporter, VerbosityLevel
import argparse


parser = argparse.ArgumentParser(description="WGUPS Package Delivery Program")
parser.add_argument(
    "-v", "--verbosity",
    type=int,
    choices=[0,1,2],
    default=0,
    help="Set verbosity level (0 = none, 1 = progress, 2 = information)"
)
parser.add_argument(
    "-p", "--package_csv",
    default="default.csv",
    help="CSV filename to load package data from"
)
args = parser.parse_args()
VERBOSITY = args.verbosity
package_list = args.package_csv

reporter = Reporter(VERBOSITY)

print("\nPress Enter to begin...")
input()


def read_data(package_list):
    reporter.report(VerbosityLevel.PROG, "\n\n")
    reporter.report(VerbosityLevel.PROG, "-----------------------------------")
    reporter.report(VerbosityLevel.PROG, "           READING DATA            ")
    reporter.report(VerbosityLevel.PROG, "-----------------------------------")

    # Read package data from packageCSV.csv file and store in the data_repository module for global access
    reporter.report(VerbosityLevel.PROG, "\nReading package data from packageCSV.csv file and storing in the 'warehouse_hash' table...")
    package_data = read_package_data(package_list)
    set_warehouse_hash(package_data)
    set_warehouse_base(package_data)
    warehouse_hash = get_warehouse_hash()
    reporter.report(VerbosityLevel.INFO, "\nPrinting warehouse_hash:")
    if VERBOSITY == 2: warehouse_hash.print_hash_table()


    # Read address data from addressCSV.csv file and store in the 'address_list'
    reporter.report(VerbosityLevel.PROG, "\nReading address data from addressCSV.csv file and storing in the 'address_list'...")
    address_list = read_address_data('addressCSV.csv')
    set_address_list(address_list)
    reporter.report(VerbosityLevel.INFO, "\nPrinting address_list:")
    if VERBOSITY == 2:
        for address in address_list:
            print(address)


    # Read distance data from distanceCSV.csv and store into a 2d symmetrical 'distance_matrix'
    reporter.report(VerbosityLevel.PROG, "\nReading distance data from distanceCSV.csv and storing into a 2d symmetrical 'distance_matrix'...")
    distance_matrix = read_distance_data('distanceCSV.csv')
    set_distance_matrix(distance_matrix)
    reporter.report(VerbosityLevel.INFO, "\nPrinting distance_matrix:")
    if VERBOSITY == 2: print_distance_matrix(distance_matrix)


    reporter.report(VerbosityLevel.INFO, "\nPress Enter to continue...")
    if VERBOSITY == 2: input()


def run(num_trucks, num_drivers):
    reporter.report(VerbosityLevel.PROG, "\n\n")
    reporter.report(VerbosityLevel.PROG, "-----------------------------------")
    reporter.report(VerbosityLevel.PROG, "          PREPARING FLEET          ")
    reporter.report(VerbosityLevel.PROG, "-----------------------------------")

    # Instantiate a fleet with 3 trucks and 2 drivers
    truck_word  = "truck"  if num_trucks  == 1 else "trucks"
    driver_word = "driver" if num_drivers == 1 else "drivers"
    reporter.report(VerbosityLevel.PROG, f"\nInstantiating a fleet with {num_trucks} {truck_word} and {num_drivers} {driver_word}...")
    drivers = [f"Driver{i+1}" for i in range(num_drivers)]
    fleet = Fleet(num_trucks)
    fleet.assign_drivers_to_trucks(drivers)
    reporter.report(VerbosityLevel.INFO, "\nPrinting fleet:")
    if VERBOSITY == 2: fleet.print_fleet()


    reporter.report(VerbosityLevel.PROG, "\nPress Enter to continue...")
    if VERBOSITY >= 1: input()


    reporter.report(VerbosityLevel.PROG, "\n\n")
    reporter.report(VerbosityLevel.PROG, "-----------------------------------")
    reporter.report(VerbosityLevel.PROG, "   HANDLING PACKAGE CONSTRAINTS    ")
    reporter.report(VerbosityLevel.PROG, "-----------------------------------")

    # Instantiate PackageHandler object, which contains the methods that manage sorting and categorization of packages.
    reporter.report(VerbosityLevel.PROG, "\nInstantiating PackageHandler object, which contains the methods that manage sorting and categorization of packages...")
    package_handler = PackageHandler()


    # Compare and set special notes and deadlines of packages that share an address. If no special note, create 'W' notes for each instead.
    reporter.report(VerbosityLevel.PROG, "\nComparing and setting special_note and delivery_deadline attributes of packages that share an address. Creating 'W' notes for those without special_notes to guarantee co-delivery...")
    package_handler.merge_addresses()


    # Search the warehouse for all packages with constraints: delivery_deadline, special_note and return as a list of packages.
    reporter.report(VerbosityLevel.PROG, "\nSearching the warehouse for all packages with constraints: delivery_deadline, special_note and return as a list of packages...")
    constraints_list = package_handler.build_constraints_list()
    reporter.report(VerbosityLevel.INFO, f"\n'constraints_list' of length {len(constraints_list)} - all packages with constraints: delivery_deadline, special_note (not including package with wrong address, with special_note 'X')\n")
    if VERBOSITY == 2: print_package_list(constraints_list)
    reporter.report(VerbosityLevel.PROG, "\nPress Enter to continue...")
    if VERBOSITY >= 1: input()


    # This returns a list grouping packages by priority solely for the purposes of a visual aid. The important thing to note is that the priority attribute of each package in the constraints_list is set based upon the following criteria:
    # Priority 0:    delivery deadline and     delayed
    # Priority 1:    delivery deadline and not delayed
    # Priority 2: no delivery deadline and not delayed
    # Priority 3: no delivery deadline and     delayed
    reporter.report(VerbosityLevel.PROG, "\nSetting priority attribute of each package in the constraints_list based upon the following criteria:")
    reporter.report(VerbosityLevel.PROG, "  Priority 0:    delivery deadline and     delayed")
    reporter.report(VerbosityLevel.PROG, "  Priority 1:    delivery deadline and not delayed")
    reporter.report(VerbosityLevel.PROG, "  Priority 2: no delivery deadline and not delayed")
    reporter.report(VerbosityLevel.PROG, "  Priority 3: no delivery deadline and     delayed")
    package_handler.set_package_priorities(constraints_list)
    reporter.report(VerbosityLevel.INFO, f"\nLength {len(constraints_list)} - packages prioritized by delivery_deadline and special note 'D'.\n")
    if VERBOSITY == 2: print_package_list(constraints_list)
    reporter.report(VerbosityLevel.PROG, "\nPress Enter to continue...")
    if VERBOSITY >= 1: input()


    # Handle special_note: 'Can only be on truck n' ('T' notes)
    reporter.report(VerbosityLevel.PROG, "\nHandling special_note: 'Can only be on truck n' ('T' notes)...")
    package_handler.handle_with_truck_note(constraints_list, fleet)
    reporter.report(VerbosityLevel.INFO, f"\nLength {len(constraints_list)} - all packages with special notes relating to packages that must be delivered with specific trucks: \n")
    if VERBOSITY == 2: print_package_list(constraints_list)
    reporter.report(VerbosityLevel.PROG, "\nPress Enter to continue...")
    if VERBOSITY >= 1: input()


    # Handle special note: 'Delayed on flight' ('D' notes). The packages with a delivery deadline are considered highest priority, and without a delivery deadline are considered lowest priority.
    reporter.report(VerbosityLevel.PROG, "\nHandling special note: 'Delayed on flight' ('D' notes) with a deadline...")
    package_handler.handle_delayed_with_deadline_note(constraints_list, fleet)
    reporter.report(VerbosityLevel.INFO, f"\nLength {len(constraints_list)} - all packages with special notes relating to delayed packages with a delivery deadline.\n")
    if VERBOSITY == 2: print_package_list(constraints_list)
    reporter.report(VerbosityLevel.PROG, "\nPress Enter to continue...")
    if VERBOSITY >= 1: input()

    reporter.report(VerbosityLevel.PROG, "\nHandling special note: 'Delayed on flight' ('D' notes) without a deadline...")
    package_handler.handle_delayed_without_deadline_note(constraints_list, fleet)
    reporter.report(VerbosityLevel.INFO, f"\nLength {len(constraints_list)} - all packages with special notes relating to delayed packages without a delivery deadline.\n")
    if VERBOSITY == 2: print_package_list(constraints_list)
    reporter.report(VerbosityLevel.PROG, "\nPress Enter to continue...")
    if VERBOSITY >= 1: input()


    # Handle special note: 'Must be delivered with x' ('W' notes). This clever algorithm uses the properties of sets to first build a list of sets before merging all sets that share common values into the smallest group of sets. The idea for handling this special note occured to me when I was boiling water; I watched while the condensation built until eventually the larger droplets bump into the smaller droplets and absorb them until their mass can no longer keep them hanging upside down and finally racing down the slope of the clear glass lid into the oblivion below. I had to work the KruskalsMinimumSpanningTree algorithm out by hand multiple times and augment it to fit my purposes, but I was thrilled enough with the results that I moved the logic for merging sets into a helper function. This algorithm also sets the package.group and the package.priority attributes of each package so they are sure to be loaded onto the same truck.
    reporter.report(VerbosityLevel.PROG, "\nHandling special note: 'Must be delivered with x' ('W' notes)...")
    constraints_list = package_handler.handle_with_package_note(constraints_list)
    reporter.report(VerbosityLevel.INFO, f"\n'constraints_list' len: {len(constraints_list)} - added packages grouped with packages that have the 'W' constraint, as they have the constraint by association. Set the group attribute of each package as needed.")
    if VERBOSITY == 2: print_package_list(constraints_list)
    reporter.report(VerbosityLevel.PROG, "\nPress Enter to continue...")
    if VERBOSITY >= 1: input()


    # Handles the remaining packages by building a list of all packages not in constraints_list, setting their priority to 4, and appending to form one list that contains all the packages in the warehouse.
    reporter.report(VerbosityLevel.PROG, "\nHandling the remaining packages...")
    package_handler.add_and_prioritize_remaining_packages(constraints_list)
    reporter.report(VerbosityLevel.INFO, f"\n'constraints_list' len: {len(constraints_list)} - all of the remaining packages in the warehouse have been prioritized and added to the constraints_list.")
    if VERBOSITY == 2: print_package_list(constraints_list)
    reporter.report(VerbosityLevel.PROG, "\nPress Enter to continue...")
    if VERBOSITY >= 1: input()


    # Finally, sort based on priority and then by group for easier iteration.
    reporter.report(VerbosityLevel.PROG, "\nSorting based on priority and then by group...")
    load_ready_list = package_handler.group_and_sort_list(constraints_list)
    reporter.report(VerbosityLevel.INFO, f"\n'load_ready_list' - grouped, sorted, and ready for loading onto the trucks!")
    if VERBOSITY == 2: print_group_list(load_ready_list)


    reporter.report(VerbosityLevel.PROG, "\nPress Enter to continue...")
    if VERBOSITY >= 1: input()

    reporter.report(VerbosityLevel.PROG, "\n\n")
    reporter.report(VerbosityLevel.PROG, "-----------------------------------")
    reporter.report(VerbosityLevel.PROG, "        LOADING THE TRUCKS         ")
    reporter.report(VerbosityLevel.PROG, "-----------------------------------")

    # Instantiate PackageLoader object, which contains the methods that manage decision around loading packages into trucks.
    reporter.report(VerbosityLevel.PROG, "\nInstantiating PackageLoader object, which contains the methods that manage decisions around loading packages into trucks...")
    package_loader = PackageLoader()


    # Iterate through the load_ready_list and load any package already assigned to a truck
    reporter.report(VerbosityLevel.PROG, "\nIterating through the 'load_ready_list' and loading any package already assigned to a truck...")
    package_loader.load_assigned_trucks(fleet, load_ready_list, reporter)
    reporter.report(VerbosityLevel.INFO, "\n\n'load_ready_list':")
    if VERBOSITY == 2:
        print_group_list(load_ready_list)
        fleet.print_fleet()


    # Load the highest priority packages to all empty trucks with a driver
    reporter.report(VerbosityLevel.PROG, "\nLoading the highest priority packages to any empty truck with a driver...")
    package_loader.load_empty_trucks_with_drivers(fleet, load_ready_list, reporter, drivers)
    reporter.report(VerbosityLevel.INFO, "\n\n'load_ready_list':")
    if VERBOSITY == 2:
        print_group_list(load_ready_list)
        fleet.print_fleet()


    # Load the trucks that currently have drivers
    reporter.report(VerbosityLevel.PROG, "\nLoading the trucks with drivers first until no packages with deadlines are unloaded...")
    package_loader.load_packages(fleet, load_ready_list, reporter, drivers)
    reporter.report(VerbosityLevel.INFO, "\n\n'load_ready_list':")
    if VERBOSITY == 2:
        print_group_list(load_ready_list)
        fleet.print_fleet()


    # Load the remaining packages onto remaining trucks
    reporter.report(VerbosityLevel.PROG, "\nLoading the remaining packages onto remaining trucks...")
    package_loader.load_packages(fleet, load_ready_list, reporter)
    reporter.report(VerbosityLevel.INFO, "\nThe fleet is loaded and ready for delivery.")
    if VERBOSITY == 2: fleet.print_fleet()


    reporter.report(VerbosityLevel.PROG, "\nPress Enter to continue...")
    if VERBOSITY >= 1: input()

    reporter.report(VerbosityLevel.PROG, "\n\n")
    reporter.report(VerbosityLevel.PROG, "-----------------------------------")
    reporter.report(VerbosityLevel.PROG, "      DELIVERING THE PACKAGES      ")
    reporter.report(VerbosityLevel.PROG, "-----------------------------------")

    # The deliver handler. It delivers the packages, of course.
    delivery_handler = DeliveryHandler()

    # Build the delivery list by generating departure/arrival times of trucks and deliveries of packages and adding them in order of execution
    reporter.report(VerbosityLevel.PROG, "\nBuilding the delivery list by generating a timeline of delivery events and adding them in order of execution...")
    delivery_handler.build_delivery_list(fleet)
    reporter.report(VerbosityLevel.INFO, "\nThe delivery list:\n")
    if VERBOSITY == 2: delivery_handler.print_delivery_list()

    # Deliver the packages.
    print("\nDelivering the packages in accelerated real-time...\n")
    delivery_handler.deliver_packages(fleet)

if __name__ == "__main__":
    read_data(package_list)

    trucks, drivers = 1, 1
    fail_count = 0

    while True:
        reset_warehouse()
        try:
            if fail_count > 0:
                reporter.report(VerbosityLevel.PROG, "\n\n" + "=" * 100)
                reporter.report(VerbosityLevel.PROG, f"    RESTARTING DELIVERY SIMULATION (Attempt #{fail_count})")
                reporter.report(VerbosityLevel.PROG, f"    Fleet: {trucks} truck{'s' if trucks != 1 else ''}, {drivers} driver{'s' if drivers != 1 else ''}")
                reporter.report(VerbosityLevel.PROG, "=" * 100 + "\n")

            run(trucks, drivers)
            break

        except SystemExit:
            fail_count += 1
            if fail_count % 2 == 1:
                trucks += 1
                reporter.report(VerbosityLevel.PROG, f"[retry #{fail_count}] No feasible plan. Increasing trucks → {trucks}, drivers → {drivers}")
            else:
                drivers += 1
                reporter.report(VerbosityLevel.PROG, f"[retry #{fail_count}] No feasible plan. Increasing drivers → {drivers}, trucks → {trucks}")
            continue

#jjg