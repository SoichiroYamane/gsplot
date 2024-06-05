FROM python:3
USER root

RUN apt-get update

RUN apt-get install -y vim less
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install poetry


WORKDIR /root/opt
COPY pyproject.toml .

RUN poetry add matplotlib numpy pandas pytest

