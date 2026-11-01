"""Business logic shared by the three MCP entry points.

All catalog entries and student identifiers are fictional demonstration data.
SQLite transactions serialize reservations so two callers cannot take the last copy.
"""

from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import re
import sqlite3
from uuid import uuid4

from .models import Book, HoldResult, ReservationResult, SearchResult, WorkflowStep


CATALOG = [
    ("B001", "Practical Python for Students", "Maya Farah", "python programming", 2),
    ("B002", "Agents and Tools", "Rami Haddad", "agentic systems mcp", 1),
    ("B003", "Introduction to Machine Learning", "Nour Salem", "machine learning", 0),
    ("B004", "Distributed Systems in Practice", "Lina Mansour", "distributed systems", 1),
    ("B005", "Database Fundamentals", "Karim Nasser", "databases sql", 2),
    ("B006", "Agentic Systems Workbook", "Sara Khoury", "agentic systems mcp", 1),
]


class LibraryError(ValueError):
    """A predictable, model-visible domain failure with a stable code."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


def validate_query(query: str) -> str:
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 100:
        raise LibraryError("INVALID_QUERY", "Provide a search query of 1 to 100 nonblank characters.")
    return query.strip()


def validate_student(student_id: str) -> None:
    if not isinstance(student_id, str) or re.fullmatch(r"S[0-9]{4}", student_id) is None:
        raise LibraryError("INVALID_STUDENT_ID", "Use a demo student ID such as S1001 (S plus four digits).")


class LibraryService:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # Initialization happens at server startup, never inside the Data tool.
        try:
            with closing(self._connect()) as conn, conn:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS books (
                        book_id TEXT PRIMARY KEY, title TEXT NOT NULL,
                        author TEXT NOT NULL, topic TEXT NOT NULL,
                        total_copies INTEGER NOT NULL CHECK(total_copies >= 0)
                    );
                    CREATE TABLE IF NOT EXISTS holds (
                        hold_id TEXT PRIMARY KEY,
                        book_id TEXT NOT NULL REFERENCES books(book_id),
                        student_id TEXT NOT NULL, created_at TEXT NOT NULL,
                        UNIQUE(book_id, student_id)
                    );
                """)
                conn.executemany("INSERT OR IGNORE INTO books VALUES (?, ?, ?, ?, ?)", CATALOG)
        except sqlite3.Error as exc:
            raise LibraryError("STORAGE_UNAVAILABLE", "Cannot initialize the library database.") from exc

    def _connect(self, *, readonly: bool = False) -> sqlite3.Connection:
        target = self.db_path.as_uri() + "?mode=ro" if readonly else str(self.db_path)
        conn = sqlite3.connect(target, uri=readonly, timeout=5)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def search_catalog(self, query: str, available_only: bool = False) -> SearchResult:
        """Search title, author, topic, or ID; every whitespace-separated term must match."""
        query = validate_query(query)
        tokens = query.casefold().split()
        try:
            with closing(self._connect(readonly=True)) as conn:
                rows = conn.execute("""
                    SELECT b.*, b.total_copies - COUNT(h.hold_id) AS available_copies
                    FROM books b LEFT JOIN holds h ON h.book_id = b.book_id
                    GROUP BY b.book_id ORDER BY b.book_id
                """).fetchall()
        except sqlite3.Error as exc:
            raise LibraryError("STORAGE_UNAVAILABLE", "Cannot read the library database; retry later.") from exc
        books = []
        for row in rows:
            haystack = " ".join(str(row[k]) for k in ("book_id", "title", "author", "topic")).casefold()
            if all(t in haystack for t in tokens) and (not available_only or row["available_copies"] > 0):
                books.append(Book(**dict(row)))
        # An empty list is a successful lookup, not a system failure.
        return SearchResult(query=query, count=len(books), books=books)

    def create_hold(self, book_id: str, student_id: str) -> HoldResult:
        """Persist one hold; repeating a book/student pair returns its original hold."""
        validate_student(student_id)
        if not isinstance(book_id, str) or re.fullmatch(r"B[0-9]{3}", book_id) is None:
            raise LibraryError("INVALID_BOOK_ID", "Use a book ID such as B001.")
        try:
            with closing(self._connect()) as conn, conn:
                conn.execute("BEGIN IMMEDIATE")
                book = conn.execute("SELECT * FROM books WHERE book_id = ?", (book_id,)).fetchone()
                if book is None:
                    raise LibraryError("BOOK_NOT_FOUND", f"Book {book_id} does not exist; search the catalog first.")
                existing = conn.execute(
                    "SELECT * FROM holds WHERE book_id = ? AND student_id = ?", (book_id, student_id)
                ).fetchone()
                if existing:
                    return HoldResult(status="existing", **dict(existing), message="This hold already exists; no duplicate was created.")
                used = conn.execute("SELECT COUNT(*) FROM holds WHERE book_id = ?", (book_id,)).fetchone()[0]
                if used >= book["total_copies"]:
                    raise LibraryError("BOOK_UNAVAILABLE", f"No copies of {book_id} are available; choose another title.")
                hold = HoldResult(
                    status="created", hold_id="H-" + uuid4().hex[:12], book_id=book_id,
                    student_id=student_id, created_at=datetime.now(timezone.utc).isoformat(),
                    message="Demo hold saved to the local library database.",
                )
                conn.execute("INSERT INTO holds VALUES (?, ?, ?, ?)",
                             (hold.hold_id, book_id, student_id, hold.created_at))
                return hold
        except sqlite3.Error as exc:
            raise LibraryError("STORAGE_UNAVAILABLE", "Cannot save the hold; retry later.") from exc

    def reserve_book(self, query: str, student_id: str) -> ReservationResult:
        """Coordinate the Data and Action implementations for one reservation goal."""
        validate_student(student_id)
        found = self.search_catalog(query, available_only=False)
        steps = [WorkflowStep(tool="search_catalog", detail=f"Found {found.count} matching title(s), ordered by book ID.")]
        if not found.books:
            raise LibraryError("NO_MATCH", "No matching titles; try a broader topic such as python or agentic.")
        for book in found.books:
            try:
                hold = self.create_hold(book.book_id, student_id)
            except LibraryError as exc:
                if exc.code != "BOOK_UNAVAILABLE":
                    raise
                steps.append(WorkflowStep(tool="create_hold", detail=f"{book.book_id}: unavailable; trying the next match."))
                continue
            steps.append(WorkflowStep(tool="create_hold", detail=f"{book.book_id}: {hold.status}; hold {hold.hold_id}."))
            # Report availability after the action, rather than a stale count.
            updated = self.search_catalog(book.book_id).books[0]
            steps.append(WorkflowStep(tool="search_catalog", detail=f"Read {book.book_id} availability after the hold."))
            return ReservationResult(query=found.query, selected_book=updated, hold=hold, steps=steps)
        raise LibraryError("NO_AVAILABLE_BOOK", "All matching titles are unavailable; try another topic.")
