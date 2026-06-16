"""应用配置：从环境变量 / .env 读取。

注意：使用 LLM_ 前缀的应用专属变量名，避免被系统已存在的
ANTHROPIC_API_KEY / ANTHROPIC_BASE_URL 等环境变量劫持。
"""
import os
from functools import lru_cache

from anthropic import Anthropic
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="LLM_", extra="ignore")

    api_key: str = ""
    base_url: str = ""  # 留空=官方；中转/代理填其地址（如 https://api.cisct.xyz）
    model: str = "claude-opus-4-8"
    fallback_model: str = ""

    # 所有字段统一带 LLM_ 前缀（env_prefix），如 LLM_UPLOAD_DIR / LLM_CORS_ORIGINS
    upload_dir: str = "./_uploads"
    file_ttl_days: int = 7
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    static_dir: str = ""  # 设置后后端同时托管前端构建产物（单服务部署用）

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def models_to_try(self) -> list[str]:
        ms = [self.model]
        if self.fallback_model.strip() and self.fallback_model != self.model:
            ms.append(self.fallback_model)
        return ms


@lru_cache
def get_settings() -> Settings:
    return Settings()


def make_client() -> Anthropic:
    """统一创建 Anthropic 客户端；支持自定义 base_url（兼容中转/代理）。

    宿主机可能已设置 ANTHROPIC_AUTH_TOKEN / ANTHROPIC_API_KEY / ANTHROPIC_BASE_URL
    （例如 Claude Code 自身的中转配置）。SDK 会自动拾取这些值，导致发出错误的
    Authorization 头而被目标中转站拒绝（401）。这里显式清除，确保只用我们的 key。
    """
    s = get_settings()
    for var in ("ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL"):
        os.environ.pop(var, None)
    kwargs: dict = {"api_key": s.api_key, "auth_token": None}
    if s.base_url.strip():
        kwargs["base_url"] = s.base_url.strip()
    return Anthropic(**kwargs)
