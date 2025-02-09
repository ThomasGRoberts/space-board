from datetime import datetime, timezone

def get_time_remaining(target_time: str) -> str:
    # Convert target_time string (ISO format) to a datetime object.
    target_dt = datetime.fromisoformat(target_time.replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    if target_dt < now:
        return ""  # Target time has passed.
    delta = target_dt - now
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{days}d {hours:02d}h {minutes:02d}m"
