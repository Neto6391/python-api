from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config.settings import settings
from app.core.config.logging import configure_logging, get_logger
from app.core.di.container import Container
from app.core.security.api_key import api_key_auth
from app.core.middleware.correlation import CorrelationIdMiddleware
from app.core.middleware.security_headers import SecurityHeadersMiddleware
from app.presentation.v1.api import api_router as v1_api_router
from app.presentation.shared.errors import AppError, app_error_handler

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("Inicializando DI Container (Singletons)")
    container = Container()
    container.init_resources()
    container.wire(packages=["app.presentation.v1.endpoints"])
    app.state.container = container
    try:
        yield
    finally:
        logger.info("Encerrando DI Container")
        container.unwire()

app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    lifespan=lifespan,
)

# Middlewares
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=settings.gzip_min_size)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Handlers de erro
app.add_exception_handler(AppError, app_error_handler)

# Roteamento
app.include_router(v1_api_router)
