from django.core.management.base import BaseCommand
from cpapp.models.nmc import NMCDoctor
import csv
from datetime import datetime
from django.utils.timezone import make_aware

class Command(BaseCommand):
    help = 'Imports NMC doctors from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')
        parser.add_argument('--dry-run', action='store_true', help='Test without saving to DB')

    def handle(self, *args, **kwargs):
        csv_path = kwargs['csv_file']
        dry_run = kwargs['dry_run']
        
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as csvfile:
                # Read sample and detect format
                sample = csvfile.read(2048)
                csvfile.seek(0)
                
                try:
                    dialect = csv.Sniffer().sniff(sample)
                except csv.Error:
                    # Fallback to Excel dialect if sniffing fails
                    dialect = csv.excel()
                
                # Skip initial blank lines
                reader = csv.DictReader((line for line in csvfile if line.strip()), dialect=dialect)
                
                if not reader.fieldnames:
                    self.stderr.write("ERROR: CSV file must contain headers in the first row")
                    self.stdout.write("Please check your CSV file format and encoding")
                    return

                self.stdout.write(f"CSV headers detected: {', '.join(reader.fieldnames)}")
                
                for row in reader:
                    # Skip empty rows
                    if not any(row.values()):
                        continue
                    
                    # Normalize column names with null check
                    row = {self.normalize_header(k): v for k, v in row.items() if k is not None}
                    
                    try:
                        doctor_id = row.get('doctor_id') or row.get('doctorid') or row.get('dr_id')
                        doctor, created = NMCDoctor.objects.get_or_create(
                            doctor_id=doctor_id,
                            defaults={
                                'year_info': row.get('year_info'),
                                'first_name': row.get('first_name', ''),
                                'middle_name': row.get('middle_name'),
                                'last_name': row.get('last_name'),
                                'phone_no': row.get('phone_no'),
                                'email_id': row.get('email_id'),
                                'gender': row.get('gender'),
                                'birth_date': self.parse_date(row.get('birth_date')),
                                'doctor_degree': row.get('doctor_degree', ''),
                                'university': row.get('university', ''),
                                'year_of_passing': row.get('year_of_passing'),
                                'smc_name': row.get('smc_name', ''),
                                'registration_no': row.get('registration_no', ''),
                                'address': row.get('address', ''),
                                'smc_id': row.get('smc_id'),
                            }
                        )
                        
                        if created and not dry_run:
                            self.stdout.write(f'Created doctor ID {doctor.doctor_id}')
                        elif dry_run:
                            self.stdout.write(f'[Dry-run] Would create doctor ID {row["doctor_id"]}')
                    except KeyError as e:
                        self.stderr.write(f"ERROR: Missing required column - {str(e)}")
                        self.stdout.write(f"Available columns: {', '.join(row.keys())}")
                        self.stdout.write("Please map these to your model fields or modify the CSV headers")
                        break
        except FileNotFoundError:
            self.stderr.write(f"Error: File {csv_path} not found")
        except csv.Error as e:
            self.stderr.write(f"CSV Error: {str(e)}")

    def parse_date(self, date_str):
        if not date_str:
            return None
        try:
            return make_aware(datetime.strptime(date_str, '%Y-%m-%d'))  # Adjust format as needed
        except ValueError:
            return None

    def normalize_header(self, header):
        """Convert camelCase to snake_case and lowercase"""
        return ''.join(
            ['_'+c.lower() if c.isupper() else c for c in header]
        ).lstrip('_').lower() 