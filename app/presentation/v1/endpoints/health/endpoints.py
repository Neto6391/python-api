from fastapi import APIRouter, Depends
from dependency_injector.wiring import Provide, inject
from app.presentation.shared.http_response import HttpResponse
from app.presentation.v1.schemas.health_response import HealthResponse
from app.presentation.v1.endpoints.health.controller import HealthController
from app.application.health.use_cases.check_health import CheckHealthUseCase
from app.core.di.container import Container
from app.core.security.api_key import api_key_auth

router = APIRouter(tags=["health"])

@router.get(
    "/health",
    response_model=HttpResponse[HealthResponse],
    summary="Health check",
    status_code=200,
)
@inject
def get_health(
    uc: CheckHealthUseCase = Depends(Provide[Container.check_health_uc]),
    _: None = Depends(api_key_auth),
):
    controller = HealthController(uc)
    return controller.get()
