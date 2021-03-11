FROM tiangolo/uwsgi-nginx-flask:python3.6


ENV STATIC_PATH /app/app/static

COPY . /app

WORKDIR /app/app

RUN pip install -r requirements.txt
