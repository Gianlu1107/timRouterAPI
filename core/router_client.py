import json
import logging
import re
import socket
import threading
import time
import urllib.parse
from typing import Any, Dict, List, Optional, Union

from core.config import settings
from core.crypto import RouterCrypto
from core.exceptions import (
    RouterAuthException,
    RouterConfigException,
    RouterConnectionException,
    RouterProtocolException,
)

logger = logging.getLogger("timRouterAPI")

class RouterClient:
    """
    HTTP Client for Telecom Italia (TIM) Sercomm AGCOMBO / AGSGP modems.
    Handles challenge-response authentication, session tracking, CSRF tokens,
    and Stanford Javascript Crypto Library (SJCL) AES-CCM 128 payload encryption/decryption.
    """
    _instance: Optional["RouterClient"] = None
    _lock = threading.Lock()

    def __init__(self):
        self.host = settings.ROUTER_HOST
        self.port = settings.ROUTER_PORT
        self.username = settings.ROUTER_USER
        self.password = settings.ROUTER_PASSWORD

        self.session_id: Optional[str] = None
        self.csrf_token: Optional[str] = None
        self.dk_hex: Optional[str] = None
        self.salt: Optional[str] = None
        self.encryption_key: Optional[str] = None
        self.fw_version: Optional[str] = None
        self.last_login_time: float = 0
        self._auth_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "RouterClient":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def _send_raw(
        self,
        path: str,
        method: str = "GET",
        body: str = "",
        extra_headers: Optional[Dict[str, str]] = None,
        timeout: int = 15,
    ) -> str:
        """
        Sends a low-level HTTP/1.1 request via raw socket to comply strictly
        with the router's embedded mini_httpd server constraints (Connection: close,
        exact Host formatting, no HTTP pipelining).
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((self.host, self.port))

            headers = {
                "Host": self.host,
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
                "Connection": "close",
            }
            if self.session_id:
                headers["Cookie"] = f"session_id={self.session_id}; username={self.username}"

            if extra_headers:
                headers.update(extra_headers)

            if body:
                encoded_body = body.encode("utf-8")
                if "Content-Type" not in headers:
                    headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
                headers["Content-Length"] = str(len(encoded_body))
            else:
                encoded_body = b""

            req_lines = [f"{method} {path} HTTP/1.1"]
            for k, v in headers.items():
                req_lines.append(f"{k}: {v}")
            req_lines.append("")
            req_lines.append("")
            raw_req = "\r\n".join(req_lines).encode("utf-8") + encoded_body

            s.sendall(raw_req)

            chunks = []
            while True:
                try:
                    c = s.recv(8192)
                    if not c:
                        break
                    chunks.append(c)
                except Exception:
                    break
            s.close()
            return b"".join(chunks).decode("latin1", errors="replace")

        except socket.timeout:
            raise RouterConnectionException(f"Connection to router {self.host}:{self.port} timed out")
        except socket.error as e:
            raise RouterConnectionException(f"Socket error connecting to router: {e}")

    @staticmethod
    def _extract_body(response: str) -> str:
        parts = response.split("\r\n\r\n", 1)
        return parts[1] if len(parts) > 1 else response

    def login(self) -> None:
        """
        Executes the Sercomm authentication handshake:
        1. GET /login.html to extract initial CSRF token
        2. GET /data/user_lang.json to obtain dynamic salt and encryption_key
        3. Double HMAC-SHA256 password hash computation
        4. SJCL PBKDF2 decryption key (dk) derivation
        5. POST /data/login.json to obtain session_id
        6. GET /overview.html to obtain the persistent session and refreshed CSRF token
        """
        with self._auth_lock:
            logger.info("Initiating router authentication handshake...")
            # Step 1: Initial login page
            res1 = self._send_raw("/login.html")
            csrf_match = re.search(r"var csrf_token = \x27([a-fA-F0-9]+)\x27", res1)
            if not csrf_match:
                raise RouterProtocolException("Could not extract initial CSRF token from /login.html")
            init_csrf = csrf_match.group(1)

            # Step 2: Extract dynamic encryption salt
            res2 = self._send_raw(f"/data/user_lang.json?csrf_token={init_csrf}")
            body2 = self._extract_body(res2)

            enc_key_match = re.search(r"\"encryption_key\":\s*\"([^\"]+)\"", body2)
            salt_match = re.search(r"\"salt\":\s*\"([^\"]+)\"", body2)
            fw_match = re.search(r"\"fw_version\":\s*\"([^\"]+)\"", body2)

            if not enc_key_match or not salt_match:
                raise RouterProtocolException("Failed to extract encryption_key or salt from /data/user_lang.json")

            self.encryption_key = enc_key_match.group(1)
            self.salt = salt_match.group(1)
            if fw_match:
                self.fw_version = fw_match.group(1)

            # Step 3 & 4: Hashes and key derivation
            user_password = RouterCrypto.compute_password_hash(self.password, self.encryption_key)
            self.dk_hex = RouterCrypto.derive_dk(self.password, self.salt)

            # Step 5: Post credentials
            login_payload = f"LoginName={self.username}&LoginPWD={user_password}"
            res3 = self._send_raw(
                f"/data/login.json?csrf_token={init_csrf}",
                method="POST",
                body=login_payload
            )

            body3 = self._extract_body(res3).strip()
            if '"3"' in body3:
                raise RouterAuthException("Invalid username or password supplied for router")

            sess_match = re.search(r"session_id=([^;]+);", res3, re.IGNORECASE)
            if not sess_match:
                raise RouterAuthException("Router did not return session_id cookie upon authentication")
            temp_session_id = sess_match.group(1)

            # Step 6: Load overview to finalize session and acquire updated CSRF token
            self.session_id = temp_session_id
            res_overview = self._send_raw("/overview.html")

            updated_sess = re.search(r"session_id=([^;]+);", res_overview, re.IGNORECASE)
            updated_csrf = re.search(r"csrf_token\s*=\s*\x27([a-fA-F0-9]+)\x27", res_overview)

            if updated_sess:
                self.session_id = updated_sess.group(1)
            if updated_csrf:
                self.csrf_token = updated_csrf.group(1)
            else:
                self.csrf_token = init_csrf

            self.last_login_time = time.time()
            logger.info("Router authentication successful. Session ID established.")

    def ensure_authenticated(self) -> None:
        if not self.session_id or not self.csrf_token or not self.dk_hex:
            self.login()
        elif time.time() - self.last_login_time > 300:  # refresh session after 5 minutes
            try:
                self.login()
            except Exception as e:
                logger.warning(f"Session refresh failed: {e}. Re-logging in...")
                self.login()

    def get_data(self, endpoint: str) -> Union[Dict[str, Any], List[Any], str]:
        """
        Queries a /data/{endpoint}.json resource from the router.
        Automatically decrypts SJCL ciphertext if the router responds encrypted.
        """
        self.ensure_authenticated()

        ts = int(time.time() * 1000)
        url = f"/data/{endpoint}.json?_={ts}&csrf_token={self.csrf_token}"
        response = self._send_raw(url)

        # Check for expired session or redirect
        if "Location: /login.html" in response or "403 Forbidden" in response:
            logger.info("Session expired or forbidden. Re-authenticating...")
            self.login()
            url = f"/data/{endpoint}.json?_={int(time.time() * 1000)}&csrf_token={self.csrf_token}"
            response = self._send_raw(url)

        body = self._extract_body(response).strip()

        if body.startswith('{"iv":'):
            if not self.dk_hex:
                self.login()
            decrypted = RouterCrypto.decrypt(self.dk_hex, body)
            try:
                return json.loads(decrypted)
            except Exception:
                return decrypted

        try:
            return json.loads(body)
        except Exception:
            return body

    def post_data(
        self,
        endpoint: str,
        params: Union[Dict[str, Any], List[tuple]],
        encrypt: bool = False
    ) -> bool:
        """
        Submits configuration parameters to /data/{endpoint}.json.
        Encrypts parameters via SJCL AES-CCM if encrypt=True.
        """
        self.ensure_authenticated()

        if isinstance(params, dict):
            items = params.items()
        else:
            items = params

        query_str = "&".join([f"{k}={urllib.parse.quote(str(v))}" for k, v in items])

        if encrypt:
            if not self.dk_hex:
                self.login()
            payload = RouterCrypto.encrypt(self.dk_hex, query_str)
        else:
            payload = query_str

        ts = int(time.time() * 1000)
        url = f"/data/{endpoint}.json?_={ts}&csrf_token={self.csrf_token}"

        response = self._send_raw(url, method="POST", body=payload)
        body = self._extract_body(response).strip()

        # Check if response is encrypted
        if body.startswith('{"iv":'):
            try:
                body = RouterCrypto.decrypt(self.dk_hex, body).strip()
            except Exception:
                pass

        if body in ['1', '"1"', '[ ]', '[]', 'true', '{"status":"ok"}'] or "200 OK" in response:
            return True

        logger.error(f"Failed to post data to {endpoint}: response was '{body}'")
        raise RouterConfigException(f"Router rejected configuration update for {endpoint}: {body}")
