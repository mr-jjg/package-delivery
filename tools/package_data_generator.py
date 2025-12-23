import argparse
import csv
from pathlib import Path
import random

class PackageDataGenerator:
    def __init__(self, num_pkgs, pct_constraints, pct_deadlines, dl_lower_band=9, dl_upper_band=16):
        self.packages = [[i, "Address", "", "", "", "EOD", "", "None"] for i in range(num_pkgs)]
        self.address_list = read_address_data('addressCSV.csv')
        self.pct_constraints = pct_constraints / 100.0
        self.pct_deadlines = pct_deadlines / 100.0
        self.dl_lower_band = dl_lower_band
        self.dl_upper_band = dl_upper_band - 1
        
        self.constraints_list = random.sample([pkg[0] for pkg in self.packages], k=int((num_pkgs * self.pct_constraints)))
        self.deadlines_list = random.sample([pkg[0] for pkg in self.packages], k=int((num_pkgs * self.pct_deadlines)))
        self.possible_w_notes = [pkg_id for pkg_id in self.constraints_list if self.packages[pkg_id][7] == "None"]
        
    def assign_random_address(self, pkg):
        address_tup = random.choice(self.address_list)
        pkg[1] = address_tup[2]
        
    def assign_deadline(self, pkg):
        if pkg[0] in self.deadlines_list:
            pkg[5] = self.make_random_time_string(self.dl_lower_band, self.dl_upper_band)
        
    def assign_special_note(self, pkg):
        notes = ["D", "T", "W"]
        if pkg[0] in self.constraints_list:
            note = random.choice(notes)
            if note == "D":
                pkg[7] = f"D, {self.make_random_time_string(self.dl_lower_band, self.dl_upper_band)}"
            elif note == "T":
                pkg[7] = f"T, {random.randint(1, 3)}"
            elif note == "W":
                k_ = random.randint(1, 2)
                chosen_notes = random.sample(self.possible_w_notes, k=k_)
                pkg[7] = f"W, {', '.join(str(note) for note in chosen_notes)}"
                    
    def make_random_time_string(self, lower_band, upper_band):
        rand_hour = random.randint(lower_band, upper_band)
        hour = rand_hour % 12
        minute = random.randint(0, 60)
        time_designation = "AM" if rand_hour < 12 else "PM"
        return f"{hour}:{minute:02} {time_designation}"
        
    def generate_csv_from_list(self, write_list):
        base_dir = Path(__file__).resolve().parents[1]
        file_path = base_dir / "packages.csv"

        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(write_list)

def read_address_data(input):
    address_list = []

    with open(input, 'r') as address_file:
        csv_reader = csv.reader(address_file)
        for row in csv_reader:
            #Unpack
            address_id, city, address = row
            address_entry = [int(address_id), city, address]

            # Store the address data in a list for later indexing
            address_list.append(address_entry)

    return address_list

def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="PackageDataGenerator")

    parser.add_argument("-n", "--num_pkgs", type=int, default = 20, help="Set number of packages in PackageData")
    parser.add_argument("-c", "--constraints", type=int, default = 20, help="Set percentage of packages with constraints")
    parser.add_argument("-d", "--deadlines", type=int, default = 20, help="Set percentage of packages with deadlines")
    parser.add_argument("-l", "--lower_bound", type=int, default = 9, help="Set lower hour bound")
    parser.add_argument("-u", "--upper_bound", type=int, default = 18, help="Set upper hour bound")

    args = parser.parse_args(argv)

    args.num_pkgs = max(20, min(args.num_pkgs, 40))
    args.constraints = max(0, min(args.constraints, 100))
    args.deadlines = max(0, min(args.deadlines, 100))
    args.lower_bound = max(9, min(args.lower_bound, 16))
    args.upper_bound = max(10, min(args.upper_bound, 18))

    return args.num_pkgs, args.constraints, args.deadlines, args.lower_bound, args.upper_bound

def main():
    args = parse_args()
    NUM_PKGS, PCT_CONSTRAINTS, PCT_DEADLINES, DL_LOWER_BOUND, DL_UPPER_BOUND = args

    if DL_LOWER_BOUND > DL_UPPER_BOUND:
        DL_UPPER_BOUND, DL_LOWER_BOUND = DL_LOWER_BOUND, DL_UPPER_BOUND

    gen = PackageDataGenerator(NUM_PKGS, PCT_CONSTRAINTS, PCT_DEADLINES, DL_LOWER_BOUND, DL_UPPER_BOUND)

    write_list = []
    for pkg in gen.packages:
        gen.assign_random_address(pkg)
        gen.assign_deadline(pkg)
        gen.assign_special_note(pkg)
        print(pkg)
        write_list.append(pkg)

    gen.generate_csv_from_list(write_list)

if __name__ == "__main__":
    main()