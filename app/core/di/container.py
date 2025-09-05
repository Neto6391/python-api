from dependency_injector import containers, providers

from app.infrastructure.health.adapters.health_check_adapter import HealthCheckAdapter
from app.application.health.use_cases.check_health import CheckHealthUseCase




class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        packages=["app.presentation.v1.endpoints"]
    )

    health_check_adapter = providers.Singleton(HealthCheckAdapter)
    check_health_uc = providers.Singleton(CheckHealthUseCase, port=health_check_adapter)