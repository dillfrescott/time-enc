FROM ubuntu:24.04 as builder

RUN apt update && apt upgrade -y

RUN apt install -y golang git

RUN git clone https://github.com/drand/tlock /tlock

WORKDIR /tlock/cmd/tle

RUN go build

FROM ubuntu:24.04 as main

COPY --from=builder /tlock/cmd/tle/tle /bin/tle

RUN apt update && apt upgrade -y

RUN apt install -y python3 python3-pip

RUN pip install Flask --break-system-packages

RUN chmod +x /bin/tle

COPY app /app

WORKDIR /app

EXPOSE 5000

ENTRYPOINT ["/bin/bash", "-c", "python3 app.py"]
