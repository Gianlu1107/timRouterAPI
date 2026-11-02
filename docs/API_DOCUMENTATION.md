# TIM Router API Specification & Reference

`timRouterAPI` is an enterprise-grade REST middleware exposing clean, strongly-typed JSON endpoints for the Sercomm TIM HUB+ router.

---

## Interactive Documentation
When running the server, interactive Swagger and ReDoc documentation are available at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI Schema**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## Base URL
```
http://localhost:8000/api/v1
```

---

## 1. Authentication Endpoints

### 1.1 Get Authentication Status
- **Method**: `GET`
- **Path**: `/api/v1/auth/status`
- **Description**: Returns the current session state and target router host.

#### Response `200 OK`
```json
{
  "authenticated": true,
  "session_id_preview": "2kVKCHjlD7sXZIaP...",
  "router_host": "192.168.1.1",
  "firmware_version": "AGSGP_1.0.9"
}
```

---

### 1.2 Explicit Login / Re-authenticate
- **Method**: `POST`
- **Path**: `/api/v1/auth/login`
- **Description**: Manually authenticate with the router or switch credentials.

#### Request Body
```json
{
  "username": "admin",
  "password": "your_secure_password"
}
```

#### Response `200 OK`
```json
{
  "authenticated": true,
  "session_id_preview": "pyumlhjyQNzINPLQ...",
  "router_host": "192.168.1.1",
  "firmware_version": "AGSGP_1.0.9"
}
```

---

## 2. Wi-Fi Endpoints

### 2.1 Get Complete Wi-Fi Overview
- **Method**: `GET`
- **Path**: `/api/v1/wifi`
- **Description**: Fetches decrypted status for both primary (2.4 GHz, 5 GHz) and guest networks, as well as band steering.

#### Response `200 OK`
```json
{
  "band_steering_enabled": false,
  "radio_24g": {
    "enabled": true,
    "frequency": "2.4GHz",
    "ssid": "TIM-94356824",
    "channel": "auto",
    "current_channel": "11",
    "bandwidth": "20MHz",
    "broadcast_ssid": true,
    "security_mode": "wpa2wpa3",
    "password": null,
    "wifi7_optimization": false
  },
  "radio_5g": {
    "enabled": true,
    "frequency": "5GHz",
    "ssid": "TIM-94356824_5G",
    "channel": "104",
    "current_channel": "104",
    "bandwidth": "160MHz",
    "broadcast_ssid": true,
    "security_mode": "wpa2wpa3",
    "password": null,
    "wifi7_optimization": false
  },
  "guest_24g": {
    "enabled": false,
    "ssid": "Guest_2.4G",
    "password": null,
    "security_mode": "wpa2",
    "allow_services": "All services",
    "limited_time": "None",
    "channel": "auto"
  },
  "guest_5g": {
    "enabled": false,
    "ssid": "Guest_5G",
    "password": null,
    "security_mode": "wpa2",
    "allow_services": "All services",
    "limited_time": "None",
    "channel": "auto"
  }
}
```

---

### 2.2 Update Primary Wi-Fi Settings
- **Method**: `POST`
- **Path**: `/api/v1/wifi/general`
- **Description**: Modifies channels, SSIDs, passwords, or power states. Payload is automatically encrypted using SJCL AES-CCM before dispatch to the router.

#### Request Body
```json
{
  "channel_5g": "104",
  "ssid_5g": "TIM-94356824_5G",
  "band_steering_enabled": false
}
```

#### Response `200 OK`
```json
{
  "success": true,
  "message": "Wi-Fi settings applied successfully"
}
```

---

### 2.3 Toggle Band Steering
- **Method**: `POST`
- **Path**: `/api/v1/wifi/band-steering`
- **Description**: Enables or disables Band Steering (BSD), separating or unifying the 2.4 GHz and 5 GHz networks.

#### Request Body
```json
{
  "enabled": false
}
```

#### Response `200 OK`
```json
{
  "success": true,
  "message": "Band steering successfully disabled"
}
```

---

### 2.4 Update Guest Wi-Fi
- **Method**: `POST`
- **Path**: `/api/v1/wifi/guest`
- **Description**: Enables or disables the isolated guest networks.

#### Request Body
```json
{
  "enabled_24g": false,
  "enabled_5g": false
}
```

#### Response `200 OK`
```json
{
  "success": true,
  "message": "Guest Wi-Fi settings updated successfully"
}
```

---

### 2.5 Restart Wi-Fi Radio Drivers
- **Method**: `POST`
- **Path**: `/api/v1/wifi/restart`
- **Description**: Restarts the router's internal radio drivers without a full system reboot. Useful when applying new frequency plans or channel changes.

#### Response `200 OK`
```json
{
  "success": true,
  "message": "Wi-Fi drivers restart initiated successfully"
}
```

---

## 3. LAN & DHCP Endpoints

### 3.1 Get LAN Settings
- **Method**: `GET`
- **Path**: `/api/v1/lan/settings`
- **Description**: Returns router IP, subnet mask, DHCP pool, and DNS configuration.

#### Response `200 OK`
```json
{
  "router_ip": "192.168.1.1",
  "subnet_mask": "255.255.255.0",
  "domain_name": "homenet.telecomitalia.it",
  "dhcp_enabled": true,
  "dhcp_start_ip": "192.168.1.2",
  "dhcp_end_ip": "192.168.1.254",
  "lease_time_seconds": "509020",
  "dns_server": "192.168.1.1",
  "dns_proxy_enabled": true,
  "ipv6_dhcp_server": true
}
```

---

### 3.2 Update LAN & DHCP Settings
- **Method**: `POST`
- **Path**: `/api/v1/lan/settings`

#### Request Body
```json
{
  "dhcp_start_ip": "192.168.1.50",
  "dhcp_end_ip": "192.168.1.200",
  "dns_server": "1.1.1.1"
}
```

---

### 3.3 List Static DHCP Reservations
- **Method**: `GET`
- **Path**: `/api/v1/lan/static-leases`

#### Response `200 OK`
```json
[
  {
    "mac_address": "00:11:22:33:44:55",
    "ip_address": "192.168.1.100",
    "hostname": "HomeServer"
  }
]
```

---

### 3.4 Add Static DHCP Reservation
- **Method**: `POST`
- **Path**: `/api/v1/lan/static-leases`

#### Request Body
```json
{
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "ip_address": "192.168.1.150",
  "hostname": "NAS-Storage"
}
```

---

### 3.5 Delete Static DHCP Reservation
- **Method**: `DELETE`
- **Path**: `/api/v1/lan/static-leases/{mac_address}`

---

## 4. WAN & Routing Endpoints

### 4.1 Get WAN Status
- **Method**: `GET`
- **Path**: `/api/v1/wan/status`

#### Response `200 OK`
```json
{
  "connected": true,
  "connection_type": "PPPoE",
  "ipv4_address": "79.17.132.196",
  "ipv6_address": "",
  "gateway": "79.17.132.1",
  "dns_primary": "85.38.28.97",
  "dns_secondary": "85.38.28.98",
  "uptime_seconds": null
}
```

---

### 4.2 Get DMZ Configuration
- **Method**: `GET`
- **Path**: `/api/v1/wan/dmz`

#### Response `200 OK`
```json
{
  "enabled": false,
  "ip_address": null
}
```

---

### 4.3 Configure DMZ
- **Method**: `POST`
- **Path**: `/api/v1/wan/dmz`

#### Request Body
```json
{
  "enabled": true,
  "ip_address": "192.168.1.20"
}
```

---

### 4.4 List Port Forwarding Rules
- **Method**: `GET`
- **Path**: `/api/v1/wan/port-forwarding`

#### Response `200 OK`
```json
[
  {
    "id": "1",
    "name": "Web Server",
    "protocol": "TCP",
    "external_port": 80,
    "internal_port": 8080,
    "internal_ip": "192.168.1.50",
    "enabled": true
  }
]
```

---

## 5. Connected Devices & Topology

### 5.1 List All Connected Network Devices
- **Method**: `GET`
- **Path**: `/api/v1/devices`
- **Description**: Merges active ARP tables, DHCP client leases, and wireless station topology. Returns RSSI and link rates for Wi-Fi clients.

#### Response `200 OK`
```json
[
  {
    "hostname": "cloudflared",
    "ip_address": "192.168.1.3",
    "mac_address": "52:54:00:12:34:56",
    "interface": "Ethernet",
    "status": "online",
    "rssi": null,
    "speed_mbps": 1000.0,
    "lease_type": "DHCP"
  },
  {
    "hostname": "MacBook-Pro",
    "ip_address": "192.168.1.189",
    "mac_address": "3C:06:30:4A:BC:DE",
    "interface": "Wi-Fi 5GHz",
    "status": "online",
    "rssi": -48,
    "speed_mbps": 866.7,
    "lease_type": "DHCP"
  }
]
```

---

## 6. System & Hardware Management

### 6.1 Get System Info
- **Method**: `GET`
- **Path**: `/api/v1/system/info`

#### Response `200 OK`
```json
{
  "model": "TIM HUB+ (Sercomm AGSGP)",
  "firmware_version": "AGSGP_1.0.9",
  "wan_ipv4": "79.17.132.196",
  "wan_ipv6": "",
  "telephony_service": true,
  "gpon_support": true,
  "uptime_seconds": null,
  "gui_locked": false,
  "capabilities": {
    "mobile_support": "0",
    "lan_switch_support": "1",
    "usb_print_support": "1",
    "bridge_support": "0",
    "5g_support": "1",
    "gpon_support": "1",
    "dsl_support": "0",
    "phone2_support": "1"
  }
}
```

---

### 6.2 Reboot Router
- **Method**: `POST`
- **Path**: `/api/v1/system/reboot`

#### Response `200 OK`
```json
{
  "success": true,
  "message": "Router reboot command issued successfully. Device will restart in 10-30 seconds."
}
```

---

### 6.3 Reconnect WAN
- **Method**: `POST`
- **Path**: `/api/v1/system/reconnect`

#### Response `200 OK`
```json
{
  "success": true,
  "message": "WAN reconnect requested. Public IP renewal in progress."
}
```
