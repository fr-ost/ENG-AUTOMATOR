from __future__ import annotations

from typing import Dict, Iterable, List, Set


def known_post_ids(existing_records: Iterable[Dict[str, str]]) -> Set[str]:
    return {str(record.get("post_id")) for record in existing_records if record.get("post_id")}


def deduplicate_posts(existing_records: Iterable[Dict[str, str]], new_posts: List[Dict[str, str]]) -> List[Dict[str, str]]:
    known = known_post_ids(existing_records)
    unique: List[Dict[str, str]] = []
    for post in new_posts:
        post_id = str(post["post_id"])
        if post_id in known:
            continue
        known.add(post_id)
        unique.append(post)
    return unique
