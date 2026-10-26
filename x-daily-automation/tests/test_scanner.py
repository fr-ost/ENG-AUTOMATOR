from src.scanner import Scanner
from src.x_client import XPost


class FakeClient:
    def __init__(self, posts):
        self.posts = posts

    def fetch_recent_posts(self, user_id, since_iso, include_quotes):
        return self.posts, 2


def test_scanner_discovers_and_deduplicates():
    existing = [{"post_id": "1"}]
    client = FakeClient(
        [
            XPost(post_id="1", text="old", created_at="2026-01-01T00:00:00Z", url="https://x.com/a/status/1"),
            XPost(post_id="2", text="new", created_at="2026-01-02T00:00:00Z", url="https://x.com/a/status/2"),
        ]
    )

    scanner = Scanner(client=client, include_quotes=False, overlap_minutes=15, first_run_lookback_hours=72)
    result = scanner.discover("123", existing, "2026-01-02T00:00:00Z", "2026-01-03T00:00:00Z")

    assert result.total_fetched == 2
    assert result.duplicates_skipped == 1
    assert result.api_pages == 2
    assert [r["post_id"] for r in result.new_records] == ["2"]


def test_scanner_empty_scan():
    scanner = Scanner(client=FakeClient([]), include_quotes=False, overlap_minutes=15, first_run_lookback_hours=72)
    result = scanner.discover("123", [], None, "2026-01-03T00:00:00Z")
    assert result.total_fetched == 0
    assert result.new_records == []
