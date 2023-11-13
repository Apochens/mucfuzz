FROM ubuntu:20.04

RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections
RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    apt-get -y upgrade && \
    apt-get install -y git build-essential wget zlib1g-dev python3-pip python3-dev python-is-python3 cmake && \
    apt-get clean

# install rust
RUN apt-get install -y curl
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# install go
RUN wget https://golang.google.cn/dl/go1.17.linux-amd64.tar.gz && \
    tar -xzf go1.17.linux-amd64.tar.gz && \
    rm go1.17.linux-amd64.tar.gz

ENV GOPATH=/go-tools \
    PATH=/clang+llvm/bin:/mucfuzz/bin:/go/bin:/go-tools/bin:$PATH \
    LD_LIBRARY_PATH=/clang+llvm/lib:$LD_LIBRARY_PATH

RUN git clone https://github.com/Apochens/mucfuzz.git
WORKDIR /mucfuzz

RUN PREFIX=/ ./build/install_llvm.sh
RUN ./build/install_tools.sh