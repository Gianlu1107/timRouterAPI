# TIM HUB+ (Sercomm AGSGP) Protocol & Cryptography Reference

This document provides a comprehensive technical reference for the reverse-engineered internal HTTP API of the **TIM HUB+ Sercomm AGSGP** router (firmware `AGSGP_1.0.9`, Sercomm platform `CN=AGCOMBO`).

---

## 1. Web Server Characteristics & Quirks

The router runs a lightweight embedded web server based on **`mini_httpd`** with specific behaviors:

1. **Rejection of HTTP Pipelining / Keep-Alive**:
   - The server often sends `UNKNOWN 400 Bad Request` or falls back to raw `HTTP/0.9` if a single TCP socket attempts multiple sequential keep-alive requests without clean connection teardown.
   - **Resolution**: Use raw TCP socket communication (`socket.socket`) with an explicit `Connection: close` header on every request, closing the socket immediately upon receiving EOF.

2. **Mandatory Request Headers**:
   - Requests lacking realistic browser headers (e.g. `User-Agent: Mozilla/5.0...`, `Accept-Language: it,it-IT;q=0.9,en;q=0.8`) may trigger silent disconnects or `400 Bad Request`.

3. **Session Cookie**:
   - Authentication relies on a cookie named `session_id`.
   - The cookie value is refreshed upon login and during initial navigation to `/overview.html`.

4. **Dynamic CSRF Tokens**:
   - Each HTML page embeds a variable `var csrf_token = '...';`.
   - Every POST or GET to `/data/<endpoint>.json` must include `?csrf_token=<token>` or pass it in the form body (`csrf_token=<token>`).

---

## 2. Authentication Flow

The authentication handshake follows a 5-step sequence:

```mermaid
sequenceDiagram
    participant Client
    participant Router as Sercomm Router (192.168.1.1)

    Client->>Router: GET /login.html
    Router-->>Client: HTML containing `var csrf_token = 'T1';`
    
    Client->>Router: GET /data/user_lang.json?csrf_token=T1
    Router-->>Client: JSON with `encryption_key`, `salt`, `fw_version`
    
    Note over Client: Calculate double HMAC-SHA256 password hash:<br/>hash1 = HMAC-SHA256("$1$SERCOMM$", password)<br/>final_hash = HMAC-SHA256(encryption_key, hash1)
    
    Client->>Router: POST /data/login.json?csrf_token=T1<br/>Body: LoginName=admin&LoginPWD=final_hash
    Router-->>Client: Set-Cookie: session_id=S1
    
    Client->>Router: GET /overview.html (Cookie: session_id=S1)
    Router-->>Client: Set-Cookie: session_id=S2<br/>HTML containing new `var csrf_token = 'T2';`
    
    Note over Client: Authenticated! Use S2 and T2 for all API calls.
```

### Password Hashing Algorithm
1. `hash1 = HMAC_SHA256(key="$1$SERCOMM$", msg=password).hexdigest()`
2. `LoginPWD = HMAC_SHA256(key=encryption_key, msg=hash1).hexdigest()`

---

## 3. Payload Cryptography (SJCL AES-128-CCM)

Certain sensitive router endpoints (such as `/data/wifi_general.json`) require client-side encryption and return encrypted JSON payloads.

### The Cryptography Standard
The router's web interface utilizes the **Stanford Javascript Crypto Library (SJCL)** configured with:
- **Cipher**: AES-128
- **Mode**: CCM (Counter with CBC-MAC)
- **Authentication Tag Size (ts)**: 64 bits
- **Key Derivation (PBKDF2)**:
  - PRF: HMAC-SHA256
  - Iterations: 1000
  - Key length: 128 bits
  - Salt: Decoded from hex bits of the `salt` parameter obtained in `user_lang.json`

### Why Native Python Crypto Libraries Fail
SJCL uses a proprietary serialization of bit-arrays with internal word alignment for CCM nonce/IV and authentication tags. When standard Python libraries (such as `PyCryptodome` or `cryptography`) attempt to verify or sign CCM payloads formatted by SJCL, MAC verification fails (`ValueError: MAC check failed`).

### Solution: Node.js SJCL Crypto Bridge
To achieve 100% interoperability with the router, the application embeds the router's exact `sjcl.js` script and calls it through `assets/crypto_bridge.js`:
- Derives the Derived Key (`dk`):
  ```bash
  node assets/crypto_bridge.js derive_dk <password> <hex_salt>
  ```
- Encrypts form parameters to SJCL JSON format:
  ```bash
  node assets/crypto_bridge.js encrypt <dk_hex> <payload_querystring>
  ```
- Decrypts router responses back into plaintext:
  ```bash
  node assets/crypto_bridge.js decrypt <dk_hex> '<sjcl_json_string>'
  ```

---

## 4. Parameter Resolution: Scalar Name vs ID

In Sercomm's JavaScript UI (`Sercomm.js` and `gui.js`), form fields are modeled using the `Scalar` class:
```javascript
new Scalar(name, id)
```
- `this.name = name;` -> Used strictly for UI rendering and DOM bindings.
- `this.id = id;` -> **The actual key sent over the wire in HTTP payloads**.

### Example Wire Parameters
| Feature | UI Form Name | Wire Parameter ID | Valid Values |
|---|---|---|---|
| Wi-Fi 2.4G State | `wifiGeneralNetworkOnOff` | `wifi_network_onoff` | `'0'` (off), `'1'` (on) |
| Wi-Fi 5G State | `wifiGeneralNetworkOnOff_5g` | `wifi_network_onoff_5g` | `'0'`, `'1'` |
| Guest 2.4G State | `wifiGeneralNetworkOnOff_guest` | `wifi_network_onoff_guest` | `'0'`, `'1'` |
| Guest 5G State | `wifiGeneralNetworkOnOff_5g_guest` | `wifi_network_onoff_5g_guest` | `'0'`, `'1'` |
| Band Steering | `bandSteeringEnable` | `band_steering_enable` | `'0'`, `'1'` |
| 2.4G Channel | `wifiChannel` | `wifi_channel` | `'auto'`, `'1'` - `'13'` |
| 5G Channel | `wifiChannel_5g` | `wifi_channel_5g` | `'auto'`, `'36'` - `'140'` |
| 2.4G SSID | `wifiSsid` | `wifi_ssid` | String (up to 32 chars) |
| 5G SSID | `wifiSsid_5g` | `wifi_ssid_5g` | String (up to 32 chars) |
| 2.4G WPA Key | `wifiPassword` | `wifi_wpa_key` | String (8-63 chars) |
| 5G WPA Key | `wifiPassword_5g` | `wifi_wpa_key_5g` | String (8-63 chars) |
| 2.4G Security | `wifiSecurity` | `wifi_security` | `'wpa2'`, `'wpa2wpa3'` |
| 5G Security | `wifiSecurity_5g` | `wifi_security_5g` | `'wpa2'`, `'wpa2wpa3'` |
| LAN IP Address | `lan_ip` | `LanIP` | IPv4 address string |
| DHCP Start IP | `lan_dhcp_start` | `LanDHCPStartIP` | IPv4 address string |
| DHCP End IP | `lan_dhcp_end` | `LanDHCPEndIP` | IPv4 address string |
| Primary DNS | `lan_dns_server` | `LanDNSServer` | IPv4 address string |
| DMZ Enabled | `dmz_enable` | `dmz_enable` | `'0'`, `'1'` |
| DMZ Target IP | `dmz_ip` | `dmz_ip` | IPv4 address string |
| UPnP Enabled | `upnp_enable` | `upnp_enable` | `'0'`, `'1'` |

---

## 5. Router JSON Endpoints

| Endpoint | Method | Encrypted | Description |
|---|---|---|---|
| `/data/wifi_general.json` | GET / POST | **YES** | Primary 2.4G and 5G Wi-Fi configuration, SSIDs, channels, passwords, and security |
| `/data/wifi_guest.json` | GET / POST | NO | Guest 2.4G and 5G Wi-Fi settings, access restrictions, duration |
| `/data/wifi_advanced.json` | GET / POST | NO | Wi-Fi 7 optimizations, channel bandwidth (20/40/80/160MHz), beacon intervals |
| `/data/wifi_bsd.json` | GET / POST | NO | Band Steering Daemon (BSD) configuration |
| `/data/wifi_restart.json` | POST | NO | Soft-restarts the Wi-Fi radio drivers |
| `/data/settings_lan.json` | GET / POST | NO | Subnets, DHCP ranges, lease time, advertised DNS |
| `/data/settings_lan_staticdhcp.json` | GET / POST | NO | DHCP IP reservations by MAC address |
| `/data/settings_lan_device.json` | GET | NO | Connected client topology (MAC, IP, RSSI, interface, link speed) |
| `/data/user_data.json` | GET | NO | Hardware features, WAN IPv4/IPv6, active interfaces |
| `/data/dmz.json` | GET / POST | NO | DMZ host configuration |
| `/data/upnp.json` | GET / POST | NO | Universal Plug and Play configuration |
| `/data/port_forwarding.json` | GET / POST | NO | NAT virtual server rules (IPv4 port forwarding) |
| `/data/reboot.json` | POST | NO | Full hardware reboot command |
| `/data/wan_connection.json` | POST | NO | WAN PPPoE reconnect / IP renewal |
