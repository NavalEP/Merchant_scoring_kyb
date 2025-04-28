import csv
import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from cpapp.models import JustDialClinic


class Command(BaseCommand):
    help = 'Import JustDial clinics data from CSV file into kyb_db database'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit the number of clinics to import (for testing)'
        )

    def clean_value(self, value):
        """Clean individual field values"""
        if value in ['Not available', 'None', '', 'not available']:
            return ''
        return value.strip()

    def parse_datetime(self, value):
        """Parse datetime from string"""
        if not value or value in ['Not available', 'None', '', 'not available']:
            return None
        try:
            # Assuming format is YYYYMMDD_HHMMSS
            return datetime.datetime.strptime(value, '%Y%m%d_%H%M%S')
        except ValueError:
            return None

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        limit = options['limit']
        
        self.stdout.write(self.style.SUCCESS(f'Starting import from {csv_file}'))
        self.stdout.write(self.style.SUCCESS(f'Using database: kyb_db'))
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                clinics_created = 0
                clinics_updated = 0
                
                for row in reader:
                    # Check if we've reached the limit
                    if limit and (clinics_created + clinics_updated) >= limit:
                        self.stdout.write(
                            self.style.SUCCESS(f'Reached import limit of {limit} clinics')
                        )
                        break
                    
                    try:
                        # Clean the data
                        cleaned_data = {
                            'location': self.clean_value(row['location']),
                            'category': self.clean_value(row['category']),
                            'name': self.clean_value(row['name']),
                            'rating': self.clean_value(row['rating']),
                            'rating_count': self.clean_value(row['rating_count']),
                            'address': self.clean_value(row['address']),
                            'phone_number': self.clean_value(row['phone_number']),
                            'scraped_at': self.parse_datetime(row['scraped_at']),
                            'associated_doctors': self.clean_value(row['associated_doctors'])
                        }

                        # Try to find existing clinic or create new one
                        clinic, created = JustDialClinic.objects.update_or_create(
                            name=cleaned_data['name'],
                            location=cleaned_data['location'],
                            category=cleaned_data['category'],
                            defaults=cleaned_data
                        )
                        
                        if created:
                            clinics_created += 1
                            if clinics_created % 10 == 0:  # Progress update every 10 clinics
                                self.stdout.write(f'Created {clinics_created} new clinics...')
                        else:
                            clinics_updated += 1
                            
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f'Warning processing clinic {row.get("name", "Unknown")}: {str(e)}')
                        )
                        continue  # Continue with next record instead of stopping
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\nImport completed:\n'
                        f'- New clinics created: {clinics_created}\n'
                        f'- Existing clinics updated: {clinics_updated}\n'
                        f'- Total processed: {clinics_created + clinics_updated}'
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