from app.domain.health.entities.health_status import HealthStatus
from app.application.health.dtos.health_status_dto import HealthStatusDTO

class HealthStatusMapper:
    @staticmethod
    def to_dto(entity: HealthStatus) -> HealthStatusDTO:
        return HealthStatusDTO(status=entity.status)

    @staticmethod
    def to_domain(dto: HealthStatusDTO) -> HealthStatus:
        return HealthStatus(status=dto.status)
