from rest_framework import serializers
from cpapp.models.practo import PractoDoctor
from cpapp.models.justdial import JustDialDoctor, JustDialClinic
from cpapp.models.nmc import NMCDoctor
from cpapp.models.nmc_dental import NMCDentalDoctor


class DoctorSearchSerializer(serializers.Serializer):
    """Serializer for doctor search results"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    source = serializers.CharField()
    speciality = serializers.CharField(required=False, allow_blank=True, default="")
    location = serializers.CharField()
    experience = serializers.CharField(required=False, allow_blank=True)
    qualification = serializers.CharField(required=False, allow_blank=True)
    rating = serializers.CharField(required=False, allow_blank=True)
    rating_count = serializers.CharField(required=False, allow_blank=True)
    education = serializers.CharField(required=False, allow_blank=True)
    registration = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    services = serializers.CharField(required=False, allow_blank=True)
    
    
class ClinicSearchSerializer(serializers.Serializer):
    """Serializer for clinic search results"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    source = serializers.CharField()
    category = serializers.CharField()
    location = serializers.CharField()
    rating = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    type = serializers.CharField(required=False, allow_blank=True)
    rating_count = serializers.CharField(required=False, allow_blank=True)
    verified = serializers.CharField(required=False, allow_blank=True)
    

class ScoreRequestSerializer(serializers.Serializer):
    """Serializer for score requests"""
    entity_type = serializers.ChoiceField(choices=['doctor', 'clinic'])
    entity_id = serializers.IntegerField()
    source = serializers.ChoiceField(choices=['practo', 'justdial', 'nmc', 'nmc_dental', 'googlemap', 'bajaj', 'savein', 'new_practo'])


class ScoreResponseSerializer(serializers.Serializer):
    """Serializer for score responses"""
    entity_type = serializers.CharField()
    entity_id = serializers.IntegerField()
    source = serializers.CharField()
    name = serializers.CharField()
    total_score = serializers.FloatField()
    risk_category = serializers.CharField()
    score_breakdown = serializers.DictField()
    created_at = serializers.DateTimeField()


class ReviewScoringRequestSerializer(serializers.Serializer):
    """Serializer for review scoring requests"""
    query = serializers.CharField(help_text="Search query or place ID to fetch reviews for")
    reviews_limit = serializers.IntegerField(default=20, help_text="Maximum number of reviews to fetch per place")
    sort = serializers.ChoiceField(
        choices=["most_relevant", "newest", "highest_rating", "lowest_rating"],
        default="most_relevant",
        help_text="Sorting method for reviews"
    )
    language = serializers.CharField(default="en", help_text="Language code for results")
    async_request = serializers.BooleanField(default=True, help_text="Whether to use asynchronous request processing")


 