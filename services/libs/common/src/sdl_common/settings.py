from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceSettings(BaseSettings):
    """Values injected by infra/charts/app. Subclass to add service-specific settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "service"
    port: int = 8000
    log_level: str = "INFO"
    root_path: str = ""  # set when served behind a stripped gateway prefix, e.g. /api/sample-api
    pod_name: str = "local"
    node_name: str = "local"
