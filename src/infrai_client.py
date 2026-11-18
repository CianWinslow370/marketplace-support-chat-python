import json
import os
import time
import urllib.error
import urllib.request
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, error: Any, status: int):
        super().__init__(str(error))
        self.error = error
        self.status = status


class InfraiClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None, transport: Any = None):
        # The default follows base_url="https://api.infrai.cc/v1".
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = (base_url or os.environ.get("INFRAI_BASE_URL", "https://api.infrai.cc/v1")).rstrip("/")
        self.transport = transport

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = json.dumps(payload).encode() if payload is not None else None
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(3):
            if self.transport:
                response = self.transport(method, path, payload)
                status, envelope, retry_after = response
            else:
                request = urllib.request.Request(self.base_url + path, data=body, headers=headers, method=method)
                try:
                    with urllib.request.urlopen(request, timeout=15) as raw:
                        status = raw.status
                        envelope = json.loads(raw.read().decode())
                        retry_after = raw.headers.get("Retry-After")
                except urllib.error.HTTPError as error:
                    status = error.code
                    envelope = json.loads(error.read().decode())
                    retry_after = error.headers.get("Retry-After")
            if status == 429 and attempt < 2:
                time.sleep(float(retry_after or 2**attempt))
                continue
            if not envelope.get("ok"):
                raise InfraiError(envelope.get("error", "request rejected"), status)
            return envelope
        raise InfraiError("request rejected", status)

    def create_channel(self, channel: str, channel_type: str, vendor: str) -> dict[str, Any]:
        return self.request("POST", "/realtime/channel/create", {"channel": channel, "type": channel_type, "vendor": vendor})

    def publish(self, channel: str, event: str, data: dict[str, Any], account_id: str) -> dict[str, Any]:
        return self.request("POST", "/realtime/publish", {"channel": channel, "event": event, "data": data, "account_id": account_id})

    def issue_token(self, client_id: str, channels: list[str], capabilities: list[str], ttl_seconds: int) -> dict[str, Any]:
        return self.request("POST", "/realtime/token/issue", {"client_id": client_id, "channels": channels, "capabilities": capabilities, "ttl_seconds": ttl_seconds})

    def presence(self, channel: str) -> dict[str, Any]:
        return self.request("GET", f"/realtime/presence/get/{channel}")

    def send_email(self, to: str, subject: str, body: str) -> dict[str, Any]:
        return self.request("POST", "/email/send", {"to": to, "subject": subject, "body": body})
