import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.presentation.shared.http_response import HttpResponse
from app.presentation.v1.schemas.health_response import HealthResponse

@pytest.mark.asyncio
async def test_health_ok_async(container):
    transport = ASGITransport(app=app)
    headers = {"X-Request-ID": "rid-test-001"}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as ac:
        resp = await ac.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.headers.get("X-Request-ID") == "rid-test-001"
    typed = HttpResponse[HealthResponse].model_validate(resp.json())
    assert typed.success is True
    assert typed.data is not None
    assert typed.data.status == "Ok"
