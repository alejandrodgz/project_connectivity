"""
URL configuration for citizen validation.
"""

from django.urls import path
from .views import CitizenValidationView
from .external_views import check_citizen_exists

app_name = 'citizen_validation'

# Internal API endpoints (require JWT authentication)
urlpatterns = [
    path('check/', CitizenValidationView.as_view(), name='check'),
]

# External API endpoints (require OAuth2 Client Credentials from auth-microservice)
external_urlpatterns = [
    path('citizen/<int:idCitizen>', check_citizen_exists, name='external-check-citizen'),
]
