import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from core.router_client import RouterClient
from models.wan import WanStatus, DmzConfig, DmzUpdateRequest, UpnpConfig, UpnpUpdateRequest, PortForwardRule
from models.system import GenericResponse

router = APIRouter(prefix="/wan", tags=["Internet & Port Forwarding"])

def _dict_from_list(data: Any) -> Dict[str, Any]:
    merged = {}
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                merged.update(item)
    elif isinstance(data, dict):
        merged = data
    return merged

@router.get("/status", response_model=WanStatus, summary="Get WAN connection and public IP status")
def get_wan_status():
    """
    Returns public IPv4 address, IPv6 connectivity, and WAN gateway status.
    """
    client = RouterClient.get_instance()
    try:
        raw = client.get_data("user_data")
        cfg = _dict_from_list(raw)
        return WanStatus(
            connected=bool(cfg.get("wan_ip4_addr")),
            ipv4_address=cfg.get("wan_ip4_addr", ""),
            ipv6_address=cfg.get("wan_ip6_addr", None),
            ipv6_enabled=cfg.get("ipv6_status") == "1",
            connection_type="GPON / Fiber (FTTH)" if cfg.get("gpon_support") == "1" else "DSL/WAN",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query WAN status: {str(e)}")

@router.get("/dmz", response_model=DmzConfig, summary="Get DMZ host settings")
def get_dmz():
    """
    Returns whether DMZ is enabled and which local IP is set as the DMZ host.
    """
    client = RouterClient.get_instance()
    try:
        raw = client.get_data("internet_dmz")
        cfg = _dict_from_list(raw)
        return DmzConfig(
            enabled=cfg.get("dmz_enable") == "1",
            ip_address=cfg.get("dmz_ip", ""),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch DMZ configuration: {str(e)}")

@router.post("/dmz", response_model=GenericResponse, summary="Configure DMZ host")
def update_dmz(req: DmzUpdateRequest):
    """
    Enables or disables DMZ forwarding for a specific local IP host.
    """
    client = RouterClient.get_instance()
    try:
        fields = [
            ("dmz_enable", "1" if req.enabled else "0"),
            ("dmz_ip", req.ip_address or ""),
        ]
        client.post_data("internet_dmz", fields, encrypt=False)
        return GenericResponse(
            status="ok",
            message=f"DMZ successfully {'enabled for ' + req.ip_address if req.enabled else 'disabled'}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update DMZ: {str(e)}")

@router.get("/upnp", response_model=UpnpConfig, summary="Get UPnP IGD status")
def get_upnp():
    """
    Returns whether Universal Plug and Play (UPnP) is active on the router.
    """
    client = RouterClient.get_instance()
    try:
        raw = client.get_data("internet_upnp")
        cfg = _dict_from_list(raw)
        return UpnpConfig(
            enabled=cfg.get("upnp") == "1",
            configurable=cfg.get("configurable", "1") == "1",
            nat_traversal=cfg.get("nat_raversal", "1") == "1",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch UPnP state: {str(e)}")

@router.post("/upnp", response_model=GenericResponse, summary="Toggle UPnP")
def toggle_upnp(req: UpnpUpdateRequest):
    """
    Enables or disables automatic port opening via UPnP IGD.
    """
    client = RouterClient.get_instance()
    try:
        fields = [
            ("upnp", "1" if req.enabled else "0"),
            ("configurable", "1"),
            ("nat_raversal", "1"),
        ]
        client.post_data("internet_upnp", fields, encrypt=False)
        return GenericResponse(
            status="ok",
            message=f"UPnP {'enabled' if req.enabled else 'disabled'} successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle UPnP: {str(e)}")

@router.get("/port-forwarding", response_model=List[PortForwardRule], summary="List active port forwarding rules")
def list_port_forwarding_rules():
    """
    Returns all active NAT virtual server and port forwarding rules.
    """
    client = RouterClient.get_instance()
    try:
        raw = client.get_data("internet_port_mappin")
        rules = []
        if isinstance(raw, list):
            for i, item in enumerate(raw):
                if isinstance(item, dict) and "lan_ip" in item:
                    rules.append(PortForwardRule(
                        id=str(item.get("id", i)),
                        name=item.get("service_name", item.get("name", "CustomRule")),
                        protocol=item.get("protocol", "TCP").upper(),
                        wan_port_start=int(item.get("wan_start_port", item.get("wan_port", 0))),
                        wan_port_end=int(item.get("wan_end_port", 0)) if item.get("wan_end_port") else None,
                        lan_ip=item.get("lan_ip", ""),
                        lan_port_start=int(item.get("lan_start_port", item.get("lan_port", 0))),
                        lan_port_end=int(item.get("lan_end_port", 0)) if item.get("lan_end_port") else None,
                        enabled=item.get("enable", "1") == "1",
                    ))
        return rules
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch port forwarding rules: {str(e)}")

@router.post("/port-forwarding", response_model=GenericResponse, summary="Add a port forwarding rule")
def add_port_forwarding_rule(rule: PortForwardRule):
    """
    Creates a new NAT port forwarding rule mapping external WAN traffic to an internal host.
    """
    client = RouterClient.get_instance()
    try:
        raw = client.get_data("internet_port_mappin")
        rule_list = raw if isinstance(raw, list) else []

        new_entry = {
            "name": rule.name,
            "protocol": rule.protocol.lower(),
            "wan_start_port": str(rule.wan_port_start),
            "wan_end_port": str(rule.wan_port_end or rule.wan_port_start),
            "lan_ip": rule.lan_ip,
            "lan_start_port": str(rule.lan_port_start),
            "lan_end_port": str(rule.lan_port_end or rule.lan_port_start),
            "enable": "1" if rule.enabled else "0",
        }
        rule_list.append(new_entry)

        client.post_data("internet_port_mappin", {"port_mapping_list": json.dumps(rule_list)}, encrypt=False)
        return GenericResponse(
            status="ok",
            message=f"Port forwarding rule '{rule.name}' for {rule.lan_ip}:{rule.lan_port_start} applied"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add port forwarding rule: {str(e)}")
