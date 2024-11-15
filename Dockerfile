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

RUN poetry add \
  matplotlib \
  numpy \
  pandas \
  pytest \
  pytest-watch \
  sphinx \
  # sphinx-rtd-theme \
  sphinx-autobuild \
  furo \
  sphinx-book-theme \
  pydata-sphinx-theme \
  ipython \
  termcolor 


RUN poetry config virtualenvs.in-project true

COPY . .
WORKDIR /root/opt
RUN pip install -e .
# RUN poetry shell & pip install -e e

# Export gui display to host using XQuartz
ENV DISPLAY=host.docker.internal:0.0
ENV QT_X11_NO_MITSHM=1
