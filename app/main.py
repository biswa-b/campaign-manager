import logging
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from . import models, schemas, database, utils
from .notifications import notifiers
from .worker import send_campaign_task, process_recipients_task
from .services.recipient_service import RecipientService
from .middleware.error_handler import error_handler_middleware
from .exceptions import (
    NotFoundError,
    DuplicateError,
    DatabaseError,
    CampaignError,
    RecipientError,
    GroupError,
)

from fastapi.middleware.cors import CORSMiddleware

# Create database tables if they don't exist
# This ensures the database schema is set up when the app starts
models.Base.metadata.create_all(bind=database.engine)

# Initialize FastAPI application
app = FastAPI(
    title="Campaign Manager API",
    description="A scalable email campaign management system with async processing, recipient management, and GDPR compliance",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure logging for the application
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

# Add CORS middleware to allow cross-origin requests
# This is useful for frontend applications that need to communicate with the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom error handling middleware
app.middleware("http")(error_handler_middleware)


def get_db():
    """
    Dependency function to get database session.

    This function creates a database session and ensures it's properly closed
    after the request is complete, even if an exception occurs.

    Yields:
        Session: SQLAlchemy database session
    """
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =============================================================================
# Campaign Endpoints
# =============================================================================


@app.post("/campaigns/", response_model=schemas.CampaignRead)
def create_campaign(campaign: schemas.CampaignCreate, db: Session = Depends(get_db)):
    """
    Create a new campaign with asynchronous recipient processing.

    This endpoint creates a campaign immediately and processes recipients in the background.
    The response is returned quickly while recipient processing happens asynchronously.

    Args:
        campaign (schemas.CampaignCreate): Campaign data including title, message, and recipient emails
        db (Session): Database session

    Returns:
        dict: Campaign data with processing status
    """
    try:
        # Create campaign without recipients first for immediate response
        db_campaign = models.Campaign(title=campaign.title, message=campaign.message)
        db.add(db_campaign)
        db.commit()
        db.refresh(db_campaign)

        # Process recipients asynchronously in the background
        process_recipients_task.delay(db_campaign.id, campaign.recipient_emails)

        return {
            **db_campaign.__dict__,
            "recipient_emails": campaign.recipient_emails,
            "recipients": [],
        }
    except Exception as e:
        db.rollback()
        raise CampaignError(f"Failed to create campaign: {str(e)}", operation="create")


@app.get("/campaigns/", response_model=list[schemas.CampaignRead])
def list_campaigns(db: Session = Depends(get_db)):
    """
    List all campaigns with their associated recipients.

    Args:
        db (Session): Database session

    Returns:
        list: List of all campaigns with recipient information
    """
    try:
        campaigns = db.query(models.Campaign).all()
        result = []
        for c in campaigns:
            # Use ORM mode conversion for proper schema validation
            campaign_data = {
                "id": c.id,
                "title": c.title,
                "message": c.message,
                "status": c.status,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
                "recipient_emails": [r.email for r in c.recipients],
                "recipients": c.recipients,  # Let Pydantic handle the conversion
            }
            result.append(campaign_data)
        return result
    except Exception as e:
        raise DatabaseError(f"Failed to list campaigns: {str(e)}", "list_campaigns")


@app.post("/campaigns/send")
def send_campaign(req: schemas.CampaignSendRequest, db: Session = Depends(get_db)):
    """
    Queue a campaign for sending.

    This endpoint triggers the asynchronous sending of a campaign to all its active recipients.
    The campaign status is updated to "queued" and the actual sending happens in the background.

    Args:
        req (schemas.CampaignSendRequest): Campaign send request with campaign ID
        db (Session): Database session

    Returns:
        dict: Status confirmation with campaign ID
    """
    try:
        campaign = (
            db.query(models.Campaign).filter(models.Campaign.id == req.id).first()
        )
        if not campaign:
            raise NotFoundError("Campaign", req.id)

        # Queue the campaign for sending in the background
        send_campaign_task.delay(campaign.id)
        campaign.status = "queued"
        db.commit()
        return {"status": "queued", "campaign_id": campaign.id}
    except NotFoundError:
        raise
    except Exception as e:
        db.rollback()
        raise CampaignError(f"Failed to send campaign: {str(e)}", req.id, "send")


# =============================================================================
# Group Endpoints
# =============================================================================


@app.post("/groups/", response_model=schemas.GroupRead)
def create_group(group: schemas.GroupCreate, db: Session = Depends(get_db)):
    """
    Create a new group for organizing recipients.

    Args:
        group (schemas.GroupCreate): Group data including name and optional description
        db (Session): Database session

    Returns:
        schemas.GroupRead: Created group data
    """
    try:
        return RecipientService.get_or_create_group(db, group.name, group.description)
    except (DuplicateError, DatabaseError):
        raise


@app.get("/groups/", response_model=list[schemas.GroupRead])
def list_groups(db: Session = Depends(get_db)):
    """
    List all groups.

    Args:
        db (Session): Database session

    Returns:
        list: List of all groups
    """
    try:
        return db.query(models.Group).all()
    except Exception as e:
        raise DatabaseError(f"Failed to list groups: {str(e)}", "list_groups")


@app.patch("/groups/{group_id}", response_model=schemas.GroupRead)
def update_group(
    group_id: int, group_update: schemas.GroupUpdate, db: Session = Depends(get_db)
):
    """
    Update a group's properties.

    Args:
        group_id (int): ID of the group to update
        group_update (schemas.GroupUpdate): Partial update data
        db (Session): Database session

    Returns:
        schemas.GroupRead: Updated group data
    """
    try:
        return RecipientService.update_group(
            db, group_id, group_update.name, group_update.description
        )
    except (NotFoundError, DuplicateError, GroupError):
        raise


@app.patch("/groups/{group_id}/recipients", response_model=list[schemas.RecipientRead])
def add_recipients_to_group(
    group_id: int,
    group_recipients: schemas.GroupAddRecipients,
    db: Session = Depends(get_db),
):
    """
    Add recipients to a group.

    Only active (non-opted-out) recipients are added to the group.
    Opted-out recipients are skipped with a warning log.

    Args:
        group_id (int): ID of the group to add recipients to
        group_recipients (schemas.GroupAddRecipients): List of recipient emails
        db (Session): Database session

    Returns:
        list: List of added recipients
    """
    try:
        return RecipientService.add_recipients_to_group_patch(
            db, group_id, group_recipients.recipient_emails
        )
    except (NotFoundError, GroupError):
        raise


# =============================================================================
# Recipient Endpoints
# =============================================================================


@app.post("/recipients/", response_model=schemas.RecipientRead)
def create_recipient(recipient: schemas.RecipientCreate, db: Session = Depends(get_db)):
    """
    Create a new recipient or get existing one.

    If a recipient with the same email already exists, it returns the existing recipient.
    This prevents duplicate recipients in the system.

    Args:
        recipient (schemas.RecipientCreate): Recipient data
        db (Session): Database session

    Returns:
        schemas.RecipientRead: Created or existing recipient data
    """
    try:
        db_recipient = RecipientService.get_or_create_recipient(
            db, recipient.email, recipient.name
        )
        if recipient.group_id:
            db_recipient.group_id = recipient.group_id
            db.commit()
        return db_recipient
    except (DuplicateError, DatabaseError, RecipientError):
        raise


@app.get("/recipients/", response_model=list[schemas.RecipientRead])
def list_recipients(db: Session = Depends(get_db), include_opted_out: bool = False):
    """
    List all recipients, optionally including opted-out ones.

    Args:
        db (Session): Database session
        include_opted_out (bool): Whether to include opted-out recipients

    Returns:
        list: List of recipients
    """
    try:
        return RecipientService.get_all_recipients(db, include_opted_out)
    except DatabaseError:
        raise


@app.patch("/recipients/{recipient_id}", response_model=schemas.RecipientRead)
def update_recipient(
    recipient_id: int,
    recipient_update: schemas.RecipientUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a recipient's properties.

    Args:
        recipient_id (int): ID of the recipient to update
        recipient_update (schemas.RecipientUpdate): Partial update data
        db (Session): Database session

    Returns:
        schemas.RecipientRead: Updated recipient data
    """
    try:
        return RecipientService.update_recipient(
            db,
            recipient_id,
            recipient_update.name,
            recipient_update.group_id,
            recipient_update.opt_out,
        )
    except (NotFoundError, RecipientError):
        raise


@app.post("/recipients/opt-out", response_model=schemas.RecipientRead)
def opt_out_recipient(opt_out: schemas.RecipientOptOut, db: Session = Depends(get_db)):
    """
    Opt out a recipient from all communications.

    This endpoint handles GDPR compliance by allowing recipients to unsubscribe.
    If the recipient doesn't exist, it creates them with opt_out=True.

    Args:
        opt_out (schemas.RecipientOptOut): Opt-out request with email and optional reason
        db (Session): Database session

    Returns:
        schemas.RecipientRead: Updated recipient data
    """
    try:
        return RecipientService.opt_out_recipient(db, opt_out.email, opt_out.reason)
    except RecipientError:
        raise


@app.post("/recipients/opt-in", response_model=schemas.RecipientRead)
def opt_in_recipient(opt_in: schemas.RecipientOptIn, db: Session = Depends(get_db)):
    """
    Opt in a recipient to communications.

    This allows recipients to re-subscribe after opting out.
    If the recipient doesn't exist, it creates them with opt_out=False.

    Args:
        opt_in (schemas.RecipientOptIn): Opt-in request with email
        db (Session): Database session

    Returns:
        schemas.RecipientRead: Updated recipient data
    """
    try:
        return RecipientService.opt_in_recipient(db, opt_in.email)
    except RecipientError:
        raise


@app.get("/recipients/active", response_model=list[schemas.RecipientRead])
def list_active_recipients(db: Session = Depends(get_db)):
    """
    List only active (non-opted-out) recipients.

    This endpoint is useful for getting a clean list of recipients who can receive communications.

    Args:
        db (Session): Database session

    Returns:
        list: List of active recipients
    """
    try:
        return RecipientService.get_active_recipients(db)
    except DatabaseError:
        raise


@app.get("/groups/{group_id}/recipients", response_model=list[schemas.RecipientRead])
def list_group_recipients(
    group_id: int, db: Session = Depends(get_db), active_only: bool = True
):
    """
    Get recipients in a group, optionally filtering by opt-out status.

    Args:
        group_id (int): ID of the group
        db (Session): Database session
        active_only (bool): Whether to include only active recipients

    Returns:
        list: List of recipients in the group
    """
    try:
        return RecipientService.get_recipients_by_group(db, group_id, active_only)
    except DatabaseError:
        raise
