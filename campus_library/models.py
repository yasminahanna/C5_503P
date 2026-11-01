"""Typed results become the MCP tools' JSON output schemas."""

from typing import Literal

from pydantic import BaseModel, Field


class Book(BaseModel):
    book_id: str
    title: str
    author: str
    topic: str
    total_copies: int = Field(ge=0)
    available_copies: int = Field(ge=0)


class SearchResult(BaseModel):
    query: str
    count: int
    books: list[Book]


class HoldResult(BaseModel):
    status: Literal["created", "existing"]
    hold_id: str
    book_id: str
    student_id: str
    created_at: str
    message: str


class WorkflowStep(BaseModel):
    tool: Literal["search_catalog", "create_hold"]
    detail: str


class ReservationResult(BaseModel):
    query: str
    selected_book: Book
    hold: HoldResult
    steps: list[WorkflowStep]
