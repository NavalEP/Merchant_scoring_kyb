from django.db import models
from django.utils import timezone


class NMCDoctor(models.Model):
    """Model for storing doctor data from the National Medical Commission (NMC)"""
    yearInfo = models.IntegerField(null=True, blank=True)
    doctorId = models.IntegerField(unique=True)
    firstName = models.CharField(max_length=255, blank=True, null=True)
    middleName = models.CharField(max_length=255, blank=True, null=True)
    lastName = models.CharField(max_length=255, blank=True, null=True)
    phoneNo = models.CharField(max_length=50, blank=True, null=True)
    emailId = models.EmailField(blank=True, null=True)
    gender = models.CharField(max_length=20, blank=True, null=True)
    birthDate = models.DateField(null=True, blank=True)
    doctorDegree = models.CharField(max_length=100, blank=True, null=True)
    university = models.CharField(max_length=255, blank=True, null=True)
    yearOfPassing = models.IntegerField(null=True, blank=True)
    smcName = models.CharField(max_length=255, blank=True, null=True)
    registrationNo = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    smcId = models.IntegerField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
   
    
    def __str__(self):
        return f"{self.firstName} - {self.doctorDegree} ({self.registrationNo})"
    
    class Meta:
        db_table = 'Cpapp_nmc_doctor' 
        managed = False