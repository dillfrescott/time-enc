FROM ubuntu:24.04 AS builder

RUN apt update && apt upgrade -y

ENV PATH=$PATH:/go/bin

RUN apt install -y git wget

RUN wget https://go.dev/dl/go1.23.2.linux-amd64.tar.gz && tar -xvf go1.23.2.linux-amd64.tar.gz

RUN git clone https://github.com/drand/tlock /tlock

WORKDIR /tlock/cmd/tle

RUN go build

FROM ubuntu:24.04 AS main

RUN apt update && apt upgrade -y

COPY --from=builder /tlock/cmd/tle/tle /bin/tle

RUN apt install -y python3 python3-pip

RUN pip install Flask --break-system-packages

RUN chmod +x /bin/tle

COPY app /app

WORKDIR /app

EXPOSE 5000

ENTRYPOINT ["/bin/bash", "-c", "python3 app.py"]
