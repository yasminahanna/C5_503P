"""FastMCP server. Only the three decorated functions are model-callable."""

import os
from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from .models import HoldResult, ReservationResult, SearchResult
from .service import LibraryError, LibraryService

ROOT = Path(__file__).resolve().parents[1]
Query = Annotated[str, Field(min_length=1, max_length=100, description="Title, author, topic, or book ID. All space-separated terms must match.")]
StudentID = Annotated[str, Field(pattern=r"^S[0-9]{4}$", description="Fictional student ID, for example S1001.")]
BookID = Annotated[str, Field(pattern=r"^B[0-9]{3}$", description="Catalog book ID, for example B001.")]


def build_server(db_path: Path | None = None) -> FastMCP:
    service = LibraryService(db_path or Path(os.getenv("LIBRARY_DB_PATH", str(ROOT / "data" / "library.sqlite3"))))
    mcp = FastMCP("Campus Library Toolkit")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False})
    def search_catalog(query: Query, available_only: bool = False) -> SearchResult:
        """DATA: Look up fictional campus books without changing stored data.

        Returns matching books with IDs and current available copy counts, ordered
        by book ID. Zero matches is a valid empty result. Blank queries fail with
        INVALID_QUERY; unreadable storage fails with STORAGE_UNAVAILABLE.
        """
        try:
            return service.search_catalog(query, available_only)
        except LibraryError as exc:
            raise ToolError(str(exc)) from exc

    @mcp.tool(annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False})
    def create_hold(book_id: BookID, student_id: StudentID) -> HoldResult:
        """ACTION: Persist one demo book hold in local SQLite for an explicit reservation request.

        Requires a known book ID and student ID. Returns a hold ID and created/existing
        status. Retrying the same book/student pair reuses the original hold. Unknown
        books fail with BOOK_NOT_FOUND; exhausted copies fail with BOOK_UNAVAILABLE.
        """
        try:
            return service.create_hold(book_id, student_id)
        except LibraryError as exc:
            raise ToolError(str(exc)) from exc

    @mcp.tool(annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False})
    def reserve_book(query: Query, student_id: StudentID) -> ReservationResult:
        """ORCHESTRATION: Fulfill one topic-based book reservation using search_catalog then create_hold.

        Changes local SQLite; use only when the user explicitly asks to reserve.
        Tries matching titles in book-ID order, skipping unavailable copies.
        Returns the selected book, persisted hold, and internal execution steps.
        No match fails with NO_MATCH; no reservable match fails with NO_AVAILABLE_BOOK.
        """
        try:
            return service.reserve_book(query, student_id)
        except LibraryError as exc:
            raise ToolError(str(exc)) from exc

    # No resources are exposed: the Data capability is a queryable tool. Thus the
    # agent discovers exactly three tools, with no duplicate catalog interface.
    return mcp


def main() -> None:
    build_server().run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()
