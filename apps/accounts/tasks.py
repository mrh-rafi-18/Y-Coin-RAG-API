from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def send_otp_email(email, code):
    subject = "Your Y-Coin AI verification code"

    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Y-Coin AI Verification</title>
    </head>

    <body style="
        margin: 0;
        padding: 0;
        background-color: #f3f4f6;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        color: #374151;
        -webkit-font-smoothing: antialiased;
    ">

        <table width="100%" cellpadding="0" cellspacing="0" border="0"
               style="background-color: #f3f4f6; padding: 40px 15px;">
            <tr>
                <td align="center">

                    <table width="100%" cellpadding="0" cellspacing="0" border="0"
                           style="
                               max-width: 520px;
                               background-color: #ffffff;
                               border-radius: 12px;
                               overflow: hidden;
                               box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
                               border: 1px solid #e5e7eb;
                           ">

                        <!-- Header -->
                        <tr>
                            <td align="center"
                                style="
                                    padding: 32px 30px 20px;
                                    background-color: #ffffff;
                                ">

                                <div style="
                                    font-size: 26px;
                                    font-weight: 800;
                                    color: #2563eb;
                                    letter-spacing: -0.5px;
                                ">
                                    Y-Coin AI
                                </div>

                            </td>
                        </tr>

                        <!-- Content -->
                        <tr>
                            <td style="padding: 0 35px 40px;">

                                <h1 style="
                                    margin: 0 0 15px 0;
                                    font-size: 22px;
                                    line-height: 30px;
                                    color: #111827;
                                    text-align: center;
                                    font-weight: 700;
                                ">
                                    Verify your email
                                </h1>

                                <p style="
                                    margin: 0 0 30px 0;
                                    font-size: 15px;
                                    line-height: 24px;
                                    color: #4b5563;
                                    text-align: center;
                                ">
                                    Use the verification code below to complete
                                    your Y-Coin AI registration.
                                </p>

                                <!-- OTP -->
                                <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                    <tr>
                                        <td align="center">

                                            <div style="
                                                display: inline-block;
                                                padding: 16px 32px;
                                                background-color: #eff6ff;
                                                border: 1px solid #bfdbfe;
                                                border-radius: 8px;
                                                font-size: 32px;
                                                font-weight: 700;
                                                letter-spacing: 6px;
                                                color: #1d4ed8;
                                            ">
                                                {code}
                                            </div>

                                        </td>
                                    </tr>
                                </table>

                                <p style="
                                    margin: 30px 0 0 0;
                                    font-size: 14px;
                                    line-height: 22px;
                                    color: #4b5563;
                                    text-align: center;
                                ">
                                    This code will expire in
                                    <strong style="color: #111827; font-weight: 600;">
                                        5 minutes
                                    </strong>.
                                </p>

                                <hr style="
                                    border: 0;
                                    border-top: 1px solid #e5e7eb;
                                    margin: 32px 0;
                                ">

                                <p style="
                                    margin: 0;
                                    font-size: 13px;
                                    line-height: 20px;
                                    color: #6b7280;
                                    text-align: center;
                                ">
                                    If you didn't request this verification code,
                                    you can safely ignore this email.
                                </p>

                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td align="center"
                                style="
                                    padding: 24px 30px;
                                    background-color: #f9fafb;
                                    border-top: 1px solid #e5e7eb;
                                ">

                                <p style="
                                    margin: 0;
                                    font-size: 12px;
                                    color: #9ca3af;
                                ">
                                    © 2026 Y-Coin AI. All rights reserved.
                                </p>

                            </td>
                        </tr>

                    </table>

                </td>
            </tr>
        </table>

    </body>
    </html>
    """

    plain_message = (
        f"Your Y-Coin AI verification code is {code}.\n\n"
        "This code will expire in 5 minutes.\n\n"
        "If you didn't request this code, you can safely ignore this email."
    )

    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        html_message=html_message,
    )