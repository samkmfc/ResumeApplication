"""导出路由：返回 PDF 文件流。"""
from __future__ import annotations

import urllib.parse

from fastapi import APIRouter
from fastapi.responses import Response

from ..schemas import ExportRequest
from ..services.exporter import resume_to_pdf

router = APIRouter(prefix="/api", tags=["export"])


@router.post("/export")
async def export(req: ExportRequest) -> Response:
    data = resume_to_pdf(req.resume)
    name = (req.resume.basics.name or "resume").strip() or "resume"
    filename = f"{name}_润色版.pdf"
    quoted = urllib.parse.quote(filename)
    return Response(
        content=data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quoted}",
        },
    )
