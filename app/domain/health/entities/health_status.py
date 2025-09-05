from dataclasses import dataclass
from .base_entity import BaseEntity

@dataclass(frozen=True)
class HealthStatus(BaseEntity):
    status: str = "Ok"
