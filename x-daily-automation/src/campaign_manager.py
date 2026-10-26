from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List


def build_planning_records(
    discovered_posts: List[Dict[str, str]],
    impression_target: int = 1000,
    like_target: int = 30,
) -> List[Dict[str, str]]:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    records: List[Dict[str, str]] = []
    for post in discovered_posts:
        records.append(
            {
                "post_id": post["post_id"],
                "post_url": post["post_url"],
                "text": post.get("text", ""),
                "created_at": post["created_at"],
                "discovered_at": post["discovered_at"],
                "status": "DISCOVERED",
                "promotion_status": "NOT_STARTED",
                "impression_target": impression_target,
                "like_target": like_target,
                "authorized_campaign_reference": None,
                "budget": None,
                "performance_metrics": None,
                "last_update_at": now,
                "errors": [],
            }
        )
    return records
