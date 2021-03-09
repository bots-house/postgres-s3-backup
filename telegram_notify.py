import requests

from datetime import datetime, timedelta
from pytz.tzfile import DstTzInfo
from typing import Optional

from config import Config


_SEND_MESSAGE_URL = "https://api.telegram.org/bot{token}/sendMessage"


_SUCCESS_TEXT = """
📦 Backup is done! ✅

Took: {took}
Size: {size}
"""

_UNSUCESSFULY_TEXT = """
📦 Backup error! ❌

Took: {took} 

Checkout logs for error details.
"""


def took_strftime(start_backup_at: datetime, tz: DstTzInfo):
    timedelta = datetime.now(tz=tz) - start_backup_at

    total_seconds = int(timedelta.total_seconds())
    hours, remainder = divmod(total_seconds,60*60)
    minutes, seconds = divmod(remainder,60)

    return f"{hours}h{minutes}m{seconds}s"


def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def notify(config: Config, success: bool, start_backup_at: datetime, size: Optional[int]=None):
    took = took_strftime(start_backup_at, config.tz)

    if size:
        size = sizeof_fmt(size)

    text = ""
    if success:
        text = _SUCCESS_TEXT.format(
            took=took,
            size=size,
        )
    else:
        text = _UNSUCESSFULY_TEXT.format(
            took=took,
        )

    url = _SEND_MESSAGE_URL.format(
        token=config.notify_telegram_bot_token,
    )
    params = dict(
        chat_id=config.notify_telegram_bot_chat_id,
        text=text,
    )

    requests.get(
        url=url,
        params=params,
    )
