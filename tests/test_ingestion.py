import pytest

from app.services.ingestion import chunk_text


def test_chunking_preserves_order_and_overlap() -> None:
    chunks = chunk_text("one two three four five six seven", chunk_size_words=4, overlap_words=1)
    assert chunks == ["one two three four", "four five six seven", "seven"]


def test_chunking_rejects_invalid_overlap() -> None:
    with pytest.raises(ValueError):
        chunk_text("one two", chunk_size_words=2, overlap_words=2)

