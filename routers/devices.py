import re
import subprocess
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from core.router_client import RouterClient
from models.devices import NetworkDevice

router = APIRouter(prefix="/devices", tags=["Connected Devices"])

def _get_local_arp() -> Dict[str, str]:
    """Fallback helper to inspect ARP cache for IP/MAC mapping"""
    arp_map = {}
    try:
        out = subprocess.check_output(["arp", "-a"], encoding="utf-8", errors="replace")
        for line in out.splitlines():
            # ? (192.168.1.80) at 7c:d3:a:24:cb:84 on en0
            m = re.search(r"\((192\.168\.\d+\.\d+)\)\s+at\s+([0-9a-fA-F:]+)", line)
            if m:
                ip, mac = m.groups()
                arp_map[ip] = mac.lower()
    except Exception:
        pass
    return arp_map

@router.get("", response_model=List[NetworkDevice], summary="List all connected network devices")
def get_connected_devices():
    """
    Returns a unified inventory of devices currently communicating on the LAN and Wi-Fi,
    including their hostname, assigned IPv4, MAC address, and connection interface.
    """
    client = RouterClient.get_instance()
    devices = []
    seen_macs = set()

    try:
        raw = client.get_data("settings_lan_device")
        if isinstance(raw, list):
            for d in raw:
                if isinstance(d, dict) and "device_ip" in d:
                    mac = d.get("device_mac", "").lower()
                    if mac:
                        seen_macs.add(mac)
                    devices.append(NetworkDevice(
                        hostname=d.get("device_name", "Unknown-Host"),
                        ip_address=d.get("device_ip", ""),
                        mac_address=mac or "N/A",
                        interface=d.get("device_type", "Ethernet"),
                        status="online" if d.get("device_status", "1") == "1" else "offline",
                        rssi=int(d["device_rssi"]) if d.get("device_rssi") else None,
                        speed_mbps=float(d["device_speed"]) if d.get("device_speed") else None,
                        lease_type="Static" if d.get("static") == "1" else "DHCP",
                    ))

        # Check static leases to complement any offline/static devices
        raw_static = client.get_data("settings_lan_staticdhcp")
        if isinstance(raw_static, list):
            for s in raw_static:
                if isinstance(s, dict) and "staticdhcp_mac" in s:
                    mac = s.get("staticdhcp_mac", "").lower()
                    if mac not in seen_macs:
                        seen_macs.add(mac)
                        devices.append(NetworkDevice(
                            hostname=s.get("staticdhcp_name", "Static-Host"),
                            ip_address=s.get("staticdhcp_ip", ""),
                            mac_address=mac,
                            interface="Ethernet",
                            status="configured",
                            lease_type="Static",
                        ))

        # Augment with local ARP table if router list was empty
        if not devices:
            arp = _get_local_arp()
            for ip, mac in arp.items():
                devices.append(NetworkDevice(
                    hostname=f"Host-{ip.split('.')[-1]}",
                    ip_address=ip,
                    mac_address=mac,
                    interface="LAN",
                    status="online",
                    lease_type="DHCP",
                ))

        return devices

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve network devices: {str(e)}")
