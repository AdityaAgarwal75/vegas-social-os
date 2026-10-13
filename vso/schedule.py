"""Daily brief queue. It never impersonates a running ChatGPT agent."""
from datetime import datetime
from zoneinfo import ZoneInfo


def save(engine, hour, timezone, channel_ids):
    if type(hour) is not int or not 0 <= hour <= 23: raise ValueError("Hour must be 0–23")
    try: ZoneInfo(timezone)
    except Exception: raise ValueError("Use an IANA timezone, e.g. Asia/Kolkata") from None
    for ident in channel_ids: engine.store.get("channel", ident)
    record = {"hour": hour, "timezone": timezone, "channel_ids": channel_ids}
    engine.store.put("schedule", "daily", record)
    return {**record, "note": "This schedules brief queue entries. Host-supported ChatGPT automation must consume them; it does not run native image generation by itself."}


def tick(engine):
    try: record = engine.store.get("schedule", "daily")
    except ValueError: return []
    now = datetime.now(ZoneInfo(record["timezone"]))
    if now.hour < record["hour"]: return []
    tasks = []
    for channel_id in record["channel_ids"]:
        ident = engine.store.digest(f"brief:{channel_id}:{now.date().isoformat()}")[:32]
        try: task = engine.store.get("brief", ident)
        except ValueError:
            task = {"id": ident, "channel_id": channel_id, "date": now.date().isoformat(), "status": "awaiting_chatgpt",
                    "instruction": "Research current channel context; create two original concepts with scripts and scene prompts. Use this task ID as plan_save request_id. Native images require the host image tool."}
            engine.store.put("brief", ident, task)
        tasks.append(task)
    return tasks
