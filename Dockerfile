# Dockerfile to build a flask demo container
# Based on https://goo.gl/IHJGtP
# Last update: 06.15.2017

FROM ubuntu

MAINTAINER Chris Coyle

# Install base package requirements
RUN apt-get update
RUN apt-get -y install tar git curl dialog net-tools

# Install python packages
RUN apt-get -y install python python-dev python-distribute python-pip

# Copy demo application
ADD /app /opt/flask_demo

# Setup environment
RUN pip install -r /opt/flask_demo/requirements.txt

# Expose HTTP
EXPOSE 8000

# Start application
WORKDIR /opt/flask_demo

# CMD service nginx start
CMD gunicorn -b 0.0.0.0 -w1 app:app --log-level DEBUG
