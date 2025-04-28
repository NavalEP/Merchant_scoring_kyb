from django.db import models
from django.utils import timezone


class BajajDoctor(models.Model):
    """Model for storing doctor data from Bajaj"""
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(default=timezone.now)
    name = models.TextField(null=True, blank=True)
    photo = models.TextField(null=True, blank=True)
    doctor_introduction = models.TextField(null=True, blank=True)
    specialities = models.TextField(null=True, blank=True)
    fees = models.TextField(null=True, blank=True)
    fee_range = models.TextField(null=True, blank=True)
    experience = models.TextField(null=True, blank=True)
    clinic_name = models.TextField(null=True, blank=True)
    clinic_address = models.TextField(null=True, blank=True)
    clinic_city = models.TextField(null=True, blank=True)
    clinic_location = models.TextField(null=True, blank=True)
    qualifications = models.TextField(null=True, blank=True)
    rating_percent = models.TextField(null=True, blank=True)
    rating_count = models.TextField(null=True, blank=True)
    hpr_id = models.TextField(null=True, blank=True)
    gender = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.specialities}"
    
    class Meta:
        db_table = 'Cpapp_bajaj_doctor'
        managed = False
