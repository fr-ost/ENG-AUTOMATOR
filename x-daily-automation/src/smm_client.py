from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


class SMMApiError(RuntimeError):
    pass


@dataclass
class SMMAccountBalance:
    balance: str
    currency: str


class SMMClient:
    def __init__(self, api_url: str, api_key: str, timeout: int = 20, max_retries: int = 3):
        if not api_url.startswith("https://"):
            raise SMMApiError("SMM API URL must use HTTPS")
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.request_count = 0
        self.session = requests.Session()

    def _call(self, action: str, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"key": self.api_key, "action": action}
        if extra:
            payload.update(extra)
        retries = 0
        while True:
            self.request_count += 1
            response = self.session.post(self.api_url, data=payload, timeout=self.timeout)
            if response.status_code in {429, 500, 502, 503, 504} and retries < self.max_retries:
                time.sleep(min(2 ** retries, 10))
                retries += 1
                continue
            if response.status_code == 401:
                raise SMMApiError("SMMSOC authentication failed (401). Check SMM_API_KEY.")
            if response.status_code >= 400:
                raise SMMApiError(f"SMMSOC API request failed ({response.status_code})")
            try:
                data = response.json()
            except ValueError as exc:
                raise SMMApiError("SMMSOC API returned non-JSON response") from exc
            if not isinstance(data, dict):
                raise SMMApiError("SMMSOC API response must be a JSON object")
            if "error" in data:
                raise SMMApiError(f"SMMSOC API error: {data['error']}")
            return data

    def get_balance(self) -> SMMAccountBalance:
        data = self._call("balance")
        if "balance" not in data or "currency" not in data:
            raise SMMApiError("SMMSOC balance response missing required fields")
        return SMMAccountBalance(balance=str(data["balance"]), currency=str(data["currency"]))

    def list_services(self) -> Dict[str, Any]:
        data = self._call("services")
        if not isinstance(data, list):
            raise SMMApiError("SMMSOC services response must be a list")
        return {"services": data}

    def get_status(self, order_id: str) -> Dict[str, Any]:
        data = self._call("status", extra={"order": order_id})
        if "status" not in data:
            raise SMMApiError("SMMSOC status response missing status field")
        return data
