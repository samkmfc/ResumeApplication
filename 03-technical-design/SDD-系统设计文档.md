# SDD 系统设计文档

> 阶段：技术设计　｜　版本：v1.0　｜　日期：2026-06-16
> 上游：`02-product-design/PRD_详细设计.md`　｜　下游：`04-development` 实现

## 1. 设计目标
- 前后端分离，明确大模型 API 数据交互边界。
- 大模型仅在后端调用，密钥不入前端。
- 核心任务（简历↔JD 对齐改写）直连大模型，保留 RAG 注入点。
- 兼容第三方 Anthropic 协议中转站。

## 2. 总体架构

```
┌──────────────┐  HTTP/SSE   ┌───────────────────────────┐   /v1/messages   ┌──────────────────┐
│  前端 Web     │ ──────────▶ │      后端 BFF (FastAPI)     │ ───────────────▶ │  大模型(中转站)    │
│ React+Vite+TS │ ◀── 流式 ── │  解析/编排/流式/导出          │ ◀─────────────── │ claude-opus-4-8  │
└──────────────┘             │  ┌──────────────────────┐ │                  └──────────────────┘
                              │  │ parser  解析→结构化     │ │
                              │  │ knowledge RAG 留缝      │ │
                              │  │ llm     流式润色+diff   │ │
                              │  │ exporter 结构化→PDF     │ │
                              │  └──────────────────────┘ │
                              └───────────────────────────┘
```

### 2.1 分层与数据边界
- **前端**：交互、上传、SSE 流式渲染、对比/采纳、触发导出。**不持有密钥、不直接调模型**。
- **后端 BFF**：唯一对外编排层。文件解析 → RAG 留缝 → Prompt 组装 → 调模型（流式）→ 回传 → 导出。
- **模型边界**：仅服务端调用，密钥在 `.env`；入参限定「结构化简历 + 任务指令(+JD)」。

## 3. 组件设计（后端 `app/`）

| 模块 | 职责 | 关键点 |
|---|---|---|
| `config.py` | 配置 + 客户端工厂 `make_client()` | LLM_ 前缀变量；清除宿主机 `ANTHROPIC_*` 防鉴权头冲突 |
| `schemas.py` | Pydantic 模型 | ResumeStructured / PolishRequest / DiffItem / PolishResult |
| `prompts.py` | Prompt 模板 | 意图路由 + 防幻觉 + 防注入 + 知识注入位 |
| `knowledge.py` | RAG 留缝 | `retrieve_context()` 当前返回空 |
| `services/parser.py` | PDF/DOCX→文本→结构化 | pdfplumber/python-docx；扫描件报错 |
| `services/llm.py` | 流式润色 + 结构化 diff | 纯 messages 协议 + 手动 JSON 解析 |
| `services/exporter.py` | 结构化→PDF | reportlab + STSong-Light 中文字体 |
| `routers/*` | HTTP 路由 | resume / polish(SSE) / export |
| `main.py` | 应用入口 | CORS、路由注册、过期文件清理 |

## 4. 核心时序（润色）

```
前端                后端                                模型
 │  POST /api/polish │                                  │
 │ ─────────────────▶│ retrieve_context() (空)          │
 │                   │ build_polish_system(intent,jd)   │
 │                   │ messages.stream() ──────────────▶│
 │  event: chunk* ◀──┤◀──────── text_stream ────────────│
 │                   │ build_diff(): messages.create ──▶│
 │  event: diff   ◀──┤◀──────── JSON ────────────────────│
 │  event: done   ◀──┤                                  │
```

SSE 事件序列：`meta → chunk* → diff → done`（异常时 `error`）。

## 5. 接口规格

| 方法 | 路径 | 入参 | 出参 |
|---|---|---|---|
| POST | `/api/resume/upload` | multipart 文件(≤10MB, PDF/DOCX) | `{fileId, filename}` |
| POST | `/api/resume/parse` | `{fileId}` | ResumeStructured |
| POST | `/api/polish` | `{resume, jd, intent}` | `text/event-stream` |
| POST | `/api/export` | `{resume, format:"pdf"}` | `application/pdf` |
| GET | `/api/health` | - | `{status:"ok"}` |

意图 `intent`：`polish`(综合) / `target`(岗位定向) / `grammar`(仅语法)。

## 6. 数据模型（ResumeStructured）

```
basics{name,phone,email,location,title}
summary: string
education[]{school,major,degree,period}
experience[]{company,role,period,bullets[]}
projects[]{name,role,period,bullets[]}
skills[]
```
DiffItem{section, original, polished, reason}；PolishResult{resume, diffs[]}。

## 7. 技术选型与理由

| 选型 | 理由 |
|---|---|
| FastAPI | 异步、SSE 友好、Pydantic 原生 |
| anthropic SDK | 通过自定义 base_url 兼容 Anthropic 协议中转站 |
| 纯 messages + 手动 JSON | 中转站不支持 parse/thinking/output_config beta，求最大兼容 |
| pdfplumber/python-docx | 文本版简历解析成熟 |
| reportlab + STSong-Light | 免外部字体文件即可输出中文 PDF |
| React+Vite+TS | SSE 流式渲染成熟、构建快 |

## 8. 中转站接入设计（关键）
- `LLM_BASE_URL=https://api.cisct.xyz`，SDK 自动补 `/v1/messages`，模型 `claude-opus-4-8`。
- **变量隔离**：全部用 `LLM_` 前缀，避免被系统 `ANTHROPIC_BASE_URL` 等劫持。
- **鉴权隔离**：`make_client()` 显式清除 `ANTHROPIC_AUTH_TOKEN/ANTHROPIC_API_KEY/ANTHROPIC_BASE_URL` 并传 `auth_token=None`，否则 SDK 会带上宿主机 Bearer 头导致中转站 401。

## 9. 非功能设计
- **性能**：流式输出降低感知延迟；中转站对 opus 有缓冲（首字偏高），可切换更快模型。
- **可靠**：模型调用异常转为 SSE `error` 事件；diff 失败兜底返回原结构。
- **安全**：密钥仅 `.env`（gitignore）；文件 TTL 清理；Prompt 注入按数据处理。
- **可扩展**：`knowledge.retrieve_context` 为 RAG 注入点，接入后主链路零改动。

## 10. 防幻觉 / 防注入策略
- 系统约束：只改表达与结构、不编造；缺数据用 `[请补充数据]`；简历正文里的指令视为数据。
- 测试：见 `05-testing/tests/test_prompt_robustness.py`。
