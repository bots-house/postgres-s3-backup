import dataclasses
import os
import pytz

from loguru import logger
from pytz.tzfile import DstTzInfo


@dataclasses.dataclass
class Config:
    db_host: str
    db_root_pwd: str
    db_name: str
    dump_compress: int # 6 is pg_dump default
    s3_expire_time: int
    s3_bucket: str
    s3_region_name: str
    s3_endpoint_url: str
    s3_access_key_id: str
    s3_secret_access_key: str
    tz: DstTzInfo
    notify_telegram_bot_token: str
    notify_telegram_bot_chat_id: int

    @staticmethod
    def parse_env():
        db_host = os.getenv("DATABASE_HOST")
        if not db_host:
            raise ValueError("DATABASE_HOST was not set")

        db_root_pwd = os.getenv("DATABASE_ROOT_PWD")
        if not db_root_pwd:
            raise ValueError("please set DATABASE_URL environment")

        db_name = os.getenv("DATABASE_NAME")
        if not db_name:
            raise ValueError("please set DATABASE_NAME env. var.")

        dump_compress = 0

        s3_expire_time = os.getenv("S3_EXPIRE_TIME")
        if not s3_expire_time:
            raise ValueError("please set S3_EXPIRE_TIME environment")

        s3_bucket = os.getenv("S3_BUCKET")
        if not s3_bucket:
            raise ValueError("please set S3_BUCKET environment")

        s3_region_name = os.getenv("S3_REGION_NAME")
        if not s3_region_name:
            raise ValueError("please set S3_REGION_NAME environment")

        s3_endpoint_url = os.getenv("S3_ENDPOINT_URL")
        if not s3_endpoint_url:
            raise ValueError("please set S3_ENDPOINT_URL environment")

        s3_access_key_id = os.getenv("S3_ACCESS_KEY_ID")
        if not s3_access_key_id:
            raise ValueError("please set S3_ACCESS_KEY_ID environment")

        s3_secret_access_key = os.getenv("S3_SECRET_ACCESS_KEY")
        if not s3_secret_access_key:
            raise ValueError("please set S3_SECRET_ACCESS_KEY environment")

        tz = os.getenv("TZ")
        if not tz:
            raise ValueError("please set TZ environment")
        try:
            tz = pytz.timezone(tz)
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError("wrong tz environment; can't parse it")

        notify_telegram_bot_token = os.getenv("NOTIFY_TELEGRAM_BOT_TOKEN")
        if not notify_telegram_bot_token:
            logger.debug("NOTIFY_TELEGRAM_BOT_TOKEN doesnt set")

        notify_telegram_bot_chat_id = os.getenv("NOTIFY_TELEGRAM_BOT_CHAT_ID")
        if not notify_telegram_bot_chat_id:
            logger.debug("NOTIFY_TELEGRAM_BOT_CHAT_ID doesnt set")

        return Config(
            db_root_pwd=db_root_pwd,
            dump_compress=int(dump_compress),
            s3_expire_time=int(s3_expire_time),
            s3_bucket=s3_bucket,
            s3_region_name=s3_region_name,
            s3_endpoint_url=s3_endpoint_url,
            s3_access_key_id=s3_access_key_id,
            s3_secret_access_key=s3_secret_access_key,
            tz=tz,
            notify_telegram_bot_token=notify_telegram_bot_token,
            notify_telegram_bot_chat_id=notify_telegram_bot_chat_id,
        )
