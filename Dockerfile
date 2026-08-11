FROM python:3.12-slim

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends libx11-dev x11-apps vim less \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir "setuptools==84.0.0" "poetry==2.4.1"

WORKDIR /root/opt
COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.in-project true \
    && poetry install --no-interaction --no-root

# !TODO: Add yazi, fish

COPY . .
RUN poetry install --no-interaction

# Export GUI display to host using XQuartz.
ENV DISPLAY=host.docker.internal:0.0
ENV QT_X11_NO_MITSHM=1
