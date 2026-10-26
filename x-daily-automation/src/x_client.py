from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests


class XApiError(RuntimeError):
    pass


@dataclass
class XPost:
    post_id: str
    text: str
    created_at: str
    url: str


class XClient:
    base_url = "https://api.x.com/2"

    def __init__(self, bearer_token: str, username: str, timeout: int = 20, max_retries: int = 3):
        self.username = username
        self.timeout = timeout
        self.max_retries = max_retries
        self.request_count = 0
        self.session = requests.Session()
        self.session.headers.update({"Authorization": "Bearer " + bearer_token})

    def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        retries = 0
        while True:
            self.request_count += 1
            response = self.session.request(method, url, params=params, timeout=self.timeout)
            if response.status_code in {429, 500, 502, 503, 504} and retries < self.max_retries:
                wait_seconds = int(response.headers.get("Retry-After", "0")) or 2 ** retries
                time.sleep(min(wait_seconds, 10))
                retries += 1
                continue
            if response.status_code == 401:
                raise XApiError("X API authentication failed (401). Check X_BEARER_TOKEN.")
            if response.status_code >= 400:
                raise XApiError(f"X API request failed ({response.status_code}): {response.text[:300]}")
            try:
                data = response.json()
            except ValueError as exc:
                raise XApiError("X API returned non-JSON response") from exc
            if not isinstance(data, dict):
                raise XApiError("X API response must be a JSON object")
            return data

    def resolve_user_id(self) -> str:
        response = self._request("GET", f"/users/by/username/{self.username}", params={"user.fields": "id"})
        user = response.get("data")
        if not isinstance(user, dict) or "id" not in user:
            raise XApiError("Unable to resolve user ID from X API response")
        return str(user["id"])

    def _build_params(self, since_iso: str, pagination_token: Optional[str]) -> Dict[str, Any]:
        params = {
            "max_results": 100,
            "tweet.fields": "created_at,referenced_tweets",
            "start_time": since_iso,
            "exclude": "replies,reposts",
        }
        if pagination_token:
            params["pagination_token"] = pagination_token
        return params

    def fetch_recent_posts(
        self,
        user_id: str,
        since_iso: str,
        include_quotes: bool = False,
    ) -> Tuple[List[XPost], int]:
        posts: List[XPost] = []
        token: Optional[str] = None
        pages = 0
        while True:
            pages += 1
            params = self._build_params(since_iso=since_iso, pagination_token=token)
            payload = self._request("GET", f"/users/{user_id}/tweets", params=params)
            data = payload.get("data", [])
            if not isinstance(data, list):
                raise XApiError("X API tweets payload has invalid data field")
            for item in data:
                if not isinstance(item, dict):
                    continue
                refs = item.get("referenced_tweets", [])
                if not include_quotes and any(r.get("type") == "quoted" for r in refs if isinstance(r, dict)):
                    continue
                post_id = str(item.get("id", "")).strip()
                created_at = str(item.get("created_at", "")).strip()
                if not post_id or not created_at:
                    continue
                posts.append(
                    XPost(
                        post_id=post_id,
                        text=str(item.get("text", "")),
                        created_at=created_at,
                        url=f"https://x.com/{self.username}/status/{post_id}",
                    )
                )
            token = payload.get("meta", {}).get("next_token") if isinstance(payload.get("meta"), dict) else None
            if not token:
                break
        return posts, pages


def compute_since_timestamp(last_successful_scan_at: Optional[str], overlap_minutes: int, first_run_lookback_hours: int) -> str:
    now = datetime.now(timezone.utc)
    if not last_successful_scan_at:
        return (now - timedelta(hours=first_run_lookback_hours)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    checkpoint = datetime.fromisoformat(last_successful_scan_at.replace("Z", "+00:00"))
    since = checkpoint - timedelta(minutes=overlap_minutes)
    return since.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def serialize_posts(posts: Iterable[XPost], discovered_at: str) -> List[Dict[str, str]]:
    serialized: List[Dict[str, str]] = []
    for post in posts:
        serialized.append(
            {
                "post_id": post.post_id,
                "post_url": post.url,
                "text": post.text,
                "created_at": post.created_at,
                "discovered_at": discovered_at,
                "status": "DISCOVERED",
                "promotion_status": "NOT_STARTED",
            }
        )
    return serialized
