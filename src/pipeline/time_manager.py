from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
from datetime import datetime, timezone
from typing import Union
import click
import backports.zoneinfo
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo


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
        print(tm1.as_isoz())                  # → '2025-07-19T15:00:00Z'
        print(tm1.as_unix())                 # → 1752946800
        print(tm1.as_datetime())             # → datetime.datetime(2025, 7, 19, 15, 0)

        rounded_tm = tm1.round_down_to_nearest_five()
        print(rounded_tm.as_formatted_date_time())

        now_tm = TimeManager.now()
        now_rounded_tm = TimeManager.now_rounded_to_five()
    """
    
    HOW_TO_UTCZ_DOC =  """
    # HOW TO CONVERT TIME BEFORE USING TIMEMANAGER
    ## 1. Create a datetime in Central Time
    central_time = datetime(2025, 7, 19, 10, 0, tzinfo=ZoneInfo("America/Chicago"))

    ## 2. Convert to UTC
    utc_time = central_time.astimezone(ZoneInfo("UTC"))

    ## 3. Use the TimeManager class to ensure ISO format (with Z). 
    utc_time_z = TimeManager(utc_time).as_isoz()

    print("Central:", central_time)
    print("UTC:    ", utc_time)

    # ALTERNATIVE METHODS 
    ## - Prepare single timestamp (top of the hour UTC)
    ``` 
    import datetime
    timestamp = datetime.datetime.now(datetime.timezone.utc).replace(minute=0, second=0, microsecond=0)
    timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    ```

    """

    def __init__(self, timestamp: Union[str, int, float, datetime]):
        if isinstance(timestamp, datetime):
            self._dt = timestamp.replace(tzinfo=timezone.utc)
        elif isinstance(timestamp, (int, float)):
            self._dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            '''
        elif isinstance(timestamp, str):
            try:
                # Use fromisoformat (Python 3.7+)
                self._dt = datetime.fromisoformat(timestamp).replace(tzinfo=timezone.utc)
            except ValueError:
                self._dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            '''
        elif isinstance(timestamp, str):
            try:
                if timestamp.endswith("Z"):
                    # Strip 'Z' and parse as UTC
                    self._dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                else:
                    # Try ISO 8601 string with offset (e.g., +00:00)
                    self._dt = datetime.fromisoformat(timestamp).astimezone(timezone.utc)
            except ValueError:
                # Fallback to "YYYY-MM-DD HH:MM:SS"
                self._dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

            '''
        elif isinstance(timestamp, str):
            try:
                # Try ISO 8601 with 'Z'
                self._dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            except ValueError:
                # Try formatted string without timezone
                self._dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            '''
        else:
            raise TypeError(f"Unsupported timestamp type: {type(timestamp)}")

    def as_datetime(self) -> datetime:
        """Return the internal datetime object (UTC)."""
        return self._dt
    
    def as_safe_isoformat_for_filename(self) -> str:
        """
        Returns an ISO 8601 formatted UTC time string safe for use in filenames.
        Example: '2025-07-19T23-35-00Z'
        """
        return self.as_datetime().isoformat().replace(":", "-") + "Z"

    def as_unix(self):# -> int:
        """Return the Unix timestamp as an integer."""
        return int(self._dt.timestamp())

    def as_isoz(self):# -> str:
        """Return ISO 8601 string (UTC) with 'Z' suffix."""
        return self._dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    def as_iso(self):# -> str:
        """Return ISO 8601, like datetime.fromtimestamp(ts).isoformat()."""
        return self._dt.isoformat()

    def as_formatted_date_time(self):# -> str:
        """Return formatted string 'YYYY-MM-DD HH:MM:SS'."""
        return self._dt.strftime("%Y-%m-%d %H:%M:%S")

    def as_formatted_time(self):# -> str:
        """Return formatted string 'HH:MM:SS'."""
        return self._dt.strftime("%H:%M:%S")
    
    def as_excel(self):# -> float:
        """Returns Excel serial number for Windows (based on 1899-12-30 epoch)."""
        unix_ts = self.as_unix()
        return unix_ts / 86400 + 25569  # 86400 seconds in a day

    def round_down_to_nearest_five(self):# -> "TimeManager":
        """Return new TimeManager rounded down to nearest 5-minute mark."""
        minute = (self._dt.minute // 5) * 5
        rounded_dt = self._dt.replace(minute=minute, second=0, microsecond=0)
        return TimeManager(rounded_dt).as_unix()

    @staticmethod
    def now():# -> "TimeManager":
        """Return current UTC time as a TimeManager."""
        return TimeManager(datetime.now(timezone.utc)).as_unix()
    

    @staticmethod
    #def from_local(dt: datetime, zone_name: str) -> "TimeManager":
    def from_local(dt, zone_name):
        """
        Convert a local datetime in the given time zone to UTC and return a TimeManager instance.

        Args:
            dt (datetime): The local datetime (can be naive or aware).
            zone_name (str): A valid IANA time zone string, e.g. 'America/Chicago'.

        Returns:
            TimeManager: A new instance based on the UTC version of the datetime.
        """
        if dt.tzinfo is None:
            local_dt = dt.replace(tzinfo=ZoneInfo(zone_name))
        else:
            local_dt = dt.astimezone(ZoneInfo(zone_name))
        utc_dt = local_dt.astimezone(timezone.utc)
        return TimeManager(utc_dt)

        
    @staticmethod
    def now_rounded_to_five():# -> "TimeManager":
        """Return current UTC time rounded down to nearest 5 minutes."""
        now = datetime.now(timezone.utc)
        minute = (now.minute // 5) * 5
        rounded = now.replace(minute=minute, second=0, microsecond=0)
        return TimeManager(rounded).as_unix()

    def __repr__(self):
        return f"TimeManager({self.as_isoz()})"

    def __str__(self):
        return self.as_formatted_date_time()
   
@click.command()
def main():
    click.echo("WELCOME TO THE `TimeManager` CLASS")
    click.echo("pipx install pipeline")
    click.echo("from pipeline.time_manager import TimeManager")
    click.echo("")
    click.echo("test>> click.MultiCommand(True)")
    click.MultiCommand(True)
    click.echo("test>> click.MultiCommand()")
    click.MultiCommand()

def howto_utcz():
    click.echo(TimeManager.HOW_TO_UTCZ_DOC)

if __name__ == "__main__":
    main()