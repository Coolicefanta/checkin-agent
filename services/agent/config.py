"""
集中参数仓 --- 所有可调参数集中在此声明
原则: 参数改一处生效, 不散落在各个模块的硬编码中
"""
from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    """支持的LLM提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    LOCAL = "local"


class LockProvider(str, Enum):
    """锁状态存储后端"""
    REDIS = "redis"
    IN_MEMORY = "in_memory"


# ---------------------------------------------------------------------------
# 层 1: 运行时 & 环境
# ---------------------------------------------------------------------------
class RuntimeSettings(BaseSettings):
    """运行时层---环境, 端口, 日志级别"""
    model_config = SettingsConfigDict(env_prefix="CHECKIN_", env_file=".env", extra="ignore")

    env: str = Field(default="development", description="运行环境")
    log_level: str = Field(default="INFO", description="日志级别")
    debug: bool = Field(default=False, description="是否开启调试模式")
    agent_host: str = Field(default="0.0.0.0", description="Agent服务监听地址")
    agent_port: int = Field(default=8000, ge=1024, le=65535, description="Agent服务端口")
    tool_api_host: str = Field(default="0.0.0.0", description="Tool API服务监听地址")
    tool_api_port: int = Field(default=8001, ge=1024, le=65535, description="Tool API服务端口")
    memory_api_host: str = Field(default="0.0.0.0", description="Memory服务监听地址")
    memory_api_port: int = Field(default=8002, ge=1024, le=65535, description="Memory服务端口")


# ---------------------------------------------------------------------------
# 层 2: LLM 配置
# ---------------------------------------------------------------------------
class LLMSettings(BaseSettings):
    """LLM层---模型选择, 温度, 超时"""
    model_config = SettingsConfigDict(env_prefix="CHECKIN_LLM_", env_file=".env", extra="ignore")

    provider: LLMProvider = Field(default=LLMProvider.DEEPSEEK, description="LLM提供商")
    model: str = Field(default="deepseek-chat", description="模型名称")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="温度, 值机场景保持低温度")
    max_tokens: int = Field(default=4096, ge=256, le=32768, description="最大输出token数")
    request_timeout: int = Field(default=30, ge=5, le=120, description="请求超时秒数")
    max_retries: int = Field(default=2, ge=0, le=5, description="LLM调用失败最大重试次数")


# ---------------------------------------------------------------------------
# 层 3: Agent图 & Loop边界
# ---------------------------------------------------------------------------
class LoopSettings(BaseSettings):
    """Loop边界层---四个有界Loop的上限值"""
    model_config = SettingsConfigDict(env_prefix="CHECKIN_LOOP_", env_file=".env", extra="ignore")

    repush_max: int = Field(default=3, ge=0, le=10, description="Loop A 重推上限")
    clarify_max: int = Field(default=1, ge=0, le=5, description="Loop B 澄清上限")
    reseat_max: int = Field(default=3, ge=0, le=10, description="Loop C 换座上限")
    tool_retry_max: int = Field(default=2, ge=0, le=5, description="Loop D 工具重试上限")


# ---------------------------------------------------------------------------
# 层 4: 评分权重 & 冷启动
# ---------------------------------------------------------------------------
class ScoreSettings(BaseSettings):
    """评分权重层---软偏好打分公式的全部可调权重"""
    model_config = SettingsConfigDict(env_prefix="CHECKIN_SCORE_", env_file=".env", extra="ignore")

    window_weight: float = Field(default=0.30, ge=0.0, le=1.0, description="靠窗偏好权重")
    aisle_weight: float = Field(default=0.25, ge=0.0, le=1.0, description="过道偏好权重")
    front_weight: float = Field(default=0.20, ge=0.0, le=1.0, description="靠前权重")
    rear_weight: float = Field(default=0.15, ge=0.0, le=1.0, description="靠后权重")
    away_from_toilet_weight: float = Field(default=0.10, ge=0.0, le=1.0, description="远离厕所权重")
    cold_start_long_term_scale: float = Field(default=0.3, ge=0.0, le=1.0,
                                               description="冷启动时long_term权重的缩放因子")
    cold_start_implicit_boost: float = Field(default=1.2, ge=1.0, le=2.0,
                                              description="冷启动时隐式偏好的增强系数")


# ---------------------------------------------------------------------------
# 层 5: 锁 & 状态机
# ---------------------------------------------------------------------------
class LockSettings(BaseSettings):
    """锁层---锁TTL, 幂等窗口"""
    model_config = SettingsConfigDict(env_prefix="CHECKIN_LOCK_", env_file=".env", extra="ignore")

    ttl_seconds: int = Field(default=180, ge=30, le=3600, description="座位临时锁TTL(秒)")
    provider: LockProvider = Field(default=LockProvider.REDIS, description="锁后端")
    idempotency_window_seconds: int = Field(default=3600, ge=60, le=86400, description="幂等键有效窗口(秒)")
    redis_url: str = Field(default="redis://localhost:6379", description="Redis连接串")
    sqlite_path: str = Field(default="/data/checkin.db", description="SQLite路径(开发用)")
    pool_size: int = Field(default=5, ge=1, le=50, description="连接池大小")
    pool_max_overflow: int = Field(default=10, ge=0, le=50, description="连接池溢出上限")


# ---------------------------------------------------------------------------
# 层 6: 数据库
# ---------------------------------------------------------------------------
class DatabaseSettings(BaseSettings):
    """数据库层"""
    model_config = SettingsConfigDict(env_prefix="CHECKIN_DB_", env_file=".env", extra="ignore")

    postgres_dsn: str = Field(default="postgresql://postgres:postgres@localhost:5432/checkin", description="PostgreSQL DSN")
    sqlite_path: str = Field(default="/data/checkin.db", description="SQLite路径(开发用)")
    pool_size: int = Field(default=5, ge=1, le=50, description="连接池大小")
    pool_max_overflow: int = Field(default=10, ge=0, le=50, description="连接池溢出上限")


# ---------------------------------------------------------------------------
# 层 7: HITL(人在回路)
# ---------------------------------------------------------------------------
class HITLSettings(BaseSettings):
    """人在回路层---超时, 重试"""
    model_config = SettingsConfigDict(env_prefix="CHECKIN_HITL_", env_file=".env", extra="ignore")

    clarify_timeout_seconds: int = Field(default=120, ge=10, le=600, description="澄清等待超时(秒)")
    confirm_timeout_seconds: int = Field(default=180, ge=10, le=600, description="确认等待超时(秒)")
    max_clarify_attempts: int = Field(default=1, ge=0, le=3, description="最大澄清重试次数")



# ---------------------------------------------------------------------------
# 层 6: 数据库
# ---------------------------------------------------------------------------
class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='CHECKIN_DB_', env_file='.env', extra='ignore')
    postgres_dsn: str = Field(default='postgresql://checkin:***@localhost:5432/checkin',
                               description='PostgreSQL DSN')
    sqlite_path: str = Field(default='/data/checkin.db', description='SQLite路径(开发用)')
    pool_size: int = Field(default=5, ge=1, le=50, description='连接池大小')
    pool_max_overflow: int = Field(default=10, ge=0, le=50, description='连接池溢出上限')


# ---------------------------------------------------------------------------
# 聚合配置
# ---------------------------------------------------------------------------
class Settings(BaseSettings):
    """全参数聚合---所有Settings层的组合, 通过settings.xxx访问"""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    runtime: RuntimeSettings = Field(default_factory=RuntimeSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    loop: LoopSettings = Field(default_factory=LoopSettings)
    score: ScoreSettings = Field(default_factory=ScoreSettings)
    lock: LockSettings = Field(default_factory=LockSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    hitl: HITLSettings = Field(default_factory=HITLSettings)

    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent)

    @property
    def prompt_dir(self) -> Path:
        """外置提示词YAML目录"""
        return self.project_root / "config" / "prompts"


# 全局单例
settings = Settings()
