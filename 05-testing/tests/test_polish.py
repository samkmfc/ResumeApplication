"""润色服务测试：结构化简历转文本 + diff schema 结构（不调用真实 API）。"""
from app.schemas import (
    Basics,
    DiffItem,
    ExperienceItem,
    PolishResult,
    ResumeStructured,
)
from app.services.llm import _resume_to_text


def _sample_resume() -> ResumeStructured:
    return ResumeStructured(
        basics=Basics(name="张三", title="产品经理", email="z@x.com"),
        summary="负责产品工作",
        experience=[
            ExperienceItem(
                company="ABC", role="产品经理", period="2022-2024",
                bullets=["负责数据处理", "对接研发"],
            )
        ],
        skills=["Axure", "SQL"],
    )


def test_resume_to_text_contains_sections():
    text = _resume_to_text(_sample_resume())
    assert "张三" in text
    assert "【工作经历】" in text
    assert "负责数据处理" in text
    assert "【技能】" in text


def test_resume_to_text_empty_resume():
    # 空简历不应抛异常
    text = _resume_to_text(ResumeStructured())
    assert isinstance(text, str)


def test_polish_result_schema_roundtrip():
    result = PolishResult(
        resume=_sample_resume(),
        diffs=[
            DiffItem(
                section="工作经历",
                original="负责数据处理",
                polished="主导清洗与结构化 5w+ 条多源数据",
                reason="强化动词并量化成果",
            )
        ],
    )
    dumped = result.model_dump_json()
    restored = PolishResult.model_validate_json(dumped)
    assert restored.diffs[0].section == "工作经历"
    assert "量化" in restored.diffs[0].reason
