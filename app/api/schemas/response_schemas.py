from typing import Generic, TypeVar, Optional, Any
from pydantic  import BaseModel

from app.api.schemas.pagination_schema import PaginationResponse

T = TypeVar('T')

class ResponseModel(BaseModel, Generic[T]):
  status: str
  code: int
  message: Optional[str] = None
  data: Optional[T] = None

class ErrorDetail(BaseModel):
  field: Optional[str] = None
  message: str

class ErrorResponse(BaseModel):
  status: str
  code: int
  message: str
  errors: Optional[list[ErrorDetail]] = None

def success_response(
    data: Any = None,
    pagination: Any = None,
    message: str = "Success",
    code: int = 200,
):
    response = {
        "status": "success",
        "code": code,
        "message": message,
        "data": data,
    }

    if pagination is not None:
        response["pagination"] = pagination

    return response

def error_response(message: str, code: int = 400, errors: list = None):
  response = {
      "status": "error",
      "code": code,
      "message": message
  }
  if errors:
      response["errors"] = errors
  return response
