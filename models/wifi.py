from typing import Optional, List
from pydantic import BaseModel, Field

class WifiRadio(BaseModel):
    enabled: bool = Field(..., description="Whether the radio is powered on")
    frequency: str = Field(..., description="Frequency band (2.4GHz or 5GHz)")
    ssid: str = Field(..., description="Wi-Fi network name (SSID)")
    channel: str = Field(..., description="Selected channel ('auto' or numeric string, e.g. '52', '100')")
    current_channel: Optional[str] = Field(None, description="Actual currently operating channel")
    bandwidth: Optional[str] = Field(None, description="Negotiated bandwidth in MHz or Mbps")
    broadcast_ssid: bool = Field(True, description="Whether the SSID is visible/broadcasted")
    security_mode: str = Field(..., description="Security protocol: 'wpa2', 'wpa3', or 'wpa2wpa3'")
    password: Optional[str] = Field(None, description="Wi-Fi WPA passphrase")
    wifi7_optimization: bool = Field(False, description="Whether 802.11be / Wi-Fi 7 optimizations are enabled")

class WifiGuestRadio(BaseModel):
    enabled: bool = Field(..., description="Whether guest Wi-Fi is active")
    ssid: str = Field(..., description="Guest network name (SSID)")
    password: Optional[str] = Field(None, description="Guest network passphrase")
    security_mode: str = Field("wpa2", description="Security mode for guest network")
    allow_services: str = Field("All services", description="Allowed guest network services")
    limited_time: str = Field("None", description="Session duration limit for guests")
    channel: Optional[str] = Field("auto", description="Channel mode")

class WifiOverview(BaseModel):
    band_steering_enabled: bool = Field(..., description="Whether Band Steering (BSD) is active")
    radio_24g: WifiRadio = Field(..., description="2.4 GHz Primary Network settings")
    radio_5g: WifiRadio = Field(..., description="5 GHz Primary Network settings")
    guest_24g: WifiGuestRadio = Field(..., description="2.4 GHz Guest Network settings")
    guest_5g: WifiGuestRadio = Field(..., description="5 GHz Guest Network settings")

class WifiGeneralUpdateRequest(BaseModel):
    band_steering_enabled: Optional[bool] = Field(None, description="Set Band Steering active/inactive")
    radio_24g_enabled: Optional[bool] = Field(None, description="Power on/off 2.4 GHz radio")
    radio_5g_enabled: Optional[bool] = Field(None, description="Power on/off 5 GHz radio")
    ssid_24g: Optional[str] = Field(None, description="New SSID for 2.4 GHz")
    password_24g: Optional[str] = Field(None, description="New WPA password for 2.4 GHz")
    channel_24g: Optional[str] = Field(None, description="Channel for 2.4 GHz ('auto' or '1'-'13')")
    broadcast_ssid_24g: Optional[bool] = Field(None, description="Broadcast SSID 2.4 GHz")
    ssid_5g: Optional[str] = Field(None, description="New SSID for 5 GHz")
    password_5g: Optional[str] = Field(None, description="New WPA password for 5 GHz")
    channel_5g: Optional[str] = Field(None, description="Channel for 5 GHz ('auto', '36', '40', '44', '48', '52', '56', '60', '64', '100', '104', '108', etc.)")
    broadcast_ssid_5g: Optional[bool] = Field(None, description="Broadcast SSID 5 GHz")
    security_5g: Optional[str] = Field(None, description="'wpa2' or 'wpa2wpa3'")

class WifiGuestUpdateRequest(BaseModel):
    enabled_24g: Optional[bool] = Field(None, description="Enable or disable 2.4 GHz Guest network")
    ssid_24g: Optional[str] = Field(None, description="SSID for 2.4 GHz Guest network")
    password_24g: Optional[str] = Field(None, description="Password for 2.4 GHz Guest network")
    enabled_5g: Optional[bool] = Field(None, description="Enable or disable 5 GHz Guest network")
    ssid_5g: Optional[str] = Field(None, description="SSID for 5 GHz Guest network")
    password_5g: Optional[str] = Field(None, description="Password for 5 GHz Guest network")

class WifiAdvancedSettings(BaseModel):
    wifi_mode_24g: str = Field(..., description="Operating mode (e.g. 'n-only', 'b/g/n')")
    bandwidth_24g: str = Field(..., description="Bandwidth for 2.4 GHz (e.g. '20MHz', '20MHz_40MHz_auto')")
    wmm_enabled_24g: bool = Field(True, description="Wi-Fi Multimedia QoS for 2.4 GHz")
    auto_channel_interval_24g: str = Field("86400", description="Auto channel reselection interval in seconds")
    wifi_mode_5g: str = Field(..., description="Operating mode for 5 GHz (e.g. 'be', 'ax', 'ac')")
    bandwidth_5g: str = Field(..., description="Bandwidth for 5 GHz (e.g. '20MHz_40MHz_80MHz_auto', '20MHz_40MHz_80MHz_160MHz_auto')")
    wmm_enabled_5g: bool = Field(True, description="Wi-Fi Multimedia QoS for 5 GHz")
    auto_channel_interval_5g: str = Field("86400", description="Auto channel reselection interval in seconds")

class WifiBandSteeringToggle(BaseModel):
    enabled: bool = Field(..., description="Enable or disable Band Steering")

class WifiRestartResponse(BaseModel):
    status: str = Field("ok", description="Status of restart command")
    message: str = Field("Wi-Fi radios restarting...", description="Human readable description")
