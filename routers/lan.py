import json
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from core.router_client import RouterClient
from models.lan import LanSettings, LanSettingsUpdateRequest, StaticLease
from models.system import GenericResponse

router = APIRouter(prefix="/lan", tags=["LAN & DHCP Configuration"])

def _get_primary_lan(data: Any) -> Dict[str, Any]:
    if isinstance(data, list):
        # Look for primary subnet 0
        for item in data:
            if isinstance(item, dict) and item.get("subnet") == "0":
                return item
        for item in data:
            if isinstance(item, dict) and "LanIP" in item:
                return item
    elif isinstance(data, dict):
        return data
    return {}

@router.get("/settings", response_model=LanSettings, summary="Get LAN and DHCP server settings")
def get_lan_settings():
    """
    Returns the router's internal IPv4 address, subnet mask, DHCP server pool range,
    lease duration, and DNS servers advertised to clients.
    """
    client = RouterClient.get_instance()
    try:
        raw = client.get_data("settings_lan")
        cfg = _get_primary_lan(raw)
        return LanSettings(
            router_ip=cfg.get("LanIP", "192.168.1.1"),
            subnet_mask=cfg.get("LanSubnetMask", "255.255.255.0"),
            domain_name=cfg.get("LanDHCPDomainName", "homenet.telecomitalia.it"),
            dhcp_enabled=cfg.get("LanDHCP") == "1",
            dhcp_start_ip=cfg.get("LanDHCPStartIP", "192.168.1.2"),
            dhcp_end_ip=cfg.get("LanDHCPEndIP", "192.168.1.254"),
            lease_time_seconds=cfg.get("LanDHCPLeaseTime", "509020"),
            dns_server=cfg.get("LanDNSServer", "192.168.1.1"),
            dns_proxy_enabled=cfg.get("LanDNSProxy") == "1",
            ipv6_dhcp_server=cfg.get("ip6_dhcp_server") == "1",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch LAN settings: {str(e)}")

@router.post("/settings", response_model=GenericResponse, summary="Update LAN & DHCP settings")
def update_lan_settings(req: LanSettingsUpdateRequest):
    """
    Modifies local IP, DHCP address pool, and custom DNS servers advertised to all devices on the network.
    """
    client = RouterClient.get_instance()
    try:
        raw = client.get_data("settings_lan")
        curr = _get_primary_lan(raw)

        router_ip = req.router_ip or curr.get("LanIP", "192.168.1.1")
        mask = req.subnet_mask or curr.get("LanSubnetMask", "255.255.255.0")
        dhcp_on = "1" if req.dhcp_enabled else ("0" if req.dhcp_enabled is False else curr.get("LanDHCP", "1"))
        start_ip = req.dhcp_start_ip or curr.get("LanDHCPStartIP", "192.168.1.2")
        end_ip = req.dhcp_end_ip or curr.get("LanDHCPEndIP", "192.168.1.254")
        dns_serv = req.dns_server or curr.get("LanDNSServer", "192.168.1.1")
        dns_proxy = "1" if req.dns_proxy_enabled else ("0" if req.dns_proxy_enabled is False else curr.get("LanDNSProxy", "1"))

        fields = [
            ("LanIP", router_ip),
            ("LanSubnetMask", mask),
            ("LanHostName", curr.get("LanHostName", "TIM")),
            ("LanDHCP", dhcp_on),
            ("LanDHCPStartIP", start_ip),
            ("LanDHCPEndIP", end_ip),
            ("LanDHCPLeaseTime", curr.get("LanDHCPLeaseTime", "509020")),
            ("LanDHCPDomainName", curr.get("LanDHCPDomainName", "homenet.telecomitalia.it")),
            ("LanDNSServer", dns_serv),
            ("LanDNSProxy", dns_proxy),
            ("ip6_dhcp_server", curr.get("ip6_dhcp_server", "1")),
            ("ip6_router_advertisement", curr.get("ip6_router_advertisement", "1")),
        ]

        client.post_data("settings_lan", fields, encrypt=False)
        return GenericResponse(status="ok", message="LAN and DHCP configuration updated successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update LAN settings: {str(e)}")

@router.get("/static-leases", response_model=List[StaticLease], summary="List static DHCP IP reservations")
def list_static_leases():
    """
    Returns all configured static IP address bindings (MAC to IP).
    """
    client = RouterClient.get_instance()
    try:
        raw = client.get_data("settings_lan_staticdhcp")
        leases = []
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, dict) and "staticdhcp_mac" in item:
                    leases.append(StaticLease(
                        name=item.get("staticdhcp_name", "Unknown"),
                        mac=item.get("staticdhcp_mac", ""),
                        ip=item.get("staticdhcp_ip", ""),
                    ))
        return leases
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch static DHCP reservations: {str(e)}")

@router.post("/static-leases", response_model=GenericResponse, summary="Add or update a static DHCP lease")
def add_static_lease(lease: StaticLease):
    """
    Assigns a fixed IP address reservation for a device given its MAC address.
    """
    client = RouterClient.get_instance()
    try:
        raw = client.get_data("settings_lan_staticdhcp")
        current_list = []
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, dict) and "staticdhcp_mac" in item:
                    # Filter out if updating existing MAC
                    if item.get("staticdhcp_mac", "").lower() != lease.mac.lower():
                        current_list.append(item)

        current_list.append({
            "staticdhcp_name": lease.name,
            "staticdhcp_mac": lease.mac.upper(),
            "staticdhcp_ip": lease.ip,
        })

        client.post_data("settings_lan", {"LanStaticDHCPList": json.dumps(current_list)}, encrypt=False)
        return GenericResponse(status="ok", message=f"Static DHCP lease for {lease.name} ({lease.mac} -> {lease.ip}) saved")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add static DHCP lease: {str(e)}")

@router.delete("/static-leases/{mac_address}", response_model=GenericResponse, summary="Delete a static DHCP lease")
def delete_static_lease(mac_address: str):
    """
    Deletes an existing static IP reservation by MAC address.
    """
    client = RouterClient.get_instance()
    try:
        raw = client.get_data("settings_lan_staticdhcp")
        new_list = []
        found = False
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, dict) and "staticdhcp_mac" in item:
                    if item.get("staticdhcp_mac", "").lower() == mac_address.lower():
                        found = True
                    else:
                        new_list.append(item)

        if not found:
            raise HTTPException(status_code=404, detail=f"Static lease with MAC {mac_address} not found")

        client.post_data("settings_lan", {"LanStaticDHCPList": json.dumps(new_list)}, encrypt=False)
        return GenericResponse(status="ok", message=f"Static lease for MAC {mac_address} removed")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete static lease: {str(e)}")
