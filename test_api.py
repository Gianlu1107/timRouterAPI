import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.router_client import RouterClient
from core.crypto import RouterCrypto
from core.config import settings

class TestTimRouterAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = RouterClient.get_instance()
        print("\n--- Connecting and authenticating with router ---")
        cls.client.login()
        print(f"Logged in successfully! Session ID: {cls.client.session_id[:16]}... FW: {cls.client.fw_version}")

    def test_01_crypto_dk(self):
        """Test SJCL PBKDF2 derivation"""
        dk = RouterCrypto.derive_dk(settings.ROUTER_PASSWORD or "TestPass123!", "782125E833C429F4")
        self.assertEqual(len(dk), 32)
        print(f"[OK] Derived DK: {dk}")

    def test_02_crypto_encrypt_decrypt(self):
        """Test roundtrip SJCL AES-CCM encrypt/decrypt"""
        dk = "0c20da4f43ff883ea8b5a4593506e977"
        plaintext = "param1=hello&param2=world123"
        enc = RouterCrypto.encrypt(dk, plaintext)
        dec = RouterCrypto.decrypt(dk, enc)
        self.assertEqual(dec, plaintext)
        print("[OK] Roundtrip encryption/decryption passed")

    def test_03_get_wifi_general(self):
        """Test querying and decrypting wifi_general data"""
        data = self.client.get_data("wifi_general")
        self.assertIsInstance(data, list)
        merged = {}
        for item in data:
            if isinstance(item, dict):
                merged.update(item)
        self.assertIn("wifi_ssid", merged)
        self.assertIn("wifi_ssid_5g", merged)
        print(f"[OK] Wi-Fi 2.4G SSID: {merged.get('wifi_ssid')} (Ch: {merged.get('wifi_now_channel')})")
        print(f"[OK] Wi-Fi 5G SSID: {merged.get('wifi_ssid_5g')} (Ch: {merged.get('wifi_now_channel_5g')})")
        print(f"[OK] Guest 2.4G active: {merged.get('wifi_network_onoff_guest') == '1'}")
        print(f"[OK] Guest 5G active: {merged.get('wifi_network_onoff_5g_guest') == '1'}")

    def test_04_get_lan_settings(self):
        """Test querying LAN settings"""
        data = self.client.get_data("settings_lan")
        self.assertIsInstance(data, list)
        primary = next((item for item in data if isinstance(item, dict) and item.get("subnet") == "0"), {})
        self.assertEqual(primary.get("LanIP"), "192.168.1.1")
        print(f"[OK] LAN IP: {primary.get('LanIP')}, DHCP Pool: {primary.get('LanDHCPStartIP')} - {primary.get('LanDHCPEndIP')}")

    def test_05_get_user_data(self):
        """Test querying user_data (WAN IP, model capabilities)"""
        data = self.client.get_data("user_data")
        self.assertIsInstance(data, list)
        merged = {}
        for item in data:
            if isinstance(item, dict):
                merged.update(item)
        print(f"[OK] WAN IPv4: {merged.get('wan_ip4_addr')}, Firmware: {merged.get('fw_version')}")

if __name__ == "__main__":
    unittest.main()
