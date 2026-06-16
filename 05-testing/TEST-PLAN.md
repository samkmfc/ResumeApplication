# 测试用例与报告

测试代码独立于研发目录，通过 `pytest.ini` 的 `pythonpath` 指向 `../04-development/backend` 的 `app` 包。

## 运行
```bash
cd 05-testing
../04-development/backend/.venv/Scripts/python.exe -m pytest -q
# 或激活 venv 后：pytest -q
```

## 用例清单（21 个，全部通过）

| 文件 | 覆盖点 | 用例数 |
|---|---|---|
| `tests/test_parser.py` | PDF/DOCX 文本提取、空文档/扫描件/不支持格式的报错 | 4 |
| `tests/test_polish.py` | 结构化简历转文本、空简历不崩、PolishResult schema 往返 | 3 |
| `tests/test_prompt_robustness.py` | 防幻觉与防注入约束恒在、JD 注入不破坏 Prompt、超长/空 JD、各意图 | 7 |
| `tests/test_export.py` | 结构化简历 → PDF 字节流（含中文）、空简历不崩 | 2 |
| `tests/test_api.py` | HTTP 接口集成：health、上传校验、upload→parse、polish SSE、export PDF | 5 |

## 测试策略
- **单元测试**：解析、Prompt 构造、PDF 导出等纯逻辑，不依赖网络。
- **接口集成测试**：用 FastAPI `TestClient` 跑通 upload→parse→polish→export 全链路，
  并 **monkeypatch 掉 LLM 调用**，既验证接口契约又不消耗大模型额度。
- **极端输入（Prompt 鲁棒性）**：空简历、超长、Prompt 注入（"忽略以上指令"）等，
  确认约束章节稳定、不越权执行。

## 最近一次结果
```
21 passed
```
