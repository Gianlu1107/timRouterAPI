from typing import Optional
from fastapi import APIRouter, HTTPException, status
from core.router_client import RouterClient
from models.auth import AuthStatus, LoginRequest
from models.system import GenericResponse

router = APIRouter(prefix="/auth", tags=["Authentication & Session"])

@router.get("/status", response_model=AuthStatus, summary="Get current router session status")
def get_auth_status():
    """
    Checks if the middleware is actively authenticated with the TIM router,
    returning the active session cookie, CSRF token, and firmware details.
    """
    client = RouterClient.get_instance()
    try:
        client.ensure_authenticated()
        return AuthStatus(
            authenticated=bool(client.session_id),
            router_host=client.host,
            router_user=client.username,
            firmware_version=client.fw_version or "Unknown",
            session_id=client.session_id or "",
            csrf_token=client.csrf_token or "",
            last_login_epoch=client.last_login_time,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to verify authentication with router: {str(e)}"
        )

@router.post("/login", response_model=AuthStatus, summary="Force re-authentication with router")
def force_login(req: Optional[LoginRequest] = None):
    """
    Forces a fresh cryptographic handshake and authentication against the router,
    invalidating previous session cache.
    """
    client = RouterClient.get_instance()
    if req:
        client.username = req.username
        client.password = req.password

    try:
        client.login()
        return AuthStatus(
            authenticated=True,
            router_host=client.host,
            router_user=client.username,
            firmware_version=client.fw_version or "Unknown",
            session_id=client.session_id or "",
            csrf_token=client.csrf_token or "",
            last_login_epoch=client.last_login_time,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Router login failed: {str(e)}"
        )
