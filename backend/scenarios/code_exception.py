"""Fault injection: repeatedly trigger the buggy service's TypeError and
POST each captured exception to the running backend's /api/ingest.
"""
from __future__ import annotations

import argparse
import sys
import time
import traceback
from datetime import datetime
import httpx

from sample_service.buggy_service import compute_total

BAD_PAYLOADS = [
    [{"price": 10}, None, {"price": 5}],
    [None],
    [{"price": 3}, None],
]


def capture_exception(service: str) -> dict | None:
    try:
        compute_total(BAD_PAYLOADS[0])
    except Exception as e:
        return {
            "service": service,
            "exception_type": type(e).__name__,
            "message": str(e),
            "stack_trace": "".join(traceback.format_exception(type(e), e, e.__traceback__)),
            "timestamp": datetime.utcnow().isoformat(),
        }
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--delay", type=float, default=0.2)
    parser.add_argument("--service", default="cart-service")
    args = parser.parse_args()

    fault_injected_at = datetime.utcnow().isoformat()
    print(f"Injecting {args.count} faults into {args.service} at {fault_injected_at}")

    with httpx.Client(base_url=args.url, timeout=5.0) as client:
        for i in range(args.count):
            payload = capture_exception(args.service)
            if payload is None:
                print("No exception raised — the bug may already be fixed!")
                return 0
            r = client.post(
                "/api/ingest",
                json=payload,
                params={"fault_injected_at": fault_injected_at},
            )
            r.raise_for_status()
            result = r.json()
            print(f"  [{i+1}/{args.count}] event={result['event_id']} alert={result.get('alert_id')}")
            time.sleep(args.delay)

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
