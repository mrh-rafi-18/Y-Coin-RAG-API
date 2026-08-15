import hashlib
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import PasswordResetToken

User = get_user_model()


def get_password_reset_token(raw_token):
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    token = (
        PasswordResetToken.objects
        .select_related("user")
        .filter(
            token_hash=token_hash,
            is_used=False,
        )
        .first()
    )

    if token is None:
        return None

    if token.expires_at <= timezone.now():
        return None

    return token


def reset_user_password(reset_token, new_password):
    token = get_password_reset_token(reset_token)

    if token is None:
        return False

    user = token.user
    user.set_password(new_password)
    user.save(update_fields=["password"])

    token.is_used = True
    token.save(update_fields=["is_used"])

    return True