from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# =============================================================================
# Group Schemas
# =============================================================================


class GroupBase(BaseModel):
    """Base schema for group operations with common fields."""

    name: str
    description: Optional[str] = None


class GroupCreate(GroupBase):
    """Schema for creating a new group."""

    pass


class GroupRead(GroupBase):
    """Schema for reading group data with all fields including timestamps."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class GroupUpdate(BaseModel):
    """Schema for partial updates to a group (PATCH operations)."""

    name: Optional[str] = None
    description: Optional[str] = None


class GroupAddRecipients(BaseModel):
    """Schema for adding multiple recipients to a group."""

    recipient_emails: List[str]


# =============================================================================
# Recipient Schemas
# =============================================================================


class RecipientBase(BaseModel):
    """Base schema for recipient operations with common fields."""

    email: EmailStr  # Validates email format
    name: Optional[str] = None
    group_id: Optional[int] = None
    opt_out: Optional[bool] = False


class RecipientCreate(RecipientBase):
    """Schema for creating a new recipient."""

    pass


class RecipientRead(RecipientBase):
    """Schema for reading recipient data with all fields including timestamps."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class RecipientUpdate(BaseModel):
    """Schema for partial updates to a recipient (PATCH operations)."""

    name: Optional[str] = None
    group_id: Optional[int] = None
    opt_out: Optional[bool] = None


class RecipientOptOut(BaseModel):
    """Schema for opting out a recipient from communications."""

    email: EmailStr
    reason: Optional[str] = None  # Optional reason for opt-out


class RecipientOptIn(BaseModel):
    """Schema for opting in a recipient to communications."""

    email: EmailStr


# =============================================================================
# Campaign Schemas
# =============================================================================


class CampaignCreate(BaseModel):
    """Schema for creating a new campaign."""

    title: str
    message: str
    recipient_emails: List[str]  # List of email addresses to target


class CampaignRead(CampaignCreate):
    """Schema for reading campaign data with all fields including relationships."""

    id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    recipients: List[RecipientRead] = []  # List of linked recipients

    class Config:
        orm_mode = True


class CampaignSendRequest(BaseModel):
    """Schema for requesting to send a campaign."""

    id: int
