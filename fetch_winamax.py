import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

API_KEY = os.environ["PULSESCORE_API_KEY"]
BASE = "https://api.pulsescore.net/api/winamax"
OUT = Path("data/winamax_odds.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "X-Secret": API_KEY,
    "Accept-Encoding": "gzip",
    "User-Agent": "winamax-pulsescore-bridge/3.0",
}

# 32 slots = 64-hour cycle.
# High-value/high-volume sports are refreshed much more often,
# while every covered sport is still refreshed at least once per cycle.
ROTATION = [
    "soccer",
    "tennis",
    "basketball",
    "soccer",
    "tennis",
    "ice-hockey",
    "basketball",
    "handball",
    "soccer",
    "tennis",
    "rugby-union",
    "volleyball",
    "soccer",
    "basketball",
    "tennis",
    "baseball",
    "soccer",
    "handball",
    "ice-hockey",
    "basketball",
    "rugby-union",
    "american-football",
    "soccer",
    "tennis",
    "volleyball",
    "rugby-league",
    "soccer",
    "badminton",
    "mma",
    "boxing",
    "snooker",
    "australian-rules",
]

ALL_SPORTS = [
    "soccer", "tennis", "basketball", "ice-hockey", "baseball", "handball",
    "rugby-union", "rugby-league", "american-football", "badminton",
    "table-tennis", "mma", "boxing", "snooker", "volleyball",
    "australian-rules",
]

def selected_sport():
    # GitHub schedule runs every 2 hours. UTC epoch gives a stable 64-hour cycle.
    slot = int(time.time() // 7200) % len(ROTATION)
    return ROTATION[slot]

def get_events(sport):
    url = f"{BASE}/{sport}/events"
    params = {"page": 1, "limit": 30}

    for attempt in range(2):
        r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        if r.status_code != 429:
            r.raise_for_status()
            payload = r.json()
            return payload.get("events", payload if isinstance(payload, list) else [])
        if attempt == 0:
            time.sleep(5)

    r.raise_for_status()

def load_previous():
    if not OUT.exists():
        return {"events": [], "lastUpdatedBySport": {}}
    try:
        return json.loads(OUT.read_text(encoding="utf-8"))
    except Exception:
        return {"events": [], "lastUpdatedBySport": {}}

def main():
    sport = selected_sport()
    previous = load_previous()
    previous_events = previous.get("events", [])
    now_stamp = datetime.now(timezone.utc).isoformat()
    errors = []

    try:
        events = get_events(sport)
        for event in events:
            event["_source"] = "Winamax"
            event["_pulscore_sport"] = sport
            event["_last_updated"] = now_stamp

        merged = [
            e for e in previous_events
            if e.get("_pulscore_sport") != sport
        ]
        merged.extend(events)

        updated = dict(previous.get("lastUpdatedBySport", {}))
        updated[sport] = now_stamp

    except Exception as exc:
        events = []
        errors.append({"sport": sport, "error": str(exc)})
        merged = previous_events
        updated = previous.get("lastUpdatedBySport", {})

    now = datetime.now(timezone.utc)
    upcoming = []

    for event in merged:
        if event.get("live") is True or event.get("live") == 1:
            continue

        raw = event.get("startTime")
        if raw:
            try:
                start = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                if start < now:
                    continue
            except ValueError:
                pass

        upcoming.append(event)

    upcoming.sort(key=lambda e: e.get("startTime") or "9999")

    output = {
        "generatedAt": now_stamp,
        "source": "PulseScore / Winamax",
        "refreshStrategy": (
            "weighted rotation every 2 hours; 32-slot/64-hour cycle; "
            "priority to soccer, tennis and basketball"
        ),
        "currentSportRefreshed": sport,
        "eventCount": len(upcoming),
        "sportsRequested": ALL_SPORTS,
        "rotation": ROTATION,
        "lastUpdatedBySport": updated,
        "errors": errors,
        "events": upcoming,
    }

    OUT.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Refreshed {sport}: {len(events)} events")
    print(f"Saved {len(upcoming)} upcoming Winamax events")

if __name__ == "__main__":
    main()
