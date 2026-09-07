import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path
import requests

API_KEY = os.environ["PULSESCORE_API_KEY"]
BASE = "https://api.pulsescore.net/api/winamax"
SPORTS = [
    "soccer", "tennis", "basketball", "ice-hockey", "baseball", "handball",
    "rugby-union", "rugby-league", "american-football", "badminton",
    "table-tennis", "mma", "boxing", "snooker", "volleyball", "australian-rules",
]
OUT = Path("data/winamax_odds.json")
OUT.parent.mkdir(parents=True, exist_ok=True)
HEADERS = {
    "X-Secret": API_KEY,
    "Accept-Encoding": "gzip",
    "User-Agent": "winamax-pulsescore-bridge/2.0",
}

def selected_sport():
    hour = datetime.now(timezone.utc).hour
    return SPORTS[(hour // 2) % len(SPORTS)]

def get_events(sport):
    url = f"{BASE}/{sport}/events"
    params = {"page": 1, "limit": 30}
    r = requests.get(url, headers=HEADERS, params=params, timeout=30)
    if r.status_code == 429:
        time.sleep(5)
        r = requests.get(url, headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    payload = r.json()
    return payload.get("events", payload if isinstance(payload, list) else [])

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
    errors = []
    now_stamp = datetime.now(timezone.utc).isoformat()

    try:
        events = get_events(sport)
        for event in events:
            event["_source"] = "Winamax"
            event["_pulscore_sport"] = sport
            event["_last_updated"] = now_stamp
        merged = [e for e in previous_events if e.get("_pulscore_sport") != sport]
        merged.extend(events)
        updated = previous.get("lastUpdatedBySport", {})
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
                if datetime.fromisoformat(raw.replace("Z", "+00:00")) < now:
                    continue
            except ValueError:
                pass
        upcoming.append(event)

    upcoming.sort(key=lambda e: e.get("startTime") or "9999")
    output = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "source": "PulseScore / Winamax",
        "refreshStrategy": "one sport every 2 hours; rotating 16-sport cache",
        "currentSportRefreshed": sport,
        "eventCount": len(upcoming),
        "sportsRequested": SPORTS,
        "lastUpdatedBySport": updated,
        "errors": errors,
        "events": upcoming,
    }
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Refreshed {sport}: {len(events)} events")
    print(f"Saved {len(upcoming)} upcoming Winamax events")

if __name__ == "__main__":
    main()
