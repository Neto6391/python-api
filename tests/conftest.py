import pytest
from app.core.di.container import Container

@pytest.fixture(scope="session")
def container():
    c = Container()
    c.init_resources()
    yield c
    c.unwire()
