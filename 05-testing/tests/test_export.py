"""导出测试：结构化简历 → PDF 字节流（中文可渲染）。"""
from app.schemas import Basics, ExperienceItem, ResumeStructured
from app.services.exporter import resume_to_pdf


def test_export_pdf_bytes():
    resume = ResumeStructured(
        basics=Basics(name="张三", title="产品经理", email="z@x.com"),
        summary="主导 AI 求职辅导平台从 0 到 1。",
        experience=[
            ExperienceItem(
                company="ABC", role="产品经理", period="2022-2024",
                bullets=["主导清洗与结构化 5w+ 条多源数据"],
            )
        ],
        skills=["Axure", "SQL"],
    )
    data = resume_to_pdf(resume)
    assert data[:5] == b"%PDF-"  # 合法 PDF 头
    assert len(data) > 800


def test_export_empty_resume_no_crash():
    data = resume_to_pdf(ResumeStructured())
    assert data[:5] == b"%PDF-"
