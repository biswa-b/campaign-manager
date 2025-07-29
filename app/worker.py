import os
import logging
from celery import Celery
from sqlalchemy.orm import Session
from . import models, database, notifications
from .exceptions import NotFoundError, DatabaseError, NotificationError, CampaignError

# Configure Celery with environment variables
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

# Initialize Celery app
celery_app = Celery(
    "campaign_manager",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.worker"],
)

# Configure Celery settings
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Configure logging for Celery tasks
logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def process_recipients_task(self, campaign_id: int, recipient_emails: list[str]):
    """
    Process recipients for a campaign asynchronously.

    This task creates new recipients or links existing ones to a campaign.
    It respects the opt-out flag and only processes active recipients.

    Args:
        campaign_id (int): ID of the campaign to process recipients for
        recipient_emails (list[str]): List of recipient email addresses

    Returns:
        dict: Processing result with counts and status
    """
    logger.info(f"Starting recipient processing for campaign {campaign_id}")

    try:
        db = database.SessionLocal()

        # Verify campaign exists
        campaign = (
            db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
        )
        if not campaign:
            raise NotFoundError("Campaign", campaign_id)

        processed_count = 0
        skipped_count = 0
        errors = []

        for email in recipient_emails:
            try:
                # Get or create recipient
                recipient = (
                    db.query(models.Recipient)
                    .filter(models.Recipient.email == email)
                    .first()
                )
                if not recipient:
                    recipient = models.Recipient(email=email, opt_out=False)
                    db.add(recipient)
                    logger.info(f"Created new recipient: {email}")
                else:
                    logger.info(f"Found existing recipient: {email}")

                # Only add to campaign if not opted out
                if not recipient.opt_out:
                    # Check if already linked to campaign
                    if recipient not in campaign.recipients:
                        campaign.recipients.append(recipient)
                        processed_count += 1
                        logger.info(
                            f"Added recipient {email} to campaign {campaign_id}"
                        )
                    else:
                        logger.info(
                            f"Recipient {email} already in campaign {campaign_id}"
                        )
                else:
                    skipped_count += 1
                    logger.warning(f"Skipped opted-out recipient: {email}")

            except Exception as e:
                error_msg = f"Error processing recipient {email}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue

        # Update campaign status
        campaign.status = "recipients_processed"
        db.commit()

        result = {
            "campaign_id": campaign_id,
            "processed_count": processed_count,
            "skipped_count": skipped_count,
            "error_count": len(errors),
            "errors": errors,
            "status": "completed",
        }

        logger.info(
            f"Recipient processing completed for campaign {campaign_id}: {result}"
        )
        return result

    except NotFoundError:
        logger.error(f"Campaign {campaign_id} not found")
        raise
    except Exception as e:
        logger.error(
            f"Error processing recipients for campaign {campaign_id}: {str(e)}"
        )
        raise CampaignError(
            f"Failed to process recipients: {str(e)}", campaign_id, "process_recipients"
        )
    finally:
        db.close()


@celery_app.task(bind=True)
def send_campaign_task(self, campaign_id: int):
    """
    Send a campaign to all its active recipients asynchronously.

    This task retrieves all recipients for a campaign, filters out opted-out recipients,
    and sends the campaign message to each active recipient.

    Args:
        campaign_id (int): ID of the campaign to send

    Returns:
        dict: Sending result with counts and status
    """
    logger.info(f"Starting campaign sending for campaign {campaign_id}")

    try:
        db = database.SessionLocal()

        # Get campaign with recipients
        campaign = (
            db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
        )
        if not campaign:
            raise NotFoundError("Campaign", campaign_id)

        # Get active recipients (not opted out)
        active_recipients = [r for r in campaign.recipients if not r.opt_out]

        if not active_recipients:
            logger.warning(f"No active recipients found for campaign {campaign_id}")
            campaign.status = "sent_no_recipients"
            db.commit()
            return {
                "campaign_id": campaign_id,
                "sent_count": 0,
                "error_count": 0,
                "status": "completed_no_recipients",
            }

        sent_count = 0
        error_count = 0
        errors = []

        # Send to each active recipient
        for recipient in active_recipients:
            try:
                # Use the email notifier to send the campaign
                notifiers["email"].send(
                    to_email=recipient.email,
                    subject=campaign.title,
                    message=campaign.message,
                )
                sent_count += 1
                logger.info(f"Sent campaign {campaign_id} to {recipient.email}")

            except Exception as e:
                error_msg = f"Error sending to {recipient.email}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                error_count += 1
                continue

        # Update campaign status
        campaign.status = "sent"
        db.commit()

        result = {
            "campaign_id": campaign_id,
            "sent_count": sent_count,
            "error_count": error_count,
            "errors": errors,
            "status": "completed",
        }

        logger.info(f"Campaign sending completed for campaign {campaign_id}: {result}")
        return result

    except NotFoundError:
        logger.error(f"Campaign {campaign_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error sending campaign {campaign_id}: {str(e)}")
        raise CampaignError(f"Failed to send campaign: {str(e)}", campaign_id, "send")
    finally:
        db.close()
