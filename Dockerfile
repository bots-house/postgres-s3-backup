FROM python:3.8.5-alpine3.12

LABEL org.opencontainers.image.source https://github.com/bots-house/postgres-s3-backup

RUN apk update
RUN apk add --no-cache postgresql-client=11.11-r0 --repository=http://dl-cdn.alpinelinux.org/alpine/v3.9/main

COPY requirements.txt requirements.txt

RUN pip install --no-cache -r requirements.txt
RUN pip install requests

COPY backup.py backup.py
COPY config.py config.py
COPY log_pipe.py log_pipe.py
COPY telegram_notify.py telegram_notify.py

CMD ["python", "backup.py"]