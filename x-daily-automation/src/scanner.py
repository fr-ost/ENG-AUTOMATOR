from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .deduplication import deduplicate_posts
from .x_client import XClient, compute_since_timestamp, serialize_posts


@dataclass
class ScanResult:
    new_records: List[Dict[str, str]]
    total_fetched: int
    duplicates_skipped: int
    api_pages: int


class Scanner:
    def __init__(self, client: XClient, include_quotes: bool, overlap_minutes: int, first_run_lookback_hours: int):
        self.client = client
        self.include_quotes = include_quotes
        self.overlap_minutes = overlap_minutes
        self.first_run_lookback_hours = first_run_lookback_hours

    def discover(self, user_id: str, existing_records: List[Dict[str, str]], last_successful_scan_at: str | None, discovered_at: str) -> ScanResult:
        since = compute_since_timestamp(last_successful_scan_at, self.overlap_minutes, self.first_run_lookback_hours)
        posts, pages = self.client.fetch_recent_posts(user_id=user_id, since_iso=since, include_quotes=self.include_quotes)
        serialized = serialize_posts(posts, discovered_at=discovered_at)
        unique = deduplicate_posts(existing_records=existing_records, new_posts=serialized)
        return ScanResult(
            new_records=unique,
            total_fetched=len(serialized),
            duplicates_skipped=len(serialized) - len(unique),
            api_pages=pages,
        )
