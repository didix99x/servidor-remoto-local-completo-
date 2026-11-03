"""
Security schemas.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from app.models.pairing import PairingStatus


class AuditLogResponse(BaseModel):
    """Audit log entry response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    device_id: Optional[int] = None
    action: str
    resource: str
    details: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime


class AlertResponse(BaseModel):
    """Security alert response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    alert_type: str
    severity: str  # info, warning, critical
    title: str
    message: str
    device_id: Optional[int] = None
    is_read: bool
    created_at: datetime


class PairingRequestResponse(BaseModel):
    """Pairing request response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    device_mac: str
    device_ip: Optional[str] = None
    device_hostname: Optional[str] = None
    device_vendor: Optional[str] = None
    requester_name: str
    status: PairingStatus
    requested_at: datetime
    responded_at: Optional[datetime] = None
    responded_by: Optional[int] = None


class PairingActionRequest(BaseModel):
    """Pairing approve/reject request."""
    action: str = Field(..., pattern="^(approve|reject)$")
    notes: Optional[str] = None