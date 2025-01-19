from datetime import datetime, timedelta
import pytz
import ephem
from timezonefinder import TimezoneFinder

def get_local_timezone(lat, lng):
    tf = TimezoneFinder()
    timezone_name = tf.timezone_at(lat=lat, lng=lng)
    if not timezone_name:
        return None
    return pytz.timezone(timezone_name)

def get_twilight_times(lat, lng, date, offset=0):
    """
    Return (sunset_time, sunrise_time) localized.
    offset is the 'Dämmerungspuffer' in minutes
    """
    local_tz = get_local_timezone(lat, lng)
    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lng)

    # Convert incoming date to UTC first
    date_utc = date.astimezone(pytz.utc)

    # Compute sunset
    sunset_local = ephem.localtime(observer.next_setting(ephem.Sun(), start=date_utc))
    sunset_local = sunset_local.astimezone(local_tz)
    night_begin = sunset_local - timedelta(minutes=offset)

    # Compute sunrise (on next day)
    next_day_utc = (date + timedelta(days=1)).astimezone(pytz.utc)
    sunrise_local = ephem.localtime(observer.previous_rising(ephem.Sun(), start=next_day_utc))
    sunrise_local = sunrise_local.astimezone(local_tz)
    night_end = sunrise_local + timedelta(minutes=offset)

    return night_begin, night_end
