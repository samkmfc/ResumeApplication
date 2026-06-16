"""API 集成测试：用 TestClient 跑通 upload→parse→polish→export 链路。

通过 monkeypatch 替换 LLM 调用，避免真实网络请求与额度消耗。
"""
import io

from docx import Document
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import DiffItem, PolishResult, ResumeStructured, Basics

client = TestClient(app)


def _make_docx_bytes(text: str) -> bytes:
    doc = Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _fake_resume() -> ResumeStructured:
    return ResumeStructured(basics=Basics(name="张三"), summary="原始简介", skills=["SQL"])


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_upload_rejects_bad_format():
    r = client.post(
        "/api/resume/upload",
        files={"file": ("a.txt", b"hi", "text/plain")},
    )
    assert r.status_code == 400


def test_upload_and_parse(monkeypatch):
    # mock 结构化解析，避免真实模型调用
    monkeypatch.setattr(
        "app.routers.resume.structure_resume", lambda _t: _fake_resume()
    )
    up = client.post(
        "/api/resume/upload",
        files={
            "file": (
                "r.docx",
                _make_docx_bytes("张三 产品经理 技能 SQL"),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert up.status_code == 200
    file_id = up.json()["fileId"]

    pr = client.post("/api/resume/parse", json={"fileId": file_id})
    assert pr.status_code == 200
    assert pr.json()["basics"]["name"] == "张三"


def test_polish_sse(monkeypatch):
    monkeypatch.setattr(
        "app.routers.polish.stream_polish",
        lambda *a, **k: iter(["润色", "结果"]),
    )
    monkeypatch.setattr(
        "app.routers.polish.build_diff",
        lambda *a, **k: PolishResult(
            resume=_fake_resume(),
            diffs=[DiffItem(section="技能", original="SQL", polished="SQL/Python", reason="补充")],
        ),
    )
    body = {"resume": _fake_resume().model_dump(), "jd": "需要 SQL", "intent": "target"}
    r = client.post("/api/polish", json=body)
    assert r.status_code == 200
    text = r.text
    assert "event: chunk" in text
    assert "event: diff" in text
    assert "event: done" in text


def test_export_pdf_endpoint():
    body = {"resume": _fake_resume().model_dump(), "format": "pdf"}
    r = client.post("/api/export", json=body)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:5] == b"%PDF-"
