from django.contrib import admin

from cpapp.models.justdial import JustDialDoctor



@admin.register(JustDialDoctor)
class JustDialDoctorAdmin(admin.ModelAdmin):
    list_display = ('doctor_name', 'location', 'category', 'rating', 'experience', 'clinic_name')
    list_filter = ('location', 'category')
    search_fields = ('doctor_name', 'clinic_name', 'clinic_address', 'specialization')
    ordering = ('-created_at',)
