"""
Binance Futures Testnet API client.

Handles:
- HMAC-SHA256 request signing
- Timestamp injection + recvWindow
- Timed HTTP GET / POST via requests
- Structured logging: REQUEST → RESPONSE (with elapsed time)
- Clean error propagation via custom exceptions
"""

import hashlib
import hmac
import os
import time
import urllib.parse
from typing import Any, Dict, Optional

import requests

from bot.logging_config import get_logger

logger = get_logger(__name__)

# ── Custom exceptions ─────────────────────────────────────────────────────────


class BinanceAPIError(Exception):
    """Raised when Binance returns a non-2xx status or an error payload."""

    def __init__(self, status_code: int, code: int, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(f"[HTTP {status_code}] Binance error {code}: {message}")


class BinanceNetworkError(Exception):
    """Raised on connection/timeout/parse failures."""


# ── Client ────────────────────────────────────────────────────────────────────


class BinanceClient:
    """
    Thin, stateless HTTP client for Binance USDT-M Futures Testnet.

    Usage
    -----
    client = BinanceClient()           # reads API_KEY, API_SECRET, BASE_URL from env
    response = client.post("/fapi/v1/order", params={...}, signed=True)
    """

    _REQUEST_TIMEOUT = 10   # seconds
    _LOG_BODY_MAX    = 400  # chars — keeps logs scannable without hiding useful data

    def __init__(self) -> None:
        self._api_key    = self._require_env("API_KEY")
        self._api_secret = self._require_env("API_SECRET")
        self._base_url   = os.environ.get(
            "BASE_URL", "https://testnet.binancefuture.com"
        ).rstrip("/")

        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": self._api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )

        logger.debug("BinanceClient initialised | base_url=%s", self._base_url)

    # ── Public interface ──────────────────────────────────────────────────────

    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False,
    ) -> Dict[str, Any]:
        return self._request("GET", path, params=params or {}, signed=signed)

    def post(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = True,
    ) -> Dict[str, Any]:
        return self._request("POST", path, params=params or {}, signed=signed)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _request(
        self,
        method: str,
        path: str,
        params: Dict[str, Any],
        signed: bool,
    ) -> Dict[str, Any]:
        if signed:
            params["timestamp"]  = self._timestamp()
            params["recvWindow"] = 5000
            params["signature"]  = self._sign(params)

        url = f"{self._base_url}{path}"
        logger.debug(
            "REQUEST  | %s %s | params=%s",
            method, path, self._redact(params),
        )

        t_start = time.perf_counter()

        try:
            if method == "GET":
                resp = self._session.get(
                    url, params=params, timeout=self._REQUEST_TIMEOUT
                )
            else:
                resp = self._session.post(
                    url, data=params, timeout=self._REQUEST_TIMEOUT
                )
        except requests.exceptions.Timeout as exc:
            elapsed = self._elapsed(t_start)
            logger.error(
                "TIMEOUT  | %s %s | elapsed=%.3fs", method, path, elapsed
            )
            raise BinanceNetworkError(
                f"Request timed out after {elapsed:.1f}s ({url})."
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            elapsed = self._elapsed(t_start)
            logger.error(
                "CONN_ERR | %s %s | elapsed=%.3fs | detail=%s",
                method, path, elapsed, exc,
            )
            raise BinanceNetworkError(
                f"Could not connect to Binance ({url}). "
                "Check your internet connection."
            ) from exc
        except requests.exceptions.RequestException as exc:
            elapsed = self._elapsed(t_start)
            logger.error(
                "NET_ERR  | %s %s | elapsed=%.3fs | detail=%s",
                method, path, elapsed, exc,
            )
            raise BinanceNetworkError(f"Network error: {exc}") from exc

        elapsed = self._elapsed(t_start)

        # ── Structured one-liner: the most important log line ─────────────────
        logger.info(
            "RESPONSE | %s %s | HTTP %s | elapsed=%.3fs",
            method, path, resp.status_code, elapsed,
        )
        logger.debug("BODY     | %s", self._truncate(resp.text))

        return self._parse_response(resp)

    def _parse_response(self, resp: requests.Response) -> Dict[str, Any]:
        try:
            data = resp.json()
        except ValueError:
            logger.error(
                "PARSE_ERR | HTTP %s | body=%s",
                resp.status_code, self._truncate(resp.text),
            )
            raise BinanceNetworkError(
                f"Received non-JSON response (HTTP {resp.status_code})."
            )

        if not resp.ok:
            code    = data.get("code", resp.status_code)
            message = data.get("msg", resp.text)
            logger.error(
                "API_ERR  | HTTP %s | code=%s | reason=%s",
                resp.status_code, code, message,
            )
            raise BinanceAPIError(resp.status_code, code, message)

        return data

    # ── Crypto / time helpers ─────────────────────────────────────────────────

    def _sign(self, params: Dict[str, Any]) -> str:
        """Return HMAC-SHA256 hex signature of the query string."""
        query_string = urllib.parse.urlencode(params)
        return hmac.new(
            self._api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def _timestamp() -> int:
        return int(time.time() * 1000)

    @staticmethod
    def _elapsed(t_start: float) -> float:
        return time.perf_counter() - t_start

    # ── Safety / display helpers ──────────────────────────────────────────────

    @staticmethod
    def _require_env(key: str) -> str:
        value = os.environ.get(key)
        if not value:
            raise EnvironmentError(
                f"Required environment variable '{key}' is not set. "
                "Please check your .env file."
            )
        return value

    @staticmethod
    def _redact(params: Dict[str, Any]) -> Dict[str, Any]:
        """Return a copy of params with the signature obscured for safe logging."""
        redacted = dict(params)
        if "signature" in redacted:
            redacted["signature"] = "***"
        return redacted

    def _truncate(self, text: str) -> str:
        """Truncate a raw body string for log readability."""
        if len(text) <= self._LOG_BODY_MAX:
            return text
        return text[: self._LOG_BODY_MAX] + f" … (+{len(text) - self._LOG_BODY_MAX} chars)"