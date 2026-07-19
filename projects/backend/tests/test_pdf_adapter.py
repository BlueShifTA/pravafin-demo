"""PdfAdapter.parse + _chunk_text edge cases — pure, no DB, no models."""

import pytest
from _pdfgen import make_text_pdf

from coresat.services.ingestion.adapters import _CHUNK_CHARS, PdfAdapter, _chunk_text


def test_whitespace_only_page_yields_no_chunks() -> None:
    valid, rejects = PdfAdapter().parse(make_text_pdf(["      "]), "ws.pdf")
    assert valid == []
    assert rejects == []


def test_blank_middle_page_keeps_chunk_index_sequential_and_page_provenance() -> None:
    # page 2 is blank: it must consume neither a chunk_index nor break page
    # numbering for the chunks that do exist.
    valid, _ = PdfAdapter().parse(
        make_text_pdf(["first page words", "   ", "third page words"]), "mid.pdf"
    )
    assert [(record.page, record.chunk_index) for record in valid] == [(1, 0), (3, 1)]


def test_source_ref_is_required() -> None:
    with pytest.raises(ValueError, match="source_ref"):
        PdfAdapter().parse(make_text_pdf(["x"]), None)


def test_corrupt_payload_raises_clear_value_error() -> None:
    # a non-PDF upload must fail like the CSV adapters (clear ValueError), not
    # leak a raw pypdf stream error.
    with pytest.raises(ValueError, match="could not read PDF"):
        PdfAdapter().parse(b"this is definitely not a pdf", "bad.pdf")


def test_nul_bytes_are_stripped_from_extracted_text() -> None:
    # Real PDFs (e.g. 10-K filings) surface NUL (0x00) in extracted text;
    # Postgres text columns reject 0x00, so the adapter must strip it before
    # building chunks — otherwise ingestion aborts on the offending document.
    valid, rejects = PdfAdapter().parse(make_text_pdf(["clean\x00text here"]), "nul.pdf")
    assert rejects == []
    assert len(valid) == 1
    assert "\x00" not in valid[0].text
    assert valid[0].text == "cleantext here"


def test_chunk_text_starts_new_chunk_at_the_boundary() -> None:
    # 400 + 1 space + 400 = 801 > 800 → the second word opens a new chunk.
    chunks = list(_chunk_text(" ".join(["a" * 400, "b" * 400])))
    assert len(chunks) == 2


def test_chunk_text_keeps_a_word_longer_than_the_limit() -> None:
    giant = "y" * (_CHUNK_CHARS + 300)
    chunks = list(_chunk_text(f"{giant} tail"))
    assert chunks[0] == giant  # never dropped, even though it exceeds the target
    assert chunks[1] == "tail"


def test_chunk_text_on_blank_input_yields_nothing() -> None:
    assert list(_chunk_text("   \n\t  ")) == []
