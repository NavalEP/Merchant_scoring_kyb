from django.db import models
from django.utils import timezone


class PractoDoctor(models.Model):
    """Model for storing doctor data scraped from Practo"""
    speciality = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    experience = models.CharField(max_length=100, blank=True)
    clinic_name = models.CharField(max_length=255, blank=True)
    doctor_address = models.TextField(blank=True)
    consultation_fee = models.CharField(max_length=100, blank=True)
    recommendation_percent = models.CharField(max_length=50, blank=True)
    patient_stories = models.CharField(max_length=50, blank=True)
    doctor_url = models.TextField(blank=True)
    detailed_qualifications = models.TextField(blank=True)
    contact_number = models.CharField(max_length=50, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.name} - {self.speciality} ({self.location})"
    
    class Meta:
        db_table = 'Cpapp_practo_doctor' 
        managed = False
