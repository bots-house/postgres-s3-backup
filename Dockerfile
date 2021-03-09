FROM python:3.8.5-alpine3.12

WORKDIR /backup

LABEL org.opencontainers.image.source https://github.com/bots-house/postgres-s3-backup

RUN apk update
RUN apk add --no-cache postgresql-client

COPY requirements.txt requirements.txt

RUN pip install --no-cache -r requirements.txt

COPY backup ./backup

CMD ["python", "backup.py"]