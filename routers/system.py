from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from core.router_client import RouterClient
from models.system import SystemInfo, GenericResponse

router = APIRouter(prefix="/system", tags=["System & Diagnostics"])

def _dict_from_list(data: Any) -> Dict[str, Any]:
    merged = {}
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                merged.update(item)
    elif isinstance(data, dict):
        merged = data
    return merged

@router.get("/info", response_model=SystemInfo, summary="Get router hardware and software information")
def get_system_info():
    """
    Returns general router system details: firmware version, public IPv4/IPv6,
    subsystem features, and GPON fiber support flags.
    """
    client = RouterClient.get_instance()
    try:
        raw = client.get_data("user_data")
        cfg = _dict_from_list(raw)
        return SystemInfo(
            model="TIM HUB+ (Sercomm AGSGP)",
            firmware_version=cfg.get("fw_version", client.fw_version or "AGSGP_1.0.9"),
            wan_ipv4=cfg.get("wan_ip4_addr", ""),
            wan_ipv6=cfg.get("wan_ip6_addr", None),
            telephony_service=cfg.get("phone_service") == "1",
            gpon_support=cfg.get("gpon_support") == "1",
            gui_locked=cfg.get("gui_locked") == "1",
            capabilities={k: v for k, v in cfg.items() if k.endswith("_support")},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch system info: {str(e)}")

@router.post("/reboot", response_model=GenericResponse, summary="Reboot the modem")
def reboot_router():
    """
    Initiates a hardware reboot cycle of the TIM router.
    The router will take approximately 60-90 seconds to restart and reconnect to the FTTH fiber link.
    """
    client = RouterClient.get_instance()
    try:
        client.post_data("status_and_support", {"restart_device": "1"}, encrypt=False)
        return GenericResponse(
            status="ok",
            message="Router reboot sequence triggered successfully. Expected downtime ~60-90s."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger router reboot: {str(e)}")

@router.post("/reconnect", response_model=GenericResponse, summary="Reconnect WAN fiber link")
def reconnect_wan():
    """
    Forces a renegotiation of the PPPoE / GPON fiber WAN session without a full hardware reboot.
    """
    client = RouterClient.get_instance()
    try:
        client.post_data("status_and_support", {"fiber_reconnect": "1"}, encrypt=False)
        return GenericResponse(
            status="ok",
            message="WAN fiber session renegotiation initiated."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to renegotiate WAN: {str(e)}")
