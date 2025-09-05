from pydantic import BaseModel, Field

class HealthStatusDTO(BaseModel):
    status: str = Field(default="Ok", description="Estado da API")
