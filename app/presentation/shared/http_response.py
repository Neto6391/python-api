from typing import Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class HttpResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None

class HttpErrorResponse(BaseModel):
    success: bool = False
    error: str
    message: Optional[str] = None
