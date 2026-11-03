"""
Network schemas.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class NetworkStatusResponse(BaseModel):
    """Network status response."""
    is_scanning: bool
    last_scan: Optional[datetime] = None
    devices_online: int
    devices_total: int
    devices_unknown: int
    scan_interval_minutes: int


class ServiceInfo(BaseModel):
    """Service/port information."""
    port: int
    protocol: str
    service: str
    version: Optional[str] = None
    state: str


class ServiceScanResponse(BaseModel):
    """Service scan results for a device."""
    device_id: int
    ip_address: str
    services: List[ServiceInfo]
    scanned_at: datetime


class ScanHistoryEntry(BaseModel):
    """Network scan history entry."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    scan_type: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    devices_found: int
    new_devices: int
    status: str


class ScanHistoryResponse(BaseModel):
    """Scan history response."""
    scans: List[ScanHistoryEntry]
    total: int


class NetworkTopologyNode(BaseModel):
    """Network topology node."""
    id: str
    label: str
    ip: Optional[str] = None
    mac: str
    device_type: str
    is_online: bool
    is_authorized: bool
    vendor: Optional[str] = None


class NetworkTopologyEdge(BaseModel):
    """Network topology edge."""
    source: str
    target: str
    type: str = "ethernet"


class NetworkTopologyResponse(BaseModel):
    """Network topology response."""
    nodes: List[NetworkTopologyNode]
    edges: List[NetworkTopologyEdge]