from django.db import models
from django.utils import timezone
import json


class NewPractoDoctor(models.Model):
    """Model for storing doctor data scraped from Practo with additional fields"""
    id = models.AutoField(primary_key=True)
    location = models.TextField(blank=True)
    doctor_name = models.TextField(blank=True)
    qualification = models.TextField(blank=True)
    specialization = models.TextField(blank=True)
    experience = models.TextField(blank=True)
    verification_label = models.TextField(blank=True)
    rating = models.TextField(blank=True)
    rating_count = models.TextField(blank=True)
    services = models.TextField(blank=True)
    education = models.TextField(blank=True)
    registration = models.TextField(blank=True)
    associated_clinic_data = models.TextField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.doctor_name} - {self.specialization} ({self.location})"
    
    @property
    def clinic_data(self):
        if not self.associated_clinic_data:
            return {}
        try:
            return json.loads(self.associated_clinic_data)
        except:
            return {}
    
    class Meta:
        db_table = 'Cpapp_new_practo_doctor'
        managed = False

    def save(self, *args, **kwargs):
        # Ensure associated_clinic_data is properly serialized as JSON
        if isinstance(self.associated_clinic_data, list):
            self.associated_clinic_data = json.dumps(self.associated_clinic_data)
        super().save(*args, **kwargs)
