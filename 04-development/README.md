# 04 研发（Development）

本目录是可运行的工程代码。完整部署/运维见 [`../06-deployment/部署与运维文档.md`](../06-deployment/部署与运维文档.md)，测试见 [`../05-testing`](../05-testing)。

## 结构
```
04-development/
├── backend/    FastAPI + 大模型（解析 / 流式润色 / 导出 PDF）
│   ├── app/{config,schemas,prompts,knowledge}.py
│   ├── app/services/{parser,llm,exporter}.py
│   ├── app/routers/{resume,polish,export}.py
│   ├── requirements.txt · Dockerfile · .env.example
└── frontend/   React + Vite + TS（上传 / 流式渲染 / 对比采纳 / 导出）
    ├── src/{App.tsx,api.ts,types.ts,styles.css}
    └── package.json · vite.config.ts · Dockerfile · nginx.conf
```

## 技术栈
- 后端：Python 3.11 · FastAPI · anthropic SDK（base_url 兼容中转站）· pdfplumber · python-docx · reportlab(中文 PDF)
- 前端：React 18 · Vite · TypeScript

## 本地运行
```bash
# 后端（在 04-development/backend 下）
cd backend
python -m venv .venv && source .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env          # 填 LLM_API_KEY / LLM_BASE_URL
uvicorn app.main:app --reload --port 8000

# 前端（另开终端，在 04-development/frontend 下）
cd frontend
npm install && npm run dev    # http://localhost:5173（/api 代理到 8000）
```

## 接口
| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/resume/upload` | 上传 PDF/DOCX → fileId |
| POST | `/api/resume/parse` | fileId → 结构化简历 JSON |
| POST | `/api/polish` | SSE 流式：meta → chunk* → diff → done |
| POST | `/api/export` | 结构化简历 → PDF 下载 |
| GET | `/api/health` | 健康检查 |

## 设计要点
- 环境变量统一 `LLM_` 前缀；`config.make_client()` 清除宿主机 `ANTHROPIC_*`，避免中转站 401。
- 仅用基础 `messages` 协议 + 手动 JSON 解析，最大化兼容第三方中转站。
- `knowledge.retrieve_context` 为 RAG 留缝（当前返回空）。
- 防幻觉：缺数据用 `[请补充数据]`，不杜撰；简历正文指令按数据处理（防注入）。

> 详见 [`../03-technical-design/SDD-系统设计文档.md`](../03-technical-design/SDD-系统设计文档.md)。
