import csv
import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from cpapp.models import JustDialDoctor


class Command(BaseCommand):
    help = 'Import JustDial doctors data from CSV file into database'

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
        if value in ['Not available', 'None', '', 'not available', 'Show Number']:
            return ''
        return value.strip()

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        limit = options['limit']
        
        self.stdout.write(self.style.SUCCESS(f'Starting import from {csv_file}'))
        
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as file:
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
                        # Required: location and category must be first two fields in DB
                        # Check if they exist in the CSV
                        if 'location' not in row or 'category' not in row:
                            self.stdout.write(
                                self.style.WARNING(f'CSV missing required fields "location" and/or "category"')
                            )
                            break
                        
                        # Clean the data
                        cleaned_data = {
                            'location': self.clean_value(row['location']),
                            'category': self.clean_value(row['category']),
                            'doctor_name': self.clean_value(row['doctor_name']),
                            'rating': self.clean_value(row['rating']),
                            'rating_count': self.clean_value(row['rating_count']),
                            'experience': self.clean_value(row['experience']),
                            'consultation_fee': self.clean_value(row['consultation_fee']),
                            'clinic_address': self.clean_value(row['clinic_address']),
                            'specialization': self.clean_value(row['specialization']),
                            'registration': self.clean_value(row['registration']),
                            'qualification': self.clean_value(row['qualification']),
                            'phone_number': self.clean_value(row['phone_number']),
                            'detail_url': self.clean_value(row['detail_url']),
                            'clinic_name': self.clean_value(row['clinic_name']),
                        }

                        # Try to find existing doctor or create new one
                        doctor, created = JustDialDoctor.objects.update_or_create(
                            doctor_name=cleaned_data['doctor_name'],
                            location=cleaned_data['location'],
                            category=cleaned_data['category'],
                            clinic_address=cleaned_data['clinic_address'],
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
                            self.style.WARNING(f'Warning processing doctor {row.get("doctor_name", "Unknown")}: {str(e)}')
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