from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib import request

from django.conf import settings


def _connector_headers(body: bytes) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "X-Connector-Secret": str(getattr(settings, "CENTRAL_CONNECTOR_SECRET", "") or ""),
    }
    if getattr(settings, "CENTRAL_CONNECTOR_SIGNED", False):
        ts = str(int(time.time()))
        secret = str(getattr(settings, "CENTRAL_CONNECTOR_SECRET", "") or "").encode("utf-8")
        msg = ts.encode("utf-8") + b"." + body
        sig = hmac.new(secret, msg, hashlib.sha256).hexdigest()
        headers["X-Connector-Timestamp"] = ts
        headers["X-Connector-Signature"] = sig
    return headers


def post_connector(path: str, payload: dict) -> dict:
    base = str(getattr(settings, "CENTRAL_PLATFORM_URL", "http://127.0.0.1:8000")).rstrip("/")
    url = f"{base}/api/connectors/{path.lstrip('/')}"
    body = json.dumps(payload, default=str).encode("utf-8")
    req = request.Request(url, data=body, method="POST")
    for key, value in _connector_headers(body).items():
        if value:
            req.add_header(key, value)
    with request.urlopen(req, timeout=20) as resp:
        raw = resp.read().decode("utf-8") or "{}"
        return json.loads(raw)
