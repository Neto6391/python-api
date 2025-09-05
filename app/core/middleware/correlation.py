from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from uuid import uuid4
from app.core.config.logging import request_id_ctx_var

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, header_name: str = "X-Request-ID") -> None:
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request, call_next):
        incoming = request.headers.get(self.header_name)
        request_id = incoming or str(uuid4())
        request.state.correlation_id = request_id
        token = request_id_ctx_var.set(request_id)
        try:
            response = await call_next(request)
        finally:
            request_id_ctx_var.reset(token)
        response.headers[self.header_name] = request_id
        return response
