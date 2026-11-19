#!/usr/bin/env python3
"""
TIM Router Wi-Fi & Configuration Watchdog.
Ensures critical network settings (5GHz DFS Channel 104, Band Steering OFF, Guest Network OFF, WPA2)
persist permanently and are automatically restored if reset by overnight router sweeps or reboots.
"""
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.router_client import RouterClient
from routers.wifi import _dict_from_router_list

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("RouterWatchdog")

TARGET_5G_CHANNEL = "104"
TARGET_BAND_STEERING = "0"
TARGET_GUEST_24G = "0"
TARGET_GUEST_5G = "0"
TARGET_SECURITY_5G = "wpa2"

def check_and_enforce():
    client = RouterClient.get_instance()
    try:
        client.login()
    except Exception as e:
        logger.warning(f"Could not connect to router (another session may be active): {e}")
        return

    try:
        raw = client.get_data("wifi_general")
        cfg = _dict_from_router_list(raw)

        curr_channel_5g = cfg.get("wifi_channel_5g", "")
        curr_band_steering = cfg.get("band_steering_enable", "")
        curr_guest_24g = cfg.get("wifi_network_onoff_guest", "")
        curr_guest_5g = cfg.get("wifi_network_onoff_5g_guest", "")
        curr_sec_5g = cfg.get("wifi_protection_5g", "")

        needs_fix = False
        reasons = []

        if curr_channel_5g != TARGET_5G_CHANNEL:
            needs_fix = True
            reasons.append(f"5G channel is '{curr_channel_5g}' (target: {TARGET_5G_CHANNEL})")

        if curr_band_steering != TARGET_BAND_STEERING:
            needs_fix = True
            reasons.append(f"Band steering is '{curr_band_steering}' (target: {TARGET_BAND_STEERING})")

        if curr_guest_24g != TARGET_GUEST_24G:
            needs_fix = True
            reasons.append(f"Guest 2.4G is '{curr_guest_24g}' (target: {TARGET_GUEST_24G})")

        if curr_guest_5g != TARGET_GUEST_5G:
            needs_fix = True
            reasons.append(f"Guest 5G is '{curr_guest_5g}' (target: {TARGET_GUEST_5G})")

        if curr_sec_5g != TARGET_SECURITY_5G:
            needs_fix = True
            reasons.append(f"5G security is '{curr_sec_5g}' (target: {TARGET_SECURITY_5G})")

        if not needs_fix:
            logger.info("Router configuration verified. All parameters are optimal.")
            return

        logger.warning(f"Configuration drift detected: {'; '.join(reasons)}. Enforcing optimal settings...")

        fields = [
            ("radio_2_enable", "1"),
            ("radio_5_enable", "1"),
            ("band_steering_enable", TARGET_BAND_STEERING),
            ("wifi_network_onoff", cfg.get("wifi_network_onoff", "1")),
            ("wifi_network_onoff_5g", cfg.get("wifi_network_onoff_5g", "1")),
            ("wifi_network_onoff_guest", TARGET_GUEST_24G),
            ("wifi_network_onoff_5g_guest", TARGET_GUEST_5G),
            ("wifi_ssid", cfg.get("wifi_ssid", "TIM-94356824")),
            ("wifi_channel", cfg.get("wifi_channel", "auto")),
            ("wifi_broadcast_ssid", cfg.get("wifi_broadcast_ssid", "1")),
            ("wifi_password", cfg.get("wifi_password", "")),
            ("wifi_protection", cfg.get("wifi_protection", "wpa2")),
            ("wifi_enable_optimization", cfg.get("wifi_enable_optimization", "0")),
            ("wifi_ssid_5g", cfg.get("wifi_ssid_5g", "TIM-94356824_5G")),
            ("wifi_channel_5g", TARGET_5G_CHANNEL),
            ("wifi_broadcast_ssid_5g", cfg.get("wifi_broadcast_ssid_5g", "1")),
            ("wifi_password_5g", cfg.get("wifi_password_5g", "")),
            ("wifi_protection_5g", TARGET_SECURITY_5G),
            ("wifi_enable_optimization_5g", "1"),
        ]

        client.post_data("wifi_general", fields, encrypt=True)
        logger.info("Optimal router configuration successfully restored and committed.")

    except Exception as e:
        logger.error(f"Error during watchdog evaluation: {e}")
    finally:
        client.logout()

if __name__ == "__main__":
    check_and_enforce()
