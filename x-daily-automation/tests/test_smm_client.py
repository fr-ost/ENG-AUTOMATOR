import pytest

from src.smm_client import SMMApiError, SMMClient


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self.responses = responses

    def post(self, *_args, **_kwargs):
        return self.responses.pop(0)


def test_get_balance_success():
    client = SMMClient("https://smmsoc.com/api/v2", "abc")
    client.session = FakeSession([FakeResponse(200, {"balance": "10.50", "currency": "USD"})])
    balance = client.get_balance()
    assert balance.balance == "10.50"


def test_services_validation():
    client = SMMClient("https://smmsoc.com/api/v2", "abc")
    client.session = FakeSession([FakeResponse(200, {"not": "a list"})])
    with pytest.raises(SMMApiError):
        client.list_services()


def test_auth_failure():
    client = SMMClient("https://smmsoc.com/api/v2", "abc")
    client.session = FakeSession([FakeResponse(401, {"error": "bad key"})])
    with pytest.raises(SMMApiError):
        client.get_balance()
