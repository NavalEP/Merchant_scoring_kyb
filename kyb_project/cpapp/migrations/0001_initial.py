# Generated by Django 5.1.7 on 2025-04-20 22:00

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='NMCDoctor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('yearinfo', models.IntegerField(blank=True, null=True)),
                ('doctorid', models.IntegerField(unique=True)),
                ('firstName', models.CharField(blank=True, max_length=255, null=True)),
                ('middleName', models.CharField(blank=True, max_length=255, null=True)),
                ('lastName', models.CharField(blank=True, max_length=255, null=True)),
                ('phoneNo', models.CharField(blank=True, max_length=50, null=True)),
                ('emailId', models.EmailField(blank=True, max_length=254, null=True)),
                ('gender', models.CharField(blank=True, max_length=20, null=True)),
                ('birthDate', models.DateField(blank=True, null=True)),
                ('doctorDegree', models.CharField(blank=True, max_length=100, null=True)),
                ('university', models.CharField(blank=True, max_length=255, null=True)),
                ('yearOfPassing', models.IntegerField(blank=True, null=True)),
                ('smcName', models.CharField(blank=True, max_length=255, null=True)),
                ('registrationNo', models.CharField(blank=True, max_length=50, null=True)),
                ('address', models.TextField(blank=True, null=True)),
                ('smcId', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'verbose_name': 'NMC Doctor',
                'verbose_name_plural': 'NMC Doctors',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='JustDialClinic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location', models.CharField(max_length=255)),
                ('category', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('rating', models.CharField(blank=True, max_length=50)),
                ('rating_count', models.CharField(blank=True, max_length=50)),
                ('address', models.TextField(blank=True)),
                ('phone_number', models.CharField(blank=True, max_length=100)),
                ('scraped_at', models.DateTimeField(blank=True, null=True)),
                ('associated_doctors', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'verbose_name': 'JustDial Clinic',
                'verbose_name_plural': 'JustDial Clinics',
                'ordering': ['-created_at'],
                'unique_together': {('name', 'location', 'category')},
            },
        ),
        migrations.CreateModel(
            name='JustDialDoctor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location', models.CharField(max_length=255)),
                ('category', models.CharField(max_length=255)),
                ('doctor_name', models.CharField(max_length=255)),
                ('rating', models.CharField(blank=True, max_length=50)),
                ('rating_count', models.CharField(blank=True, max_length=50)),
                ('experience', models.CharField(blank=True, max_length=100)),
                ('consultation_fee', models.CharField(blank=True, max_length=100)),
                ('clinic_address', models.TextField(blank=True)),
                ('specialization', models.TextField(blank=True)),
                ('registration', models.CharField(blank=True, max_length=255)),
                ('qualification', models.TextField(blank=True)),
                ('phone_number', models.CharField(blank=True, max_length=100)),
                ('detail_url', models.URLField(blank=True, max_length=1000)),
                ('clinic_name', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'verbose_name': 'JustDial Doctor',
                'verbose_name_plural': 'JustDial Doctors',
                'ordering': ['-created_at'],
                'unique_together': {('doctor_name', 'location', 'category', 'clinic_address')},
            },
        ),
        migrations.CreateModel(
            name='PractoDoctor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('speciality', models.CharField(max_length=255)),
                ('location', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('experience', models.CharField(blank=True, max_length=100)),
                ('clinic_name', models.CharField(blank=True, max_length=255)),
                ('doctor_address', models.TextField(blank=True)),
                ('consultation_fee', models.CharField(blank=True, max_length=100)),
                ('recommendation_percent', models.CharField(blank=True, max_length=50)),
                ('patient_stories', models.CharField(blank=True, max_length=50)),
                ('doctor_url', models.TextField(blank=True)),
                ('detailed_qualifications', models.TextField(blank=True)),
                ('contact_number', models.CharField(blank=True, max_length=50)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'verbose_name': 'Practo Doctor',
                'verbose_name_plural': 'Practo Doctors',
                'ordering': ['-created_at'],
                'unique_together': {('name', 'doctor_url')},
            },
        ),
    ]
