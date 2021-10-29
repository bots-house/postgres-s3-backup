import os
import subprocess
import boto3

from datetime import datetime, timezone, timedelta

from loguru import logger

import telegram_notify
from log_pipe import LogPipe
from config import Config



def dump_db(config: Config, filename: str):
    logger.info("start pg_dump")
    logpipe_debug = LogPipe()

    try:
        subprocess.run(
            [
                "pg_dump",
                "--verbose",
                "--format=custom",
                f"--compress={config.dump_compress}",
                f"--file={filename}",
                config.db_url,
            ],
            stdout=logpipe_debug,
            stderr=logpipe_debug,
            check=True,
        )
    finally:
        logpipe_debug.close()

def create_boto3_client(config: Config):
    session = boto3.session.Session()

    return session.client(
        "s3",
        region_name=config.s3_region_name,
        endpoint_url=config.s3_endpoint_url,
        aws_access_key_id=config.s3_access_key_id,
        aws_secret_access_key=config.s3_secret_access_key,
    )


def clean_expired_dumps(config: Config, client):
    logger.debug("clean expired dumps")

    objects = client.list_objects(Bucket=config.s3_bucket, Prefix="backup")
    if not objects:
        return

    backups = [
        content
        for content in objects["Contents"]
        if content["Key"].startswith("backup")
    ]

    border = datetime.now(timezone.utc) - timedelta(seconds=config.s3_expire_time)
    for backup in backups:
        if backup["LastModified"] < border:
            logger.debug(f"delete expired dump; key={backup['Key']};")
            client.delete_object(Bucket=config.s3_bucket, Key=backup["Key"])
        

def upload_dump(config: Config, client, filename: str, start_backup_at: datetime):
    logger.debug("upload dump to s3")

    key = "backup-" + start_backup_at.strftime("%Y-%m-%d-%H-%M")
    client.upload_file(
        Filename=filename,
        Bucket=config.s3_bucket,
        Key=key,
    )

    
def main():
    config = Config.parse_env()
    logger.info(config)

    filename = "backup.dump"
    start_backup_at = datetime.now(config.tz)

    try:
        dump_db(config=config, filename=filename)
    except subprocess.CalledProcessError as err:
        telegram_notify.notify(config=config, success=False, start_backup_at=start_backup_at)
        exit(err.returncode)
    
    try:
        client = create_boto3_client(config=config)

        clean_expired_dumps(
            config=config,
            client=client,
        )

        upload_dump(
            config=config,
            client=client,
            filename=filename,
            start_backup_at=start_backup_at,
        )

        size = os.path.getsize(filename)
        telegram_notify.notify(config=config, success=True, start_backup_at=start_backup_at, size=size)

    except Exception as err:
        logger.error(err)
        telegram_notify.notify(config=config, success=False, start_backup_at=start_backup_at)

    finally:
        os.remove(filename)

if __name__ == "__main__":
    main()