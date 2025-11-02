"""
URL configuration for affiliation app.
"""

from django.urls import path
from .views import AffiliationCheckView, AffiliationHistoryView

app_name = 'affiliation'

urlpatterns = [
    path('check/', AffiliationCheckView.as_view(), name='check'),
    path('history/', AffiliationHistoryView.as_view(), name='history'),
]
