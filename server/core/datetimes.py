import datetime
import traceback
from datetime import date, time
from typing import Optional

from utils.ints import IntUtils


class Interval:

    def __init__(self, since: Optional[datetime.datetime], until: Optional[datetime.datetime]):
        self.since = since
        self.until = until

        if self.since is not None:
            assert isinstance(self.since, datetime.datetime)

        if self.until is not None:
            assert isinstance(self.until, datetime.datetime)

    def __str__(self):
        return f'{self.__class__.__name__}(since={self.since}, until={self.until})'

    def __repr__(self):
        return str(self)


class DatetimeUtils:

    @staticmethod
    def to_datetime(value) -> Optional[datetime.datetime]:
        if isinstance(value, str):
            try:
                value = IntUtils.to_int(value)
                if not value:
                    return None
                return datetime.datetime.fromtimestamp(value)
            except (Exception,):
                return None
        elif isinstance(value, int):
            return datetime.datetime.fromtimestamp(value)
        elif isinstance(value, datetime.datetime):
            return value
        return None

    @staticmethod
    def get_current_timestamp() -> int:
        return int(datetime.datetime.timestamp(datetime.datetime.now()))

    @staticmethod
    def as_interval_start(value, fmt='%Y-%m-%d') -> Optional[datetime.datetime]:
        if value and isinstance(value, str):
            value = DatetimeUtils.str_2_datetime(value, fmt=fmt)
        if value and isinstance(value, datetime.datetime):
            return value.replace(hour=0, minute=0, second=0, microsecond=0)
        return None

    @staticmethod
    def as_interval_end(value, fmt='%Y-%m-%d') -> Optional[datetime.datetime]:
        if value and isinstance(value, str):
            value = DatetimeUtils.str_2_datetime(value, fmt=fmt)
        if value and isinstance(value, datetime.datetime):
            return value.replace(hour=23, minute=59, second=59, microsecond=59)
        return None

    @staticmethod
    def as_date_interval(value, fmt='%Y-%m-%d') -> Optional[Interval]:
        if value and isinstance(value, str):
            if '..' in value:
                since, until = value.split('..', maxsplit=1)

                if since and isinstance(since, str):
                    since = DatetimeUtils.as_interval_start(since, fmt=fmt)

                if until and isinstance(until, str):
                    until = DatetimeUtils.as_interval_end(until, fmt=fmt)

                if isinstance(since, datetime.datetime):
                    if isinstance(until, datetime.datetime):
                        return Interval(since, until)
                    else:
                        return Interval(since, None)
                elif isinstance(until, datetime.datetime):
                    return Interval(None, until)

        return None

    @staticmethod
    def as_interval(value) -> Optional[Interval]:
        if value and isinstance(value, str):
            if '..' in value:
                since, until = value.split('..', maxsplit=1)

                if since and isinstance(since, str):
                    since = since.rstrip('Z')
                    since = datetime.datetime.fromisoformat(since)

                if until and isinstance(until, str):
                    until = until.rstrip('Z')
                    until = datetime.datetime.fromisoformat(until)

                if isinstance(since, datetime.datetime):
                    if isinstance(until, datetime.datetime):
                        return Interval(since, until)
                    else:
                        return Interval(since, None)
                elif isinstance(until, datetime.datetime):
                    return Interval(None, until)

        return None

    @staticmethod
    def parse(value, default=None, time_index=None, *fmts) -> Optional[datetime.datetime]:
        if not fmts:
            fmts = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d']

        output = None

        for fmt in fmts:
            output = DatetimeUtils.str_2_datetime(value, fmt)
            if output:
                break

        if not output:
            if isinstance(default, datetime.datetime):
                output = default

        if output:
            if time_index == 'min':
                return output.replace(hour=0, minute=0, second=0, microsecond=0)
            elif time_index == 'max':
                return output.replace(hour=23, minute=59, second=59, microsecond=59)
            return output
        return None

    @staticmethod
    def str_2_datetime(value, fmt, exception_level=None) -> Optional[datetime.datetime]:
        if value and isinstance(value, str):
            try:
                return datetime.datetime.strptime(value, fmt)
            except (Exception,):
                if exception_level == 'info':
                    traceback.print_exc()
        return None

    @staticmethod
    def datetime_2_str(value, fmt='%Y-%m-%d %H:%M:%S.%f', exception_level=None) -> Optional[str]:
        if value and isinstance(value, datetime.datetime):
            try:
                return datetime.datetime.strftime(value, fmt)
            except (Exception,):
                if exception_level == 'info':
                    traceback.print_exc()
        return None

    @staticmethod
    def time_2_minutes(value) -> Optional[int]:
        if isinstance(value, time):
            return int(value.hour * 60 + value.minute + value.second // 60)
        return None

    @staticmethod
    def time_2_seconds(value) -> Optional[int]:
        if isinstance(value, time):
            return int(
                datetime.timedelta(
                    hours=value.hour,
                    minutes=value.minute,
                    seconds=value.second,
                    microseconds=value.microsecond
                ).total_seconds()
            )
        return None

    @staticmethod
    def minutes_2_time(value) -> Optional[time]:
        if isinstance(value, int):
            return time(hour=value // 60, minute=value % 60, second=0)
        return None

    @staticmethod
    def time_2_str(value, fmt='iso', timespec='seconds') -> Optional[str]:
        if isinstance(value, time):
            if fmt == 'iso':
                return value.isoformat(timespec=timespec)
        return None

    @staticmethod
    def str_2_time(value, fmt='iso') -> Optional[time]:
        if isinstance(value, str):
            if fmt == 'iso':
                if hasattr(time, 'fromisoformat'):
                    return time.fromisoformat(value)
                else:
                    return time(*DatetimeUtils._parse_isoformat_time(value))
        return None

    @staticmethod
    def str_2_date(value, fmt='iso') -> Optional[date]:
        if isinstance(value, str):
            if fmt == 'iso':
                if hasattr(date, 'fromisoformat'):
                    try:
                        year, month, day = value.split('-')
                        return date.fromisoformat(f'{year}-{month.zfill(2)}-{day.zfill(2)}')
                    except (Exception,):
                        traceback.print_exc()
                else:
                    return date(*DatetimeUtils._parse_isoformat_date(value))
        return None

    @staticmethod
    def date_2_str(value, fmt='iso') -> Optional[str]:
        if isinstance(value, date):
            if fmt == 'iso':
                return value.isoformat()
        return None

    @staticmethod
    def _parse_isoformat_date(dtstr):
        # It is assumed that this function will only be called with a
        # string of length exactly 10, and (though this is not used) ASCII-only
        year = int(dtstr[0:4])
        if dtstr[4] != '-':
            raise ValueError('Invalid date separator: %s' % dtstr[4])

        month = int(dtstr[5:7])

        if dtstr[7] != '-':
            raise ValueError('Invalid date separator')

        day = int(dtstr[8:10])

        return [year, month, day]

    # Code copied from datetime.py file, because some systems has Python version < 3.6
    @staticmethod
    def _parse_isoformat_time(tstr):
        # Format supported is HH[:MM[:SS[.fff[fff]]]][+HH:MM[:SS[.ffffff]]]
        len_str = len(tstr)
        if len_str < 2:
            raise ValueError('Isoformat time too short')

        # This is equivalent to re.search('[+-]', tstr), but faster
        tz_pos = (tstr.find('-') + 1 or tstr.find('+') + 1)
        timestr = tstr[:tz_pos - 1] if tz_pos > 0 else tstr

        time_comps = DatetimeUtils._parse_hh_mm_ss_ff(timestr)

        tzi = None
        if tz_pos > 0:
            tzstr = tstr[tz_pos:]

            # Valid time zone strings are:
            # HH:MM               len: 5
            # HH:MM:SS            len: 8
            # HH:MM:SS.ffffff     len: 15

            if len(tzstr) not in (5, 8, 15):
                raise ValueError('Malformed time zone string')

            tz_comps = DatetimeUtils._parse_hh_mm_ss_ff(tzstr)
            if all(x == 0 for x in tz_comps):
                tzi = datetime.timezone.utc
            else:
                tzsign = -1 if tstr[tz_pos - 1] == '-' else 1

                td = datetime.timedelta(
                    hours=tz_comps[0],
                    minutes=tz_comps[1],
                    seconds=tz_comps[2],
                    microseconds=tz_comps[3]
                )

                tzi = datetime.timezone(tzsign * td)

        time_comps.append(tzi)

        return time_comps

    @staticmethod
    def _parse_hh_mm_ss_ff(tstr):
        # Parses things of the form HH[:MM[:SS[.fff[fff]]]]
        len_str = len(tstr)

        time_comps = [0, 0, 0, 0]
        pos = 0
        for comp in range(0, 3):
            if (len_str - pos) < 2:
                raise ValueError('Incomplete time component')

            time_comps[comp] = int(tstr[pos:pos + 2])

            pos += 2
            next_char = tstr[pos:pos + 1]

            if not next_char or comp >= 2:
                break

            if next_char != ':':
                raise ValueError('Invalid time separator: %c' % next_char)

            pos += 1

        if pos < len_str:
            if tstr[pos] != '.':
                raise ValueError('Invalid microsecond component')
            else:
                pos += 1

                len_remainder = len_str - pos
                if len_remainder not in (3, 6):
                    raise ValueError('Invalid microsecond component')

                time_comps[3] = int(tstr[pos:])
                if len_remainder == 3:
                    time_comps[3] *= 1000

        return time_comps

    @staticmethod
    def datetime_by_hours(start_time, stop_time):
        if stop_time <= start_time:
            return []

        def seconds_since_hour_start(dt):
            return dt.minute * 60 + dt.second

        def seconds_until_hour_end(dt):
            return (60 - dt.minute) * 60 - dt.second

        hourly_times_corrected = []
        hour = start_time
        while hour < stop_time:
            hour = hour.replace(minute=0, second=0, microsecond=0)
            if hour == start_time.replace(minute=0, second=0, microsecond=0) and \
                hour == stop_time.replace(minute=0, second=0, microsecond=0):
                seconds = (stop_time - start_time).seconds
            elif hour == start_time.replace(minute=0, second=0, microsecond=0):
                seconds = seconds_until_hour_end(start_time)
            elif hour < stop_time.replace(minute=0, second=0, microsecond=0):
                seconds = 3600
            else:
                seconds = seconds_since_hour_start(stop_time)

            hourly_times_corrected.append(
                {
                    'date_key': hour.strftime('%Y-%m-%d'),
                    'hour': hour.strftime('%H'),
                    'time': seconds
                }
            )
            hour += datetime.timedelta(hours=1)

        return hourly_times_corrected
