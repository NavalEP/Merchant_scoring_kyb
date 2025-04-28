import csv
from django.core.management.base import BaseCommand
from django.utils import timezone
from cpapp.models import PractoDoctor

class Command(BaseCommand):
    help = 'Import Practo doctors data from CSV file into kyb_db database'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit the number of doctors to import (for testing)'
        )

    def clean_value(self, value):
        """Clean individual field values"""
        if value in ['Not available', 'None', '', 'not available']:
            return ''
        return value.strip()

    def clean_numeric(self, value):
        """Clean numeric values (consultation fee, recommendation percent)"""
        if value in ['Not available', 'None', '', 'not available']:
            return ''
        # Remove currency symbols, percentages and spaces
        value = value.replace('₹', '').replace('%', '').strip()
        return value

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        limit = options['limit']
        
        self.stdout.write(self.style.SUCCESS(f'Starting import from {csv_file}'))
        self.stdout.write(self.style.SUCCESS(f'Using database: kyb_db'))
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                doctors_created = 0
                doctors_updated = 0
                
                for row in reader:
                    # Check if we've reached the limit
                    if limit and (doctors_created + doctors_updated) >= limit:
                        self.stdout.write(
                            self.style.SUCCESS(f'Reached import limit of {limit} doctors')
                        )
                        break
                    
                    try:
                        # Clean the data
                        cleaned_data = {
                            'name': self.clean_value(row['name']),
                            'speciality': self.clean_value(row['speciality']),
                            'location': self.clean_value(row['location']),
                            'experience': self.clean_value(row['experience']),
                            'clinic_name': self.clean_value(row['clinic_name']),
                            'doctor_address': self.clean_value(row['doctor_address']),
                            'consultation_fee': self.clean_numeric(row['consultation_fee']),
                            'recommendation_percent': self.clean_numeric(row['recommendation_percent']),
                            'patient_stories': self.clean_value(row['patient_stories']),
                            'doctor_url': self.clean_value(row['doctor_url']),
                            'detailed_qualifications': self.clean_value(row.get('detailed_qualifications', '')),
                            'contact_number': self.clean_value(row['contact_number'])
                        }

                        # Try to find existing doctor or create new one
                        doctor, created = PractoDoctor.objects.update_or_create(
                            name=cleaned_data['name'],
                            doctor_url=cleaned_data['doctor_url'],
                            defaults=cleaned_data
                        )
                        
                        if created:
                            doctors_created += 1
                            if doctors_created % 10 == 0:  # Progress update every 10 doctors
                                self.stdout.write(f'Created {doctors_created} new doctors...')
                        else:
                            doctors_updated += 1
                            
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f'Warning processing doctor {row.get("name", "Unknown")}: {str(e)}')
                        )
                        continue  # Continue with next record instead of stopping
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\nImport completed:\n'
                        f'- New doctors created: {doctors_created}\n'
                        f'- Existing doctors updated: {doctors_updated}\n'
                        f'- Total processed: {doctors_created + doctors_updated}'
                    )
                )
                
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'CSV file not found: {csv_file}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during import: {str(e)}')
            ) 