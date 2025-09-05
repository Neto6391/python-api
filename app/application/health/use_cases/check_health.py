from app.domain.health.entities.health_status import HealthStatus
from app.domain.health.ports.health_check_port import HealthCheckPort

class CheckHealthUseCase:
    def __init__(self, port: HealthCheckPort) -> None:
        self._port = port

    def execute(self) -> HealthStatus:
        return self._port.check()
