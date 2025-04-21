from rest_framework import serializers

class LocationCoordinatesSerializer(serializers.Serializer):
    lat = serializers.FloatField(min_value=-90, max_value=90)
    lng = serializers.FloatField(min_value=-180, max_value=180)
    radius = serializers.IntegerField(min_value=100, max_value=2000, required=False, default=1000)


class LocationAddressSerializer(serializers.Serializer):
    address = serializers.CharField(max_length=500)
    pincode = serializers.CharField(max_length=10, required=False)
    radius = serializers.IntegerField(min_value=100, max_value=2000, required=False, default=1000)