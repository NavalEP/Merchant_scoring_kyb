from django.db import models
from django.utils import timezone


class JustDialClinic(models.Model):
    """Model for storing clinic data scraped from JustDial"""
    location = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    rating = models.CharField(max_length=50, blank=True)
    rating_count = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    phone_number = models.CharField(max_length=100, blank=True)
    scraped_at = models.DateTimeField(blank=True, null=True)
    associated_doctors = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.name} - {self.category} ({self.location})"
    
    class Meta:
        db_table = 'Cpapp_justdial_clinic' 
        managed = False


class JustDialDoctor(models.Model):
    """Model for storing doctor data scraped from JustDial"""
    location = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    doctor_name = models.CharField(max_length=255)
    rating = models.CharField(max_length=50, blank=True)
    rating_count = models.CharField(max_length=50, blank=True)
    experience = models.CharField(max_length=100, blank=True)
    consultation_fee = models.CharField(max_length=100, blank=True)
    clinic_address = models.TextField(blank=True)
    specialization = models.TextField(blank=True)
    registration = models.CharField(max_length=255, blank=True)
    qualification = models.TextField(blank=True)
    phone_number = models.CharField(max_length=100, blank=True)
    detail_url = models.URLField(max_length=1000, blank=True)
    clinic_name = models.CharField(max_length=255, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.doctor_name} - {self.category} ({self.location})"
    
    class Meta:
        db_table = 'Cpapp_justdial_doctor' 
        managed = False
