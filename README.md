# Clean Arch + DDD + Hexagonal

## Destaques

- **Ports & Adapters**, DI **Singleton**, **lifespan** moderno.
- **CORS** por settings, **TrustedHost**, **GZip**, **Correlation-Id**.
- **Security headers** (HSTS opcional), **API Key** opcional via `X-API-Key`.
- Envelopes **tipados** `HttpRequest[T]` e `HttpResponse[T]`.
- **/api/v1/health** único endpoint.
- **Dockerfile** com **gunicorn + uvicorn workers**.

## Execução local

```bash
uvicorn app.main:app --reload
# GET http://127.0.0.1:8000/api/v1/health
```

## Docker

```bash
docker build -t . .
docker run -p 8080:8080 -e ALLOWED_HOSTS='["*"]' -e CORS_ORIGINS='["http://localhost:3000"]' .
# http://127.0.0.1:8080/api/v1/health
```

### 🔧 Principais Melhorias

**1. Geração Modular por Componente**

- `--component model`: Gera apenas Domain (entidades + ports)
- `--component usecase`: Gera apenas Application (DTOs + mappers + use cases)
- `--component adapter`: Gera apenas Infrastructure (adapters in-memory)
- `--component endpoints`: Gera apenas Presentation (schemas + controller + endpoints)
- `--component full`: Gera todos os componentes (comportamento original)

### 🧪 Testes Realizados

Todos os componentes foram testados individualmente:

- ✅ **Model**: `cocli --resource product --component model` → Gerou `domain/product/`
- ✅ **UseCase**: `cocli --resource product --component usecase` → Gerou `application/product/`
- ✅ **Adapter**: `cocli --resource product --component adapter` → Gerou `infrastructure/product/`
- ✅ **Endpoints**: `cocli --resource product --component endpoints` → Gerou `presentation/v1/endpoints/product/`
- ✅ **Full**: `cocli --resource order --component full` → Gerou todas as camadas

### 🚀 Como Usar

**Geração modular** (recomendado):

```bash
# Gerar apenas o modelo de domínio
cocli --resource user --path /api/v1/users --component model --fields "name:str,email:str"

# Gerar apenas os use cases
cocli --resource user --path /api/v1/users --component usecase --fields "name:str,email:str"

# Gerar apenas os adapters
cocli --resource user --path /api/v1/users --component adapter --fields "name:str,email:str"

# Gerar apenas os endpoints
cocli --resource user --path /api/v1/users --component endpoints --fields "name:str,email:str"
```

**Geração completa** (comportamento original):

```bash
cocli --resource user --path /api/v1/users --component full --fields "name:str,email:str"
```

### 📁 Estrutura Gerada

Cada componente gera arquivos nas camadas apropriadas:

- **Domain**: `app/domain/<recurso>/entities/<recurso>.py` + `ports/<recurso>_port.py`
- **Application**: `app/application/<recurso>/dtos/` + `mappers/` + `use_cases/`
- **Infrastructure**: `app/infrastructure/<recurso>/adapters/in_memory_<recurso>_adapter.py`
- **Presentation**: `app/presentation/v1/schemas/<recurso>_{request,response}.py` + `endpoints/<recurso>/`
- **Configuração**: `app/core/di/container.py` e `app/presentation/v1/api.py` atualizados automaticamente

> **Nota**: Os adapters são **in-memory** por padrão, perfeitos para prototipagem rápida e testes de contrato da API.
