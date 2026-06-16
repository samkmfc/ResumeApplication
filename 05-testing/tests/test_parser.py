"""解析服务测试：文本提取与扫描件提示。"""
import io

import pytest
from docx import Document

from app.services.parser import ParseError, extract_text


def _make_docx(text: str) -> bytes:
    doc = Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_extract_docx_ok():
    data = _make_docx("张三\n工作经历\n负责数据处理")
    text = extract_text("resume.docx", data)
    assert "张三" in text
    assert "数据处理" in text


def test_empty_docx_raises():
    data = _make_docx("")
    with pytest.raises(ParseError):
        extract_text("empty.docx", data)


def test_unsupported_format():
    with pytest.raises(ParseError):
        extract_text("resume.txt", b"hello")


def test_scanned_pdf_message():
    # 构造一个无文本的最小 PDF（pdfplumber 提取为空），应给出扫描件提示
    minimal_pdf = (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f \n"
        b"trailer<</Root 1 0 R/Size 4>>\nstartxref\n0\n%%EOF"
    )
    with pytest.raises(ParseError) as exc:
        extract_text("scan.pdf", minimal_pdf)
    assert "扫描件" in str(exc.value) or "文本版" in str(exc.value)
