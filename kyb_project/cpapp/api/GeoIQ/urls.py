from django.urls import path
from .views import LocationAnalysisByCoordinatesView, LocationAnalysisByAddressView

urlpatterns = [
    path('location/coordinates/', LocationAnalysisByCoordinatesView.as_view(), name='location-analysis-coordinates'),
    path('location/address/', LocationAnalysisByAddressView.as_view(), name='location-analysis-address'),
]