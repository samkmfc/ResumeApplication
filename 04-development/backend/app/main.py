"""FastAPI 入口：CORS、路由注册、过期文件清理、（可选）托管前端。"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .routers import export, polish, resume


def _cleanup_expired() -> None:
    """删除超过 TTL 的上传文件。"""
    s = get_settings()
    d = Path(s.upload_dir)
    if not d.exists():
        return
    cutoff = time.time() - s.file_ttl_days * 86400
    for f in d.iterdir():
        if f.is_file() and f.stat().st_mtime < cutoff:
            f.unlink(missing_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _cleanup_expired()
    yield


app = FastAPI(title="AI 简历润色平台", version="1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume.router)
app.include_router(polish.router)
app.include_router(export.router)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


# 单服务部署：若配置了 LLM_STATIC_DIR 且目录存在，则由后端托管前端构建产物。
# 必须放在所有 /api 路由注册之后，挂载在 "/" 作为兜底（API 路由优先匹配）。
_static = get_settings().static_dir
if _static and Path(_static).is_dir():
    app.mount("/", StaticFiles(directory=_static, html=True), name="static")

