"""
Audit logging service.
"""
import logging
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """Service for recording and retrieving audit log entries."""

    async def log(
        self,
        db: AsyncSession,
        action: str,
        resource: str,
        user_id: Optional[int] = None,
        device_id: Optional[int] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """Create an audit log entry."""
        entry = AuditLog(
            user_id=user_id,
            device_id=device_id,
            action=action,
            resource=resource,
            details=details,
            ip_address=ip_address,
        )
        db.add(entry)
        await db.flush()
        return entry

    async def get_logs(
        self,
        db: AsyncSession,
        limit: int = 100,
        offset: int = 0,
        user_id: Optional[int] = None,
        device_id: Optional[int] = None,
        action: Optional[str] = None,
    ) -> List[AuditLog]:
        """Get audit logs with optional filtering."""
        query = select(AuditLog).order_by(desc(AuditLog.timestamp))

        if user_id is not None:
            query = query.where(AuditLog.user_id == user_id)
        if device_id is not None:
            query = query.where(AuditLog.device_id == device_id)
        if action is not None:
            query = query.where(AuditLog.action == action)

        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_recent_alerts(
        self,
        db: AsyncSession,
        limit: int = 20,
    ) -> List[AuditLog]:
        """Get recent security-relevant log entries."""
        security_actions = ["login_failed", "unauthorized_access", "new_device", "device_blocked"]
        query = (
            select(AuditLog)
            .where(AuditLog.action.in_(security_actions))
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()


_audit_service: Optional[AuditService] = None


def get_audit_service() -> AuditService:
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService()
    return _audit_service
