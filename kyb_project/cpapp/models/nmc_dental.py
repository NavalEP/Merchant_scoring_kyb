from django.db import models
from django.utils import timezone


class NMCDentalDoctor(models.Model):
    """Model for storing dental doctor data from the National Medical Commission (NMC)"""
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(default=timezone.now)
    full_name = models.TextField(blank=True, null=True)
    state_medical_council = models.TextField(blank=True, null=True)
    father_husband_name = models.TextField(blank=True, null=True)
    date_of_birth = models.TextField(blank=True, null=True)
    qualification = models.TextField(blank=True, null=True)
    qualification_year = models.TextField(blank=True, null=True)
    university_name = models.TextField(blank=True, null=True)
    registration_number = models.TextField(blank=True, null=True)
    registration_year = models.TextField(blank=True, null=True)
    nmr_id = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.full_name} - {self.qualification} ({self.registration_number})"
    
    class Meta:
        db_table = 'Cpapp_nmc_dental_doctor'
        managed = False
