from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TermsAndConditionsViewSet, PrivacyPolicyViewSet

router = DefaultRouter()

# Registers at: /api/core/terms/
router.register(r'terms', TermsAndConditionsViewSet, basename='terms')

# Registers at: /api/core/privacy/
router.register(r'privacy', PrivacyPolicyViewSet, basename='privacy')

urlpatterns = [
    path('', include(router.urls)),
]