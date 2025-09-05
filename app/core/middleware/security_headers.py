from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.core.config.settings import settings

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        # Básicos para API
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        # HSTS (apenas se habilitado e sob TLS)
        if settings.enable_hsts:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
