"""Claude 封装：流式润色 + 结构化 diff 生成。

为兼容第三方中转/代理，只使用基础 messages 协议：
- 不使用 messages.parse / output_config / thinking 等 beta 特性；
- 结构化结果通过"要求模型输出 JSON + 手动解析"实现。
"""
from __future__ import annotations

import json
from collections.abc import Iterator

import anthropic
from pydantic import BaseModel, ValidationError

from ..config import get_settings, make_client
from ..knowledge import retrieve_context
from ..prompts import (
    POLISH_STREAM_INSTRUCTION,
    STRUCTURED_INSTRUCTION,
    build_polish_system,
)
from ..schemas import Intent, PolishResult, ResumeStructured


def _resume_to_text(resume: ResumeStructured) -> str:
    """把结构化简历转成给模型阅读的纯文本。"""
    lines: list[str] = []
    b = resume.basics
    if any([b.name, b.title, b.email, b.phone, b.location]):
        lines.append(f"姓名：{b.name}  职位意向：{b.title}")
        lines.append(f"联系方式：{b.phone} {b.email} {b.location}")
    if resume.summary:
        lines.append(f"\n【个人简介】\n{resume.summary}")
    if resume.experience:
        lines.append("\n【工作经历】")
        for e in resume.experience:
            lines.append(f"- {e.company} | {e.role} | {e.period}")
            lines.extend(f"  · {x}" for x in e.bullets)
    if resume.projects:
        lines.append("\n【项目经历】")
        for p in resume.projects:
            lines.append(f"- {p.name} | {p.role} | {p.period}")
            lines.extend(f"  · {x}" for x in p.bullets)
    if resume.skills:
        lines.append("\n【技能】\n" + "、".join(resume.skills))
    return "\n".join(lines)


def _extract_json(text: str) -> str:
    """从模型输出中抽取 JSON 主体：去除 ```json 代码围栏，截取首个 { 到末个 }。"""
    t = text.strip()
    if "```" in t:
        # 取代码围栏内内容
        parts = t.split("```")
        for seg in parts:
            seg = seg.lstrip()
            if seg.startswith("json"):
                seg = seg[4:]
            seg = seg.strip()
            if seg.startswith("{"):
                t = seg
                break
    start, end = t.find("{"), t.rfind("}")
    if start != -1 and end != -1 and end > start:
        return t[start : end + 1]
    return t


def complete_json(system: str | None, user: str, schema: type[BaseModel], max_tokens: int = 16000):
    """要求模型输出 JSON 并解析为指定 Pydantic 模型；逐个尝试可用模型。"""
    settings = get_settings()
    client = make_client()
    last_err: Exception | None = None
    for model in settings.models_to_try:
        try:
            kwargs: dict = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": user}],
            }
            if system:
                kwargs["system"] = system
            resp = client.messages.create(**kwargs)
            text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
            return schema.model_validate_json(_extract_json(text))
        except (anthropic.APIError, anthropic.APIConnectionError, ValidationError, json.JSONDecodeError) as e:
            last_err = e
            continue
    raise RuntimeError(f"模型结构化输出失败：{last_err}")


def stream_polish(resume: ResumeStructured, jd: str, intent: Intent) -> Iterator[str]:
    """流式输出润色后的简历正文（首字快速呈现）。失败时降级到备用模型。"""
    settings = get_settings()
    client = make_client()
    knowledge = retrieve_context(jd, intent)  # RAG 留缝，直连模式下为空
    system = build_polish_system(intent, jd, knowledge)
    user = f"{POLISH_STREAM_INSTRUCTION}\n\n原始简历：\n{_resume_to_text(resume)}"

    models = settings.models_to_try
    for i, model in enumerate(models):
        try:
            with client.messages.stream(
                model=model,
                max_tokens=8000,
                system=system,
                messages=[{"role": "user", "content": user}],
            ) as stream:
                for text in stream.text_stream:
                    yield text
            return
        except (anthropic.APIError, anthropic.APIConnectionError):
            if i == len(models) - 1:
                raise
            continue


def build_diff(
    resume: ResumeStructured, polished_text: str, jd: str, intent: Intent
) -> PolishResult:
    """基于原始简历 + 润色正文，产出结构化简历与逐处修改说明。"""
    knowledge = retrieve_context(jd, intent)
    system = build_polish_system(intent, jd, knowledge)
    schema_hint = (
        '请只输出 JSON，结构为：{"resume": {结构化简历，含 basics{name,phone,email,location,title},'
        ' summary, education[], experience[{company,role,period,bullets[]}],'
        ' projects[{name,role,period,bullets[]}], skills[]}, '
        '"diffs": [{"section","original","polished","reason"}]}。'
    )
    user = (
        f"{STRUCTURED_INSTRUCTION}\n\n{schema_hint}\n\n"
        f"原始简历：\n{_resume_to_text(resume)}\n\n润色后正文：\n{polished_text}"
    )
    try:
        return complete_json(system, user, PolishResult)
    except Exception:
        # 兜底：至少返回原结构，避免前端崩溃
        return PolishResult(resume=resume, diffs=[])
