import csv
import re

# Input and output paths
sql_file_path = 'nmc_migration.sql'
csv_file_path = 'nmc_doctors.csv'

# Define CSV headers (in the correct column order from your SQL insert)
headers = [
    'yearInfo', 'doctorId', 'firstName', 'middleName', 'lastName',
    'phoneNo', 'emailId', 'gender', 'birthDate', 'doctorDegree',
    'university', 'yearOfPassing', 'smcName', 'registrationNo', 'address', 'smcId'
]

# Regex to match each value set inside the VALUES (...), (...), ...
pattern = re.compile(r'\((.*?)\),?', re.DOTALL)

def parse_sql_values(value_str):
    # Split the fields respecting commas inside quotes
    fields = []
    current = ''
    in_quote = False

    for char in value_str:
        if char == "'" and not in_quote:
            in_quote = True
            current += char
        elif char == "'" and in_quote:
            in_quote = False
            current += char
        elif char == ',' and not in_quote:
            fields.append(current.strip())
            current = ''
        else:
            current += char

    if current:
        fields.append(current.strip())

    # Clean each field
    cleaned_fields = []
    for field in fields:
        if field.upper() == 'NULL':
            cleaned_fields.append('')
        elif field.startswith("'") and field.endswith("'"):
            cleaned_fields.append(field[1:-1].replace("''", "'").strip())
        else:
            cleaned_fields.append(field)

    return cleaned_fields

with open(sql_file_path, 'r', encoding='utf-8') as sql_file, open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(headers)

    content = sql_file.read()

    # Extract all value tuples from the SQL
    values = pattern.findall(content)

    for value_str in values:
        row = parse_sql_values(value_str)
        writer.writerow(row)

print(f"✅ CSV created successfully at {csv_file_path}")
