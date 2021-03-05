import os
import subprocess
import threading
import dataclasses

from datetime import datetime, timezone, timedelta

import boto3
from loguru import logger


@dataclasses.dataclass
class Config:
    db_url: str
    s3_expire_time: int
    s3_bucket: str
    s3_region_name: str
    s3_endpoint_url: str
    s3_access_key_id: str
    s3_secret_access_key: str

    @staticmethod
    def parse_env():
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("please set DATABASE_URL environment")
        
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

        return Config(
            db_url=db_url,
            s3_expire_time=int(s3_expire_time),
            s3_bucket=s3_bucket,
            s3_region_name=s3_region_name,
            s3_endpoint_url=s3_endpoint_url,
            s3_access_key_id=s3_access_key_id,
            s3_secret_access_key=s3_secret_access_key,
        )



class LogPipe(threading.Thread):

    def __init__(self):
        """Setup the object with a logger and a loglevel
        and start the thread
        """
        threading.Thread.__init__(self)
        self.daemon = False
        self.level = "DEBUG"
        self.fdRead, self.fdWrite = os.pipe()
        self.pipeReader = os.fdopen(self.fdRead)
        self.start()

    def fileno(self):
        """Return the write file descriptor of the pipe
        """
        return self.fdWrite

    def run(self):
        """Run the thread, logging everything.
        """
        for line in iter(self.pipeReader.readline, ''):
            logger.log(self.level, line.strip('\n'))

        self.pipeReader.close()

    def close(self):
        """Close the write end of the pipe.
        """
        os.close(self.fdWrite)


def dump_db(db_url: str, filename: str):
    logger.info("start pg_dump")
    logpipe_debug = LogPipe()

    try:
        subprocess.run(
            [
                "pg_dump",
                "--verbose",
                "--format=custom",
                "--compress=9",
                f"--file={filename}",
                db_url,
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

    objects = client.list_objects(Bucket=config.s3_bucket)
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
    start_backup_at = datetime.now(timezone.utc)

    try:
        dump_db(db_url=config.db_url, filename=filename)
    except subprocess.CalledProcessError as err:
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
    except Exception as err:
        logger.error(err)

    finally:
        os.remove(filename)

if __name__ == "__main__":
    main()