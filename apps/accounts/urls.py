from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()

# Registers at: /api/accounts/users/
router.register(r'users', AdminUserViewSet, basename='admin-user')

urlpatterns = [
    path("auth/register/", RegisterAPIView.as_view(), name="register"),
    path("auth/register/request-otp/", RegisterRequestOTPAPIView.as_view(), name="register-request-otp"),
    path("auth/password-reset/request-otp/", PasswordResetRequestOTPAPIView.as_view(), name="password-reset-request-otp"),
    path("auth/register/verify-email/", VerifyEmailAPIView.as_view(), name="verify-email"),
    path("auth/password-reset/verify-otp/", VerifyOTPAPIView.as_view(), name="verify-otp"),
    path("auth/change-password/", ChangePasswordAPIView.as_view(), name="change-password"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/refresh/", RefreshTokenView.as_view(), name="token-refresh"),
    path("auth/change-password/", ChangePasswordAPIView.as_view(), name="change-password"),
    path("password-reset/",ResetPasswordAPIView.as_view(),name="password-reset"),
    path("logout/", LogoutView.as_view(), name="logout"),

    #admin dashboard
    path('', include(router.urls)),
]