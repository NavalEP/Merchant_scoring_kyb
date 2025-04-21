from rest_framework import serializers
from typing import List, Optional

class OutscraperReviewsSerializer(serializers.Serializer):
    query = serializers.CharField(required=True)
    reviews_limit = serializers.IntegerField(default=100, required=False)
    reviews_query = serializers.CharField(required=False, allow_null=True)
    limit = serializers.IntegerField(default=1, required=False)
    sort = serializers.ChoiceField(
        choices=["most_relevant", "newest", "highest_rating", "lowest_rating"],
        default="most_relevant",
        required=False
    )
    last_pagination_id = serializers.CharField(required=False, allow_null=True)
    start = serializers.IntegerField(required=False, allow_null=True)
    cutoff = serializers.IntegerField(required=False, allow_null=True)
    cutoff_rating = serializers.IntegerField(required=False, allow_null=True)
    ignore_empty = serializers.BooleanField(default=False, required=False)
    source = serializers.CharField(required=False, allow_null=True)
    language = serializers.CharField(default="en", required=False)
    region = serializers.CharField(required=False, allow_null=True)
    fields = serializers.CharField(required=False, allow_null=True)
    async_request = serializers.BooleanField(default=True, required=False)
    ui = serializers.BooleanField(default=False, required=False)
    webhook = serializers.URLField(required=False, allow_null=True) 