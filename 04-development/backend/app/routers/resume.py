"""简历上传与解析路由。"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from ..config import get_settings
from ..schemas import ParseRequest, ResumeStructured, UploadResponse
from ..services.parser import ParseError, extract_text, structure_resume

router = APIRouter(prefix="/api/resume", tags=["resume"])

_MAX_BYTES = 10 * 1024 * 1024  # 10MB


def _upload_dir() -> Path:
    d = Path(get_settings().upload_dir)
    d.mkdir(parents=True, exist_ok=True)
    return d


@router.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)) -> UploadResponse:
    name = (file.filename or "").lower()
    if not (name.endswith(".pdf") or name.endswith(".docx")):
        raise HTTPException(400, "仅支持 PDF 或 DOCX 文件。")
    data = await file.read()
    if len(data) > _MAX_BYTES:
        raise HTTPException(413, "文件过大，请上传 ≤ 10MB 的简历。")
    file_id = uuid.uuid4().hex
    ext = ".pdf" if name.endswith(".pdf") else ".docx"
    (_upload_dir() / f"{file_id}{ext}").write_bytes(data)
    return UploadResponse(fileId=file_id, filename=file.filename or f"resume{ext}")


@router.post("/parse", response_model=ResumeStructured)
async def parse(req: ParseRequest) -> ResumeStructured:
    matches = list(_upload_dir().glob(f"{req.fileId}.*"))
    if not matches:
        raise HTTPException(404, "文件不存在或已过期，请重新上传。")
    path = matches[0]
    data = path.read_bytes()
    try:
        text = extract_text(path.name, data)
        return structure_resume(text)
    except ParseError as e:
        raise HTTPException(422, str(e)) from e
