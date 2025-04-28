import csv
import re
from io import StringIO

# Input SQL file
sql_file_path = 'nmc_migration.sql' 
# Output CSV files
csv_file_path_1 = 'output_1.csv'
csv_file_path_2 = 'output_2.csv'

# Define headers
headers = [
    'yearInfo', 'doctorId', 'firstName', 'middleName', 'lastName',
    'phoneNo', 'emailId', 'gender', 'birthDate', 'doctorDegree',
    'university', 'yearOfPassing', 'smcName', 'registrationNo', 'address', 'smcId'
]

def parse_sql_values(value_str):
    temp_quote = "__QUOTE__"
    value_str = value_str.replace("''", temp_quote)
    fake_file = StringIO(value_str)
    reader = csv.reader(fake_file, delimiter=',', quotechar="'", skipinitialspace=True)
    try:
        fields = next(reader)
    except Exception:
        return None
    cleaned = []
    for field in fields:
        field = field.strip()
        if field.upper() == 'NULL':
            cleaned.append('')
        else:
            field = field.replace(temp_quote, "'")
            cleaned.append(field)
    return cleaned

# Read and extract rows
with open(sql_file_path, 'r', encoding='utf-8') as sql_file:
    content = re.sub(r'\s+', ' ', sql_file.read())

insert_pattern = re.compile(r'INSERT\s+INTO\s+\w+\s*\([^)]+\)\s*VALUES\s*(.*?);', re.IGNORECASE)
all_rows = []

for match in insert_pattern.finditer(content):
    values_block = match.group(1)
    value_groups = re.findall(r'\((.*?)\)(?:,|$)', values_block)
    for value_str in value_groups:
        row = parse_sql_values(value_str)
        if row and len(row) == len(headers):
            all_rows.append(row)

# Split and write to CSV
split_index = len(all_rows) // 2
rows_part1 = all_rows[:split_index]
rows_part2 = all_rows[split_index:]

with open(csv_file_path_1, 'w', newline='', encoding='utf-8') as f1:
    writer1 = csv.writer(f1)
    writer1.writerow(headers)
    writer1.writerows(rows_part1)

with open(csv_file_path_2, 'w', newline='', encoding='utf-8') as f2:
    writer2 = csv.writer(f2)
    writer2.writerow(headers)
    writer2.writerows(rows_part2)

print(f"✅ Done! Files created: {csv_file_path_1} and {csv_file_path_2}")
