from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status
from core.router_client import RouterClient
from models.wifi import (
    WifiOverview,
    WifiRadio,
    WifiGuestRadio,
    WifiGeneralUpdateRequest,
    WifiGuestUpdateRequest,
    WifiAdvancedSettings,
    WifiBandSteeringToggle,
    WifiRestartResponse,
)
from models.system import GenericResponse

router = APIRouter(prefix="/wifi", tags=["Wi-Fi Management"])

def _dict_from_router_list(data: Any) -> Dict[str, Any]:
    merged = {}
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                merged.update(item)
    elif isinstance(data, dict):
        merged = data
    return merged

@router.get("", response_model=WifiOverview, summary="Get full Wi-Fi status and radios")
def get_wifi_overview():
    """
    Retrieves the complete state of the 2.4 GHz and 5 GHz primary and guest wireless networks,
    including current active channel, bandwidth, encryption type, and Band Steering status.
    """
    client = RouterClient.get_instance()
    try:
        raw_data = client.get_data("wifi_general")
        cfg = _dict_from_router_list(raw_data)

        # 2.4 GHz Primary
        radio_24g = WifiRadio(
            enabled=cfg.get("wifi_network_onoff") == "1",
            frequency="2.4GHz",
            ssid=cfg.get("wifi_ssid", "TIM-94356824"),
            channel=cfg.get("wifi_channel", "auto"),
            current_channel=cfg.get("wifi_now_channel", "1"),
            bandwidth=cfg.get("wifi_now_bandwidth", "573") + " Mbps",
            broadcast_ssid=cfg.get("wifi_broadcast_ssid") == "1",
            security_mode=cfg.get("wifi_protection", "wpa2"),
            password=cfg.get("wifi_password", "********"),
            wifi7_optimization=cfg.get("wifi_enable_optimization") == "1",
        )

        # 5 GHz Primary
        radio_5g = WifiRadio(
            enabled=cfg.get("wifi_network_onoff_5g") == "1",
            frequency="5GHz",
            ssid=cfg.get("wifi_ssid_5g", "TIM-94356824_5G"),
            channel=cfg.get("wifi_channel_5g", "auto"),
            current_channel=cfg.get("wifi_now_channel_5g", "48"),
            bandwidth=cfg.get("wifi_now_bandwidth_5g", "2880") + " Mbps",
            broadcast_ssid=cfg.get("wifi_broadcast_ssid_5g") == "1",
            security_mode=cfg.get("wifi_protection_5g", "wpa2wpa3"),
            password=cfg.get("wifi_password_5g", "********"),
            wifi7_optimization=cfg.get("wifi_enable_optimization_5g") == "1",
        )

        # 2.4 GHz Guest
        guest_24g = WifiGuestRadio(
            enabled=cfg.get("wifi_network_onoff_guest") == "1",
            ssid=cfg.get("wifi_ssid_guest", "TIM-Guest"),
            password=cfg.get("wifi_password_guest", "********"),
            security_mode=cfg.get("wifi_protection_guest", "wpa2"),
            allow_services=cfg.get("wifi_allow_guest", "All services"),
            limited_time=cfg.get("wifi_limited_time_guest", "None"),
            channel=cfg.get("wifi_channel_guest", "auto"),
        )

        # 5 GHz Guest
        guest_5g = WifiGuestRadio(
            enabled=cfg.get("wifi_network_onoff_5g_guest") == "1",
            ssid=cfg.get("wifi_ssid_5g_guest", "TIM-Guest-5G"),
            password=cfg.get("wifi_password_5g_guest", "********"),
            security_mode=cfg.get("wifi_protection_5g_guest", "wpa2"),
            allow_services=cfg.get("wifi_allow_5g_guest", "All services"),
            limited_time=cfg.get("wifi_limited_time_5g_guest", "None"),
            channel=cfg.get("wifi_channel_5g_guest", "auto"),
        )

        return WifiOverview(
            band_steering_enabled=cfg.get("band_steering_enable") == "1",
            radio_24g=radio_24g,
            radio_5g=radio_5g,
            guest_24g=guest_24g,
            guest_5g=guest_5g,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query Wi-Fi status: {str(e)}")

@router.post("/general", response_model=GenericResponse, summary="Update primary Wi-Fi parameters")
def update_wifi_general(req: WifiGeneralUpdateRequest):
    """
    Updates the primary Wi-Fi parameters (SSID, password, channels, band steering).
    Any omitted field preserves its current active value.
    Payload is automatically encrypted with SJCL AES-CCM before dispatching to the router.
    """
    client = RouterClient.get_instance()
    try:
        # Load current config to avoid overwriting unmentioned fields
        raw_current = client.get_data("wifi_general")
        curr = _dict_from_router_list(raw_current)

        # Compute new values
        band_steering = "1" if req.band_steering_enabled else ("0" if req.band_steering_enabled is False else curr.get("band_steering_enable", "0"))
        on_24g = "1" if req.radio_24g_enabled else ("0" if req.radio_24g_enabled is False else curr.get("wifi_network_onoff", "1"))
        on_5g = "1" if req.radio_5g_enabled else ("0" if req.radio_5g_enabled is False else curr.get("wifi_network_onoff_5g", "1"))
        guest_24g = curr.get("wifi_network_onoff_guest", "0")
        guest_5g = curr.get("wifi_network_onoff_5g_guest", "0")

        ssid_24 = req.ssid_24g or curr.get("wifi_ssid", "TIM-Network")
        pw_24 = req.password_24g or curr.get("wifi_password", "")
        ch_24 = req.channel_24g or curr.get("wifi_channel", "auto")
        bcast_24 = "1" if req.broadcast_ssid_24g is not False else "0"

        ssid_5 = req.ssid_5g or curr.get("wifi_ssid_5g", "TIM-Network_5G")
        pw_5 = req.password_5g or curr.get("wifi_password_5g", "")
        ch_5 = req.channel_5g or curr.get("wifi_channel_5g", "auto")
        bcast_5 = "1" if req.broadcast_ssid_5g is not False else "0"
        sec_5 = req.security_5g or curr.get("wifi_protection_5g", "wpa2wpa3")

        fields = [
            ("radio_2_enable", "1"),
            ("radio_5_enable", "1"),
            ("band_steering_enable", band_steering),
            ("wifi_network_onoff", on_24g),
            ("wifi_network_onoff_5g", on_5g),
            ("wifi_network_onoff_guest", guest_24g),
            ("wifi_network_onoff_5g_guest", guest_5g),
            ("wifi_ssid", ssid_24),
            ("wifi_channel", ch_24),
            ("wifi_broadcast_ssid", bcast_24),
            ("wifi_password", pw_24),
            ("wifi_protection", curr.get("wifi_protection", "wpa2")),
            ("wifi_enable_optimization", curr.get("wifi_enable_optimization", "0")),
            ("wifi_ssid_5g", ssid_5),
            ("wifi_channel_5g", ch_5),
            ("wifi_broadcast_ssid_5g", bcast_5),
            ("wifi_password_5g", pw_5),
            ("wifi_protection_5g", sec_5),
            ("wifi_enable_optimization_5g", curr.get("wifi_enable_optimization_5g", "1")),
        ]

        client.post_data("wifi_general", fields, encrypt=True)
        return GenericResponse(status="ok", message="Wi-Fi general settings successfully applied to router")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update Wi-Fi configuration: {str(e)}")

@router.post("/guest", response_model=GenericResponse, summary="Configure or disable guest Wi-Fi")
def update_wifi_guest(req: WifiGuestUpdateRequest):
    """
    Enables, disables, or updates credentials for the Guest Wi-Fi networks (2.4G & 5G).
    Set enabled_24g=false and enabled_5g=false to completely deactivate guest Wi-Fi.
    """
    client = RouterClient.get_instance()
    try:
        raw_current = client.get_data("wifi_general")
        curr = _dict_from_router_list(raw_current)

        guest_24_on = "1" if req.enabled_24g else ("0" if req.enabled_24g is False else curr.get("wifi_network_onoff_guest", "0"))
        guest_5_on = "1" if req.enabled_5g else ("0" if req.enabled_5g is False else curr.get("wifi_network_onoff_5g_guest", "0"))

        fields = [
            ("radio_2_enable", curr.get("radio_2_enable", "1")),
            ("radio_5_enable", curr.get("radio_5_enable", "1")),
            ("band_steering_enable", curr.get("band_steering_enable", "0")),
            ("wifi_network_onoff", curr.get("wifi_network_onoff", "1")),
            ("wifi_network_onoff_5g", curr.get("wifi_network_onoff_5g", "1")),
            ("wifi_network_onoff_guest", guest_24_on),
            ("wifi_network_onoff_5g_guest", guest_5_on),
            ("wifi_ssid", curr.get("wifi_ssid", "TIM-94356824")),
            ("wifi_channel", curr.get("wifi_channel", "auto")),
            ("wifi_broadcast_ssid", curr.get("wifi_broadcast_ssid", "1")),
            ("wifi_password", curr.get("wifi_password", "")),
            ("wifi_protection", curr.get("wifi_protection", "wpa2")),
            ("wifi_enable_optimization", curr.get("wifi_enable_optimization", "0")),
            ("wifi_ssid_5g", curr.get("wifi_ssid_5g", "TIM-Network_5G")),
            ("wifi_channel_5g", curr.get("wifi_channel_5g", "auto")),
            ("wifi_broadcast_ssid_5g", curr.get("wifi_broadcast_ssid_5g", "1")),
            ("wifi_password_5g", curr.get("wifi_password_5g", "")),
            ("wifi_protection_5g", curr.get("wifi_protection_5g", "wpa2wpa3")),
            ("wifi_enable_optimization_5g", curr.get("wifi_enable_optimization_5g", "1")),
        ]

        if guest_24_on == "1":
            fields.extend([
                ("wifi_ssid_guest", req.ssid_24g or curr.get("wifi_ssid_guest", "TIM-Guest")),
                ("wifi_password_guest", req.password_24g or curr.get("wifi_password_guest", "")),
                ("wifi_broadcast_ssid_guest", "1"),
                ("wifi_protection_guest", "wpa2"),
                ("wifi_allow_guest", "All services"),
                ("wifi_limited_time_guest", "None"),
            ])

        if guest_5_on == "1":
            fields.extend([
                ("wifi_ssid_5g_guest", req.ssid_5g or curr.get("wifi_ssid_5g_guest", "TIM-Guest-5G")),
                ("wifi_password_5g_guest", req.password_5g or curr.get("wifi_password_5g_guest", "")),
                ("wifi_broadcast_ssid_5g_guest", "1"),
                ("wifi_protection_5g_guest", "wpa2"),
                ("wifi_allow_5g_guest", "All services"),
                ("wifi_limited_time_5g_guest", "None"),
            ])

        client.post_data("wifi_general", fields, encrypt=True)
        return GenericResponse(
            status="ok",
            message=f"Guest network state updated (2.4G={'ON' if guest_24_on == '1' else 'OFF'}, 5G={'ON' if guest_5_on == '1' else 'OFF'})"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update Guest Wi-Fi: {str(e)}")

@router.get("/settings", response_model=WifiAdvancedSettings, summary="Get advanced radio options")
def get_wifi_settings():
    """
    Returns advanced RF configurations: 802.11 modes, channel bandwidths (up to 160MHz),
    and channel reselection intervals.
    """
    client = RouterClient.get_instance()
    try:
        raw = client.get_data("wifi_settings")
        cfg = _dict_from_router_list(raw)
        return WifiAdvancedSettings(
            wifi_mode_24g=cfg.get("wifi-mode", "n-only"),
            bandwidth_24g=cfg.get("bandwidth", "20MHz"),
            wmm_enabled_24g=cfg.get("wmm_enabled") == "1",
            auto_channel_interval_24g=cfg.get("auto_channel_reselection_interval", "86400"),
            wifi_mode_5g=cfg.get("wifi-mode_5g", "be"),
            bandwidth_5g=cfg.get("bandwidth_5g", "20MHz_40MHz_80MHz_auto"),
            wmm_enabled_5g=cfg.get("wmm_enabled_5g") == "1",
            auto_channel_interval_5g=cfg.get("auto_channel_reselection_interval_5g", "86400"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch advanced Wi-Fi settings: {str(e)}")

@router.post("/band-steering", response_model=GenericResponse, summary="Toggle Band Steering")
def toggle_band_steering(req: WifiBandSteeringToggle):
    """
    Quick endpoint to turn Band Steering (BSD) ON or OFF.
    Note: For Band Steering to work reliably, 2.4G and 5G should share the same SSID.
    """
    client = RouterClient.get_instance()
    try:
        raw_current = client.get_data("wifi_general")
        curr = _dict_from_router_list(raw_current)

        fields = [
            ("radio_2_enable", curr.get("radio_2_enable", "1")),
            ("radio_5_enable", curr.get("radio_5_enable", "1")),
            ("band_steering_enable", "1" if req.enabled else "0"),
            ("wifi_network_onoff", curr.get("wifi_network_onoff", "1")),
            ("wifi_network_onoff_5g", curr.get("wifi_network_onoff_5g", "1")),
            ("wifi_network_onoff_guest", curr.get("wifi_network_onoff_guest", "0")),
            ("wifi_network_onoff_5g_guest", curr.get("wifi_network_onoff_5g_guest", "0")),
            ("wifi_ssid", curr.get("wifi_ssid", "TIM-Network")),
            ("wifi_channel", curr.get("wifi_channel", "auto")),
            ("wifi_broadcast_ssid", curr.get("wifi_broadcast_ssid", "1")),
            ("wifi_password", curr.get("wifi_password", "")),
            ("wifi_protection", curr.get("wifi_protection", "wpa2")),
            ("wifi_enable_optimization", curr.get("wifi_enable_optimization", "0")),
            ("wifi_ssid_5g", curr.get("wifi_ssid_5g", "TIM-Network_5G")),
            ("wifi_channel_5g", curr.get("wifi_channel_5g", "auto")),
            ("wifi_broadcast_ssid_5g", curr.get("wifi_broadcast_ssid_5g", "1")),
            ("wifi_password_5g", curr.get("wifi_password_5g", "")),
            ("wifi_protection_5g", curr.get("wifi_protection_5g", "wpa2wpa3")),
            ("wifi_enable_optimization_5g", curr.get("wifi_enable_optimization_5g", "1")),
        ]

        client.post_data("wifi_general", fields, encrypt=True)
        return GenericResponse(
            status="ok",
            message=f"Band Steering successfully {'enabled' if req.enabled else 'disabled'}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle Band Steering: {str(e)}")

@router.post("/restart", response_model=WifiRestartResponse, summary="Restart Wi-Fi radios")
def restart_wifi_radios():
    """
    Commands the router to soft-restart its wireless chipsets and hostapd daemon.
    Takes approximately 5-10 seconds to re-initialize wireless links.
    """
    client = RouterClient.get_instance()
    try:
        client.post_data("wifi_general", {"wifi_start": "1"}, encrypt=False)
        return WifiRestartResponse(status="ok", message="Wi-Fi subsystem reload initiated")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restart Wi-Fi: {str(e)}")
