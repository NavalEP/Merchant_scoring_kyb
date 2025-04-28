from django.urls import path
from . import views

app_name = 'outscraper_reviews'

urlpatterns = [
    path('reviews/', views.OutscraperReviewsView.as_view(), name='reviews'),
    path('results/<str:request_id>/', views.OutscraperReviewsResultsView.as_view(), name='results'),
    path('custom-search/', views.CustomSearchView.as_view(), name='custom_search'),
] 