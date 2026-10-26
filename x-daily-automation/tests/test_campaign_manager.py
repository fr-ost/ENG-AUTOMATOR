from src.campaign_manager import build_planning_records


def test_build_planning_records_defaults():
    records = build_planning_records(
        [
            {
                "post_id": "123",
                "post_url": "https://x.com/u/status/123",
                "created_at": "2026-01-01T00:00:00Z",
                "discovered_at": "2026-01-02T00:00:00Z",
            }
        ]
    )
    assert records[0]["impression_target"] == 1000
    assert records[0]["like_target"] == 30
    assert records[0]["promotion_status"] == "NOT_STARTED"
