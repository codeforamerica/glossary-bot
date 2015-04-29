# You first need get the postgres image from the hub with:
#
# docker pull postgres:9.4   
#
# and create an instance of it with:
#
# sudo docker run --name=db -d postgres:9.4 
# 
# Create the db and tables, you can connect an instance with psql.
#
# createdb -h `sudo docker inspect db | grep IPAddress  | awk -F\" '{print $4}'` -U postgres gloss
#
# and run the manager
#
# export DATABASE_URL=postgresql://postgres@$(sudo docker inspect db | grep IPAddress  | awk -F\" '{print $4}')/gloss
# python manager.py db createdb
#
# Set the variables from env.sample into env.docker excepts the variable `DATABASE_URL`
# and finally run:
#
# docker run --env-file=env.docker -d --link db:db gloss

FROM python:2
MAINTAINER Miguel Angel Gordian <miguel.angel@codeandomexico.org>

ENV DB_DATABASENAME gloss

ENV SLACK_TOKEN ""
ENV SLACK_WEBHOOK_URL ""

WORKDIR /gloss
ADD . /gloss

RUN pip install -r requirements.txt

EXPOSE 8085

ENTRYPOINT gunicorn gloss.docker:app -b 0.0.0.0:8085 --log-file=-
