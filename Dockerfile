FROM python:3
USER root

RUN apt-get update

RUN apt-get install -y --no-install-recommends libx11-dev x11-apps

RUN apt-get install -y vim less
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install poetry

WORKDIR /root/opt
COPY pyproject.toml .

RUN poetry install

# !TODO: Add yazi, fish


RUN poetry config virtualenvs.in-project true

COPY . .
WORKDIR /root/opt
RUN pip install -e .
RUN poetry run pip install -e .

# Export gui display to host using XQuartz
ENV DISPLAY=host.docker.internal:0.0
ENV QT_X11_NO_MITSHM=1
