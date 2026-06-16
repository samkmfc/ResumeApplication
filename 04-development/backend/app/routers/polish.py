"""润色路由：SSE 流式输出 meta → chunk* → diff → done。"""
from __future__ import annotations

import json

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from ..schemas import PolishRequest
from ..services.llm import build_diff, stream_polish

router = APIRouter(prefix="/api", tags=["polish"])


@router.post("/polish")
async def polish(req: PolishRequest) -> EventSourceResponse:
    def event_gen():
        yield {"event": "meta", "data": json.dumps({"intent": req.intent.value})}

        collected: list[str] = []
        try:
            for chunk in stream_polish(req.resume, req.jd, req.intent):
                collected.append(chunk)
                yield {"event": "chunk", "data": json.dumps({"text": chunk})}
        except Exception as e:  # noqa: BLE001 —— 把模型错误转成可读事件
            yield {"event": "error", "data": json.dumps({"message": f"润色失败：{e}"})}
            return

        polished_text = "".join(collected)
        try:
            result = build_diff(req.resume, polished_text, req.jd, req.intent)
            yield {
                "event": "diff",
                "data": result.model_dump_json(),
            }
        except Exception as e:  # noqa: BLE001
            yield {"event": "error", "data": json.dumps({"message": f"生成对比失败：{e}"})}
            return

        yield {"event": "done", "data": "{}"}

    return EventSourceResponse(event_gen())
