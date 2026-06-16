"""导出：结构化简历 → PDF（单栏专业风，内置中文字体）。"""
from __future__ import annotations

import io

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from ..schemas import ResumeStructured

# 注册 reportlab 内置 CJK 字体，无需外部字体文件即可输出中文
_FONT = "STSong-Light"
_font_registered = False


def _ensure_font() -> None:
    global _font_registered
    if not _font_registered:
        pdfmetrics.registerFont(UnicodeCIDFont(_FONT))
        _font_registered = True


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()["Normal"]
    return {
        "name": ParagraphStyle(
            "name", parent=base, fontName=_FONT, fontSize=20,
            alignment=TA_CENTER, spaceAfter=4, leading=24,
        ),
        "contact": ParagraphStyle(
            "contact", parent=base, fontName=_FONT, fontSize=9,
            alignment=TA_CENTER, textColor="#666666", spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base, fontName=_FONT, fontSize=13,
            textColor="#2f6df0", spaceBefore=10, spaceAfter=4, leading=16,
        ),
        "sub": ParagraphStyle(
            "sub", parent=base, fontName=_FONT, fontSize=10.5,
            spaceAfter=2, leading=14,
        ),
        "body": ParagraphStyle(
            "body", parent=base, fontName=_FONT, fontSize=10,
            leftIndent=10, spaceAfter=2, leading=15, textColor="#222222",
        ),
    }


def _esc(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def resume_to_pdf(resume: ResumeStructured) -> bytes:
    """渲染单栏专业风 PDF，返回字节流。"""
    _ensure_font()
    st = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
    )
    flow: list = []

    b = resume.basics
    if b.name:
        flow.append(Paragraph(_esc(b.name), st["name"]))
    contact = " | ".join(x for x in [b.title, b.phone, b.email, b.location] if x)
    if contact:
        flow.append(Paragraph(_esc(contact), st["contact"]))

    def section(title: str) -> None:
        flow.append(Paragraph(_esc(title), st["h2"]))
        flow.append(HRFlowable(width="100%", thickness=0.6, color="#dddddd", spaceAfter=4))

    if resume.summary:
        section("个人简介")
        flow.append(Paragraph(_esc(resume.summary), st["body"]))

    if resume.experience:
        section("工作经历")
        for e in resume.experience:
            head = " | ".join(x for x in [e.company, e.role, e.period] if x)
            flow.append(Paragraph(f"<b>{_esc(head)}</b>", st["sub"]))
            for x in e.bullets:
                flow.append(Paragraph("• " + _esc(x), st["body"]))

    if resume.projects:
        section("项目经历")
        for p in resume.projects:
            head = " | ".join(x for x in [p.name, p.role, p.period] if x)
            flow.append(Paragraph(f"<b>{_esc(head)}</b>", st["sub"]))
            for x in p.bullets:
                flow.append(Paragraph("• " + _esc(x), st["body"]))

    if resume.education:
        section("教育背景")
        for ed in resume.education:
            head = " | ".join(x for x in [ed.school, ed.major, ed.degree, ed.period] if x)
            flow.append(Paragraph(_esc(head), st["sub"]))

    if resume.skills:
        section("技能")
        flow.append(Paragraph(_esc("、".join(resume.skills)), st["body"]))

    if not flow:
        flow.append(Spacer(1, 1))
    doc.build(flow)
    return buf.getvalue()
