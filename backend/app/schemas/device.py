"""
Device schemas.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from app.models.device import DeviceType


class DeviceBase(BaseModel):
    """Base device fields."""
    mac_address: str = Field(..., pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")
    ip_address: Optional[str] = None
    hostname: Optional[str] = None
    vendor: Optional[str] = None
    device_type: DeviceType = DeviceType.UNKNOWN
    os_info: Optional[str] = None
    notes: Optional[str] = None


class DeviceCreate(DeviceBase):
    """Device creation request."""
    pass


class DeviceUpdate(BaseModel):
    """Device update request."""
    hostname: Optional[str] = None
    device_type: Optional[DeviceType] = None
    notes: Optional[str] = None
    is_known: Optional[bool] = None
    is_authorized: Optional[bool] = None


class DeviceResponse(DeviceBase):
    """Device response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_online: bool
    is_known: bool
    is_authorized: bool
    first_seen: datetime
    last_seen: datetime


class DeviceHistoryResponse(BaseModel):
    """Device history entry response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    ip_address: Optional[str] = None
    event_type: str
    timestamp: datetime
    details: Optional[str] = None


class NetworkMapNode(BaseModel):
    """Network map node."""
    id: str  # device id as string
    label: str
    ip: Optional[str] = None
    mac: str
    type: DeviceType
    is_online: bool
    is_authorized: bool
    vendor: Optional[str] = None


class NetworkMapEdge(BaseModel):
    """Network map edge (connection)."""
    source: str
    target: str
    type: str = "ethernet"


class NetworkMapResponse(BaseModel):
    """Network topology map."""
    nodes: List[NetworkMapNode]
    edges: List[NetworkMapEdge]


class NetworkScanRequest(BaseModel):
    """Network scan request."""
    scan_type: str = Field(default="arp", pattern="^(arp|nmap|full)$")
    target_network: Optional[str] = None  # CIDR notation