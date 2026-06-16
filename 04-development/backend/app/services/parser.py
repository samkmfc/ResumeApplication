"""简历解析：PDF/DOCX → 文本 → 结构化 JSON。"""
from __future__ import annotations

import io

import pdfplumber
from docx import Document

from ..schemas import ResumeStructured


class ParseError(Exception):
    """解析失败（如扫描件无文本）。"""


def extract_text(filename: str, data: bytes) -> str:
    """从 PDF / DOCX 字节流提取纯文本。"""
    name = filename.lower()
    if name.endswith(".pdf"):
        text_parts: list[str] = []
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages:
                text_parts.append(page.extract_text() or "")
        text = "\n".join(text_parts).strip()
        if not text:
            raise ParseError("无法识别文本，可能是扫描件/图片版简历，请上传文本版简历。")
        return text
    if name.endswith(".docx"):
        doc = Document(io.BytesIO(data))
        text = "\n".join(p.text for p in doc.paragraphs).strip()
        if not text:
            raise ParseError("文档为空或无法识别文本。")
        return text
    raise ParseError("仅支持 PDF 或 DOCX 格式。")


_STRUCTURE_PROMPT = (
    "你是简历解析器。将下面的简历纯文本解析为结构化 JSON，尽量完整准确，"
    "无法确定的字段留空字符串或空数组，不要编造内容。\n"
    '只输出 JSON，结构：{"basics":{"name","phone","email","location","title"},'
    '"summary","education":[{"school","major","degree","period"}],'
    '"experience":[{"company","role","period","bullets":[]}],'
    '"projects":[{"name","role","period","bullets":[]}],"skills":[]}\n\n简历文本：\n'
)


def structure_resume(text: str) -> ResumeStructured:
    """用大模型把文本解析成结构化 ResumeStructured（手动 JSON 解析，兼容中转）。"""
    from .llm import complete_json  # 延迟导入，避免循环依赖

    try:
        return complete_json(None, _STRUCTURE_PROMPT + text[:20000], ResumeStructured)
    except Exception as e:  # noqa: BLE001
        raise ParseError(f"结构化解析失败，请重试或检查简历内容：{e}") from e
