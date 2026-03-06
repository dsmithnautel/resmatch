"""Standardized error response models."""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str
    detail: str
    retry_after: int | None = None
