from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class SystemInfo(BaseModel):
    model: str = Field("TIM HUB+ (Sercomm AGSGP)", description="Router hardware model")
    firmware_version: str = Field(..., description="Running firmware version")
    wan_ipv4: Optional[str] = Field(None, description="Public WAN IPv4 address")
    wan_ipv6: Optional[str] = Field(None, description="Public WAN IPv6 address")
    telephony_service: bool = Field(True, description="VoIP telephony subsystem active")
    gpon_support: bool = Field(True, description="GPON fiber optics integrated support")
    uptime_seconds: Optional[int] = Field(None, description="Router uptime in seconds")
    gui_locked: bool = Field(False, description="Whether web GUI is in locked state")
    capabilities: Dict[str, Any] = Field(default_factory=dict, description="Router hardware feature flags")

class GenericResponse(BaseModel):
    status: str = Field("ok", description="Status code ('ok' or 'error')")
    message: str = Field(..., description="Detailed result message")
