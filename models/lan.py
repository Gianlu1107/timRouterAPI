from typing import Optional, List
from pydantic import BaseModel, Field

class StaticLease(BaseModel):
    name: str = Field(..., description="Device friendly name (e.g. 'Proxmox-Server')")
    mac: str = Field(..., description="Hardware MAC address (e.g. '7c:d3:0a:24:cb:84')")
    ip: str = Field(..., description="Static reserved IP address (e.g. '192.168.1.80')")

class LanSettings(BaseModel):
    router_ip: str = Field("192.168.1.1", description="Local IP address of the gateway router")
    subnet_mask: str = Field("255.255.255.0", description="LAN Subnet Mask")
    domain_name: str = Field("homenet.telecomitalia.it", description="LAN Local Domain Name")
    dhcp_enabled: bool = Field(True, description="Whether the built-in DHCP server is active")
    dhcp_start_ip: str = Field("192.168.1.2", description="Start of DHCP IP pool")
    dhcp_end_ip: str = Field("192.168.1.254", description="End of DHCP IP pool")
    lease_time_seconds: str = Field("509020", description="DHCP lease time in seconds")
    dns_server: str = Field("192.168.1.1", description="DNS Server advertised to DHCP clients")
    dns_proxy_enabled: bool = Field(True, description="Whether the router acts as a local DNS proxy")
    ipv6_dhcp_server: bool = Field(True, description="IPv6 stateful DHCPv6 server active")

class LanSettingsUpdateRequest(BaseModel):
    router_ip: Optional[str] = Field(None, description="Router LAN IP (default: 192.168.1.1)")
    subnet_mask: Optional[str] = Field(None, description="Subnet Mask")
    dhcp_enabled: Optional[bool] = Field(None, description="Enable or disable DHCP server")
    dhcp_start_ip: Optional[str] = Field(None, description="DHCP range start")
    dhcp_end_ip: Optional[str] = Field(None, description="DHCP range end")
    dns_server: Optional[str] = Field(None, description="Custom DNS advertised via DHCP (e.g. '1.1.1.1')")
    dns_proxy_enabled: Optional[bool] = Field(None, description="Enable or disable internal DNS proxying")
