from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    ROUTER_HOST: str = "192.168.1.1"
    ROUTER_PORT: int = 80
    ROUTER_USER: str = "admin"
    ROUTER_PASSWORD: str = ""

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    @property
    def router_base_url(self) -> str:
        return f"http://{self.ROUTER_HOST}:{self.ROUTER_PORT}"

settings = Settings()
