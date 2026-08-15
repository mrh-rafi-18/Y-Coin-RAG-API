from django.shortcuts import render
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView, RetrieveUpdateAPIView
from datetime import timedelta
from django.utils import timezone
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from rest_framework import status
from .models import *
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .tasks import send_otp_email
from django.contrib.auth import get_user_model
from .serializers import *
from .utils import *
from .services import *
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)

# Create your views here.


User = get_user_model()


@extend_schema(
    tags=["Users"],
    request=UserSerializer,
    responses=UserSerializer,
)
class UserListCreateAPIView(ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


@extend_schema(
    tags=["Auth"],
    request=UserSerializer,
    responses={
        201: UserSerializer,
    },
)
class RegisterAPIView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = UserSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        # Invalidate any previous registration OTPs
        OTP.objects.filter(
            email=email,
            purpose=OTP.Purpose.REGISTRATION,
            is_used=False,
        ).update(is_used=True)

        # Create user
        user = serializer.save()

        # Generate a 6-digit OTP
        code = generate_otp()

        # Store only the hashed OTP
        OTP.objects.create(
            email=email,
            code_hash=hash_otp(code),
            purpose=OTP.Purpose.REGISTRATION,
            expires_at=timezone.now() + timedelta(minutes=5),
        )

        send_otp_email.delay(
                email=email,
                code=code,
            )

        return Response(
            {
                "message": "Registration successful. Please verify your email.",
                "email": user.email,
            },
            status=status.HTTP_201_CREATED,
        )




@extend_schema(
    tags=["Auth"],
    request=RequestOTPSerializer,
    responses={
        200: {"description": "OTP sent successfully."},
        400: {"description": "Invalid request."},
        404: {"description": "User not found."},
    },
)
class RegisterRequestOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        user = User.objects.filter(email=email).first()

        if user is None:
            return Response(
                {
                    "detail": (
                        "No account exists with this email. "
                        "Please register first."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.is_email_verified:
            return Response(
                {
                    "detail": (
                        "An account with this email already exists "
                        "and is already verified."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Invalidate previous registration OTPs
        OTP.objects.filter(
            email=email,
            purpose=OTP.Purpose.REGISTRATION,
            is_used=False,
        ).update(is_used=True)

        # Generate new OTP
        code = generate_otp()

        # Store hashed OTP
        OTP.objects.create(
            email=email,
            code_hash=hash_otp(code),
            purpose=OTP.Purpose.REGISTRATION,
            expires_at=timezone.now() + timedelta(minutes=5),
        )

        send_otp_email.delay(
                email=email,
                code=code,
            )

        return Response(
            {
                "detail": "OTP sent successfully."
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(
    tags=["Auth"],
    request=RequestOTPSerializer,
    responses={
        200: {"description": "OTP sent successfully."},
        400: {"description": "Invalid request."},
        404: {"description": "User not found."},
    },
)
class PasswordResetRequestOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        user = User.objects.filter(email=email).first()

        if user is None:
            return Response(
                {
                    "detail": "No account exists with this email."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if not user.is_email_verified:
            return Response(
                {
                    "detail": (
                        "This email address has not been verified. "
                        "Please verify your email first."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Invalidate previous password reset OTPs
        OTP.objects.filter(
            email=email,
            purpose=OTP.Purpose.PASSWORD_RESET,
            is_used=False,
        ).update(is_used=True)

        # Generate new OTP
        code = generate_otp()

        # Store hashed OTP
        OTP.objects.create(
            email=email,
            code_hash=hash_otp(code),
            purpose=OTP.Purpose.PASSWORD_RESET,
            expires_at=timezone.now() + timedelta(minutes=5),
        )

        send_otp_email.delay(
                email=email,
                code=code,
            )

        return Response(
            {
                "detail": "OTP sent successfully."
            },
            status=status.HTTP_200_OK,
        )




@extend_schema(
    tags=["Auth"],
    request=VerifyOTPSerializer,
    responses={
        200: {"description": "Email verified successfully."},
        400: {"description": "Invalid or expired OTP."},
        404: {"description": "User or OTP not found."},
    },
)
class VerifyEmailAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["otp"]

        user = User.objects.filter(email=email).first()

        if user is None:
            return Response(
                {"detail": "No account exists with this email."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.is_email_verified:
            return Response(
                {"detail": "Email is already verified."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp = (
            OTP.objects.filter(
                email=email,
                purpose=OTP.Purpose.REGISTRATION,
                is_used=False,
            )
            .order_by("-created_at")
            .first()
        )

        if otp is None:
            return Response(
                {"detail": "No active verification OTP found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if otp.expires_at <= timezone.now():
            return Response(
                {"detail": "OTP has expired. Please request a new OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not verify_otp(code, otp.code_hash):
            return Response(
                {"detail": "Invalid OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])

        otp.is_used = True
        otp.save(update_fields=["is_used"])

        return Response(
            {"detail": "Email verified successfully."},
            status=status.HTTP_200_OK,
        )




@extend_schema(
    tags=["Auth"],
    request=VerifyOTPSerializer,
    responses={
        200: {"description": "Password reset OTP verified successfully."},
        400: {"description": "Invalid or expired OTP."},
        404: {"description": "User or OTP not found."},
    },
)
class VerifyOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["otp"]

        user = User.objects.filter(email=email).first()

        if user is None:
            return Response(
                {"detail": "No account exists with this email."},
                status=status.HTTP_404_NOT_FOUND,
            )

        otp = (
            OTP.objects.filter(
                email=email,
                purpose=OTP.Purpose.PASSWORD_RESET,
                is_used=False,
            )
            .order_by("-created_at")
            .first()
        )

        if otp is None:
            return Response(
                {"detail": "No active password reset OTP found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if otp.expires_at <= timezone.now():
            return Response(
                {"detail": "OTP has expired. Please request a new OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not verify_otp(code, otp.code_hash):
            return Response(
                {"detail": "Invalid OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        reset_token = create_password_reset_token(user)

        otp.is_used = True
        otp.save(update_fields=["is_used"])

        return Response({
            "detail": "Password reset OTP verified successfully.",
            "reset_token": reset_token,
        })





@extend_schema(
    tags=["Auth"],
    request=ChangePasswordSerializer,
    responses={
        200: {"description": "Password changed successfully."},
        400: {"description": "The current password is incorrect."},
        404: {"description": "User account not found."},
    },
)
class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        current_password = serializer.validated_data["current_password"]
        new_password = serializer.validated_data["new_password"]

        user = request.user

        if not user.check_password(current_password):
            return Response(
                {
                    "detail": (
                        "The current password you entered is incorrect."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save(update_fields=["password"])

        return Response(
            {
                "detail": "Your password has been changed successfully."
            },
            status=status.HTTP_200_OK,
        )



@extend_schema(
    tags=["Auth"],
    request=ResetPasswordSerializer,
    responses={
        200: {"description": "Password reset successfully."},
        400: {"description": "Invalid or expired reset token."},
    },
)
class ResetPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reset_token = serializer.validated_data["reset_token"]
        new_password = serializer.validated_data["new_password"]

        success = reset_user_password(
            reset_token=reset_token,
            new_password=new_password,
        )

        if not success:
            return Response(
                {"detail": "Invalid or expired reset token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": "Password reset successfully."},
            status=status.HTTP_200_OK,
        )






@extend_schema(
    tags=["Users"],
    request=UserSerializer,
    responses=UserSerializer,
)
class ProfileView(RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema(
    tags=["Auth"],
)
class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


@extend_schema(
    tags=["Auth"],
)
class RefreshTokenView(TokenRefreshView):
    pass