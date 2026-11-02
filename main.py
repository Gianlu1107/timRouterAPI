import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import settings
from core.router_client import RouterClient
from core.exceptions import RouterException
from routers.auth import router as auth_router
from routers.wifi import router as wifi_router
from routers.lan import router as lan_router
from routers.wan import router as wan_router
from routers.devices import router as devices_router
from routers.system import router as system_router

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("timRouterAPI")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing TIM Router API Middleware...")
    client = RouterClient.get_instance()
    try:
        client.ensure_authenticated()
        logger.info(f"Connected to TIM Router at {settings.ROUTER_HOST} (FW: {client.fw_version})")
    except Exception as e:
        logger.warning(f"Could not connect to router during startup: {e}. Will retry upon first request.")
    yield
    logger.info("Shutting down TIM Router API Middleware.")

app = FastAPI(
    title="TIM HUB+ Router REST API Middleware",
    description="""
# TIM Sercomm AGCOMBO / AGSGP REST API Middleware

A high-performance Python FastAPI middleware exposing complete programmatic control
over **TIM HUB+ (Sercomm AGSGP / AGTHP / AGCOMBO)** fiber & DSL routers.

### Capabilities:
- **Authentication**: Automatic HMAC-SHA256 handshake, session recovery, CSRF token handling.
- **Payload Security**: Native Stanford Javascript Crypto Library (SJCL) AES-128-CCM encryption/decryption bridge.
- **Wi-Fi Control**: Dual-band radio management (2.4G & 5G), SSID, WPA2/WPA3 credentials, manual & auto channel selection, Band Steering toggle.
- **Guest Wi-Fi**: Complete activation, isolation, and scheduling for guest networks.
- **LAN & DHCP**: IP pool configurations, custom DNS server distribution, static DHCP MAC/IP reservations.
- **WAN & NAT**: Port forwarding / virtual server rules, DMZ host exposure, UPnP IGD control.
- **Diagnostics**: Network device inventory (LAN & Wi-Fi), hardware stats, WAN link renegotiation, remote reboot.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Enable CORS for dashboards, Home Assistant, or frontend apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Exception Handler
@app.exception_handler(RouterException)
async def router_exception_handler(request: Request, exc: RouterException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.__class__.__name__, "message": exc.message}
    )

# Include API Routers under /api/v1
app.include_router(auth_router, prefix="/api/v1")
app.include_router(wifi_router, prefix="/api/v1")
app.include_router(lan_router, prefix="/api/v1")
app.include_router(wan_router, prefix="/api/v1")
app.include_router(devices_router, prefix="/api/v1")
app.include_router(system_router, prefix="/api/v1")

@app.get("/", tags=["Health"])
def root():
    return {
        "service": "TIM Router REST API Middleware",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "router_target": f"http://{settings.ROUTER_HOST}:{settings.ROUTER_PORT}"
    }

@app.get("/health", tags=["Health"])
def health():
    client = RouterClient.get_instance()
    return {
        "status": "healthy",
        "authenticated": bool(client.session_id),
        "router_host": client.host,
        "firmware": client.fw_version or "Unknown"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.API_HOST, port=settings.API_PORT, reload=settings.API_DEBUG)
