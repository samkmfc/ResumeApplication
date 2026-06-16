# AI 智能求职辅导 Agent 平台 · 简历润色

**背景**：求职者海投简历，但简历与目标岗位 JD 不匹配，过不了初筛。本平台让求职者上传简历（可附目标 JD），**AI 对齐 JD 改写并给逐条修改意见**，采纳后**直接导出修改好的简历 PDF**。前后端分离，大模型仅在后端调用。

## 仓库结构（按现代产研全流程组织）

| 阶段 | 目录 | 内容 |
|---|---|---|
| 0 立项与调研 | [`00-initiation`](00-initiation) | BRD 商业需求文档（背景/市场/竞品/范围/风险） |
| 1 需求分析 | [`01-requirements`](01-requirements) | 需求分析文档(MRD)、用户画像与用户故事 |
| 2 产品设计 | [`02-product-design`](02-product-design) | PRD 详细设计、原型图(HTML)、交互/状态机 |
| 3 技术设计 | [`03-technical-design`](03-technical-design) | SDD 系统设计文档（架构/接口/数据/选型/安全） |
| 4 研发 | [`04-development`](04-development) | backend(FastAPI)、frontend(React+Vite)、各自 Dockerfile |
| 5 测试 | [`05-testing`](05-testing) | 测试计划、用例(21)、报告（pytest） |
| 6 部署上线 | [`06-deployment`](06-deployment) | docker-compose、CI 样例、部署与运维文档 |
| 7 运营迭代 | [`07-operations`](07-operations) | 指标体系、埋点、Roadmap、复盘、RAG 升级计划 |

## 快速开始（本地）

```bash
# 1) 后端
cd 04-development/backend
python -m venv .venv && source .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env          # 填 LLM_API_KEY / LLM_BASE_URL
uvicorn app.main:app --reload --port 8000

# 2) 前端（另开终端）
cd 04-development/frontend
npm install && npm run dev    # http://localhost:5173

# 3) 测试
cd 05-testing
../04-development/backend/.venv/Scripts/python.exe -m pytest -q
```

打开 **http://localhost:5173**：上传简历 → 填目标 JD → AI 润色 + 逐条意见 → 采纳 → 导出 PDF。

容器化部署见 [`06-deployment/部署与运维文档.md`](06-deployment/部署与运维文档.md)。

## 关键设计决策
- **直连 + RAG 留缝**：JD 由用户提供即岗位需求权威上下文，核心匹配直连大模型；`knowledge.retrieve_context` 为 RAG 注入点，后续接入零改动。
- **中转站兼容**：经 `https://api.cisct.xyz` 调 `claude-opus-4-8`；环境变量用 `LLM_` 前缀隔离，`make_client()` 清除宿主机 `ANTHROPIC_*` 防鉴权头冲突；只用基础 messages 协议 + 手动 JSON，兼容性最强。
- **防幻觉/防注入**：只改表达不编造，缺数据用 `[请补充数据]`；简历正文中的指令按数据处理。
