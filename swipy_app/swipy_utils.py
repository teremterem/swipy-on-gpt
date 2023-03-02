from datetime import datetime


def current_time_utc_ms():
    """Returns current time in UTC in milliseconds"""
    return int(datetime.utcnow().timestamp() * 1000)
