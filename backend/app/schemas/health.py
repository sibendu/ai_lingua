from pydantic import BaseModel


class DependencyStatus(BaseModel):
    status: str
    detail: str | None = None


class ModelProviderStatus(BaseModel):
    configured: bool
    enabled: bool = False


class HealthResponse(BaseModel):
    status: str
    app: str
    environment: str
    dependencies: dict[str, DependencyStatus]
    model_providers: dict[str, ModelProviderStatus]
