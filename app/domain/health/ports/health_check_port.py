from typing import Protocol
from app.domain.health.entities.health_status import HealthStatus

class HealthCheckPort(Protocol):
    def check(self) -> HealthStatus: ...
