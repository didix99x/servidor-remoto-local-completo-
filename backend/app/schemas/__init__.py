# schemas package
from app.schemas.auth import *
from app.schemas.device import *
from app.schemas.share import *
from app.schemas.media import *
from app.schemas.network import *
from app.schemas.security import *
from app.schemas.settings import *
from app.schemas.computing import *

__all__ = [
    # auth
    "LoginRequest", "RegisterRequest", "Token", "TokenPayload", "UserResponse", "UserCreate", "UserUpdate", "ChangePasswordRequest",
    # device
    "DeviceResponse", "DeviceUpdate", "DeviceHistoryResponse", "PairingRequestCreate", "PairingRequestResponse",
    # share
    "ShareCreate", "ShareUpdate", "ShareResponse", "ShareContentResponse", "SharePermissionCreate", "SharePermissionResponse",
    "FileUploadResponse", "FileRenameRequest", "DiskUsageResponse",
    # media
    "MediaLibraryResponse", "MediaItemResponse", "StreamRequest", "StreamResponse",
    # network
    "NetworkStatusResponse", "NetworkMapResponse", "ScanResult", "LocalIPResponse",
    # security
    "SecurityOverviewResponse", "AlertResponse", "AuditLogResponse", "ConnectionEventResponse", "PortScanRequest", "PortScanResponse",
    # settings
    "ServerInfoResponse", "SettingResponse", "SettingUpdate",
    # computing
    "SunshineConfigCreate", "SunshineConfigUpdate", "SunshineConfigResponse", "SunshineStatus",
    "StreamingSessionResponse", "StreamingSessionCreate", "StreamingSessionUpdate",
    "DiscoveredAppResponse", "DiscoveredAppCreate", "DiscoveredAppUpdate",
    "StreamUrlRequest", "StreamUrlResponse", "AppLaunchRequest", "AppLaunchResponse",
    "SystemComputingInfo", "GPUInfo", "QualityProfile", "QUALITY_PROFILES", "get_quality_profile",
    "SessionType", "SessionStatus", "VideoEncoder",
]