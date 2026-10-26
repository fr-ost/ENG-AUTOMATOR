from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from src.campaign_manager import build_planning_records
from src.config import ConfigError, load_config
from src.reporter import build_report_markdown, write_daily_report
from src.scanner import Scanner
from src.smm_client import SMMApiError, SMMClient
from src.storage import StateError, file_lock, load_state, save_state, utc_now_iso
from src.telegram import TelegramError, send_telegram_report
from src.x_client import XApiError, XClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")



def run() -> int:
    errors: list[str] = []
    try:
        cfg = load_config()
    except ConfigError as exc:
        logging.error("Configuration error: %s", exc)
        return 2

    try:
        with file_lock(cfg.lock_file):
            state = load_state(cfg.state_file, allow_recovery=os.getenv("ALLOW_STATE_RECOVERY", "false").lower() == "true")

            x_client = XClient(cfg.x_bearer_token, cfg.x_username, timeout=cfg.timeout_seconds)
            scanner = Scanner(
                client=x_client,
                include_quotes=cfg.include_quotes,
                overlap_minutes=cfg.checkpoint_overlap_minutes,
                first_run_lookback_hours=cfg.scan_lookback_hours_first_run,
            )

            user_id = cfg.x_user_id or x_client.resolve_user_id()
            discovered_at = utc_now_iso()
            scan = scanner.discover(
                user_id=user_id,
                existing_records=state.posts,
                last_successful_scan_at=state.last_successful_scan_at,
                discovered_at=discovered_at,
            )

            planning_records = build_planning_records(scan.new_records)
            state.posts.extend(planning_records)

            smm_balance = None
            smm_request_count = 0
            smm_status_checks = {}
            if cfg.smm_enabled and cfg.smm_api_key:
                try:
                    smm = SMMClient(api_url=cfg.smm_api_url, api_key=cfg.smm_api_key, timeout=cfg.timeout_seconds)
                    smm_balance_obj = smm.get_balance()
                    smm_balance = f"{smm_balance_obj.balance} {smm_balance_obj.currency}"
                    if cfg.smm_query_services:
                        smm.list_services()
                    for order_id in cfg.smm_status_order_ids:
                        smm_status_checks[order_id] = smm.get_status(order_id)
                    smm_request_count = smm.request_count
                except SMMApiError as exc:
                    errors.append(str(exc))

            state.last_successful_scan_at = discovered_at
            save_state(cfg.state_file, state)

            report = build_report_markdown(
                report_time_utc=datetime.now(timezone.utc),
                new_records=planning_records,
                duplicates_skipped=scan.duplicates_skipped,
                api_requests_x=x_client.request_count,
                api_requests_smm=smm_request_count,
                smm_balance=smm_balance,
                smm_status_checks=smm_status_checks,
                errors=errors,
                pricing_note="X API pricing varies by access tier; estimate manually from your account plan.",
            )
            report_path = write_daily_report(cfg.reports_dir, report)

            if cfg.telegram_enabled:
                try:
                    if not cfg.telegram_bot_token or not cfg.telegram_chat_id:
                        raise TelegramError("Telegram is enabled but TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing")
                    send_telegram_report(cfg.telegram_bot_token, cfg.telegram_chat_id, report, timeout=cfg.timeout_seconds)
                except TelegramError as exc:
                    logging.error("Telegram notification failed: %s", exc)
                    errors.append(str(exc))

            logging.info(
                "Scan completed: new_posts=%s duplicates=%s report=%s", len(planning_records), scan.duplicates_skipped, report_path
            )
            return 0
    except (StateError, XApiError) as exc:
        logging.error("Scan failed: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(run())
