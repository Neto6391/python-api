from fastapi import Request
from fastapi.responses import JSONResponse
from starlette import status
from app.presentation.shared.http_response import HttpErrorResponse

class AppError(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message

async def app_error_handler(request: Request, exc: AppError):
    payload = HttpErrorResponse(error="AppError", message=exc.message)
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())
