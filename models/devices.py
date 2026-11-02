from typing import Optional
from pydantic import BaseModel, Field

class NetworkDevice(BaseModel):
    hostname: str = Field(..., description="Device hostname or advertised name")
    ip_address: str = Field(..., description="Current IPv4 address")
    mac_address: str = Field(..., description="Physical MAC address")
    interface: str = Field("Ethernet", description="Connection medium: 'Ethernet', 'Wi-Fi 2.4GHz', or 'Wi-Fi 5GHz'")
    status: str = Field("online", description="Connection status: 'online' or 'offline'")
    rssi: Optional[int] = Field(None, description="Wi-Fi signal strength in dBm (if wireless)")
    speed_mbps: Optional[float] = Field(None, description="Negotiated physical link rate in Mbps")
    lease_type: str = Field("DHCP", description="'DHCP' or 'Static'")
