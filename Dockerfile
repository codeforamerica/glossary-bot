FROM python:2
MAINTAINER Miguel Gordian <miguel.angel@codeandomexico.org>

ENV DB_DATABASENAME gloss

ENV SLACK_TOKEN ""
ENV SLACK_WEBHOOK_URL ""


WORKDIR /gloss
ADD . /gloss

RUN pip install -r requirements.txt

# ENTRYPOINT gunicorn gloss.docker:app -b 0.0.0.0:80 --log-file=-
