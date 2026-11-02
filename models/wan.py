from typing import Optional, List
from pydantic import BaseModel, Field

class WanStatus(BaseModel):
    connected: bool = Field(..., description="Whether WAN Internet connection is established")
    ipv4_address: Optional[str] = Field(None, description="Public IPv4 address assigned to the router")
    ipv6_address: Optional[str] = Field(None, description="Public IPv6 prefix/address assigned")
    ipv6_enabled: bool = Field(True, description="Whether IPv6 is operational")
    connection_type: str = Field("GPON/Fiber", description="WAN physical link type")

class DmzConfig(BaseModel):
    enabled: bool = Field(..., description="Whether DMZ host mode is active")
    ip_address: Optional[str] = Field(None, description="Local IP address exposed to DMZ")

class DmzUpdateRequest(BaseModel):
    enabled: bool = Field(..., description="Enable or disable DMZ")
    ip_address: Optional[str] = Field(None, description="Target host IP in LAN")

class UpnpConfig(BaseModel):
    enabled: bool = Field(..., description="Whether UPnP IGD is active")
    configurable: bool = Field(True, description="Allow clients to open ports automatically")
    nat_traversal: bool = Field(True, description="NAT traversal enabled")

class UpnpUpdateRequest(BaseModel):
    enabled: bool = Field(..., description="Enable or disable UPnP IGD")

class PortForwardRule(BaseModel):
    id: Optional[str] = Field(None, description="Rule identifier")
    name: str = Field(..., description="Friendly label for the service (e.g. 'Minecraft', 'SSH')")
    protocol: str = Field("TCP", description="Protocol: 'TCP', 'UDP', or 'BOTH'")
    wan_port_start: int = Field(..., description="External WAN port or start of port range")
    wan_port_end: Optional[int] = Field(None, description="External WAN end of port range")
    lan_ip: str = Field(..., description="Destination internal host IP address")
    lan_port_start: int = Field(..., description="Destination internal port")
    lan_port_end: Optional[int] = Field(None, description="Destination internal end port")
    enabled: bool = Field(True, description="Whether the forwarding rule is active")
