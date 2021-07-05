import logging
import os
import re
import time
import traceback

from logging.handlers import BaseRotatingHandler
from stat import ST_MTIME

from com.lib.filelock import file_io_lock

#
_MIDNIGHT = 24 * 60 * 60  # number of seconds in a day

LOCK_FILE = ".logging.lock"


class TimedRotatingFileHandler(BaseRotatingHandler):
    """

    优化：（python3.8 & django3.2）

    - 命名规范化
    - 多进程安全


    # ===========

    Handler for logging to a file, rotating the log file at certain timed
    intervals.

    If backup_count is > 0, when rollover is done, no more than backup_count
    files are kept - the oldest ones are deleted.
    """

    def __init__(
            self, filename, when='h', interval=1, backup_count=0, encoding=None, delay=False, utc=False, at_time=None
    ):
        BaseRotatingHandler.__init__(self, filename, 'a', encoding, delay)
        #
        filename = os.fspath(filename)
        # keep the absolute path, otherwise derived classes which use this
        # may come a cropper when the current directory changes
        self.base_filename = os.path.abspath(filename)
        self.lock_file = os.path.join(os.path.dirname(self.base_filename), LOCK_FILE)
        #
        self.when = when.upper()
        self.backup_count = backup_count
        self.utc = utc
        self.at_time = at_time
        # Calculate the real rollover interval, which is just the number of
        # seconds between rollovers.  Also set the filename suffix used when
        # a rollover occurs.  Current 'when' events supported:
        # S - Seconds
        # M - Minutes
        # H - Hours
        # D - Days
        # midnight - roll over at midnight
        # W{0-6} - roll over on a certain day; 0 - Monday
        #
        # Case of the 'when' specifier is not important; lower or upper case
        # will work.
        if self.when == 'S':
            self.interval = 1  # one second
            self.suffix = "%Y-%m-%d_%H-%M-%S"
            self.ext_match = r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}(\.\w+)?$"
        elif self.when == 'M':
            self.interval = 60  # one minute
            self.suffix = "%Y-%m-%d_%H-%M"
            self.ext_match = r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}(\.\w+)?$"
        elif self.when == 'H':
            self.interval = 60 * 60  # one hour
            self.suffix = "%Y-%m-%d_%H"
            self.ext_match = r"^\d{4}-\d{2}-\d{2}_\d{2}(\.\w+)?$"
        elif self.when == 'D' or self.when == 'MIDNIGHT':
            self.interval = 60 * 60 * 24  # one day
            self.suffix = "%Y-%m-%d"
            self.ext_match = r"^\d{4}-\d{2}-\d{2}(\.\w+)?$"
        elif self.when.startswith('W'):
            self.interval = 60 * 60 * 24 * 7  # one week
            if len(self.when) != 2:
                raise ValueError("You must specify a day for weekly rollover from 0 to 6 (0 is Monday): %s" % self.when)
            if self.when[1] < '0' or self.when[1] > '6':
                raise ValueError("Invalid day specified for weekly rollover: %s" % self.when)
            self.day_of_week = int(self.when[1])
            self.suffix = "%Y-%m-%d"
            self.ext_match = r"^\d{4}-\d{2}-\d{2}(\.\w+)?$"
        else:
            raise ValueError("Invalid rollover interval specified: %s" % self.when)

        self.ext_match = re.compile(self.ext_match, re.ASCII)
        self.interval = self.interval * interval  # multiply by units requested
        # The following line added because the filename passed in could be a
        # path object (see Issue #27493), but self.baseFilename will be a string
        filename = self.base_filename
        if os.path.exists(filename):
            t = os.stat(filename)[ST_MTIME]
        else:
            t = int(time.time())
        self.rollover_at = self.compute_rollover(t)

    def emit(self, record):
        """
        Emit a record.

        Output the record to the file, catering for rollover as described
        in doRollover().
        """
        try:
            if self.should_rollover(record):
                self.do_rollover()
            logging.FileHandler.emit(self, record)
        except Exception:
            traceback.print_exc()

    def compute_rollover(self, current_time):
        """
        Work out the rollover time based on the specified time.
        """
        result = current_time + self.interval
        # If we are rolling over at midnight or weekly, then the interval is already known.
        # What we need to figure out is WHEN the next interval is.  In other words,
        # if you are rolling over at midnight, then your base interval is 1 day,
        # but you want to start that one day clock at midnight, not now.  So, we
        # have to fudge the rollover_at value in order to trigger the first rollover
        # at the right time.  After that, the regular interval will take care of
        # the rest.  Note that this code doesn't care about leap seconds. :)
        if self.when == 'MIDNIGHT' or self.when.startswith('W'):
            # This could be done with less code, but I wanted it to be clear
            if self.utc:
                t = time.gmtime(current_time)
            else:
                t = time.localtime(current_time)
            current_hour = t[3]
            current_minute = t[4]
            current_second = t[5]
            current_day = t[6]
            # r is the number of seconds left between now and the next rotation
            if self.at_time is None:
                rotate_ts = _MIDNIGHT
            else:
                rotate_ts = ((self.at_time.hour * 60 + self.at_time.minute) * 60 +
                             self.at_time.second)

            r = rotate_ts - ((current_hour * 60 + current_minute) * 60 +
                             current_second)
            if r < 0:
                # Rotate time is before the current time (for example when
                # self.rotateAt is 13:45 and it now 14:15), rotation is
                # tomorrow.
                r += _MIDNIGHT
                current_day = (current_day + 1) % 7
            result = current_time + r
            # If we are rolling over on a certain day, add in the number of days until
            # the next rollover, but offset by 1 since we just calculated the time
            # until the next day starts.  There are three cases:
            # Case 1) The day to rollover is today; in this case, do nothing
            # Case 2) The day to rollover is further in the interval (i.e., today is
            #         day 2 (Wednesday) and rollover is on day 6 (Sunday).  Days to
            #         next rollover is simply 6 - 2 - 1, or 3.
            # Case 3) The day to rollover is behind us in the interval (i.e., today
            #         is day 5 (Saturday) and rollover is on day 3 (Thursday).
            #         Days to rollover is 6 - 5 + 3, or 4.  In this case, it's the
            #         number of days left in the current week (1) plus the number
            #         of days in the next week until the rollover day (3).
            # The calculations described in 2) and 3) above need to have a day added.
            # This is because the above time calculation takes us to midnight on this
            # day, i.e. the start of the next day.
            if self.when.startswith('W'):
                day = current_day  # 0 is Monday
                if day != self.day_of_week:
                    if day < self.day_of_week:
                        days_to_wait = self.day_of_week - day
                    else:
                        days_to_wait = 6 - day + self.day_of_week + 1
                    new_rollover_at = result + (days_to_wait * (60 * 60 * 24))
                    if not self.utc:
                        dst_now = t[-1]
                        dst_at_rollover = time.localtime(new_rollover_at)[-1]
                        if dst_now != dst_at_rollover:
                            if not dst_now:  # DST kicks in before next rollover, so we need to deduct an hour
                                addend = -3600
                            else:  # DST bows out before next rollover, so we need to add an hour
                                addend = 3600
                            new_rollover_at += addend
                    result = new_rollover_at
        return result

    def should_rollover(self, record):
        """
        Determine if rollover should occur.

        record is not used, as we are just comparing times, but it is needed so
        the method signatures are the same
        """
        t = int(time.time())
        if t >= self.rollover_at:
            return 1
        return 0

    def get_files_to_delete(self):
        """
        Determine the files to delete when rolling over.

        More specific than the earlier method, which just used glob.glob().
        """
        dirname, basename = os.path.split(self.base_filename)
        filenames = os.listdir(dirname)
        result = []
        prefix = basename + "."
        plen = len(prefix)
        for filename in filenames:
            if filename[:plen] == prefix:
                suffix = filename[plen:]
                if self.ext_match.match(suffix):
                    result.append(os.path.join(dirname, filename))
        if len(result) < self.backup_count:
            result = []
        else:
            result.sort()
            result = result[:len(result) - self.backup_count]
        return result

    def do_rollover(self):
        """
        do a rollover; in this case, a date/time stamp is appended to the filename
        when the rollover happens.  However, you want the file to be named for the
        start of the interval, not the current time.  If there is a backup count,
        then we have to get a list of matching filenames, sort them and remove
        the one with the oldest suffix.
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        # get the time that this sequence started at and make it a TimeTuple
        current_time = int(time.time())
        dst_now = time.localtime(current_time)[-1]
        t = self.rollover_at - self.interval
        if self.utc:
            time_tuple = time.gmtime(t)
        else:
            time_tuple = time.localtime(t)
            dstThen = time_tuple[-1]
            if dst_now != dstThen:
                if dst_now:
                    addend = 3600
                else:
                    addend = -3600
                time_tuple = time.localtime(t + addend)
        dest_filename = self.rotation_filename(self.base_filename + "." + time.strftime(self.suffix, time_tuple))
        # 判断是否切分日志文件
        if not os.path.exists(dest_filename):
            with file_io_lock(self.lock_file):
                if not os.path.exists(dest_filename):
                    self.rotate(self.base_filename, dest_filename)

        # 清理备份的日志文件
        if self.backup_count > 0:
            for s in self.get_files_to_delete():
                if os.path.exists(s):
                    try:
                        os.remove(s)
                    except FileNotFoundError:
                        pass
        #
        if not self.delay:
            self.stream = self._open()
        new_rollover_at = self.compute_rollover(current_time)
        while new_rollover_at <= current_time:
            new_rollover_at = new_rollover_at + self.interval
        # If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dst_at_rollover = time.localtime(new_rollover_at)[-1]
            if dst_now != dst_at_rollover:
                if not dst_now:  # DST kicks in before next rollover, so we need to deduct an hour
                    addend = -3600
                else:  # DST bows out before next rollover, so we need to add an hour
                    addend = 3600
                new_rollover_at += addend
        self.rollover_at = new_rollover_at
