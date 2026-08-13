import secrets

from django.contrib.auth.hashers import check_password, make_password


def generate_otp():
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(code):
    return make_password(code)


def verify_otp(code, code_hash):
    return check_password(code, code_hash)


if __name__=="__main__":
    from django.conf import settings
    
    # Configure minimal settings required by make_password
    settings.configure(
        PASSWORD_HASHERS=[
            'django.contrib.auth.hashers.PBKDF2PasswordHasher',
        ]
    )
    otp=generate_otp()
    hash=hash_otp(otp)

    print(otp)
    print(hash)
    print(verify_otp(otp,hash))