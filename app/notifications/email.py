import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .base import Notifier
from ..exceptions import NotificationError, ConfigurationError

logger = logging.getLogger(__name__)


class EmailNotifier(Notifier):
    """
    Email notification implementation using SMTP.

    This class handles sending email notifications through SMTP servers.
    It supports both plain text and HTML email formats and includes
    comprehensive error handling and logging.

    Configuration:
    - SMTP_HOST: SMTP server hostname
    - SMTP_PORT: SMTP server port (usually 587 for TLS or 465 for SSL)
    - SMTP_USER: SMTP username/email
    - SMTP_PASSWORD: SMTP password
    - SMTP_USE_TLS: Whether to use TLS (default: True)
    """

    def __init__(self):
        """Initialize the email notifier with SMTP configuration."""
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

        # Validate required configuration
        if not all([self.smtp_host, self.smtp_user, self.smtp_password]):
            raise ConfigurationError(
                "Missing required SMTP configuration. Please set SMTP_HOST, SMTP_USER, and SMTP_PASSWORD.",
                config_key="smtp_configuration",
            )

        logger.info(
            f"Email notifier initialized with host: {self.smtp_host}:{self.smtp_port}"
        )

    def send(
        self, to_email: str, subject: str, message: str, html_message: str = None
    ) -> bool:
        """
        Send an email notification.

        Args:
            to_email (str): Recipient email address
            subject (str): Email subject line
            message (str): Plain text email body
            html_message (str, optional): HTML email body

        Returns:
            bool: True if email sent successfully, False otherwise

        Raises:
            NotificationError: If email sending fails
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["From"] = self.smtp_user
            msg["To"] = to_email
            msg["Subject"] = subject

            # Add plain text part
            text_part = MIMEText(message, "plain")
            msg.attach(text_part)

            # Add HTML part if provided
            if html_message:
                html_part = MIMEText(html_message, "html")
                msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()

                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP authentication failed: {str(e)}"
            logger.error(error_msg)
            raise NotificationError(error_msg, "email", [to_email])

        except smtplib.SMTPRecipientsRefused as e:
            error_msg = f"Recipient refused: {to_email} - {str(e)}"
            logger.error(error_msg)
            raise NotificationError(error_msg, "email", [to_email])

        except smtplib.SMTPServerDisconnected as e:
            error_msg = f"SMTP server disconnected: {str(e)}"
            logger.error(error_msg)
            raise NotificationError(error_msg, "email", [to_email])

        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {str(e)}"
            logger.error(error_msg)
            raise NotificationError(error_msg, "email", [to_email])

        except Exception as e:
            error_msg = f"Unexpected error sending email: {str(e)}"
            logger.error(error_msg)
            raise NotificationError(error_msg, "email", [to_email])

    def send_bulk(
        self, to_emails: list[str], subject: str, message: str, html_message: str = None
    ) -> dict:
        """
        Send bulk email notifications.

        Args:
            to_emails (list[str]): List of recipient email addresses
            subject (str): Email subject line
            message (str): Plain text email body
            html_message (str, optional): HTML email body

        Returns:
            dict: Results with success count, failure count, and errors
        """
        results = {"success_count": 0, "failure_count": 0, "errors": []}

        for email in to_emails:
            try:
                success = self.send(email, subject, message, html_message)
                if success:
                    results["success_count"] += 1
                else:
                    results["failure_count"] += 1

            except NotificationError as e:
                results["failure_count"] += 1
                results["errors"].append({"email": email, "error": str(e)})
                logger.error(f"Failed to send email to {email}: {str(e)}")

        logger.info(
            f"Bulk email sending completed: {results['success_count']} successful, {results['failure_count']} failed"
        )
        return results


# For development/testing purposes, create a mock email notifier
class MockEmailNotifier(Notifier):
    """
    Mock email notifier for development and testing.

    This class simulates email sending without actually sending emails.
    It logs the email details and always returns success.
    Useful for development, testing, and when SMTP is not configured.
    """

    def __init__(self):
        """Initialize the mock email notifier."""
        logger.info("Mock email notifier initialized - no actual emails will be sent")

    def send(
        self, to_email: str, subject: str, message: str, html_message: str = None
    ) -> bool:
        """
        Mock email sending - logs the email details.

        Args:
            to_email (str): Recipient email address
            subject (str): Email subject line
            message (str): Plain text email body
            html_message (str, optional): HTML email body

        Returns:
            bool: Always returns True (simulated success)
        """
        logger.info(f"[MOCK] Email would be sent to {to_email}")
        logger.info(f"[MOCK] Subject: {subject}")
        logger.info(
            f"[MOCK] Message: {message[:100]}{'...' if len(message) > 100 else ''}"
        )

        if html_message:
            logger.info(
                f"[MOCK] HTML Message: {html_message[:100]}{'...' if len(html_message) > 100 else ''}"
            )

        return True

    def send_bulk(
        self, to_emails: list[str], subject: str, message: str, html_message: str = None
    ) -> dict:
        """
        Mock bulk email sending.

        Args:
            to_emails (list[str]): List of recipient email addresses
            subject (str): Email subject line
            message (str): Plain text email body
            html_message (str, optional): HTML email body

        Returns:
            dict: Simulated results
        """
        logger.info(f"[MOCK] Bulk email would be sent to {len(to_emails)} recipients")
        logger.info(f"[MOCK] Subject: {subject}")

        return {"success_count": len(to_emails), "failure_count": 0, "errors": []}


# Initialize the appropriate email notifier based on configuration
def get_email_notifier():
    """
    Get the appropriate email notifier based on configuration.

    Returns:
        Notifier: Email notifier instance (real or mock)
    """
    try:
        # Try to create a real email notifier
        return EmailNotifier()
    except ConfigurationError:
        logger.warning("SMTP configuration not found, using mock email notifier")
        return MockEmailNotifier()


# Create the email notifier instance
email_notifier = get_email_notifier()
