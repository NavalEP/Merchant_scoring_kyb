from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from cpapp.services.GeoIQ import GeoIQService
from .serializers import LocationCoordinatesSerializer, LocationAddressSerializer

class LocationAnalysisByCoordinatesView(APIView):
    """API endpoint to get location analysis by coordinates"""
    
    def post(self, request):
        serializer = LocationCoordinatesSerializer(data=request.data)
        if serializer.is_valid():
            latitude = serializer.validated_data['lat']
            longitude = serializer.validated_data['lng']
            radius = serializer.validated_data.get('radius', 1000)
            
            geoiq_service = GeoIQService()
            try:
                analysis = geoiq_service.analyze_location(
                    latitude=latitude,
                    longitude=longitude,
                    radius=radius
                )
                return Response(analysis, status=status.HTTP_200_OK)
            except Exception as e:
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LocationAnalysisByAddressView(APIView):
    """API endpoint to get location analysis by address"""
    
    def post(self, request):
        serializer = LocationAddressSerializer(data=request.data)
        if serializer.is_valid():
            address = serializer.validated_data['address']
            pincode = serializer.validated_data.get('pincode')
            radius = serializer.validated_data.get('radius', 1000)
            
            geoiq_service = GeoIQService()
            try:
                analysis = geoiq_service.analyze_location(
                    address=address,
                    pincode=pincode,
                    radius=radius
                )
                return Response(analysis, status=status.HTTP_200_OK)
            except Exception as e:
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)