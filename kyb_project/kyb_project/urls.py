"""
URL configuration for kyb_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/geoiq/', include('cpapp.api.GeoIQ.urls')),
    path('api/scoring/', include('cpapp.api.scoring.urls')),
    path('api/outscraper_reviews/', include('cpapp.api.outscraper_reviews.urls')),
    # Handle any non-API route with our React app
    re_path(r'^(?!api/).*$', TemplateView.as_view(template_name='index.html'), name='home'),
]

# Explicitly adding static file serving for development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # For direct URL path mapping to actual files in the static/assets directory
    urlpatterns += [
        path('assets/<path:path>', lambda request, path: static.serve(
            request, path, document_root=str(settings.BASE_DIR / 'kyb_project/static/assets')
        ))
    ]
