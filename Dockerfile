FROM ubuntu:24.04

RUN apt update && apt upgrade -y

RUN apt install -y python3 python3-pip postgresql-server-dev-all

RUN pip install Flask Flask-SQLAlchemy PyCrypto psycopg2 pycryptodome --break-system-packages

COPY app /app

WORKDIR /app

EXPOSE 5000

ENTRYPOINT ["/bin/bash", "-c", "python3 app.py"]