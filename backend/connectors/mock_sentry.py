"""Mock Sentry-style connector.

In a real deployment this would pull from Sentry's API. For the demo we
accept events via HTTP ingest and route them into the detection engine.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pydantic import BaseModel, Field


class SentryEvent(BaseModel):
    service: str
    exception_type: str
    message: str
    stack_trace: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    extra: dict = Field(default_factory=dict)

    def signature(self) -> str:
        # Stable hash over exception type + top stack frame
        first_frame = ""
        for line in self.stack_trace.splitlines():
            line = line.strip()
            if line.startswith("File "):
                first_frame = line
                break
        raw = f"{self.exception_type}|{first_frame}".encode()
        return hashlib.sha1(raw).hexdigest()[:12]

    def to_json(self) -> str:
        return json.dumps(self.model_dump(mode="json"))
