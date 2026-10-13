def save(engine, name, brand, timezone, goals):
    from zoneinfo import ZoneInfo
    if not isinstance(name, str) or not name.strip() or len(name) > 100: raise ValueError("Enter your name")
    if len(brand) > 120 or len(goals) > 4000: raise ValueError("Profile details exceed limits")
    try: ZoneInfo(timezone)
    except Exception: raise ValueError("Select a valid timezone") from None
    body = {"name": name.strip(), "brand": brand.strip(), "timezone": timezone, "goals": goals.strip()}
    engine.store.put("profile", "owner", body)
    return {"status": "saved", "profile": body}


def status(engine):
    try: profile = engine.store.get("profile", "owner")
    except ValueError: profile = None
    accounts = engine.store.all("account")
    doctor = engine.doctor()
    return {"profile": profile, "profile_complete": bool(profile),
            "account_count": len(accounts), "channels": len(engine.store.all("channel")),
            "youtube_ready": doctor["youtube_oauth_configured"], "instagram_ready": doctor["instagram_oauth_configured"],
            "flow_browser_mode": "remote" if __import__('os').getenv('VSO_REMOTE_BROWSER') == '1' else "local",
            "image_work": "ChatGPT only; never a dashboard image generator",
            "agent_message": "The setup agent configures infrastructure and provider apps. You sign in and approve content."}
