FROM ubuntu:20.04

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y cmake build-essential git

RUN mkdir -p /src
WORKDIR /src
RUN git clone https://github.com/rism-digital/verovio.git
WORKDIR /src/verovio/tools
RUN cmake ../cmake
RUN make -j4
RUN make install