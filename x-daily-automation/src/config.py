from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class ConfigError(ValueError):
    pass


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Config:
    x_bearer_token: str
    x_username: str
    x_user_id: Optional[str]
    include_quotes: bool
    smm_api_url: str
    smm_api_key: Optional[str]
    smm_impression_service_id: Optional[str]
    smm_like_service_id: Optional[str]
    smm_query_services: bool
    smm_status_order_ids: tuple[str, ...]
    telegram_enabled: bool
    telegram_bot_token: Optional[str]
    telegram_chat_id: Optional[str]
    data_dir: Path
    reports_dir: Path
    state_file: Path
    lock_file: Path
    checkpoint_overlap_minutes: int
    scan_lookback_hours_first_run: int
    timeout_seconds: int

    @property
    def smm_enabled(self) -> bool:
        return bool(self.smm_api_key)



def load_config() -> Config:
    token = os.getenv("X_BEARER_TOKEN", "").strip()
    username = os.getenv("X_USERNAME", "").strip().lstrip("@")
    if not token:
        raise ConfigError("X_BEARER_TOKEN is required")
    if not username:
        raise ConfigError("X_USERNAME is required")

    data_dir = Path(os.getenv("DATA_DIR", "data")).resolve()
    reports_dir = Path(os.getenv("REPORTS_DIR", "reports")).resolve()

    state_file = Path(os.getenv("STATE_FILE", str(data_dir / "state.json"))).resolve()
    lock_file = Path(os.getenv("LOCK_FILE", str(data_dir / ".scan.lock"))).resolve()

    overlap = int(os.getenv("CHECKPOINT_OVERLAP_MINUTES", "15"))
    lookback = int(os.getenv("FIRST_RUN_LOOKBACK_HOURS", "72"))
    timeout = int(os.getenv("HTTP_TIMEOUT_SECONDS", "20"))

    smm_api_url = os.getenv("SMM_API_URL", "https://smmsoc.com/api/v2").strip()
    if not smm_api_url.startswith("https://"):
        raise ConfigError("SMM_API_URL must use HTTPS")

    return Config(
        x_bearer_token=token,
        x_username=username,
        x_user_id=os.getenv("X_USER_ID"),
        include_quotes=_env_bool("X_INCLUDE_QUOTES", False),
        smm_api_url=smm_api_url,
        smm_api_key=os.getenv("SMM_API_KEY"),
        smm_impression_service_id=os.getenv("SMM_IMPRESSION_SERVICE_ID"),
        smm_like_service_id=os.getenv("SMM_LIKE_SERVICE_ID"),
        smm_query_services=_env_bool("SMM_QUERY_SERVICES", False),
        smm_status_order_ids=tuple(
            part.strip()
            for part in os.getenv("SMM_STATUS_ORDER_IDS", "").split(",")
            if part.strip()
        ),
        telegram_enabled=_env_bool("TELEGRAM_ENABLED", False),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        data_dir=data_dir,
        reports_dir=reports_dir,
        state_file=state_file,
        lock_file=lock_file,
        checkpoint_overlap_minutes=overlap,
        scan_lookback_hours_first_run=lookback,
        timeout_seconds=timeout,
    )
