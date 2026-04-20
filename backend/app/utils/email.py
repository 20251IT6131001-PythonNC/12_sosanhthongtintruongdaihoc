"""
Email utilities for sending verification emails via Gmail SMTP.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
from app.config import settings


def send_verification_code_email(recipient_email: str, first_name: str, verification_code: str) -> bool:
    """
    Send 6-digit verification code to user email.

    Args:
        recipient_email: User's email address
        first_name: User's first name
        verification_code: 6-digit code to send

    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Your {settings.EMAIL_FROM_NAME} verification code"
        msg['From'] = f"{settings.EMAIL_FROM_NAME} <{settings.GMAIL_SENDER_EMAIL}>"
        msg['To'] = recipient_email

        # HTML email template
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; background-color: #f5f5f5; }
                .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; }
                .header { text-align: center; margin-bottom: 30px; }
                .logo { font-size: 24px; font-weight: bold; color: #1f3ab0; }
                .content { color: #333; line-height: 1.6; }
                .code-box {
                    background-color: #f0f0f0;
                    border: 2px dashed #1f3ab0;
                    padding: 20px;
                    text-align: center;
                    margin: 30px 0;
                    border-radius: 8px;
                }
                .code-text {
                    font-size: 36px;
                    font-weight: bold;
                    color: #1f3ab0;
                    letter-spacing: 8px;
                    font-family: monospace;
                }
                .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #999; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">{{ email_from_name }}</div>
                </div>

                <div class="content">
                    <p>Hi {{ first_name }},</p>

                    <p>Thank you for signing up! Use the following code to verify your account:</p>

                    <div class="code-box">
                        <div class="code-text">{{ code }}</div>
                    </div>

                    <p>This code will expire in 10 minutes.</p>

                    <p>If you didn't request this code, you can safely ignore this email.</p>
                </div>

                <div class="footer">
                    <p>© 2026 {{ email_from_name }}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Render template
        template = Template(html_template)
        html_content = template.render(
            first_name=first_name,
            email_from_name=settings.EMAIL_FROM_NAME,
            code=verification_code
        )

        # Plain text fallback
        text_content = f"""
Hi {first_name},

Thank you for signing up! Use the following code to verify your account:

{verification_code}

This code will expire in 10 minutes.

If you didn't request this code, you can safely ignore this email.
"""

        # Attach both text and HTML versions
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))

        # Send email
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.GMAIL_SENDER_EMAIL, settings.GMAIL_APP_PASSWORD)
            server.send_message(msg)

        return True

    except Exception as e:
        print(f"Error sending verification code email: {e}")
        return False
    """
    Send email verification link to user.

    Args:
        recipient_email: User's email address
        first_name: User's first name
        verification_token: Verification token to include in link

    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Build verification link
        verification_link = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"

        # Create email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Verify your {settings.EMAIL_FROM_NAME} email"
        msg['From'] = f"{settings.EMAIL_FROM_NAME} <{settings.GMAIL_SENDER_EMAIL}>"
        msg['To'] = recipient_email

        # HTML email template
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; background-color: #f5f5f5; }
                .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; }
                .header { text-align: center; margin-bottom: 30px; }
                .logo { font-size: 24px; font-weight: bold; color: #1f3ab0; }
                .content { color: #333; line-height: 1.6; }
                .verification-button {
                    display: inline-block;
                    background-color: #1f3ab0;
                    color: white;
                    padding: 12px 30px;
                    text-decoration: none;
                    border-radius: 4px;
                    margin-top: 20px;
                }
                .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #999; }
                .token { font-family: monospace; background-color: #f5f5f5; padding: 10px; border-radius: 4px; word-break: break-all; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">{{ email_from_name }}</div>
                </div>

                <div class="content">
                    <p>Hi {{ first_name }},</p>

                    <p>Thank you for signing up! Please verify your email address to complete your registration.</p>

                    <p>Click the button below to verify your email:</p>

                    <a href="{{ verification_link }}" class="verification-button">Verify Email</a>

                    <p>Or copy and paste this link in your browser:</p>
                    <div class="token">{{ verification_link }}</div>

                    <p>This link will expire in {{ expiry_hours }} hours.</p>

                    <p>If you didn't create this account, you can safely ignore this email.</p>
                </div>

                <div class="footer">
                    <p>© 2026 {{ email_from_name }}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Render template
        template = Template(html_template)
        html_content = template.render(
            first_name=first_name,
            email_from_name=settings.EMAIL_FROM_NAME,
            verification_link=verification_link,
            expiry_hours=settings.EMAIL_VERIFICATION_EXPIRY_HOURS
        )

        # Plain text fallback
        text_content = f"""
Hi {first_name},

Thank you for signing up! Please verify your email address to complete your registration.

Click this link to verify your email:
{verification_link}

This link will expire in {settings.EMAIL_VERIFICATION_EXPIRY_HOURS} hours.

If you didn't create this account, you can safely ignore this email.
"""

        # Attach both text and HTML versions
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))

        # Send email
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.GMAIL_SENDER_EMAIL, settings.GMAIL_APP_PASSWORD)
            server.send_message(msg)

        return True

    except Exception as e:
        print(f"Error sending verification email: {e}")
        return False
