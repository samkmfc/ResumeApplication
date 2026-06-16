"""Pydantic 数据模型：简历结构、润色请求、修改对比项。"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Education(BaseModel):
    school: str = ""
    major: str = ""
    degree: str = ""
    period: str = ""


class ExperienceItem(BaseModel):
    company: str = ""
    role: str = ""
    period: str = ""
    bullets: list[str] = Field(default_factory=list)


class ProjectItem(BaseModel):
    name: str = ""
    role: str = ""
    period: str = ""
    bullets: list[str] = Field(default_factory=list)


class Basics(BaseModel):
    name: str = ""
    phone: str = ""
    email: str = ""
    location: str = ""
    title: str = ""


class ResumeStructured(BaseModel):
    """结构化简历。润色的输入与输出都使用此结构。"""

    basics: Basics = Field(default_factory=Basics)
    summary: str = ""
    education: list[Education] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)


class Intent(str, Enum):
    """意图路由：润色 / 针对岗位优化 / 仅语法修正。"""

    polish = "polish"
    target = "target"
    grammar = "grammar"


class PolishRequest(BaseModel):
    resume: ResumeStructured
    jd: str = ""
    intent: Intent = Intent.polish


class DiffItem(BaseModel):
    """一处修改：原文 / 润色后 / 修改说明。"""

    section: str
    original: str
    polished: str
    reason: str


class PolishResult(BaseModel):
    resume: ResumeStructured
    diffs: list[DiffItem] = Field(default_factory=list)


class ExportFormat(str, Enum):
    pdf = "pdf"


class ExportRequest(BaseModel):
    resume: ResumeStructured
    format: ExportFormat = ExportFormat.pdf


class UploadResponse(BaseModel):
    fileId: str
    filename: str


class ParseRequest(BaseModel):
    fileId: str
