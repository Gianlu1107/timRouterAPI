import hashlib
import hmac
import subprocess
from pathlib import Path
from core.exceptions import RouterProtocolException

BRIDGE_PATH = Path(__file__).resolve().parent.parent / "assets" / "crypto_bridge.js"

class RouterCrypto:
    @staticmethod
    def compute_password_hash(password: str, encryption_key: str) -> str:
        """
        Computes the double HMAC-SHA256 required by Sercomm router:
        1. hash1 = HMAC-SHA256("$1$SERCOMM$", password)
        2. user_password = HMAC-SHA256(encryption_key, hash1)
        """
        hash1 = hmac.new(b"$1$SERCOMM$", password.encode("utf-8"), hashlib.sha256).hexdigest()
        user_password = hmac.new(encryption_key.encode("utf-8"), hash1.encode("utf-8"), hashlib.sha256).hexdigest()
        return user_password

    @staticmethod
    def derive_dk(password: str, salt_hex: str) -> str:
        """
        Derives the 128-bit decryption key (dk) via SJCL PBKDF2 (1000 iterations).
        """
        try:
            res = subprocess.check_output(
                ["node", str(BRIDGE_PATH), "derive_dk", password, salt_hex],
                stderr=subprocess.PIPE
            )
            return res.decode("utf-8").strip()
        except subprocess.CalledProcessError as e:
            raise RouterProtocolException(f"Failed to derive SJCL key: {e.stderr.decode('utf-8')}")

    @staticmethod
    def encrypt(dk_hex: str, plaintext: str) -> str:
        """
        Encrypts plaintext into SJCL JSON format using AES-128-CCM.
        """
        try:
            res = subprocess.check_output(
                ["node", str(BRIDGE_PATH), "encrypt", dk_hex, plaintext],
                stderr=subprocess.PIPE
            )
            return res.decode("utf-8").strip()
        except subprocess.CalledProcessError as e:
            raise RouterProtocolException(f"Failed to encrypt payload with SJCL: {e.stderr.decode('utf-8')}")

    @staticmethod
    def decrypt(dk_hex: str, ciphertext_json: str) -> str:
        """
        Decrypts an SJCL JSON payload using AES-128-CCM.
        """
        try:
            res = subprocess.check_output(
                ["node", str(BRIDGE_PATH), "decrypt", dk_hex, ciphertext_json],
                stderr=subprocess.PIPE
            )
            return res.decode("utf-8").strip()
        except subprocess.CalledProcessError as e:
            raise RouterProtocolException(f"Failed to decrypt payload with SJCL: {e.stderr.decode('utf-8')}")
