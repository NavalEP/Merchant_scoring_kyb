from django.urls import path
from .views import (
    SearchAPIView, ScoreAPIView, 
    ReviewScoringAPIView
)

urlpatterns = [
    path('search/', SearchAPIView.as_view(), name='api-search'),
    path('score/', ScoreAPIView.as_view(), name='api-score'),
    path('review-scoring/', ReviewScoringAPIView.as_view(), name='api-review-scoring'),
    
] 