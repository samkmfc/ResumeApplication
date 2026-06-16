# 单服务镜像：构建前端 → 由 Python 后端同时托管前端与 API（同源，免 CORS）
# Render 用此 Dockerfile 一键部署。

# ---- 阶段 1：构建前端 ----
FROM node:20-alpine AS frontend
WORKDIR /fe
COPY 04-development/frontend/package*.json ./
RUN npm install
COPY 04-development/frontend/ ./
RUN npm run build          # 产出 /fe/dist

# ---- 阶段 2：后端 + 托管前端 ----
FROM python:3.11-slim
WORKDIR /app
COPY 04-development/backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY 04-development/backend/app ./app
COPY --from=frontend /fe/dist ./static

ENV LLM_STATIC_DIR=/app/static
# Render 会注入 $PORT；本地默认 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
