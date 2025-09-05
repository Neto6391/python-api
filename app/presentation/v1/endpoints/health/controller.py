from app.presentation.v1.schemas.health_response import HealthResponse
from app.presentation.shared.http_response import HttpResponse
from app.application.health.use_cases.check_health import CheckHealthUseCase
from app.application.health.mappers.health_status_mapper import HealthStatusMapper

class HealthController:
    def __init__(self, uc: CheckHealthUseCase) -> None:
        self._uc = uc

    def get(self) -> HttpResponse[HealthResponse]:
        entity = self._uc.execute()
        dto = HealthStatusMapper.to_dto(entity)
        response = HealthResponse(status=dto.status)
        return HttpResponse[HealthResponse](success=True, data=response)
