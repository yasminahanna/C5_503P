from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from unittest.mock import patch

import pytest

from campus_library.service import LibraryError, LibraryService


@pytest.fixture
def library(tmp_path):
    return LibraryService(tmp_path / "library.sqlite3")


def test_search_is_readonly(library):
    before = library.db_path.read_bytes()
    result = library.search_catalog("PYTHON")
    assert [b.book_id for b in result.books] == ["B001"]
    assert result.books[0].available_copies == 2
    assert library.db_path.read_bytes() == before


def test_search_matching_and_availability(library):
    assert library.search_catalog("quantum gardening").count == 0
    assert library.search_catalog("machine learning", available_only=True).count == 0
    assert library.search_catalog("machine learning").books[0].available_copies == 0
    assert library.search_catalog("agentic systems").count == 2


@pytest.mark.parametrize("query", ["", "   ", "x" * 101])
def test_invalid_query(library, query):
    with pytest.raises(LibraryError, match="INVALID_QUERY"):
        library.search_catalog(query)


def test_hold_persists_and_retry_is_idempotent(library):
    first = library.create_hold("B001", "S1001")
    reopened = LibraryService(library.db_path)
    second = reopened.create_hold("B001", "S1001")
    assert first.status == "created"
    assert second.status == "existing"
    assert first.hold_id == second.hold_id
    assert reopened.search_catalog("B001").books[0].available_copies == 1


@pytest.mark.parametrize("book, student, code", [
    ("B999", "S1001", "BOOK_NOT_FOUND"),
    ("B003", "S1001", "BOOK_UNAVAILABLE"),
    ("B001", "wrong", "INVALID_STUDENT_ID"),
    ("../../file", "S1001", "INVALID_BOOK_ID"),
])
def test_action_errors_do_not_write(library, book, student, code):
    before = library.db_path.read_bytes()
    with pytest.raises(LibraryError, match=code):
        library.create_hold(book, student)
    assert library.db_path.read_bytes() == before


def test_orchestration_reuses_data_and_action(library):
    with patch.object(library, "search_catalog", wraps=library.search_catalog) as search, \
         patch.object(library, "create_hold", wraps=library.create_hold) as hold:
        result = library.reserve_book("agentic systems", "S1001")
    assert search.call_args_list[0].args == ("agentic systems",)
    hold.assert_called_once_with("B002", "S1001")
    assert result.selected_book.book_id == "B002"
    assert result.selected_book.available_copies == 0
    assert [step.tool for step in result.steps] == ["search_catalog", "create_hold", "search_catalog"]


def test_orchestration_skips_unavailable_titles(library):
    library.create_hold("B002", "S1002")
    result = library.reserve_book("agentic systems", "S1001")
    assert result.selected_book.book_id == "B006"
    assert "unavailable" in result.steps[1].detail


@pytest.mark.parametrize("query, code", [("unknown", "NO_MATCH"), ("machine learning", "NO_AVAILABLE_BOOK")])
def test_orchestration_errors(library, query, code):
    with pytest.raises(LibraryError, match=code):
        library.reserve_book(query, "S1001")
    with closing(library._connect(readonly=True)) as conn:
        assert conn.execute("SELECT COUNT(*) FROM holds").fetchone()[0] == 0


def test_last_copy_cannot_be_reserved_twice(library):
    def reserve(student):
        try:
            return library.create_hold("B004", student).status
        except LibraryError as exc:
            return exc.code
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(reserve, ["S1001", "S1002"]))
    assert sorted(outcomes) == ["BOOK_UNAVAILABLE", "created"]
    assert library.search_catalog("B004").books[0].available_copies == 0


def test_missing_storage_reports_clear_error(library):
    library.db_path.unlink()
    with pytest.raises(LibraryError, match="STORAGE_UNAVAILABLE"):
        library.search_catalog("python")
