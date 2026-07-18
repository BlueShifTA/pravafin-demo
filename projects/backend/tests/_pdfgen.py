"""Minimal text-PDF builder for ingestion tests (pypdf-extractable).

Not a test module (underscore prefix → pytest skips collection). One Tj-drawn
string per page, correct xref offsets, so page provenance and chunk splitting
are assertable without a PDF-writer dependency.
"""

from collections.abc import Sequence


def make_text_pdf(pages: Sequence[str]) -> bytes:
    objs: dict[int, bytes] = {}
    font_num = 3
    kids: list[int] = []
    next_num = 4
    for body in pages:
        page_num, content_num = next_num, next_num + 1
        next_num += 2
        kids.append(page_num)
        stream = f"BT /F1 12 Tf 72 720 Td ({body}) Tj ET".encode()
        objs[content_num] = b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream"
        objs[page_num] = (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Contents %d 0 R /Resources << /Font << /F1 %d 0 R >> >> >>" % (content_num, font_num)
        )
    objs[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objs[2] = b"<< /Type /Pages /Kids [%s] /Count %d >>" % (
        b" ".join(b"%d 0 R" % k for k in kids),
        len(pages),
    )
    objs[3] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    out = bytearray(b"%PDF-1.4\n")
    offsets: dict[int, int] = {}
    for num in sorted(objs):
        offsets[num] = len(out)
        out += b"%d 0 obj\n" % num + objs[num] + b"\nendobj\n"
    xref_pos = len(out)
    count = max(objs) + 1
    out += b"xref\n0 %d\n0000000000 65535 f \n" % count
    for num in range(1, count):
        out += b"%010d 00000 n \n" % offsets[num]
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF" % (count, xref_pos)
    return bytes(out)
