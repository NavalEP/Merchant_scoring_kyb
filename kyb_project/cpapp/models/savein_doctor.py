from django.db import models

class SaveinDoctor(models.Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.TextField(null=True)
    rating = models.TextField(null=True)
    reviews_count = models.TextField(null=True)
    experience = models.TextField(null=True)
    location = models.TextField(null=True)
    doctor_name = models.TextField(null=True)
    qualification = models.TextField(null=True)
    consultation_fee = models.TextField(null=True)
    specialization = models.TextField(null=True)
    address = models.TextField(null=True)
    price_category = models.TextField(null=True)
    services = models.TextField(null=True)
    scrape_timestamp = models.TextField(null=True)
    
    def __str__(self):
        return self.name or self.doctor_name or str(self.id)
    
    class Meta:
        db_table = "Cpapp_savein_doctor"
        managed = False
