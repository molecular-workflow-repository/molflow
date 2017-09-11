FROM python:2.7-slim

RUN apt-get update && apt-get install -y --no-install-recommends vim git curl
RUN curl -fsSLO https://get.docker.com/builds/Linux/x86_64/docker-17.04.0-ce.tgz \
  && tar xzvf docker-17.04.0-ce.tgz \
  && mv docker/docker /usr/local/bin \
  && rm -r docker docker-17.04.0-ce.tgz

ADD . /opt/molecular-workflow-repository
RUN pip install -r /opt/molecular-workflow-repository/requirements.txt \
 && pip install -e /opt/molecular-workflow-repository
