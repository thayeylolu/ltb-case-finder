"""Task 11: Pydantic request/response models for POST /search."""

from typing import List, Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    issues: List[str] = Field(..., min_length=1, description="User-facing issue names to search for")


class CaseResult(BaseModel):
    file_number: str
    order_date: str
    issues: List[str]
    city: Optional[str] = None
    document_type: str
    view_order_url: str


class SearchResponse(BaseModel):
    results: List[CaseResult]
