import os
import django
import sys
import re
from datetime import datetime

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kyb_project.settings')
django.setup()

from cpapp.models import NMCDoctor

def clean_sql_value(value):
    """Clean SQL values by removing quotes, parentheses, and extra spaces"""
    if value == 'NULL':
        return None
    value = value.strip()
    value = value.strip("'")
    value = value.strip(")")
    value = value.strip()
    return value

def parse_sql_values(sql_content):
    """Parse SQL INSERT statement values into a list of records"""
    # Extract the VALUES part
    values_match = re.search(r'VALUES\s*\((.*)\)', sql_content, re.DOTALL)
    if not values_match:
        return []
    
    values_str = values_match.group(1)
    records = []
    current_record = []
    current_value = ''
    in_quotes = False
    in_address = False
    
    for char in values_str:
        if char == "'" and not in_quotes:
            in_quotes = True
        elif char == "'" and in_quotes:
            in_quotes = False
        elif char == ',' and not in_quotes and not in_address:
            current_record.append(clean_sql_value(current_value))
            current_value = ''
        elif char == ')' and not in_quotes and not in_address:
            current_record.append(clean_sql_value(current_value))
            records.append(current_record)
            current_record = []
            current_value = ''
        else:
            current_value += char
            # If we're in the address field (last field), keep accumulating
            if len(current_record) >= 14:  # Address is the 15th field
                in_address = True
    
    return records

def convert_sql_to_data(sql_content):
    records = parse_sql_values(sql_content)
    data = []
    
    for values in records:
        try:
            # Ensure we have all required fields
            if len(values) < 16:
                print(f"Skipping record with insufficient fields: {values}")
                continue
                
            record_dict = {
                'year_info': int(values[0]) if values[0] is not None else None,
                'doctor_id': int(values[1]) if values[1] is not None else None,
                'first_name': values[2],
                'middle_name': values[3],
                'last_name': values[4],
                'phone_no': values[5],
                'email_id': values[6],
                'gender': values[7],
                'birth_date': values[8],
                'doctor_degree': values[9],
                'university': values[10],
                'year_of_passing': int(values[11]) if values[11] is not None else None,
                'smc_name': values[12],
                'registration_no': values[13],
                'address': values[14],  # Address field can contain commas
                'smc_id': int(values[15]) if values[15] is not None else None
            }
            data.append(record_dict)
        except (ValueError, IndexError) as e:
            print(f"Error processing record: {values}")
            print(f"Error details: {str(e)}")
            continue
    
    return data

def clean_value(value):
    """Clean string values by removing extra spaces and handling NULL values"""
    if value is None or value == 'NULL':
        return None
    if isinstance(value, str):
        return value.strip()
    return value

def import_nmc_data():
    # Read the SQL file
    with open('nmc_migration.sql', 'r') as f:
        sql_content = f.read()
    
    # Convert SQL to data
    data = convert_sql_to_data(sql_content)
    
    # Process each record
    for record in data:
        try:
            # Clean all values
            cleaned_record = {k: clean_value(v) for k, v in record.items()}
            
            # Create or update the record
            NMCDoctor.objects.update_or_create(
                doctor_id=cleaned_record['doctor_id'],
                defaults=cleaned_record
            )
            print(f"Successfully imported record for doctor_id: {cleaned_record['doctor_id']}")
            
        except Exception as e:
            print(f"Error importing record {record}: {str(e)}")

if __name__ == "__main__":
    print("Starting NMC data import...")
    import_nmc_data()
    print("Import completed!") 