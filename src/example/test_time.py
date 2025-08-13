from datetime import timedelta, datetime
from src.pipeline.time_manager import TimeManager
nowtime = int(datetime.now().timestamp())
endtime =  nowtime
delta = timedelta(hours = 1)
starttime = TimeManager(endtime).as_datetime() - delta