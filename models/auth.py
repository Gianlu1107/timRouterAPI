from pydantic import BaseModel, Field

class AuthStatus(BaseModel):
    authenticated: bool = Field(..., description="Whether the middleware is actively authenticated with the router")
    router_host: str = Field(..., description="Target router IP address or hostname")
    router_user: str = Field(..., description="Username used to connect")
    firmware_version: str = Field(..., description="Router firmware version detected")
    session_id: str = Field(..., description="Current router session cookie value")
    csrf_token: str = Field(..., description="Current CSRF security token")
    last_login_epoch: float = Field(..., description="Unix timestamp of the last successful handshake")

class LoginRequest(BaseModel):
    username: str = Field(default="admin", description="Router administrator username")
    password: str = Field(..., description="Router administrator password")
