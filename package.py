from datetime import time, datetime

class Package:
    EOD_TIME = time(23, 59)
    
    def __init__(self, 
                 package_id,
                 address, 
                 city, 
                 state, 
                 zip_code, 
                 delivery_deadline, 
                 weight_kilo, 
                 special_note, 
                 delivery_status='at_the_hub', 
                 time_of_delivery = None,
                 truck=None,
                 group=None,
                 priority=None):
        self.package_id = package_id
        self.address = address
        self.address_history = [(None, address)]
        self.city = city
        self.state = state
        self.zip_code = zip_code
        self.delivery_deadline = self.parse_delivery_deadline(delivery_deadline) if isinstance(delivery_deadline, str) else delivery_deadline
        self.weight_kilo = weight_kilo
        self.special_note = special_note
        self.delivery_status = delivery_status
        self.time_of_delivery = None
        self.truck = truck
        self.group = group
        self.priority = priority
        
    
    def __str__(self):
        # Handling parsed list of special notes:
        # If special_note is a list, and there is a note:
        if self.special_note and self.special_note[0] == 'X':
            special_note_str = 'X'
        elif isinstance(self.special_note, list) and self.special_note:
            # Cast each note in list as string and join to special_note_str separated with commas
            special_note_str = ', '.join(str(note) for note in self.special_note)
        else:
            # Otherwise, it is not a list or is empty.
            special_note_str = 'None'
            
        delivery_deadline_str = self.get_deadline_str()
        time_of_delivery_str = self.get_time_str(self.time_of_delivery)
        
        return (
            f"Package ID: {self.package_id:<5}" # DEBUG ONLY
            f"Address: {self.address:<40}"
            #f"City: {self.city:<20}"
            #f"State: {self.state:<4}" # DEBUG ONLY
            #f"Zip Code: {self.zip_code:<7}"
            f"Delivery Deadline: {delivery_deadline_str:<10}"
            #f"Weight (kg): {self.weight_kilo:<5}"
            f"Special Note: {special_note_str:<15}" # DEBUG ONLY
            f"Delivery Status: {self.delivery_status or 'None':<12}"
            f"Delivery Time: {time_of_delivery_str or 'None':<11}"
            f"Truck: {self.truck + 1 if self.truck is not None else 'None':<6}" # DEBUG ONLY
            f"Group: {self.group if self.group is not None else 'None':<6}" # DEBUG ONLY
            f"Priority: {self.priority if self.priority is not None else 'None':<6}" # DEBUG ONLY Falsy 0 on priority had me stumped for a while. This logic was more or less copied to the Truck and Group fields.
            )
        
    
    # Adding magic method so that packages can be compared by package_id
    def __lt__(self, other):
        return self.package_id < other.package_id
        
    
    def parse_delivery_deadline(self, deadline_str):
        #print(f"{deadline_str} is a {type(deadline_str)}")
        if deadline_str is None or deadline_str == '' or deadline_str == 'None':
            return None
        elif deadline_str == 'EOD':
            return time(23, 59)
        else:
            datetime_obj = datetime.strptime(deadline_str, "%I:%M %p")
            time_obj = time(datetime_obj.hour, datetime_obj.minute)
            #print(f"This is the time object being returned by parse_delivery_deadline: {time_obj}")
            return time_obj
        
    def parse_delayed_package(self, delayed_str):
        if delayed_str is None or delayed_str == '' or delayed_str == 'None':
            return None
        else:
            datetime_obj = datetime.strptime(delayed_str, "%I:%M %p")
            time_obj = time(datetime_obj.hour, datetime_obj.minute)
            return time_obj
    
    # Helper function that parses and cleans specialnote and returns as cleaned list:
    def parse_special_note(self):
        if self.special_note is None:
            return None
        
        parsed_note = self.special_note.split(",")
        #print(f"parsing {self.special_note} as parsed_note: {parsed_note} ", end='') # DEBUG ONLY
        
        cleaned_parsed_note = [self.try_casting_to_int(note.strip()) for note in parsed_note]
        #print(f"and cleaning as cleaned_parsed_note: {cleaned_parsed_note}") # DEBUG ONLY
        
        # Per project specifications, there is a package with an incorrect address. The correct address is unknown, but the time of delivery is known and needs to be parsed as a time object. Also, if the special note is 'D' for delayed, parse as a time object
        if cleaned_parsed_note[0] == 'D' or cleaned_parsed_note[0] == 'X':
            #print(f"Passing to parse_delayed_package: {cleaned_parsed_note[1]} type: {type(cleaned_parsed_note[1])}")
            time_object = self.parse_delayed_package(cleaned_parsed_note[1])
            cleaned_parsed_note[1] = time_object
        
        self.special_note = cleaned_parsed_note
        return cleaned_parsed_note
        
    def get_special_note_str(self):
        if not self.special_note:
            return 'None'
        return ', '.join(
            note.strftime("%I:%M %p") if isinstance(note, time) else str(note)
            for note in self.special_note
        )
    
    
    def get_deadline_str(self):
        if self.delivery_deadline is None:
            return 'None'
        elif self.delivery_deadline == Package.EOD_TIME:
            return 'EOD'
        elif isinstance(self.delivery_deadline, time):
            return self.delivery_deadline.strftime("%I:%M %p")
        else:
            return str(self.delivery_deadline)
        
    
    def get_time_str(self, time_object):
        if time_object is None:
            return 'None'
        else:
            return time_object.strftime("%I:%M %p")
        
    
    # Helper function that safely casts a value to int
    def try_casting_to_int(self, value):
        try:
            return int(value)
        except ValueError:
            return value
        
    

# Helper function that prints a list of packages
def print_package_list(package_list):
    
    headers = ["ID", "Address", "City", "State", "Zip", "Deadline", "Weight", "Note", "Status", "Delivery Time", "Truck", "Group", "Priority"]
    # Initialize max widths with header lengths
    col_widths = [len(header) for header in headers]
    rows = []
    
    for package in package_list:
        row = [
            str(package.package_id),
            package.address,
            package.city,
            package.state,
            package.zip_code,
            package.delivery_deadline.strftime("%I:%M %p") if hasattr(package.delivery_deadline, 'strftime') else str(package.delivery_deadline),
            str(package.weight_kilo),
            package.get_special_note_str(),
            package.delivery_status,
            package.time_of_delivery.strftime("%I:%M %p") if hasattr(package, 'time_of_delivery') and package.time_of_delivery else "None",
            str(package.truck) if package.truck is not None else "None",
            str(package.group) if package.group is not None else "None",
            str(package.priority) if package.priority is not None else "None"
        ]
        rows.append(row)
        # Update column widths based on string length
        for i, val in enumerate(row):
            if val is None:
                print(f"Value at index {i} is None: {headers[i]}")
            val_str = str(val)
            if len(val_str) > col_widths[i]:
                col_widths[i] = len(val_str)
            
    # Build format string for aligned columns
    format_str = ' | '.join(f"{{:<{w}}}" for w in col_widths)
    
    # Print header
    print(format_str.format(*headers))
    print('-' * (sum(col_widths) + 3 * (len(headers) - 1)))
    
    # Print each package row
    for row in rows:
        print(format_str.format(*row))
    

# Helper function that prints a list of groups
def print_group_list(group_list):
    #print("\n\nprint_group_list function:") # DEBUG ONLY
    total_length = sum(len(group) for group in group_list)
    print(f"\nSum of all groups: {total_length}")
    for i, group in enumerate(group_list):
        print(f"Group {i} | Size {len(group)}")
        print_package_list(group)
#jjg