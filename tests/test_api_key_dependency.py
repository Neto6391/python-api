import pytest
from httpx import AsyncClient, ASGITransport

@pytest.mark.asyncio
async def test_api_key_required_when_configured(monkeypatch):
    # ativa API key em runtime
    from app.core.config import settings as cfg
    monkeypatch.setattr(cfg.settings, "api_keys", ["secret-key-1"], raising=False)

    # Reimporta app para reavaliar inclusão do router?
    # Dependência lê settings a cada request, então basta enviar o header.
    from app.main import app
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r1 = await ac.get("/api/v1/health")
        assert r1.status_code == 401

        r2 = await ac.get("/api/v1/health", headers={"X-API-Key": "secret-key-1"})
        assert r2.status_code == 200
