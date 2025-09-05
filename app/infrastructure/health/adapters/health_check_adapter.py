from app.domain.health.entities.health_status import HealthStatus
from app.domain.health.ports.health_check_port import HealthCheckPort
from app.core.config.logging import get_logger

logger = get_logger(__name__)

class HealthCheckAdapter(HealthCheckPort):
    def check(self) -> HealthStatus:
        logger.debug("HealthCheckAdapter.check")
        return HealthStatus(status="Ok")
