from datetime import datetime, timezone
from typing import Union

class TimeManager:
    """
    TimeManager is a flexible utility for handling various datetime representations.

    Supports initialization from:
    - ISO 8601 string (e.g., "2025-07-19T15:00:00Z")
    - Formatted datetime string (e.g., "2025-07-19 15:00:00")
    - Unix timestamp as int or float
    - datetime.datetime object

    Example usage:
        tm1 = TimeManager("2025-07-19T15:00:00Z")        # ISO 8601
        tm2 = TimeManager("2025-07-19 15:00:00")         # formatted string
        tm3 = TimeManager(1752946800)                    # unix int
        tm4 = TimeManager(1752946800.0)                  # unix float
        tm5 = TimeManager(datetime(2025, 7, 19, 15, 0))  # datetime object

        print(tm1.as_formatted_date_time())  # → '2025-07-19 15:00:00'
        print(tm1.as_formatted_time())  # → '15:00:00'
        print(tm1.as_iso())                  # → '2025-07-19T15:00:00Z'
        print(tm1.as_unix())                 # → 1752946800
        print(tm1.as_datetime())             # → datetime.datetime(2025, 7, 19, 15, 0)

        rounded_tm = tm1.round_down_to_nearest_five()
        print(rounded_tm.as_formatted_date_time())

        now_tm = TimeManager.now()
        now_rounded_tm = TimeManager.now_rounded_to_five()
    """

    def __init__(self, timestamp: Union[str, int, float, datetime]):
        if isinstance(timestamp, datetime):
            self._dt = timestamp.replace(tzinfo=timezone.utc)
        elif isinstance(timestamp, (int, float)):
            self._dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        elif isinstance(timestamp, str):
            try:
                # Try ISO 8601 with 'Z'
                self._dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            except ValueError:
                # Try formatted string without timezone
                self._dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        else:
            raise TypeError(f"Unsupported timestamp type: {type(timestamp)}")

    def as_datetime(self) -> datetime:
        """Return the internal datetime object (UTC)."""
        return self._dt

    def as_unix(self) -> int:
        """Return the Unix timestamp as an integer."""
        return int(self._dt.timestamp())

    def as_iso(self) -> str:
        """Return ISO 8601 string (UTC) with 'Z' suffix."""
        return self._dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def as_formatted_date_time(self) -> str:
        """Return formatted string 'YYYY-MM-DD HH:MM:SS'."""
        return self._dt.strftime("%Y-%m-%d %H:%M:%S")

    def as_formatted_time(self) -> str:
        """Return formatted string 'HH:MM:SS'."""
        return self._dt.strftime("%H:%M:%S")
    
    def as_excel(self) -> float:
        """Returns Excel serial number for Windows (based on 1899-12-30 epoch)."""
        unix_ts = self.as_unix()
        return unix_ts / 86400 + 25569  # 86400 seconds in a day

    def round_down_to_nearest_five(self) -> "TimeManager":
        """Return new TimeManager rounded down to nearest 5-minute mark."""
        minute = (self._dt.minute // 5) * 5
        rounded_dt = self._dt.replace(minute=minute, second=0, microsecond=0)
        return TimeManager(rounded_dt)

    @staticmethod
    def now() -> "TimeManager":
        """Return current UTC time as a TimeManager."""
        return TimeManager(datetime.now(timezone.utc))

    @staticmethod
    def now_rounded_to_five() -> "TimeManager":
        """Return current UTC time rounded down to nearest 5 minutes."""
        now = datetime.now(timezone.utc)
        minute = (now.minute // 5) * 5
        rounded = now.replace(minute=minute, second=0, microsecond=0)
        return TimeManager(rounded)

    def __repr__(self):
        return f"TimeManager({self.as_iso()})"

    def __str__(self):
        return self.as_formatted_date_time()
