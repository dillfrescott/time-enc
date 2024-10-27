FROM ubuntu:24.04

RUN apt update && apt upgrade -y

RUN apt install -y python3 python3-pip

RUN pip install Flask --break-system-packages

COPY tle /bin/tle

RUN chmod +x /bin/tle

COPY app /app

WORKDIR /app

EXPOSE 5000

ENTRYPOINT ["/bin/bash", "-c", "python3 app.py"]