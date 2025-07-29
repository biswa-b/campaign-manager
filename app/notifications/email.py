from .base import Notifier
import smtplib
from email.message import EmailMessage
import os
import logging

# SMTP configuration - uncomment and configure for actual email sending
# For production deployment, set these environment variables:
# SMTP_USER, SMTP_PASSWORD, SMTP_HOST, SMTP_PORT
# SMTP_USER = os.environ.get("SMTP_USER")
# SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
# SMTP_HOST = os.environ.get("SMTP_HOST")
# SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))

logger = logging.getLogger(__name__)


class EmailNotifier(Notifier):
    """
    Email notification implementation.

    This class handles sending email notifications to recipients.
    Currently implemented as a mock that logs the email details.
    For production use, uncomment the SMTP configuration and implement
    actual email sending logic.

    To enable actual email sending:
    1. Uncomment the SMTP configuration variables above
    2. Set the appropriate environment variables in your .env file
    3. Uncomment the email sending code in the send method
    4. Test with a small campaign first

    Production considerations:
    - Use a reliable SMTP service (SendGrid, Mailgun, etc.)
    - Implement rate limiting to avoid being marked as spam
    - Add email templates for better formatting
    - Monitor delivery rates and bounces
    """

    def send(self, title: str, message: str, recipients: list[str]):
        """
        Send an email notification to the specified recipients.

        Currently implemented as a mock that logs the email details.
        To enable actual email sending, uncomment the SMTP code below.

        Args:
            title (str): Email subject line
            message (str): Email body content
            recipients (list[str]): List of recipient email addresses

        Raises:
            Exception: If email sending fails (when SMTP is enabled)
        """
        logger.info(f"[EMAIL] '{title}' to {recipients}: {message}")

        # Mock implementation - logs email details instead of sending
        # Uncomment the code below to enable actual email sending

        # email = EmailMessage()
        # email['Subject'] = "Campaign Notification"
        # email['From'] = SMTP_USER
        # email['To'] = ", ".join(recipients)
        # email.set_content(message)
        #
        # try:
        #     with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        #         server.starttls()
        #         server.login(SMTP_USER, SMTP_PASSWORD)
        #         server.send_message(email)
        # except Exception as e:
        #     logger.error(f"Failed to send email: {e}")
        #     raise
