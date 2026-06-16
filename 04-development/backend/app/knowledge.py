"""知识增强注入点（RAG 留缝）。

当前为直连模式：retrieve_context 返回空字符串，主链路不依赖任何外部检索。
后续接入 RAG 时，只需在此实现向量检索（岗位 JD/面经/优秀简历范式等），
把召回的岗位级增值知识拼成一段文本返回，prompts.build_polish_system 会自动注入，
主链路与接口无需改动。
"""
from __future__ import annotations

from .schemas import Intent


def retrieve_context(jd: str, intent: Intent) -> str:
    """返回与目标岗位相关的增值知识文本；直连模式下为空。

    后续 RAG 实现示例（伪代码）：
        query = jd or intent.value
        hits = vector_store.search(query, top_k=3)   # 岗位JD/面经/范式语料
        return "\n".join(h.text for h in hits)
    """
    return ""
