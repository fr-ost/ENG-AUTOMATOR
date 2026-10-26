from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from zoneinfo import ZoneInfo


def build_report_markdown(
    report_time_utc: datetime,
    new_records: List[Dict[str, str]],
    duplicates_skipped: int,
    api_requests_x: int,
    api_requests_smm: int,
    smm_balance: Optional[str],
    smm_status_checks: Dict[str, Dict[str, str]],
    errors: Iterable[str],
    pricing_note: str,
) -> str:
    dhaka_time = report_time_utc.astimezone(ZoneInfo("Asia/Dhaka"))
    lines = [
        "# Daily X Automation Report",
        "",
        f"- Scan date (Asia/Dhaka): {dhaka_time.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"- New posts discovered: {len(new_records)}",
        f"- Duplicates skipped: {duplicates_skipped}",
        f"- X API requests: {api_requests_x}",
        f"- SMMSOC API requests: {api_requests_smm}",
        f"- SMMSOC balance: {smm_balance if smm_balance else 'unavailable'}",
        f"- Pricing note: {pricing_note}",
        "",
        "## New Posts",
    ]
    if not new_records:
        lines.append("- None")
    else:
        for row in new_records:
            lines.append(
                f"- {row['post_url']} (targets: impressions={row['impression_target']}, likes={row['like_target']})"
            )
    lines.extend(["", "## Authorized Campaign/Order Status Checks"])
    if not smm_status_checks:
        lines.append("- None")
    else:
        for order_id, status_payload in smm_status_checks.items():
            lines.append(f"- {order_id}: {status_payload.get('status', 'unknown')}")
    lines.extend(["", "## Errors / Incomplete Operations"])
    error_list = list(errors)
    if not error_list:
        lines.append("- None")
    else:
        for error in error_list:
            lines.append(f"- {error}")
    return "\n".join(lines) + "\n"


def write_daily_report(reports_dir: Path, content: str, timestamp: datetime | None = None) -> Path:
    now = timestamp or datetime.now(timezone.utc)
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / f"report-{now.strftime('%Y-%m-%d')}.md"
    report_path.write_text(content, encoding="utf-8")
    return report_path
