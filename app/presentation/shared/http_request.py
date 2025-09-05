from typing import Generic, Optional, TypeVar
from pydantic import BaseModel
from pydantic.generics import GenericModel

T = TypeVar("T", bound=BaseModel)

class HttpRequest(GenericModel, Generic[T]):
    correlation_id: Optional[str] = None
    data: Optional[T] = None
