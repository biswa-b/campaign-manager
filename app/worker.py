import os
from celery import Celery
from .notifications import notifiers
from .database import SessionLocal
from .models import Campaign, Recipient
from .utils import parse_recipients
from .services.recipient_service import RecipientService
import logging

logger = logging.getLogger(__name__)

# Initialize Celery with Redis as broker and result backend
# This enables asynchronous task processing for the application
# Redis is used for both message queuing and result storage
celery = Celery(
    __name__,
    broker=os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
)


@celery.task
def send_campaign_task(campaign_id: int):
    """
    Celery task to send a campaign to all its active recipients.

    This task is triggered when a campaign is queued for sending.
    It filters out opted-out recipients and sends notifications through all configured notifiers.

    Args:
        campaign_id (int): The ID of the campaign to send

    Returns:
        None: Task completion is logged but no return value
    """
    db = SessionLocal()
    try:
        # Retrieve the campaign from database
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if campaign:
            # Filter out opted-out recipients - only send to active subscribers
            active_recipients = [r for r in campaign.recipients if not r.opt_out]
            recipient_emails = [r.email for r in active_recipients]

            # Handle case where no active recipients exist
            if not recipient_emails:
                logger.warning(f"Campaign {campaign_id} has no active recipients")
                campaign.status = "no_active_recipients"
                db.commit()
                return

            # Send campaign through all configured notifiers (email, SMS, etc.)
            for notifier in notifiers:
                notifier.send(campaign.title, campaign.message, recipient_emails)

            # Update campaign status to sent
            campaign.status = "sent"
            db.commit()
            logger.info(
                f"Campaign {campaign_id} sent to {len(recipient_emails)} active recipients"
            )
    finally:
        db.close()


@celery.task
def process_recipients_task(campaign_id: int, recipient_emails: list[str]):
    """
    Celery task to process and link recipients to a campaign.

    This task runs asynchronously when a campaign is created.
    It handles recipient creation, deduplication, and linking to the campaign.
    Only active (non-opted-out) recipients are linked to the campaign.

    Args:
        campaign_id (int): The ID of the campaign to link recipients to
        recipient_emails (list[str]): List of email addresses to process

    Returns:
        None: Task completion is logged but no return value
    """
    db = SessionLocal()
    try:
        # Retrieve the campaign from database
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            logger.error(f"Campaign {campaign_id} not found")
            return

        # Process each recipient email
        recipients = []
        for email in recipient_emails:
            # Get or create recipient (handles deduplication)
            recipient = RecipientService.get_or_create_recipient(db, email)
            # Only add if not opted out
            if not recipient.opt_out:
                recipients.append(recipient)
            else:
                logger.info(f"Skipping opted-out recipient: {email}")

        # Link only active recipients to the campaign
        campaign.recipients = recipients
        db.commit()

        logger.info(
            f"Processed {len(recipients)} active recipients for campaign {campaign_id}"
        )
    except Exception as e:
        logger.error(f"Error processing recipients for campaign {campaign_id}: {e}")
        db.rollback()
    finally:
        db.close()
