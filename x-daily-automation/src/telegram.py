from __future__ import annotations

from typing import Iterable

import requests


class TelegramError(RuntimeError):
    pass


def _chunks(text: str, chunk_size: int = 4000) -> Iterable[str]:
    for idx in range(0, len(text), chunk_size):
        yield text[idx : idx + chunk_size]


def send_telegram_report(bot_token: str, chat_id: str, message: str, timeout: int = 20) -> None:
    endpoint = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    for part in _chunks(message):
        response = requests.post(
            endpoint,
            json={"chat_id": chat_id, "text": part, "disable_web_page_preview": True},
            timeout=timeout,
        )
        if response.status_code >= 400:
            raise TelegramError(f"Telegram API failed with status {response.status_code}")
