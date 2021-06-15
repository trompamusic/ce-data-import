FROM mtgupf/verovio:latest as verovio

FROM ubuntu:20.04

RUN apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
       musescore3 \
       xvfb \
       python3 \
       python3-pip \
       git \
  && rm -rf /var/lib/apt/lists/*

COPY --from=verovio /usr/local/bin/verovio /usr/local/bin/verovio
COPY --from=verovio /usr/local/share/verovio /usr/local/share/verovio

RUN mkdir /code
WORKDIR /code

COPY requirements.txt /code
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install --no-cache-dir ipython

COPY . /code


# Optional, install verovio from source
#FROM buildpack-deps:buster AS build-env
#
#ARG VEROVIO_VERSION=3.2.0
#
#RUN apt-get update \
#  && apt-get install -y cmake build-essential
#
#RUN mkdir /tmp/verovio
#WORKDIR /tmp/verovio
#RUN wget -O verovio-$VEROVIO_VERSION.tar.gz https://github.com/rism-ch/verovio/archive/version-$VEROVIO_VERSION.tar.gz
#RUN tar xfz verovio-$VEROVIO_VERSION.tar.gz
#WORKDIR /tmp/verovio/verovio-version-$VEROVIO_VERSION/tools
#
#RUN cmake ../cmake && make && make install/strip
#
#COPY --from=build-env /usr/local/bin/verovio /usr/local/bin/verovio
#COPY --from=build-env /usr/local/share/verovio /usr/local/share/verovio