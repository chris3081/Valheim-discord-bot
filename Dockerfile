FROM python:3.10.0b3-alpine3.14

COPY . /app
RUN apk add gcc python3-dev libc-dev linux-headers && \
    pip install -r app/requirements.txt
WORKDIR /app
ENTRYPOINT ["python", "bot.py"]
