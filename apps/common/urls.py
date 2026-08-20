from django.urls import path
from .views import TermsView, PrivacyView

urlpatterns = [
    # Both Admin and Public hit these same endpoints
    path('terms/', TermsView.as_view(), name='terms'),
    path('privacy/', PrivacyView.as_view(), name='privacy'),
]