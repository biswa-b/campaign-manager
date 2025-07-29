from sqlalchemy import Column, Integer, String, Table, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

# Association table for many-to-many relationship between campaigns and recipients
# This allows campaigns to have multiple recipients and recipients to be in multiple campaigns
campaign_recipients = Table(
    "campaign_recipients",
    Base.metadata,
    Column("campaign_id", Integer, ForeignKey("campaigns.id")),
    Column("recipient_id", Integer, ForeignKey("recipients.id")),
)


class Group(Base):
    """
    Group model for organizing recipients into categories.

    Groups can be used to segment recipients (e.g., "VIP Customers", "Newsletter Subscribers")
    and make campaign targeting more efficient.
    """

    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)  # Unique group name
    description = Column(String, nullable=True)  # Optional description
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship: One group can have many recipients
    recipients = relationship("Recipient", back_populates="groups")


class Recipient(Base):
    """
    Recipient model for storing email recipients and their preferences.

    Each recipient has an email address and can be part of groups.
    The opt_out flag tracks whether they've unsubscribed from communications.
    """

    __tablename__ = "recipients"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)  # Unique email address
    name = Column(String, nullable=True)  # Optional display name
    group_id = Column(
        Integer, ForeignKey("groups.id"), nullable=True
    )  # Optional group assignment
    opt_out = Column(Boolean, default=False)  # Track subscription status
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    groups = relationship(
        "Group", back_populates="recipients"
    )  # Many-to-one with Group
    campaigns = relationship(
        "Campaign", secondary=campaign_recipients, back_populates="recipients"
    )  # Many-to-many with Campaign


class Campaign(Base):
    """
    Campaign model for storing email campaigns and their metadata.

    Campaigns represent email campaigns that can be sent to multiple recipients.
    The status field tracks the campaign's lifecycle (pending, queued, sent, etc.).
    """

    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)  # Campaign title
    message = Column(String)  # Campaign message content
    status = Column(
        String, default="pending"
    )  # Campaign status: pending, queued, sent, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship: Many-to-many with Recipient through campaign_recipients table
    recipients = relationship(
        "Recipient", secondary=campaign_recipients, back_populates="campaigns"
    )
