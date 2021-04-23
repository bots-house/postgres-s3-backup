FROM python:3.8.5-alpine3.12

RUN apk update && apk add --no-cache mysql-client

COPY requirements.txt requirements.txt

RUN pip install --no-cache -r requirements.txt &&  pip install requests

COPY backup.py config.py log_pipe.py telegram_notify.py ./

CMD ["python", "backup.py"]
