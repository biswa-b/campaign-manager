from sqlalchemy.orm import Session
from ..models import Recipient, Group
from ..schemas import RecipientCreate, GroupCreate
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class RecipientService:
    """
    Service class for managing recipients and groups.

    This service encapsulates all business logic related to recipients and groups,
    including creation, updates, opt-out handling, and group management.
    It provides a clean interface between the API layer and the data layer.

    Key features:
    - Recipient deduplication (same email = same recipient)
    - Opt-out/opt-in compliance
    - Group management
    - Audit logging for all operations
    """

    @staticmethod
    def get_or_create_recipient(
        db: Session, email: str, name: Optional[str] = None
    ) -> Recipient:
        """Get existing recipient or create new one"""
        recipient = db.query(Recipient).filter(Recipient.email == email).first()
        if recipient:
            logger.info(f"Found existing recipient: {email}")
            return recipient

        recipient = Recipient(email=email, name=name, opt_out=False)
        db.add(recipient)
        db.commit()
        db.refresh(recipient)
        logger.info(f"Created new recipient: {email}")
        return recipient

    @staticmethod
    def opt_out_recipient(
        db: Session, email: str, reason: Optional[str] = None
    ) -> Recipient:
        """Opt out a recipient from communications"""
        recipient = db.query(Recipient).filter(Recipient.email == email).first()
        if not recipient:
            # Create recipient if doesn't exist and opt them out
            recipient = Recipient(email=email, opt_out=True)
            db.add(recipient)
        else:
            recipient.opt_out = True

        db.commit()
        db.refresh(recipient)
        logger.info(f"Recipient {email} opted out. Reason: {reason}")
        return recipient

    @staticmethod
    def opt_in_recipient(db: Session, email: str) -> Recipient:
        """Opt in a recipient to communications"""
        recipient = db.query(Recipient).filter(Recipient.email == email).first()
        if not recipient:
            # Create recipient if doesn't exist
            recipient = Recipient(email=email, opt_out=False)
            db.add(recipient)
        else:
            recipient.opt_out = False

        db.commit()
        db.refresh(recipient)
        logger.info(f"Recipient {email} opted in")
        return recipient

    @staticmethod
    def get_active_recipients(db: Session) -> List[Recipient]:
        """Get all recipients who haven't opted out"""
        return db.query(Recipient).filter(Recipient.opt_out == False).all()

    @staticmethod
    def get_recipients_by_group(
        db: Session, group_id: int, active_only: bool = True
    ) -> List[Recipient]:
        """Get all recipients in a group, optionally filtering by opt-out status"""
        query = db.query(Recipient).filter(Recipient.group_id == group_id)
        if active_only:
            query = query.filter(Recipient.opt_out == False)
        return query.all()

    @staticmethod
    def get_or_create_group(
        db: Session, name: str, description: Optional[str] = None
    ) -> Group:
        """Get existing group or create new one"""
        group = db.query(Group).filter(Group.name == name).first()
        if group:
            logger.info(f"Found existing group: {name}")
            return group

        group = Group(name=name, description=description)
        db.add(group)
        db.commit()
        db.refresh(group)
        logger.info(f"Created new group: {name}")
        return group

    @staticmethod
    def add_recipients_to_group(
        db: Session, group_id: int, recipient_emails: List[str]
    ) -> List[Recipient]:
        """Add recipients to a group (only active recipients)"""
        recipients = []
        for email in recipient_emails:
            recipient = RecipientService.get_or_create_recipient(db, email)
            # Only add if not opted out
            if not recipient.opt_out:
                recipient.group_id = group_id
                recipients.append(recipient)
            else:
                logger.warning(f"Skipping opted-out recipient: {email}")

        db.commit()
        logger.info(f"Added {len(recipients)} active recipients to group {group_id}")
        return recipients

    @staticmethod
    def get_all_recipients(
        db: Session, include_opted_out: bool = False
    ) -> List[Recipient]:
        """Get all recipients, optionally including opted-out ones"""
        query = db.query(Recipient)
        if not include_opted_out:
            query = query.filter(Recipient.opt_out == False)
        return query.all()

    @staticmethod
    def update_group(
        db: Session,
        group_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Group:
        """Update a group's properties"""
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise ValueError(f"Group {group_id} not found")

        if name is not None:
            group.name = name
        if description is not None:
            group.description = description

        db.commit()
        db.refresh(group)
        logger.info(f"Updated group {group_id}: name={name}, description={description}")
        return group

    @staticmethod
    def update_recipient(
        db: Session,
        recipient_id: int,
        name: Optional[str] = None,
        group_id: Optional[int] = None,
        opt_out: Optional[bool] = None,
    ) -> Recipient:
        """Update a recipient's properties"""
        recipient = db.query(Recipient).filter(Recipient.id == recipient_id).first()
        if not recipient:
            raise ValueError(f"Recipient {recipient_id} not found")

        if name is not None:
            recipient.name = name
        if group_id is not None:
            # Verify group exists
            group = db.query(Group).filter(Group.id == group_id).first()
            if not group:
                raise ValueError(f"Group {group_id} not found")
            recipient.group_id = group_id
        if opt_out is not None:
            recipient.opt_out = opt_out

        db.commit()
        db.refresh(recipient)
        logger.info(
            f"Updated recipient {recipient_id}: name={name}, group_id={group_id}, opt_out={opt_out}"
        )
        return recipient

    @staticmethod
    def add_recipients_to_group_patch(
        db: Session, group_id: int, recipient_emails: List[str]
    ) -> List[Recipient]:
        """Add recipients to a group via PATCH (only active recipients)"""
        # Verify group exists
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise ValueError(f"Group {group_id} not found")

        recipients = []
        for email in recipient_emails:
            recipient = RecipientService.get_or_create_recipient(db, email)
            # Only add if not opted out
            if not recipient.opt_out:
                recipient.group_id = group_id
                recipients.append(recipient)
            else:
                logger.warning(f"Skipping opted-out recipient: {email}")

        db.commit()
        logger.info(f"Added {len(recipients)} active recipients to group {group_id}")
        return recipients
