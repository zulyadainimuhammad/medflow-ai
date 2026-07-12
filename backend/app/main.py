from fastapi import FastAPI

from app.api.auth.routes import router as auth_router
from app.api.health.routes import router as health_router
from app.api.middleware import AuthenticationMiddleware
from app.core.config import get_settings
from app.security import get_token_service

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.app_debug,
)

token_service = get_token_service(
    secret_key=settings.jwt_secret_key,
    issuer=settings.jwt_issuer,
    audience=settings.jwt_audience,
    algorithm=settings.jwt_algorithm,
)

app.add_middleware(
    AuthenticationMiddleware,
    token_service=token_service,
    skip_paths=("/", "/docs", "/openapi.json", f"{settings.api_base_path}/health"),
)

app.include_router(health_router, prefix=settings.api_base_path)
app.include_router(auth_router, prefix=settings.api_base_path)


@app.get("/", tags=["root"])
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "environment": settings.app_env,
        "status": "running",
    }
