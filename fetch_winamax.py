import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

API_KEY = os.environ["PULSESCORE_API_KEY"]
BASE = "https://api.pulsescore.net/api/winamax"

# Winamax currently exposes these 16 sports through PulseScore.
SPORTS = [
    "soccer", "tennis", "ice-hockey", "basketball", "baseball",
    "handball", "rugby-union", "rugby-league", "american-football",
    "badminton", "table-tennis", "mma", "boxing", "snooker",
    "volleyball", "australian-rules",
]

OUT = Path("data/winamax_odds.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "X-Secret": API_KEY,
    "Accept-Encoding": "gzip",
    "User-Agent": "winamax-pulsescore-bridge/1.0",
}

def get_events(sport: str):
    # One request per sport keeps the free 500-request monthly allowance
    # usable for an hourly run (16 requests/hour ≈ 384/month).
    url = f"{BASE}/{sport}/events"
    r = requests.get(
        url,
        headers=HEADERS,
        params={"page": 1, "limit": 100},
        timeout=30,
    )
    r.raise_for_status()
    payload = r.json()
    return payload.get("events", payload if isinstance(payload, list) else [])

def main():
    all_events = []
    errors = []

    for sport in SPORTS:
        try:
            events = get_events(sport)
            for event in events:
                event["_source"] = "Winamax"
                event["_pulscore_sport"] = sport
            all_events.extend(events)
        except Exception as exc:
            errors.append({"sport": sport, "error": str(exc)})
        time.sleep(0.2)

    # Keep only upcoming/non-live events when startTime is available.
    now = datetime.now(timezone.utc)
    upcoming = []
    for event in all_events:
        if event.get("live") is True or event.get("live") == 1:
            continue
        raw = event.get("startTime")
        if raw:
            try:
                dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                if dt < now:
                    continue
            except ValueError:
                pass
        upcoming.append(event)

    # Sort by start time where possible.
    upcoming.sort(key=lambda e: e.get("startTime") or "9999")

    output = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "source": "PulseScore / Winamax",
        "eventCount": len(upcoming),
        "sportsRequested": SPORTS,
        "errors": errors,
        "events": upcoming,
    }

    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(upcoming)} upcoming Winamax events to {OUT}")
    if errors:
        print("Warnings:", json.dumps(errors, ensure_ascii=False))

if __name__ == "__main__":
    main()
